"""
课程管理API
提供课程、选课、教师-课程关联、分组的CRUD操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime
from io import BytesIO

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.utils.excel_handler import read_excel_file, generate_excel_template
from app.models.user import User
from app.models.team import Team
from app.models.device import Device
from app.models.course_model import Course, CourseTeacher, CourseStudent, CourseGroup, GroupMember
from app.models.device_group import DeviceGroup, DeviceGroupMember, CourseDeviceAuthorization
from app.schemas.course_schema import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse, CourseStatistics,
    CourseEnrollRequest, CourseEnrollBatchRequest, CourseEnrollmentUpdate, 
    CourseEnrollmentResponse, CourseEnrollmentListResponse,
    CourseTeacherAdd, CourseTeacherBatchAdd, CourseTeacherResponse, CourseTeacherListResponse,
    CourseGroupCreate, CourseGroupUpdate, CourseGroupResponse, CourseGroupListResponse,
    GroupMemberAdd, GroupMemberBatchAdd, GroupMemberResponse, GroupMemberListResponse
)
from app.schemas.device_group import (
    CourseDeviceAuthorizationCreate, CourseDeviceAuthorizationUpdate,
    CourseDeviceAuthorizationResponse, CourseDeviceAuthorizationListResponse,
    AuthorizedDeviceResponse
)
from app.utils.timezone import get_beijing_time_naive

router = APIRouter(prefix="/courses", tags=["课程管理"])

# ============================================================================
# 权限检查函数
# ============================================================================

def check_team_admin_or_teacher(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为团队管理员或教师"""
    if current_user.role not in ['platform_admin', 'team_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有团队管理员和教师才能执行此操作"
        )
    return current_user


# ============================================================================
# 课程管理 APIs
# ============================================================================

