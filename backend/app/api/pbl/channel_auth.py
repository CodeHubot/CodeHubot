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

# ===== 已废弃的渠道商登录接口（2024-12-24）=====
# 系统已统一使用 /api/auth/login 作为唯一登录接口
# 原登录接口已删除
# ============================================

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
