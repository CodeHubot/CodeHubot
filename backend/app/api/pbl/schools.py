"""
学校管理 API
用于平台管理员管理学校
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date
import uuid as uuid_lib

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...core.security import get_password_hash
from ...models.admin import Admin, User
from ...models.school import School
from ...core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/list")
def get_schools(
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取学校列表
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以查看学校列表",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 构建查询
    query = db.query(School)
    
    # 筛选条件
    if is_active is not None:
        query = query.filter(School.is_active == is_active)
    
    if search:
        query = query.filter(
            (School.school_name.like(f'%{search}%')) |
            (School.school_code.like(f'%{search}%')) |
            (School.city.like(f'%{search}%'))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    schools = query.offset(skip).limit(limit).all()
    
    # 序列化结果
    result = []
    for school in schools:
        # 统计当前教师和学生数（实时查询）
        teacher_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role.in_(['teacher', 'school_admin']),
            User.deleted_at == None,
            User.is_active == True
        ).scalar() or 0
        
        student_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role == 'student',
            User.deleted_at == None,
            User.is_active == True
        ).scalar() or 0
        
        result.append({
            'id': school.id,
            'uuid': school.uuid,
            'school_code': school.school_code,
            'school_name': school.school_name,
            'province': school.province,
            'city': school.city,
            'district': school.district,
            'address': school.address,
            'contact_person': school.contact_person,
            'contact_phone': school.contact_phone,
            'contact_email': school.contact_email,
            'is_active': school.is_active,
            'license_expire_at': school.license_expire_at.isoformat() if school.license_expire_at else None,
            'max_teachers': school.max_teachers,
            'current_teachers': teacher_count,
            'max_students': school.max_students,
            'current_students': student_count,
            'max_devices': school.max_devices,
            'admin_user_id': school.admin_user_id,
            'admin_username': school.admin_username,
            'description': school.description,
            'video_student_view_limit': school.video_student_view_limit,
            'video_teacher_view_limit': school.video_teacher_view_limit,
            'created_at': school.created_at.isoformat() if school.created_at else None,
            'updated_at': school.updated_at.isoformat() if school.updated_at else None
        })
    
    return success_response(data={
        'total': total,
        'items': result
    })


# ============================================================================
# 便捷API - 无需传递UUID（必须在 /{school_uuid} 路由之前）
# ============================================================================

@router.get("/my-school/info")
def get_my_school_info(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取当前管理员所属学校的基本信息
    用于前端获取当前学校的UUID等信息
    """
    # 检查当前管理员是否有关联的学校
    if not current_admin.school_id:
        return error_response(
            message="您的账号未关联任何学校",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 获取管理员的学校
    school = db.query(School).filter(School.id == current_admin.school_id).first()
    if not school:
        logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
        return error_response(
            message="您关联的学校不存在，请联系管理员",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return success_response(data={
        'id': school.id,
        'uuid': school.uuid,
        'school_code': school.school_code,
        'school_name': school.school_name,
        'province': school.province,
        'city': school.city,
        'district': school.district,
        'address': school.address,
        'is_active': school.is_active,
        'license_expire_at': school.license_expire_at.isoformat() if school.license_expire_at else None,
        'max_teachers': school.max_teachers,
        'max_students': school.max_students,
        'max_devices': school.max_devices,
        'description': school.description,
        'created_at': school.created_at.isoformat() if school.created_at else None
    })


@router.get("/my-school/users")
def get_my_school_users(
    skip: int = 0,
    limit: int = 20,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取当前管理员所属学校的用户列表（教师和学生）
    权限：学校管理员只能查看自己学校的用户
    这是一个便捷端点，无需传递 school_uuid
    """
    # 检查当前管理员是否有关联的学校
    if not current_admin.school_id:
        return error_response(
            message="您的账号未关联任何学校",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 获取管理员的学校
    school = db.query(School).filter(School.id == current_admin.school_id).first()
    if not school:
        logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
        return error_response(
            message="您关联的学校不存在，请联系管理员",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    logger.info(
        f"管理员 {current_admin.username} 查询自己学校 {school.school_name} 的用户列表"
    )
    
    # 构建查询
    query = db.query(User).filter(
        User.school_id == school.id,
        User.deleted_at == None
    )
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    else:
        # 默认只查询教师和学生
        query = query.filter(User.role.in_(['teacher', 'student']))
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.name.like(f'%{keyword}%')) |
            (User.real_name.like(f'%{keyword}%')) |
            (User.username.like(f'%{keyword}%')) |
            (User.teacher_number.like(f'%{keyword}%')) |
            (User.student_number.like(f'%{keyword}%'))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    users = query.offset(skip).limit(limit).all()
    
    # 序列化结果
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'name': user.name or user.real_name,
            'role': user.role,
            'teacher_number': user.teacher_number,
            'student_number': user.student_number,
            'gender': user.gender,
            'phone': user.phone,
            'email': user.email,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    return success_response(data={
        'items': result,
        'total': total,
        'skip': skip,
        'limit': limit,
        'school_name': school.school_name,
        'school_uuid': school.uuid
    })


@router.get("/my-school/statistics")
def get_my_school_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取当前管理员所属学校的统计信息
    权限：学校管理员只能查看自己学校的统计
    这是一个便捷端点，无需传递 school_uuid
    """
    # 检查当前管理员是否有关联的学校
    if not current_admin.school_id:
        return error_response(
            message="您的账号未关联任何学校",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 获取管理员的学校
    school = db.query(School).filter(School.id == current_admin.school_id).first()
    if not school:
        logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
        return error_response(
            message="您关联的学校不存在，请联系管理员",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    logger.info(
        f"管理员 {current_admin.username} 查询自己学校 {school.school_name} 的统计信息"
    )
    
    # 统计教师数
    teacher_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'teacher',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    # 统计学生数
    student_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'student',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    # 统计学校管理员数
    admin_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'school_admin',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    return success_response(data={
        'teacher_count': teacher_count,
        'student_count': student_count,
        'admin_count': admin_count,
        'max_teachers': school.max_teachers,
        'max_students': school.max_students,
        'max_devices': school.max_devices,
        'school_name': school.school_name,
        'school_uuid': school.uuid
    })


# ============================================================================
# 带UUID的API - 用于平台管理员或兼容旧代码
# ============================================================================

@router.get("/{school_uuid}")
def get_school(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取学校详情
    权限：
    - 平台管理员：可以查看任何学校
    - 学校管理员：自动忽略传入的UUID，只能查看自己学校（安全设计）
    """
    # 安全设计：如果是学校管理员，自动使用其所属学校的ID，忽略传入的UUID
    if current_admin.role == 'school_admin':
        if not current_admin.school_id:
            return error_response(
                message="您的账号未关联任何学校",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        school = db.query(School).filter(School.id == current_admin.school_id).first()
        if not school:
            logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
            return error_response(
                message="您关联的学校不存在，请联系管理员",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # 如果传入的UUID与管理员所属学校不符，记录警告日志
        if school.uuid != school_uuid:
            logger.warning(
                f"🔒 安全拦截 - 学校管理员 {current_admin.username} 尝试访问其他学校UUID ({school_uuid})，"
                f"已自动重定向到其所属学校 {school.school_name} (uuid={school.uuid})"
            )
    else:
        # 平台管理员可以查看任何学校
        school = db.query(School).filter(School.uuid == school_uuid).first()
        if not school:
            return error_response(
                message="学校不存在",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    # 获取学校管理员信息
    admin_user = None
    if school.admin_user_id:
        admin_user = db.query(User).filter(User.id == school.admin_user_id).first()
    
    # 统计当前教师和学生数
    teacher_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role.in_(['teacher', 'school_admin']),
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    student_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'student',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    result = {
        'id': school.id,
        'uuid': school.uuid,
        'school_code': school.school_code,
        'school_name': school.school_name,
        'province': school.province,
        'city': school.city,
        'district': school.district,
        'address': school.address,
        'contact_person': school.contact_person,
        'contact_phone': school.contact_phone,
        'contact_email': school.contact_email,
        'is_active': school.is_active,
        'license_expire_at': school.license_expire_at.isoformat() if school.license_expire_at else None,
        'max_teachers': school.max_teachers,
        'current_teachers': teacher_count,
        'max_students': school.max_students,
        'current_students': student_count,
        'max_devices': school.max_devices,
        'description': school.description,
        'video_student_view_limit': school.video_student_view_limit,
        'video_teacher_view_limit': school.video_teacher_view_limit,
        'created_at': school.created_at.isoformat() if school.created_at else None,
        'updated_at': school.updated_at.isoformat() if school.updated_at else None,
        'admin_user': None
    }
    
    if admin_user:
        result['admin_user'] = {
            'id': admin_user.id,
            'username': admin_user.username,
            'name': admin_user.name or admin_user.real_name,
            'phone': admin_user.phone,
            'email': admin_user.email
        }
    
    return success_response(data=result)


@router.post("")
def create_school(
    school_code: str = Form(...),
    school_name: str = Form(...),
    province: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    contact_person: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    max_teachers: int = Form(100),
    max_students: int = Form(1000),
    max_devices: int = Form(500),
    license_expire_at: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    video_student_view_limit: Optional[int] = Form(None),
    video_teacher_view_limit: Optional[int] = Form(None),
    admin_teacher_number: Optional[str] = Form(None),
    admin_password: Optional[str] = Form(None),
    admin_name: Optional[str] = Form(None),
    admin_phone: Optional[str] = Form(None),
    admin_email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    创建学校
    权限：仅平台管理员
    可同时创建学校管理员账号
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以创建学校",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查学校代码是否已存在
    existing_school = db.query(School).filter(School.school_code == school_code).first()
    if existing_school:
        return error_response(
            message="学校代码已存在",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查学校名称是否已存在
    existing_name = db.query(School).filter(School.school_name == school_name).first()
    if existing_name:
        return error_response(
            message="学校名称已存在",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 转换日期
    license_date = None
    if license_expire_at:
        try:
            license_date = datetime.fromisoformat(license_expire_at).date()
        except:
            pass
    
    # 创建学校
    new_school = School(
        uuid=str(uuid_lib.uuid4()),
        school_code=school_code,
        school_name=school_name,
        province=province,
        city=city,
        district=district,
        address=address,
        contact_person=contact_person,
        contact_phone=contact_phone,
        contact_email=contact_email,
        is_active=True,
        license_expire_at=license_date,
        max_teachers=max_teachers,
        max_students=max_students,
        max_devices=max_devices,
        description=description,
        video_student_view_limit=video_student_view_limit,
        video_teacher_view_limit=video_teacher_view_limit
    )
    
    db.add(new_school)
    db.flush()  # 获取school的id
    
    # 如果提供了管理员信息，创建学校管理员账号
    admin_user = None
    if admin_teacher_number and admin_password:
        # 自动生成用户名：职工号 + 学校编码
        admin_username = f"{admin_teacher_number}@{school_code}"
        
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == admin_username).first()
        if existing_user:
            db.rollback()
            return error_response(
                message=f"该职工号在本校已存在",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建管理员账号
        admin_user = User(
            username=admin_username,
            password_hash=get_password_hash(admin_password),
            name=admin_name or admin_teacher_number,
            phone=admin_phone,
            email=admin_email,
            teacher_number=admin_teacher_number,
            role='school_admin',
            school_id=new_school.id,
            school_name=new_school.school_name,
            is_active=True,
            need_change_password=True
        )
        db.add(admin_user)
        db.flush()
        
        # 更新学校的管理员信息
        new_school.admin_user_id = admin_user.id
        new_school.admin_username = admin_user.username
    
    db.commit()
    db.refresh(new_school)
    
    logger.info(f"创建学校成功 - 学校: {school_name}, 代码: {school_code}, 操作者: {current_admin.username}")
    if admin_user:
        logger.info(f"创建学校管理员成功 - 用户名: {admin_username}, 学校: {school_name}")
    
    result = {
        'id': new_school.id,
        'uuid': new_school.uuid,
        'school_code': new_school.school_code,
        'school_name': new_school.school_name,
        'is_active': new_school.is_active
    }
    
    if admin_user:
        result['admin_user'] = {
            'id': admin_user.id,
            'username': admin_user.username,
            'name': admin_user.name
        }
    
    return success_response(
        data=result,
        message="学校创建成功" + ("，管理员账号已创建" if admin_user else "")
    )


@router.put("/{school_uuid}")
def update_school(
    school_uuid: str,
    school_name: Optional[str] = Form(None),
    province: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    contact_person: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    max_teachers: Optional[int] = Form(None),
    max_students: Optional[int] = Form(None),
    max_devices: Optional[int] = Form(None),
    license_expire_at: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    video_student_view_limit: Optional[int] = Form(None),
    video_teacher_view_limit: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    更新学校信息
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以修改学校信息",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 更新字段
    if school_name is not None:
        # 检查名称是否与其他学校重复
        existing = db.query(School).filter(
            School.school_name == school_name,
            School.uuid != school_uuid
        ).first()
        if existing:
            return error_response(
                message="学校名称已被其他学校使用",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        school.school_name = school_name
    
    if province is not None:
        school.province = province
    if city is not None:
        school.city = city
    if district is not None:
        school.district = district
    if address is not None:
        school.address = address
    if contact_person is not None:
        school.contact_person = contact_person
    if contact_phone is not None:
        school.contact_phone = contact_phone
    if contact_email is not None:
        school.contact_email = contact_email
    if max_teachers is not None:
        school.max_teachers = max_teachers
    if max_students is not None:
        school.max_students = max_students
    if max_devices is not None:
        school.max_devices = max_devices
    if license_expire_at is not None:
        try:
            school.license_expire_at = datetime.fromisoformat(license_expire_at).date()
        except:
            pass
    if description is not None:
        school.description = description
    
    # 更新视频权限
    if video_student_view_limit is not None:
        school.video_student_view_limit = video_student_view_limit
    if video_teacher_view_limit is not None:
        school.video_teacher_view_limit = video_teacher_view_limit
    
    db.commit()
    db.refresh(school)
    
    logger.info(f"更新学校信息 - 学校: {school.school_name}, UUID: {school_uuid}, 操作者: {current_admin.username}")
    
    return success_response(message="学校信息更新成功")


@router.patch("/{school_uuid}/toggle-active")
def toggle_school_active(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    启用/禁用学校
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 切换状态
    school.is_active = not school.is_active
    db.commit()
    
    status_text = "启用" if school.is_active else "禁用"
    logger.info(f"{status_text}学校 - 学校: {school.school_name}, UUID: {school_uuid}, 操作者: {current_admin.username}")
    
    return success_response(
        data={'is_active': school.is_active},
        message=f"学校已{status_text}"
    )


@router.post("/{school_uuid}/assign-admin")
def assign_school_admin(
    school_uuid: str,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    为学校分配管理员
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以分配学校管理员",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查学校是否存在
    school = db.query(School).filter(School.uuid == school_uuid).first()
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error_response(
            message="用户不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查用户角色
    if user.role != 'school_admin':
        return error_response(
            message="只能分配学校管理员角色的用户",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 更新用户的学校ID
    user.school_id = school.id
    user.school_name = school.school_name
    
    # 更新学校的管理员信息
    school.admin_user_id = user_id
    school.admin_username = user.username
    
    db.commit()
    
    logger.info(f"分配学校管理员 - 学校: {school.school_name}, 管理员: {user.username}, 操作者: {current_admin.username}")
    
    return success_response(message="学校管理员分配成功")


@router.get("/{school_uuid}/admin")
def get_school_admin(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取学校管理员信息
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以查看学校管理员",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查学校是否存在
    school = db.query(School).filter(School.uuid == school_uuid).first()
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取学校管理员
    admin_user = None
    if school.admin_user_id:
        admin_user = db.query(User).filter(User.id == school.admin_user_id).first()
    
    result = {
        'has_admin': admin_user is not None,
        'admin_user': None
    }
    
    if admin_user:
        result['admin_user'] = {
            'id': admin_user.id,
            'username': admin_user.username,
            'name': admin_user.name or admin_user.real_name,
            'teacher_number': admin_user.teacher_number,
            'phone': admin_user.phone,
            'email': admin_user.email,
            'is_active': admin_user.is_active
        }
    
    return success_response(data=result)


@router.post("/{school_uuid}/admin")
def create_or_update_school_admin(
    school_uuid: str,
    teacher_number: str = Form(...),
    password: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    创建或更新学校管理员
    权限：仅平台管理员
    如果学校已有管理员，则更新管理员信息；否则创建新管理员
    注意：更新时如果密码为空，则不更新密码；创建时密码必填
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以管理学校管理员",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查学校是否存在
    school = db.query(School).filter(School.uuid == school_uuid).first()
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 生成用户名：职工号@学校编码
    username = f"{teacher_number}@{school.school_code}"
    
    # 检查是否已有管理员
    existing_admin = None
    if school.admin_user_id:
        existing_admin = db.query(User).filter(User.id == school.admin_user_id).first()
    
    if existing_admin:
        # 更新现有管理员
        # 如果用户名变化，需要检查新用户名是否已被使用
        if existing_admin.username != username:
            existing_user = db.query(User).filter(
                User.username == username,
                User.id != existing_admin.id
            ).first()
            if existing_user:
                return error_response(
                    message=f"该职工号在本校已被使用",
                    code=400,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            existing_admin.username = username
        
        # 更新其他信息
        existing_admin.teacher_number = teacher_number
        # 只有密码不为空时才更新密码
        if password:
            existing_admin.password_hash = get_password_hash(password)
            existing_admin.need_change_password = True
        if name:
            existing_admin.name = name
        if phone:
            existing_admin.phone = phone
        if email:
            existing_admin.email = email
        
        # 更新学校的管理员用户名
        school.admin_username = username
        
        db.commit()
        db.refresh(existing_admin)
        
        logger.info(f"更新学校管理员 - 学校: {school.school_name}, 管理员: {username}, 操作者: {current_admin.username}")
        
        return success_response(
            message="学校管理员更新成功",
            data={
                'id': existing_admin.id,
                'username': existing_admin.username,
                'name': existing_admin.name
            }
        )
    else:
        # 创建新管理员
        # 创建时密码必填
        if not password:
            return error_response(
                message="创建学校管理员时密码不能为空",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return error_response(
                message=f"该职工号在本校已存在",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建管理员账号
        new_admin = User(
            username=username,
            password_hash=get_password_hash(password),
            name=name or teacher_number,
            phone=phone,
            email=email,
            teacher_number=teacher_number,
            role='school_admin',
            school_id=school.id,
            school_name=school.school_name,
            is_active=True,
            need_change_password=True
        )
        db.add(new_admin)
        db.flush()
        
        # 更新学校的管理员信息
        school.admin_user_id = new_admin.id
        school.admin_username = new_admin.username
        
        db.commit()
        db.refresh(new_admin)
        
        logger.info(f"创建学校管理员 - 学校: {school.school_name}, 管理员: {username}, 操作者: {current_admin.username}")
        
        return success_response(
            message="学校管理员创建成功",
            data={
                'id': new_admin.id,
                'username': new_admin.username,
                'name': new_admin.name
            }
        )


@router.delete("/{school_uuid}")
def delete_school(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    删除学校（仅在学校没有关联数据时允许删除）
    权限：仅平台管理员
    """
    # 权限检查
    if current_admin.role != 'platform_admin':
        return error_response(
            message="仅平台管理员可以删除学校",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查是否有关联的用户
    user_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.deleted_at == None
    ).scalar()
    
    if user_count > 0:
        return error_response(
            message=f"该学校还有 {user_count} 个用户，无法删除",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 删除学校
    db.delete(school)
    db.commit()
    
    logger.info(f"删除学校 - 学校: {school.school_name}, UUID: {school_uuid}, 操作者: {current_admin.username}")
    
    return success_response(message="学校删除成功")


@router.get("/{school_uuid}/users")
def get_school_users(
    school_uuid: str,
    skip: int = 0,
    limit: int = 20,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取学校用户列表（教师和学生）
    权限：
    - 平台管理员：可以查看任何学校的用户
    - 学校管理员：自动忽略传入的UUID，只能查看自己学校的用户（安全设计）
    """
    # 安全设计：如果是学校管理员，自动使用其所属学校的ID，忽略传入的UUID
    if current_admin.role == 'school_admin':
        # 检查学校管理员是否有关联的学校
        if not current_admin.school_id:
            return error_response(
                message="您的账号未关联任何学校",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 直接使用管理员所属的学校
        school = db.query(School).filter(School.id == current_admin.school_id).first()
        if not school:
            logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
            return error_response(
                message="您关联的学校不存在，请联系管理员",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # 如果传入的UUID与管理员所属学校不符，记录警告日志但仍返回管理员自己学校的数据
        if school.uuid != school_uuid:
            logger.warning(
                f"🔒 安全拦截 - 学校管理员 {current_admin.username} 尝试访问其他学校UUID ({school_uuid})，"
                f"已自动重定向到其所属学校 {school.school_name} (uuid={school.uuid})"
            )
    else:
        # 平台管理员可以查看任何学校
        school = db.query(School).filter(School.uuid == school_uuid).first()
        if not school:
            return error_response(
                message="学校不存在",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    # 构建查询
    query = db.query(User).filter(
        User.school_id == school.id,
        User.deleted_at == None
    )
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    else:
        # 默认只查询教师和学生
        query = query.filter(User.role.in_(['teacher', 'student']))
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.name.like(f'%{keyword}%')) |
            (User.real_name.like(f'%{keyword}%')) |
            (User.username.like(f'%{keyword}%')) |
            (User.teacher_number.like(f'%{keyword}%')) |
            (User.student_number.like(f'%{keyword}%'))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    users = query.offset(skip).limit(limit).all()
    
    # 序列化结果
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'name': user.name or user.real_name,
            'role': user.role,
            'teacher_number': user.teacher_number,
            'student_number': user.student_number,
            'gender': user.gender,
            'phone': user.phone,
            'email': user.email,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    return success_response(data={
        'items': result,
        'total': total,
        'skip': skip,
        'limit': limit
    })


@router.get("/{school_uuid}/statistics")
def get_school_statistics(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取学校统计信息
    权限：
    - 平台管理员：可以查看任何学校
    - 学校管理员：自动忽略传入的UUID，只能查看自己学校（安全设计）
    """
    # 安全设计：如果是学校管理员，自动使用其所属学校的ID，忽略传入的UUID
    if current_admin.role == 'school_admin':
        if not current_admin.school_id:
            return error_response(
                message="您的账号未关联任何学校",
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        school = db.query(School).filter(School.id == current_admin.school_id).first()
        if not school:
            logger.error(f"管理员 {current_admin.username} 的 school_id={current_admin.school_id} 找不到对应的学校")
            return error_response(
                message="您关联的学校不存在，请联系管理员",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # 如果传入的UUID与管理员所属学校不符，记录警告日志
        if school.uuid != school_uuid:
            logger.warning(
                f"🔒 安全拦截 - 学校管理员 {current_admin.username} 尝试访问其他学校UUID ({school_uuid})，"
                f"已自动重定向到其所属学校 {school.school_name} (uuid={school.uuid})"
            )
    else:
        # 平台管理员可以查看任何学校
        school = db.query(School).filter(School.uuid == school_uuid).first()
        if not school:
            return error_response(
                message="学校不存在",
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    # 统计教师数
    teacher_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'teacher',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    # 统计学生数
    student_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'student',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    # 统计学校管理员数
    admin_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'school_admin',
        User.deleted_at == None,
        User.is_active == True
    ).scalar()
    
    result = {
        'school_id': school.id,
        'school_uuid': school.uuid,
        'school_name': school.school_name,
        'teacher_count': teacher_count,
        'max_teachers': school.max_teachers,
        'student_count': student_count,
        'max_students': school.max_students,
        'admin_count': admin_count,
        'capacity_usage': {
            'teachers': {
                'current': teacher_count,
                'max': school.max_teachers,
                'percentage': round(teacher_count / school.max_teachers * 100, 2) if school.max_teachers > 0 else 0
            },
            'students': {
                'current': student_count,
                'max': school.max_students,
                'percentage': round(student_count / school.max_students * 100, 2) if school.max_students > 0 else 0
            }
        }
    }
    
    return success_response(data=result)
