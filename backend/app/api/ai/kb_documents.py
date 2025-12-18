"""
知识库文档管理API
提供文档的上传、查询、更新、删除、向量化等操作
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime
import hashlib
import os
import asyncio
import logging
import re
from pathlib import Path

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentChunk
from app.schemas.document_schema import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    DocumentUploadResponse, DocumentEmbedRequest, DocumentChunkResponse
)
from app.utils.timezone import get_beijing_time_naive

router = APIRouter()

# 日志记录器
logger = logging.getLogger(__name__)

# 文件存储根目录（支持环境变量配置，兼容不同容器的工作目录）
import os
UPLOAD_DIR = Path(os.getenv('KNOWLEDGE_BASE_STORAGE', 'data/knowledge-bases'))
# 如果是相对路径，转换为绝对路径（基于backend目录）
if not UPLOAD_DIR.is_absolute():
    # 尝试从backend目录解析
    backend_dir = Path(__file__).parent.parent.parent  # 从 app/api/kb_documents.py 到 backend/
    UPLOAD_DIR = backend_dir / UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 文件大小限制（1MB）- 防止消耗过多系统资源
MAX_FILE_SIZE = 1 * 1024 * 1024


# ============================================================================
# 辅助函数
# ============================================================================

def check_kb_write_permission(user: User, kb: KnowledgeBase, db: Session) -> bool:
    """检查用户对知识库的写入权限（简化版）"""
    # 导入权限检查函数
    from app.api.ai.knowledge_bases import check_kb_permission
    return check_kb_permission(user, kb, 'write', db)


def calculate_file_hash(content: bytes) -> str:
    """计算文件MD5哈希"""
    return hashlib.md5(content).hexdigest()


def save_file_to_disk(kb_uuid: str, doc_uuid: str, file_content: bytes, file_type: str) -> str:
    """
    保存文件到本地磁盘
    
    Returns:
        str: 文件相对路径
    """
    # 创建知识库目录
    kb_dir = UPLOAD_DIR / kb_uuid
    kb_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件路径
    filename = f"{doc_uuid}.{file_type}"
    file_path = kb_dir / filename
    
    # 写入文件
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # 返回相对路径
    return f"{kb_uuid}/{filename}"


def read_file_from_disk(file_url: str) -> bytes:
    """从本地磁盘读取文件"""
    file_path = UPLOAD_DIR / file_url
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_url}")
    
    with open(file_path, 'rb') as f:
        return f.read()


def parse_text_file(file_content: bytes, file_type: str) -> str:
    """
    解析文本文件（使用增强的编码检测）
    
    Args:
        file_content: 文件内容（bytes）
        file_type: 文件类型（txt/md）
    
    Returns:
        str: 文件内容（文本）
    
    Raises:
        ValueError: 如果文件编码无法识别或包含过多乱码
    """
    from app.utils.document_parser import get_parser
    
    try:
        # 使用文档解析器的增强编码处理
        parser = get_parser(file_type)
        text = parser.parse(file_content)
        return text
    except ValueError as e:
        # 编码错误，抛出明确的错误信息
        logger.error(f"文件解析失败: {str(e)}")
        raise
    except Exception as e:
        # 其他错误
        logger.error(f"文件解析异常: {str(e)}")
        raise ValueError(f"文件解析失败: {str(e)}")


def run_document_embedding(document_id: int):
    """
    后台任务：执行文档向量化
    
    Args:
        document_id: 文档ID
    """
    # 确保加载环境变量（后台任务需要）
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)  # 不覆盖已存在的环境变量
    except ImportError:
        pass  # python-dotenv 未安装，跳过
    
    from app.core.database import SessionLocal
    from app.services.embedding_service import embed_document
    
    # 创建新的数据库会话
    db = SessionLocal()
    
    try:
        # 执行向量化（异步函数需要在新的事件循环中运行）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(embed_document(document_id, db))
            logger.info(f"文档 {document_id} 向量化完成")
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"文档 {document_id} 向量化失败: {str(e)}")
    finally:
        db.close()


# ============================================================================
# 文档管理API
# ============================================================================

@router.post("/{kb_uuid}/preview", response_model=dict)
async def preview_document_chunks(
    kb_uuid: str,
    file: UploadFile = File(...),
    split_mode: str = Form("fixed"),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览文档切分结果（不保存，不向量化）"""
    
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    if not check_kb_write_permission(current_user, kb, db):
        return error_response(message="无权上传文档到该知识库", code=403)
    
    # 检查文件
    if not file.filename:
        return error_response(message="文件名不能为空", code=400)
    
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in ['txt', 'md']:
        return error_response(message="只支持TXT和Markdown格式", code=400)
    
    # 读取文件
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        return error_response(message=f"文件大小超过限制（最大1MB）", code=400)
    
    if file_size == 0:
        return error_response(message="文件内容为空", code=400)
    
    # 检测文件编码
    from app.utils.document_parser import DocumentParser
    detected_encoding, encoding_confidence = DocumentParser.detect_encoding(
        file_content, return_confidence=True
    )
    logger.info(f"文件 {file.filename} 编码: {detected_encoding} (置信度: {encoding_confidence:.2%})")
    
    # 解析并切分文档（一次性完成，避免重复解析）
    try:
        from app.utils.document_parser import parse_and_split_document
        
        # 确定切分参数
        # 对于段落切分模式，不需要 chunk_size 和 chunk_overlap
        if split_mode in ['paragraph', 'paragraph_double']:
            use_chunk_size = 500  # 仅用于初始化，实际不使用
            use_chunk_overlap = 50  # 仅用于初始化，实际不使用
        else:
            use_chunk_size = chunk_size if (split_mode == 'custom' and chunk_size) else (kb.chunk_size or 500)
            use_chunk_overlap = chunk_overlap if (split_mode == 'custom' and chunk_overlap) else (kb.chunk_overlap or 50)
        
        logger.info(f"预览切分 - 文件: {file.filename}, 模式: {split_mode}, chunk_size: {use_chunk_size}, chunk_overlap: {use_chunk_overlap}")
        
        # ✅ 只解析一次，同时获取文本和切分结果
        content, chunks_data = parse_and_split_document(
            file_content,
            file_ext,
            use_chunk_size,
            use_chunk_overlap,
            split_mode
        )
        
        logger.info(f"文档切分完成: 总共 {len(chunks_data)} 个文本块")
    except ValueError as e:
        # 编码错误，返回详细信息
        logger.error(f"文件解析失败: {str(e)}")
        return error_response(
            message=f"文件编码错误: {str(e)}",
            code=400,
            data={
                'detected_encoding': detected_encoding,
                'confidence': f"{encoding_confidence:.1%}",
                'suggestion': '请使用 UTF-8 编码保存文件，或使用"记事本"等工具转换编码后重试'
            }
        )
    except Exception as e:
        logger.error(f"文件解析或切分失败: {str(e)}", exc_info=True)
        return error_response(message=f"文件处理失败: {str(e)}", code=400)
    
    # ✅ 构建预览数据（移到 try-except 外部）
    try:
        preview_chunks = []
        for chunk in chunks_data[:50]:  # 最多预览前50个块
            preview_chunks.append({
                'chunk_index': chunk['chunk_index'],
                'content': chunk['content'],
                'content_preview': chunk['content'][:200] + ('...' if len(chunk['content']) > 200 else ''),
                'char_count': chunk['char_count'],
                'token_count': chunk['token_count']
            })
        
        # 计算文本统计信息
        total_chars = len(content)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        return success_response(data={
            'file_name': file.filename,
            'file_size': file_size,
            'file_type': file_ext,
            'file_encoding': detected_encoding,
            'encoding_confidence': f"{encoding_confidence:.1%}",
            'content_stats': {
                'total_chars': total_chars,
                'chinese_chars': chinese_chars,
                'english_chars': english_chars
            },
            'total_chunks': len(chunks_data),
            'preview_chunks': preview_chunks,
            'split_config': {
                'split_mode': split_mode,
                'chunk_size': use_chunk_size,
                'chunk_overlap': use_chunk_overlap
            },
            'is_preview_only': True  # 标记这只是预览
        }, message=f"文档切分预览成功（编码: {detected_encoding}）")
    except Exception as e:
        logger.error(f"构建预览数据失败: {str(e)}", exc_info=True)
        return error_response(message=f"生成预览失败: {str(e)}", code=500)


