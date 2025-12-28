"""
AI对话记录模型
用于存储和分析学生与AI的对话记录
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Boolean, DECIMAL, Index
from sqlalchemy.sql import func
from app.db.base_class import Base


class AIChatSession(Base):
    """AI对话会话表"""
    __tablename__ = "pbl_ai_chat_sessions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment='会话唯一标识')
    
    # 关联信息
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    student_id = Column(BigInteger, index=True, comment='学生ID')
    course_id = Column(BigInteger, comment='课程ID')
    course_uuid = Column(String(36), index=True, comment='课程UUID')
    unit_id = Column(BigInteger, comment='单元ID')
    unit_uuid = Column(String(36), index=True, comment='单元UUID')
    
    # 会话统计
    message_count = Column(Integer, default=0, comment='消息总数')
    user_message_count = Column(Integer, default=0, comment='用户消息数')
    ai_message_count = Column(Integer, default=0, comment='AI回复数')
    helpful_count = Column(Integer, default=0, comment='有帮助的回复数')
    
    # 会话时长
    started_at = Column(DateTime, nullable=False, index=True, comment='会话开始时间')
    ended_at = Column(DateTime, comment='会话结束时间')
    duration_seconds = Column(Integer, default=0, comment='会话时长（秒）')
    
    # 会话状态
    status = Column(String(20), default='active', index=True, comment='会话状态')
    is_anonymous = Column(Boolean, default=False, comment='是否匿名')
    
    # 设备和环境信息
    device_type = Column(String(50), comment='设备类型')
    browser_type = Column(String(50), comment='浏览器类型')
    ip_address = Column(String(50), comment='IP地址')
    
    # 通用字段
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')


class AIChatMessage(Base):
    """AI对话消息表"""
    __tablename__ = "pbl_ai_chat_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment='消息唯一标识')
    
    # 关联信息
    session_id = Column(BigInteger, nullable=False, index=True, comment='会话ID')
    session_uuid = Column(String(36), nullable=False, index=True, comment='会话UUID')
    user_id = Column(BigInteger, nullable=False, index=True, comment='用户ID')
    unit_uuid = Column(String(36), index=True, comment='单元UUID')
    
    # 消息内容
    message_type = Column(String(20), nullable=False, index=True, comment='消息类型')
    content = Column(Text, nullable=False, comment='消息内容')
    content_length = Column(Integer, default=0, comment='内容长度')
    
    # 消息顺序和时间
    sequence_number = Column(Integer, nullable=False, comment='消息序号')
    sent_at = Column(DateTime, nullable=False, index=True, comment='发送时间')
    response_time_ms = Column(Integer, comment='响应时长（毫秒）')
    
    # AI相关信息
    ai_model = Column(String(50), comment='AI模型名称')
    ai_provider = Column(String(50), comment='AI服务提供商')
    ai_tokens_used = Column(Integer, comment='使用的token数')
    ai_confidence = Column(DECIMAL(5, 2), comment='AI回复置信度')
    
    # 用户反馈
    is_helpful = Column(Boolean, index=True, comment='是否有帮助')
    feedback_at = Column(DateTime, comment='反馈时间')
    
    # 分类和标签
    category = Column(String(50), index=True, comment='问题分类')
    tags = Column(String(255), comment='标签')
    intent = Column(String(50), comment='用户意图')
    
    # 上下文信息
    context_data = Column(Text, comment='上下文数据')
    
    # 通用字段
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 创建组合索引
    __table_args__ = (
        Index('idx_session_sequence', 'session_id', 'sequence_number'),
    )


