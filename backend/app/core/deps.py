"""
依赖注入模块
提供FastAPI路由所需的依赖项
"""
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.database import get_db as _get_db
from app.core.security import verify_token, verify_internal_api_key
from app.models.user import User
import logging

# Note: Admin 和 User 实际上是同一个表 (core_users)，只是不同的ORM类
# 为了避免 SQLAlchemy 报错，这里只使用 User 类，通过 role 字段区分
Admin = User  # Admin 是 User 的别名

logger = logging.getLogger(__name__)

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

# 导出 get_db
get_db = _get_db


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（仅限User表）
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 查询用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # 检查用户是否被禁用
    if not user.is_active:
        logger.warning(f"用户尝试使用已禁用的账户: {user.email} (ID: {user.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return user


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """获取当前管理员（仅限Admin表）
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Admin: 当前管理员对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 查询管理员
    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    if admin is None:
        raise credentials_exception
    
    # 检查管理员是否被禁用
    if not admin.is_active:
        logger.warning(f"管理员尝试使用已禁用的账户: {admin.username} (ID: {admin.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return admin


async def get_current_user_flexible(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Union[User, Admin]:
    """灵活获取当前用户（支持User和Admin表）
    
    根据token中的user_role字段决定从哪个表查询用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Union[User, Admin]: 用户或管理员对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        user_role: str = payload.get("user_role", "student")  # 默认为student
        
        if user_id is None:
            raise credentials_exception
            
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 根据角色查询不同的表
    if user_role in ['platform_admin', 'team_admin', 'teacher']:
        # 从Admin表查询
        user = db.query(Admin).filter(Admin.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        
        # 检查管理员是否被禁用
        if not user.is_active:
            logger.warning(f"管理员尝试使用已禁用的账户: {user.username} (ID: {user.id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
    else:
        # 从User表查询
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        
        # 检查用户是否被禁用
        if not user.is_active:
            logger.warning(f"用户尝试使用已禁用的账户: {user.email or user.username} (ID: {user.id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
    
    return user


async def verify_internal_or_user(
    request: Request,
    x_internal_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Union[User, str]:
    """验证内部API密钥或JWT token
    
    优先级：
    1. X-Internal-API-Key header（用于内部服务）
    2. Authorization header with Bearer token（用于用户认证）
    
    Args:
        request: FastAPI请求对象
        x_internal_api_key: 内部API密钥（从header获取）
        db: 数据库会话
        
    Returns:
        Union[User, str]: 用户对象或字符串"internal"
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    # 1. 优先检查内部API密钥
    if x_internal_api_key:
        try:
            verify_internal_api_key(x_internal_api_key)
            logger.info("内部API密钥验证成功")
            return "internal"
        except HTTPException:
            logger.warning("内部API密钥验证失败")
            pass  # 继续尝试JWT token验证
    
    # 2. 检查JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            user = await get_current_user(token=token, db=db)
            logger.info(f"用户Token验证成功: {user.email} (ID: {user.id})")
            return user
        except HTTPException:
            logger.warning("用户Token验证失败")
            raise
    
    # 3. 都没有，抛出未授权异常
    logger.warning("未提供有效的认证凭据")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="需要认证",
        headers={"WWW-Authenticate": "Bearer"},
    )


# 可选的用户依赖（允许未认证访问）
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，允许为None）
    
    Args:
        token: JWT token（可选）
        db: 数据库会话
        
    Returns:
        Optional[User]: 用户对象或None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


async def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """获取当前教师用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Admin: 教师用户对象
        
    Raises:
        HTTPException: 认证失败或权限不足时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 查询教师用户
    teacher = db.query(Admin).filter(Admin.id == int(user_id)).first()
    if teacher is None:
        raise credentials_exception
    
    # 检查是否为教师角色
    if teacher.role != 'teacher':
        logger.warning(f"用户 {teacher.username} (ID: {teacher.id}) 尝试访问教师接口，但角色为 {teacher.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    
    # 检查教师是否被禁用
    if not teacher.is_active:
        logger.warning(f"教师尝试使用已禁用的账户: {teacher.username} (ID: {teacher.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return teacher


async def get_current_user_or_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Union[User, Admin]:
    """获取当前用户或管理员（支持所有角色）
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Union[User, Admin]: 用户或管理员对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        user_role: str = payload.get("user_role", "student")
        
        if user_id is None:
            raise credentials_exception
            
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 根据角色查询不同的表
    if user_role in ['platform_admin', 'team_admin', 'channel_manager', 'channel_partner', 'teacher']:
        # 从Admin表查询
        user = db.query(Admin).filter(Admin.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        
        # 检查管理员是否被禁用
        if not user.is_active:
            logger.warning(f"管理员尝试使用已禁用的账户: {user.username} (ID: {user.id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
    else:
        # 从User表查询
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        
        # 检查用户是否被禁用
        if not user.is_active:
            logger.warning(f"用户尝试使用已禁用的账户: {user.email or user.username} (ID: {user.id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
    
    return user


async def get_current_channel_partner(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """获取当前渠道商用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Admin: 渠道商用户对象
        
    Raises:
        HTTPException: 认证失败或权限不足时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 查询渠道商用户
    channel_partner = db.query(Admin).filter(Admin.id == int(user_id)).first()
    if channel_partner is None:
        raise credentials_exception
    
    # 检查是否为渠道商角色
    if channel_partner.role != 'channel_partner':
        logger.warning(f"用户 {channel_partner.username} (ID: {channel_partner.id}) 尝试访问渠道商接口，但角色为 {channel_partner.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要渠道商权限"
        )
    
    # 检查渠道商是否被禁用
    if not channel_partner.is_active:
        logger.warning(f"渠道商尝试使用已禁用的账户: {channel_partner.username} (ID: {channel_partner.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return channel_partner


async def get_current_channel_manager(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """获取当前渠道管理员用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        Admin: 渠道管理员用户对象
        
    Raises:
        HTTPException: 认证失败或权限不足时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception
    
    # 查询渠道管理员用户
    channel_manager = db.query(Admin).filter(Admin.id == int(user_id)).first()
    if channel_manager is None:
        raise credentials_exception
    
    # 检查是否为渠道管理员或平台管理员角色
    if channel_manager.role not in ['channel_manager', 'platform_admin']:
        logger.warning(f"用户 {channel_manager.username} (ID: {channel_manager.id}) 尝试访问渠道管理接口，但角色为 {channel_manager.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要渠道管理员权限"
        )
    
    # 检查管理员是否被禁用
    if not channel_manager.is_active:
        logger.warning(f"渠道管理员尝试使用已禁用的账户: {channel_manager.username} (ID: {channel_manager.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return channel_manager
