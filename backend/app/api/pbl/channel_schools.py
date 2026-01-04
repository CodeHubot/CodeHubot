from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Tuple

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_channel_partner
from ...core.logging_config import get_logger
from ...models.admin import Admin, User
from ...models.pbl import (
    PBLCourse, PBLClass, PBLClassMember, PBLClassTeacher,
    PBLGroup, PBLGroupMember, PBLUnit, PBLTask, PBLTaskProgress,
    ChannelSchoolRelation
)
from ...models.school import School
from ...utils.timezone import get_beijing_time_naive

router = APIRouter()
logger = get_logger(__name__)

# ===== 辅助函数 =====

def verify_channel_school_permission(
    school_id: int,
    channel_partner_id: int,
    db: Session
) -> Tuple[School, ChannelSchoolRelation]:
    """
    验证渠道商是否有权限访问该学校
    
    Args:
        school_id: 学校ID
        channel_partner_id: 渠道商ID
        db: 数据库会话
    
    Returns:
        (学校对象, 渠道商学校关联对象)
    
    Raises:
        HTTPException: 权限验证失败时抛出
    """
    # 查询学校
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学校不存在"
        )
    
    # 验证渠道商是否负责该学校
    relation = db.query(ChannelSchoolRelation).filter(
        ChannelSchoolRelation.channel_partner_id == channel_partner_id,
        ChannelSchoolRelation.school_id == school_id,
        ChannelSchoolRelation.is_active == 1
    ).first()
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    return school, relation

# ===== 学校管理 =====

@router.get("/schools")
def get_channel_schools(
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取渠道商负责的所有学校列表"""
    
    # 查询渠道商负责的学校关联
    relations = db.query(ChannelSchoolRelation).filter(
        ChannelSchoolRelation.channel_partner_id == current_channel.id,
        ChannelSchoolRelation.is_active == 1
    ).all()
    
    if not relations:
        return success_response(data=[], message="暂无负责的学校")
    
    school_ids = [rel.school_id for rel in relations]
    
    # 查询学校详情
    schools = db.query(School).filter(
        School.id.in_(school_ids)
    ).all()
    
    result = []
    for school in schools:
        # 统计班级数量
        class_count = db.query(func.count(PBLClass.id)).filter(
            PBLClass.school_id == school.id
        ).scalar()
        
        # 统计课程数量（通过班级关联）
        course_count = db.query(func.count(PBLCourse.id)).join(
            PBLClass, PBLCourse.class_id == PBLClass.id
        ).filter(
            PBLClass.school_id == school.id
        ).scalar()
        
        # 统计教师数量
        teacher_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role == 'teacher'
        ).scalar()
        
        # 统计学生数量
        student_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role == 'student'
        ).scalar()
        
        result.append({
            "id": school.id,
            "uuid": school.uuid,
            "school_code": school.school_code,
            "school_name": school.school_name,
            "province": school.province,
            "city": school.city,
            "district": school.district,
            "is_active": school.is_active,
            # 统计数据平铺到顶层，使用前端期望的字段名
            "total_courses": course_count,
            "total_students": student_count,
            "total_teachers": teacher_count,
            "class_count": class_count,
            "created_at": school.created_at.isoformat() if school.created_at else None
        })
    
    logger.info(f"渠道商 {current_channel.username} 共负责 {len(result)} 所学校")
    return success_response(data=result)

@router.get("/schools/{school_uuid}")
def get_school_detail(
    school_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取学校详细信息"""
    
    # 通过UUID查询学校
    school = db.query(School).filter(School.uuid == school_uuid).first()
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证权限
    try:
        school, relation = verify_channel_school_permission(school.id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 获取班级列表
    classes = db.query(PBLClass).filter(
        PBLClass.school_id == school.id
    ).all()
    
    class_list = []
    for pbl_class in classes:
        # 统计课程数量
        course_count = db.query(func.count(PBLCourse.id)).filter(
            PBLCourse.class_id == pbl_class.id
        ).scalar()
        
        class_list.append({
            "id": pbl_class.id,
            "uuid": pbl_class.uuid,
            "name": pbl_class.name,
            "class_type": pbl_class.class_type,
            "current_members": pbl_class.current_members,
            "course_count": course_count,
            "is_active": pbl_class.is_active
        })
    
    # 获取统计数据
    teacher_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'teacher'
    ).scalar()
    
    student_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'student'
    ).scalar()
    
    result = {
        "id": school.id,
        "uuid": school.uuid,
        "school_code": school.school_code,
        "school_name": school.school_name,
        "province": school.province,
        "city": school.city,
        "district": school.district,
        "address": school.address,
        "contact_person": school.contact_person,
        "contact_phone": school.contact_phone,
        "contact_email": school.contact_email,
        "is_active": school.is_active,
        "description": school.description,
        "classes": class_list,
        "statistics": {
            "class_count": len(class_list),
            "teacher_count": teacher_count,
            "student_count": student_count
        },
        "created_at": school.created_at.isoformat() if school.created_at else None
    }
    
    return success_response(data=result)

