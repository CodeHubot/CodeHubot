from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.utils.timezone import get_beijing_time_naive

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_user, get_current_admin
from ...models.admin import User, Admin
from ...models.pbl import PBLCourse, PBLUnit, PBLResource, PBLTask, PBLTaskProgress, PBLLearningProgress, PBLClassMember
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/my-progress")
def get_my_learning_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的学习进度概览"""
    # 查询当前用户所在的所有活跃班级
    class_members = db.query(PBLClassMember).filter(
        PBLClassMember.student_id == current_user.id,
        PBLClassMember.is_active == 1
    ).all()
    
    if not class_members:
        return success_response(data=[])
    
    # 获取所有班级ID
    class_ids = [cm.class_id for cm in class_members]
    
    # 查询这些班级的所有已发布课程
    courses = db.query(PBLCourse).filter(
        PBLCourse.class_id.in_(class_ids),
        PBLCourse.status == 'published'
    ).all()
    
    result = []
    for course in courses:
        # 统计单元完成情况
        units = db.query(PBLUnit).filter(PBLUnit.course_id == course.id).all()
        total_units = len(units)
        
        # 统计任务完成情况
        tasks_query = db.query(PBLTask).join(
            PBLUnit, PBLUnit.id == PBLTask.unit_id
        ).filter(
            PBLUnit.course_id == course.id
        )
        total_tasks = tasks_query.count()
        
        # 统计已完成的任务
        completed_tasks = db.query(PBLTaskProgress).join(
            PBLTask, PBLTask.id == PBLTaskProgress.task_id
        ).join(
            PBLUnit, PBLUnit.id == PBLTask.unit_id
        ).filter(
            PBLUnit.course_id == course.id,
            PBLTaskProgress.user_id == current_user.id,
            PBLTaskProgress.submission.isnot(None)  # 只要提交了就算完成
        ).count()
        
        # 计算进度
        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)
        else:
            progress = 0
        
        result.append({
            'course_id': course.id,
            'course_uuid': course.uuid,
            'course_title': course.title,
            'course_cover': course.cover_image,
            'difficulty': course.difficulty,
            'total_units': total_units,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress': progress,
            'status': 'in-progress' if progress > 0 and progress < 100 else ('completed' if progress == 100 else 'not-started')
        })
    
    return success_response(data=result)

@router.get("/course/{course_id}/progress")
def get_course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定课程的详细进度"""
    course = db.query(PBLCourse).filter(PBLCourse.id == course_id).first()
    
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取所有单元
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course_id
    ).order_by(PBLUnit.order).all()
    
    units_progress = []
    for unit in units:
        # 获取单元下的所有任务
        tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
        total_tasks = len(tasks)
        
        # 获取已完成的任务
        completed_tasks = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == current_user.id,
            PBLTaskProgress.task_id.in_([t.id for t in tasks]),
            PBLTaskProgress.submission.isnot(None)  # 只要提交了就算完成
        ).count()
        
        # 获取单元下的资源数
        resources_count = db.query(PBLResource).filter(
            PBLResource.unit_id == unit.id
        ).count()
        
        # 计算单元进度
        if total_tasks > 0:
            unit_progress = int((completed_tasks / total_tasks) * 100)
        else:
            unit_progress = 0
        
        units_progress.append({
            'unit_id': unit.id,
            'unit_uuid': unit.uuid,
            'unit_title': unit.title,
            'unit_order': unit.order,
            'unit_status': unit.status,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'resources_count': resources_count,
            'progress': unit_progress
        })
    
    return success_response(data={
        'course_id': course.id,
        'course_title': course.title,
        'units': units_progress
    })

