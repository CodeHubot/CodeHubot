"""
学习助手相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, DECIMAL, BigInteger
from sqlalchemy.sql import func
from app.db.base_class import Base


class LearningAssistantConversation(Base):
    """学习助手会话表"""
    __tablename__ = "pbl_learning_assistant_conversations"
    
    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), default='新的对话')
    
    # 学习上下文
    course_uuid = Column(String(36), index=True)
    course_name = Column(String(200))
    unit_uuid = Column(String(36), index=True)
    unit_name = Column(String(200))
    current_resource_id = Column(String(36))
    current_resource_type = Column(String(50))
    current_resource_title = Column(String(200))
    
    # 来源
    source = Column(Enum('manual', 'course_learning', 'homework_help'), default='manual')
    
    # 统计信息
    message_count = Column(Integer, default=0)
    user_message_count = Column(Integer, default=0)
    ai_message_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    avg_response_time = Column(Integer)
    
    # 教师关注
    teacher_reviewed = Column(Integer, default=0)
    teacher_flagged = Column(Integer, default=0)
    teacher_comment = Column(Text)
    
    # 审核
    moderation_status = Column(
        Enum('pending', 'approved', 'flagged', 'blocked'),
        default='approved'
    )
    moderation_flags = Column(JSON)
    
    # 时间
    started_at = Column(DateTime, default=func.now())
    last_message_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """转换为字典（学生视角）"""
        return {
            'uuid': self.uuid,
            'title': self.title,
            'source': self.source,
            'message_count': self.message_count,
            'course_name': self.course_name,
            'unit_name': self.unit_name,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_teacher_dict(self):
        """转换为字典（教师视角）"""
        data = self.to_dict()
        data.update({
            'teacher_reviewed': bool(self.teacher_reviewed),
            'teacher_flagged': bool(self.teacher_flagged),
            'teacher_comment': self.teacher_comment,
            'moderation_status': self.moderation_status
        })
        return data


class LearningAssistantMessage(Base):
    """学习助手消息表"""
    __tablename__ = "pbl_learning_assistant_messages"
    
    id = Column(BigInteger, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    conversation_id = Column(BigInteger, nullable=False, index=True)
    role = Column(Enum('user', 'assistant', 'system'), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64))
    
    # 上下文快照
    context_snapshot = Column(JSON)
    
    # AI回复扩展信息
    knowledge_sources = Column(JSON)
    token_usage = Column(JSON)
    model_used = Column(String(100))
    response_time_ms = Column(Integer)
    
    # 审核
    moderation_result = Column(JSON)
    was_blocked = Column(Integer, default=0)
    original_content = Column(Text)
    
    # 反馈
    was_helpful = Column(Integer)
    user_feedback = Column(Text)
    
    # 教师干预
    teacher_corrected = Column(Integer, default=0)
    teacher_correction = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """转换为字典（学生视角）"""
        return {
            'uuid': self.uuid,
            'role': self.role,
            'content': self.content,
            'knowledge_sources': self.knowledge_sources,
            'was_helpful': self.was_helpful,
            'teacher_corrected': bool(self.teacher_corrected),
            'teacher_correction': self.teacher_correction if self.teacher_corrected else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_teacher_dict(self):
        """转换为字典（教师视角）"""
        data = self.to_dict()
        data.update({
            'context_snapshot': self.context_snapshot,
            'moderation_result': self.moderation_result,
            'was_blocked': bool(self.was_blocked),
            'token_usage': self.token_usage
        })
        return data


class StudentLearningProfile(Base):
    """学生学习档案表"""
    __tablename__ = "pbl_student_learning_profiles"
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # 基础统计
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    
    # 学习统计
    courses_learned = Column(JSON)
    units_learned = Column(JSON)
    total_learning_time = Column(Integer, default=0)
    
    # 知识掌握
    knowledge_map = Column(JSON)
    weak_points = Column(JSON)
    strong_points = Column(JSON)
    
    # 学习特征
    learning_style = Column(String(50))
    avg_questions_per_session = Column(DECIMAL(10, 2), default=0)
    preferred_question_types = Column(JSON)
    
    # 最近活动
    last_active_at = Column(DateTime)
    last_course_uuid = Column(String(36))
    last_unit_uuid = Column(String(36))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ContentModerationLog(Base):
    """内容审核日志表"""
    __tablename__ = "pbl_content_moderation_logs"
    
    id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, index=True)
    conversation_id = Column(BigInteger, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    content_type = Column(Enum('user_message', 'ai_response'))
    original_content = Column(Text, nullable=False)
    filtered_content = Column(Text)
    
    # 审核结果
    status = Column(Enum('pass', 'warning', 'blocked'))
    flags = Column(JSON)
    risk_score = Column(DECIMAL(5, 2))
    
    # 审核详情
    sensitive_words = Column(JSON)
    moderation_service = Column(String(50))
    moderation_response = Column(JSON)
    
    # 处理
    action_taken = Column(String(100))
    notified_teacher = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())


class TeacherViewLog(Base):
    """教师查看日志表"""
    __tablename__ = "pbl_teacher_view_logs"
    
    id = Column(BigInteger, primary_key=True)
    teacher_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    conversation_id = Column(BigInteger, index=True)
    
    action = Column(String(50), nullable=False)
    details = Column(Text)
    
    created_at = Column(DateTime, default=func.now())


class SensitiveWord(Base):
    """敏感词库表"""
    __tablename__ = "pbl_sensitive_words"
    
    id = Column(Integer, primary_key=True)
    word = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    severity = Column(Enum('low', 'medium', 'high'), default='medium')
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())

