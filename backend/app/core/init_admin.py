"""
管理员账号初始化模块
在应用启动时自动创建管理员账号（如果不存在）
"""
import logging
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

# 加载 .env 文件
load_dotenv()

logger = logging.getLogger(__name__)


def init_admin_user(db: Session) -> bool:
    """
    初始化管理员账号
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 是否成功创建或已存在
    """
    # 从环境变量读取管理员配置
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_email = os.getenv("ADMIN_EMAIL", f"{admin_username}@aiot.com")
    
    # 记录配置信息（不记录密码）
    logger.info(f"📋 管理员配置读取: username={admin_username}, email={admin_email}, has_password={bool(admin_password)}")
    
    # 如果没有设置密码，跳过初始化
    if not admin_password:
        logger.warning("⚠️  未设置 ADMIN_PASSWORD 环境变量，跳过管理员账号初始化")
        logger.warning("⚠️  请在 .env 文件中设置 ADMIN_PASSWORD 以自动创建管理员账号")
        return False
    
    # 检查管理员账号是否已存在（通过用户名或邮箱）
    try:
        logger.info(f"🔍 检查管理员账号是否存在: username={admin_username}, email={admin_email}")
        existing_user = db.query(User).filter(
            (User.username == admin_username) | (User.email == admin_email)
        ).first()
        
        if existing_user:
            logger.info(f"ℹ️  管理员账号已存在: {admin_username} (ID: {existing_user.id}, role: {existing_user.role})")
            # 如果账号存在但不是管理员角色，更新为管理员
            if existing_user.role != 'platform_admin':
                logger.info(f"🔄 更新用户角色为平台管理员: {admin_username}")
                existing_user.role = 'platform_admin'
                db.commit()
                logger.info(f"✅ 已更新用户角色为平台管理员: {admin_username}")
            return True
    except Exception as e:
        logger.error(f"❌ 检查管理员账号时发生错误: {e}", exc_info=True)
        raise
    
    # 创建管理员账号
    try:
        logger.info(f"🔐 开始创建管理员账号: username={admin_username}, email={admin_email}")
        hashed_password = get_password_hash(admin_password)
        logger.debug(f"✅ 密码哈希生成成功")
        
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            role='platform_admin',  # 平台管理员角色
            is_active=True,
            team_id=None  # 平台管理员不属于任何团队
        )
        logger.debug(f"✅ 管理员用户对象创建成功")
        
        db.add(admin_user)
        logger.debug(f"✅ 管理员用户已添加到会话")
        
        db.commit()
        logger.debug(f"✅ 数据库事务提交成功")
        
        db.refresh(admin_user)
        logger.info(f"✅ 管理员账号创建成功: {admin_username} (邮箱: {admin_email}, ID: {admin_user.id})")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建管理员账号失败: {e}", exc_info=True)
        logger.error(f"❌ 失败详情 - username: {admin_username}, email: {admin_email}")
        raise  # 抛出异常以便更好地调试


def init_admin_on_startup():
    """
    应用启动时初始化管理员账号
    """
    logger.info("=" * 60)
    logger.info("🚀 开始初始化管理员账号...")
    logger.info("=" * 60)
    
    db = None
    try:
        logger.info("📡 创建数据库会话...")
        db = SessionLocal()
        logger.info("✅ 数据库会话创建成功")
        
        result = init_admin_user(db)
        if result:
            logger.info("✅ 管理员账号初始化完成")
        else:
            logger.info("⚠️  管理员账号初始化跳过")
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ 初始化管理员账号时发生错误: {type(e).__name__}: {e}", exc_info=True)
        logger.error("=" * 60)
        logger.error("⚠️  应用将继续启动，但管理员账号未创建！")
        logger.error("⚠️  请检查以下内容：")
        logger.error("   1. 数据库连接是否正常")
        logger.error("   2. core_users 表是否存在")
        logger.error("   3. ADMIN_PASSWORD 环境变量是否已设置")
        logger.error("   4. 数据库用户是否有INSERT权限")
        logger.error("=" * 60)
    finally:
        if db:
            db.close()
            logger.debug("✅ 数据库会话已关闭")
    
    logger.info("=" * 60)

