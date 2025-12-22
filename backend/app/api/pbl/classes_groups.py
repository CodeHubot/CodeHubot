from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.utils.timezone import get_beijing_time_naive

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...models.admin import Admin, User
from ...models.pbl import (
    PBLClass, PBLGroup, PBLGroupMember, PBLClassMember,
    PBLClassTeacher, PBLClassCourse, PBLCourse,
    PBLLearningProgress,
    PBLTaskProgress, PBLTask, PBLUnit
)
from ...core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

# ===== 请求模型 =====

class CreateClassRequest(BaseModel):
    """创建班级请求模型"""
    name: str
    class_type: str = 'regular'
    grade: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[int] = None

class GroupMemberAddRequest(BaseModel):
    """添加小组成员请求模型"""
    student_ids: List[int]

class CreateGroupRequest(BaseModel):
    """创建小组请求模型"""
    name: str
    class_id: Optional[int] = None
    course_id: Optional[int] = None
    max_members: int = 6

class AddStudentsRequest(BaseModel):
    """添加学生到班级请求模型"""
    student_ids: List[int]

class AssignTeacherRequest(BaseModel):
    """分配教师到班级请求模型"""
    teacher_id: int
    subject: Optional[str] = None
    is_primary: bool = False

class AssignCourseRequest(BaseModel):
    """分配课程到班级请求模型"""
    course_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    remarks: Optional[str] = None

# ===== 班级管理 =====

