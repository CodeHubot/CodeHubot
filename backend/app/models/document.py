"""
文档模型
包含：文档、文本块
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, BigInteger, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib
import enum


class FileType(str, enum.Enum):
    """文件类型枚举"""
    TXT = "txt"  # 纯文本
    MD = "md"    # Markdown


class EmbeddingStatus(str, enum.Enum):
    """向量化状态枚举"""
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class Document(Base):
    """
    文档模型
    仅支持TXT和Markdown格式
    """
    __tablename__ = "kb_documents"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="文档ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="所属知识库ID")
    
    # 文档基本信息
    title = Column(String(200), nullable=False, comment="文档标题")
    content = Column(Text, comment="文档内容（纯文本）")
    file_type = Column(String(10), nullable=False, index=True, comment="文件类型")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    file_url = Column(String(500), comment="文件存储路径")
    file_hash = Column(String(64), index=True, comment="文件MD5哈希")
    
    # 向量化状态
    embedding_status = Column(String(20), default="pending", index=True, comment="向量化状态")
    chunk_count = Column(Integer, default=0, comment="文本块数量")
    embedding_error = Column(Text, comment="向量化失败原因")
    embedded_at = Column(DateTime, comment="向量化完成时间")
    
    # 元数据
    author = Column(String(100), comment="作者")
    source = Column(String(200), comment="来源")
    language = Column(String(20), default="zh", comment="语言")
    tags = Column(JSON, comment="标签")
    meta_data = Column(JSON, comment="扩展元数据")
    
    # 上传者
    uploader_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, index=True, comment="上传者用户ID")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活")
    view_count = Column(Integer, default=0, comment="查看次数")
    reference_count = Column(Integer, default=0, comment="被引用次数")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploader_id])
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', type='{self.file_type}')>"


class DocumentChunk(Base):
    """
    文本块模型
    用于向量检索
    """
    __tablename__ = "kb_document_chunks"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="文本块ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    document_id = Column(Integer, ForeignKey("kb_documents.id"), nullable=False, index=True, comment="所属文档ID")
    knowledge_base_id = Column(Integer, ForeignKey("kb_main.id"), nullable=False, index=True, comment="所属知识库ID")
    
    # 文本内容
    content = Column(Text, nullable=False, comment="文本块内容")
    chunk_index = Column(Integer, nullable=False, comment="在文档中的顺序")
    char_count = Column(Integer, comment="字符数")
    token_count = Column(Integer, comment="Token数")
    
    # 向量（存储在MySQL的JSON字段）
    embedding_vector = Column(JSON, comment="向量表示（JSON数组）")
    
    # 上下文信息
    previous_chunk_id = Column(Integer, ForeignKey("kb_document_chunks.id"), nullable=True, comment="上一个文本块ID")
    next_chunk_id = Column(Integer, ForeignKey("kb_document_chunks.id"), nullable=True, comment="下一个文本块ID")
    
    # 元数据
    meta_data = Column(JSON, comment="扩展元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")
    previous_chunk = relationship("DocumentChunk", remote_side=[id], foreign_keys=[previous_chunk_id])
    next_chunk = relationship("DocumentChunk", remote_side=[id], foreign_keys=[next_chunk_id])
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"

