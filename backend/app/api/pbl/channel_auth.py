from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.security import verify_password, create_access_token, create_refresh_token, verify_token
from ...core.deps import get_db, get_current_channel_partner
from ...core.logging_config import get_logger
from ...schemas.user import UserResponse, RefreshTokenRequest
from ...models.admin import Admin
from ...utils.timezone import get_beijing_time_naive

router = APIRouter()
logger = get_logger(__name__)

class ChannelLoginRequest(BaseModel):
    """渠道商登录请求"""
    username: str
    password: str

@router.post("/login")
def channel_login(login_data: ChannelLoginRequest, db: Session = Depends(get_db)):
    """渠道商用户登录 - 使用账号+密码登录"""
    logger.info(f"收到渠道商登录请求 - 账号: {login_data.username}")
    
    # 1. 查找渠道商用户（role为channel_partner）
    channel_partner = db.query(Admin).filter(
        Admin.username == login_data.username,
        Admin.role == 'channel_partner'
    ).first()
    
    if not channel_partner:
        logger.warning(f"渠道商登录失败：用户不存在或角色不匹配 - {login_data.username}")
        return error_response(
            message="账号或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"找到渠道商 - ID: {channel_partner.id}, 用户名: {channel_partner.username}, 激活状态: {channel_partner.is_active}")
    
    # 2. 验证密码
    logger.debug(f"验证渠道商 {login_data.username} 的密码...")
    password_valid = verify_password(login_data.password, channel_partner.password_hash)
    
    if not password_valid:
        logger.warning(f"渠道商登录失败 - 账号 {login_data.username} 密码错误")
        return error_response(
            message="账号或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"渠道商 {login_data.username} 密码验证通过")
    
    # 3. 检查账户状态
    if not channel_partner.is_active:
        logger.warning(f"渠道商登录失败 - 账号 {login_data.username} 已被禁用")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 4. 更新最后登录时间
    channel_partner.last_login = get_beijing_time_naive()
    db.commit()
    logger.debug(f"已更新渠道商 {login_data.username} 的最后登录时间")
    
    # 5. 创建访问令牌和刷新令牌（标记为channel_portal）
    access_token = create_access_token(data={"sub": str(channel_partner.id), "user_role": "channel_partner", "portal": "channel"})
    refresh_token = create_refresh_token(data={"sub": str(channel_partner.id), "user_role": "channel_partner", "portal": "channel"})
    
    logger.info(f"✅ 渠道商登录成功: {channel_partner.username} (ID: {channel_partner.id})")
    
    # 将 Admin 模型转换为 UserResponse schema
    channel_response = UserResponse.model_validate(channel_partner)
    
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": channel_response.model_dump(mode='json')
        },
        message="登录成功"
    )

@router.get("/me")
def get_current_channel_info(current_channel: Admin = Depends(get_current_channel_partner)):
    """获取当前渠道商信息（需要认证）"""
    logger.debug(f"获取渠道商信息 - 用户名: {current_channel.username}, ID: {current_channel.id}")
    
    channel_response = UserResponse.model_validate(current_channel)
    return success_response(data=channel_response.model_dump(mode='json'))

@router.post("/refresh")
def refresh_channel_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用refresh token刷新access token（渠道商端）
    """
    logger.info("收到渠道商刷新令牌请求")
    
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException as e:
        logger.warning(f"渠道商刷新令牌验证失败: {str(e)}")
        return error_response(
            message="无效的刷新令牌或已过期",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    channel_id = payload.get("sub")
    user_role = payload.get("user_role")
    portal = payload.get("portal")
    
    if channel_id is None or portal != "channel":
        logger.warning("刷新令牌中没有渠道商ID或portal标记错误")
        return error_response(
            message="无效的刷新令牌",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"渠道商刷新令牌解析 - 渠道商ID: {channel_id}")
    
    # 验证渠道商是否存在
    channel_partner = db.query(Admin).filter(
        Admin.id == int(channel_id),
        Admin.role == 'channel_partner'
    ).first()
    
    if channel_partner is None:
        logger.warning(f"刷新令牌失败 - 渠道商不存在: {channel_id}")
        return error_response(
            message="渠道商不存在",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    if not channel_partner.is_active:
        logger.warning(f"刷新令牌失败 - 渠道商账户已禁用: {channel_partner.username}")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 生成新的tokens
    new_access_token = create_access_token(data={"sub": str(channel_partner.id), "user_role": "channel_partner", "portal": "channel"})
    new_refresh_token = create_refresh_token(data={"sub": str(channel_partner.id), "user_role": "channel_partner", "portal": "channel"})
    
    logger.info(f"渠道商令牌刷新成功 - 用户: {channel_partner.username} (ID: {channel_partner.id})")
    
    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        },
        message="令牌刷新成功"
    )
