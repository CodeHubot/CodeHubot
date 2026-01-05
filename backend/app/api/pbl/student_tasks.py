from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_user
from ...models.admin import User
from ...models.pbl import PBLTask, PBLTaskProgress

router = APIRouter()

@router.get("/tasks/{task_uuid}")
def get_task_detail(
    task_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"获取任务详情 - 任务UUID: {task_uuid}, 用户ID: {current_user.id}")
    
    task = db.query(PBLTask).filter(PBLTask.uuid == task_uuid).first()
    
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 获取当前用户的任务进度
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.task_id == task.id,
        PBLTaskProgress.user_id == current_user.id
    ).first()
    
    # 如果没有进度记录，创建一个
    if not progress:
        logger.info("未找到进度记录，创建新记录")
        progress = PBLTaskProgress(
            task_id=task.id,
            user_id=current_user.id,
            status='pending',
            progress=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    else:
        # 刷新对象以确保获取最新数据
        db.refresh(progress)
        logger.info(f"找到进度记录 - ID: {progress.id}, 状态: {progress.status}")
        logger.info(f"提交内容: {json.dumps(progress.submission, ensure_ascii=False) if progress.submission else 'None'}")
    
    # 构造返回数据
    progress_data = {
        'id': progress.id,
        'status': progress.status,
        'progress': progress.progress,
        'submission': progress.submission if progress.submission else None,
        'score': progress.score,
        'feedback': progress.feedback,
        'graded_at': progress.graded_at.isoformat() if progress.graded_at else None,
        'created_at': progress.created_at.isoformat() if progress.created_at else None,
        'updated_at': progress.updated_at.isoformat() if progress.updated_at else None
    }
    
    logger.info(f"返回的progress数据: {json.dumps(progress_data, ensure_ascii=False)}")
    
    result = {
        'id': task.id,
        'uuid': task.uuid,
        'unit_id': task.unit_id,
        'title': task.title,
        'description': task.description,
        'type': task.type,
        'difficulty': task.difficulty,
        'estimated_time': task.estimated_time,
        'requirements': task.requirements,
        'prerequisites': task.prerequisites,
        'progress': progress_data
    }
    
    return success_response(data=result)

@router.post("/tasks/{task_uuid}/submit")
def submit_task(
    task_uuid: str,
    submission: Dict[str, Any] = Body(...),
    file_tokens: List[Dict[str, Any]] = Body(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    学生提交任务（支持重复提交）
    
    Args:
        task_uuid: 任务UUID
        submission: 提交内容（作业文字内容）
        file_tokens: 临时文件信息列表，每项包含：
            - file_token: 临时文件标识
            - filename: 原始文件名
            - file_type: 文件类型（word/pdf）
            - file_ext: 文件扩展名
            - file_size: 文件大小
        
    工作流程：
    1. 验证任务和权限
    2. 创建/更新任务进度记录
    3. 处理附件：将临时文件移动到永久目录并创建附件记录
    4. 返回结果
    """
    import json
    import logging
    from typing import List
    
    logger = logging.getLogger(__name__)
    logger.info(f"收到提交请求 - 任务UUID: {task_uuid}, 用户ID: {current_user.id}")
    logger.info(f"提交内容: {json.dumps(submission, ensure_ascii=False)}")
    logger.info(f"附件数量: {len(file_tokens)}")
    
    task = db.query(PBLTask).filter(PBLTask.uuid == task_uuid).first()
    
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    logger.info(f"找到任务 - ID: {task.id}, 标题: {task.title}")
    
    # ===== 安全检查：防止恶意修改 =====
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.task_id == task.id,
        PBLTaskProgress.user_id == current_user.id
    ).first()
    
    # ✅ 安全检查1：禁止修改已评分的作业
    if progress and progress.status == 'completed' and progress.score is not None:
        logger.warning(f"用户 {current_user.id} 尝试修改已评分作业 - 任务: {task_uuid}, 评分: {progress.score}")
        return error_response(
            message="作业已评分，不允许修改。如需修改请联系教师取消评分",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # ✅ 安全检查2：截止日期后不允许修改（但允许延迟首次提交）
    if task.deadline:
        from datetime import datetime
        now = datetime.now()
        
        # 如果已经提交过，且超过截止日期，不允许修改
        if progress and progress.submission and now > task.deadline:
            logger.warning(f"用户 {current_user.id} 尝试在截止日期后修改作业 - 任务: {task_uuid}")
            return error_response(
                message=f"已超过作业截止日期（{task.deadline.strftime('%Y-%m-%d %H:%M')}），不允许修改",
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # 延迟首次提交（警告但允许）
        if (not progress or not progress.submission) and now > task.deadline:
            logger.warning(f"延迟提交 - 用户: {current_user.id}, 任务: {task_uuid}, 截止时间: {task.deadline}")
    
    try:
        # 查找或创建任务进度
        is_resubmit = False
        if not progress:
            logger.info("创建新的进度记录")
            progress = PBLTaskProgress(
                task_id=task.id,
                user_id=current_user.id,
                status='pending',
                progress=0
            )
            db.add(progress)
            db.flush()  # 先 flush 以获取 ID
        else:
            logger.info(f"找到现有进度记录 - ID: {progress.id}, 状态: {progress.status}")
            # 如果是重新提交，清除原有的评分和反馈
            if progress.status in ['review', 'completed']:
                is_resubmit = True
                progress.score = None
                progress.feedback = None
                progress.graded_by = None
                progress.graded_at = None
        
        # 更新提交内容和状态
        progress.submission = submission
        progress.status = 'review'
        progress.progress = 100
        
        logger.info(f"准备提交到数据库 - 进度ID: {progress.id}, submission: {progress.submission}")
        
        db.commit()
        db.refresh(progress)
        
        logger.info(f"数据库提交成功 - 进度ID: {progress.id}")
        
        # ===== 处理附件：将临时文件移动到永久目录 =====
        attached_files = []
        if file_tokens:
            from ...models.pbl import PBLTaskAttachment
            from ...api.pbl.temp_attachments import move_temp_to_permanent
            
            logger.info(f"开始处理 {len(file_tokens)} 个附件")
            
            for token_info in file_tokens:
                try:
                    # token_info 格式：{"file_token": "xxx", "filename": "yyy.docx", "file_type": "word", "file_ext": ".docx", "file_size": 123}
                    file_token = token_info.get('file_token')
                    filename = token_info.get('filename')
                    file_type = token_info.get('file_type')
                    file_ext = token_info.get('file_ext')
                    file_size = token_info.get('file_size')
                    
                    # 将临时文件移动到永久目录
                    stored_filename = move_temp_to_permanent(current_user.id, file_token, file_ext)
                    
                    # 创建附件记录
                    attachment = PBLTaskAttachment(
                        progress_id=progress.id,
                        user_id=current_user.id,
                        filename=filename,
                        stored_filename=stored_filename,
                        file_type=file_type,
                        file_ext=file_ext,
                        file_size=file_size,
                        file_url=f"/uploads/task-attachments/{stored_filename}"
                    )
                    db.add(attachment)
                    db.flush()
                    
                    attached_files.append({
                        'id': attachment.id,
                        'uuid': attachment.uuid,
                        'filename': attachment.filename,
                        'file_type': attachment.file_type,
                        'file_size': attachment.file_size,
                        'file_url': attachment.file_url
                    })
                    
                    logger.info(f"附件处理成功: {filename} → {stored_filename}")
                    
                except Exception as e:
                    logger.error(f"处理附件失败: {token_info}, 错误: {str(e)}", exc_info=True)
                    # 继续处理其他附件，不中断提交
            
            if attached_files:
                db.commit()
                logger.info(f"附件保存成功，共 {len(attached_files)} 个")
        
        # 验证数据是否写入
        verify = db.query(PBLTaskProgress).filter(PBLTaskProgress.id == progress.id).first()
        logger.info(f"验证写入 - submission: {verify.submission}")
        
        message = "作业重新提交成功，等待教师重新评分" if is_resubmit else "任务提交成功，等待教师评分"
        if attached_files:
            message += f"，附件已上传（{len(attached_files)}个）"
        
        return success_response(
            data={
                'id': progress.id,
                'task_id': progress.task_id,
                'status': progress.status,
                'progress': progress.progress,
                'submission': progress.submission,
                'submitted_at': progress.updated_at.isoformat() if progress.updated_at else None,
                'is_resubmit': is_resubmit,
                'attachments': attached_files
            },
            message=message
        )
    except Exception as e:
        db.rollback()
        
        # 清理未使用的临时文件
        if file_tokens:
            from ...api.pbl.temp_attachments import cleanup_temp_files
            try:
                token_list = [t.get('file_token') for t in file_tokens if isinstance(t, dict)]
                cleanup_temp_files(current_user.id, token_list)
            except Exception as cleanup_error:
                logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
        
        logger.error(f"提交失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"提交失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.patch("/tasks/{task_uuid}/progress")
def update_task_progress(
    task_uuid: str,
    progress_value: int,
    task_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务进度"""
    task = db.query(PBLTask).filter(PBLTask.uuid == task_uuid).first()
    
    if not task:
        return error_response(
            message="任务不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证进度值
    if progress_value < 0 or progress_value > 100:
        return error_response(
            message="进度值必须在0-100之间",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证状态值
    if task_status and task_status not in ['pending', 'in-progress', 'blocked', 'review', 'completed']:
        return error_response(
            message="无效的任务状态",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 查找或创建任务进度
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.task_id == task.id,
        PBLTaskProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = PBLTaskProgress(
            task_id=task.id,
            user_id=current_user.id,
            status='pending',
            progress=0
        )
        db.add(progress)
    
    # 更新进度
    progress.progress = progress_value
    if task_status:
        progress.status = task_status
    elif progress_value > 0 and progress.status == 'pending':
        progress.status = 'in-progress'
    
    db.commit()
    db.refresh(progress)
    
    return success_response(
        data={
            'id': progress.id,
            'task_id': progress.task_id,
            'status': progress.status,
            'progress': progress.progress,
            'updated_at': progress.updated_at.isoformat() if progress.updated_at else None
        },
        message="任务进度更新成功"
    )

@router.get("/my-tasks")
def get_my_tasks(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我提交的所有任务"""
    from ...models.pbl import PBLUnit, PBLCourse
    
    # 只查询已提交的任务（status为review或completed）
    query = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.user_id == current_user.id,
        PBLTaskProgress.status.in_(['review', 'completed'])
    )
    
    if status_filter:
        query = query.filter(PBLTaskProgress.status == status_filter)
    
    progress_list = query.all()
    
    result = []
    for progress in progress_list:
        task = db.query(PBLTask).filter(PBLTask.id == progress.task_id).first()
        if task:
            # 获取单元信息
            unit = db.query(PBLUnit).filter(PBLUnit.id == task.unit_id).first()
            if unit:
                # 获取课程信息
                course = db.query(PBLCourse).filter(PBLCourse.id == unit.course_id).first()
                if course:
                    result.append({
                        'task_id': task.id,
                        'task_uuid': task.uuid,
                        'task_title': task.title,
                        'task_type': task.type,
                        'task_difficulty': task.difficulty,
                        'estimated_time': task.estimated_time,
                        'task_order': task.order,
                        'unit_id': unit.id,
                        'unit_uuid': unit.uuid,
                        'unit_title': unit.title,
                        'unit_order': unit.order,
                        'course_id': course.id,
                        'course_uuid': course.uuid,
                        'course_title': course.title,
                        'progress_id': progress.id,
                        'status': progress.status,
                        'progress': progress.progress,
                        'score': progress.score,
                        'feedback': progress.feedback,
                        'submitted_at': progress.updated_at.isoformat() if progress.updated_at else None,
                        'graded_at': progress.graded_at.isoformat() if progress.graded_at else None
                    })
    
    # 按照课程ID、单元倒序、任务顺序排序
    result.sort(key=lambda x: (x['course_id'], -x['unit_order'], x['task_order']))
    
    return success_response(data=result)
