"""
知识库模型
包含：知识库、智能体关联、权限、共享等
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib
import enum


class ScopeType(str, enum.Enum):
    """作用域类型枚举"""
    SYSTEM = "system"      # 系统级
    SCHOOL = "school"      # 学校级
    COURSE = "course"      # 课程级
    AGENT = "agent"        # 智能体级
    PERSONAL = "personal"  # 个人级


class AccessLevel(str, enum.Enum):
    """访问级别枚举"""
    PUBLIC = "public"        # 公开
    PROTECTED = "protected"  # 保护（需授权）
    PRIVATE = "private"      # 私有


class KnowledgeBase(Base):
    """
    知识库模型
    支持四级层级：系统级 > 学校级 > 课程级 > 智能体级/个人级
    """
    __tablename__ = "kb_main"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="知识库ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    name = Column(String(100), nullable=False, comment="知识库名称")
    description = Column(Text, comment="知识库描述")
    icon = Column(String(200), comment="知识库图标URL")
    
    # 层级与归属
    scope_type = Column(String(20), nullable=False, index=True, comment="作用域类型")
    scope_id = Column(Integer, nullable=True, index=True, comment="作用域ID")
    parent_kb_id = Column(Integer, ForeignKey("kb_main.id"), nullable=True, comment="父知识库ID")
    
    # 创建者与权限
    owner_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="创建者用户ID")
    access_level = Column(String(20), default="protected", comment="访问级别")
    
    # 统计信息
    document_count = Column(Integer, default=0, comment="文档数量")
    chunk_count = Column(Integer, default=0, comment="文本块数量")
    total_size = Column(Integer, default=0, comment="总大小（字节）")
    last_updated_at = Column(DateTime, comment="最后更新时间")
    
    # 配置参数
    chunk_size = Column(Integer, default=500, comment="文本块大小")
    chunk_overlap = Column(Integer, default=50, comment="文本块重叠大小")
    embedding_model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=True, comment="Embedding模型ID")
    retrieval_config = Column(JSON, comment="检索配置")
    
    # 状态与元数据
    is_active = Column(Integer, default=1, index=True, comment="是否激活")
    is_system = Column(Integer, default=0, comment="是否系统内置")
    tags = Column(JSON, comment="标签")
    meta_data = Column(JSON, comment="扩展元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    owner = relationship("User", foreign_keys=[owner_id])
    parent_kb = relationship("KnowledgeBase", remote_side=[id], backref="child_kbs")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="knowledge_base", cascade="all, delete-orphan")
    agent_associations = relationship("AgentKnowledgeBase", back_populates="knowledge_base", cascade="all, delete-orphan")
    permissions = relationship("KBPermission", back_populates="knowledge_base", cascade="all, delete-orphan")
    sharings = relationship("KBSharing", back_populates="knowledge_base", cascade="all, delete-orphan")
    analytics = relationship("KBAnalytics", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}', scope_type='{self.scope_type}')>"


class AgentKnowledgeBase(Base):
    """
    智能体知识库关联模型
    一个智能体可以关联多个知识库
    """
    __tablename__ = "agent_knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    agent_id = Column(Integer, ForeignKey("agent_main.id"), nullable=False, index=True, comment="智能体ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    
    # 配置
    priority = Column(Integer, default=0, comment="优先级")
    is_enabled = Column(Integer, default=1, comment="是否启用")
    
    # 检索配置
    top_k = Column(Integer, default=5, comment="检索返回数量")
    similarity_threshold = Column(DECIMAL(3, 2), default=0.70, comment="相似度阈值")
    retrieval_mode = Column(String(20), default="hybrid", comment="检索模式")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    agent = relationship("Agent")
    knowledge_base = relationship("KnowledgeBase", back_populates="agent_associations")
    
    def __repr__(self):
        return f"<AgentKnowledgeBase(agent_id={self.agent_id}, kb_id={self.knowledge_base_id})>"


class PermissionType(str, enum.Enum):
    """权限类型枚举"""
    READ = "read"      # 只读
    WRITE = "write"    # 读写
    MANAGE = "manage"  # 管理
    ADMIN = "admin"    # 管理员


class KBPermission(Base):
    """
    知识库权限模型
    支持用户级和角色级权限
    """
    __tablename__ = "kb_permissions"
    
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    
    # 授权对象（二选一）
    user_id = Column(Integer, ForeignKey("core_users.id"), nullable=True, index=True, comment="用户ID")
    role = Column(String(50), nullable=True, index=True, comment="角色")
    
    # 权限类型
    permission_type = Column(String(20), nullable=False, comment="权限类型")
    
    # 授权者
    granted_by = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="授权人ID")
    
    # 时间限制
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self):
        return f"<KBPermission(kb_id={self.knowledge_base_id}, type='{self.permission_type}')>"


class ShareType(str, enum.Enum):
    """共享类型枚举"""
    READ_ONLY = "read_only"    # 只读
    EDITABLE = "editable"      # 可编辑
    REFERENCE = "reference"    # 引用


class KBSharing(Base):
    """
    知识库共享模型
    支持共享给学校、课程或用户
    """
    __tablename__ = "kb_sharing"
    
    id = Column(Integer, primary_key=True, index=True, comment="共享ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="知识库ID")
    
    # 共享范围（三选一）
    school_id = Column(Integer, ForeignKey("core_schools.id"), nullable=True, index=True, comment="学校ID")
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=True, index=True, comment="课程ID")
    user_id = Column(Integer, ForeignKey("core_users.id"), nullable=True, index=True, comment="用户ID")
    
    # 共享类型
    share_type = Column(String(20), default="read_only", comment="共享类型")
    
    # 共享者
    shared_by = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="共享人ID")
    
    # 时间限制
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="sharings")
    school = relationship("School")
    course = relationship("Course")
    user = relationship("User", foreign_keys=[user_id])
    sharer = relationship("User", foreign_keys=[shared_by])
    
    def __repr__(self):
        return f"<KBSharing(kb_id={self.knowledge_base_id}, type='{self.share_type}')>"