@router.get("/schools/{school_uuid}/courses")
def get_school_courses(
    school_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取学校的所有课程列表"""
    
    # 通过UUID查询学校
    school = db.query(School).filter(School.uuid == school_uuid).first()
    if not school:
        return error_response(
            message="学校不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证权限
    try:
        school, relation = verify_channel_school_permission(school.id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 查询学校的所有班级
    classes = db.query(PBLClass).filter(
        PBLClass.school_id == school.id
    ).all()
    
    if not classes:
        return success_response(data=[], message="该学校暂无班级")
    
    class_ids = [c.id for c in classes]
    
    # 查询这些班级的课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id.in_(class_ids)
    ).all()
    
    result = []
    for course in courses:
        # 获取班级信息
        pbl_class = next((c for c in classes if c.id == course.class_id), None)
        
        # 统计单元数量
        unit_count = db.query(func.count(PBLUnit.id)).filter(
            PBLUnit.course_id == course.id
        ).scalar()
        
        # 统计任务数量
        task_count = db.query(func.count(PBLTask.id)).join(
            PBLUnit, PBLTask.unit_id == PBLUnit.id
        ).filter(
            PBLUnit.course_id == course.id
        ).scalar()
        
        # 格式化日期
        start_date = course.start_date.isoformat() if course.start_date else None
        end_date = course.end_date.isoformat() if course.end_date else None
        
        result.append({
            "id": course.id,
            "uuid": course.uuid,
            "course_name": course.title,  # 前端期望的字段名
            "class_name": pbl_class.name if pbl_class else None,  # 平铺班级名称
            "teacher_name": course.teacher_name,  # 授课教师
            "student_count": pbl_class.current_members if pbl_class else 0,  # 学生数
            "start_date": start_date,  # 开始时间
            "end_date": end_date,  # 结束时间
            "status": course.status,  # 状态
            "difficulty": course.difficulty,
            "description": course.description,
            "cover_image": course.cover_image,
            "unit_count": unit_count,
            "task_count": task_count,
            "created_at": course.created_at.isoformat() if course.created_at else None
        })
    
    return success_response(data=result)

@router.get("/courses/{course_uuid}/student-submissions")
def get_course_student_submissions(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程学生作业提交统计（性能优化版 - SQL聚合查询）"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级信息
    pbl_class = None
    if course.class_id:
        pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    
    if not pbl_class:
        return error_response(
            message="课程未关联班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证渠道商是否负责该学校
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # ===== 性能优化：使用SQL聚合查询 =====
    
    # 1. 获取课程的所有单元（用于表头和排序）
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    if not units:
        return success_response(data={
            "course": {
                "id": course.id,
                "uuid": course.uuid,
                "title": course.title,
                "class_name": pbl_class.name,
                "school_name": school.school_name
            },
            "units": [],
            "students": []
        })
    
    unit_ids = [u.id for u in units]
    
    # 2. 获取班级的所有学生
    students = db.query(User).join(
        PBLClassMember, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).order_by(User.name).all()
    
    if not students:
        # 构建单元列表
        unit_list = []
        for unit in units:
            task_count = db.query(func.count(PBLTask.id)).filter(
                PBLTask.unit_id == unit.id
            ).scalar()
            unit_list.append({
                "id": unit.id,
                "uuid": unit.uuid,
                "title": unit.title,
                "order": unit.order,
                "task_count": task_count
            })
        
        return success_response(data={
            "course": {
                "id": course.id,
                "uuid": course.uuid,
                "title": course.title,
                "class_name": pbl_class.name,
                "school_name": school.school_name
            },
            "units": unit_list,
            "students": []
        })
    
    student_ids = [s.id for s in students]
    
    # 3. 使用SQL聚合查询统计每个单元的任务数
    from sqlalchemy import case
    
    unit_task_counts = db.query(
        PBLUnit.id.label('unit_id'),
        func.count(PBLTask.id).label('task_count')
    ).outerjoin(
        PBLTask, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.id.in_(unit_ids)
    ).group_by(
        PBLUnit.id
    ).all()
    
    # 建立单元任务数映射
    unit_task_map = {row.unit_id: row.task_count for row in unit_task_counts}
    
    # 4. 使用SQL聚合查询统计每个学生在每个单元的提交数（核心优化）
    submission_stats = db.query(
        User.id.label('student_id'),
        PBLUnit.id.label('unit_id'),
        func.count(
            case(
                (PBLTaskProgress.status.in_(['review', 'completed']), PBLTaskProgress.id),
                else_=None
            )
        ).label('submission_count')
    ).select_from(User).join(
        PBLClassMember, PBLClassMember.student_id == User.id
    ).outerjoin(
        PBLUnit, PBLUnit.course_id == course.id
    ).outerjoin(
        PBLTask, PBLTask.unit_id == PBLUnit.id
    ).outerjoin(
        PBLTaskProgress,
        (PBLTaskProgress.task_id == PBLTask.id) &
        (PBLTaskProgress.user_id == User.id)
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1,
        User.id.in_(student_ids),
        PBLUnit.id.in_(unit_ids)
    ).group_by(
        User.id, PBLUnit.id
    ).all()
    
    # 5. 建立内存索引：(学生ID, 单元ID) -> 提交数
    submission_map = {
        (row.student_id, row.unit_id): row.submission_count 
        for row in submission_stats
    }
    
    # 6. 构建单元列表（用于前端表头）
    unit_list = []
    for unit in units:
        unit_list.append({
            "id": unit.id,
            "uuid": unit.uuid,
            "title": unit.title,
            "order": unit.order,
            "task_count": unit_task_map.get(unit.id, 0)
        })
    
    # 7. 构建学生提交统计列表（从内存索引中快速查找）
    student_submissions = []
    for student in students:
        unit_submissions = []
        total_submissions = 0
        total_tasks = 0
        
        for unit in units:
            task_count = unit_task_map.get(unit.id, 0)
            submission_count = submission_map.get((student.id, unit.id), 0)
            
            unit_submissions.append({
                "unit_id": unit.id,
                "unit_title": unit.title,
                "submission_count": submission_count,
                "task_count": task_count
            })
            
            total_submissions += submission_count
            total_tasks += task_count
        
        student_submissions.append({
            "student_id": student.id,
            "student_uuid": student.uuid,
            "student_name": student.name or student.real_name,
            "student_number": student.student_number,
            "unit_submissions": unit_submissions,
            "total_submissions": total_submissions,
            "total_tasks": total_tasks
        })
    
    result = {
        "course": {
            "id": course.id,
            "uuid": course.uuid,
            "title": course.title,
            "class_name": pbl_class.name,
            "school_name": school.school_name
        },
        "units": unit_list,
        "students": student_submissions
    }
    
    logger.info(f"渠道商 {current_channel.username} 查询课程 {course.title} 的学生提交统计，"
                f"共 {len(students)} 名学生，{len(units)} 个单元")
    
    return success_response(data=result)


@router.get("/courses/{course_uuid}")
def get_course_detail(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程详细信息（只读）"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级信息
    pbl_class = None
    if course.class_id:
        pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    
    if not pbl_class:
        return error_response(
            message="课程未关联班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证渠道商是否负责该学校
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 获取班级成员
    member_count = db.query(func.count(PBLClassMember.id)).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).scalar()
    
    # 获取小组信息
    group_count = db.query(func.count(PBLGroup.id)).filter(
        PBLGroup.class_id == pbl_class.id,
        PBLGroup.is_active == 1
    ).scalar()
    
    # 获取教师信息
    teachers = db.query(PBLClassTeacher, User).join(
        User, PBLClassTeacher.teacher_id == User.id
    ).filter(
        PBLClassTeacher.class_id == pbl_class.id
    ).all()
    
    teacher_list = []
    for teacher_rel, user in teachers:
        teacher_list.append({
            "id": user.id,
            "name": user.name or user.real_name,
            "teacher_number": user.teacher_number,
            "role": teacher_rel.role,
            "subject": teacher_rel.subject,
            "is_primary": teacher_rel.is_primary
        })
    
    # 获取单元列表
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    unit_list = []
    for unit in units:
        # 统计任务数量
        task_count = db.query(func.count(PBLTask.id)).filter(
            PBLTask.unit_id == unit.id
        ).scalar()
        
        unit_list.append({
            "id": unit.id,
            "uuid": unit.uuid,
            "title": unit.title,
            "description": unit.description,
            "order": unit.order,
            "status": unit.status,
            "task_count": task_count
        })
    
    result = {
        "id": course.id,
        "uuid": course.uuid,
        "title": course.title,
        "description": course.description,
        "cover_image": course.cover_image,
        "difficulty": course.difficulty,
        "status": course.status,
        "duration": course.duration,
        "start_date": course.start_date.isoformat() if course.start_date else None,
        "end_date": course.end_date.isoformat() if course.end_date else None,
        "school_name": school.school_name,
        "class_name": pbl_class.name,
        "teacher_name": course.teacher_name,
        "student_count": member_count,
        "class": {
            "id": pbl_class.id,
            "uuid": pbl_class.uuid,
            "name": pbl_class.name,
            "class_type": pbl_class.class_type,
            "current_members": pbl_class.current_members,
            "member_count": member_count,
            "group_count": group_count
        },
        "teachers": teacher_list,
        "units": unit_list,
        "created_at": course.created_at.isoformat() if course.created_at else None
    }
    
    return success_response(data=result)


@router.get("/courses/{course_uuid}/submission-statistics")
def get_course_submission_statistics(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程作业提交统计（学生×单元）"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级信息
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    if not pbl_class:
        return error_response(
            message="课程未关联班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证渠道商权限
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 获取所有单元（按顺序）
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    # 获取班级所有学生
    members = db.query(PBLClassMember, User).join(
        User, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    # 构建学生列表
    students = []
    for member, user in members:
        students.append({
            "id": user.id,
            "uuid": user.uuid if hasattr(user, 'uuid') else None,
            "name": user.real_name or user.name or user.username,
            "student_number": user.student_number
        })
    
    # 构建单元列表
    unit_list = []
    for unit in units:
        unit_list.append({
            "id": unit.id,
            "uuid": unit.uuid,
            "title": unit.title,
            "order": unit.order
        })
    
    # 统计每个学生在每个单元的作业提交数
    submission_stats = []
    for student in students:
        student_stat = {
            "student_id": student["id"],
            "student_name": student["name"],
            "student_number": student["student_number"],
            "unit_submissions": {}
        }
        
        for unit in unit_list:
            # 获取该单元的所有任务
            tasks = db.query(PBLTask).filter(
                PBLTask.unit_id == unit["id"]
            ).all()
            
            if not tasks:
                student_stat["unit_submissions"][str(unit["id"])] = 0
                continue
            
            # 统计该学生在这个单元已提交的任务数
            task_ids = [t.id for t in tasks]
            submitted_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id.in_(task_ids),
                PBLTaskProgress.user_id == student["id"],
                PBLTaskProgress.submitted_at.isnot(None)
            ).scalar()
            
            student_stat["unit_submissions"][str(unit["id"])] = submitted_count
        
        submission_stats.append(student_stat)
    
    result = {
        "course_name": course.title,
        "class_name": pbl_class.name,
        "units": unit_list,
        "students": submission_stats
    }
    
    return success_response(data=result)

@router.get("/courses/{course_uuid}/progress")
def get_course_progress(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程学习进度统计（只读）"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(message="课程不存在", code=404, status_code=status.HTTP_404_NOT_FOUND)
    
    # 获取班级信息
    if not course.class_id:
        return error_response(message="课程未关联班级", code=400, status_code=status.HTTP_400_BAD_REQUEST)
    
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    if not pbl_class:
        return error_response(message="班级不存在", code=404, status_code=status.HTTP_404_NOT_FOUND)
    
    # 验证权限
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 获取班级成员
    students = db.query(User).join(
        PBLClassMember, User.id == PBLClassMember.student_id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).all()
    
    # 获取所有单元
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    # 统计每个学生的进度
    student_progress = []
    for student in students:
        completed_units = 0
        total_tasks = 0
        completed_tasks = 0
        
        for unit in units:
            unit_tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
            total_tasks += len(unit_tasks)
            
            for task in unit_tasks:
                progress = db.query(PBLTaskProgress).filter(
                    PBLTaskProgress.task_id == task.id,
                    PBLTaskProgress.user_id == student.id,
                    PBLTaskProgress.status == 'completed'
                ).first()
                
                if progress:
                    completed_tasks += 1
            
            # 判断单元是否完成
            if len(unit_tasks) > 0:
                unit_completed = db.query(func.count(PBLTaskProgress.id)).filter(
                    PBLTaskProgress.task_id.in_([t.id for t in unit_tasks]),
                    PBLTaskProgress.user_id == student.id,
                    PBLTaskProgress.status == 'completed'
                ).scalar()
                
                if unit_completed == len(unit_tasks):
                    completed_units += 1
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        student_progress.append({
            "student_id": student.id,
            "student_name": student.name or student.real_name,
            "student_number": student.student_number,
            "completed_units": completed_units,
            "total_units": len(units),
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "progress_percentage": round(progress_percentage, 2)
        })
    
    # 整体统计
    overall_stats = {
        "total_students": len(students),
        "total_units": len(units),
        "average_progress": round(sum([s['progress_percentage'] for s in student_progress]) / len(student_progress), 2) if student_progress else 0
    }
    
    return success_response(data={
        "overall": overall_stats,
        "students": student_progress
    })

@router.get("/courses/{course_uuid}/homework")
def get_course_homework(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程作业统计（只读）"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(message="课程不存在", code=404, status_code=status.HTTP_404_NOT_FOUND)
    
    # 获取班级信息
    if not course.class_id:
        return error_response(message="课程未关联班级", code=400, status_code=status.HTTP_400_BAD_REQUEST)
    
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    if not pbl_class:
        return error_response(message="班级不存在", code=404, status_code=status.HTTP_404_NOT_FOUND)
    
    # 验证权限
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 查询任务
    tasks = db.query(PBLTask, PBLUnit).join(
        PBLUnit, PBLTask.unit_id == PBLUnit.id
    ).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order, PBLTask.order).all()
    
    result = []
    for task, unit in tasks:
        # 统计提交情况
        total_submissions = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.status.in_(['review', 'completed'])
        ).scalar()
        
        pending_review = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.status == 'review'
        ).scalar()
        
        graded = db.query(func.count(PBLTaskProgress.id)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.status == 'completed',
            PBLTaskProgress.score.isnot(None)
        ).scalar()
        
        # 平均分数
        avg_score = db.query(func.avg(PBLTaskProgress.score)).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.score.isnot(None)
        ).scalar()
        
        result.append({
            "task_id": task.id,
            "task_uuid": task.uuid,
            "task_title": task.title,
            "task_type": task.type,
            "difficulty": task.difficulty,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "unit_title": unit.title,
            "statistics": {
                "total_submissions": total_submissions,
                "pending_review": pending_review,
                "graded": graded,
                "average_score": round(float(avg_score), 2) if avg_score else None
            }
        })
    
    return success_response(data=result)

@router.get("/courses/{course_uuid}/student-unit-submissions")
def get_student_unit_submissions(
    course_uuid: str,
    current_channel: Admin = Depends(get_current_channel_partner),
    db: Session = Depends(get_db)
):
    """获取课程中每个学生每个单元的作业提交统计"""
    
    # 查询课程
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取班级信息
    if not course.class_id:
        return error_response(
            message="课程未关联班级",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    pbl_class = db.query(PBLClass).filter(PBLClass.id == course.class_id).first()
    if not pbl_class:
        return error_response(
            message="班级不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证渠道商权限
    try:
        school, relation = verify_channel_school_permission(pbl_class.school_id, current_channel.id, db)
    except HTTPException as e:
        return error_response(message=e.detail, code=e.status_code, status_code=e.status_code)
    
    # 获取班级所有学生
    students = db.query(User).join(
        PBLClassMember, PBLClassMember.student_id == User.id
    ).filter(
        PBLClassMember.class_id == pbl_class.id,
        PBLClassMember.is_active == 1
    ).order_by(User.name).all()
    
    # 获取课程所有单元（按顺序）
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course.id
    ).order_by(PBLUnit.order).all()
    
    # 构建单元列表（用于表头）
    unit_list = []
    for unit in units:
        unit_list.append({
            "id": unit.id,
            "uuid": unit.uuid,
            "title": unit.title,
            "order": unit.order
        })
    
    # 构建学生-单元作业提交统计
    student_list = []
    for student in students:
        student_data = {
            "student_id": student.id,
            "student_name": student.name or student.real_name,
            "student_number": student.student_number,
            "submissions": []  # 每个单元的提交统计
        }
        
        # 统计每个单元的作业提交情况
        for unit in units:
            # 获取该单元的所有任务
            tasks = db.query(PBLTask).filter(
                PBLTask.unit_id == unit.id
            ).all()
            
            task_ids = [task.id for task in tasks]
            
            # 统计该学生在该单元提交的作业数量
            submitted_count = db.query(func.count(PBLTaskProgress.id)).filter(
                PBLTaskProgress.task_id.in_(task_ids),
                PBLTaskProgress.user_id == student.id,
                PBLTaskProgress.submitted_at.isnot(None)  # 已提交
            ).scalar() if task_ids else 0
            
            # 该单元的总任务数
            total_tasks = len(tasks)
            
            student_data["submissions"].append({
                "unit_id": unit.id,
                "unit_uuid": unit.uuid,
                "submitted_count": submitted_count,
                "total_tasks": total_tasks
            })
        
        student_list.append(student_data)
    
    result = {
        "course_name": course.title,
        "class_name": pbl_class.name,
        "units": unit_list,
        "students": student_list
    }
    
    return success_response(data=result)
