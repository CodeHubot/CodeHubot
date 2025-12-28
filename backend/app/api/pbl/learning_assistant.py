"""
学习助手 API - 学生端
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response
from app.models.user import User
from app.models.learning_assistant import (
    LearningAssistantConversation,
    LearningAssistantMessage,
    StudentLearningProfile
)
from app.models.pbl import PBLCourse, PBLUnit
from app.services.learning_assistant_service import LearningAssistantService

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    context: Dict = Field(default_factory=dict, description="学习上下文")
    conversation_id: Optional[str] = Field(None, description="会话UUID（可选）")


class ConversationUpdateRequest(BaseModel):
    """会话更新请求"""
    title: Optional[str] = Field(None, description="会话标题")


class MessageFeedbackRequest(BaseModel):
    """消息反馈请求"""
    was_helpful: bool = Field(..., description="是否有帮助")
    feedback: Optional[str] = Field(None, description="反馈内容")


# ==================== API Endpoints ====================

@router.post("/chat")
async def chat_with_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与学习助手对话
    
    Context结构示例:
    {
        "course_uuid": "xxx",
        "course_name": "xxx",
        "unit_uuid": "xxx",
        "unit_name": "xxx",
        "current_resource": {
            "uuid": "xxx",
            "type": "video/pdf/quiz",
            "title": "xxx"
        }
    }
    """
    try:
        service = LearningAssistantService(db)
        
        result = await service.chat(
            user_id=current_user.id,
            message=request.message,
            context=request.context,
            conversation_id=request.conversation_id
        )
        
        return success_response(data=result)
    
    except Exception as e:
        logger.error(f"对话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="对话失败，请稍后重试")


@router.get("/conversations")
def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, alias="pageSize", ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的会话列表"""
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
            LearningAssistantConversation.user_id == current_user.id,
            LearningAssistantConversation.is_active == 1
        ).order_by(LearningAssistantConversation.last_message_at.desc())
        
        total = query.count()
        results = query.offset((page - 1) * pageSize).limit(pageSize).all()
        
        items = []
        for conv, fetched_course_name, fetched_unit_name in results:
            d = conv.to_dict()
            # 核心修复：始终优先使用从课程/单元表实时关联到的最新标题
            # 只有当关联查询不到（如课程被物理删除）时，才保留数据库中的快照名称
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
        logger.error(f"获取会话列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.delete("/conversations")
def clear_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空所有会话（软删除）"""
    try:
        service = LearningAssistantService(db)
        count = service.clear_all_conversations(current_user.id)
        return success_response(message=f"已成功清空 {count} 个对话")
    except Exception as e:
        logger.error(f"清空会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="清空对话失败")


@router.get("/conversations/{conversation_uuid}")
def get_conversation(
    conversation_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话详情"""
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid,
        LearningAssistantConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return success_response(data=conversation.to_dict())


@router.put("/conversations/{conversation_uuid}")
def update_conversation(
    conversation_uuid: str,
    request: ConversationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新会话（如重命名）"""
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid,
        LearningAssistantConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 更新标题
    if request.title is not None:
        conversation.title = request.title
    
    db.commit()
    db.refresh(conversation)
    
    return success_response(data=conversation.to_dict(), message="更新成功")


@router.delete("/conversations/{conversation_uuid}")
def delete_conversation(
    conversation_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除会话（软删除）"""
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid,
        LearningAssistantConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 软删除
    conversation.is_active = 0
    db.commit()
    
    return success_response(message="删除成功")


@router.get("/conversations/{conversation_uuid}/messages")
def get_conversation_messages(
    conversation_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的所有消息"""
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.uuid == conversation_uuid,
        LearningAssistantConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = db.query(LearningAssistantMessage).filter(
        LearningAssistantMessage.conversation_id == conversation.id
    ).order_by(LearningAssistantMessage.created_at.asc()).all()
    
    return success_response(data={
        'conversation': conversation.to_dict(),
        'messages': [m.to_dict() for m in messages]
    })


@router.post("/messages/{message_uuid}/feedback")
def submit_message_feedback(
    message_uuid: str,
    request: MessageFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交消息反馈（有帮助/无帮助）"""
    message = db.query(LearningAssistantMessage).filter(
        LearningAssistantMessage.uuid == message_uuid
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 验证权限（确保是该用户的会话）
    conversation = db.query(LearningAssistantConversation).filter(
        LearningAssistantConversation.id == message.conversation_id,
        LearningAssistantConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 更新反馈
    message.was_helpful = 1 if request.was_helpful else 0
    if request.feedback:
        message.user_feedback = request.feedback
    
    db.commit()
    
    return success_response(message="反馈已提交")


@router.get("/my-profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的学习档案"""
    profile = db.query(StudentLearningProfile).filter(
        StudentLearningProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        # 创建默认档案
        profile = StudentLearningProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return success_response(data={
        'total_conversations': profile.total_conversations,
        'total_questions': profile.total_questions,
        'courses_learned': profile.courses_learned or [],
        'weak_points': profile.weak_points or [],
        'strong_points': profile.strong_points or [],
        'learning_style': profile.learning_style,
        'last_active_at': profile.last_active_at.isoformat() if profile.last_active_at else None
    })

