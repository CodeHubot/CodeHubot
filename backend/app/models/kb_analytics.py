"""
知识库分析模型
包含：检索日志、统计分析
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Date, DECIMAL, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib
import enum


class UserFeedback(str, enum.Enum):
    """用户反馈枚举"""
    HELPFUL = "helpful"          # 有帮助
    NOT_HELPFUL = "not_helpful"  # 没帮助
    IRRELEVANT = "irrelevant"    # 不相关


class KBRetrievalLog(Base):
    """
    知识库检索日志模型
    用于记录每次知识库检索的详细信息
    """
    __tablename__ = "aiot_kb_retrieval_logs"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    
    # 查询信息
    query = Column(Text, nullable=False, comment="查询文本")
    agent_id = Column(Integer, ForeignKey("aiot_agents.id"), nullable=True, index=True, comment="智能体ID")
    user_id = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=False, index=True, comment="用户ID")
    
    # 检索范围
    kb_ids = Column(JSON, comment="检索的知识库ID列表")
    scope_type = Column(String(50), comment="检索范围类型")
    
    # 检索结果
    retrieved_chunks = Column(JSON, comment="检索到的文本块ID及分数")
    chunk_count = Column(Integer, comment="返回的文本块数量")
    avg_similarity_score = Column(DECIMAL(4, 3), comment="平均相似度分数")
    retrieval_time_ms = Column(Integer, comment="检索耗时（毫秒）")
    
    # 用户反馈
    user_feedback = Column(String(20), nullable=True, comment="用户反馈")
    feedback_at = Column(DateTime, nullable=True, comment="反馈时间")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, index=True, comment="创建时间")
    
    # 关系
    agent = relationship("Agent")
    user = relationship("User")
    
    def __repr__(self):
        return f"<KBRetrievalLog(id={self.id}, query='{self.query[:30]}...')>"


class KBAnalytics(Base):
    """
    知识库统计分析模型
    按日统计知识库的使用情况和质量指标
    """
    __tablename__ = "aiot_kb_analytics"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="统计ID")
    knowledge_base_id = Column(Integer, ForeignKey("aiot_knowledge_bases.id"), nullable=False, index=True, comment="知识库ID")
    date = Column(Date, nullable=False, index=True, comment="统计日期")
    
    # 查询统计
    query_count = Column(Integer, default=0, comment="查询次数")
    unique_users = Column(Integer, default=0, comment="独立用户数")
    
    # 质量统计
    hit_rate = Column(DECIMAL(4, 3), comment="命中率")
    avg_similarity = Column(DECIMAL(4, 3), comment="平均相似度")
    positive_feedback_count = Column(Integer, default=0, comment="正面反馈数")
    negative_feedback_count = Column(Integer, default=0, comment="负面反馈数")
    
    # 更新统计
    document_added = Column(Integer, default=0, comment="新增文档数")
    document_updated = Column(Integer, default=0, comment="更新文档数")
    document_deleted = Column(Integer, default=0, comment="删除文档数")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="analytics")
    
    def __repr__(self):
        return f"<KBAnalytics(kb_id={self.knowledge_base_id}, date='{self.date}')>"