@router.post("/{kb_uuid}", response_model=dict)
async def upload_document(
    kb_uuid: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON字符串
    auto_embedding: bool = Form(True),
    split_mode: str = Form("fixed"),  # 切分方式: fixed/paragraph/paragraph_double/sentence/custom
    chunk_size: Optional[int] = Form(None),  # 自定义块大小
    chunk_overlap: Optional[int] = Form(None),  # 自定义重叠大小
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档到知识库"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    if not check_kb_write_permission(current_user, kb, db):
        return error_response(message="无权上传文档到该知识库", code=403)
    
    # 检查文件类型
    if not file.filename:
        return error_response(message="文件名不能为空", code=400)
    
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in ['txt', 'md']:
        return error_response(message="只支持TXT和Markdown格式", code=400)
    
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)
    
    # 检查文件大小
    if file_size > MAX_FILE_SIZE:
        return error_response(message=f"文件大小超过限制（最大1MB）", code=400)
    
    if file_size == 0:
        return error_response(message="文件内容为空", code=400)
    
    # 转换 auto_embedding（Form接收的是字符串）
    auto_embedding_bool = auto_embedding.lower() in ('true', '1', 'yes', 'on') if isinstance(auto_embedding, str) else bool(auto_embedding)
    
    # 计算文件哈希
    file_hash = calculate_file_hash(file_content)
    
    # 检查重复
    existing_doc = db.query(Document).filter(
        Document.knowledge_base_id == kb.id,
        Document.file_hash == file_hash,
        Document.deleted_at.is_(None)
    ).first()
    
    if existing_doc:
        return error_response(message=f"文档已存在：{existing_doc.title}", code=400)
    
    # 解析文件内容
    try:
        content = parse_text_file(file_content, file_ext)
    except Exception as e:
        return error_response(message=f"文件解析失败: {str(e)}", code=400)
    
    # 准备切分参数的metadata
    import json
    split_config = {
        'split_mode': split_mode,
        'chunk_size': chunk_size if split_mode == 'custom' and chunk_size else None,
        'chunk_overlap': chunk_overlap if split_mode == 'custom' and chunk_overlap else None
    }
    
    # 创建文档记录
    doc = Document(
        knowledge_base_id=kb.id,
        title=title or file.filename,
        content=content,
        file_type=file_ext,
        file_size=file_size,
        file_hash=file_hash,
        author=author,
        language='zh',
        uploader_id=current_user.id,
        embedding_status='pending' if auto_embedding_bool else 'completed',
        meta_data=split_config  # 保存切分配置
    )
    
    # 处理标签
    if tags:
        try:
            doc.tags = json.loads(tags) if isinstance(tags, str) else tags
        except:
            doc.tags = []
    
    db.add(doc)
    db.flush()  # 获取doc.id
    
    # 保存文件到磁盘
    try:
        file_url = save_file_to_disk(kb.uuid, doc.uuid, file_content, file_ext)
        doc.file_url = file_url
    except Exception as e:
        db.rollback()
        return error_response(message=f"文件保存失败: {str(e)}", code=500)
    
    # 更新知识库统计
    kb.document_count = (kb.document_count or 0) + 1
    kb.total_size = (kb.total_size or 0) + file_size
    kb.last_updated_at = get_beijing_time_naive()
    
    db.commit()
    db.refresh(doc)
    
    # 保存文档ID用于后台任务
    doc_id = doc.id
    
    # 如果需要自动向量化，使用 Celery 任务
    if auto_embedding_bool:
        try:
            # 尝试使用 Celery 任务（更稳定）
            from app.tasks.embedding_tasks import embed_document_task
            task = embed_document_task.delay(doc_id)
            logger.info(f"已提交 Celery 向量化任务: doc={doc.uuid}, task_id={task.id}")
        except Exception as e:
            # 如果 Celery 不可用，回退到后台任务
            logger.warning(f"Celery 任务提交失败，使用后台任务: {str(e)}")
            background_tasks.add_task(run_document_embedding, doc_id)
            logger.info(f"已添加后台向量化任务: {doc.uuid}")
    
    response_data = DocumentUploadResponse(
        document_uuid=doc.uuid,
        title=doc.title,
        file_type=doc.file_type,
        file_size=doc.file_size,
        embedding_status=doc.embedding_status,
        message="文档上传成功"
    )
    
    return success_response(data=response_data.model_dump(), message="文档上传成功")


