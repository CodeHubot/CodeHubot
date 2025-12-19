from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging
import hashlib
from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文 - 支持bcrypt和pbkdf2_sha256算法（与CodeHubot-PBL系统保持一致）
# bcrypt 用于新密码（更安全），pbkdf2_sha256 用于兼容旧密码
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto"
)

def _preprocess_password(password: str) -> str:
    """预处理密码以适应 bcrypt 的 72 字节限制
    
    使用 SHA256 对密码进行预哈希，然后转换为十六进制字符串。
    这样可以接受任意长度的密码，同时保持在 bcrypt 的限制范围内。
    
    Args:
        password: 原始密码
        
    Returns:
        str: 预处理后的密码（64个十六进制字符）
    """
    # 使用 SHA256 哈希密码，输出为十六进制字符串（64字符，远小于72字节）
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    try:
        # 先预处理密码，然后验证
        preprocessed = _preprocess_password(plain_password)
        
        # 方案1: 先尝试预处理后的密码（新密码）
        if pwd_context.verify(preprocessed, hashed_password):
            logger.debug(f"✅ 密码验证成功（使用预处理）")
            return True
        
        # 方案2: 尝试原始密码（兼容旧数据）
        if pwd_context.verify(plain_password, hashed_password):
            logger.debug(f"✅ 密码验证成功（使用原始密码）")
            return True
        
        logger.debug(f"❌ 密码验证失败（两种方式都不匹配）")
        return False
    except Exception as e:
        logger.error(f"密码验证异常: {e}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: �ashed后的密码
        
    Note:
        使用 SHA256 预处理密码以支持任意长度的密码。
        bcrypt 4.0+ 版本会自动处理超过 72 字节的密码。
    """
    try:
        # 先用 SHA256 预处理密码，支持任意长度的密码输入
        preprocessed = _preprocess_password(password)
        # SHA256 hex 输出固定为 64 字符（64 字节），安全地在 bcrypt 限制范围内
        return pwd_context.hash(preprocessed)
    except Exception as e:
        logger.error(f"密码哈希失败: {e}", exc_info=True)
        raise ValueError(f"密码哈希失败: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建access token
    
    注意：如果 data 中已包含 "type" 字段，将使用该值，否则默认为 "access"
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # 如果 data 中没有 type 字段，才设置为 "access"
    if "type" not in to_encode:
        to_encode["type"] = "access"
    
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建refresh token
    
    Args:
        data: token中包含的数据
        expires_delta: 自定义过期时间
        
    Returns:
        str: 编码后的JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: Optional[str] = "access") -> dict:
    """验证token
    
    Args:
        token: JWT token
        token_type: token类型（access、refresh、password_reset 等）。如果为 None，则不验证类型
        
    Returns:
        dict: token payload
        
    Raises:
        HTTPException: token无效或类型不匹配
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # 如果指定了 token_type，验证类型是否匹配
        if token_type is not None:
            payload_type = payload.get("type")
            if payload_type != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"无效的token类型，期望: {token_type}，实际: {payload_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return payload
    except HTTPException:
        # 重新抛出 HTTPException（类型不匹配）
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_internal_api_key(api_key: str) -> bool:
    """验证内部API密钥
    
    用于内部服务（如plugin-service）调用后端API时的认证
    
    Args:
        api_key: 内部API密钥
        
    Returns:
        bool: 密钥是否有效
    """
    # 从配置中获取内部API密钥
    internal_api_key = getattr(settings, 'internal_api_key', None)
    
    # 如果未配置内部API密钥，则不允许访问
    if not internal_api_key:
        logger.warning("未配置内部API密钥，拒绝访问")
        return False
    
    # 验证密钥是否匹配
    return api_key == internal_api_key