@router.post("", response_model=dict)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """创建课程（教师和团队管理员可创建）"""
    # 权限检查和团队ID设置
    team_id = current_user.team_id
    
    # 教师创建课程时，自动使用自己的团队ID
    if current_user.role == 'teacher':
        if not team_id:
            return error_response(message="教师账号未关联团队", code=400)
        # 强制使用教师的团队ID
        course_data.team_id = team_id
    elif current_user.role == 'team_admin':
        # 团队管理员只能创建自己团队的课程
        if course_data.team_id != team_id:
            return error_response(message="无权创建其他团队的课程", code=403)
    
    # 检查团队是否存在
    team = db.query(Team).filter(Team.id == course_data.team_id).first()
    if not team:
        return error_response(message="团队不存在", code=404)
    
    # 检查课程名称是否重复
    existing = db.query(Course).filter(
        Course.team_id == course_data.team_id,
        Course.course_name == course_data.course_name,
        Course.deleted_at.is_(None)
    ).first()
    
    if existing:
        return error_response(message="课程名称已存在", code=400)
    
    # 创建课程
    course = Course(
        team_id=course_data.team_id,
        course_name=course_data.course_name,
        course_code=course_data.course_code,
        academic_year=course_data.academic_year,
        semester=course_data.semester if course_data.semester else None,
        max_students=course_data.max_students,
        credits=course_data.credits,
        description=course_data.description,
        is_active=True
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return success_response(
        data=CourseResponse.from_orm(course).model_dump(),
        message="课程创建成功"
    )


@router.get("", response_model=dict)
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    team_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程列表"""
    # 构建查询
    query = db.query(Course).filter(Course.deleted_at.is_(None))
    
    # 权限控制
    if current_user.role == 'team_admin':
        query = query.filter(Course.team_id == current_user.team_id)
    elif current_user.role == 'teacher':
        # 教师只能看到自己教的课程
        teacher_course_ids = db.query(CourseTeacher.course_id).filter(
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).all()
        course_ids = [cid[0] for cid in teacher_course_ids]
        if course_ids:
            query = query.filter(Course.id.in_(course_ids))
        else:
            # 没有课程就返回空
            return success_response(data={
                "total": 0,
                "page": page,
                "page_size": page_size,
                "courses": []
            })
    elif current_user.role == 'student':
        # 学生只能看到自己选的课程
        student_course_ids = db.query(CourseStudent.course_id).filter(
            CourseStudent.student_id == current_user.id,
            CourseStudent.deleted_at.is_(None)
        ).all()
        course_ids = [cid[0] for cid in student_course_ids]
        if course_ids:
            query = query.filter(Course.id.in_(course_ids))
        else:
            return success_response(data={
                "total": 0,
                "page": page,
                "page_size": page_size,
                "courses": []
            })
    
    # 团队筛选
    if team_id:
        query = query.filter(Course.team_id == team_id)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Course.course_name.like(f"%{keyword}%"),
                Course.course_code.like(f"%{keyword}%")
            )
        )
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(Course.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    courses = query.order_by(Course.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式，并添加教师信息、设备组信息、分组信息
    course_list = []
    for course in courses:
        course_dict = CourseListResponse.from_orm(course).model_dump()
        
        # 查询该课程的所有教师
        course_teachers = db.query(CourseTeacher, User).join(
            User, CourseTeacher.teacher_id == User.id
        ).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.deleted_at.is_(None)
        ).all()
        
        # 添加教师信息
        course_dict['teachers'] = [
            {
                "id": teacher.id,
                "name": teacher.real_name or teacher.name or teacher.username,
                "username": teacher.username
            }
            for _, teacher in course_teachers
        ]
        
        # 查询授权的设备组信息
        device_authorizations = db.query(
            CourseDeviceAuthorization,
            DeviceGroup
        ).join(
            DeviceGroup, CourseDeviceAuthorization.device_group_id == DeviceGroup.id
        ).filter(
            CourseDeviceAuthorization.course_id == course.id,
            CourseDeviceAuthorization.is_active == True,
            DeviceGroup.deleted_at.is_(None)
        ).all()
        
        # 添加设备组信息
        device_groups_info = []
        total_devices = 0
        for auth, group in device_authorizations:
            # 动态计算设备数量
            device_count = db.query(func.count(DeviceGroupMember.id)).filter(
                DeviceGroupMember.group_id == group.id,
                DeviceGroupMember.left_at.is_(None)
            ).scalar() or 0
            
            device_groups_info.append({
                "group_id": group.id,
                "group_uuid": group.uuid,
                "group_name": group.group_name,
                "device_count": device_count,
                "expires_at": auth.expires_at
            })
            total_devices += device_count
        
        course_dict['device_groups'] = device_groups_info
        course_dict['total_devices'] = total_devices
        
        # 查询学生分组数量
        group_count = db.query(func.count(CourseGroup.id)).filter(
            CourseGroup.course_id == course.id,
            CourseGroup.deleted_at.is_(None)
        ).scalar() or 0
        
        course_dict['group_count'] = group_count
        
        course_list.append(course_dict)
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "courses": course_list
    })


@router.get("/{course_uuid}", response_model=dict)
async def get_course(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程详情"""
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权查看该课程", code=403)
    
    return success_response(data=CourseResponse.from_orm(course).model_dump())


@router.put("/{course_uuid}", response_model=dict)
async def update_course(
    course_uuid: str,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """更新课程信息"""
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权修改该课程", code=403)
    
    # 更新字段
    if course_data.course_name is not None:
        course.course_name = course_data.course_name
    if course_data.course_code is not None:
        course.course_code = course_data.course_code
    if course_data.academic_year is not None:
        course.academic_year = course_data.academic_year
    if course_data.semester is not None:
        course.semester = course_data.semester if course_data.semester else None
    if course_data.max_students is not None:
        course.max_students = course_data.max_students
    if course_data.credits is not None:
        course.credits = course_data.credits
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.is_active is not None:
        course.is_active = course_data.is_active
    
    course.updated_at = get_beijing_time_naive()
    db.commit()
    db.refresh(course)
    
    return success_response(
        data=CourseResponse.from_orm(course).model_dump(),
        message="课程更新成功"
    )


@router.delete("/{course_uuid}", response_model=dict)
async def delete_course(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """删除课程（软删除）"""
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权删除该课程", code=403)
    
    # 软删除
    course.deleted_at = get_beijing_time_naive()
    db.commit()
    
    return success_response(message="课程删除成功")


@router.get("/{course_uuid}/statistics", response_model=dict)
async def get_course_statistics(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程统计信息"""
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权查看该课程", code=403)
    
    # 统计数据
    teacher_count = db.query(func.count(CourseTeacher.id)).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.deleted_at.is_(None)
    ).scalar()
    
    enrolled_count = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).scalar()
    
    completed_count = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.status == 'completed',
        CourseStudent.deleted_at.is_(None)
    ).scalar()
    
    group_count = db.query(func.count(CourseGroup.id)).filter(
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).scalar()
    
    return success_response(data={
        "course_id": course.id,
        "course_uuid": course.uuid,
        "course_name": course.course_name,
        "teacher_count": teacher_count,
        "enrolled_students": enrolled_count,
        "completed_students": completed_count,
        "total_students": enrolled_count + completed_count,
        "max_students": course.max_students,
        "group_count": group_count,
        "credits": float(course.credits) if course.credits else 0
    })


# ============================================================================
# 教师-课程关联管理 APIs
# ============================================================================

@router.post("/{course_uuid}/teachers", response_model=dict)
async def add_course_teacher(
    course_uuid: str,
    teacher_data: CourseTeacherAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """为课程添加教师"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 检查教师是否存在且是教师角色
    teacher = db.query(User).filter(
        User.id == teacher_data.teacher_id,
        User.role == 'teacher',
        User.deleted_at.is_(None)
    ).first()
    
    if not teacher:
        return error_response(message="教师不存在", code=404)
    
    # 检查是否已存在关联
    existing = db.query(CourseTeacher).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.teacher_id == teacher_data.teacher_id,
        CourseTeacher.deleted_at.is_(None)
    ).first()
    
    if existing:
        return error_response(message="该教师已在课程中", code=400)
    
    # 创建关联
    course_teacher = CourseTeacher(
        course_id=course.id,
        teacher_id=teacher_data.teacher_id
    )
    
    db.add(course_teacher)
    
    # 更新课程教师数
    course.teacher_count = db.query(func.count(CourseTeacher.id)).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.deleted_at.is_(None)
    ).scalar() + 1
    
    db.commit()
    db.refresh(course_teacher)
    
    # 构建响应数据
    response_data = {
        "id": course_teacher.id,
        "course_id": course.id,
        "teacher_id": teacher.id,
        "teacher_name": teacher.real_name or teacher.username,
        "teacher_username": teacher.username,
        "created_at": course_teacher.created_at
    }
    
    return success_response(data=response_data, message="教师添加成功")


@router.post("/{course_uuid}/teachers/batch", response_model=dict)
async def batch_add_course_teachers(
    course_uuid: str,
    batch_data: CourseTeacherBatchAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """批量为课程添加教师"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 批量添加
    added_count = 0
    skipped_count = 0
    
    for teacher_id in batch_data.teacher_ids:
        # 检查教师是否存在
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == 'teacher',
            User.deleted_at.is_(None)
        ).first()
        
        if not teacher:
            skipped_count += 1
            continue
        
        # 检查是否已存在关联
        existing = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == teacher_id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建关联
        course_teacher = CourseTeacher(
            course_id=course.id,
            teacher_id=teacher_id
        )
        
        db.add(course_teacher)
        added_count += 1
    
    # 更新课程教师数
    course.teacher_count = db.query(func.count(CourseTeacher.id)).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.deleted_at.is_(None)
    ).scalar() + added_count
    
    db.commit()
    
    return success_response(
        data={"added": added_count, "skipped": skipped_count},
        message=f"批量添加完成，成功{added_count}个，跳过{skipped_count}个"
    )


@router.get("/{course_uuid}/teachers", response_model=dict)
async def list_course_teachers(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程的教师列表"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权查看该课程", code=403)
    
    # 查询教师列表
    teachers = db.query(CourseTeacher, User).join(
        User, CourseTeacher.teacher_id == User.id
    ).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.deleted_at.is_(None),
        User.deleted_at.is_(None)
    ).all()
    
    teacher_list = []
    for ct, user in teachers:
        teacher_list.append({
            "id": ct.id,
            "teacher_id": user.id,
            "teacher_name": user.real_name or user.username,
            "teacher_username": user.username
        })
    
    return success_response(data={"teachers": teacher_list})


@router.delete("/{course_uuid}/teachers/{teacher_uuid}", response_model=dict)
async def remove_course_teacher(
    course_uuid: str,
    teacher_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """从课程移除教师"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找教师
    teacher = db.query(User).filter(
        User.uuid == teacher_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not teacher:
        return error_response(message="教师不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 查找关联记录
    course_teacher = db.query(CourseTeacher).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.teacher_id == teacher.id,
        CourseTeacher.deleted_at.is_(None)
    ).first()
    
    if not course_teacher:
        return error_response(message="该教师不在课程中", code=404)
    
    # 软删除
    course_teacher.deleted_at = get_beijing_time_naive()
    
    # 更新课程教师数
    course.teacher_count = db.query(func.count(CourseTeacher.id)).filter(
        CourseTeacher.course_id == course.id,
        CourseTeacher.deleted_at.is_(None)
    ).scalar() - 1
    
    db.commit()
    
    return success_response(message="教师移除成功")


# ============================================================================
# 选课管理 APIs（新增核心功能）
# ============================================================================

@router.post("/{course_uuid}/enroll", response_model=dict)
async def enroll_course(
    course_uuid: str,
    enroll_data: CourseEnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生选课"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None),
        Course.is_active == True
    ).first()
    
    if not course:
        return error_response(message="课程不存在或已关闭", code=404)
    
    # 权限检查：只有团队管理员和学生本人可以选课
    if current_user.role == 'student' and current_user.id != enroll_data.student_id:
        return error_response(message="只能为自己选课", code=403)
    elif current_user.role not in ['platform_admin', 'team_admin', 'student']:
        return error_response(message="无权选课", code=403)
    
    # 检查学生是否存在
    student = db.query(User).filter(
        User.id == enroll_data.student_id,
        User.role == 'student',
        User.deleted_at.is_(None)
    ).first()
    
    if not student:
        return error_response(message="学生不存在", code=404)
    
    # 检查是否已选课
    existing = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == enroll_data.student_id,
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if existing:
        if existing.status == 'dropped':
            # 已退课，可以重新选课
            existing.status = 'enrolled'
            existing.enrolled_at = get_beijing_time_naive()
            existing.deleted_at = None
            db.commit()
            return success_response(message="重新选课成功")
        else:
            return error_response(message="已经选过该课程", code=400)
    
    # 检查课程是否已满
    current_students = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).scalar()
    
    if current_students >= course.max_students:
        return error_response(message=f"课程已满（{course.max_students}人）", code=400)
    
    # 创建选课记录
    enrollment = CourseStudent(
        course_id=course.id,
        student_id=enroll_data.student_id,
        status='enrolled'
    )
    
    db.add(enrollment)
    
    # 更新课程学生数
    course.student_count = current_students + 1
    
    db.commit()
    db.refresh(enrollment)
    
    return success_response(
        data={
            "id": enrollment.id,
            "course_id": course.id,
            "course_name": course.course_name,
            "student_id": student.id,
            "student_name": student.real_name or student.username,
            "enrolled_at": enrollment.enrolled_at,
            "status": enrollment.status
        },
        message="选课成功"
    )


@router.post("/{course_uuid}/enroll/batch", response_model=dict)
async def batch_enroll_course(
    course_uuid: str,
    batch_data: CourseEnrollBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """批量选课（管理员操作）"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None),
        Course.is_active == True
    ).first()
    
    if not course:
        return error_response(message="课程不存在或已关闭", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 检查课程容量
    current_students = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).scalar()
    
    available_slots = course.max_students - current_students
    
    if len(batch_data.student_ids) > available_slots:
        return error_response(
            message=f"课程剩余名额不足（剩余{available_slots}个，需要{len(batch_data.student_ids)}个）",
            code=400
        )
    
    # 批量选课
    enrolled_count = 0
    skipped_count = 0
    
    for student_id in batch_data.student_ids:
        # 检查学生是否存在
        student = db.query(User).filter(
            User.id == student_id,
            User.role == 'student',
            User.deleted_at.is_(None)
        ).first()
        
        if not student:
            skipped_count += 1
            continue
        
        # 确保只能添加本校学生
        if student.team_id != course.team_id:
            skipped_count += 1
            continue
        
        # 检查是否已选课
        existing = db.query(CourseStudent).filter(
            CourseStudent.course_id == course.id,
            CourseStudent.student_id == student_id,
            CourseStudent.deleted_at.is_(None)
        ).first()
        
        if existing and existing.status != 'dropped':
            skipped_count += 1
            continue
        
        if existing and existing.status == 'dropped':
            # 重新选课
            existing.status = 'enrolled'
            existing.enrolled_at = get_beijing_time_naive()
        else:
            # 新选课
            enrollment = CourseStudent(
                course_id=course.id,
                student_id=student_id,
                status='enrolled'
            )
            db.add(enrollment)
        
        enrolled_count += 1
    
    # 更新课程学生数
    course.student_count = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).scalar()
    
    db.commit()
    
    return success_response(
        data={"enrolled": enrolled_count, "skipped": skipped_count},
        message=f"批量选课完成，成功{enrolled_count}个，跳过{skipped_count}个"
    )


@router.get("/{course_uuid}/students", response_model=dict)
async def list_course_students(
    course_uuid: str,
    status_filter: Optional[str] = Query(None, description="状态筛选：enrolled/completed/dropped"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程的学生列表（选课记录）"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权查看该课程", code=403)
    
    # 构建查询
    query = db.query(CourseStudent, User).join(
        User, CourseStudent.student_id == User.id
    ).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.deleted_at.is_(None),
        User.deleted_at.is_(None)
    )
    
    # 状态筛选
    if status_filter:
        query = query.filter(CourseStudent.status == status_filter)
    
    # 总数
    total = query.count()
    
    # 分页
    enrollments = query.order_by(CourseStudent.enrolled_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    student_list = []
    for cs, user in enrollments:
        student_list.append({
            "id": cs.id,
            "course_id": course.id,
            "course_name": course.course_name,
            "student_id": user.id,
            "student_name": user.real_name or user.username,
            "student_number": user.student_number,
            "status": cs.status,
            "score": float(cs.score) if cs.score else None,
            "enrolled_at": cs.enrolled_at
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "students": student_list
    })


@router.put("/{course_uuid}/students/{student_id}", response_model=dict)
async def update_enrollment(
    course_uuid: str,
    student_id: int,
    update_data: CourseEnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """更新选课状态或成绩"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 查找选课记录
    enrollment = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == student_id,
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if not enrollment:
        return error_response(message="未找到选课记录", code=404)
    
    # 更新状态
    if update_data.status is not None:
        old_status = enrollment.status
        enrollment.status = update_data.status
        
        # 如果状态变为 dropped，更新课程学生数
        if update_data.status == 'dropped' and old_status == 'enrolled':
            course.student_count = max(0, course.student_count - 1)
    
    # 更新成绩
    if update_data.score is not None:
        enrollment.score = update_data.score
    
    db.commit()
    
    return success_response(message="选课信息更新成功")


@router.delete("/{course_uuid}/students/{student_uuid}", response_model=dict)
async def drop_course(
    course_uuid: str,
    student_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """退课"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找学生
    student = db.query(User).filter(
        User.uuid == student_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not student:
        return error_response(message="学生不存在", code=404)
    
    # 权限检查：学生只能为自己退课
    if current_user.role == 'student' and current_user.uuid != student_uuid:
        return error_response(message="只能为自己退课", code=403)
    elif current_user.role not in ['platform_admin', 'team_admin', 'student']:
        return error_response(message="无权退课", code=403)
    
    # 查找选课记录
    enrollment = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == student.id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if not enrollment:
        return error_response(message="未找到选课记录或已退课", code=404)
    
    # 标记为退课
    enrollment.status = 'dropped'
    
    # 更新课程学生数
    course.student_count = max(0, course.student_count - 1)
    
    # 从分组中移除（如果有）
    group_memberships = db.query(GroupMember).filter(
        GroupMember.course_id == course.id,
        GroupMember.student_id == student_id,
        GroupMember.left_at.is_(None)
    ).all()
    
    for membership in group_memberships:
        membership.left_at = get_beijing_time_naive()
        
        # 更新小组成员数
        group = db.query(CourseGroup).filter(CourseGroup.id == membership.group_id).first()
        if group:
            group.member_count = max(0, group.member_count - 1)
    
    db.commit()
    
    return success_response(message="退课成功")


# ============================================================================
# 课程分组管理 APIs
# ============================================================================

@router.post("/{course_uuid}/groups", response_model=dict)
async def create_course_group(
    course_uuid: str,
    group_data: CourseGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """创建课程分组"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该课程", code=403)
    
    # 创建分组
    group = CourseGroup(
        course_id=course.id,
        team_id=course.team_id,
        group_name=group_data.group_name,
        group_number=group_data.group_number,
        leader_id=group_data.leader_id,
        description=group_data.description
    )
    
    # 如果指定了组长，设置组长姓名
    if group_data.leader_id:
        leader = db.query(User).filter(User.id == group_data.leader_id).first()
        if leader:
            group.leader_name = leader.real_name or leader.username
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    return success_response(
        data=CourseGroupResponse.from_orm(group).model_dump(),
        message="分组创建成功"
    )


@router.get("/{course_uuid}/groups", response_model=dict)
async def list_course_groups(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程的分组列表"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查询分组列表
    groups = db.query(CourseGroup).filter(
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).order_by(CourseGroup.group_number, CourseGroup.created_at).all()
    
    group_list = [CourseGroupListResponse.from_orm(g).model_dump() for g in groups]
    
    return success_response(data={"groups": group_list})


@router.put("/{course_uuid}/groups/{group_uuid}", response_model=dict)
async def update_course_group(
    course_uuid: str,
    group_uuid: str,
    group_data: CourseGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """更新分组信息"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权操作该分组", code=403)
    
    # 更新字段
    if group_data.group_name is not None:
        group.group_name = group_data.group_name
    if group_data.group_number is not None:
        group.group_number = group_data.group_number
    if group_data.leader_id is not None:
        group.leader_id = group_data.leader_id
        leader = db.query(User).filter(User.id == group_data.leader_id).first()
        if leader:
            group.leader_name = leader.real_name or leader.username
    if group_data.description is not None:
        group.description = group_data.description
    if group_data.is_active is not None:
        group.is_active = group_data.is_active
    
    group.updated_at = get_beijing_time_naive()
    db.commit()
    
    return success_response(message="分组更新成功")


@router.delete("/{course_uuid}/groups/{group_uuid}", response_model=dict)
async def delete_course_group(
    course_uuid: str,
    group_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """删除分组"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权删除该分组", code=403)
    
    # 软删除
    group.deleted_at = get_beijing_time_naive()
    
    # 标记所有成员的离开时间
    db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.left_at.is_(None)
    ).update({"left_at": get_beijing_time_naive()})
    
    db.commit()
    
    return success_response(message="分组删除成功")


# ============================================================================
# 分组成员管理 APIs
# ============================================================================

@router.post("/{course_uuid}/groups/{group_uuid}/members", response_model=dict)
async def add_group_member(
    course_uuid: str,
    group_uuid: str,
    member_data: GroupMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """添加分组成员"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 检查学生是否存在且已选该课程
    enrollment = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == member_data.student_id,
        CourseStudent.status == 'enrolled',
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if not enrollment:
        return error_response(message="学生未选该课程", code=400)
    
    # 检查是否已在其他分组
    existing = db.query(GroupMember).filter(
        GroupMember.course_id == course.id,
        GroupMember.student_id == member_data.student_id,
        GroupMember.left_at.is_(None)
    ).first()
    
    if existing:
        return error_response(message="学生已在其他分组中", code=400)
    
    # 获取学生信息
    student = db.query(User).filter(User.id == member_data.student_id).first()
    
    # 创建成员记录
    member = GroupMember(
        group_id=group.id,
        course_id=course.id,
        team_id=course.team_id,
        student_id=member_data.student_id,
        student_name=student.real_name or student.username if student else None,
        student_number=student.student_number if student else None,
        is_leader=member_data.is_leader
    )
    
    db.add(member)
    
    # 更新小组成员数
    group.member_count = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id == group.id,
        GroupMember.left_at.is_(None)
    ).scalar() + 1
    
    # 如果设为组长，更新分组的组长信息
    if member_data.is_leader:
        group.leader_id = member_data.student_id
        group.leader_name = student.real_name or student.username if student else None
    
    db.commit()
    
    return success_response(message="成员添加成功")


@router.post("/{course_uuid}/groups/{group_uuid}/members/batch", response_model=dict)
async def batch_add_group_members(
    course_uuid: str,
    group_uuid: str,
    batch_data: GroupMemberBatchAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """批量添加分组成员"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 批量添加
    added_count = 0
    skipped_count = 0
    
    for student_id in batch_data.student_ids:
        # 检查是否已选该课程
        enrollment = db.query(CourseStudent).filter(
            CourseStudent.course_id == course.id,
            CourseStudent.student_id == student_id,
            CourseStudent.status == 'enrolled',
            CourseStudent.deleted_at.is_(None)
        ).first()
        
        if not enrollment:
            skipped_count += 1
            continue
        
        # 检查是否已在分组
        existing = db.query(GroupMember).filter(
            GroupMember.course_id == course.id,
            GroupMember.student_id == student_id,
            GroupMember.left_at.is_(None)
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        
        # 创建成员记录
        member = GroupMember(
            group_id=group.id,
            course_id=course.id,
            team_id=course.team_id,
            student_id=student_id,
            student_name=student.real_name or student.username if student else None,
            student_number=student.student_number if student else None,
            is_leader=False
        )
        
        db.add(member)
        added_count += 1
    
    # 更新小组成员数
    group.member_count = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id == group.id,
        GroupMember.left_at.is_(None)
    ).scalar()
    
    db.commit()
    
    return success_response(
        data={"added": added_count, "skipped": skipped_count},
        message=f"批量添加完成，成功{added_count}个，跳过{skipped_count}个"
    )


@router.get("/{course_uuid}/groups/{group_uuid}/members", response_model=dict)
async def list_group_members(
    course_uuid: str,
    group_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分组成员列表"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 查询成员列表
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.left_at.is_(None)
    ).order_by(GroupMember.is_leader.desc(), GroupMember.joined_at).all()
    
    member_list = [GroupMemberListResponse.from_orm(m).model_dump() for m in members]
    
    return success_response(data={"members": member_list})


@router.put("/{course_uuid}/groups/{group_uuid}/leader/{student_id}", response_model=dict)
async def set_group_leader(
    course_uuid: str,
    group_uuid: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """设置分组组长"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 检查该学生是否在该组中
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.student_id == student_id,
        GroupMember.left_at.is_(None)
    ).first()
    
    if not member:
        return error_response(message="该学生不在该分组中", code=400)
    
    # 获取学生信息
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        return error_response(message="学生不存在", code=404)
    
    # 清除该组所有成员的组长标记
    db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.left_at.is_(None)
    ).update({"is_leader": False})
    
    # 设置新组长
    member.is_leader = True
    
    # 更新分组的组长信息
    group.leader_id = student_id
    group.leader_name = student.real_name or student.username
    
    db.commit()
    
    return success_response(message="组长设置成功")


@router.delete("/{course_uuid}/groups/{group_uuid}/members/{student_uuid}", response_model=dict)
async def remove_group_member(
    course_uuid: str,
    group_uuid: str,
    student_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """从分组移除成员"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找分组
    group = db.query(CourseGroup).filter(
        CourseGroup.uuid == group_uuid,
        CourseGroup.course_id == course.id,
        CourseGroup.deleted_at.is_(None)
    ).first()
    
    if not group:
        return error_response(message="分组不存在", code=404)
    
    # 查找学生
    student = db.query(User).filter(
        User.uuid == student_uuid,
        User.deleted_at.is_(None)
    ).first()
    
    if not student:
        return error_response(message="学生不存在", code=404)
    
    # 查找成员记录
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.student_id == student.id,
        GroupMember.left_at.is_(None)
    ).first()
    
    if not member:
        return error_response(message="该学生不是小组成员", code=400)
    
    # 标记离开时间
    member.left_at = get_beijing_time_naive()
    
    # 更新小组成员数
    group.member_count = max(0, group.member_count - 1)
    
    # 如果是组长，清除组长信息
    if group.leader_id == student_id:
        group.leader_id = None
        group.leader_name = None
    
    db.commit()
    
    return success_response(message="成员移除成功")


# ============================================================================
# 课程设备授权管理 APIs
# ============================================================================

@router.post("/{course_uuid}/device-authorizations", response_model=dict)
async def create_device_authorization(
    course_uuid: str,
    auth_data: CourseDeviceAuthorizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """为课程授权设备组（团队管理员操作）"""
    # 权限检查：只有团队管理员可以授权
    if current_user.role != 'team_admin' and current_user.role != 'platform_admin':
        return error_response(message="只有团队管理员才能授权设备", code=403)
    
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查：只能为本校课程授权
    if current_user.team_id != course.team_id:
        return error_response(message="只能为本校课程授权", code=403)
    
    # 查找设备组
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.id == auth_data.device_group_id,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 检查设备组是否属于本校
    if device_group.team_id != course.team_id:
        return error_response(message="设备组不属于本校", code=403)
    
    # 检查是否已存在有效授权
    existing = db.query(CourseDeviceAuthorization).filter(
        CourseDeviceAuthorization.course_id == course.id,
        CourseDeviceAuthorization.device_group_id == auth_data.device_group_id,
        CourseDeviceAuthorization.is_active == True,
        or_(
            CourseDeviceAuthorization.expires_at.is_(None),
            CourseDeviceAuthorization.expires_at > datetime.now()
        )
    ).first()
    
    if existing:
        return error_response(message="该设备组已授权给该课程", code=400)
    
    # 创建授权
    authorization = CourseDeviceAuthorization(
        course_id=course.id,
        device_group_id=auth_data.device_group_id,
        authorized_by=current_user.id,
        expires_at=auth_data.expires_at,
        notes=auth_data.notes,
        is_active=True
    )
    
    db.add(authorization)
    db.commit()
    db.refresh(authorization)
    
    # 构建响应数据
    response_data = {
        "id": authorization.id,
        "uuid": authorization.uuid,
        "course_id": course.id,
        "course_name": course.course_name,
        "device_group_id": device_group.id,
        "device_group_name": device_group.group_name,
        "device_count": device_group.device_count,
        "authorized_by": current_user.id,
        "authorized_by_name": current_user.real_name or current_user.username,
        "authorized_at": authorization.authorized_at,
        "expires_at": authorization.expires_at,
        "is_active": True,
        "notes": authorization.notes,
        "created_at": authorization.created_at
    }
    
    return success_response(data=response_data, message="设备授权成功")


@router.get("/{course_uuid}/device-authorizations", response_model=dict)
async def list_device_authorizations(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程的设备授权列表"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin' and current_user.team_id != course.team_id:
        return error_response(message="无权查看该课程", code=403)
    
    # 查询授权列表
    authorizations = db.query(CourseDeviceAuthorization, DeviceGroup).join(
        DeviceGroup, CourseDeviceAuthorization.device_group_id == DeviceGroup.id
    ).filter(
        CourseDeviceAuthorization.course_id == course.id,
        DeviceGroup.deleted_at.is_(None)
    ).order_by(CourseDeviceAuthorization.created_at.desc()).all()
    
    # 转换为响应格式
    auth_list = []
    now = datetime.now()
    
    for auth, device_group in authorizations:
        is_expired = auth.expires_at and auth.expires_at < now
        auth_list.append({
            "id": auth.id,
            "uuid": auth.uuid,
            "device_group_id": device_group.id,
            "device_group_name": device_group.group_name,
            "device_count": device_group.device_count,
            "authorized_at": auth.authorized_at,
            "expires_at": auth.expires_at,
            "is_active": auth.is_active and not is_expired,
            "is_expired": is_expired
        })
    
    return success_response(data={"authorizations": auth_list})


@router.put("/{course_uuid}/device-authorizations/{auth_id}", response_model=dict)
async def update_device_authorization(
    course_uuid: str,
    auth_id: int,
    auth_data: CourseDeviceAuthorizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """更新设备授权信息（如延期）"""
    # 权限检查
    if current_user.role not in ['platform_admin', 'team_admin']:
        return error_response(message="只有团队管理员才能修改授权", code=403)
    
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找授权记录
    authorization = db.query(CourseDeviceAuthorization).filter(
        CourseDeviceAuthorization.id == auth_id,
        CourseDeviceAuthorization.course_id == course.id
    ).first()
    
    if not authorization:
        return error_response(message="授权记录不存在", code=404)
    
    # 更新字段
    if auth_data.expires_at is not None:
        authorization.expires_at = auth_data.expires_at
    if auth_data.is_active is not None:
        authorization.is_active = auth_data.is_active
    if auth_data.notes is not None:
        authorization.notes = auth_data.notes
    
    authorization.updated_at = get_beijing_time_naive()
    db.commit()
    
    return success_response(message="授权更新成功")


@router.delete("/{course_uuid}/device-authorizations/{auth_id}", response_model=dict)
async def revoke_device_authorization(
    course_uuid: str,
    auth_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_team_admin_or_teacher)
):
    """撤销设备授权"""
    # 权限检查
    if current_user.role not in ['platform_admin', 'team_admin']:
        return error_response(message="只有团队管理员才能撤销授权", code=403)
    
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 查找授权记录
    authorization = db.query(CourseDeviceAuthorization).filter(
        CourseDeviceAuthorization.id == auth_id,
        CourseDeviceAuthorization.course_id == course.id
    ).first()
    
    if not authorization:
        return error_response(message="授权记录不存在", code=404)
    
    # 撤销授权
    authorization.is_active = False
    authorization.updated_at = get_beijing_time_naive()
    db.commit()
    
    return success_response(message="授权已撤销")


@router.get("/{course_uuid}/authorized-devices", response_model=dict)
async def list_authorized_devices(
    course_uuid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程已授权的设备列表（教师和学生可查看）"""
    # 查找课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 获取当前有效的授权
    now = datetime.now()
    authorizations = db.query(CourseDeviceAuthorization).filter(
        CourseDeviceAuthorization.course_id == course.id,
        CourseDeviceAuthorization.is_active == True,
        or_(
            CourseDeviceAuthorization.expires_at.is_(None),
            CourseDeviceAuthorization.expires_at > now
        )
    ).all()
    
    if not authorizations:
        return success_response(data={
            "total": 0,
            "page": page,
            "page_size": page_size,
            "devices": []
        })
    
    # 获取所有授权的设备组ID
    group_ids = [auth.device_group_id for auth in authorizations]
    
    # 查询设备列表
    query = db.query(DeviceGroupMember, Device, DeviceGroup).join(
        Device, DeviceGroupMember.device_id == Device.id
    ).join(
        DeviceGroup, DeviceGroupMember.group_id == DeviceGroup.id
    ).filter(
        DeviceGroupMember.group_id.in_(group_ids),
        DeviceGroupMember.left_at.is_(None),
        DeviceGroup.deleted_at.is_(None)
    )
    
    # 总数
    total = query.count()
    
    # 分页
    devices = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为响应格式
    device_list = []
    for member, device, group in devices:
        # 找到对应的授权记录
        auth = next((a for a in authorizations if a.device_group_id == group.id), None)
        
        device_list.append({
            "device_id": device.id,
            "device_name": device.name,
            "device_mac": device.mac_address or "",  # MAC地址，空值处理
            "device_status": device.device_status,
            "is_online": device.is_online,
            "group_name": group.group_name,
            "authorization_expires_at": auth.expires_at if auth else None
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "devices": device_list
    })


# ============================================================================
# 课程学生管理 API
# ============================================================================

@router.get("/{course_uuid}/students", response_model=dict)
async def get_course_students(
    course_uuid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程学生列表"""
    # 获取课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查：只有本校管理员和任课教师可以查看
    if current_user.role == 'team_admin':
        if current_user.team_id != course.team_id:
            return error_response(message="无权查看该课程", code=403)
    elif current_user.role == 'teacher':
        # 检查是否是该课程的任课教师
        is_teacher = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        if not is_teacher:
            return error_response(message="无权查看该课程", code=403)
    elif not is_admin_user(current_user):
        return error_response(message="无权查看该课程", code=403)
    
    # 构建查询 - 关联学生和分组信息
    query = db.query(
        CourseStudent,
        User,
        CourseGroup,
        GroupMember
    ).join(
        User, CourseStudent.student_id == User.id
    ).outerjoin(
        GroupMember, and_(
            GroupMember.student_id == User.id,
            GroupMember.course_id == course.id,
            GroupMember.deleted_at.is_(None)
        )
    ).outerjoin(
        CourseGroup, and_(
            CourseGroup.id == GroupMember.group_id,
            CourseGroup.deleted_at.is_(None)
        )
    ).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.deleted_at.is_(None)
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.name.like(f"%{keyword}%"),
                User.student_number.like(f"%{keyword}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    results = query.order_by(CourseStudent.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    student_list = []
    for enrollment, student, group, membership in results:
        student_list.append({
            "id": student.id,
            "student_number": student.student_number,
            "name": student.real_name or student.name or student.username,
            "gender": student.gender,
            "group_id": group.id if group else None,
            "group_name": group.group_name if group else None,
            "is_leader": membership.is_leader if membership else False,
            "joined_at": enrollment.created_at,
            "status": enrollment.status
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "students": student_list
    })


@router.post("/{course_uuid}/students", response_model=dict)
async def add_student_to_course(
    course_uuid: str,
    student_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加学生到课程"""
    # 获取课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查：只有本校管理员和任课教师可以添加学生
    if current_user.role == 'team_admin':
        if current_user.team_id != course.team_id:
            return error_response(message="无权操作该课程", code=403)
    elif current_user.role == 'teacher':
        is_teacher = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        if not is_teacher:
            return error_response(message="无权操作该课程", code=403)
    elif not is_admin_user(current_user):
        return error_response(message="无权操作该课程", code=403)
    
    student_id = student_data.get('student_id')
    if not student_id:
        return error_response(message="student_id是必填项", code=400)
    
    # 检查学生是否存在
    student = db.query(User).filter(
        User.id == student_id,
        User.role == 'student',
        User.deleted_at.is_(None)
    ).first()
    
    if not student:
        return error_response(message="学生不存在", code=404)
    
    # 检查学生是否属于本校
    if student.team_id != course.team_id:
        return error_response(message="只能添加本校学生", code=403)
    
    # 检查是否已经在课程中
    existing = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == student_id,
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if existing:
        return error_response(message="学生已在该课程中", code=400)
    
    # 检查课程人数限制
    current_count = db.query(func.count(CourseStudent.id)).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.deleted_at.is_(None)
    ).scalar() or 0
    
    if current_count >= course.max_students:
        return error_response(message=f"课程学生人数已达上限({course.max_students}人)", code=400)
    
    # 添加学生
    enrollment = CourseStudent(
        course_id=course.id,
        student_id=student_id,
        status='enrolled'
    )
    
    db.add(enrollment)
    db.commit()
    
    return success_response(message="学生添加成功")


@router.delete("/{course_uuid}/students/{student_id}", response_model=dict)
async def remove_student_from_course(
    course_uuid: str,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从课程中移除学生"""
    # 获取课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin':
        if current_user.team_id != course.team_id:
            return error_response(message="无权操作该课程", code=403)
    elif current_user.role == 'teacher':
        is_teacher = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        if not is_teacher:
            return error_response(message="无权操作该课程", code=403)
    elif not is_admin_user(current_user):
        return error_response(message="无权操作该课程", code=403)
    
    # 查找选课记录
    enrollment = db.query(CourseStudent).filter(
        CourseStudent.course_id == course.id,
        CourseStudent.student_id == student_id,
        CourseStudent.deleted_at.is_(None)
    ).first()
    
    if not enrollment:
        return error_response(message="学生不在该课程中", code=404)
    
    # 软删除选课记录
    enrollment.deleted_at = get_beijing_time_naive()
    
    # 同时软删除该学生在该课程中的分组关系
    group_memberships = db.query(GroupMember).filter(
        GroupMember.student_id == student_id,
        GroupMember.course_id == course.id,
        GroupMember.deleted_at.is_(None)
    ).all()
    
    for membership in group_memberships:
        membership.deleted_at = get_beijing_time_naive()
    
    db.commit()
    
    return success_response(message="学生已移除")


@router.get("/{course_uuid}/students/template")
async def download_course_student_template(
    course_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载课程学生导入模板"""
    # 获取课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    # 权限检查
    if current_user.role == 'team_admin':
        if current_user.team_id != course.team_id:
            raise HTTPException(status_code=403, detail="无权操作该课程")
    elif current_user.role == 'teacher':
        is_teacher = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        if not is_teacher:
            raise HTTPException(status_code=403, detail="无权操作该课程")
    elif not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="无权操作该课程")
    
    # 生成Excel模板
    columns = ['学号', '姓名', '性别']
    example_data = [
        ['2025001', '张三', '男'],
        ['2025002', '李四', '女']
    ]
    
    excel_file = generate_excel_template(
        columns=columns,
        example_data=example_data,
        sheet_name='学生信息'
    )
    
    # 返回文件下载
    return StreamingResponse(
        BytesIO(excel_file),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=course_students_template_{course_uuid}.xlsx'
        }
    )


@router.post("/{course_uuid}/students/batch-import", response_model=dict)
async def batch_import_course_students(
    course_uuid: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量导入学生到课程"""
    # 获取课程
    course = db.query(Course).filter(
        Course.uuid == course_uuid,
        Course.deleted_at.is_(None)
    ).first()
    
    if not course:
        return error_response(message="课程不存在", code=404)
    
    # 权限检查
    if current_user.role == 'team_admin':
        if current_user.team_id != course.team_id:
            return error_response(message="无权操作该课程", code=403)
    elif current_user.role == 'teacher':
        is_teacher = db.query(CourseTeacher).filter(
            CourseTeacher.course_id == course.id,
            CourseTeacher.teacher_id == current_user.id,
            CourseTeacher.deleted_at.is_(None)
        ).first()
        if not is_teacher:
            return error_response(message="无权操作该课程", code=403)
    elif not is_admin_user(current_user):
        return error_response(message="无权操作该课程", code=403)
    
    # 检查文件格式
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error_response(message="只支持Excel文件", code=400)
    
    try:
        # 读取Excel文件
        contents = await file.read()
        rows = read_excel_file(contents)
        
        if not rows:
            return error_response(message="文件内容为空", code=400)
        
        # 验证表头
        expected_columns = ['学号', '姓名', '性别']
        if len(rows) < 2 or rows[0] != expected_columns:
            return error_response(
                message=f"Excel表头不正确，应为: {', '.join(expected_columns)}", 
                code=400
            )
        
        # 处理数据行
        success_count = 0
        failed_count = 0
        error_details = []
        
        # 使用事务处理
        try:
            for idx, row in enumerate(rows[1:], start=2):  # 跳过表头
                try:
                    if len(row) < 3:
                        error_details.append(f"第{idx}行: 数据列数不足")
                        failed_count += 1
                        continue
                    
                    student_number = str(row[0]).strip()
                    name = str(row[1]).strip()
                    gender_str = str(row[2]).strip()
                    
                    # 验证必填字段
                    if not student_number or not name:
                        error_details.append(f"第{idx}行: 学号和姓名不能为空")
                        failed_count += 1
                        continue
                    
                    # 性别转换
                    gender_map = {'男': 'male', '女': 'female', '其他': 'other'}
                    gender = gender_map.get(gender_str)
                    if not gender:
                        error_details.append(f"第{idx}行: 性别只能是'男'、'女'或'其他'")
                        failed_count += 1
                        continue
                    
                    # 查找学生（通过学号）
                    student = db.query(User).filter(
                        User.student_number == student_number,
                        User.role == 'student',
                        User.team_id == course.team_id,
                        User.deleted_at.is_(None)
                    ).first()
                    
                    if not student:
                        error_details.append(f"第{idx}行: 学号'{student_number}'的学生不存在或不属于本校")
                        failed_count += 1
                        continue
                    
                    # 检查是否已在课程中
                    existing = db.query(CourseStudent).filter(
                        CourseStudent.course_id == course.id,
                        CourseStudent.student_id == student.id,
                        CourseStudent.deleted_at.is_(None)
                    ).first()
                    
                    if existing:
                        error_details.append(f"第{idx}行: 学生'{name}'已在该课程中")
                        failed_count += 1
                        continue
                    
                    # 检查课程人数限制
                    current_count = db.query(func.count(CourseStudent.id)).filter(
                        CourseStudent.course_id == course.id,
                        CourseStudent.deleted_at.is_(None)
                    ).scalar() or 0
                    
                    if current_count >= course.max_students:
                        error_details.append(f"第{idx}行: 课程学生人数已达上限({course.max_students}人)")
                        failed_count += 1
                        continue
                    
                    # 创建选课记录
                    enrollment = CourseStudent(
                        course_id=course.id,
                        student_id=student.id,
                        status='enrolled'
                    )
                    db.add(enrollment)
                    success_count += 1
                    
                except Exception as row_error:
                    error_details.append(f"第{idx}行: {str(row_error)}")
                    failed_count += 1
                    continue
            
            # 如果有任何失败，全部回滚
            if failed_count > 0:
                db.rollback()
                return error_response(
                    message=f"导入失败，共{len(rows)-1}条记录，失败{failed_count}条",
                    code=400,
                    data={
                        "total": len(rows) - 1,
                        "success": 0,
                        "failed": failed_count,
                        "errors": error_details[:10]  # 只返回前10条错误
                    }
                )
            
            # 全部成功，提交事务
            db.commit()
            
            return success_response(
                data={
                    "total": len(rows) - 1,
                    "success": success_count,
                    "failed": failed_count
                },
                message=f"批量导入成功，共{success_count}条记录"
            )
            
        except Exception as e:
            db.rollback()
            return error_response(message=f"导入失败: {str(e)}", code=500)
            
    except Exception as e:
        return error_response(message=f"文件处理失败: {str(e)}", code=500)


