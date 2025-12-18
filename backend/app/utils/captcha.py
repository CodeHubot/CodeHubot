"""验证码生成和验证工具"""

import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CaptchaStore:
    """验证码存储类（内存存储）"""
    
    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._login_attempts: Dict[str, dict] = {}
        self._blocked_accounts: Dict[str, datetime] = {}  # 被临时禁用的账户
    
    def set_captcha(self, key: str, code: str, expire_minutes: int = 5):
        """保存验证码
        
        Args:
            key: 验证码标识（通常是用户标识）
            code: 验证码内容
            expire_minutes: 过期时间（分钟）
        """
        self._store[key] = {
            'code': code.lower(),  # 统一转小写存储
            'expire_time': datetime.now() + timedelta(minutes=expire_minutes)
        }
        logger.info(f"保存验证码: key={key}, code={code}")
    
    def verify_captcha(self, key: str, code: str) -> bool:
        """验证验证码
        
        Args:
            key: 验证码标识
            code: 用户输入的验证码
            
        Returns:
            验证是否通过
        """
        if key not in self._store:
            logger.warning(f"验证码不存在: key={key}")
            return False
        
        captcha_data = self._store[key]
        
        # 检查是否过期
        if datetime.now() > captcha_data['expire_time']:
            logger.warning(f"验证码已过期: key={key}")
            del self._store[key]
            return False
        
        # 验证验证码（不区分大小写）
        is_valid = captcha_data['code'] == code.lower()
        
        if is_valid:
            # 验证成功后删除验证码（一次性使用）
            del self._store[key]
            logger.info(f"验证码验证成功: key={key}")
        else:
            logger.warning(f"验证码错误: key={key}, expected={captcha_data['code']}, got={code.lower()}")
        
        return is_valid
    
    def delete_captcha(self, key: str):
        """删除验证码"""
        if key in self._store:
            del self._store[key]
            logger.info(f"删除验证码: key={key}")
    
    def record_login_attempt(self, identifier: str) -> int:
        """记录登录失败次数
        
        Args:
            identifier: 用户标识（用户名或邮箱）
            
        Returns:
            当前失败次数
        """
        if identifier not in self._login_attempts:
            self._login_attempts[identifier] = {
                'count': 1,
                'first_attempt': datetime.now()
            }
        else:
            # 检查是否超过1小时，如果超过则重置
            if datetime.now() - self._login_attempts[identifier]['first_attempt'] > timedelta(hours=1):
                self._login_attempts[identifier] = {
                    'count': 1,
                    'first_attempt': datetime.now()
                }
            else:
                self._login_attempts[identifier]['count'] += 1
        
        count = self._login_attempts[identifier]['count']
        logger.info(f"记录登录失败: identifier={identifier}, count={count}")
        return count
    
    def get_login_attempts(self, identifier: str) -> int:
        """获取登录失败次数
        
        Args:
            identifier: 用户标识
            
        Returns:
            失败次数
        """
        if identifier not in self._login_attempts:
            return 0
        
        # 检查是否超过1小时
        if datetime.now() - self._login_attempts[identifier]['first_attempt'] > timedelta(hours=1):
            del self._login_attempts[identifier]
            return 0
        
        return self._login_attempts[identifier]['count']
    
    def reset_login_attempts(self, identifier: str):
        """重置登录失败次数（登录成功后调用）
        
        Args:
            identifier: 用户标识
        """
        if identifier in self._login_attempts:
            del self._login_attempts[identifier]
            logger.info(f"重置登录失败次数: identifier={identifier}")
    
    def is_account_blocked(self, identifier: str, block_duration_minutes: int = 30) -> bool:
        """检查账户是否被临时禁用
        
        Args:
            identifier: 用户标识
            block_duration_minutes: 禁用时长（分钟），默认30分钟
            
        Returns:
            是否被禁用
        """
        if identifier not in self._blocked_accounts:
            return False
        
        block_time = self._blocked_accounts[identifier]
        block_until = block_time + timedelta(minutes=block_duration_minutes)
        
        # 检查是否已经解封
        if datetime.now() > block_until:
            del self._blocked_accounts[identifier]
            logger.info(f"账户禁用已到期，自动解封: identifier={identifier}")
            return False
        
        return True
    
    def get_block_remaining_time(self, identifier: str, block_duration_minutes: int = 30) -> Optional[int]:
        """获取账户剩余禁用时间（秒）
        
        Args:
            identifier: 用户标识
            block_duration_minutes: 禁用时长（分钟），默认30分钟
            
        Returns:
            剩余秒数，如果未被禁用返回 None
        """
        if identifier not in self._blocked_accounts:
            return None
        
        block_time = self._blocked_accounts[identifier]
        block_until = block_time + timedelta(minutes=block_duration_minutes)
        remaining = (block_until - datetime.now()).total_seconds()
        
        if remaining <= 0:
            del self._blocked_accounts[identifier]
            return None
        
        return int(remaining)
    
    def block_account(self, identifier: str):
        """临时禁用账户（失败5次后调用）
        
        Args:
            identifier: 用户标识
        """
        self._blocked_accounts[identifier] = datetime.now()
        logger.warning(f"账户已被临时禁用: identifier={identifier}")
    
    def unblock_account(self, identifier: str):
        """解除账户禁用（管理员手动解封）
        
        Args:
            identifier: 用户标识
        """
        if identifier in self._blocked_accounts:
            del self._blocked_accounts[identifier]
            logger.info(f"账户禁用已手动解除: identifier={identifier}")
    
    def clear_expired(self):
        """清理过期的验证码"""
        now = datetime.now()
        expired_keys = [
            key for key, data in self._store.items()
            if now > data['expire_time']
        ]
        for key in expired_keys:
            del self._store[key]
        
        if expired_keys:
            logger.info(f"清理过期验证码: {len(expired_keys)}个")


