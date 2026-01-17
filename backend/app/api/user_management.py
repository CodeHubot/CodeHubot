"""
用户管理API
提供教师、学生的创建和管理，以及角色分配功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.utils.timezone import get_beijing_time_naive
from app.core.security import get_password_hash
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.models.user import User
from app.models.school import School
from app.models.course_model import Course, CourseTeacher, CourseStudent
from app.schemas.user_management import (
    SchoolAdminCreate, TeacherCreate, StudentCreate,
    AssignRoleRequest, UserSearchQuery, InstitutionLoginRequest,
    UserListResponse, AssignRoleResponse, BatchImportResult
)
from app.schemas.user import UserResponse
from app.utils.excel_handler import (
    parse_teacher_excel, parse_student_excel,
    generate_teacher_template, generate_student_template
)

router = APIRouter(prefix="/user-management", tags=["user-management"])

def check_platform_admin(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为平台管理员"""
    if current_user.role != 'platform_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员才能执行此操作"
        )
    return current_user

def check_school_admin_or_teacher(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为学校管理员或教师"""
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学校管理员或教师才能执行此操作"
        )
    return current_user

def check_school_admin(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为学校管理员"""
    if current_user.role not in ['platform_admin', 'school_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学校管理员才能执行此操作"
        )
    return current_user

def check_school_admin_or_teacher(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为学校管理员或教师"""
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学校管理员或教师才能执行此操作"
        )
    return current_user

# ============================================================================
# 通用用户查询
# ============================================================================

@router.get("/users", response_model=dict)
async def list_users(
    role: Optional[str] = Query(None, description="角色筛选"),
    school_id: Optional[int] = Query(None, description="学校ID筛选"),
    course_id: Optional[int] = Query(None, description="课程ID筛选（学生）"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin_or_teacher)
):
    """
    获取用户列表（支持多条件筛选）
    用于分组管理等场景
    """
    
    # 构建查询
    query = db.query(User).filter(User.deleted_at.is_(None))
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    
    # 学校筛选（权限控制）
    if current_user.role in ['school_admin', 'teacher']:
        # 学校管理员和教师只能查看自己学校的用户
        query = query.filter(User.school_id == current_user.school_id)
    elif school_id:
        query = query.filter(User.school_id == school_id)
    
    # 课程筛选（学生）
    if course_id:
        # 查询选修该课程的学生ID列表
        student_ids = db.query(CourseStudent.student_id).filter(
            CourseStudent.course_id == course_id,
            CourseStudent.status == 'enrolled',
            CourseStudent.deleted_at.is_(None)
        ).all()
        student_id_list = [sid[0] for sid in student_ids]
        
        if student_id_list:
            query = query.filter(User.id.in_(student_id_list))
        else:
            # 如果该课程没有学生，返回空列表
            return success_response(data={
                "users": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            })
    
    # 关键词搜索
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                User.username.like(search_pattern),
                User.real_name.like(search_pattern),
                User.student_number.like(search_pattern),
                User.teacher_number.like(search_pattern)
            )
        )
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 构建响应
    user_list = [UserListResponse.from_orm(user).model_dump() for user in users]
    
    return success_response(data={
        "users": user_list,
        "total": total,
        "page": page,
        "page_size": page_size
    })

# ============================================================================
# 学校管理员管理
# ============================================================================

@router.post("/school-admins", response_model=dict)
async def create_school_admin(
    admin: SchoolAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_platform_admin)
):
    """创建学校管理员（仅平台管理员）"""
    
    # 检查学校是否存在
    school = db.query(School).filter(School.id == admin.school_id).first()
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == admin.username).first()
    if existing_user:
        return error_response(message="用户名已存在", code=400)
    
    # 检查邮箱是否已存在
    if admin.email:
        existing_email = db.query(User).filter(User.email == admin.email).first()
        if existing_email:
            return error_response(message="邮箱已存在", code=400)
    
    # 检查工号是否在该学校已存在
    existing_number = db.query(User).filter(
        User.school_id == admin.school_id,
        User.teacher_number == admin.teacher_number
    ).first()
    if existing_number:
        return error_response(message="工号在该学校已存在", code=400)
    
    # 创建学校管理员
    db_user = User(
        username=admin.username,
        password_hash=get_password_hash(admin.password),
        real_name=admin.real_name or None,
        email=admin.email or None,  # 空字符串转为 None
        phone=admin.phone or None,  # 空字符串转为 None
        role='school_admin',
        school_id=admin.school_id,
        school_name=school.school_name,
        teacher_number=admin.teacher_number or None,
        is_active=True,
        need_change_password=True  # 首次登录需修改密码
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return success_response(
        data=UserResponse.from_orm(db_user),
        message="学校管理员创建成功"
    )

# ============================================================================
# 教师管理
# ============================================================================

@router.post("/teachers", response_model=dict)
async def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """创建教师（学校管理员）"""
    
    # 获取学校ID
    if current_user.role == 'platform_admin':
        # 平台管理员需要指定学校（这里暂不支持，让其通过创建学校管理员的方式）
        return error_response(
            message="平台管理员请先创建学校管理员，再由学校管理员创建教师",
            code=400
        )
    
    school_id = current_user.school_id
    
    # 检查学校
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == teacher.username).first()
    if existing_user:
        return error_response(message="用户名已存在", code=400)
    
    # 检查邮箱是否已存在
    if teacher.email:
        existing_email = db.query(User).filter(User.email == teacher.email).first()
        if existing_email:
            return error_response(message="邮箱已存在", code=400)
    
    # 检查工号是否在该学校已存在
    existing_number = db.query(User).filter(
        User.school_id == school_id,
        User.teacher_number == teacher.teacher_number
    ).first()
    if existing_number:
        return error_response(message="工号在该学校已存在", code=400)
    
    # 检查是否超过最大教师数
    teacher_count = db.query(func.count(User.id)).filter(
        User.school_id == school_id,
        User.role.in_(['teacher', 'school_admin']),
        User.deleted_at.is_(None)
    ).scalar()
    
    if teacher_count >= school.max_teachers:
        return error_response(
            message=f"已达到最大教师数限制（{school.max_teachers}）",
            code=400
        )
    
    # 创建教师
    db_user = User(
        username=teacher.username,
        password_hash=get_password_hash(teacher.password),
        real_name=teacher.real_name,
        email=teacher.email,
        phone=teacher.phone,
        role='teacher',
        school_id=school_id,
        school_name=school.school_name,
        teacher_number=teacher.teacher_number,
        subject=teacher.subject,
        is_active=True,
        need_change_password=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return success_response(
        data=UserResponse.from_orm(db_user),
        message="教师创建成功"
    )

@router.get("/teachers", response_model=dict)
async def list_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """获取教师列表（学校管理员）"""
    
    # 获取学校ID
    if current_user.role == 'platform_admin':
        # 平台管理员可以看所有教师（暂不支持）
        school_id = None
    else:
        school_id = current_user.school_id
    
    # 构建查询
    query = db.query(User).filter(
        User.role == 'teacher',
        User.deleted_at.is_(None)
    )
    
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.real_name.like(f"%{keyword}%"),
                User.teacher_number.like(f"%{keyword}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    teachers = query.order_by(User.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式并添加课程信息
    teacher_list = []
    for teacher in teachers:
        teacher_data = UserListResponse.from_orm(teacher).model_dump()
        
        # 查询教师任教的课程
        course_relations = db.query(CourseTeacher, Course).join(
            Course, CourseTeacher.course_id == Course.id
        ).filter(
            CourseTeacher.teacher_id == teacher.id,
            CourseTeacher.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).all()
        
        # 生成课程名称列表
        course_names = [c.course_name for ct, c in course_relations]
        teacher_data['course_names'] = ', '.join(course_names) if course_names else None
        teacher_data['course_count'] = len(course_names)
        
        teacher_list.append(teacher_data)
    
    return success_response(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "teachers": teacher_list
        }
    )

# ============================================================================
# 学生管理
# ============================================================================

@router.post("/students", response_model=dict)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建学生（学校管理员或教师）"""
    
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限创建学生"
        )
    
    # 获取学校ID
    if current_user.role == 'platform_admin':
        return error_response(
            message="平台管理员请先创建学校管理员，再由学校管理员创建学生",
            code=400
        )
    
    school_id = current_user.school_id
    
    # 检查学校
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == student.username).first()
    if existing_user:
        return error_response(message="用户名已存在", code=400)
    
    # 检查邮箱是否已存在
    if student.email:
        existing_email = db.query(User).filter(User.email == student.email).first()
        if existing_email:
            return error_response(message="邮箱已存在", code=400)
    
    # 检查学号是否在该学校已存在
    existing_number = db.query(User).filter(
        User.school_id == school_id,
        User.student_number == student.student_number
    ).first()
    if existing_number:
        return error_response(message="学号在该学校已存在", code=400)
    
    # 检查是否超过最大学生数
    student_count = db.query(func.count(User.id)).filter(
        User.school_id == school_id,
        User.role == 'student',
        User.deleted_at.is_(None)
    ).scalar()
    
    if student_count >= school.max_students:
        return error_response(
            message=f"已达到最大学生数限制（{school.max_students}）",
            code=400
        )
    
    # 创建学生（简化版：学号、姓名、性别）
    db_user = User(
        username=student.username,
        password_hash=get_password_hash(student.password),
        real_name=student.real_name,
        gender=student.gender,
        student_number=student.student_number,
        role='student',
        school_id=school_id,
        school_name=school.school_name,
        is_active=True,
        need_change_password=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 如果提供了初始选课列表，自动选课
    if student.course_ids:
        for course_id in student.course_ids:
            course = db.query(Course).filter(
                Course.id == course_id,
                Course.school_id == school_id,
                Course.deleted_at.is_(None),
                Course.is_active == True
            ).first()
            
            if course:
                # 检查课程是否已满
                current_students = db.query(func.count(CourseStudent.id)).filter(
                    CourseStudent.course_id == course.id,
                    CourseStudent.status == 'enrolled',
                    CourseStudent.deleted_at.is_(None)
                ).scalar()
                
                if current_students < course.max_students:
                    enrollment = CourseStudent(
                        course_id=course.id,
                        student_id=db_user.id,
                        status='enrolled'
                    )
                    db.add(enrollment)
        
        db.commit()
    
    return success_response(
        data=UserResponse.from_orm(db_user).model_dump(),
        message="学生创建成功"
    )

@router.get("/students", response_model=dict)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学生列表（学校管理员或教师）"""
    
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看学生列表"
        )
    
    # 获取学校ID
    if current_user.role == 'platform_admin':
        school_id = None
    else:
        school_id = current_user.school_id
    
    # 构建查询
    query = db.query(User).filter(
        User.role == 'student',
        User.deleted_at.is_(None)
    )
    
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.real_name.like(f"%{keyword}%"),
                User.student_number.like(f"%{keyword}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    students = query.order_by(User.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式并添加课程信息
    student_list = []
    for student in students:
        student_data = UserListResponse.from_orm(student).model_dump()
        
        # 查询学生选修的课程
        course_enrollments = db.query(CourseStudent, Course).join(
            Course, CourseStudent.course_id == Course.id
        ).filter(
            CourseStudent.student_id == student.id,
            CourseStudent.status == 'enrolled',
            CourseStudent.deleted_at.is_(None),
            Course.deleted_at.is_(None)
        ).all()
        
        # 生成课程名称列表
        course_names = [c.course_name for cs, c in course_enrollments]
        student_data['course_names'] = ', '.join(course_names) if course_names else None
        student_data['course_count'] = len(course_names)
        
        # 计算总学分
        total_credits = sum(
            float(c.credits or 0) 
            for cs, c in db.query(CourseStudent, Course).join(
                Course, CourseStudent.course_id == Course.id
            ).filter(
                CourseStudent.student_id == student.id,
                CourseStudent.status == 'completed',
                CourseStudent.deleted_at.is_(None),
                Course.deleted_at.is_(None)
            ).all()
        )
        student_data['total_credits'] = total_credits
        
        student_list.append(student_data)
    
    return success_response(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "students": student_list
        }
    )

# ============================================================================
# 角色分配（独立用户→教师/学生）
# ============================================================================

@router.get("/search-individual-users", response_model=dict)
async def search_individual_users(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """搜索独立用户（用于添加为教师/学校管理员）
    
    支持通过用户名(username)或真实姓名(real_name)进行模糊搜索
    """
    
    # 构建查询
    query = db.query(User).filter(
        User.role == 'individual',
        User.school_id.is_(None),
        User.deleted_at.is_(None)
    )
    
    # 关键词搜索（仅搜索用户名和真实姓名）
    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.real_name.like(f"%{keyword}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    users = query.order_by(User.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式（添加设备和智能体数量）
    user_list = []
    for user in users:
        user_data = UserListResponse.from_orm(user)
        # TODO: 统计设备和智能体数量
        user_data.device_count = 0
        user_data.agent_count = 0
        user_list.append(user_data.model_dump())  # 转换为字典
    
    return success_response(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "users": user_list
        }
    )

@router.post("/users/{user_uuid}/assign-role", response_model=dict)
async def assign_role(
    user_uuid: str,
    assign_request: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """分配角色（将独立用户转为教师、学生或学校管理员）"""
    
    # 查找用户
    user = db.query(User).filter(
        User.uuid == user_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        return error_response(message="用户不存在", code=404)
    
    # 检查用户是否为独立用户
    if user.role != 'individual' or user.school_id is not None:
        return error_response(
            message="只能将独立用户转换为教师、学生或学校管理员",
            code=400
        )
    
    # 获取学校ID（如果是设置学校管理员，使用请求中的school_id；否则使用当前用户的school_id）
    if assign_request.new_role == 'school_admin':
        # 平台管理员可以设置任意学校的管理员
        if current_user.role != 'platform_admin':
            return error_response(
                message="只有平台管理员才能设置学校管理员",
                code=403
            )
        school_id = assign_request.school_id
    else:
        # 学校管理员只能为自己的学校添加教师/学生
        school_id = current_user.school_id
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 保存旧角色
    old_role = user.role
    
    # 根据新角色进行处理
    if assign_request.new_role == 'teacher':
        # 检查工号是否已存在
        existing_number = db.query(User).filter(
            User.school_id == school_id,
            User.teacher_number == assign_request.teacher_number
        ).first()
        if existing_number:
            return error_response(message="工号在该学校已存在", code=400)
        
        # 检查是否超过最大教师数
        teacher_count = db.query(func.count(User.id)).filter(
            User.school_id == school_id,
            User.role.in_(['teacher', 'school_admin']),
            User.deleted_at.is_(None)
        ).scalar()
        
        if teacher_count >= school.max_teachers:
            return error_response(
                message=f"已达到最大教师数限制（{school.max_teachers}）",
                code=400
            )
        
        # 更新用户信息
        user.role = 'teacher'
        user.school_id = school_id
        user.school_name = school.school_name
        user.teacher_number = assign_request.teacher_number
        user.subject = assign_request.subject
        
    elif assign_request.new_role == 'student':
        # 检查学号是否已存在
        existing_number = db.query(User).filter(
            User.school_id == school_id,
            User.student_number == assign_request.student_number
        ).first()
        if existing_number:
            return error_response(message="学号在该学校已存在", code=400)
        
        # 检查是否超过最大学生数
        student_count = db.query(func.count(User.id)).filter(
            User.school_id == school_id,
            User.role == 'student',
            User.deleted_at.is_(None)
        ).scalar()
        
        if student_count >= school.max_students:
            return error_response(
                message=f"已达到最大学生数限制（{school.max_students}）",
                code=400
            )
        
        # 更新用户信息
        user.role = 'student'
        user.school_id = school_id
        user.school_name = school.school_name
        user.student_number = assign_request.student_number
        
    elif assign_request.new_role == 'school_admin':
        # 检查工号是否已存在
        existing_number = db.query(User).filter(
            User.school_id == school_id,
            User.teacher_number == assign_request.teacher_number,
            User.deleted_at.is_(None)
        ).first()
        if existing_number:
            return error_response(message="工号在该学校已存在", code=400)
        
        # 检查是否超过最大教师数（学校管理员也算在教师数内）
        teacher_count = db.query(func.count(User.id)).filter(
            User.school_id == school_id,
            User.role.in_(['teacher', 'school_admin']),
            User.deleted_at.is_(None)
        ).scalar()
        
        if teacher_count >= school.max_teachers:
            return error_response(
                message=f"已达到最大教师数限制（{school.max_teachers}）",
                code=400
            )
        
        # 更新用户信息
        user.role = 'school_admin'
        user.school_id = school_id
        user.school_name = school.school_name
        user.teacher_number = assign_request.teacher_number
        user.subject = assign_request.subject  # 学校管理员也可以有学科
    
    # TODO: 更新用户的设备和智能体的school_id
    
    db.commit()
    db.refresh(user)
    
    # 构建响应
    response = AssignRoleResponse(
        user_id=user.id,
        username=user.username,
        old_role=old_role,
        new_role=user.role,
        school_id=user.school_id,
        school_name=user.school_name,
        teacher_number=user.teacher_number,
        student_number=user.student_number,
        devices_retained=0,  # TODO: 统计设备数
        agents_retained=0,  # TODO: 统计智能体数
        message="角色分配成功，用户已转为" + ("教师" if user.role == 'teacher' else "学生")
    )
    
    return success_response(data=response)

# ============================================================================
# 用户信息更新
# ============================================================================

@router.put("/users/{user_uuid}", response_model=dict)
async def update_user(
    user_uuid: str,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息（管理员用）"""
    
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限更新用户信息"
        )
    
    # 查找用户
    user = db.query(User).filter(
        User.uuid == user_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        return error_response(message="用户不存在", code=404)
    
    # 学校管理员只能更新本校用户
    if current_user.role == 'school_admin':
        if user.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能更新本校用户"
            )
    
    # 更新字段
    if is_active is not None:
        user.is_active = is_active
    
    db.commit()
    db.refresh(user)
    
    return success_response(
        data=UserResponse.from_orm(user),
        message="用户信息更新成功"
    )

