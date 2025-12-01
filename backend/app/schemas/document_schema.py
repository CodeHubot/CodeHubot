"""
文档Schema定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# 文档 Schemas
# ============================================================================

class DocumentCreate(BaseModel):
    """创建文档Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    file_type: str = Field(..., description="文件类型：txt/md")
    author: Optional[str] = Field(None, max_length=100, description="作者")
    source: Optional[str] = Field(None, max_length=200, description="来源")
    language: str = Field("zh", description="语言")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    auto_embedding: bool = Field(True, description="是否自动向量化")
    
    @validator('file_type')
    def validate_file_type(cls, v):
        valid_types = ['txt', 'md']
        if v not in valid_types:
            raise ValueError(f'file_type必须是{valid_types}之一')
        return v


class DocumentUpdate(BaseModel):
    """更新文档Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    re_embed: bool = Field(False, description="是否重新向量化")


class DocumentResponse(BaseModel):
    """文档响应Schema"""
    id: int
    uuid: str
    knowledge_base_id: int
    knowledge_base_name: Optional[str] = None  # 冗余字段
    
    title: str
    content: Optional[str] = None  # 可选，详情时返回
    file_type: str
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    
    embedding_status: str = "pending"
    chunk_count: int = 0
    embedding_error: Optional[str] = None
    embedded_at: Optional[datetime] = None
    
    author: Optional[str] = None
    source: Optional[str] = None
    language: str = "zh"
    tags: Optional[List[str]] = []
    meta_data: Optional[Dict[str, Any]] = None
    
    uploader_id: int
    uploader_name: Optional[str] = None  # 冗余字段
    
    is_active: bool = True
    view_count: int = 0
    reference_count: int = 0
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应Schema（简化版）"""
    id: int
    uuid: str
    knowledge_base_id: int
    
    title: str
    file_type: str
    file_size: Optional[int] = None
    
    embedding_status: str = "pending"
    chunk_count: int = 0
    embedded_at: Optional[datetime] = None  # 向量化完成时间
    
    uploader_id: int
    uploader_name: Optional[str] = None
    
    view_count: int = 0
    reference_count: int = 0
    
    tags: Optional[List[str]] = []
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """文档上传响应Schema"""
    document_uuid: str
    title: str
    file_type: str
    file_size: int
    embedding_status: str
    message: str


class DocumentEmbedRequest(BaseModel):
    """文档向量化请求Schema"""
    force: bool = Field(False, description="是否强制重新向量化")
    chunk_size: Optional[int] = Field(None, ge=100, le=2000, description="文本块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=200, description="文本块重叠")


# ============================================================================
# 文本块 Schemas
# ============================================================================

class DocumentChunkResponse(BaseModel):
    """文本块响应Schema"""
    id: int
    uuid: str
    document_id: int
    knowledge_base_id: int
    
    content: str
    chunk_index: int
    char_count: Optional[int] = None
    token_count: Optional[int] = None
    
    has_embedding: bool = False  # 是否已向量化
    
    previous_chunk_id: Optional[int] = None
    next_chunk_id: Optional[int] = None
    
    meta_data: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 知识检索 Schemas
# ============================================================================

class KnowledgeSearchRequest(BaseModel):
    """知识检索请求Schema"""
    query: str = Field(..., min_length=1, description="查询文本")
    kb_uuids: Optional[List[str]] = Field(None, description="知识库UUID列表")
    top_k: int = Field(5, ge=1, le=20, description="返回数量")
    similarity_threshold: float = Field(0.70, ge=0.0, le=1.0, description="相似度阈值")
    retrieval_mode: str = Field("hybrid", description="检索模式：vector/keyword/hybrid")
    include_inherited: bool = Field(True, description="是否包含继承的知识库")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    
    @validator('retrieval_mode')
    def validate_retrieval_mode(cls, v):
        valid_modes = ['vector', 'keyword', 'hybrid']
        if v not in valid_modes:
            raise ValueError(f'retrieval_mode必须是{valid_modes}之一')
        return v


class SearchResultItem(BaseModel):
    """检索结果项Schema"""
    chunk_id: int
    chunk_uuid: str
    content: str
    similarity_score: float
    
    document_id: int
    document_uuid: str
    document_title: str
    
    knowledge_base_id: int
    knowledge_base_uuid: str
    knowledge_base_name: str
    
    meta_data: Optional[Dict[str, Any]] = None


class KnowledgeSearchResponse(BaseModel):
    """知识检索响应Schema"""
    query: str
    results: List[SearchResultItem]
    total_chunks_searched: int
    retrieval_time_ms: int
    avg_similarity: Optional[float] = None


class KeywordSearchRequest(BaseModel):
    """关键词检索请求Schema"""
    keyword: str = Field(..., min_length=1, description="关键词")
    kb_uuids: Optional[List[str]] = Field(None, description="知识库UUID列表")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

