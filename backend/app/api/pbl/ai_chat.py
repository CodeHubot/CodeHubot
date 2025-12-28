"""
AI对话记录API
用于保存和分析学生与AI的对话记录
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import uuid

from app.core.deps import get_db, get_current_user
from app.core.response import success_response
from app.models.ai_chat import AIChatSession, AIChatMessage
from app.models.user import User
from app.schemas.ai_chat import (
    AIChatSessionCreate,
    AIChatSessionResponse,
    AIChatMessageCreate,
    AIChatMessageResponse,
    AIChatMessageUpdate,
    AIChatMessageBatchCreate,
    StudentChatStats,
    ChatAnalytics
)

router = APIRouter()


# ===== 会话管理 =====

@router.post("/sessions", response_model=AIChatSessionResponse)
def create_chat_session(
    session_data: AIChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建AI对话会话
    
    - 开始新的学习会话时调用
    - 返回会话UUID，用于后续消息关联
    """
    # 创建会话
    chat_session = AIChatSession(
        uuid=str(uuid.uuid4()),
        user_id=current_user.id,
        student_id=current_user.id if current_user.role == 'student' else None,
        course_uuid=session_data.course_uuid,
        unit_uuid=session_data.unit_uuid,
        started_at=datetime.now(),
        status='active',
        device_type=session_data.device_type,
        browser_type=session_data.browser_type
    )
    
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return chat_session


