"""
AI对话记录 Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ===== 会话相关 =====

class AIChatSessionCreate(BaseModel):
    """创建AI对话会话"""
    unit_uuid: str = Field(..., description="单元UUID")
    course_uuid: Optional[str] = Field(None, description="课程UUID")
    device_type: Optional[str] = Field(None, description="设备类型")
    browser_type: Optional[str] = Field(None, description="浏览器类型")


class AIChatSessionUpdate(BaseModel):
    """更新AI对话会话"""
    status: Optional[str] = Field(None, description="会话状态")
    ended_at: Optional[datetime] = Field(None, description="结束时间")


class AIChatSessionResponse(BaseModel):
    """AI对话会话响应"""
    id: int
    uuid: str
    user_id: int
    unit_uuid: Optional[str]
    course_uuid: Optional[str]
    message_count: int
    user_message_count: int
    ai_message_count: int
    helpful_count: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== 消息相关 =====

class AIChatMessageCreate(BaseModel):
    """创建AI对话消息"""
    session_uuid: str = Field(..., description="会话UUID")
    message_type: str = Field(..., description="消息类型: user, ai, system")
    content: str = Field(..., description="消息内容")
    sequence_number: int = Field(..., description="消息序号")
    
    # AI相关（可选）
    ai_model: Optional[str] = Field(None, description="AI模型名称")
    ai_provider: Optional[str] = Field(None, description="AI服务提供商")
    response_time_ms: Optional[int] = Field(None, description="响应时长")
    
    # 分类（可选）
    category: Optional[str] = Field(None, description="问题分类")
    intent: Optional[str] = Field(None, description="用户意图")


class AIChatMessageUpdate(BaseModel):
    """更新AI对话消息"""
    is_helpful: Optional[bool] = Field(None, description="是否有帮助")
    category: Optional[str] = Field(None, description="问题分类")
    tags: Optional[str] = Field(None, description="标签")


class AIChatMessageResponse(BaseModel):
    """AI对话消息响应"""
    id: int
    uuid: str
    session_uuid: str
    message_type: str
    content: str
    sequence_number: int
    sent_at: datetime
    response_time_ms: Optional[int]
    is_helpful: Optional[bool]
    category: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AIChatMessageBatchCreate(BaseModel):
    """批量创建消息"""
    session_uuid: str = Field(..., description="会话UUID")
    messages: List[dict] = Field(..., description="消息列表")


# ===== 统计分析相关 =====

class StudentChatStats(BaseModel):
    """学生对话统计"""
    user_id: int
    username: str
    total_sessions: int
    total_questions: int
    helpful_answers: int
    avg_session_duration: float
    last_chat_time: Optional[datetime]


class UnitQuestionStats(BaseModel):
    """单元问题统计"""
    unit_uuid: str
    question: str
    ask_count: int
    helpful_rate: float


class ChatAnalytics(BaseModel):
    """对话分析数据"""
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    helpful_rate: float
    top_questions: List[dict]
    active_hours: List[dict]
    category_distribution: List[dict]


