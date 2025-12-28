"""
学习助手 API - 教师端
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response
from app.models.user import User
from app.models.learning_assistant import (
    LearningAssistantConversation,
    LearningAssistantMessage,
    TeacherViewLog
)
from app.models.pbl import PBLCourse, PBLUnit

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class MessageCorrectionRequest(BaseModel):
    """消息修正请求"""
    correction: str = Field(..., description="修正内容")


class ConversationFlagRequest(BaseModel):
    """会话标记请求"""
    comment: Optional[str] = Field(None, description="备注")


# ==================== Helper Functions ====================

def is_admin(user: User) -> bool:
    """检查是否是学校管理员或超级管理员"""
    return user.role in ['school_admin', 'super_admin']


def can_view_student(teacher_id: int, student_id: int, db: Session) -> bool:
    """
    检查教师是否有权查看学生
    
    TODO: 实现更细粒度的权限检查（如是否教该学生的课）
    """
    # 简化版：所有教师都可以查看所有学生
    # 实际应该检查教师是否教该学生
    return True


def log_teacher_view(
    teacher_id: int,
    student_id: int,
    action: str,
    db: Session,
    conversation_id: int = None,
    details: str = None
):
    """记录教师查看日志"""
    log = TeacherViewLog(
        teacher_id=teacher_id,
        student_id=student_id,
        conversation_id=conversation_id,
        action=action,
        details=details
    )
    db.add(log)
    db.commit()


# ==================== API Endpoints ====================

@router.get("/students")
def get_students_list(
    course_uuid: str = Query(None, description="课程UUID（可选）"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取学生列表（教师视角）
    """
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 获取所有有对话记录的学生
        from sqlalchemy import func, distinct
        
        query = db.query(
            User.id,
            User.username,
            User.name,
            User.real_name,
            User.nickname,
            func.count(LearningAssistantConversation.id).label('total_conversations'),
            func.sum(
                LearningAssistantConversation.teacher_flagged
            ).label('flagged_conversations'),
            func.max(LearningAssistantConversation.last_message_at).label('last_active')
        ).join(
            LearningAssistantConversation,
            User.id == LearningAssistantConversation.user_id
        ).filter(
            User.role == 'student'
        )
        
        # 如果指定了课程，筛选该课程的学生
        if course_uuid:
            query = query.filter(
                LearningAssistantConversation.course_uuid == course_uuid
            )
        
        query = query.group_by(User.id, User.username, User.name, User.real_name, User.nickname)
        
        total = query.count()
        students = query.offset((page - 1) * pageSize).limit(pageSize).all()
        
        result = []
        for student in students:
            # 手动构造full_name（因为它是property，不能在query中使用）
            full_name = student.name or student.real_name or student.nickname or student.username
            
            result.append({
                'student_id': student.id,
                'student_uuid': str(student.id),  # 使用ID作为UUID（兼容前端）
                'student_name': full_name,
                'username': student.username,
                'total_conversations': student.total_conversations or 0,
                'flagged_conversations': student.flagged_conversations or 0,
                'last_active': student.last_active.isoformat() if student.last_active else None
            })
        
        return success_response(data={
            'items': result,
            'total': total,
            'page': page,
            'page_size': pageSize
        })
    
    except Exception as e:
        logger.error(f"获取学生列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取学生列表失败")


