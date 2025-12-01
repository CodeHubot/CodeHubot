from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import timedelta, datetime
from pydantic import BaseModel
from typing import Optional, Union
import logging
from app.core.database import get_db
from app.models.user import User
from app.models.school import School
from app.utils.timezone import get_beijing_time_naive
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, LoginResponse,
    PasswordResetRequest, PasswordResetConfirm,
    ChangePasswordRequest, UpdateProfileRequest
)
from app.schemas.user_management import InstitutionLoginRequest
from app.core.security import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token, verify_token,
    verify_internal_api_key
)
from app.core.constants import (
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    ErrorMessages, SuccessMessages
)
from app.core.config import settings
from app.services.email import send_welcome_email, send_password_reset_email

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册 - 增强输入验证和事务管理（邮箱可选）"""
    try:
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
            email=user_data.email,  # 可以是 None
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
    """用户登录 - 支持用户名或邮箱登录"""
    try:
        # 查找用户（支持用户名或邮箱）
        login_identifier = login_data.email  # 这个字段现在可以是用户名或邮箱
        
        # 先尝试按邮箱查找
        user = db.query(User).filter(User.email == login_identifier).first()
        
        # 如果没找到，再尝试按用户名查找
        if not user:
            user = db.query(User).filter(User.username == login_identifier).first()
        
        # 验证用户和密码
        if not user or not verify_password(login_data.password, user.password_hash):
            logger.warning(f"登录失败：用户名/邮箱或密码错误 - {login_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        # 检查账户状态
        if not user.is_active:
            logger.warning(f"登录失败：账户已禁用 - {login_identifier}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.ACCOUNT_DISABLED
            )
        
        # 更新最后登录时间
        user.last_login = get_beijing_time_naive()
        db.commit()
        
        # 生成访问令牌和刷新令牌
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
            return {
                "message": "如果该邮箱已注册，重置链接将发送到您的邮箱"
            }
        
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
        
        return {
            "message": "密码重置链接已发送到您的邮箱",
            "expires_in": PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        }
        
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
        
        return {
            "message": SuccessMessages.PASSWORD_RESET_SUCCESS
        }
        
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
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60  # 转换为秒
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token刷新失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token刷新失败，请稍后重试"
        )

@router.post("/institution-login", response_model=LoginResponse)
async def institution_login(login_data: InstitutionLoginRequest, db: Session = Depends(get_db)):
    """机构登录 - 学校代码+工号/学号+密码登录"""
    try:
        # 1. 查找学校
        school = db.query(School).filter(
            School.school_code == login_data.school_code.upper()
        ).first()
        
        if not school:
            logger.warning(f"机构登录失败：学校不存在 - {login_data.school_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学校不存在"
            )
        
        if not school.is_active:
            logger.warning(f"机构登录失败：学校已禁用 - {login_data.school_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校已禁用"
            )
        
        # 2. 查找用户（通过工号或学号）
        user = db.query(User).filter(
            User.school_id == school.id,
            (User.teacher_number == login_data.number) | (User.student_number == login_data.number)
        ).first()
        
        if not user:
            logger.warning(f"机构登录失败：用户不存在 - {login_data.school_code}/{login_data.number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="工号/学号或密码错误"
            )
        
        # 3. 验证密码
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"机构登录失败：密码错误 - {login_data.school_code}/{login_data.number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="工号/学号或密码错误"
            )
        
        # 4. 检查账户状态
        if not user.is_active:
            logger.warning(f"机构登录失败：账户已禁用 - {login_data.school_code}/{login_data.number}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.ACCOUNT_DISABLED
            )
        
        # 5. 更新最后登录时间
        user.last_login = get_beijing_time_naive()
        db.commit()
        
        # 6. 生成访问令牌和刷新令牌
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        logger.info(f"✅ 机构用户登录成功: {user.username} ({user.role}) - {school.school_name} (ID: {user.id})")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,  # 转换为秒
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 机构登录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )

@router.get("/user-info", response_model=UserResponse)
async def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码 - 需要验证旧密码"""
    try:
        # 验证旧密码
        if not verify_password(password_data.old_password, current_user.password_hash):
            logger.warning(f"修改密码失败：旧密码错误 - 用户ID: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 更新密码
        current_user.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info(f"✅ 密码修改成功: {current_user.username} (ID: {current_user.id})")
        
        return {
            "message": "密码修改成功"
        }
        
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


