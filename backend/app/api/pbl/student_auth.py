from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Tuple

from ...core.response import success_response, error_response
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from ...core.deps import get_db, get_current_user
from ...core.logging_config import get_logger
from ...schemas.user import UserLogin, UserCreate, UserResponse, TokenResponse, RefreshTokenRequest, RefreshTokenResponse, InstitutionLoginRequest, ChangePasswordRequest
from ...models.admin import User
from ...models.school import School
from ...utils.timezone import get_beijing_time_naive

router = APIRouter()
logger = get_logger(__name__)

# ===== 已废弃的学生登录接口（2024-12-24）=====
# 系统已统一使用 /api/auth/login 作为唯一登录接口
# 原登录接口已删除
# ============================================

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    logger.debug(f"获取用户信息 - 用户名: {current_user.username}, ID: {current_user.id}")
    user_response = UserResponse.model_validate(current_user)
    return success_response(data=user_response.model_dump(mode='json'))

@router.post("/register")
def student_register(user_data: UserCreate, db: Session = Depends(get_db)):
    """学生用户注册"""
    logger.info(f"收到学生注册请求 - 用户名: {user_data.username}")
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"注册失败 - 用户名已存在: {user_data.username}")
        return error_response(
            message="用户名已存在",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查邮箱是否已存在（如果提供）
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            logger.warning(f"注册失败 - 邮箱已被使用: {user_data.email}")
            return error_response(
                message="邮箱已被使用",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        nickname=user_data.nickname,
        name=user_data.name,
        real_name=user_data.real_name,
        gender=user_data.gender,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role if user_data.role else 'student',
        school_id=user_data.school_id,
        class_id=user_data.class_id,
        group_id=user_data.group_id,
        school_name=user_data.school_name,
        student_number=user_data.student_number,
        is_active=True,
        need_change_password=True  # 首次登录需要修改密码
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"学生用户创建成功 - 用户名: {user_data.username}, ID: {new_user.id}")
    
    # 将 User 模型转换为 UserResponse schema
    user_response = UserResponse.model_validate(new_user)
    return success_response(data=user_response.model_dump(mode='json'), message="注册成功")

@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用refresh token刷新access token
    当access token过期时，客户端可以使用有效的refresh token获取新的access token和refresh token
    仅支持学生用户（role=student）
    """
    logger.info("收到学生刷新令牌请求")
    
    # 验证refresh token
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException as e:
        # refresh token 无效或已过期
        logger.warning(f"刷新令牌验证失败: {str(e)}")
        return error_response(
            message="无效的刷新令牌或已过期",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 获取用户ID和用户角色
    user_id = payload.get("sub")
    user_role = payload.get("user_role")  # 可能为None（旧版本token）
    
    if user_id is None:
        logger.warning("刷新令牌中没有用户ID")
        return error_response(
            message="无效的刷新令牌",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"刷新令牌解析 - 用户ID: {user_id}, Token中的角色: {user_role}")
    
    # 验证用户是否存在（查询User表）
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        logger.warning(f"刷新令牌失败 - 学生用户不存在: {user_id}")
        return error_response(
            message="用户不存在",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 检查用户角色是否是学生类型
    if user.role != 'student':
        logger.warning(f"刷新令牌失败 - 不是学生类型的用户: user_role={user.role}")
        return error_response(
            message="无效的用户类型",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 如果token中有user_role字段，验证是否匹配（向后兼容：旧token没有此字段）
    if user_role is not None and user.role != user_role:
        logger.warning(f"刷新令牌失败 - 用户角色不匹配: token角色={user_role}, 实际角色={user.role}")
        return error_response(
            message="用户角色不匹配",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"刷新令牌验证通过 - 用户ID: {user_id}, 实际角色: {user.role}")
    
    if not user.is_active:
        logger.warning(f"刷新令牌失败 - 用户账户已禁用: {user.username}")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 生成新的access token和refresh token（包含用户类型信息）
    new_access_token = create_access_token(data={"sub": str(user.id), "user_role": user.role})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "user_role": user.role})
    
    logger.info(f"令牌刷新成功 - 用户: {user.username} (角色: {user.role}, ID: {user.id})")
    
    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        },
        message="令牌刷新成功"
    )

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    验证密码强度：至少8位，包含大写字母、小写字母、数字三种中的两种
    返回：(是否有效, 错误消息)
    """
    if len(password) < 8:
        return False, "密码至少需要8位"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    type_count = sum([has_upper, has_lower, has_digit])
    
    if type_count < 2:
        return False, "密码必须包含大写字母、小写字母、数字三种中的至少两种"
    
    return True, ""

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户的密码
    需要提供当前密码进行验证
    """
    logger.info(f"收到修改密码请求 - 用户: {current_user.username} (ID: {current_user.id})")
    
    # 验证当前密码
    if not verify_password(request.current_password, current_user.password_hash):
        logger.warning(f"修改密码失败 - 当前密码错误: {current_user.username}")
        return error_response(
            message="当前密码错误",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证新密码强度
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        logger.warning(f"修改密码失败 - 密码强度不足: {current_user.username}, {error_msg}")
        return error_response(
            message=error_msg,
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查新密码是否与当前密码相同
    if verify_password(request.new_password, current_user.password_hash):
        logger.warning(f"修改密码失败 - 新密码与当前密码相同: {current_user.username}")
        return error_response(
            message="新密码不能与当前密码相同",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(request.new_password)
    
    # 清除强制修改密码标记
    if current_user.need_change_password:
        current_user.need_change_password = False
    
    db.commit()
    
    logger.info(f"密码修改成功 - 用户: {current_user.username} (ID: {current_user.id})")
    
    return success_response(
        data={
            'need_change_password': current_user.need_change_password
        },
        message="密码修改成功"
    )
