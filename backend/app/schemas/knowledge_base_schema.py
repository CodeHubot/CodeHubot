"""
知识库Schema定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# 知识库 Schemas
# ============================================================================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    icon: Optional[str] = Field(None, max_length=200, description="图标URL")
    
    scope_type: str = Field(..., description="作用域类型：system/team/course/agent/personal")
    scope_id: Optional[int] = Field(None, description="作用域ID")
    parent_kb_id: Optional[int] = Field(None, description="父知识库ID")
    
    access_level: Optional[str] = Field(None, description="访问级别（可选，系统自动设置）：public/protected/private")
    
    chunk_size: int = Field(500, ge=100, le=2000, description="文本块大小")
    chunk_overlap: int = Field(50, ge=0, le=200, description="文本块重叠大小")
    embedding_model_id: Optional[int] = Field(None, description="Embedding模型ID")
    
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    
    @validator('scope_type')
    def validate_scope_type(cls, v):
        valid_types = ['system', 'team', 'course', 'agent', 'personal']
        if v not in valid_types:
            raise ValueError(f'scope_type必须是{valid_types}之一')
        return v
    
    @validator('access_level')
    def validate_access_level(cls, v):
        valid_levels = ['public', 'protected', 'private']
        if v not in valid_levels:
            raise ValueError(f'access_level必须是{valid_levels}之一')
        return v


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    access_level: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=200)
    embedding_model_id: Optional[int] = None
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    retrieval_config: Optional[Dict[str, Any]] = Field(None, description="检索配置，包含similarity_threshold等")
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应Schema"""
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    
    scope_type: str
    scope_id: Optional[int] = None
    scope_name: Optional[str] = None  # 冗余字段，便于前端显示
    parent_kb_id: Optional[int] = None
    
    owner_id: int
    owner_name: Optional[str] = None  # 冗余字段
    access_level: str
    
    document_count: int = 0
    chunk_count: int = 0
    total_size: int = 0
    last_updated_at: Optional[datetime] = None
    
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model_id: Optional[int] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    
    is_active: bool = True
    is_system: bool = False
    tags: Optional[List[str]] = []
    meta_data: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应Schema（简化版）"""
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    
    scope_type: str
    scope_id: Optional[int] = None
    scope_name: Optional[str] = None
    
    owner_id: int
    owner_name: Optional[str] = None
    access_level: str
    
    document_count: int = 0
    chunk_count: int = 0
    total_size: int = 0
    last_updated_at: Optional[datetime] = None
    
    is_active: bool = True
    is_system: bool = False
    is_inherited: bool = False  # 是否继承的知识库
    tags: Optional[List[str]] = []
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseStatistics(BaseModel):
    """知识库统计Schema"""
    total_kbs: int
    system_kbs: int
    team_kbs: int
    course_kbs: int
    agent_kbs: int
    total_documents: int
    total_chunks: int
    total_size: int


# ============================================================================
# 智能体知识库关联 Schemas
# ============================================================================

class AgentKnowledgeBaseCreate(BaseModel):
    """创建智能体知识库关联Schema"""
    knowledge_base_uuid: str = Field(..., description="知识库UUID")
    priority: int = Field(0, description="优先级")
    is_enabled: bool = Field(True, description="是否启用")
    top_k: int = Field(5, ge=1, le=20, description="检索返回数量")
    similarity_threshold: Decimal = Field(0.70, ge=0.0, le=1.0, description="相似度阈值")
    retrieval_mode: str = Field("hybrid", description="检索模式：vector/keyword/hybrid")
    
    @validator('retrieval_mode')
    def validate_retrieval_mode(cls, v):
        valid_modes = ['vector', 'keyword', 'hybrid']
        if v not in valid_modes:
            raise ValueError(f'retrieval_mode必须是{valid_modes}之一')
        return v


class AgentKnowledgeBaseUpdate(BaseModel):
    """更新智能体知识库关联Schema"""
    priority: Optional[int] = None
    is_enabled: Optional[bool] = None
    top_k: Optional[int] = Field(None, ge=1, le=20)
    similarity_threshold: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    retrieval_mode: Optional[str] = None


class AgentKnowledgeBaseResponse(BaseModel):
    """智能体知识库关联响应Schema"""
    id: int
    agent_id: int
    knowledge_base_id: int
    knowledge_base_uuid: str
    knowledge_base_name: str
    
    priority: int = 0
    is_enabled: bool = True
    top_k: int = 5
    similarity_threshold: Decimal = Decimal("0.70")
    retrieval_mode: str = "hybrid"
    
    document_count: int = 0  # 冗余字段
    is_inherited: bool = False  # 是否继承的知识库
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# 知识库权限 Schemas
# ============================================================================

class KBPermissionCreate(BaseModel):
    """创建知识库权限Schema"""
    user_id: Optional[int] = Field(None, description="用户ID（与role二选一）")
    role: Optional[str] = Field(None, description="角色（与user_id二选一）")
    permission_type: str = Field(..., description="权限类型：read/write/manage/admin")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @validator('permission_type')
    def validate_permission_type(cls, v):
        valid_types = ['read', 'write', 'manage', 'admin']
        if v not in valid_types:
            raise ValueError(f'permission_type必须是{valid_types}之一')
        return v


class KBPermissionResponse(BaseModel):
    """知识库权限响应Schema"""
    id: int
    knowledge_base_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None  # 冗余字段
    role: Optional[str] = None
    permission_type: str
    granted_by: int
    granter_name: Optional[str] = None  # 冗余字段
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 知识库共享 Schemas
# ============================================================================

class KBSharingCreate(BaseModel):
    """创建知识库共享Schema"""
    team_id: Optional[int] = Field(None, description="团队ID（三选一）")
    course_id: Optional[int] = Field(None, description="课程ID（三选一）")
    user_id: Optional[int] = Field(None, description="用户ID（三选一）")
    share_type: str = Field("read_only", description="共享类型：read_only/editable/reference")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @validator('share_type')
    def validate_share_type(cls, v):
        valid_types = ['read_only', 'editable', 'reference']
        if v not in valid_types:
            raise ValueError(f'share_type必须是{valid_types}之一')
        return v


class KBSharingResponse(BaseModel):
    """知识库共享响应Schema"""
    id: int
    knowledge_base_id: int
    team_id: Optional[int] = None
    team_name: Optional[str] = None  # 冗余字段
    course_id: Optional[int] = None
    course_name: Optional[str] = None  # 冗余字段
    user_id: Optional[int] = None
    user_name: Optional[str] = None  # 冗余字段
    share_type: str
    shared_by: int
    sharer_name: Optional[str] = None  # 冗余字段
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