# 全局验证码存储实例
captcha_store = CaptchaStore()


def generate_captcha_code(length: int = 4) -> str:
    """生成随机验证码
    
    Args:
        length: 验证码长度
        
    Returns:
        验证码字符串
    """
    # 排除容易混淆的字符：0O、1Il
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('l', '')
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(code: str, width: int = 120, height: int = 40) -> BytesIO:
    """生成验证码图片
    
    Args:
        code: 验证码文本
        width: 图片宽度
        height: 图片高度
        
    Returns:
        图片的BytesIO对象
    """
    # 创建图片
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 绘制背景干扰线
    for _ in range(random.randint(3, 5)):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(
            random.randint(180, 220),
            random.randint(180, 220),
            random.randint(180, 220)
        ), width=1)
    
    # 绘制验证码文本
    try:
        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            except:
                # 使用默认字体
                font = ImageFont.load_default()
    except Exception as e:
        logger.warning(f"加载字体失败: {e}")
        font = ImageFont.load_default()
    
    # 计算文本位置
    char_width = width // len(code)
    for i, char in enumerate(code):
        x = char_width * i + random.randint(5, 10)
        y = random.randint(5, 10)
        # 随机颜色
        color = (
            random.randint(20, 100),
            random.randint(20, 100),
            random.randint(20, 100)
        )
        draw.text((x, y), char, fill=color, font=font)
    
    # 添加干扰点
    for _ in range(random.randint(50, 100)):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(
            random.randint(150, 200),
            random.randint(150, 200),
            random.randint(150, 200)
        ))
    
    # 应用滤镜（稍微模糊）
    image = image.filter(ImageFilter.SMOOTH)
    
    # 保存到BytesIO
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def create_captcha(identifier: str) -> Tuple[str, BytesIO]:
    """创建验证码（生成验证码并保存）
    
    Args:
        identifier: 用户标识（用于存储验证码）
        
    Returns:
        (验证码文本, 验证码图片BytesIO)
    """
    code = generate_captcha_code()
    captcha_store.set_captcha(identifier, code)
    image = generate_captcha_image(code)
    return code, image