@router.get("/sessions/{session_uuid}", response_model=AIChatSessionResponse)
def get_chat_session(
    session_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话详情"""
    session = db.query(AIChatSession).filter(
        AIChatSession.uuid == session_uuid,
        AIChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return session


@router.put("/sessions/{session_uuid}/end")
def end_chat_session(
    session_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    结束AI对话会话
    
    - 用户退出单元学习时调用
    - 计算会话时长和统计信息
    """
    session = db.query(AIChatSession).filter(
        AIChatSession.uuid == session_uuid,
        AIChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 更新会话信息
    session.ended_at = datetime.now()
    session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
    session.status = 'completed'
    
    db.commit()
    
    return success_response(message="会话已结束")


# ===== 消息管理 =====

@router.post("/messages", response_model=AIChatMessageResponse)
def create_chat_message(
    message_data: AIChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    保存单条AI对话消息
    
    - 用户发送消息或AI回复时调用
    - 自动更新会话统计信息
    """
    # 查找会话
    session = db.query(AIChatSession).filter(
        AIChatSession.uuid == message_data.session_uuid
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 创建消息
    message = AIChatMessage(
        uuid=str(uuid.uuid4()),
        session_id=session.id,
        session_uuid=session.uuid,
        user_id=current_user.id,
        unit_uuid=session.unit_uuid,
        message_type=message_data.message_type,
        content=message_data.content,
        content_length=len(message_data.content),
        sequence_number=message_data.sequence_number,
        sent_at=datetime.now(),
        response_time_ms=message_data.response_time_ms,
        ai_model=message_data.ai_model,
        ai_provider=message_data.ai_provider,
        category=message_data.category,
        intent=message_data.intent
    )
    
    db.add(message)
    
    # 更新会话统计
    session.message_count += 1
    if message_data.message_type == 'user':
        session.user_message_count += 1
    elif message_data.message_type == 'ai':
        session.ai_message_count += 1
    
    db.commit()
    db.refresh(message)
    
    return message


@router.post("/messages/batch")
def create_chat_messages_batch(
    batch_data: AIChatMessageBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量保存对话消息
    
    - 用于同步本地缓存的历史消息
    - 提高性能，减少API调用次数
    """
    # 查找会话
    session = db.query(AIChatSession).filter(
        AIChatSession.uuid == batch_data.session_uuid
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 批量创建消息
    messages_to_add = []
    user_count = 0
    ai_count = 0
    
    for msg_data in batch_data.messages:
        message = AIChatMessage(
            uuid=str(uuid.uuid4()),
            session_id=session.id,
            session_uuid=session.uuid,
            user_id=current_user.id,
            unit_uuid=session.unit_uuid,
            message_type=msg_data.get('type'),
            content=msg_data.get('content'),
            content_length=len(msg_data.get('content', '')),
            sequence_number=msg_data.get('sequence_number'),
            sent_at=datetime.fromtimestamp(msg_data.get('timestamp', 0) / 1000),
            category=msg_data.get('category')
        )
        messages_to_add.append(message)
        
        if msg_data.get('type') == 'user':
            user_count += 1
        elif msg_data.get('type') == 'ai':
            ai_count += 1
    
    db.bulk_save_objects(messages_to_add)
    
    # 更新会话统计
    session.message_count = len(messages_to_add)
    session.user_message_count = user_count
    session.ai_message_count = ai_count
    
    db.commit()
    
    return success_response(
        data={"saved_count": len(messages_to_add)},
        message=f"已保存 {len(messages_to_add)} 条消息"
    )


@router.put("/messages/{message_uuid}/feedback")
def update_message_feedback(
    message_uuid: str,
    update_data: AIChatMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新消息反馈（点赞/有帮助）
    
    - 用户点击"有帮助"按钮时调用
    - 用于评估AI回复质量
    """
    message = db.query(AIChatMessage).filter(
        AIChatMessage.uuid == message_uuid,
        AIChatMessage.user_id == current_user.id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 更新反馈
    old_helpful = message.is_helpful
    message.is_helpful = update_data.is_helpful
    message.feedback_at = datetime.now()
    
    # 更新会话的有帮助计数
    if update_data.is_helpful is not None:
        session = db.query(AIChatSession).filter(
            AIChatSession.id == message.session_id
        ).first()
        
        if session:
            if update_data.is_helpful and not old_helpful:
                session.helpful_count += 1
            elif not update_data.is_helpful and old_helpful:
                session.helpful_count = max(0, session.helpful_count - 1)
    
    db.commit()
    
    return success_response(message="反馈已更新")


@router.get("/messages/session/{session_uuid}", response_model=List[AIChatMessageResponse])
def get_session_messages(
    session_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的所有消息"""
    messages = db.query(AIChatMessage).filter(
        AIChatMessage.session_uuid == session_uuid,
        AIChatMessage.user_id == current_user.id
    ).order_by(AIChatMessage.sequence_number).all()
    
    return messages


# ===== 统计分析 =====

@router.get("/stats/student/{user_id}")
def get_student_chat_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取学生对话统计
    
    - 管理员查看学生学习行为
    - 学生查看自己的统计数据
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher'] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    
    # 查询统计数据
    stats = db.query(
        func.count(AIChatSession.id).label('total_sessions'),
        func.count(AIChatMessage.id).filter(AIChatMessage.message_type == 'user').label('total_questions'),
        func.count(AIChatMessage.id).filter(AIChatMessage.is_helpful == True).label('helpful_answers'),
        func.avg(AIChatSession.duration_seconds).label('avg_duration')
    ).select_from(AIChatSession).outerjoin(
        AIChatMessage, AIChatSession.id == AIChatMessage.session_id
    ).filter(
        AIChatSession.user_id == user_id
    ).first()
    
    # 最近聊天时间
    last_session = db.query(AIChatSession).filter(
        AIChatSession.user_id == user_id
    ).order_by(desc(AIChatSession.started_at)).first()
    
    return success_response(data={
        "total_sessions": stats.total_sessions or 0,
        "total_questions": stats.total_questions or 0,
        "helpful_answers": stats.helpful_answers or 0,
        "avg_session_duration": float(stats.avg_duration or 0),
        "last_chat_time": last_session.started_at if last_session else None
    })


@router.get("/stats/unit/{unit_uuid}/popular-questions")
def get_unit_popular_questions(
    unit_uuid: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单元热门问题
    
    - 分析学生常见问题
    - 优化课程内容
    """
    # 查询热门问题
    popular_questions = db.query(
        AIChatMessage.content,
        func.count(AIChatMessage.id).label('ask_count')
    ).filter(
        AIChatMessage.unit_uuid == unit_uuid,
        AIChatMessage.message_type == 'user',
        AIChatMessage.content_length > 5  # 过滤过短的消息
    ).group_by(
        AIChatMessage.content
    ).having(
        func.count(AIChatMessage.id) >= 2  # 至少被问过2次
    ).order_by(
        desc('ask_count')
    ).limit(limit).all()
    
    questions_data = [
        {
            "question": q.content,
            "ask_count": q.ask_count
        }
        for q in popular_questions
    ]
    
    return success_response(data=questions_data)


@router.get("/analytics/overview")
def get_chat_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    unit_uuid: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取对话分析总览
    
    - 管理员查看整体数据
    - 支持时间范围和单元过滤
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="无权访问")
    
    # 构建查询条件
    filters = []
    if start_date:
        filters.append(AIChatSession.started_at >= datetime.fromisoformat(start_date))
    if end_date:
        filters.append(AIChatSession.started_at <= datetime.fromisoformat(end_date))
    if unit_uuid:
        filters.append(AIChatSession.unit_uuid == unit_uuid)
    
    # 基础统计
    total_sessions = db.query(func.count(AIChatSession.id)).filter(*filters).scalar()
    total_messages = db.query(func.count(AIChatMessage.id)).join(
        AIChatSession, AIChatMessage.session_id == AIChatSession.id
    ).filter(*filters).scalar()
    
    helpful_count = db.query(func.count(AIChatMessage.id)).join(
        AIChatSession, AIChatMessage.session_id == AIChatSession.id
    ).filter(
        AIChatMessage.is_helpful == True,
        *filters
    ).scalar()
    
    ai_message_count = db.query(func.count(AIChatMessage.id)).join(
        AIChatSession, AIChatMessage.session_id == AIChatSession.id
    ).filter(
        AIChatMessage.message_type == 'ai',
        *filters
    ).scalar()
    
    # 计算指标
    avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
    helpful_rate = helpful_count / ai_message_count if ai_message_count > 0 else 0
    
    # 问题分类分布
    category_dist = db.query(
        AIChatMessage.category,
        func.count(AIChatMessage.id).label('count')
    ).join(
        AIChatSession, AIChatMessage.session_id == AIChatSession.id
    ).filter(
        AIChatMessage.message_type == 'user',
        AIChatMessage.category.isnot(None),
        *filters
    ).group_by(AIChatMessage.category).all()
    
    return success_response(data={
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "avg_messages_per_session": round(avg_messages_per_session, 2),
        "helpful_rate": round(helpful_rate * 100, 2),  # 转换为百分比
        "category_distribution": [
            {"category": c.category, "count": c.count}
            for c in category_dist
        ]
    })


