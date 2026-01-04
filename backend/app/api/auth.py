from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import timedelta, datetime
from pydantic import BaseModel, Field
from typing import Optional, Union
import logging
from app.core.database import get_db
from app.models.user import User
from app.utils.timezone import get_beijing_time_naive
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, LoginResponse,
    PasswordResetRequest, PasswordResetConfirm,
    ChangePasswordRequest, UpdateProfileRequest
)
from app.core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token, verify_token,
    verify_internal_api_key
)
from app.core.response import success_response
from app.core.constants import (
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    ErrorMessages, SuccessMessages
)
from app.core.config import settings
from app.services.email import send_welcome_email, send_password_reset_email
from app.utils.captcha import captcha_store, create_captcha

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter()

# 验证码相关的常量
LOGIN_ATTEMPT_THRESHOLD = 3  # 登录失败次数阈值，超过此次数需要验证码
BLOCK_THRESHOLD = 5  # 登录失败次数阈值，超过此次数临时禁用账户
BLOCK_DURATION_MINUTES = 3  # 账户禁用时长（分钟）

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册 - 增强输入验证和事务管理（邮箱可选）"""
    try:
        # ===== 检查是否开启用户注册功能 =====
        from app.models.system_config import SystemConfig
        registration_config = db.query(SystemConfig).filter(
            SystemConfig.config_key == "enable_user_registration"
        ).first()
        
        # 如果配置存在且为 false，则禁止注册
        if registration_config and registration_config.config_value.lower() in ('false', '0', 'no'):
            logger.warning(f"注册失败：用户注册功能已关闭")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户注册功能已关闭，请联系管理员"
            )
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if user_data.email:
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                logger.warning(f"注册失败：邮箱已存在 - {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessages.EMAIL_EXISTS
                )
        
        # 检查用户名是否已存在
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            logger.warning(f"注册失败：用户名已存在 - {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.USERNAME_EXISTS
            )
        
        # 创建用户（默认为独立用户）
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email or None,  # 空字符串转为 None，避免唯一索引冲突
            username=user_data.username,
            password_hash=hashed_password,
            role='individual',  # 默认为独立用户
            school_id=None  # 独立用户不属于任何学校
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"✅ 用户注册成功: {user_data.username} (邮箱: {user_data.email or '未提供'}) (ID: {db_user.id})")
        
        # 发送欢迎邮件（已禁用，避免 SSL 证书验证问题）
        # if user_data.email:
        #     try:
        #         await send_welcome_email(user_data.email, user_data.username)
        #         logger.info(f"欢迎邮件已发送: {user_data.email}")
        #     except Exception as e:
        #         logger.warning(f"发送欢迎邮件失败: {e}", exc_info=True)
        #         # 邮件发送失败不影响注册流程
        
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 用户注册失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录 - 支持用户名或邮箱登录，失败3次后需要验证码，失败5次后临时禁用30分钟"""
    try:
        # 查找用户（支持用户名或邮箱）
        login_identifier = login_data.email  # 这个字段现在可以是用户名或邮箱
        
        # 0. 检查账户是否被临时禁用
        if captcha_store.is_account_blocked(login_identifier, BLOCK_DURATION_MINUTES):
            remaining_seconds = captcha_store.get_block_remaining_time(login_identifier, BLOCK_DURATION_MINUTES)
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"登录失败：账户已被临时禁用 - {login_identifier}，剩余 {remaining_minutes} 分钟")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"由于多次登录失败，账户已被临时禁用。请在 {remaining_minutes} 分钟后重试"
            )
        
        # 1. 检查是否需要验证码，如果需要则先验证验证码
        login_attempts = captcha_store.get_login_attempts(login_identifier)
        if login_attempts >= LOGIN_ATTEMPT_THRESHOLD:
            # 需要验证码
            if not login_data.captcha_code:
                logger.warning(f"登录失败：需要验证码 - {login_identifier}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="请输入验证码"
                )
            
            # 先验证验证码（验证码错误也要记录失败次数）
            if not captcha_store.verify_captcha(login_identifier, login_data.captcha_code):
                # 验证码错误，记录失败次数
                captcha_store.record_login_attempt(login_identifier)
                current_attempts = captcha_store.get_login_attempts(login_identifier)
                logger.warning(f"登录失败：验证码错误 - {login_identifier} (失败次数: {current_attempts})")
                
                # 检查是否达到禁用阈值
                if current_attempts >= BLOCK_THRESHOLD:
                    captcha_store.block_account(login_identifier)
                    logger.error(f"⚠️ 账户已被临时禁用: {login_identifier}，禁用时长: {BLOCK_DURATION_MINUTES}分钟")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"由于多次登录失败，账户已被临时禁用 {BLOCK_DURATION_MINUTES} 分钟"
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"验证码错误（还有{BLOCK_THRESHOLD - current_attempts}次机会后将被禁用{BLOCK_DURATION_MINUTES}分钟）"
                )
        
        # 2. 验证码通过（或不需要验证码），再查找用户并验证密码
        # 先尝试按邮箱查找
        user = db.query(User).filter(User.email == login_identifier).first()
        
        # 如果没找到，再尝试按用户名查找
        if not user:
            user = db.query(User).filter(User.username == login_identifier).first()
        
        # 3. 验证用户和密码
        logger.info(f"🔍 开始验证密码 - 用户: {login_identifier}")
        if user:
            logger.debug(f"找到用户: {user.username} (ID: {user.id})")
            logger.debug(f"密码哈希前缀: {user.password_hash[:20]}...")
        
        if not user or not verify_password(login_data.password, user.password_hash):
            # 记录登录失败次数
            captcha_store.record_login_attempt(login_identifier)
            current_attempts = captcha_store.get_login_attempts(login_identifier)
            
            logger.warning(f"登录失败：用户名/邮箱或密码错误 - {login_identifier} (失败次数: {current_attempts})")
            
            # 检查是否达到禁用阈值
            if current_attempts >= BLOCK_THRESHOLD:
                captcha_store.block_account(login_identifier)
                logger.error(f"⚠️ 账户已被临时禁用: {login_identifier}，禁用时长: {BLOCK_DURATION_MINUTES}分钟")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"由于多次登录失败，账户已被临时禁用 {BLOCK_DURATION_MINUTES} 分钟"
                )
            
            # 如果失败次数达到验证码阈值，提示需要验证码
            if current_attempts >= LOGIN_ATTEMPT_THRESHOLD:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"用户名/邮箱或密码错误（还有{BLOCK_THRESHOLD - current_attempts}次机会后将被禁用{BLOCK_DURATION_MINUTES}分钟）"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"用户名/邮箱或密码错误（还有{LOGIN_ATTEMPT_THRESHOLD - current_attempts}次机会需要输入验证码）"
                )
        
        # 4. 检查账户状态
        if not user.is_active:
            logger.warning(f"登录失败：账户已禁用 - {login_identifier}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.ACCOUNT_DISABLED
            )
        
        # 5. 登录成功，重置失败次数和解除禁用
        captcha_store.reset_login_attempts(login_identifier)
        captcha_store.unblock_account(login_identifier)
        
        # 6. 更新最后登录时间
        user.last_login = get_beijing_time_naive()
        db.commit()
        
        # 7. 生成访问令牌和刷新令牌
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        logger.info(f"✅ 用户登录成功: {user.username} ({user.email}) (ID: {user.id})")
        logger.info(f"🔑 Token有效期 - Access: {settings.access_token_expire_minutes}分钟, Refresh: {settings.refresh_token_expire_minutes}分钟")
        
        # 使用UserResponse序列化用户信息，确保不返回password_hash
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,  # 转换为秒
            user=UserResponse.model_validate(user)  # 使用UserResponse确保不返回敏感信息
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 用户登录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证 access token（默认类型）
        payload = verify_token(token, token_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        # 重新抛出 HTTPException（token 类型不匹配或已过期）
        raise
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # 检查用户是否被禁用
    if not user.is_active:
        logger.warning(f"用户尝试使用已禁用的账户: {user.email} (ID: {user.id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.ACCOUNT_DISABLED
        )
    
    return user


@router.get("/captcha")
async def get_captcha(identifier: str):
    """获取验证码图片
    
    Args:
        identifier: 用户标识（用户名或邮箱）
        
    Returns:
        验证码图片（PNG格式）
    """
    try:
        _, image = create_captcha(identifier)
        return StreamingResponse(image, media_type="image/png")
    except Exception as e:
        logger.error(f"❌ 生成验证码失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成验证码失败"
        )


@router.get("/login-attempts/{identifier}")
async def get_login_attempts(identifier: str):
    """查询登录失败次数
    
    Args:
        identifier: 用户标识（用户名或邮箱）
        
    Returns:
        登录失败次数和是否需要验证码
    """
    try:
        attempts = captcha_store.get_login_attempts(identifier)
        needs_captcha = attempts >= LOGIN_ATTEMPT_THRESHOLD
        
        return success_response(data={
            "attempts": attempts,
            "needs_captcha": needs_captcha,
            "threshold": LOGIN_ATTEMPT_THRESHOLD
        })
    except Exception as e:
        logger.error(f"❌ 查询登录失败次数失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询失败"
        )


async def verify_internal_or_user(
    request: Request,
    x_internal_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Union[User, str]:
    """验证内部API密钥或JWT token
    
    优先级：
    1. X-Internal-API-Key header（用于内部服务）
    2. Authorization header（用于用户请求）
    
    Returns:
        User对象（JWT认证）或 "internal"（内部API密钥认证）
        
    Raises:
        HTTPException: 认证失败
    """
    # 1. 检查内部API密钥
    if x_internal_api_key:
        if verify_internal_api_key(x_internal_api_key):
            logger.info("✅ 内部API密钥验证通过")
            return "internal"  # 返回特殊标识表示内部服务
        else:
            logger.warning("❌ 内部API密钥无效")
            # 继续尝试JWT认证
    
    # 2. 尝试JWT token认证
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            payload = verify_token(token)
            user_id: str = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    logger.info(f"✅ JWT认证通过: user_id={user_id}")
                    return user
        except JWTError:
            pass
    
    # 3. 都失败了，返回401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="需要有效的认证凭据（JWT token 或 内部API密钥）",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/request-password-reset")
async def request_password_reset(
    reset_request: PasswordResetRequest, 
    db: Session = Depends(get_db)
):
    """请求密码重置 - 发送重置邮件"""
    try:
        # 查找用户
        user = db.query(User).filter(User.email == reset_request.email).first()
        
        # 不暴露用户是否存在（安全最佳实践）
        if not user:
            logger.info(f"密码重置请求：用户不存在 - {reset_request.email}")
            return success_response(
                message="如果该邮箱已注册，重置链接将发送到您的邮箱"
            )
        
        # 生成重置令牌（30分钟有效）
        reset_token = create_access_token(
            data={
                "sub": str(user.id),
                "type": "password_reset",
                "email": user.email
            },
            expires_delta=timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )
        
        # 发送密码重置邮件
        try:
            await send_password_reset_email(user.email, reset_token)
            logger.info(f"✅ 密码重置邮件已发送: {user.email}")
        except Exception as e:
            logger.error(f"发送密码重置邮件失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送重置邮件失败，请稍后重试"
            )
        
        return success_response(
            data={
                "expires_in": PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            },
            message="密码重置链接已发送到您的邮箱"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 密码重置请求失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )

@router.post("/reset-password")
async def reset_password(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """确认密码重置 - 验证token并更新密码"""
    try:
        # 验证重置令牌
        try:
            # 指定 token_type 为 "password_reset" 进行验证
            payload = verify_token(reset_confirm.token, token_type="password_reset")
            user_id = payload.get("sub")
            
            if not user_id:
                logger.warning(f"密码重置失败：令牌中缺少用户ID")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的重置令牌"
                )
                
        except HTTPException:
            # 重新抛出 HTTPException（类型不匹配或已过期）
            raise
        except JWTError as e:
            logger.warning(f"密码重置失败：令牌验证失败 - {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置令牌无效或已过期"
            )
        
        # 查找用户
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.error(f"密码重置失败：用户不存在 - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorMessages.USER_NOT_FOUND
            )
        
        # 更新密码
        user.password_hash = get_password_hash(reset_confirm.new_password)
        db.commit()
        
        logger.info(f"✅ 密码重置成功: {user.email} (ID: {user.id})")
        
        return success_response(
            message=SuccessMessages.PASSWORD_RESET_SUCCESS
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 密码重置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )

class RefreshTokenRequest(BaseModel):
    """刷新Token请求模型"""
    refresh_token: str

@router.post("/refresh")
async def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """使用refresh token获取新的access token
    
    Args:
        request: 包含refresh_token的请求体
        
    Returns:
        新的access token和refresh token
    """
    try:
        # 验证refresh token（verify_token 会自动检查过期时间）
        try:
            payload = verify_token(request.refresh_token, token_type="refresh")
        except HTTPException as e:
            # refresh token 无效或已过期
            logger.warning(f"Refresh token验证失败: {e.detail}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token无效或已过期，请重新登录"
            )
        
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.warning("Refresh token中缺少用户ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的refresh token"
            )
        
        # 验证用户是否存在且活跃
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"Refresh token失败：用户不存在 - ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        if not user.is_active:
            logger.warning(f"Refresh token失败：账户已禁用 - {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorMessages.ACCOUNT_DISABLED
            )
        
        # 生成新的access token和refresh token
        token_data = {"sub": str(user.id)}
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)
        
        logger.info(f"🔄 Token刷新成功: {user.username} ({user.email}) (ID: {user.id})")
        
        return success_response(
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60  # 转换为秒
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token刷新失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token刷新失败，请稍后重试"
        )

@router.get("/user-info")
async def get_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息（支持所有角色）"""
    logger.debug(f"获取用户信息 - 用户名: {current_user.username}, ID: {current_user.id}, 角色: {current_user.role}")
    
    user_response = UserResponse.model_validate(current_user)
    response_data = user_response.model_dump(mode='json')
    
    # 如果用户关联了学校，返回学校信息
    if current_user.school_id:
        from app.models.school import School
        school = db.query(School).filter(School.id == current_user.school_id).first()
        if school:
            response_data['school'] = {
                "id": school.id,
                "uuid": school.uuid,
                "school_code": school.school_code,
                "school_name": school.school_name
            }
            response_data['school_uuid'] = school.uuid  # 兼容旧版API
    
    return success_response(data=response_data)

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码 - 需要验证旧密码"""
    try:
        # 验证旧密码
        logger.info(f"🔍 开始验证旧密码 - 用户: {current_user.username} (ID: {current_user.id})")
        logger.debug(f"密码哈希前缀: {current_user.password_hash[:20]}...")
        
        if not verify_password(password_data.old_password, current_user.password_hash):
            logger.warning(f"修改密码失败：旧密码错误 - 用户ID: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 更新密码
        current_user.password_hash = get_password_hash(password_data.new_password)
        
        # 清除强制修改密码标志
        if current_user.need_change_password:
            current_user.need_change_password = False
            logger.info(f"✅ 清除首次登录修改密码标志: {current_user.username} (ID: {current_user.id})")
        
        db.commit()
        
        logger.info(f"✅ 密码修改成功: {current_user.username} (ID: {current_user.id})")
        
        return success_response(message="密码修改成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 修改密码失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败，请稍后重试"
        )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改个人信息 - 邮箱、用户名和昵称"""
    try:
        # 检查是否有更新内容
        if profile_data.email is None and profile_data.username is None and profile_data.nickname is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供要更新的信息"
            )
        
        # 更新邮箱
        if profile_data.email is not None:
            # 检查邮箱是否已被其他用户使用
            existing_user = db.query(User).filter(
                User.email == profile_data.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                logger.warning(f"修改邮箱失败：邮箱已被使用 - {profile_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被使用"
                )
            current_user.email = profile_data.email
        
        # 更新用户名
        if profile_data.username is not None:
            # 检查用户名是否已被其他用户使用
            existing_user = db.query(User).filter(
                User.username == profile_data.username,
                User.id != current_user.id
            ).first()
            if existing_user:
                logger.warning(f"修改用户名失败：用户名已被使用 - {profile_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该用户名已被使用"
                )
            current_user.username = profile_data.username
        
        # 更新昵称
        if profile_data.nickname is not None:
            current_user.nickname = profile_data.nickname
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"✅ 个人信息修改成功: {current_user.username} (ID: {current_user.id})")
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 修改个人信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改个人信息失败，请稍后重试"
        )


