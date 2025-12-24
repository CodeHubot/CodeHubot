from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from ...core.deps import get_db, get_current_admin
from ...core.logging_config import get_logger
from ...schemas.admin import AdminLogin, AdminCreate, AdminResponse, TokenResponse, RefreshTokenRequest, RefreshTokenResponse
from ...schemas.user import InstitutionLoginRequest
from ...models.admin import Admin
from ...models.school import School
from ...utils.timezone import get_beijing_time_naive

router = APIRouter()
logger = get_logger(__name__)

@router.post("/platform-login")
def platform_admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    """平台管理员登录 - 使用用户名+密码"""
    logger.info(f"收到平台管理员登录请求 - 用户名: {login_data.username}")
    
    # 1. 查找平台管理员用户（role 必须是 platform_admin）
    admin = db.query(Admin).filter(
        Admin.username == login_data.username,
        Admin.role == 'platform_admin'
    ).first()
    
    # 检查用户是否存在
    if not admin:
        logger.warning(f"平台管理员登录失败 - 用户不存在或不是平台管理员: {login_data.username}")
        return error_response(
            message="用户名或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"找到平台管理员 - ID: {admin.id}, 用户名: {admin.username}, 角色: {admin.role}, 激活状态: {admin.is_active}")
    
    # 2. 验证密码
    logger.debug(f"验证平台管理员 {login_data.username} 的密码...")
    password_valid = verify_password(login_data.password, admin.password_hash)
    
    if not password_valid:
        logger.warning(f"平台管理员登录失败 - 用户 {login_data.username} 密码错误")
        return error_response(
            message="用户名或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"平台管理员 {login_data.username} 密码验证通过")
    
    # 3. 检查账户状态
    if not admin.is_active:
        logger.warning(f"平台管理员登录失败 - 用户 {login_data.username} 账户已被禁用")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 4. 更新最后登录时间
    admin.last_login = get_beijing_time_naive()
    db.commit()
    logger.debug(f"已更新平台管理员 {login_data.username} 的最后登录时间")
    
    # 5. 创建访问令牌和刷新令牌（包含用户类型信息）
    access_token = create_access_token(data={"sub": str(admin.id), "user_role": admin.role})
    refresh_token = create_refresh_token(data={"sub": str(admin.id), "user_role": admin.role})
    
    logger.info(f"✅ 平台管理员登录成功: {admin.username} (ID: {admin.id})")
    
    # 将 Admin 模型转换为 AdminResponse schema
    admin_response = AdminResponse.model_validate(admin)
    
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "admin": admin_response.model_dump(mode='json')
        },
        message="登录成功"
    )