@router.get("/unit/{unit_id}/progress")
def get_unit_progress(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定单元的详细进度"""
    unit = db.query(PBLUnit).filter(PBLUnit.id == unit_id).first()
    
    if not unit:
        return error_response(
            message="单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取单元下的所有任务及其进度
    tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit_id).all()
    
    tasks_progress = []
    for task in tasks:
        # 获取任务进度
        progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.task_id == task.id,
            PBLTaskProgress.user_id == current_user.id
        ).first()
        
        tasks_progress.append({
            'task_id': task.id,
            'task_uuid': task.uuid,
            'task_title': task.title,
            'task_type': task.type,
            'task_difficulty': task.difficulty,
            'estimated_time': task.estimated_time,
            'status': progress.status if progress else 'pending',
            'progress': progress.progress if progress else 0,
            'score': progress.score if progress else None,
            'submitted_at': progress.updated_at.isoformat() if progress and progress.status == 'review' else None,
            'graded_at': progress.graded_at.isoformat() if progress and progress.graded_at else None
        })
    
    # 获取单元下的资源
    resources = db.query(PBLResource).filter(
        PBLResource.unit_id == unit_id
    ).order_by(PBLResource.order).all()
    
    resources_list = [{
        'resource_id': r.id,
        'resource_uuid': r.uuid,
        'resource_title': r.title,
        'resource_type': r.type,
        'duration': r.duration,
        'order': r.order
    } for r in resources]
    
    return success_response(data={
        'unit_id': unit.id,
        'unit_title': unit.title,
        'tasks': tasks_progress,
        'resources': resources_list
    })

@router.get("/unit/{unit_uuid}/resources-progress")
def get_unit_resources_progress(
    unit_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单元内所有资源和任务的完成状态"""
    # 根据UUID查询单元
    unit = db.query(PBLUnit).filter(PBLUnit.uuid == unit_uuid).first()
    if not unit:
        return error_response(
            message="单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取该单元下所有资源的最新进度
    resources = db.query(PBLResource).filter(PBLResource.unit_id == unit.id).all()
    resource_progress = {}
    
    for resource in resources:
        # 获取该资源的最新进度记录
        latest_progress = db.query(PBLLearningProgress).filter(
            PBLLearningProgress.user_id == current_user.id,
            PBLLearningProgress.resource_id == resource.id
        ).order_by(PBLLearningProgress.created_at.desc()).first()
        
        if latest_progress:
            resource_progress[f"resource-{resource.id}"] = {
                'status': latest_progress.status,
                'progress_value': latest_progress.progress_value,
                'completed_at': latest_progress.completed_at.isoformat() if latest_progress.completed_at else None,
                'time_spent': latest_progress.time_spent
            }
    
    # 获取该单元下所有任务的最新进度
    tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
    task_progress = {}
    
    for task in tasks:
        # 从 PBLTaskProgress 表获取任务进度（包含提交内容）
        task_prog = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == current_user.id,
            PBLTaskProgress.task_id == task.id
        ).first()
        
        if task_prog:
            task_progress[f"task-{task.id}"] = {
                'id': task_prog.id,  # ✅ 添加 progress_id，用于加载附件列表
                'status': task_prog.status,
                'progress_value': task_prog.progress,
                'completed_at': task_prog.updated_at.isoformat() if task_prog.updated_at else None,
                'time_spent': 0,  # PBLTaskProgress 表没有 time_spent 字段
                'submission': task_prog.submission,  # 添加提交内容
                'score': task_prog.score,  # 添加分数
                'feedback': task_prog.feedback  # 添加反馈
            }
        else:
            # 如果 PBLTaskProgress 中没有记录，尝试从 PBLLearningProgress 中获取
            latest_progress = db.query(PBLLearningProgress).filter(
                PBLLearningProgress.user_id == current_user.id,
                PBLLearningProgress.task_id == task.id
            ).order_by(PBLLearningProgress.created_at.desc()).first()
            
            if latest_progress:
                task_progress[f"task-{task.id}"] = {
                    'status': latest_progress.status,
                    'progress_value': latest_progress.progress_value,
                    'completed_at': latest_progress.completed_at.isoformat() if latest_progress.completed_at else None,
                    'time_spent': latest_progress.time_spent,
                    'submission': None,  # PBLLearningProgress 表没有 submission 字段
                    'score': None,
                    'feedback': None
                }
    
    return success_response(data={
        'unit_id': unit.id,
        'unit_uuid': unit.uuid,
        'resource_progress': resource_progress,
        'task_progress': task_progress
    })

@router.post("/track")
def track_learning_activity(
    track_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录学习行为（使用UUID）"""
    # 验证课程是否存在
    course_uuid = track_data.get('course_uuid')
    if not course_uuid:
        return error_response(
            message="缺少课程UUID",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    course = db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 根据UUID查找对应的ID
    unit_id = None
    unit_uuid = track_data.get('unit_uuid')
    if unit_uuid:
        unit = db.query(PBLUnit).filter(PBLUnit.uuid == unit_uuid).first()
        if unit:
            unit_id = unit.id
    
    resource_id = None
    resource_uuid = track_data.get('resource_uuid')
    if resource_uuid:
        resource = db.query(PBLResource).filter(PBLResource.uuid == resource_uuid).first()
        if resource:
            resource_id = resource.id
    
    task_id = None
    task_uuid = track_data.get('task_uuid')
    if task_uuid:
        task = db.query(PBLTask).filter(PBLTask.uuid == task_uuid).first()
        if task:
            task_id = task.id
    
    # 获取其他参数
    progress_type = track_data.get('progress_type', 'resource_view')
    progress_value = track_data.get('progress_value', 0)
    time_spent = track_data.get('time_spent', 0)
    metadata = track_data.get('metadata')
    
    # 判断完成状态
    is_completed = progress_value >= 100
    completed_at = get_beijing_time_naive() if is_completed else None
    
    # 插入学习进度记录
    learning_progress = PBLLearningProgress(
        user_id=current_user.id,
        course_id=course.id,
        unit_id=unit_id,
        resource_id=resource_id,
        task_id=task_id,
        progress_type=progress_type,
        progress_value=progress_value,
        status='completed' if is_completed else 'in_progress',
        completed_at=completed_at,
        time_spent=time_spent,
        meta_data=metadata
    )
    db.add(learning_progress)
    db.commit()
    
    logger.debug(f"学习行为追踪 - 用户: {current_user.id}, 课程: {course_uuid}, 类型: {progress_type}")
    
    return success_response(
        data={
            'tracked': True,
            'user_id': current_user.id,
            'course_uuid': course_uuid,
            'unit_uuid': unit_uuid,
            'resource_uuid': resource_uuid,
            'task_uuid': task_uuid,
            'progress_type': progress_type,
            'progress_value': progress_value,
            'status': 'completed' if is_completed else 'in_progress',
            'time_spent': time_spent
        },
        message="学习行为记录成功"
    )

@router.delete("/reset-progress")
def reset_learning_progress(
    resource_uuid: Optional[str] = None,
    task_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置学习进度（将资源或任务标记为未完成）"""
    try:
        # 根据UUID查找对应的ID
        if resource_uuid:
            resource = db.query(PBLResource).filter(PBLResource.uuid == resource_uuid).first()
            if not resource:
                return error_response(
                    message="资源不存在",
                    code=404,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # 删除该资源的所有学习进度记录
            db.query(PBLLearningProgress).filter(
                PBLLearningProgress.user_id == current_user.id,
                PBLLearningProgress.resource_id == resource.id
            ).delete()
            
            logger.debug(f"重置资源进度 - 用户: {current_user.id}, 资源: {resource_uuid}")
        
        if task_uuid:
            task = db.query(PBLTask).filter(PBLTask.uuid == task_uuid).first()
            if not task:
                return error_response(
                    message="任务不存在",
                    code=404,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # 删除该任务的所有学习进度记录
            db.query(PBLLearningProgress).filter(
                PBLLearningProgress.user_id == current_user.id,
                PBLLearningProgress.task_id == task.id
            ).delete()
            
            logger.debug(f"重置任务进度 - 用户: {current_user.id}, 任务: {task_uuid}")
        
        db.commit()
        
        return success_response(
            data={'reset': True},
            message="学习进度已重置"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"重置学习进度失败: {str(e)}")
        return error_response(
            message="重置失败",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ===== 管理员端：查看学生进度 =====

@router.get("/course/{course_id}/students")
def get_course_students_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """查看课程下所有学生的进度（管理员）"""
    course = db.query(PBLCourse).filter(PBLCourse.id == course_id).first()
    
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if course.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该课程",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 如果课程没有关联班级，返回空列表
    if not course.class_id:
        return success_response(data={'students': []})
    
    # 查询班级的所有活跃成员
    class_members = db.query(PBLClassMember).filter(
        PBLClassMember.class_id == course.class_id,
        PBLClassMember.is_active == 1
    ).all()
    
    if not class_members:
        return success_response(data={'students': []})
    
    student_ids = [cm.student_id for cm in class_members]
    students = db.query(User).filter(
        User.id.in_(student_ids),
        User.role == 'student',
        User.deleted_at == None
    ).all()
    
    # 获取课程的单元和任务
    units = db.query(PBLUnit).filter(PBLUnit.course_id == course_id).all()
    total_units = len(units)
    
    tasks = db.query(PBLTask).join(
        PBLUnit, PBLUnit.id == PBLTask.unit_id
    ).filter(
        PBLUnit.course_id == course_id
    ).all()
    total_tasks = len(tasks)
    task_ids = [t.id for t in tasks]
    
    result = []
    for student in students:
        # 统计任务完成情况
        completed_tasks = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == student.id,
            PBLTaskProgress.task_id.in_(task_ids),
            PBLTaskProgress.submission.isnot(None)  # 只要提交了就算完成
        ).count() if task_ids else 0
        
        # 计算平均分
        avg_score = db.query(func.avg(PBLTaskProgress.score)).filter(
            PBLTaskProgress.user_id == student.id,
            PBLTaskProgress.task_id.in_(task_ids),
            PBLTaskProgress.score != None
        ).scalar() if task_ids else None
        
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        # 统计完成的单元数
        completed_units = 0
        for unit in units:
            unit_tasks = [t.id for t in tasks if t.unit_id == unit.id]
            if unit_tasks:
                unit_completed = db.query(PBLTaskProgress).filter(
                    PBLTaskProgress.user_id == student.id,
                    PBLTaskProgress.task_id.in_(unit_tasks),
                    PBLTaskProgress.submission.isnot(None)  # 只要提交了就算完成
                ).count()
                if unit_completed == len(unit_tasks):
                    completed_units += 1
        
        # 获取最后活跃时间
        last_progress = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == student.id,
            PBLTaskProgress.task_id.in_(task_ids)
        ).order_by(PBLTaskProgress.updated_at.desc()).first() if task_ids else None
        
        result.append({
            'student_id': student.id,
            'student_name': student.name or student.real_name,
            'student_number': student.student_number,
            'class_id': student.class_id,
            'total_units': total_units,
            'completed_units': completed_units,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress': progress,
            'average_score': round(float(avg_score), 2) if avg_score else None,
            'last_active_at': last_progress.updated_at.isoformat() if last_progress and last_progress.updated_at else None
        })
    
    return success_response(data={'students': result})

@router.get("/student/{student_id}/course/{course_id}")
def get_student_detail_progress(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """查看学生指定课程的详细进度（管理员）"""
    student = db.query(User).filter(
        User.id == student_id,
        User.role == 'student'
    ).first()
    
    if not student:
        return error_response(
            message="学生不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    course = db.query(PBLCourse).filter(PBLCourse.id == course_id).first()
    if not course:
        return error_response(
            message="课程不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 权限检查
    if current_admin.role != 'platform_admin':
        if student.school_id != current_admin.school_id or course.school_id != current_admin.school_id:
            return error_response(
                message="无权限查看该学生",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    # 获取课程下的所有单元
    units = db.query(PBLUnit).filter(
        PBLUnit.course_id == course_id
    ).order_by(PBLUnit.order).all()
    
    # 统计课程整体进度
    units_progress = []
    for unit in units:
        tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
        total_tasks = len(tasks)
        task_ids = [t.id for t in tasks]
        
        completed_tasks = db.query(PBLTaskProgress).filter(
            PBLTaskProgress.user_id == student_id,
            PBLTaskProgress.task_id.in_(task_ids),
            PBLTaskProgress.status == 'completed'
        ).count() if task_ids else 0
        
        # 查询单元完成时间
        unit_complete_record = db.query(PBLLearningProgress).filter(
            PBLLearningProgress.user_id == student_id,
            PBLLearningProgress.unit_id == unit.id,
            PBLLearningProgress.progress_type == 'unit_complete'
        ).order_by(PBLLearningProgress.created_at.desc()).first()
        
        units_progress.append({
            'unit_id': unit.id,
            'unit_title': unit.title,
            'completed': completed_tasks == total_tasks if total_tasks > 0 else False,
            'completed_at': unit_complete_record.created_at.isoformat() if unit_complete_record else None
        })
    
    # 获取课程下所有任务的进度
    tasks_progress = []
    for unit in units:
        tasks = db.query(PBLTask).filter(PBLTask.unit_id == unit.id).all()
        for task in tasks:
            progress = db.query(PBLTaskProgress).filter(
                PBLTaskProgress.user_id == student_id,
                PBLTaskProgress.task_id == task.id
            ).first()
            
            tasks_progress.append({
                'task_id': task.id,
                'task_title': task.title,
                'unit_title': unit.title,
                'task_type': task.type,
                'status': progress.status if progress else 'pending',
                'score': progress.score if progress else None,
                'submitted_at': progress.updated_at.isoformat() if progress and progress.updated_at else None,
                'graded_at': progress.graded_at.isoformat() if progress and progress.graded_at else None
            })
    
    # 计算统计信息
    total_tasks = sum(len(db.query(PBLTask).filter(PBLTask.unit_id == u.id).all()) for u in units)
    completed_tasks = len([t for t in tasks_progress if t['status'] == 'completed'])
    progress_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    # 计算平均分
    scores = [t['score'] for t in tasks_progress if t['score'] is not None]
    average_score = round(sum(scores) / len(scores), 2) if scores else None
    
    return success_response(data={
        'student_id': student_id,
        'student_name': student.name or student.real_name,
        'student_number': student.student_number,
        'course_id': course_id,
        'course_title': course.title,
        'progress': progress_percentage,
        'average_score': average_score,
        'total_units': len(units),
        'completed_units': len([u for u in units_progress if u['completed']]),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'units': units_progress,
        'tasks': tasks_progress
    })