@router.get("/students/{student_uuid}/conversations")
def get_student_conversations(
    student_uuid: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查看学生的对话列表"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 将student_uuid转换为ID（因为User表没有uuid字段）
    try:
        student_id = int(student_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的学生ID")
    
    # 根据ID获取学生
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 权限检查
    if not can_view_student(current_user.id, student.id, db):
        raise HTTPException(status_code=403, detail="无权查看该学生")
    
    # 记录查看日志
    log_teacher_view(
        teacher_id=current_user.id,
        student_id=student.id,
        action='view_conversations',
        db=db
    )
    
    try:
        from sqlalchemy.orm import aliased
        CourseAlias = aliased(PBLCourse)
        UnitAlias = aliased(PBLUnit)
        
        query = db.query(
            LearningAssistantConversation,
            CourseAlias.title.label('fetched_course_name'),
            UnitAlias.title.label('fetched_unit_name')
        ).outerjoin(
            CourseAlias, LearningAssistantConversation.course_uuid == CourseAlias.uuid
        ).outerjoin(
            UnitAlias, LearningAssistantConversation.unit_uuid == UnitAlias.uuid
        ).filter(
            LearningAssistantConversation.user_id == student.id,
            LearningAssistantConversation.is_active == 1
        ).order_by(LearningAssistantConversation.last_message_at.desc())
        
        total = query.count()
        results = query.offset((page - 1) * pageSize).limit(pageSize).all()
        
        items = []
        for conv, fetched_course_name, fetched_unit_name in results:
            d = conv.to_teacher_dict()
            # 核心修复：始终优先使用实时关联到的最新标题
            if fetched_course_name:
                d['course_name'] = fetched_course_name
            if fetched_unit_name:
                d['unit_name'] = fetched_unit_name
            items.append(d)
        
        return success_response(data={
            'items': items,
            'total': total,
            'page': page,
            'page_size': pageSize
        })
    
    except Exception as e:
        logger.error(f"获取学生对话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取学生对话失败")


@router.get("/conversations/{conversation_uuid}/messages")
def get_conversation_messages(
    conversation_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查看会话的所有消息"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 权限检查
    if not can_view_student(current_user.id, conversation.user_id, db):
        raise HTTPException(status_code=403, detail="无权查看")
    
    # 记录查看日志
    log_teacher_view(
        teacher_id=current_user.id,
        student_id=conversation.user_id,
        action='view_conversation_detail',
        conversation_id=conversation.id,
        details=f'conversation_uuid:{conversation_uuid}',
        db=db
    )
    
    # 标记为已查看
    conversation.teacher_reviewed = 1
    db.commit()
    
    # 获取消息
    messages = db.query(LearningAssistantMessage).filter(
        LearningAssistantMessage.conversation_id == conversation.id
    ).order_by(LearningAssistantMessage.created_at.asc()).all()
    
    return success_response(data={
        'conversation': conversation.to_teacher_dict(),
        'messages': [msg.to_teacher_dict() for msg in messages]
    })


@router.post("/messages/{message_uuid}/correct")
def correct_ai_response(
    message_uuid: str,
    request: MessageCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """教师修正AI回复"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    message = db.query(LearningAssistantMessage).filter(
        LearningAssistantMessage.uuid == message_uuid,
        LearningAssistantMessage.role == 'assistant'
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 权限检查
    conversation = db.query(LearningAssistantConversation).get(message.conversation_id)
    if not can_view_student(current_user.id, conversation.user_id, db):
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 保存修正
    message.teacher_corrected = 1
    message.teacher_correction = request.correction
    db.commit()
    
    # 记录日志
    log_teacher_view(
        teacher_id=current_user.id,
        student_id=conversation.user_id,
        action='correct_message',
        conversation_id=conversation.id,
        details=f'message_uuid:{message_uuid}',
        db=db
    )
    
    return success_response(message="修正已保存")


@router.post("/conversations/{conversation_uuid}/flag")
def flag_conversation(
    conversation_uuid: str,
    request: ConversationFlagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记需要关注的对话"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 权限检查
    if not can_view_student(current_user.id, conversation.user_id, db):
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 标记
    conversation.teacher_flagged = 1
    if request.comment:
        conversation.teacher_comment = request.comment
    db.commit()
    
    # 记录日志
    log_teacher_view(
        teacher_id=current_user.id,
        student_id=conversation.user_id,
        action='flag_conversation',
        conversation_id=conversation.id,
        details=f'comment:{request.comment}' if request.comment else None,
        db=db
    )
    
    return success_response(message="已标记")


@router.delete("/conversations/{conversation_uuid}/flag")
def unflag_conversation(
    conversation_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消标记"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 权限检查
    if not can_view_student(current_user.id, conversation.user_id, db):
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 取消标记
    conversation.teacher_flagged = 0
    conversation.teacher_comment = None
    db.commit()
    
    return success_response(message="已取消标记")


@router.get("/statistics")
def get_statistics(
    course_uuid: str = Query(None, description="课程UUID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统计数据"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    from sqlalchemy import func
    
    try:
        # 基础查询
        query = db.query(LearningAssistantConversation)
        
        if course_uuid:
            query = query.filter(
                LearningAssistantConversation.course_uuid == course_uuid
            )
        
        # 统计数据
        total_conversations = query.count()
        total_students = query.with_entities(
            func.count(func.distinct(LearningAssistantConversation.user_id))
        ).scalar()
        
        flagged_conversations = query.filter(
            LearningAssistantConversation.teacher_flagged == 1
        ).count()
        
        # 总消息数
        total_messages = db.query(func.count(LearningAssistantMessage.id)).join(
            LearningAssistantConversation,
            LearningAssistantMessage.conversation_id == LearningAssistantConversation.id
        )
        
        if course_uuid:
            total_messages = total_messages.filter(
                LearningAssistantConversation.course_uuid == course_uuid
            )
        
        total_messages = total_messages.scalar() or 0
        
        return success_response(data={
            'total_conversations': total_conversations,
            'total_students': total_students or 0,
            'total_messages': total_messages,
            'flagged_conversations': flagged_conversations
        })
    
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取统计数据失败")