@router.post("/login")
def admin_login(login_data: InstitutionLoginRequest, db: Session = Depends(get_db)):
    """教师/学校管理员登录 - 机构登录方式（学校代码+工号+密码）"""
    logger.info(f"收到教师登录请求 - 学校代码: {login_data.school_code}, 工号: {login_data.number}")
    
    # 1. 查找学校
    school = db.query(School).filter(
        School.school_code == login_data.school_code.upper()
    ).first()
    
    if not school:
        logger.warning(f"机构登录失败：学校不存在 - {login_data.school_code}")
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if not school.is_active:
        logger.warning(f"机构登录失败：学校已禁用 - {login_data.school_code}")
        return error_response(
            message="学校已禁用",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 2. 查找用户（通过工号，role为teacher或school_admin或platform_admin）
    admin = db.query(Admin).filter(
        Admin.school_id == school.id,
        Admin.teacher_number == login_data.number
    ).first()
    
    # 检查用户是否存在
    if not admin:
        logger.warning(f"登录失败 - 用户不存在: {login_data.school_code}/{login_data.number}")
        return error_response(
            message="工号或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"找到用户 - ID: {admin.id}, 用户名: {admin.username}, 角色: {admin.role}, 激活状态: {admin.is_active}")
    
    # 检查用户角色是否为教师或管理员（排除学生）
    if admin.role == 'student':
        logger.warning(f"登录失败 - 用户 {login_data.number} 是学生用户，不能登录教师端")
        return error_response(
            message="该用户不是教师，无法登录教师端",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 3. 验证密码
    logger.debug(f"验证用户 {login_data.number} 的密码...")
    password_valid = verify_password(login_data.password, admin.password_hash)
    
    if not password_valid:
        logger.warning(f"登录失败 - 用户 {login_data.number} 密码错误")
        return error_response(
            message="工号或密码错误",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"用户 {login_data.number} 密码验证通过")
    
    # 4. 检查账户状态
    if not admin.is_active:
        logger.warning(f"登录失败 - 用户 {login_data.number} 账户已被禁用")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 5. 更新最后登录时间
    admin.last_login = get_beijing_time_naive()
    db.commit()
    logger.debug(f"已更新用户 {login_data.number} 的最后登录时间")
    
    # 6. 创建访问令牌和刷新令牌（包含用户类型信息）
    access_token = create_access_token(data={"sub": str(admin.id), "user_role": admin.role})
    refresh_token = create_refresh_token(data={"sub": str(admin.id), "user_role": admin.role})
    
    logger.info(f"✅ 教师用户登录成功: {admin.username} ({admin.role}) - {school.school_name} (ID: {admin.id})")
    
    # 将 Admin 模型转换为 AdminResponse schema
    admin_response = AdminResponse.model_validate(admin)
    
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "admin": admin_response.model_dump(mode='json')
        },
        message="登录成功"
    )

@router.get("/me")
def get_current_admin_info(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """获取当前管理员信息"""
    logger.debug(f"获取管理员信息 - 用户名: {current_admin.username}, ID: {current_admin.id}")
    admin_response = AdminResponse.model_validate(current_admin)
    
    # 如果管理员有关联学校，获取学校的 UUID
    if current_admin.school_id:
        school = db.query(School).filter(School.id == current_admin.school_id).first()
        if school:
            admin_response.school_uuid = school.uuid
    
    return success_response(data=admin_response.model_dump(mode='json'))

@router.post("/register")
def admin_register(admin_data: AdminCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    """注册新平台管理员（需要现有平台管理员权限）"""
    logger.info(f"收到注册平台管理员请求 - 新用户名: {admin_data.username}, 操作者: {current_admin.username}")
    
    # 检查用户名是否已存在
    existing_user = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_user:
        logger.warning(f"注册失败 - 用户名已存在: {admin_data.username}")
        return error_response(
            message="用户名已存在",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查邮箱是否已存在
    if admin_data.email:
        existing_email = db.query(Admin).filter(Admin.email == admin_data.email).first()
        if existing_email:
            logger.warning(f"注册失败 - 邮箱已被使用: {admin_data.email}")
            return error_response(
                message="邮箱已被使用",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # 创建新平台管理员用户
    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=get_password_hash(admin_data.password),
        name=admin_data.full_name,  # 使用 name 字段存储全名
        role='platform_admin',  # 设置为平台管理员角色
        is_active=True,
        need_change_password=True  # 首次登录需要修改密码
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    logger.info(f"平台管理员创建成功 - 新用户名: {admin_data.username}, ID: {new_admin.id}, 操作者: {current_admin.username}")
    
    # 将 Admin 模型转换为 AdminResponse schema
    admin_response = AdminResponse.model_validate(new_admin)
    return success_response(data=admin_response.model_dump(mode='json'), message="平台管理员创建成功")

@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用refresh token刷新access token
    当access token过期时，客户端可以使用有效的refresh token获取新的access token和refresh token
    支持所有管理员类型（platform_admin, school_admin, teacher）
    """
    logger.info("收到管理员刷新令牌请求")
    
    # 验证refresh token（verify_token 现在会抛出异常）
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
    admin_id = payload.get("sub")
    user_role = payload.get("user_role")  # 可能为None（旧版本token）
    
    if admin_id is None:
        logger.warning("刷新令牌中没有用户ID")
        return error_response(
            message="无效的刷新令牌",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"刷新令牌解析 - 用户ID: {admin_id}, Token中的角色: {user_role}")
    
    # 验证用户是否存在（查询Admin表）
    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    
    if admin is None:
        logger.warning(f"刷新令牌失败 - 管理员不存在: {admin_id}")
        return error_response(
            message="用户不存在",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 检查用户角色是否是管理员类型
    if admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        logger.warning(f"刷新令牌失败 - 不是管理员类型的用户: admin_role={admin.role}")
        return error_response(
            message="无效的用户类型",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 如果token中有user_role字段，验证是否匹配（向后兼容：旧token没有此字段）
    if user_role is not None and admin.role != user_role:
        logger.warning(f"刷新令牌失败 - 用户角色不匹配: token角色={user_role}, 实际角色={admin.role}")
        return error_response(
            message="用户角色不匹配",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"刷新令牌验证通过 - 用户ID: {admin_id}, 实际角色: {admin.role}")
    
    if not admin.is_active:
        logger.warning(f"刷新令牌失败 - 用户账户已禁用: {admin.username}")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 生成新的access token和refresh token（包含用户类型信息）
    new_access_token = create_access_token(data={"sub": str(admin.id), "user_role": admin.role})
    new_refresh_token = create_refresh_token(data={"sub": str(admin.id), "user_role": admin.role})
    
    logger.info(f"令牌刷新成功 - 用户: {admin.username} (角色: {admin.role}, ID: {admin.id})")
    
    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        },
        message="令牌刷新成功"
    )
