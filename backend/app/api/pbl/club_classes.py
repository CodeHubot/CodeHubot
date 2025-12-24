"""
社团班课程系统API
- 班级管理（创建、列表、详情、更新、删除）
- 班级成员管理（添加、移除、设置角色）
- 基于模板创建课程并自动选课
- 学生端班级和课程查询
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, select
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from app.utils.timezone import get_beijing_time_naive
from pydantic import BaseModel

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...core.security import get_password_hash
from ...models.admin import Admin, User
from ...models.pbl import (
    PBLClass, PBLClassMember, PBLCourse, PBLCourseTemplate, PBLClassCourse,
    PBLUnit, PBLResource, PBLTask,
    PBLClassTeacher, PBLTaskProgress, PBLProjectOutput,
    PBLUnitTemplate, PBLResourceTemplate, PBLTaskTemplate
)
from ...core.logging_config import get_logger
from ...models.school import School

router = APIRouter()
logger = get_logger(__name__)

# ===== 权限检查辅助函数 =====

def check_class_permission(
    pbl_class: PBLClass,
    current_admin: Admin,
    db: Session,
    allow_teacher: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    检查用户是否有权限操作班级
    
    Args:
        pbl_class: 班级对象
        current_admin: 当前用户
        db: 数据库会话
        allow_teacher: 是否允许教师操作（默认True）
        
    Returns:
        (has_permission, error_message): 是否有权限及错误信息
    """
    # 1. 平台管理员有所有权限
    if current_admin.role == 'platform_admin':
        return True, None
    
    # 2. 学校管理员只能操作本学校的班级
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return False, "无权限操作该班级"
        return True, None
    
    # 3. 教师只能操作自己教授的班级
    if current_admin.role == 'teacher' and allow_teacher:
        is_class_teacher = db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.teacher_id == current_admin.id
        ).first()
        
        if not is_class_teacher:
            return False, "您不是该班级的教师，无权限操作"
        return True, None
    
    # 4. 其他角色无权限
    return False, "无权限操作"

# ===== Pydantic 模型 =====

class ClassCreate(BaseModel):
    name: str
    class_type: str = 'club'  # club, project, interest, competition, regular
    description: Optional[str] = None
    max_students: int = 30
    template_id: Optional[int] = None  # 课程模板ID

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    class_type: Optional[str] = None
    description: Optional[str] = None
    max_students: Optional[int] = None
    is_open: Optional[bool] = None

class MemberAdd(BaseModel):
    student_ids: List[int]
    role: str = 'member'

class MemberRoleUpdate(BaseModel):
    role: str  # member, leader, deputy

class CourseCreateFromTemplate(BaseModel):
    template_id: int
    class_id: int
    title: Optional[str] = None
    auto_enroll: bool = True

class TeacherAdd(BaseModel):
    teacher_ids: List[int]
    role: str = 'assistant'  # main, assistant

class TeacherRoleUpdate(BaseModel):
    role: str  # main, assistant

class TaskReview(BaseModel):
    score: Optional[int] = None
    grade: Optional[str] = None  # excellent, good, pass, fail
    feedback: Optional[str] = None
    status: str = 'review'  # review, completed

class StudentPasswordReset(BaseModel):
    """重置学生密码请求"""
    student_id: int
    new_password: str = "Aa123456"  # 默认密码

# ===== 班级管理 =====

