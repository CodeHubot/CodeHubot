"""
知识库相关模型
包括：通用知识库、单元知识库、智能体知识库关联、权限管理等
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Boolean, DECIMAL, Index, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib


class KnowledgeBase(Base):
    """通用知识库表"""
    __tablename__ = "kb_main"
    
    id = Column(Integer, primary_key=True, index=True, comment="知识库ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    name = Column(String(100), nullable=False, comment="知识库名称")
    description = Column(Text, comment="知识库描述")
    icon = Column(String(200), comment="知识库图标URL")
    
    # 作用域
    scope_type = Column(Enum('system', 'team', 'course', 'agent', 'personal', name='kb_scope_type'), nullable=False, comment="作用域类型")
    scope_id = Column(Integer, comment="作用域ID")
    parent_kb_id = Column(Integer, ForeignKey("kb_main.id"), comment="父知识库ID")
    
    # 所有者和访问控制
    owner_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="创建者用户ID")
    access_level = Column(Enum('public', 'protected', 'private', name='kb_access_level'), default='protected', comment="访问级别")
    
    # 统计信息
    document_count = Column(Integer, default=0, comment="文档数量")
    chunk_count = Column(Integer, default=0, comment="文本块数量")
    total_size = Column(BigInteger, default=0, comment="总大小（字节）")
    last_updated_at = Column(DateTime, comment="最后更新时间")
    
    # 配置
    chunk_size = Column(Integer, default=500, comment="文本块大小")
    chunk_overlap = Column(Integer, default=50, comment="文本块重叠大小")
    embedding_model_id = Column(Integer, comment="Embedding模型ID")
    retrieval_config = Column(JSON, comment="检索配置")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_system = Column(Boolean, default=False, comment="是否系统内置")
    is_deleted = Column(Integer, default=0, comment="是否删除（0=未删除，1=已删除，软删除）")
    
    # 扩展
    tags = Column(JSON, comment="标签")
    meta_data = Column(JSON, comment="扩展元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间（保留兼容）")
    
    # 关系
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="knowledge_base", cascade="all, delete-orphan")
    agent_associations = relationship("AgentKnowledgeBase", back_populates="knowledge_base", cascade="all, delete-orphan")
    analytics = relationship("KBAnalytics", back_populates="knowledge_base", cascade="all, delete-orphan")


class AgentKnowledgeBase(Base):
    """智能体知识库关联表"""
    __tablename__ = "agent_knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    agent_id = Column(Integer, ForeignKey("agent_main.id"), nullable=False, index=True, comment="智能体ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    
    # 检索配置
    priority = Column(Integer, default=0, comment="优先级")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    top_k = Column(Integer, default=5, comment="检索返回数量")
    similarity_threshold = Column(DECIMAL(3, 2), default=0.70, comment="相似度阈值")
    retrieval_mode = Column(Enum('vector', 'keyword', 'hybrid', name='retrieval_mode_enum'), default='hybrid', comment="检索模式")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    agent = relationship("Agent", back_populates="knowledge_bases")
    knowledge_base = relationship("KnowledgeBase", back_populates="agent_associations")


class KBPermission(Base):
    """知识库权限表"""
    __tablename__ = "kb_permissions"
    
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    user_id = Column(Integer, ForeignKey("core_users.id"), index=True, comment="用户ID")
    role = Column(String(50), comment="角色")
    permission_type = Column(Enum('read', 'write', 'manage', 'admin', name='kb_permission_type'), nullable=False, comment="权限类型")
    granted_by = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="授权人ID")
    expires_at = Column(DateTime, comment="过期时间")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")


class KBSharing(Base):
    """知识库共享表"""
    __tablename__ = "kb_sharing"
    
    id = Column(Integer, primary_key=True, index=True, comment="共享ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    team_id = Column(Integer, ForeignKey("core_teams.id"), comment="共享给团队ID")
    course_id = Column(BigInteger, comment="共享给课程ID")
    user_id = Column(Integer, ForeignKey("core_users.id"), comment="共享给用户ID")
    share_type = Column(Enum('read_only', 'editable', 'reference', name='kb_share_type'), default='read_only', comment="共享类型")
    shared_by = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="共享人ID")
    expires_at = Column(DateTime, comment="过期时间")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")


class UnitKnowledgeBase(Base):
    """单元知识库表"""
    __tablename__ = "pbl_unit_knowledge_base"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    
    # 关联信息
    unit_id = Column(BigInteger)
    unit_uuid = Column(String(36), nullable=False, index=True)
    course_id = Column(BigInteger)
    course_uuid = Column(String(36), index=True)
    
    # 知识内容
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text')
    summary = Column(String(500))
    
    # 分类和标签
    category = Column(String(50), index=True)
    tags = Column(String(255))
    keywords = Column(Text)
    
    # 来源信息
    source_type = Column(String(50))
    source_id = Column(BigInteger)
    source_url = Column(String(500))
    
    # 优先级和质量
    priority = Column(Integer, default=0, index=True)
    quality_score = Column(DECIMAL(5, 2), default=0.00, index=True)
    usage_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    
    # 状态管理
    status = Column(String(20), default='active', index=True)
    is_public = Column(Boolean, default=True)
    
    # 扩展信息
    extra_metadata = Column(Text)
    
    # 创建和更新
    created_by = Column(BigInteger)
    updated_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class KnowledgeUsageLog(Base):
    """知识点使用记录表"""
    __tablename__ = "pbl_knowledge_usage_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 关联信息
    knowledge_id = Column(BigInteger, nullable=False, index=True)
    knowledge_uuid = Column(String(36), nullable=False, index=True)
    message_id = Column(BigInteger, index=True)
    message_uuid = Column(String(36), index=True)
    session_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    
    # 检索信息
    query_text = Column(String(500))
    relevance_score = Column(DECIMAL(5, 2))
    match_type = Column(String(50))
    
    # 反馈信息
    is_helpful = Column(Boolean)
    feedback_at = Column(DateTime)
    
    # 时间戳
    used_at = Column(DateTime, server_default=func.now(), index=True)