@router.get("/classes")
def get_classes(
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级列表"""
    # 权限控制
    if current_admin.role != 'platform_admin':
        school_id = current_admin.school_id
    
    # 查询班级
    query = db.query(PBLClass).filter(PBLClass.is_active == True)
    if school_id:
        query = query.filter(PBLClass.school_id == school_id)
    
    classes = query.all()
    
    result = []
    for cls in classes:
        # 统计班级学生数（通过班级成员表）
        student_count = db.query(PBLClassMember).filter(
            PBLClassMember.class_id == cls.id,
            PBLClassMember.is_active == 1
        ).count()
        
        result.append({
            'id': cls.id,
            'uuid': cls.uuid,
            'name': cls.name,
            'grade': cls.grade,
            'school_id': cls.school_id,
            'academic_year': cls.academic_year,
            'class_teacher_id': cls.class_teacher_id,
            'max_students': cls.max_students,
            'student_count': student_count,
            'created_at': cls.created_at.isoformat() if cls.created_at else None
        })
    
    return success_response(data=result)

@router.post("/classes")
def create_class(
    request: CreateClassRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建班级
    
    学校ID自动从当前登录管理员中获取，无需前端传递
    如果提供template_id，将从模板创建课程并关联到班级
    """
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 从当前管理员获取学校ID
    school_id = current_admin.school_id
    if not school_id:
        return error_response(
            message="当前管理员未关联学校，无法创建班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 解构请求参数
    name = request.name
    class_type = request.class_type
    grade = request.grade
    description = request.description
    template_id = request.template_id
    
    # 如果提供了template_id，从模板创建完整的课程
    course_id = None
    course_title = None
    new_course = None
    if template_id:
        from ...services.template_service import copy_course_from_template, validate_template_permission
        
        try:
            # 验证模板权限
            template, permission = validate_template_permission(db, template_id, school_id)
            
            # 先创建班级（因为课程需要关联班级）
            temp_class = PBLClass(
                school_id=school_id,
                name=name,
                class_type=class_type,
                grade=grade,
                description=description,
                is_active=True
            )
            db.add(temp_class)
            db.flush()
            
            # 从模板复制完整的课程（包括单元、资源、任务）
            new_course = copy_course_from_template(
                db=db,
                template_id=template_id,
                school_id=school_id,
                creator_id=current_admin.id,
                class_id=temp_class.id,
                class_name=name,
                permission_id=permission.id
            )
            
            course_id = new_course.id
            course_title = new_course.title
            
            # 更新权限的实例计数
            instance_count = db.query(PBLCourse).filter(
                PBLCourse.template_id == template_id,
                PBLCourse.school_id == school_id
            ).count()
            permission.current_instances = instance_count
            
            logger.info(f"从模板创建完整课程 - 模板ID: {template_id}, 课程ID: {course_id}, 学校ID: {school_id}")
            
            # 将temp_class赋值给new_class，后续不需要再创建
            new_class = temp_class
            
        except ValueError as e:
            return error_response(
                message=str(e),
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"从模板创建课程失败: {str(e)}", exc_info=True)
            return error_response(
                message=f"从模板创建课程失败: {str(e)}",
                code=500,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # 没有提供template_id，正常创建班级
        new_class = None
    
    # 如果没有提供template_id，创建班级记录
    if new_class is None:
        new_class = PBLClass(
            school_id=school_id,
            name=name,
            class_type=class_type,
            grade=grade,
            description=description,
            is_active=True
        )
        db.add(new_class)
        db.flush()
    
    # 如果创建了课程，创建班级课程关联记录
    if course_id:
        class_course = PBLClassCourse(
            class_id=new_class.id,
            course_id=course_id,
            assigned_by=current_admin.id,
            status='active'
        )
        db.add(class_course)
    
    db.commit()
    db.refresh(new_class)
    
    logger.info(f"创建班级 - 名称: {name}, 学校ID: {school_id}, 关联课程: {course_title or '无'}, 操作者: {current_admin.username}")
    
    result_data = {
        'id': new_class.id,
        'uuid': new_class.uuid,
        'name': new_class.name,
        'grade': new_class.grade,
        'school_id': new_class.school_id,
        'created_at': new_class.created_at.isoformat() if new_class.created_at else None
    }
    
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

@router.get("/classes/{class_id}/students")
def get_class_students(
    class_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级学生列表"""
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（学校管理员只能查看本校班级）
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 查询班级中的学生（通过班级成员表）
    students = db.query(User).join(
        PBLClassMember,
        User.id == PBLClassMember.student_id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1,
        User.deleted_at == None
    ).all()
    
    result = []
    for student in students:
        # 性别转换
        gender_display = ''
        if student.gender == 'male':
            gender_display = '男'
        elif student.gender == 'female':
            gender_display = '女'
        else:
            gender_display = student.gender or ''
        
        result.append({
            'id': student.id,
            'username': student.username,
            'name': student.name or student.real_name,
            'student_number': student.student_number,
            'gender': gender_display
        })
    
    return success_response(data=result)

@router.post("/classes/{class_id}/add-students")
def add_students_to_class(
    class_id: str,
    request: AddStudentsRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """批量添加学生到班级"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（学校管理员只能操作本校班级）
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    success_count = 0
    for student_id in request.student_ids:
        student = db.query(User).filter(
            User.id == student_id,
            User.role == 'student'
        ).first()
        
        if student:
            # 权限检查：学校管理员只能操作本校学生
            if current_admin.role == 'school_admin':
                if student.school_id != current_admin.school_id:
                    continue
            
            # 检查是否已经在班级中
            existing = db.query(PBLClassMember).filter(
                PBLClassMember.class_id == pbl_class.id,
                PBLClassMember.student_id == student_id
            ).first()
            
            if existing:
                # 如果已存在但不活跃，则激活
                if existing.is_active == 0:
                    existing.is_active = 1
                    success_count += 1
            else:
                # 创建新的班级成员记录
                member = PBLClassMember(
                    class_id=pbl_class.id,
                    student_id=student_id,
                    is_active=1
                )
                db.add(member)
                success_count += 1
    
    db.commit()
    
    logger.info(f"添加学生到班级 - 班级UUID: {class_id}, 成功: {success_count}, 操作者: {current_admin.username}")
    
    return success_response(
        data={'added_count': success_count},
        message=f"成功添加 {success_count} 名学生到班级"
    )

# ===== 小组管理 =====

@router.get("/groups")
def get_groups(
    class_id: Optional[int] = None,
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取小组列表"""
    # 查询小组
    query = db.query(PBLGroup).filter(PBLGroup.is_active == True)
    
    if class_id:
        query = query.filter(PBLGroup.class_id == class_id)
    if course_id:
        query = query.filter(PBLGroup.course_id == course_id)
    
    groups = query.all()
    
    result = []
    for group in groups:
        # 统计小组成员数
        member_count = db.query(PBLGroupMember).filter(
            PBLGroupMember.group_id == group.id,
            PBLGroupMember.is_active == True
        ).count()
        
        # 获取组长信息
        leader = None
        if group.leader_id:
            leader_user = db.query(User).filter(User.id == group.leader_id).first()
            if leader_user:
                leader = {
                    'id': leader_user.id,
                    'name': leader_user.name or leader_user.real_name
                }
        
        result.append({
            'id': group.id,
            'uuid': group.uuid,
            'name': group.name,
            'description': group.description,
            'class_id': group.class_id,
            'course_id': group.course_id,
            'leader': leader,
            'max_members': group.max_members,
            'member_count': member_count,
            'created_at': group.created_at.isoformat() if group.created_at else None
        })
    
    return success_response(data=result)

@router.post("/groups")
def create_group(
    request: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建小组"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 创建小组记录
    new_group = PBLGroup(
        name=request.name,
        class_id=request.class_id,
        course_id=request.course_id,
        max_members=request.max_members,
        is_active=True
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    logger.info(f"创建小组 - 名称: {request.name}, 班级ID: {request.class_id}, 操作者: {current_admin.username}")
    
    return success_response(
        data={
            'id': new_group.id,
            'uuid': new_group.uuid,
            'name': new_group.name,
            'class_id': new_group.class_id,
            'course_id': new_group.course_id,
            'max_members': new_group.max_members,
            'created_at': new_group.created_at.isoformat() if new_group.created_at else None
        },
        message="小组创建成功"
    )

@router.get("/groups/{group_id}/members")
def get_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取小组成员列表"""
    # 查询小组
    group = db.query(PBLGroup).filter(PBLGroup.uuid == group_id).first()
    if not group:
        return error_response(
            message="小组不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查询小组成员
    group_members = db.query(PBLGroupMember).filter(
        PBLGroupMember.group_id == group.id,
        PBLGroupMember.is_active == True
    ).all()
    
    result = []
    for gm in group_members:
        member = db.query(User).filter(
            User.id == gm.user_id,
            User.deleted_at == None
        ).first()
        
        if member:
            result.append({
                'id': member.id,
                'username': member.username,
                'name': member.name or member.real_name,
                'student_number': member.student_number,
                'gender': member.gender,
                'role': gm.role,
                'joined_at': gm.joined_at.isoformat() if gm.joined_at else None
            })
    
    return success_response(data=result)

@router.get("/groups/{group_id}/available-students")
def get_available_students_for_group(
    group_id: str,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取小组可添加的学生列表（班级中未分组的学生）"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查小组是否存在
    group = db.query(PBLGroup).filter(PBLGroup.uuid == group_id).first()
    if not group:
        return error_response(
            message="小组不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 必须有班级ID
    if not group.class_id:
        return success_response(data=[])
    
    # 查询该班级的所有学生（通过班级成员表）
    query = db.query(User).join(
        PBLClassMember,
        User.id == PBLClassMember.student_id
    ).filter(
        PBLClassMember.class_id == group.class_id,
        PBLClassMember.is_active == 1,
        User.deleted_at == None
    )
    
    # 权限检查：学校管理员只能看本校学生
    if current_admin.role == 'school_admin':
        query = query.filter(User.school_id == current_admin.school_id)
    
    # 关键词搜索
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                User.name.like(keyword_pattern),
                User.real_name.like(keyword_pattern),
                User.student_number.like(keyword_pattern)
            )
        )
    
    class_students = query.all()
    
    # 获取已经在小组中的学生ID列表
    grouped_student_ids = db.query(PBLGroupMember.user_id).filter(
        PBLGroupMember.group_id == group.id,
        PBLGroupMember.is_active == True
    ).all()
    grouped_student_ids = [sid[0] for sid in grouped_student_ids]
    
    # 过滤出未分组的学生
    result = []
    for student in class_students:
        if student.id not in grouped_student_ids:
            result.append({
                'id': student.id,
                'username': student.username,
                'name': student.name or student.real_name,
                'student_number': student.student_number,
                'gender': student.gender
            })
    
    return success_response(data=result)

@router.post("/groups/{group_id}/add-members")
def add_members_to_group(
    group_id: str,
    request_data: GroupMemberAddRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """批量添加成员到小组"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 检查小组是否存在
    group = db.query(PBLGroup).filter(PBLGroup.uuid == group_id).first()
    if not group:
        return error_response(
            message="小组不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    success_count = 0
    for student_id in request_data.student_ids:
        student = db.query(User).filter(
            User.id == student_id,
            User.role == 'student'
        ).first()
        
        if not student:
            continue
        
        # 权限检查
        if current_admin.role == 'school_admin':
            if student.school_id != current_admin.school_id:
                continue
        
        # 检查是否已经在小组中
        existing_member = db.query(PBLGroupMember).filter(
            PBLGroupMember.group_id == group.id,
            PBLGroupMember.user_id == student_id,
            PBLGroupMember.is_active == True
        ).first()
        
        if existing_member:
            continue
        
        # 添加成员
        member = PBLGroupMember(
            group_id=group.id,
            user_id=student_id,
            role='member',
            is_active=True
        )
        db.add(member)
        success_count += 1
    
    db.commit()
    
    logger.info(f"添加成员到小组 - 小组UUID: {group_id}, 成功: {success_count}, 操作者: {current_admin.username}")
    
    return success_response(
        data={'added_count': success_count},
        message=f"成功添加 {success_count} 名成员到小组"
    )

@router.delete("/groups/{group_id}/members/{student_id}")
def remove_member_from_group(
    group_id: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """从小组移除成员"""
    # 查询小组
    group = db.query(PBLGroup).filter(PBLGroup.uuid == group_id).first()
    if not group:
        return error_response(
            message="小组不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查找小组成员记录
    member = db.query(PBLGroupMember).filter(
        PBLGroupMember.group_id == group.id,
        PBLGroupMember.user_id == student_id,
        PBLGroupMember.is_active == True
    ).first()
    
    if not member:
        return error_response(
            message="学生不在该小组中",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 将成员标记为非激活状态（软删除）
    member.is_active = False
    db.commit()
    
    logger.info(f"从小组移除成员 - 小组UUID: {group_id}, 学生ID: {student_id}, 操作者: {current_admin.username}")
    
    return success_response(message="成员已从小组移除")

@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除小组"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin', 'teacher']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 查询小组
    group = db.query(PBLGroup).filter(PBLGroup.uuid == group_id).first()
    if not group:
        return error_response(
            message="小组不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 软删除小组（标记为非激活状态）
    group.is_active = False
    
    # 同时软删除所有小组成员
    db.query(PBLGroupMember).filter(
        PBLGroupMember.group_id == group.id
    ).update({'is_active': False})
    
    db.commit()
    
    logger.info(f"删除小组 - 小组UUID: {group_id}, 操作者: {current_admin.username}")
    
    return success_response(message="小组已删除")


# ===== 班级教师管理 =====

@router.get("/classes/{class_id}/teachers")
def get_class_teachers(
    class_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级教师列表"""
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（学校管理员只能查看本校班级）
    if current_admin.role != 'platform_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 查询班级教师
    class_teachers = db.query(PBLClassTeacher).filter(
        PBLClassTeacher.class_id == pbl_class.id
    ).all()
    
    result = []
    for ct in class_teachers:
        teacher = db.query(User).filter(User.id == ct.teacher_id).first()
        if teacher:
            result.append({
                'id': ct.id,
                'teacher_id': teacher.id,
                'teacher_name': teacher.name or teacher.real_name,
                'teacher_number': teacher.teacher_number,
                'subject': ct.subject,
                'is_primary': ct.is_primary == 1,
                'created_at': ct.created_at.isoformat() if ct.created_at else None
            })
    
    return success_response(data=result)


@router.post("/classes/{class_id}/teachers")
def assign_teacher_to_class(
    class_id: str,
    request: AssignTeacherRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """为班级分配教师"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查（学校管理员只能操作本校班级）
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 验证教师存在且是教师角色
    teacher = db.query(User).filter(
        User.id == request.teacher_id,
        User.role == 'teacher'
    ).first()
    
    if not teacher:
        return error_response(
            message="教师不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查是否已经分配
    existing = db.query(PBLClassTeacher).filter(
        PBLClassTeacher.class_id == pbl_class.id,
        PBLClassTeacher.teacher_id == request.teacher_id
    ).first()
    
    if existing:
        return error_response(
            message="该教师已分配到此班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 如果设置为班主任，先取消其他班主任
    if request.is_primary:
        db.query(PBLClassTeacher).filter(
            PBLClassTeacher.class_id == pbl_class.id,
            PBLClassTeacher.is_primary == 1
        ).update({'is_primary': 0})
        
        # 同时更新班级表的class_teacher_id
        pbl_class.class_teacher_id = request.teacher_id
    
    # 创建班级教师关联记录
    class_teacher = PBLClassTeacher(
        class_id=pbl_class.id,
        teacher_id=request.teacher_id,
        subject=request.subject,
        is_primary=1 if request.is_primary else 0
    )
    db.add(class_teacher)
    db.commit()
    db.refresh(class_teacher)
    
    logger.info(f"为班级分配教师 - 班级UUID: {class_id}, 教师ID: {request.teacher_id}, 操作者: {current_admin.username}")
    
    return success_response(
        data={
            'id': class_teacher.id,
            'teacher_id': request.teacher_id,
            'teacher_name': teacher.name or teacher.real_name,
            'subject': request.subject,
            'is_primary': request.is_primary
        },
        message="教师分配成功"
    )


@router.delete("/classes/{class_id}/teachers/{teacher_id}")
def remove_teacher_from_class(
    class_id: str,
    teacher_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """从班级移除教师"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查找班级教师记录
    class_teacher = db.query(PBLClassTeacher).filter(
        PBLClassTeacher.class_id == pbl_class.id,
        PBLClassTeacher.teacher_id == teacher_id
    ).first()
    
    if not class_teacher:
        return error_response(
            message="该教师未分配到此班级",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 如果是班主任，清除班级表的class_teacher_id
    if class_teacher.is_primary == 1:
        pbl_class.class_teacher_id = None
    
    # 删除关联记录
    db.delete(class_teacher)
    db.commit()
    
    logger.info(f"从班级移除教师 - 班级UUID: {class_id}, 教师ID: {teacher_id}, 操作者: {current_admin.username}")
    
    return success_response(message="教师已从班级移除")


# ===== 班级课程管理 =====

@router.get("/classes/{class_id}/courses")
def get_class_courses(
    class_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取班级课程列表"""
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
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
    
    # 查询班级课程
    class_courses = db.query(PBLClassCourse).filter(
        PBLClassCourse.class_id == pbl_class.id
    ).all()
    
    result = []
    for cc in class_courses:
        course = db.query(PBLCourse).filter(PBLCourse.id == cc.course_id).first()
        if course:
            # 统计班级成员数（所有班级成员自动拥有课程访问权限）
            enrolled_count = db.query(PBLClassMember).filter(
                PBLClassMember.class_id == pbl_class.id,
                PBLClassMember.is_active == 1
            ).count()

            result.append({
                'id': cc.id,
                'uuid': cc.uuid,
                'course_id': course.id,
                'course_uuid': course.uuid,
                'course_title': course.title,
                'course_description': course.description,
                'course_cover': course.cover_image,
                'status': cc.status,
                'start_date': cc.start_date.isoformat() if cc.start_date else None,
                'end_date': cc.end_date.isoformat() if cc.end_date else None,
                'assigned_at': cc.assigned_at.isoformat() if cc.assigned_at else None,
                'enrolled_count': enrolled_count,
                'remarks': cc.remarks
            })
    
    return success_response(data=result)


@router.post("/classes/{class_id}/courses")
def assign_course_to_class(
    class_id: str,
    request: AssignCourseRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """为班级分配课程（会自动为班级所有学生分配该课程）"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role == 'school_admin':
        if pbl_class.school_id != current_admin.school_id:
            return error_response(
                message="无权限操作该班级",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 验证课程存在
    course = db.query(PBLCourse).filter(PBLCourse.id == request.course_id).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查是否已经分配
    existing = db.query(PBLClassCourse).filter(
        PBLClassCourse.class_id == pbl_class.id,
        PBLClassCourse.course_id == request.course_id
    ).first()
    
    if existing:
        return error_response(
            message="该课程已分配给此班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 创建班级课程分配记录
    class_course = PBLClassCourse(
        class_id=pbl_class.id,
        course_id=request.course_id,
        assigned_by=current_admin.id,
        start_date=datetime.fromisoformat(request.start_date) if request.start_date else None,
        end_date=datetime.fromisoformat(request.end_date) if request.end_date else None,
        status='active',
        remarks=request.remarks
    )
    db.add(class_course)
    db.flush()
    
    # 注意：班级成员自动拥有班级课程的访问权限，无需创建选课记录
    # 统计班级成员数量
    enrolled_count = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).count()

    db.commit()
    db.refresh(class_course)
    
    logger.info(f"为班级分配课程 - 班级UUID: {class_id}, 课程ID: {request.course_id}, 自动分配学生数: {enrolled_count}, 操作者: {current_admin.username}")
    
    return success_response(
        data={
            'id': class_course.id,
            'uuid': class_course.uuid,
            'course_id': request.course_id,
            'course_title': course.title,
            'enrolled_students': enrolled_count
        },
        message=f"课程分配成功，已为 {enrolled_count} 名学生自动分配该课程"
    )


@router.delete("/classes/{class_id}/courses/{course_uuid}")
def remove_course_from_class(
    class_id: str,
    course_uuid: str,
    remove_student_enrollments: bool = False,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """从班级移除课程"""
    # 权限检查
    if current_admin.role not in ['platform_admin', 'school_admin']:
        return error_response(
            message="无权限操作",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查找班级课程记录
    class_course = db.query(PBLClassCourse).filter(
        PBLClassCourse.uuid == course_uuid,
        PBLClassCourse.class_id == pbl_class.id
    ).first()
    
    if not class_course:
        return error_response(
            message="该课程未分配给此班级",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 注意：不再需要删除选课记录，因为访问控制已改为基于班级成员关系
    
    # 删除班级课程分配记录
    db.delete(class_course)
    db.commit()
    
    logger.info(f"从班级移除课程 - 班级UUID: {class_id}, 课程UUID: {course_uuid}, 操作者: {current_admin.username}")
    
    return success_response(message="课程已从班级移除")


# ===== 班级学习进度查询 =====

@router.get("/classes/{class_id}/progress")
def get_class_learning_progress(
    class_id: str,
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """查看班级学生的课程学习进度"""
    # 根据UUID查询班级
    pbl_class = db.query(PBLClass).filter(PBLClass.uuid == class_id).first()
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
    
    # 查询班级所有学生（通过班级成员表）
    students = db.query(User).join(
        PBLClassMember,
        User.id == PBLClassMember.student_id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1,
        User.deleted_at == None
    ).all()
    
    # 如果指定了课程ID，只查询该课程的进度
    courses_query = db.query(PBLCourse)
    if course_id:
        courses_query = courses_query.filter(PBLCourse.id == course_id)
    else:
        # 否则查询班级所有分配的课程
        class_course_ids = db.query(PBLClassCourse.course_id).filter(
            PBLClassCourse.class_id == pbl_class.id
        ).all()
        course_ids = [cc[0] for cc in class_course_ids]
        courses_query = courses_query.filter(PBLCourse.id.in_(course_ids))
    
    courses = courses_query.all()
    
    result = []
    for student in students:
        student_data = {
            'student_id': student.id,
            'student_name': student.name or student.real_name,
            'student_number': student.student_number,
            'courses': []
        }
        
        for course in courses:
            # 统计课程单元数
            total_units = db.query(PBLUnit).filter(
                PBLUnit.course_id == course.id
            ).count()
            
            # 统计已完成单元数
            completed_units = db.query(PBLLearningProgress).filter(
                PBLLearningProgress.user_id == student.id,
                PBLLearningProgress.course_id == course.id,
                PBLLearningProgress.progress_type == 'unit_complete',
                PBLLearningProgress.status == 'completed'
            ).count()
            
            # 统计任务完成情况
            total_tasks = db.query(PBLTask).join(PBLUnit).filter(
                PBLUnit.course_id == course.id
            ).count()
            
            completed_tasks = db.query(PBLTaskProgress).join(PBLTask).join(PBLUnit).filter(
                PBLUnit.course_id == course.id,
                PBLTaskProgress.user_id == student.id,
                PBLTaskProgress.submission.isnot(None)  # 只要提交了就算完成
            ).count()
            
            # 计算平均分
            avg_score_result = db.query(func.avg(PBLTaskProgress.score)).join(PBLTask).join(PBLUnit).filter(
                PBLUnit.course_id == course.id,
                PBLTaskProgress.user_id == student.id,
                PBLTaskProgress.score != None
            ).scalar()
            
            avg_score = float(avg_score_result) if avg_score_result else None
            
            # 计算课程进度（基于完成的单元数）
            course_progress_percent = int((completed_units / total_units * 100)) if total_units > 0 else 0
            
            course_progress = {
                'course_id': course.id,
                'course_uuid': course.uuid,
                'course_title': course.title,
                'progress': course_progress_percent,
                'total_units': total_units,
                'completed_units': completed_units,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'avg_score': round(avg_score, 2) if avg_score else None
            }
            
            student_data['courses'].append(course_progress)
        
        result.append(student_data)
    
    return success_response(data=result)