@router.get("/classes")
def get_classes(
    school_id: Optional[int] = None,
    class_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级列表（支持按类型筛选）"""
    # 权限控制
    if current_admin.role == 'teacher':
        # 教师只能查看自己教授的班级
        teacher_class_ids = db.query(PBLClassTeacher.class_id).filter(
            PBLClassTeacher.teacher_id == current_admin.id
        ).all()
        teacher_class_ids = [item[0] for item in teacher_class_ids]
        
        query = db.query(PBLClass).filter(
            PBLClass.is_active == 1,
            PBLClass.id.in_(teacher_class_ids) if teacher_class_ids else False
        )
    else:
        # 平台管理员和学校管理员
        if current_admin.role != 'platform_admin':
            school_id = current_admin.school_id
        
        # 构建查询
        query = db.query(PBLClass).filter(PBLClass.is_active == 1)
        
        if school_id:
            query = query.filter(PBLClass.school_id == school_id)
    
    if class_type:
        query = query.filter(PBLClass.class_type == class_type)
    
    classes = query.order_by(PBLClass.created_at.desc()).all()
    
    result = []
    for cls in classes:
        # 获取班级的课程（一个班级对应一个课程）
        course = db.query(PBLCourse).filter(
            PBLCourse.class_id == cls.id,
            PBLCourse.status == 'published'
        ).first()
        
        result.append({
            'id': cls.id,
            'uuid': cls.uuid,
            'name': cls.name,
            'class_type': cls.class_type,
            'description': cls.description,
            'school_id': cls.school_id,
            'max_students': cls.max_students,
            'current_members': cls.current_members or 0,  # 直接使用字段，性能更好
            'is_open': cls.is_open == 1,
            'is_active': cls.is_active == 1,
            'created_at': cls.created_at.isoformat() if cls.created_at else None,
            # 课程信息
            'course': {
                'id': course.id,
                'uuid': course.uuid,
                'title': course.title,
                'description': course.description,
                'cover_image': course.cover_image,
                'difficulty': course.difficulty,
                'duration': course.duration,
                'teacher_id': course.teacher_id,
                'teacher_name': course.teacher_name,
                'start_date': course.start_date.isoformat() if course.start_date else None,
                'end_date': course.end_date.isoformat() if course.end_date else None,
                'enrolled_count': cls.current_members or 0  # 使用班级成员数
            } if course else None
        })
    
    return success_response(data=result)


@router.post("/classes")
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建班级
    
    如果提供template_id，将从模板创建完整的课程实例并关联到班级
    教师创建的班级，自动成为该班级的主讲教师
    """
    # 权限检查（允许教师创建班级）
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 从当前管理员获取学校ID
    school_id = current_admin.school_id
    if not school_id:
        return error_response(
            message="您未关联学校，无法创建班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 创建班级
    new_class = PBLClass(
        school_id=school_id,
        name=class_data.name,
        class_type=class_data.class_type,
        description=class_data.description,
        max_students=class_data.max_students,
        current_members=0,
        is_active=1,
        is_open=1
    )
    db.add(new_class)
    db.flush()  # 获取班级ID
    
    # 如果提供了template_id，从模板创建完整的课程
    course_id = None
    course_title = None
    if class_data.template_id:
        from ...services.template_service import copy_course_from_template, validate_template_permission
        
        try:
            # 验证模板权限
            template, permission = validate_template_permission(db, class_data.template_id, school_id)
            
            # 从模板复制完整的课程（包括单元、资源、任务）
            new_course = copy_course_from_template(
                db=db,
                template_id=class_data.template_id,
                school_id=school_id,
                creator_id=current_admin.id,
                class_id=new_class.id,
                class_name=class_data.name,
                permission_id=permission.id
            )
            
            course_id = new_course.id
            course_title = new_course.title
            
            # 创建班级课程关联记录
            class_course = PBLClassCourse(
                class_id=new_class.id,
                course_id=course_id,
                assigned_by=current_admin.id,
                status='active'
            )
            db.add(class_course)
            
            # 更新权限的实例计数
            instance_count = db.query(PBLCourse).filter(
                PBLCourse.template_id == class_data.template_id,
                PBLCourse.school_id == school_id
            ).count()
            permission.current_instances = instance_count
            
            logger.info(f"从模板创建完整课程 - 模板ID: {class_data.template_id}, 课程ID: {course_id}, 班级ID: {new_class.id}")
            
        except ValueError as e:
            db.rollback()
            return error_response(
                message=str(e),
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"从模板创建课程失败: {str(e)}", exc_info=True)
            db.rollback()
            return error_response(
                message=f"从模板创建课程失败: {str(e)}",
                code=500,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # 如果是教师创建的班级，自动添加为主讲教师
    if current_admin.role == 'teacher':
        class_teacher = PBLClassTeacher(
            class_id=new_class.id,
            teacher_id=current_admin.id,
            role='main',  # 主讲教师
            is_primary=1  # 班主任
        )
        db.add(class_teacher)
        logger.info(f"自动添加教师为班级主讲 - 教师ID: {current_admin.id}, 班级ID: {new_class.id}")
    
    db.commit()
    db.refresh(new_class)
    
    log_message = f"创建班级 - 名称: {class_data.name}, 类型: {class_data.class_type}, 学校ID: {school_id}"
    if course_title:
        log_message += f", 关联课程: {course_title}"
    logger.info(log_message)
    
    result_data = {
        'id': new_class.id,
        'uuid': new_class.uuid,
        'name': new_class.name,
        'class_type': new_class.class_type,
        'description': new_class.description,
        'max_students': new_class.max_students,
        'current_members': new_class.current_members,
        'created_at': new_class.created_at.isoformat() if new_class.created_at else None
    }
    
    # 如果创建了课程，添加课程信息到返回数据
    if course_id:
        result_data['course'] = {
            'id': course_id,
            'title': course_title
        }
    
    message = "班级创建成功"
    if course_title:
        message = f"班级创建成功，并已关联课程「{course_title}」"
    
    return success_response(
        data=result_data,
        message=message
    )


@router.get("/classes/{class_uuid}")
def get_class_detail(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级详情（优化版）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级成员
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    member_list = []
    for member, user in members:
        member_list.append({
            'student_id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number,
            'role': member.role,
            'joined_at': member.joined_at.isoformat() if member.joined_at else None
        })
    
    # 获取班级课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    course_list = []
    for course in courses:
        course_list.append({
            'id': course.id,
            'uuid': course.uuid,
            'title': course.title,
            'description': course.description,
            'cover_image': course.cover_image,
            'enrolled_count': pbl_class.current_members or 0  # 使用班级成员数
        })
    
    return success_response(data={
        'id': pbl_class.id,
        'uuid': pbl_class.uuid,
        'name': pbl_class.name,
        'class_type': pbl_class.class_type,
        'description': pbl_class.description,
        'max_students': pbl_class.max_students,
        'current_members': pbl_class.current_members or 0,  # 直接使用字段
        'is_open': pbl_class.is_open == 1,
        'is_active': pbl_class.is_active == 1,
        'members': member_list,
        'courses': course_list,
        'created_at': pbl_class.created_at.isoformat() if pbl_class.created_at else None
    })


@router.put("/classes/{class_uuid}")
def update_class(
    class_uuid: str,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新班级信息"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师修改）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 更新字段
    if class_data.name is not None:
        pbl_class.name = class_data.name
    if class_data.class_type is not None:
        pbl_class.class_type = class_data.class_type
    if class_data.description is not None:
        pbl_class.description = class_data.description
    if class_data.max_students is not None:
        pbl_class.max_students = class_data.max_students
    if class_data.is_open is not None:
        pbl_class.is_open = 1 if class_data.is_open else 0
    
    db.commit()
    db.refresh(pbl_class)
    
    logger.info(f"更新班级 - UUID: {class_uuid}, 操作者: {current_admin.username}")
    
    return success_response(message="班级更新成功")


@router.delete("/classes/{class_uuid}")
def delete_class(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除班级（软删除）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 软删除
    pbl_class.is_active = 0
    db.commit()
    
    logger.info(f"删除班级 - UUID: {class_uuid}, 操作者: {current_admin.username}")
    
    return success_response(message="班级已删除")


# ===== 班级成员管理 =====

@router.get("/classes/{class_uuid}/available-students")
def get_available_students(
    class_uuid: str,
    search: Optional[str] = Query(None, description="搜索关键词（姓名或学号）"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取可添加到班级的学生列表（学校学生中未在该班级的学生）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role == 'teacher':
        # 教师需要是该班级的授课教师
        is_class_teacher = db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.teacher_id == current_admin.id
        ).first()
        
        if not is_class_teacher:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    elif current_admin.role == 'school_admin':
        # 学校管理员只能操作本校班级
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    elif current_admin.role != 'platform_admin':
        # 其他角色无权限
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 获取已在班级中的学生ID列表
    existing_member_ids = db.query(PBLClassMember.student_id).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    existing_member_ids = [row[0] for row in existing_member_ids]
    
    # 查询学校的所有学生（排除已在班级中的）
    query = db.query(User).filter(
        User.school_id == pbl_class.school_id,
        User.role == 'student',
        User.is_active == True,
        User.deleted_at == None
    )
    
    # 排除已在班级中的学生
    if existing_member_ids:
        query = query.filter(User.id.notin_(existing_member_ids))
    
    # 支持搜索
    if search:
        query = query.filter(
            or_(
                User.name.like(f'%{search}%'),
                User.real_name.like(f'%{search}%'),
                User.student_number.like(f'%{search}%')
            )
        )
    
    # 按学号排序
    students = query.order_by(User.student_number).limit(100).all()
    
    result = []
    for student in students:
        result.append({
            'id': student.id,
            'name': student.name or student.real_name,
            'student_number': student.student_number,
            'gender': student.gender,
            'class_name': student.class_name if hasattr(student, 'class_name') else None
        })
    
    return success_response(data=result)


@router.get("/classes/{class_uuid}/members")
def get_class_members(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级成员列表"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )

    # 查询成员（关联School表获取school_code）
    members = db.query(PBLClassMember, User, School).join(
        User, PBLClassMember.student_id == User.id
    ).join(
        School, User.school_id == School.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()

    result = []
    for member, user, school in members:
        # 构建登录名：学号@学校代码
        login_name = f"{user.student_number}@{school.school_code}" if user.student_number and school.school_code else None
        
        result.append({
            'student_id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number,
            'school_code': school.school_code,
            'login_name': login_name,
            'gender': user.gender,
            'role': member.role,
            'joined_at': member.joined_at.isoformat() if member.joined_at else None
        })

    return success_response(data=result)


@router.post("/classes/{class_uuid}/members")
def add_members_to_class(
    class_uuid: str,
    member_data: MemberAdd,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """添加成员到班级（并自动为其选上班级的所有课程）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师添加学生）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    added_count = 0
    auto_enrolled_courses = []
    
    for student_id in member_data.student_ids:
        # 检查学生是否存在
        student = db.query(User).filter(
            User.id == student_id,
            User.role == 'student'
        ).first()
        
        if not student:
            continue
        
        # 权限检查：学校管理员只能操作本校学生
        if current_admin.role == 'school_admin':
            if student.school_id != current_admin.school_id:
                continue
        
        # 检查是否已在班级中
        existing = db.query(PBLClassMember).filter(
            PBLClassMember.class_id == pbl_class.id,
            PBLClassMember.student_id == student_id,
            PBLClassMember.is_active == 1
        ).first()
        
        if existing:
            continue
        
        # 添加到班级
        member = PBLClassMember(
            class_id=pbl_class.id,
            student_id=student_id,
            role=member_data.role,
            is_active=1
        )
        db.add(member)
        added_count += 1
        
        # 更新班级成员数
        pbl_class.current_members = (pbl_class.current_members or 0) + 1
        
        # 注意：班级成员自动拥有班级课程的访问权限，无需创建选课记录
    
    db.commit()
    
    logger.info(f"添加成员到班级 - 班级UUID: {class_uuid}, 成功: {added_count}, 自动选课: {len(auto_enrolled_courses)}")
    
    return success_response(
        data={
            'added_count': added_count,
            'auto_enrolled_courses': auto_enrolled_courses
        },
        message=f"成功添加 {added_count} 名成员到班级"
    )


@router.delete("/classes/{class_uuid}/members/{student_id}")
def remove_member_from_class(
    class_uuid: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """从班级移除成员"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师移除学生）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 查找成员记录
    member = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.student_id == student_id,
        PBLClassMember.is_active == 1
    ).first()
    
    if not member:
        return error_response(
            message="学生不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 软删除（标记为非活跃）
    member.is_active = 0
    member.left_at = get_beijing_time_naive()
    
    # 更新班级成员数
    if pbl_class.current_members > 0:
        pbl_class.current_members -= 1
    
    db.commit()
    
    logger.info(f"从班级移除成员 - 班级UUID: {class_uuid}, 学生ID: {student_id}")
    
    return success_response(message="成员已从班级移除")


@router.put("/classes/{class_uuid}/members/{student_id}/role")
def update_member_role(
    class_uuid: str,
    student_id: int,
    role_data: MemberRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """设置班级成员角色"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师设置学生角色）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 查找成员记录
    member = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.student_id == student_id,
        PBLClassMember.is_active == 1
    ).first()
    
    if not member:
        return error_response(
            message="学生不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 如果设置为班长，需要取消其他班长
    if role_data.role == 'leader':
        db.query(PBLClassMember).filter(
            PBLClassMember.class_id == pbl_class.id,
            PBLClassMember.role == 'leader',
            PBLClassMember.is_active == 1
        ).update({'role': 'member'})
    
    # 更新角色
    member.role = role_data.role
    db.commit()
    
    logger.info(f"更新成员角色 - 班级UUID: {class_uuid}, 学生ID: {student_id}, 角色: {role_data.role}")
    
    return success_response(message=f"成员角色已更新为 {role_data.role}")


@router.post("/classes/{class_uuid}/members/{student_id}/reset-password")
def reset_member_password(
    class_uuid: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """重置班级成员密码（教师专用）
    
    将学生密码重置为默认密码（Aa123456），并标记为需要强制修改密码
    """
    # 查找班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查：教师、学校管理员、平台管理员
    if current_admin.role == 'teacher':
        # 教师需要是该班级的授课教师
        is_class_teacher = db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.teacher_id == current_admin.id
        ).first()
        
        if not is_class_teacher:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    elif current_admin.role == 'school_admin':
        # 学校管理员只能操作本校班级
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    elif current_admin.role != 'platform_admin':
        # 其他角色无权限
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查学生是否在班级中
    member = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.student_id == student_id,
        PBLClassMember.is_active == 1
    ).first()
    
    if not member:
        return error_response(
            message="学生不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查找学生用户
    student = db.query(User).filter(
        User.id == student_id,
        User.role == 'student'
    ).first()
    
    if not student:
        return error_response(
            message="学生用户不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查：学校管理员只能操作本校学生
    if current_admin.role == 'school_admin':
        if student.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该学生",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 重置密码为默认密码
    default_password = "Aa123456"
    student.password_hash = get_password_hash(default_password)
    
    # 标记需要强制修改密码
    student.need_change_password = True
    
    db.commit()
    
    logger.info(f"重置学生密码 - 班级UUID: {class_uuid}, 学生ID: {student_id}, 学生姓名: {student.name}, 操作者: {current_admin.username}")
    
    return success_response(
        data={
            'student_id': student.id,
            'student_name': student.name or student.real_name,
            'default_password': default_password
        },
        message=f"已重置学生 {student.name or student.real_name} 的密码为：{default_password}，该学生下次登录后需强制修改密码"
    )


# ===== 基于模板创建课程 =====

@router.get("/course-templates")
def get_course_templates(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取课程模板列表"""
    query = db.query(PBLCourseTemplate).filter(PBLCourseTemplate.is_public == 1)
    
    if category:
        query = query.filter(PBLCourseTemplate.category == category)
    if difficulty:
        query = query.filter(PBLCourseTemplate.difficulty == difficulty)
    
    templates = query.order_by(PBLCourseTemplate.created_at.desc()).all()
    
    result = []
    for template in templates:
        result.append({
            'id': template.id,
            'uuid': template.uuid,
            'title': template.title,
            'description': template.description,
            'cover_image': template.cover_image,
            'duration': template.duration,
            'difficulty': template.difficulty,
            'category': template.category,
            'version': template.version,
            'usage_count': template.usage_count,
            'created_at': template.created_at.isoformat() if template.created_at else None
        })
    
    return success_response(data=result)


@router.post("/courses/create-from-template")
def create_course_from_template(
    course_data: CourseCreateFromTemplate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """基于模板为班级创建课程（并自动为班级成员选课）"""
    # 检查班级是否存在
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course_data.class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师为自己的班级创建课程）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查模板是否存在
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.id == course_data.template_id
    ).first()
    if not template:
        return error_response(
            message="课程模板不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 创建课程
    course_title = course_data.title if course_data.title else f"{pbl_class.name}{template.title}"
    
    new_course = PBLCourse(
        template_id=template.id,
        template_version=template.version,
        is_customized=0,
        sync_with_template=1,
        class_id=pbl_class.id,
        class_name=pbl_class.name,
        title=course_title,
        description=template.description,
        cover_image=template.cover_image,
        duration=template.duration,
        difficulty=template.difficulty,
        status='published',
        creator_id=current_admin.id,
        school_id=pbl_class.school_id
    )
    db.add(new_course)
    db.flush()
    
    # 从模板复制单元、资源、任务
    units_count = 0
    resources_count = 0
    tasks_count = 0
    
    # 查询模板的所有单元（包括关联的资源和任务）
    template_units = db.query(PBLUnitTemplate).filter(
        PBLUnitTemplate.course_template_id == template.id
    ).order_by(PBLUnitTemplate.order).all()
    
    # 复制单元、资源、任务
    for template_unit in template_units:
        # 创建单元副本，默认状态为 'locked'（关闭）
        new_unit = PBLUnit(
            course_id=new_course.id,
            title=template_unit.title,
            description=template_unit.description,
            order=template_unit.order,
            status='locked',  # 默认关闭
            learning_guide=template_unit.learning_objectives  # 复制学习目标作为学习指南
        )
        db.add(new_unit)
        db.flush()  # 获取新单元的ID
        units_count += 1
        
        # 复制资源
        template_resources = db.query(PBLResourceTemplate).filter(
            PBLResourceTemplate.unit_template_id == template_unit.id
        ).order_by(PBLResourceTemplate.order).all()
        
        for template_resource in template_resources:
            new_resource = PBLResource(
                unit_id=new_unit.id,
                type=template_resource.type,
                title=template_resource.title,
                description=template_resource.description,
                url=template_resource.url,
                content=template_resource.content,
                duration=template_resource.duration,
                order=template_resource.order,
                video_id=template_resource.video_id,
                video_cover_url=template_resource.video_cover_url,
                max_views=template_resource.default_max_views
            )
            db.add(new_resource)
            resources_count += 1
        
        # 复制任务
        template_tasks = db.query(PBLTaskTemplate).filter(
            PBLTaskTemplate.unit_template_id == template_unit.id
        ).order_by(PBLTaskTemplate.order).all()
        
        for template_task in template_tasks:
            new_task = PBLTask(
                unit_id=new_unit.id,
                title=template_task.title,
                description=template_task.description,
                type=template_task.type,
                difficulty=template_task.difficulty,
                estimated_time=template_task.estimated_time,
                order=template_task.order,
                requirements=template_task.requirements,
                prerequisites=template_task.prerequisites,
                is_required=1,  # 默认必做
                publish_status='draft'  # 默认草稿状态
            )
            db.add(new_task)
            tasks_count += 1
    
    # 注意：班级成员自动拥有班级课程的访问权限，无需创建选课记录
    # 统计班级成员数量
    enrolled_count = 0
    if course_data.auto_enroll:
        enrolled_count = db.query(PBLClassMember).filter(
            PBLClassMember.class_id == pbl_class.id,
            PBLClassMember.is_active == 1
        ).count()
    
    # 更新模板使用次数
    template.usage_count += 1
    
    db.commit()
    db.refresh(new_course)
    
    logger.info(f"基于模板创建课程 - 模板ID: {template.id}, 班级ID: {pbl_class.id}, 课程ID: {new_course.id}")
    
    return success_response(
        data={
            'course_id': new_course.id,
            'course_uuid': new_course.uuid,
            'title': new_course.title,
            'class_name': pbl_class.name,
            'template_title': template.title,
            'units_count': units_count,
            'resources_count': resources_count,
            'tasks_count': tasks_count,
            'enrolled_students': enrolled_count
        },
        message="课程创建成功"
    )


# ===== 为课程的班级成员批量选课 =====

@router.post("/courses/{course_id}/enroll-class-members")
def enroll_class_members_to_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """为课程的班级成员批量选课"""
    # 检查课程是否存在
    course = db.query(PBLCourse).filter(PBLCourse.id == course_id).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if not course.class_id:
        return error_response(
            message="该课程未关联班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 获取班级对象进行权限检查
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    if not pbl_class:
        return error_response(
            message="关联的班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（允许教师为自己班级的课程批量选课）
    has_permission, error_msg = check_class_permission(pbl_class, current_admin, db, allow_teacher=True)
    if not has_permission:
        return error_response(
            message=error_msg,
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 注意：班级成员自动拥有班级课程的访问权限，无需创建选课记录
    # 统计班级成员数量
    enrolled_count = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == course.class_id,
        PBLClassMember.is_active == 1
    ).count()

    db.commit()
    
    logger.info(f"批量选课 - 课程ID: {course_id}, 班级ID: {course.class_id}, 选课人数: {enrolled_count}")
    
    return success_response(
        data={'enrolled_count': enrolled_count},
        message=f"成功为 {enrolled_count} 名学生选课"
    )


# ===== 教师管理 =====

@router.get("/classes/{class_uuid}/teachers")
def get_class_teachers(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级教师列表"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 查询教师
    teachers = db.query(PBLClassTeacher, User).join(
        User, PBLClassTeacher.teacher_id == User.id
    ).filter(
        PBLClassTeacher.class_id == pbl_class.id
    ).all()
    
    result = []
    for teacher_rel, user in teachers:
        result.append({
            'teacher_id': user.id,
            'name': user.name or user.real_name,
            'username': user.username,
            'role': teacher_rel.role if hasattr(teacher_rel, 'role') else 'assistant',
            'subject': teacher_rel.subject,
            'is_primary': teacher_rel.is_primary == 1,
            'added_at': teacher_rel.added_at.isoformat() if hasattr(teacher_rel, 'added_at') and teacher_rel.added_at else teacher_rel.created_at.isoformat()
        })
    
    return success_response(data=result)


@router.post("/classes/{class_uuid}/teachers")
def add_teachers_to_class(
    class_uuid: str,
    teacher_data: TeacherAdd,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """添加教师到班级"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    added_count = 0
    for teacher_id in teacher_data.teacher_ids:
        # 检查教师是否存在
        teacher = db.query(User).filter(
            User.id == teacher_id,
            or_(User.role == 'teacher', User.role == 'admin')
        ).first()
        
        if not teacher:
            continue
        
        # 权限检查：学校管理员只能操作本校教师
        if current_admin.role == 'school_admin':
            if teacher.school_id != current_admin.school_id:
                continue
        
        # 检查是否已在班级中
        existing = db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.teacher_id == teacher_id
        ).first()
        
        if existing:
            continue
        
        # 添加到班级
        teacher_rel = PBLClassTeacher(
            class_id=pbl_class.id,
            teacher_id=teacher_id,
            role=teacher_data.role
        )
        db.add(teacher_rel)
        added_count += 1
    
    db.commit()
    
    logger.info(f"添加教师到班级 - 班级UUID: {class_uuid}, 成功: {added_count}")
    
    return success_response(
        data={'added_count': added_count},
        message=f"成功添加 {added_count} 位教师到班级"
    )


@router.delete("/classes/{class_uuid}/teachers/{teacher_id}")
def remove_teacher_from_class(
    class_uuid: str,
    teacher_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """从班级移除教师"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 查找教师记录
    teacher_rel = db.query(PBLClassTeacher).filter(
        PBLClassTeacher.class_id == pbl_class.id,
        PBLClassTeacher.teacher_id == teacher_id
    ).first()
    
    if not teacher_rel:
        return error_response(
            message="教师不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 删除
    db.delete(teacher_rel)
    db.commit()
    
    logger.info(f"从班级移除教师 - 班级UUID: {class_uuid}, 教师ID: {teacher_id}")
    
    return success_response(message="教师已从班级移除")


@router.put("/classes/{class_uuid}/teachers/{teacher_id}/role")
def update_teacher_role(
    class_uuid: str,
    teacher_id: int,
    role_data: TeacherRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新教师角色"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 查找教师记录
    teacher_rel = db.query(PBLClassTeacher).filter(
        PBLClassTeacher.class_id == pbl_class.id,
        PBLClassTeacher.teacher_id == teacher_id
    ).first()
    
    if not teacher_rel:
        return error_response(
            message="教师不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 如果设置为主讲教师，需要取消其他主讲教师
    if role_data.role == 'main':
        db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.role == 'main'
        ).update({'role': 'assistant'})
    
    # 更新角色
    teacher_rel.role = role_data.role
    db.commit()
    
    logger.info(f"更新教师角色 - 班级UUID: {class_uuid}, 教师ID: {teacher_id}, 角色: {role_data.role}")
    
    return success_response(message=f"教师角色已更新为 {role_data.role}")


# ===== 学习进度 =====

@router.get("/classes/{class_uuid}/progress/overview")
def get_class_progress_overview(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级学习进度概览（仅统计数据，不返回详细列表）
    
    轻量级API，用于快速获取班级整体进度统计：
    - 平均完成率
    - 已完成/进行中/未开始人数
    - 平均学习时长
    - 总提交作业数
    
    响应速度：< 100ms
    """
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data={
            'total_students': 0,
            'avg_completion_rate': 0,
            'completed_count': 0,
            'in_progress_count': 0,
            'not_started_count': 0,
            'avg_learning_hours': 0,
            'total_submissions': 0
        })
    
    course = courses[0]
    
    # 获取班级成员数
    total_students = db.query(func.count(PBLClassMember.id)).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).scalar() or 0
    
    if total_students == 0:
        return success_response(data={
            'total_students': 0,
            'avg_completion_rate': 0,
            'completed_count': 0,
            'in_progress_count': 0,
            'not_started_count': 0,
            'avg_learning_hours': 0,
            'total_submissions': 0
        })
    
    # 获取学生ID列表
    student_ids = [row[0] for row in db.query(PBLClassMember.student_id).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()]
    
    # 获取总单元数
    total_units = db.query(func.count(PBLUnit.id)).filter(
        PBLUnit.course_id == course.id
    ).scalar() or 0
    
    if total_units == 0:
        return success_response(data={
            'total_students': total_students,
            'avg_completion_rate': 0,
            'completed_count': 0,
            'in_progress_count': 0,
            'not_started_count': total_students,
            'avg_learning_hours': 0,
            'total_submissions': 0
        })
    
    # 批量统计每个学生的完成单元数
    from sqlalchemy import literal
    
    # 子查询：每个单元的任务数
    unit_task_count = db.query(
        PBLTask.unit_id,
        func.count(PBLTask.id).label('task_count')
    ).filter(
        PBLTask.unit_id.in_(
            db.query(PBLUnit.id).filter(PBLUnit.course_id == course.id)
        )
    ).group_by(PBLTask.unit_id).subquery()
    
    # 子查询：每个学生每个单元的完成任务数
    student_unit_completed = db.query(
        PBLTaskProgress.user_id,
        PBLTask.unit_id,
        func.sum(case((PBLTaskProgress.status == 'completed', 1), else_=0)).label('completed_count')
    ).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).filter(
        PBLTask.unit_id.in_(
            db.query(PBLUnit.id).filter(PBLUnit.course_id == course.id)
        ),
        PBLTaskProgress.user_id.in_(student_ids)
    ).group_by(
        PBLTaskProgress.user_id,
        PBLTask.unit_id
    ).subquery()
    
    # 计算每个学生完成的单元数（完成单元=该单元所有任务都完成）
    student_completed_units = db.query(
        student_unit_completed.c.user_id,
        func.sum(
            case((student_unit_completed.c.completed_count >= unit_task_count.c.task_count, 1), else_=0)
        ).label('completed_units')
    ).outerjoin(
        unit_task_count,
        student_unit_completed.c.unit_id == unit_task_count.c.unit_id
    ).group_by(
        student_unit_completed.c.user_id
    ).all()
    
    # 构建学生完成单元字典
    student_completion_dict = {row.user_id: row.completed_units for row in student_completed_units}
    
    # 统计各状态人数
    completed_count = 0
    in_progress_count = 0
    not_started_count = 0
    total_completion_rate = 0
    
    for student_id in student_ids:
        completed_units = student_completion_dict.get(student_id, 0)
        completion_rate = (completed_units / total_units * 100) if total_units > 0 else 0
        total_completion_rate += completion_rate
        
        if completion_rate == 100:
            completed_count += 1
        elif completion_rate > 0:
            in_progress_count += 1
        else:
            not_started_count += 1
    
    avg_completion_rate = int(total_completion_rate / total_students) if total_students > 0 else 0
    
    # 统计总提交作业数
    total_submissions = db.query(func.count(PBLTaskProgress.id)).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id,
        PBLTaskProgress.user_id.in_(student_ids),
        PBLTaskProgress.submission.isnot(None)
    ).scalar() or 0
    
    avg_learning_hours = int((total_submissions * 2) / total_students) if total_students > 0 else 0
    
    return success_response(data={
        'total_students': total_students,
        'avg_completion_rate': avg_completion_rate,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'not_started_count': not_started_count,
        'avg_learning_hours': avg_learning_hours,
        'total_submissions': total_submissions
    })


@router.get("/classes/{class_uuid}/progress")
def get_class_progress(
    class_uuid: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选: not_started, in_progress, completed"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名或学号）"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级学习进度列表（支持分页和筛选）
    
    优化策略：
    1. 支持分页，避免一次性加载所有数据
    2. 支持按状态筛选和关键词搜索
    3. 使用批量查询优化性能
    4. 只查询当前页需要的学生数据
    
    响应速度：< 500ms（每页20条数据）
    """
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data={
            'items': [],
            'total': 0,
            'page': page,
            'page_size': page_size,
            'total_pages': 0
        })
    
    course = courses[0]
    
    # 构建班级成员查询（支持搜索）
    members_query = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    )
    
    # 添加搜索条件
    if search:
        members_query = members_query.filter(
            or_(
                User.name.like(f'%{search}%'),
                User.real_name.like(f'%{search}%'),
                User.student_number.like(f'%{search}%')
            )
        )
    
    # 获取总数（用于分页）
    total_count = members_query.count()
    
    if total_count == 0:
        return success_response(data={
            'items': [],
            'total': 0,
            'page': page,
            'page_size': page_size,
            'total_pages': 0
        })
    
    # 分页获取成员列表（先不应用分页，因为需要根据状态筛选）
    all_members = members_query.all()
    all_student_ids = [member.student_id for member, _ in all_members]
    
    # === 优化策略：使用批量查询 ===
    
    # 1. 获取课程的总单元数（1次查询）
    total_units = db.query(func.count(PBLUnit.id)).filter(
        PBLUnit.course_id == course.id
    ).scalar() or 0
    
    # 2. 批量获取每个单元的任务ID列表（1次查询）
    unit_tasks = db.query(
        PBLUnit.id.label('unit_id'),
        func.group_concat(PBLTask.id).label('task_ids'),
        func.count(PBLTask.id).label('task_count')
    ).outerjoin(
        PBLTask, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id
    ).group_by(
        PBLUnit.id
    ).all()
    
    # 构建单元->任务映射
    unit_task_map = {}
    for row in unit_tasks:
        task_ids = []
        if row.task_ids:
            task_ids = [int(tid) for tid in row.task_ids.split(',')]
        unit_task_map[row.unit_id] = {
            'task_ids': task_ids,
            'task_count': row.task_count
        }
    
    # 3. 批量获取所有学生的任务完成情况（1次查询）
    task_progress_query = db.query(
        PBLTaskProgress.user_id,
        PBLTask.unit_id,
        func.count(PBLTaskProgress.id).label('total_progress'),
        func.sum(
            case((PBLTaskProgress.status == 'completed', 1), else_=0)
        ).label('completed_count')
    ).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id,
        PBLTaskProgress.user_id.in_(all_student_ids)
    ).group_by(
        PBLTaskProgress.user_id,
        PBLTask.unit_id
    ).all()
    
    # 构建学生单元完成情况字典
    student_unit_progress = {}
    for row in task_progress_query:
        user_id = row.user_id
        unit_id = row.unit_id
        
        if user_id not in student_unit_progress:
            student_unit_progress[user_id] = {}
        
        student_unit_progress[user_id][unit_id] = {
            'completed_count': row.completed_count,
            'total_progress': row.total_progress
        }
    
    # 4. 批量获取提交作业数（1次查询）
    submissions_query = db.query(
        PBLTaskProgress.user_id,
        func.count(PBLTaskProgress.id).label('submissions_count')
    ).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id,
        PBLTaskProgress.user_id.in_(all_student_ids),
        PBLTaskProgress.submission.isnot(None)
    ).group_by(
        PBLTaskProgress.user_id
    ).all()
    
    submissions_dict = {row.user_id: row.submissions_count for row in submissions_query}
    
    # 5. 批量获取最后活跃时间（1次查询）
    last_active_query = db.query(
        PBLTaskProgress.user_id,
        func.max(PBLTaskProgress.updated_at).label('last_active')
    ).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id,
        PBLTaskProgress.user_id.in_(all_student_ids)
    ).group_by(
        PBLTaskProgress.user_id
    ).all()
    
    last_active_dict = {row.user_id: row.last_active for row in last_active_query}

    # === 组装结果数据并应用状态筛选（内存计算） ===
    all_results = []
    for member, user in all_members:
        student_id = member.student_id
        
        # 计算完成的单元数
        completed_units = 0
        student_progress = student_unit_progress.get(student_id, {})
        
        for unit_id, unit_info in unit_task_map.items():
            task_count = unit_info['task_count']
            if task_count == 0:
                continue
            
            # 获取该学生该单元的进度
            unit_progress = student_progress.get(unit_id, {})
            completed_count = unit_progress.get('completed_count', 0)
            
            # 如果该单元的所有任务都完成，则单元完成
            if completed_count >= task_count:
                completed_units += 1
        
        # 计算完成率
        completion_rate = 0
        if total_units > 0:
            completion_rate = int((completed_units / total_units) * 100)
        
        # 计算学习状态
        learning_status = 'not_started'
        if completion_rate == 100:
            learning_status = 'completed'
        elif completion_rate > 0:
            learning_status = 'in_progress'
        
        # 状态筛选
        if status and learning_status != status:
            continue
        
        # 获取提交作业数
        submissions_count = submissions_dict.get(student_id, 0)
        
        # 获取最后活跃时间
        last_active = None
        if student_id in last_active_dict:
            last_active = last_active_dict[student_id].isoformat()
        elif student_id in enrollments_dict:
            last_active = enrollments_dict[student_id].updated_at.isoformat()
        
        # 简化学习时长计算
        learning_hours = submissions_count * 2  # 简单估算：每个作业2小时
        
        all_results.append({
            'student_id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number or '',
            'completion_rate': completion_rate,
            'status': learning_status,
            'completed_units': completed_units,
            'total_units': total_units,
            'learning_hours': learning_hours,
            'submissions_count': submissions_count,
            'last_active': last_active
        })
    
    # 应用分页
    total_filtered = len(all_results)
    total_pages = (total_filtered + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = all_results[start_idx:end_idx]
    
    return success_response(data={
        'items': paginated_results,
        'total': total_filtered,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })


@router.get("/classes/{class_uuid}/students/{student_id}/progress")
def get_student_progress(
    class_uuid: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取单个学生的学习进度详情
    
    按需查询单个学生的详细学习进度，包括：
    - 总体进度统计
    - 每个单元的完成情况
    - 每个任务的完成状态和成绩
    
    响应速度：< 200ms
    """
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 检查学生是否在班级中
    member = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.student_id == student_id,
        PBLClassMember.is_active == 1
    ).first()
    
    if not member:
        return error_response(
            message="学生不在该班级中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取学生信息
    user = db.query(User).filter(User.id == student_id).first()
    
    # 获取班级课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data={
            'student': {
                'id': user.id,
                'name': user.name or user.real_name,
                'student_number': user.student_number
            },
            'overall': {
                'completion_rate': 0,
                'completed_units': 0,
                'total_units': 0,
                'learning_hours': 0,
                'submissions_count': 0
            },
            'units': []
        })
    
    course = courses[0]
    
    # 获取所有单元及其任务
    units_with_tasks = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    total_units = len(units_with_tasks)
    completed_units = 0
    units_detail = []
    
    for unit in units_with_tasks:
        # 获取单元的所有任务
        tasks = db.query(PBLTask).filter(
            PBLTask.unit_id == unit.id
        ).order_by(PBLTask.order).all()
        
        # 获取该学生在这些任务上的进度
        task_ids = [t.id for t in tasks]
        task_progress_list = []
        
        if task_ids:
            progress_records = db.query(PBLTaskProgress).filter(
                PBLTaskProgress.task_id.in_(task_ids),
                PBLTaskProgress.user_id == student_id
            ).all()
            
            progress_dict = {p.task_id: p for p in progress_records}
            
            for task in tasks:
                progress = progress_dict.get(task.id)
                task_progress_list.append({
                    'task_id': task.id,
                    'task_title': task.title,
                    'task_type': task.type,
                    'is_required': task.is_required == 1,
                    'status': progress.status if progress else 'not_started',
                    'score': progress.score if progress else None,
                    'submission_time': progress.updated_at.isoformat() if progress and progress.updated_at else None
                })
        
        # 判断单元是否完成
        completed_tasks = len([tp for tp in task_progress_list if tp['status'] == 'completed'])
        total_tasks = len(tasks)
        unit_completed = completed_tasks == total_tasks and total_tasks > 0
        
        if unit_completed:
            completed_units += 1
        
        units_detail.append({
            'unit_id': unit.id,
            'unit_title': unit.title,
            'unit_description': unit.description,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'completion_rate': int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'is_completed': unit_completed,
            'tasks': task_progress_list
        })
    
    # 统计总体信息
    total_submissions = db.query(func.count(PBLTaskProgress.id)).join(
        PBLTask, PBLTaskProgress.task_id == PBLTask.id
    ).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id,
        PBLTaskProgress.user_id == student_id,
        PBLTaskProgress.submission.isnot(None)
    ).scalar() or 0
    
    completion_rate = int(completed_units / total_units * 100) if total_units > 0 else 0
    learning_hours = total_submissions * 2
    
    return success_response(data={
        'student': {
            'id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number
        },
        'overall': {
            'completion_rate': completion_rate,
            'completed_units': completed_units,
            'total_units': total_units,
            'learning_hours': learning_hours,
            'submissions_count': total_submissions
        },
        'units': units_detail
    })


@router.get("/classes/{class_uuid}/progress/units")
def get_class_progress_by_units(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级的单元列表（极简版，无统计）
    
    性能优化：
    - 只返回单元基本信息，不做任何统计
    - 响应速度：< 50ms
    - 点击单元时再查询该单元详情
    """
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data=[])
    
    course = courses[0]  # 假设一个班级对应一个主课程
    
    # 获取课程的所有单元（只查询基本信息）
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    # 批量获取每个单元的任务数（1次查询）
    unit_task_counts = db.query(
        PBLTask.unit_id,
        func.count(PBLTask.id).label('task_count')
    ).filter(
        PBLTask.unit_id.in_([u.id for u in units])
    ).group_by(
        PBLTask.unit_id
    ).all()
    
    task_count_dict = {row.unit_id: row.task_count for row in unit_task_counts}
    
    # 构建单元列表（无统计）
    unit_list = []
    for unit in units:
        unit_list.append({
            'id': unit.id,
            'uuid': unit.uuid,
            'title': unit.title,
            'description': unit.description,
            'order': unit.order,
            'task_count': task_count_dict.get(unit.id, 0)
        })
    
    return success_response(data=unit_list)


@router.get("/classes/{class_uuid}/progress/units/{unit_id}")
def get_unit_progress_detail(
    class_uuid: str,
    unit_id: int,
    search: Optional[str] = Query(None, description="搜索关键词（姓名或学号）"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取指定单元的学生学习进度详情（极简优化版）
    
    优化策略：
    1. 批量查询所有学生的任务进度，避免N+1查询
    2. 一次性返回所有学生数据（单元维度，数据量可控）
    3. 支持搜索学生
    
    响应速度：< 300ms
    """
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取单元信息
    unit = db.query(PBLUnit).filter(PBLUnit.id == unit_id).first()
    if not unit:
        return error_response(
            message="单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取单元的所有任务
    tasks = db.query(PBLTask).filter(
        PBLTask.unit_id == unit.id
    ).order_by(PBLTask.order).all()
    
    task_ids = [t.id for t in tasks]
    
    # 构建任务信息
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'uuid': task.uuid,
            'title': task.title,
            'type': task.type,
            'order': task.order,
            'is_required': task.is_required == 1
        })
    
    # 查询班级成员（支持搜索）
    members_query = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    )
    
    # 添加搜索条件
    if search:
        members_query = members_query.filter(
            or_(
                User.name.like(f'%{search}%'),
                User.real_name.like(f'%{search}%'),
                User.student_number.like(f'%{search}%')
            )
        )
    
    # 获取所有成员
    members = members_query.all()
    
    if not members:
        return success_response(data={
            'unit': {
                'id': unit.id,
                'uuid': unit.uuid,
                'title': unit.title,
                'description': unit.description,
                'order': unit.order
            },
            'tasks': task_list,
            'students': []
        })
    
    student_ids = [member.student_id for member, _ in members]
    
    # 批量获取所有学生的任务进度（1次查询）
    if task_ids and student_ids:
        progress_records = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.task_id.in_(task_ids),
            PBLTaskProgress.user_id.in_(student_ids)
        ).all()
        
        # 构建进度字典：{user_id: {task_id: progress}}
        progress_dict = {}
        for p in progress_records:
            if p.user_id not in progress_dict:
                progress_dict[p.user_id] = {}
            progress_dict[p.user_id][p.task_id] = p
    else:
        progress_dict = {}
    
    # 构建学生进度信息
    student_progress = []
    for member, user in members:
        task_progress_list = []
        completed_count = 0
        total_score = 0
        score_count = 0
        
        student_progress_data = progress_dict.get(member.student_id, {})
        
        for task in tasks:
            progress = student_progress_data.get(task.id)
            
            if progress:
                # 只要提交了就算完成（submission不为None）
                is_completed = progress.submission is not None
                if is_completed:
                    completed_count += 1
                
                if progress.score is not None:
                    total_score += progress.score
                    score_count += 1
                
                task_progress_list.append({
                    'task_id': task.id,
                    'task_title': task.title,
                    'status': progress.status,
                    'score': progress.score,
                    'submission_time': progress.updated_at.isoformat() if progress.updated_at else None,
                    'is_completed': is_completed
                })
            else:
                task_progress_list.append({
                    'task_id': task.id,
                    'task_title': task.title,
                    'status': 'not_started',
                    'score': None,
                    'submission_time': None,
                    'is_completed': False
                })
        
        # 计算平均分
        avg_score = round(total_score / score_count, 1) if score_count > 0 else None
        
        # 计算完成率
        completion_rate = int((completed_count / len(tasks)) * 100) if len(tasks) > 0 else 0
        
        student_progress.append({
            'student_id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number or '',
            'completion_rate': completion_rate,
            'completed_tasks': completed_count,
            'total_tasks': len(tasks),
            'avg_score': avg_score,
            'task_progress': task_progress_list
        })
    
    return success_response(data={
        'unit': {
            'id': unit.id,
            'uuid': unit.uuid,
            'title': unit.title,
            'description': unit.description,
            'order': unit.order
        },
        'tasks': task_list,
        'students': student_progress
    })


@router.get("/classes/{class_uuid}/progress/export")
def export_class_progress(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """导出班级学习进度报表"""
    from fastapi.responses import Response
    from ...utils.export import export_progress_to_csv, generate_export_filename
    
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取进度数据（内部调用）
    progress_data = _get_class_progress_data(class_uuid, db)
    
    # 导出为 CSV
    csv_content = export_progress_to_csv(progress_data)
    
    # 生成文件名
    filename = generate_export_filename(f'{pbl_class.name}_progress')
    
    # 返回 CSV 文件
    return Response(
        content=csv_content.encode('utf-8-sig'),  # 使用 BOM 以支持 Excel 正确显示中文
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


def _get_class_progress_data(class_uuid: str, db: Session) -> List[Dict]:
    """内部方法：获取班级进度数据（用于导出）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return []
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return []
    
    # 获取班级成员
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    result = []
    course = courses[0]  # 假设一个班级对应一个主课程
    
    # 统计单元数量
    total_units = db.query(func.count(PBLUnit.id)).filter(
        PBLUnit.course_id == course.id
    ).scalar() or 0
    
    for member, user in members:
        # 统计已完成单元
        completed_units = 0
        if total_units > 0:
            units = db.query(PBLUnit).filter(PBLUnit.course_id == course.id).all()
            for unit in units:
                tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
                if not tasks:
                    continue
                
                all_completed = True
                for task in tasks:
                    task_progress = db.query(PBLTaskProgress).filter(
                        PBLTaskProgress.task_id == task.id,
                        PBLTaskProgress.user_id == member.student_id
                    ).first()
                    if not task_progress or task_progress.status != 'completed':
                        all_completed = False
                        break
                
                if all_completed:
                    completed_units += 1
        
        # 计算完成率
        completion_rate = 0
        if total_units > 0:
            completion_rate = int((completed_units / total_units) * 100)
        
        # 计算学习状态
        learning_status = 'not_started'
        if completion_rate == 100:
            learning_status = 'completed'
        elif completion_rate > 0:
            learning_status = 'in_progress'
        
        # 统计提交作业数
        submissions_count = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.user_id == member.student_id,
            PBLTaskProgress.submission.isnot(None)
        ).join(
            PBLTask, PBLTaskProgress.task_id == PBLTask.id
        ).join(
            PBLUnit, PBLTask.unit_id == PBLUnit.id
        ).filter(
            PBLUnit.course_id == course.id
        ).scalar() or 0
        
        # 获取最后活跃时间
        last_progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == member.student_id
        ).join(
            PBLTask, PBLTaskProgress.task_id == PBLTask.id
        ).join(
            PBLUnit, PBLTask.unit_id == PBLUnit.id
        ).filter(
            PBLUnit.course_id == course.id
        ).order_by(PBLTaskProgress.updated_at.desc()).first()
        
        last_active = None
        if last_progress:
            last_active = last_progress.updated_at.isoformat()
        elif enrollment:
            last_active = enrollment.updated_at.isoformat()
        
        learning_hours = submissions_count * 2  # 简单估算
        
        result.append({
            'student_id': user.id,
            'name': user.name or user.real_name,
            'student_number': user.student_number or '',
            'completion_rate': completion_rate,
            'status': learning_status,
            'completed_units': completed_units,
            'total_units': total_units,
            'learning_hours': learning_hours,
            'submissions_count': submissions_count,
            'last_active': last_active
        })
    
    return result


# ===== 作业管理 =====

@router.get("/classes/{class_uuid}/homework")
def get_class_homework(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级作业列表（学生提交情况）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data=[])
    
    # 获取班级成员数量
    total_students = db.query(func.count(PBLClassMember.id)).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).scalar() or 0
    
    result = []
    for course in courses:
        # 获取课程的所有任务
        tasks = db.query(PBLTask, PBLUnit).join(
            PBLUnit, PBLTask.unit_id == PBLUnit.id
        ).filter(
            PBLUnit.course_id == course.id
        ).order_by(PBLUnit.order, PBLTask.order).all()
        
        for task, unit in tasks:
            # 统计提交情况
            submitted_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id == task.id,
                PBLTaskProgress.submission.isnot(None)
            ).scalar() or 0
            
            # 统计待批改数量
            to_review_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id == task.id,
                PBLTaskProgress.status == 'review',
                PBLTaskProgress.graded_at.is_(None)
            ).scalar() or 0
            
            # 判断作业状态
            homework_status = 'ongoing'
            if hasattr(task, 'deadline') and task.deadline:
                from datetime import datetime
                if task.deadline < get_beijing_time_naive():
                    homework_status = 'ended'
            
            # 判断是否为必做
            is_required = task.type == 'required' if hasattr(task, 'type') else True
            
            result.append({
                'id': task.id,
                'uuid': task.uuid,
                'title': task.title,
                'description': task.description,
                'unit_name': unit.title,
                'unit_id': unit.id,
                'status': homework_status,
                'is_required': is_required,
                'submitted_count': submitted_count,
                'total_count': total_students,
                'to_review_count': to_review_count,
                'start_time': task.start_time.isoformat() if hasattr(task, 'start_time') and task.start_time else None,
                'deadline': task.deadline.isoformat() if hasattr(task, 'deadline') and task.deadline else None,
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
    
    return success_response(data=result)


@router.get("/classes/{class_uuid}/homework/export")
def export_class_homework(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """导出班级作业列表"""
    from fastapi.responses import Response
    from ...utils.export import export_homework_to_csv, generate_export_filename
    
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取作业数据（内部调用）
    homework_data = _get_class_homework_data(class_uuid, db)
    
    # 导出为 CSV
    csv_content = export_homework_to_csv(homework_data)
    
    # 生成文件名
    filename = generate_export_filename(f'{pbl_class.name}_homework')
    
    # 返回 CSV 文件
    return Response(
        content=csv_content.encode('utf-8-sig'),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


def _get_class_homework_data(class_uuid: str, db: Session) -> List[Dict]:
    """内部方法：获取班级作业数据（用于导出）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return []
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return []
    
    # 获取班级成员数量
    total_students = db.query(func.count(PBLClassMember.id)).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).scalar() or 0
    
    result = []
    for course in courses:
        # 获取课程的所有任务
        tasks = db.query(PBLTask, PBLUnit).join(
            PBLUnit, PBLTask.unit_id == PBLUnit.id
        ).filter(
            PBLUnit.course_id == course.id
        ).order_by(PBLUnit.order, PBLTask.order).all()
        
        for task, unit in tasks:
            # 统计提交情况
            submitted_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id == task.id,
                PBLTaskProgress.submission.isnot(None)
            ).scalar() or 0
            
            # 统计待批改数量
            to_review_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id == task.id,
                PBLTaskProgress.status == 'review',
                PBLTaskProgress.graded_at.is_(None)
            ).scalar() or 0
            
            # 判断作业状态
            homework_status = 'ongoing'
            if hasattr(task, 'deadline') and task.deadline:
                if task.deadline < get_beijing_time_naive():
                    homework_status = 'ended'
            
            # 判断是否为必做
            is_required = task.type == 'required' if hasattr(task, 'type') else True
            
            result.append({
                'id': task.id,
                'uuid': task.uuid,
                'title': task.title,
                'description': task.description,
                'unit_name': unit.title,
                'unit_id': unit.id,
                'status': homework_status,
                'is_required': is_required,
                'submitted_count': submitted_count,
                'total_count': total_students,
                'to_review_count': to_review_count,
                'start_time': task.start_time.isoformat() if hasattr(task, 'start_time') and task.start_time else None,
                'deadline': task.deadline.isoformat() if hasattr(task, 'deadline') and task.deadline else None,
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
    
    return result


@router.get("/classes/{class_uuid}/homework/{task_id}/submissions")
def get_homework_submissions(
    class_uuid: str,
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取作业提交详情"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取任务
    task = db.query(PBLTask).filter(PBLTask.id == task_id).first()
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级成员
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    result = []
    for member, user in members:
        # 获取提交记录
        progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.task_id == task_id,
            PBLTaskProgress.user_id == member.student_id
        ).first()
        
        if progress:
            # 获取评分人信息
            grader_name = None
            if progress.graded_by:
                grader = db.query(User).filter(User.id == progress.graded_by).first()
                if grader:
                    grader_name = grader.name or grader.real_name
            
            result.append({
                'submission_id': progress.id,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': progress.status,
                'submission': progress.submission,
                'score': progress.score,
                'feedback': progress.feedback,
                'graded_by': progress.graded_by,
                'grader_name': grader_name,
                'graded_at': progress.graded_at.isoformat() if progress.graded_at else None,
                'submitted_at': progress.updated_at.isoformat() if progress.updated_at else None
            })
        else:
            # 未提交
            result.append({
                'submission_id': None,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': 'pending',
                'submission': None,
                'score': None,
                'feedback': None,
                'graded_by': None,
                'grader_name': None,
                'graded_at': None,
                'submitted_at': None
            })
    
    return success_response(data=result)


@router.get("/classes/{class_uuid}/homework/{task_id}/submissions/export")
def export_homework_submissions(
    class_uuid: str,
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """导出作业提交详情"""
    from fastapi.responses import Response
    from ...utils.export import export_submissions_to_csv, generate_export_filename
    
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取任务
    task = db.query(PBLTask).filter(PBLTask.id == task_id).first()
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取提交数据
    submissions_data = _get_homework_submissions_data(class_uuid, task_id, db)
    
    # 导出为 CSV
    csv_content = export_submissions_to_csv(submissions_data)
    
    # 生成文件名
    filename = generate_export_filename(f'{task.title}_submissions')
    
    # 返回 CSV 文件
    return Response(
        content=csv_content.encode('utf-8-sig'),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


def _get_homework_submissions_data(class_uuid: str, task_id: int, db: Session) -> List[Dict]:
    """内部方法：获取作业提交数据（用于导出）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return []
    
    # 获取班级成员
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    result = []
    for member, user in members:
        # 获取提交记录
        progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.task_id == task_id,
            PBLTaskProgress.user_id == member.student_id
        ).first()
        
        if progress:
            # 获取评分人信息
            grader_name = None
            if progress.graded_by:
                grader = db.query(User).filter(User.id == progress.graded_by).first()
                if grader:
                    grader_name = grader.name or grader.real_name
            
            result.append({
                'submission_id': progress.id,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': progress.status,
                'submission': progress.submission,
                'score': progress.score,
                'feedback': progress.feedback,
                'graded_by': progress.graded_by,
                'grader_name': grader_name,
                'graded_at': progress.graded_at.isoformat() if progress.graded_at else None,
                'submitted_at': progress.updated_at.isoformat() if progress.updated_at else None
            })
        else:
            # 未提交
            result.append({
                'submission_id': None,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': 'pending',
                'submission': None,
                'score': None,
                'feedback': None,
                'graded_by': None,
                'grader_name': None,
                'graded_at': None,
                'submitted_at': None
            })
    
    return result


@router.put("/classes/{class_uuid}/homework/submissions/{submission_id}/review")
def review_homework_submission(
    class_uuid: str,
    submission_id: int,
    review_data: TaskReview,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """批阅作业"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取提交记录
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.id == submission_id
    ).first()
    
    if not progress:
        return error_response(
            message="提交记录不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 更新评分和反馈
    if review_data.score is not None:
        progress.score = review_data.score
    if review_data.grade is not None:
        # 更新 grade 字段（需要确保数据库字段存在）
        setattr(progress, 'grade', review_data.grade)
    if review_data.feedback is not None:
        progress.feedback = review_data.feedback
    
    progress.status = review_data.status
    progress.graded_by = current_admin.id
    progress.graded_at = get_beijing_time_naive()
    
    db.commit()
    db.refresh(progress)
    
    logger.info(f"批阅作业 - 提交ID: {submission_id}, 评分: {review_data.score}, 评阅人: {current_admin.username}")
    
    return success_response(
        data={
            'submission_id': progress.id,
            'score': progress.score,
            'grade': getattr(progress, 'grade', None),
            'feedback': progress.feedback,
            'status': progress.status
        },
        message="作业批阅成功"
    )


# ===== 作业管理（优化版 - 按单元展示） =====

@router.get("/classes/{class_uuid}/homework/units")
def get_homework_units(
    class_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级作业单元列表（极速加载）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id == pbl_class.id,
        PBLCourse.status == 'published'
    ).all()
    
    if not courses:
        return success_response(data=[])
    
    course_ids = [course.id for course in courses]
    
    # 获取所有单元及其作业数量
    units_data = db.query(
        PBLUnit.id,
        PBLUnit.title,
        PBLUnit.description,
        PBLUnit.order,
        func.count(PBLTask.id).label('task_count')
    ).outerjoin(
        PBLTask, PBLUnit.id == PBLTask.unit_id
    ).filter(
        PBLUnit.course_id.in_(course_ids)
    ).group_by(
        PBLUnit.id
    ).order_by(
        PBLUnit.order
    ).all()
    
    result = []
    for unit in units_data:
        result.append({
            'id': unit.id,
            'title': unit.title,
            'description': unit.description,
            'order': unit.order,
            'task_count': unit.task_count or 0
        })
    
    return success_response(data=result)


@router.get("/classes/{class_uuid}/homework/units/{unit_id}")
def get_homework_unit_detail(
    class_uuid: str,
    unit_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取单元作业详情（按需加载）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取单元信息
    unit = db.query(PBLUnit).filter(PBLUnit.id == unit_id).first()
    if not unit:
        return error_response(
            message="单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级成员数量
    total_students = db.query(func.count(PBLClassMember.id)).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).scalar() or 0
    
    # 获取单元下的所有作业
    tasks = db.query(PBLTask).filter(
        PBLTask.unit_id == unit_id
    ).order_by(PBLTask.order).all()
    
    task_list = []
    for task in tasks:
        # 统计提交情况
        submitted_count = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.submission.isnot(None)
        ).scalar() or 0
        
        # 统计待批改数量
        to_review_count = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.status == 'review',
            PBLTaskProgress.graded_at.is_(None)
        ).scalar() or 0
        
        # 判断作业状态
        homework_status = 'draft'
        if hasattr(task, 'publish_status'):
            if task.publish_status == 'published':
                homework_status = 'ongoing'
                if hasattr(task, 'deadline') and task.deadline:
                    from datetime import datetime
                    if task.deadline < get_beijing_time_naive():
                        homework_status = 'ended'
        
        task_list.append({
            'id': task.id,
            'uuid': task.uuid,
            'title': task.title,
            'description': task.description,
            'type': task.type,
            'difficulty': task.difficulty,
            'status': homework_status,
            'submitted_count': submitted_count,
            'total_count': total_students,
            'to_review_count': to_review_count,
            'start_time': task.start_time.isoformat() if hasattr(task, 'start_time') and task.start_time else None,
            'deadline': task.deadline.isoformat() if hasattr(task, 'deadline') and task.deadline else None,
            'created_at': task.created_at.isoformat() if task.created_at else None
        })
    
    return success_response(data={
        'unit': {
            'id': unit.id,
            'title': unit.title,
            'description': unit.description,
            'order': unit.order
        },
        'tasks': task_list,
        'total_students': total_students
    })


@router.get("/classes/{class_uuid}/homework/tasks/{task_id}/submissions")
def get_task_submissions_for_grading(
    class_uuid: str,
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取作业提交列表（用于批改）"""
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_uuid).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取任务信息
    task = db.query(PBLTask).filter(PBLTask.id == task_id).first()
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级成员及其提交情况
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).order_by(User.student_number).all()
    
    result = []
    for member, user in members:
        # 获取提交记录
        progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.task_id == task_id,
            PBLTaskProgress.user_id == member.student_id
        ).first()
        
        if progress:
            # 获取评分人信息
            grader_name = None
            if progress.graded_by:
                grader = db.query(User).filter(User.id == progress.graded_by).first()
                if grader:
                    grader_name = grader.name or grader.real_name
            
            result.append({
                'submission_id': progress.id,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': progress.status,
                'submission': progress.submission,
                'score': progress.score,
                'grade': getattr(progress, 'grade', None),
                'feedback': progress.feedback,
                'graded_by': progress.graded_by,
                'grader_name': grader_name,
                'graded_at': progress.graded_at.isoformat() if progress.graded_at else None,
                'submitted_at': progress.submitted_at.isoformat() if progress.submitted_at else (progress.updated_at.isoformat() if progress.updated_at else None)
            })
        else:
            # 未提交
            result.append({
                'submission_id': None,
                'student_id': user.id,
                'student_name': user.name or user.real_name,
                'student_number': user.student_number or '',
                'status': 'pending',
                'submission': None,
                'score': None,
                'grade': None,
                'feedback': None,
                'graded_by': None,
                'grader_name': None,
                'graded_at': None,
                'submitted_at': None
            })
    
    return success_response(data={
        'task': {
            'id': task.id,
            'uuid': task.uuid,
            'title': task.title,
            'description': task.description
        },
        'submissions': result
    })


@router.get("/feedback-templates")
def get_feedback_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取评语模板列表"""
    from sqlalchemy import Table, MetaData, Column, BigInteger, String, Text, Integer, TIMESTAMP
    from sqlalchemy.sql import select
    
    # 动态访问评语模板表
    metadata = MetaData()
    feedback_templates = Table(
        'pbl_feedback_templates',
        metadata,
        Column('id', BigInteger, primary_key=True),
        Column('uuid', String(36)),
        Column('school_id', Integer),
        Column('category', String(50)),
        Column('title', String(100)),
        Column('content', Text),
        Column('is_active', Integer),
        Column('created_by', Integer),
        Column('created_at', TIMESTAMP),
        Column('updated_at', TIMESTAMP),
        autoload_with=db.get_bind()
    )
    
    # 构建查询
    query = select(feedback_templates).where(
        feedback_templates.c.school_id == current_admin.school_id,
        feedback_templates.c.is_active == 1
    )
    
    if category:
        query = query.where(feedback_templates.c.category == category)
    
    query = query.order_by(feedback_templates.c.category, feedback_templates.c.id)
    
    # 执行查询
    result = db.execute(query).fetchall()
    
    templates = []
    for row in result:
        templates.append({
            'id': row.id,
            'uuid': row.uuid,
            'category': row.category,
            'title': row.title,
            'content': row.content
        })
    
    return success_response(data=templates)
