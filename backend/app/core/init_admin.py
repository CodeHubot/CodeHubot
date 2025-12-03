"""
管理员账号初始化模块
在应用启动时自动创建管理员账号（如果不存在）
"""
import logging
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

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
    
    # 如果没有设置密码，跳过初始化
    if not admin_password:
        logger.info("⚠️  未设置 ADMIN_PASSWORD 环境变量，跳过管理员账号初始化")
        return False
    
    # 检查管理员账号是否已存在（通过用户名或邮箱）
    existing_user = db.query(User).filter(
        (User.username == admin_username) | (User.email == admin_email)
    ).first()
    
    if existing_user:
        logger.info(f"ℹ️  管理员账号已存在: {admin_username} (ID: {existing_user.id})")
        # 如果账号存在但不是管理员角色，更新为管理员
        if existing_user.role != 'platform_admin':
            existing_user.role = 'platform_admin'
            db.commit()
            logger.info(f"✅ 已更新用户角色为平台管理员: {admin_username}")
        return True
    
    # 创建管理员账号
    try:
        hashed_password = get_password_hash(admin_password)
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            role='platform_admin',  # 平台管理员角色
            is_active=True,
            school_id=None  # 平台管理员不属于任何学校
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✅ 管理员账号创建成功: {admin_username} (邮箱: {admin_email}, ID: {admin_user.id})")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建管理员账号失败: {e}", exc_info=True)
        return False


def init_admin_on_startup():
    """
    应用启动时初始化管理员账号
    """
    try:
        db = SessionLocal()
        try:
            init_admin_user(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ 初始化管理员账号时发生错误: {e}", exc_info=True)