@router.delete("/users/{user_uuid}", response_model=dict)
async def delete_user(
    user_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户（软删除）"""
    
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除用户"
        )
    
    # 查找用户
    user = db.query(User).filter(
        User.uuid == user_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        return error_response(message="用户不存在", code=404)
    
    # 学校管理员只能删除本校用户
    if current_user.role == 'school_admin':
        if user.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能删除本校用户"
            )
    
    # 管理员不能删除自己
    if user.id == current_user.id:
        return error_response(message="管理员不能删除自己", code=400)
    
    # 软删除
    user.deleted_at = get_beijing_time_naive()
    user.is_active = False
    
    db.commit()
    
    return success_response(message="用户删除成功")


# ============================================================================
# 批量导入功能
# ============================================================================

@router.post("/teachers/batch-import", response_model=dict)
async def batch_import_teachers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin_or_teacher)
):
    """
    批量导入教师（Excel文件）
    事务回滚：遇到错误全部回滚
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin']:
        return error_response(message="只有学校管理员才能批量导入教师", code=403)
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error_response(message="只支持Excel文件格式（.xlsx, .xls）", code=400)
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析Excel
        teachers_data, parse_errors = parse_teacher_excel(file_content)
        
        if parse_errors:
            return error_response(
                message="Excel文件解析失败",
                code=400,
                data={"errors": parse_errors}
            )
        
        if not teachers_data:
            return error_response(message="Excel文件中没有有效数据", code=400)
        
        # 获取学校ID
        school_id = current_user.school_id
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            return error_response(message="学校不存在", code=404)
        
        # 开始事务
        success_count = 0
        error_count = 0
        errors = []
        created_users = []
        
        try:
            for idx, teacher_data in enumerate(teachers_data, 1):
                try:
                    # 检查用户名是否已存在
                    existing = db.query(User).filter(
                        User.username == teacher_data['username'],
                        User.deleted_at.is_(None)
                    ).first()
                    
                    if existing:
                        errors.append(f"第{idx}条：用户名'{teacher_data['username']}'已存在")
                        error_count += 1
                        # 全部回滚
                        raise Exception(f"用户名'{teacher_data['username']}'已存在")
                    
                    # 检查工号是否已存在
                    existing_number = db.query(User).filter(
                        User.teacher_number == teacher_data['teacher_number'],
                        User.school_id == school_id,
                        User.deleted_at.is_(None)
                    ).first()
                    
                    if existing_number:
                        errors.append(f"第{idx}条：工号'{teacher_data['teacher_number']}'已存在")
                        error_count += 1
                        raise Exception(f"工号'{teacher_data['teacher_number']}'已存在")
                    
                    # 创建教师
                    db_user = User(
                        username=teacher_data['username'],
                        password_hash=get_password_hash(teacher_data['password']),
                        real_name=teacher_data['real_name'],
                        teacher_number=teacher_data['teacher_number'],
                        subject=teacher_data.get('subject'),
                        phone=teacher_data.get('phone'),
                        role='teacher',
                        school_id=school_id,
                        school_name=school.school_name,
                        is_active=True,
                        need_change_password=True
                    )
                    
                    db.add(db_user)
                    created_users.append({
                        'username': teacher_data['username'],
                        'real_name': teacher_data['real_name'],
                        'teacher_number': teacher_data['teacher_number']
                    })
                    success_count += 1
                    
                except Exception as e:
                    # 遇到错误，回滚所有操作
                    db.rollback()
                    return error_response(
                        message=f"导入失败：{str(e)}",
                        code=400,
                        data={
                            "total": len(teachers_data),
                            "success": 0,
                            "failed": len(teachers_data),
                            "errors": errors + [str(e)]
                        }
                    )
            
            # 全部成功，提交事务
            db.commit()
            
            return success_response(
                message=f"批量导入成功！共导入{success_count}名教师",
                data={
                    "total": len(teachers_data),
                    "success": success_count,
                    "failed": 0,
                    "created_users": created_users
                }
            )
            
        except Exception as e:
            db.rollback()
            return error_response(
                message=f"批量导入失败：{str(e)}",
                code=500,
                data={"errors": errors}
            )
            
    except Exception as e:
        return error_response(message=f"文件处理失败：{str(e)}", code=500)


@router.post("/students/batch-import", response_model=dict)
async def batch_import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin_or_teacher)
):
    """
    批量导入学生（Excel文件）
    事务回滚：遇到错误全部回滚
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin']:
        return error_response(message="只有学校管理员才能批量导入学生", code=403)
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error_response(message="只支持Excel文件格式（.xlsx, .xls）", code=400)
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析Excel
        students_data, parse_errors = parse_student_excel(file_content)
        
        if parse_errors:
            return error_response(
                message="Excel文件解析失败",
                code=400,
                data={"errors": parse_errors}
            )
        
        if not students_data:
            return error_response(message="Excel文件中没有有效数据", code=400)
        
        # 获取学校ID
        school_id = current_user.school_id
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            return error_response(message="学校不存在", code=404)
        
        # 开始事务
        success_count = 0
        error_count = 0
        errors = []
        created_users = []
        
        try:
            for idx, student_data in enumerate(students_data, 1):
                try:
                    # 检查用户名是否已存在
                    existing = db.query(User).filter(
                        User.username == student_data['username'],
                        User.deleted_at.is_(None)
                    ).first()
                    
                    if existing:
                        errors.append(f"第{idx}条：用户名'{student_data['username']}'已存在")
                        error_count += 1
                        raise Exception(f"用户名'{student_data['username']}'已存在")
                    
                    # 检查学号是否已存在
                    existing_number = db.query(User).filter(
                        User.student_number == student_data['student_number'],
                        User.school_id == school_id,
                        User.deleted_at.is_(None)
                    ).first()
                    
                    if existing_number:
                        errors.append(f"第{idx}条：学号'{student_data['student_number']}'已存在")
                        error_count += 1
                        raise Exception(f"学号'{student_data['student_number']}'已存在")
                    
                    # 创建学生
                    db_user = User(
                        username=student_data['username'],
                        password_hash=get_password_hash(student_data['password']),
                        real_name=student_data['real_name'],
                        gender=student_data['gender'],
                        student_number=student_data['student_number'],
                        role='student',
                        school_id=school_id,
                        school_name=school.school_name,
                        is_active=True,
                        need_change_password=True
                    )
                    
                    db.add(db_user)
                    created_users.append({
                        'username': student_data['username'],
                        'real_name': student_data['real_name'],
                        'student_number': student_data['student_number']
                    })
                    success_count += 1
                    
                except Exception as e:
                    # 遇到错误，回滚所有操作
                    db.rollback()
                    return error_response(
                        message=f"导入失败：{str(e)}",
                        code=400,
                        data={
                            "total": len(students_data),
                            "success": 0,
                            "failed": len(students_data),
                            "errors": errors + [str(e)]
                        }
                    )
            
            # 全部成功，提交事务
            db.commit()
            
            return success_response(
                message=f"批量导入成功！共导入{success_count}名学生",
                data={
                    "total": len(students_data),
                    "success": success_count,
                    "failed": 0,
                    "created_users": created_users
                }
            )
            
        except Exception as e:
            db.rollback()
            return error_response(
                message=f"批量导入失败：{str(e)}",
                code=500,
                data={"errors": errors}
            )
            
    except Exception as e:
        return error_response(message=f"文件处理失败：{str(e)}", code=500)


@router.get("/teachers/import-template")
async def download_teacher_template(
    current_user: User = Depends(check_school_admin_or_teacher)
):
    """下载教师导入模板"""
    template = generate_teacher_template()
    
    return StreamingResponse(
        template,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=teacher_import_template.xlsx"
        }
    )


@router.get("/students/import-template")
async def download_student_template(
    current_user: User = Depends(check_school_admin_or_teacher)
):
    """下载学生导入模板"""
    template = generate_student_template()
    
    return StreamingResponse(
        template,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=student_import_template.xlsx"
        }
    )

