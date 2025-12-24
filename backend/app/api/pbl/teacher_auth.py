from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from pydantic import BaseModel

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.security import verify_password, create_access_token, create_refresh_token, verify_token, get_password_hash
from ...core.deps import get_db, get_current_teacher
from ...core.logging_config import get_logger
from ...schemas.user import InstitutionLoginRequest, UserResponse, RefreshTokenRequest
from ...models.admin import Admin
from ...models.school import School
from ...utils.timezone import get_beijing_time_naive

router = APIRouter()
logger = get_logger(__name__)

# ===== Pydantic Schemas =====

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""
    name: str = None
    phone: str = None
    subject: str = None

# ===== 已废弃的教师登录接口（2024-12-24）=====
# 系统已统一使用 /api/auth/login 作为唯一登录接口
# 原登录接口已删除
# ============================================

@router.get("/me")
def get_current_teacher_info(current_teacher: Admin = Depends(get_current_teacher), db: Session = Depends(get_db)):
    """获取当前教师信息（需要认证）"""
    logger.debug(f"获取教师信息 - 用户名: {current_teacher.username}, ID: {current_teacher.id}")
    
    # 获取教师所在学校信息
    school = None
    if current_teacher.school_id:
        school = db.query(School).filter(School.id == current_teacher.school_id).first()
    
    teacher_response = UserResponse.model_validate(current_teacher)
    
    response_data = teacher_response.model_dump(mode='json')
    if school:
        response_data['school'] = {
            "id": school.id,
            "uuid": school.uuid,
            "school_code": school.school_code,
            "school_name": school.school_name
        }
    
    return success_response(data=response_data)

@router.post("/refresh")
def refresh_teacher_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用refresh token刷新access token（教师端）
    """
    logger.info("收到教师刷新令牌请求")
    
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException as e:
        logger.warning(f"教师刷新令牌验证失败: {str(e)}")
        return error_response(
            message="无效的刷新令牌或已过期",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    teacher_id = payload.get("sub")
    user_role = payload.get("user_role")
    portal = payload.get("portal")
    
    if teacher_id is None or portal != "teacher":
        logger.warning("刷新令牌中没有教师ID或portal标记错误")
        return error_response(
            message="无效的刷新令牌",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    logger.debug(f"教师刷新令牌解析 - 教师ID: {teacher_id}")
    
    # 验证教师是否存在
    teacher = db.query(Admin).filter(
        Admin.id == int(teacher_id),
        Admin.role == 'teacher'
    ).first()
    
    if teacher is None:
        logger.warning(f"刷新令牌失败 - 教师不存在: {teacher_id}")
        return error_response(
            message="教师不存在",
            code=401,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    if not teacher.is_active:
        logger.warning(f"刷新令牌失败 - 教师账户已禁用: {teacher.username}")
        return error_response(
            message="账户已被禁用",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 生成新的tokens
    new_access_token = create_access_token(data={"sub": str(teacher.id), "user_role": "teacher", "portal": "teacher"})
    new_refresh_token = create_refresh_token(data={"sub": str(teacher.id), "user_role": "teacher", "portal": "teacher"})
    
    logger.info(f"教师令牌刷新成功 - 用户: {teacher.username} (ID: {teacher.id})")
    
    return success_response(
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        },
        message="令牌刷新成功"
    )

@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_teacher: Admin = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """修改密码"""
    logger.info(f"教师 {current_teacher.username} 请求修改密码")
    
    # 验证旧密码
    if not verify_password(password_data.old_password, current_teacher.password_hash):
        logger.warning(f"教师 {current_teacher.username} 旧密码验证失败")
        return error_response(
            message="旧密码错误",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证新密码长度
    if len(password_data.new_password) < 6:
        return error_response(
            message="新密码长度不能少于6位",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 更新密码
    current_teacher.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"教师 {current_teacher.username} 密码修改成功")
    
    return success_response(message="密码修改成功")

@router.put("/profile")
def update_profile(
    profile_data: UpdateProfileRequest,
    current_teacher: Admin = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新个人信息"""
    logger.info(f"教师 {current_teacher.username} 更新个人信息")
    
    # 更新字段
    if profile_data.name is not None:
        current_teacher.name = profile_data.name
    if profile_data.phone is not None:
        current_teacher.phone = profile_data.phone
    if profile_data.subject is not None:
        current_teacher.subject = profile_data.subject
    
    db.commit()
    db.refresh(current_teacher)
    
    logger.info(f"教师 {current_teacher.username} 个人信息更新成功")
    
    # 返回更新后的信息
    school = None
    if current_teacher.school_id:
        school = db.query(School).filter(School.id == current_teacher.school_id).first()
    
    teacher_response = UserResponse.model_validate(current_teacher)
    response_data = teacher_response.model_dump(mode='json')
    if school:
        response_data['school'] = {
            "id": school.id,
            "uuid": school.uuid,
            "school_code": school.school_code,
            "school_name": school.school_name
        }
    
    return success_response(data=response_data, message="个人信息更新成功")