@router.get("/{kb_uuid}", response_model=dict)
async def list_documents(
    kb_uuid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    embedding_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档列表"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    from app.api.ai.knowledge_bases import check_kb_permission
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权查看该知识库", code=403)
    
    # 构建查询
    query = db.query(Document).filter(
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    )
    
    # 筛选条件
    if keyword:
        query = query.filter(
            or_(
                Document.title.like(f"%{keyword}%"),
                Document.content.like(f"%{keyword}%")
            )
        )
    
    if file_type:
        query = query.filter(Document.file_type == file_type)
    
    if embedding_status:
        query = query.filter(Document.embedding_status == embedding_status)
    
    # 总数
    total = query.count()
    
    # 分页
    documents = query.order_by(Document.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    doc_list = []
    for doc in documents:
        doc_dict = DocumentListResponse.from_orm(doc).model_dump()
        
        # 添加上传者姓名
        uploader = db.query(User).filter(User.id == doc.uploader_id).first()
        doc_dict['uploader_name'] = uploader.real_name or uploader.name or uploader.username if uploader else None
        
        doc_list.append(doc_dict)
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "documents": doc_list
    })


@router.get("/{kb_uuid}/{doc_uuid}", response_model=dict)
async def get_document(
    kb_uuid: str,
    doc_uuid: str,
    include_content: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档详情"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        return error_response(message="文档不存在", code=404)
    
    # 权限检查
    from app.api.ai.knowledge_bases import check_kb_permission
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权查看该文档", code=403)
    
    # 转换为响应格式
    doc_dict = DocumentResponse.from_orm(doc).model_dump()
    
    # 添加知识库名称
    doc_dict['knowledge_base_name'] = kb.name
    
    # 添加上传者姓名
    uploader = db.query(User).filter(User.id == doc.uploader_id).first()
    doc_dict['uploader_name'] = uploader.real_name or uploader.name or uploader.username if uploader else None
    
    # 如果不需要完整内容，移除content字段
    if not include_content:
        doc_dict.pop('content', None)
    
    # 增加查看次数
    doc.view_count = (doc.view_count or 0) + 1
    db.commit()
    
    return success_response(data=doc_dict)


@router.put("/{kb_uuid}/{doc_uuid}", response_model=dict)
async def update_document(
    kb_uuid: str,
    doc_uuid: str,
    doc_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文档"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        return error_response(message="文档不存在", code=404)
    
    # 权限检查
    if not check_kb_write_permission(current_user, kb, db):
        return error_response(message="无权编辑该文档", code=403)
    
    # 更新字段
    update_data = doc_data.model_dump(exclude_unset=True, exclude={'re_embed'})
    for field, value in update_data.items():
        if hasattr(doc, field):
            setattr(doc, field, value)
    
    # 如果内容有更新且需要重新向量化
    if doc_data.re_embed and doc_data.content:
        doc.embedding_status = 'pending'
        doc.embedded_at = None
        # TODO: 触发重新向量化任务
    
    db.commit()
    
    return success_response(message="文档更新成功")


@router.delete("/{kb_uuid}/{doc_uuid}", response_model=dict)
async def delete_document(
    kb_uuid: str,
    doc_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文档"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        return error_response(message="文档不存在", code=404)
    
    # 权限检查
    if not check_kb_write_permission(current_user, kb, db):
        return error_response(message="无权删除该文档", code=403)
    
    # 软删除文档
    doc.deleted_at = get_beijing_time_naive()
    
    # 直接删除所有文本块（文本块没有 deleted_at 字段）
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc.id
    ).delete()
    
    # 更新知识库统计
    kb.document_count = max(0, (kb.document_count or 0) - 1)
    kb.chunk_count = max(0, (kb.chunk_count or 0) - (doc.chunk_count or 0))
    kb.total_size = max(0, (kb.total_size or 0) - (doc.file_size or 0))
    kb.last_updated_at = get_beijing_time_naive()
    
    db.commit()
    
    return success_response(message="文档已删除")


@router.post("/{kb_uuid}/{doc_uuid}/embed", response_model=dict)
async def trigger_embedding(
    kb_uuid: str,
    doc_uuid: str,
    embed_request: DocumentEmbedRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发文档向量化"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        return error_response(message="文档不存在", code=404)
    
    # 权限检查
    if not check_kb_write_permission(current_user, kb, db):
        return error_response(message="无权操作该文档", code=403)
    
    # 检查是否需要强制重新向量化
    if not embed_request.force and doc.embedding_status == 'completed':
        return error_response(message="文档已完成向量化，如需重新处理请设置force=true", code=400)
    
    # 更新状态
    doc.embedding_status = 'pending'
    doc.embedded_at = None
    doc.embedding_error = None
    
    db.commit()
    
    # 保存文档ID用于后台任务
    doc_id = doc.id
    
    # 使用 Celery 任务进行向量化
    try:
        from app.tasks.embedding_tasks import embed_document_task
        task = embed_document_task.delay(doc_id)
        logger.info(f"已提交 Celery 向量化任务: doc={doc.uuid}, task_id={task.id}")
        return success_response(
            data={'task_id': task.id},
            message="向量化任务已提交到队列，正在后台处理"
        )
    except Exception as e:
        # 如果 Celery 不可用，回退到后台任务
        logger.warning(f"Celery 任务提交失败，使用后台任务: {str(e)}")
        background_tasks.add_task(run_document_embedding, doc_id)
        logger.info(f"已添加后台向量化任务: {doc.uuid}")
        return success_response(message="向量化任务已提交，正在后台处理")


@router.get("/{kb_uuid}/{doc_uuid}/chunks", response_model=dict)
async def list_document_chunks(
    kb_uuid: str,
    doc_uuid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档的文本块列表"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        return error_response(message="文档不存在", code=404)
    
    # 权限检查
    from app.api.ai.knowledge_bases import check_kb_permission
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权查看该文档", code=403)
    
    # 查询文本块
    query = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc.id
    )
    
    total = query.count()
    
    chunks = query.order_by(DocumentChunk.chunk_index)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    chunk_list = []
    for chunk in chunks:
        chunk_dict = DocumentChunkResponse.from_orm(chunk).model_dump()
        chunk_dict['has_embedding'] = chunk.embedding_vector is not None
        chunk_list.append(chunk_dict)
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": chunk_list  # 使用 items 保持与其他列表API一致
    })


@router.get("/{kb_uuid}/{doc_uuid}/download")
async def download_document(
    kb_uuid: str,
    doc_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载文档原文件"""
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 获取文档
    doc = db.query(Document).filter(
        Document.uuid == doc_uuid,
        Document.knowledge_base_id == kb.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 权限检查
    from app.api.ai.knowledge_bases import check_kb_permission
    if not check_kb_permission(current_user, kb, 'read', db):
        raise HTTPException(status_code=403, detail="无权下载该文档")
    
    # 读取文件
    try:
        file_content = read_file_from_disk(doc.file_url)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件下载
    from io import BytesIO
    media_type = 'text/markdown' if doc.file_type == 'md' else 'text/plain'
    
    return StreamingResponse(
        BytesIO(file_content),
        media_type=media_type,
        headers={
            'Content-Disposition': f'attachment; filename={doc.title}'
        }
    )


@router.post("/{kb_uuid}/search", response_model=dict)
async def search_knowledge_base(
    kb_uuid: str,
    query: str = Query(..., description="搜索查询文本"),
    top_k: int = Query(5, ge=1, le=20, description="返回结果数量"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值（0-1），低于此值的结果将被过滤，默认0.7"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    向量检索：在知识库中搜索相关内容
    
    功能：
    - 将查询文本向量化
    - 计算与文档块的相似度
    - 返回最相关的文档块
    """
    logger.info(f"向量检索: kb={kb_uuid}, query={query[:50]}..., top_k={top_k}")
    
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    from app.api.ai.knowledge_bases import check_kb_permission
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权访问该知识库", code=403)
    
    # 检查知识库是否有向量化的文档
    chunk_count = db.query(func.count(DocumentChunk.id)).filter(
        DocumentChunk.knowledge_base_id == kb.id,
        DocumentChunk.embedding_vector.isnot(None)
    ).scalar()
    
    if chunk_count == 0:
        return success_response(
            data={
                "query": query,
                "results": [],
                "total": 0,
                "message": "知识库中暂无已向量化的内容"
            }
        )
    
    # 从知识库配置中读取相似度阈值，如果没有则使用传入的参数或默认值
    if similarity_threshold == 0.7:  # 如果使用默认值，尝试从配置读取
        if kb.retrieval_config and isinstance(kb.retrieval_config, dict):
            config_threshold = kb.retrieval_config.get('similarity_threshold')
            if config_threshold is not None:
                similarity_threshold = float(config_threshold)
                logger.info(f"使用知识库配置的相似度阈值: {similarity_threshold}")
    
    try:
        # 1. 查询扩展（为智能家居等场景添加同义词和场景词）
        from app.utils.query_expander import expand_query
        expanded_query = expand_query(query, domain='smart_home', mode='embedding')
        if expanded_query != query:
            logger.info(f"查询扩展: '{query}' -> '{expanded_query}'")
        
        # 2. 对扩展后的查询文本进行向量化
        from app.services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        
        logger.info(f"开始向量化查询文本...")
        query_vector = await embedding_service.embed_text(expanded_query)
        
        if not query_vector:
            return error_response(message="查询文本向量化失败，请稍后重试", code=500)
        
        logger.info(f"查询文本向量化成功，向量维度: {len(query_vector)}")
        
        # 2. 获取所有有向量的文档块
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_base_id == kb.id,
            DocumentChunk.embedding_vector.isnot(None)
        ).all()
        
        logger.info(f"找到 {len(chunks)} 个已向量化的文档块")
        
        # 4. 计算相似度（使用embedding_service的统一方法）
        results = []
        similarities = []  # 用于统计
        
        for chunk in chunks:
            if chunk.embedding_vector:
                # 使用embedding_service的calculate_similarity方法（已归一化到0-1）
                similarity = embedding_service.calculate_similarity(
                    query_vector,
                    chunk.embedding_vector
                )
                similarities.append(similarity)
                
                results.append({
                    'chunk': chunk,
                    'similarity': float(similarity)
                })
        
        # 5. 相似度统计
        if similarities:
            max_sim = max(similarities)
            min_sim = min(similarities)
            avg_sim = sum(similarities) / len(similarities)
            logger.info(f"相似度统计 - 最高:{max_sim:.4f}, 最低:{min_sim:.4f}, 平均:{avg_sim:.4f}, 总数:{len(similarities)}")
            
            # 输出Top5相似度
            top5 = sorted(similarities, reverse=True)[:5]
            logger.info(f"Top5相似度: {[f'{s:.4f}' for s in top5]}")
        
        # 6. 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 7. 应用相似度阈值过滤
        filtered_results = [r for r in results if r['similarity'] >= similarity_threshold]
        
        if filtered_results:
            logger.info(f"阈值过滤后剩余 {len(filtered_results)} 个结果（阈值: {similarity_threshold}）")
        else:
            # 如果没有结果超过阈值，尝试降低阈值（降低10%）再过滤一次
            fallback_threshold = max(0.5, similarity_threshold - 0.1)
            filtered_results = [r for r in results if r['similarity'] >= fallback_threshold]
            
            if filtered_results:
                logger.warning(f"使用降级阈值 {fallback_threshold}，找到 {len(filtered_results)} 个结果")
            else:
                logger.warning(f"所有结果都低于阈值 {similarity_threshold}，返回最高相似度的结果")
                # 如果降级后仍没有结果，至少返回最高相似度的结果
                filtered_results = results[:1] if results else []
        
        # 8. 取前 top_k 个
        top_results = filtered_results[:top_k]
        
        if top_results:
            logger.info(f"最终返回 {len(top_results)} 个结果，最高相似度: {top_results[0]['similarity']:.4f}")
        
        # 5. 构建响应数据
        result_list = []
        for item in top_results:
            chunk = item['chunk']
            # 获取文档信息
            doc = db.query(Document).filter(Document.id == chunk.document_id).first()
            
            result_list.append({
                'chunk_id': chunk.id,
                'chunk_uuid': chunk.uuid,
                'chunk_index': chunk.chunk_index,
                'content': chunk.content,
                'char_count': chunk.char_count,
                'token_count': chunk.token_count,
                'similarity': round(item['similarity'], 4),
                'similarity_percent': f"{item['similarity'] * 100:.2f}%",
                'document': {
                    'id': doc.id,
                    'uuid': doc.uuid,
                    'title': doc.title,
                    'file_type': doc.file_type
                } if doc else None,
                'created_at': chunk.created_at.isoformat() if chunk.created_at else None
            })
        
        return success_response(data={
            "query": query,
            "results": result_list,
            "total": len(result_list),
            "searched_chunks": len(chunks),
            "kb_info": {
                "name": kb.name,
                "document_count": kb.document_count,
                "chunk_count": kb.chunk_count
            }
        })
        
    except Exception as e:
        logger.error(f"向量检索失败: {str(e)}", exc_info=True)
        return error_response(message=f"检索失败: {str(e)}", code=500)

