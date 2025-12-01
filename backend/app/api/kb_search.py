"""
知识库检索API
提供向量检索、关键词检索、混合检索等功能
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
import time

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentChunk
from app.schemas.document_schema import KnowledgeSearchRequest, KnowledgeSearchResponse, SearchResultItem
from app.services.embedding_service import get_embedding_service
from app.utils.timezone import get_beijing_time_naive

router = APIRouter()


def get_accessible_kb_ids(user: User, db: Session) -> List[int]:
    """获取用户可访问的知识库ID列表"""
    from app.api.knowledge_bases import check_kb_permission
    
    # 平台管理员可访问所有
    if user.role == 'platform_admin':
        kbs = db.query(KnowledgeBase.id).filter(
            KnowledgeBase.deleted_at.is_(None)
        ).all()
        return [kb_id for kb_id, in kbs]
    
    accessible_ids = []
    
    # 查询所有知识库（简化版，实际应该更智能）
    all_kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.deleted_at.is_(None)
    ).all()
    
    for kb in all_kbs:
        if check_kb_permission(user, kb, 'read', db):
            accessible_ids.append(kb.id)
    
    return accessible_ids


async def vector_search(
    query: str,
    kb_ids: List[int],
    top_k: int,
    similarity_threshold: float,
    db: Session
) -> List[dict]:
    """
    向量检索
    
    Args:
        query: 查询文本
        kb_ids: 知识库ID列表
        top_k: 返回数量
        similarity_threshold: 相似度阈值
        db: 数据库会话
    
    Returns:
        List[dict]: 检索结果列表
    """
    # 获取Embedding服务
    embedding_service = get_embedding_service()
    
    # 对查询进行向量化
    query_embedding = await embedding_service.embed_text(query)
    if not query_embedding:
        return []
    
    # 查询所有相关文本块
    chunks = db.query(DocumentChunk).join(
        Document, DocumentChunk.document_id == Document.id
    ).filter(
        DocumentChunk.knowledge_base_id.in_(kb_ids),
        DocumentChunk.embedding_vector.isnot(None),
        Document.deleted_at.is_(None),
        Document.is_active == 1
    ).all()
    
    # 计算相似度
    results = []
    for chunk in chunks:
        if chunk.embedding_vector:
            # 从JSON中提取向量
            chunk_embedding = chunk.embedding_vector
            
            # 计算余弦相似度
            similarity = embedding_service.calculate_similarity(
                query_embedding,
                chunk_embedding
            )
            
            # 过滤低于阈值的结果
            if similarity >= similarity_threshold:
                # 获取文档和知识库信息
                doc = db.query(Document).filter(Document.id == chunk.document_id).first()
                kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == chunk.knowledge_base_id).first()
                
                if doc and kb:
                    results.append({
                        'chunk': chunk,
                        'document': doc,
                        'knowledge_base': kb,
                        'similarity_score': similarity
                    })
    
    # 按相似度排序并取topK
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:top_k]


def keyword_search(
    query: str,
    kb_ids: List[int],
    top_k: int,
    db: Session
) -> List[dict]:
    """
    关键词检索
    
    Args:
        query: 查询文本
        kb_ids: 知识库ID列表
        top_k: 返回数量
        db: 数据库会话
    
    Returns:
        List[dict]: 检索结果列表
    """
    # 查询包含关键词的文本块
    chunks = db.query(DocumentChunk).join(
        Document, DocumentChunk.document_id == Document.id
    ).filter(
        DocumentChunk.knowledge_base_id.in_(kb_ids),
        DocumentChunk.content.like(f"%{query}%"),
        Document.deleted_at.is_(None),
        Document.is_active == 1
    ).limit(top_k * 2).all()  # 多取一些，后续可以排序
    
    results = []
    for chunk in chunks:
        # 获取文档和知识库信息
        doc = db.query(Document).filter(Document.id == chunk.document_id).first()
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == chunk.knowledge_base_id).first()
        
        if doc and kb:
            # 简单的相关性评分（关键词出现次数）
            keyword_count = chunk.content.lower().count(query.lower())
            score = min(1.0, keyword_count * 0.2)  # 简单归一化
            
            results.append({
                'chunk': chunk,
                'document': doc,
                'knowledge_base': kb,
                'similarity_score': score
            })
    
    # 按评分排序
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:top_k]


@router.post("/search", response_model=dict)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """知识库检索"""
    start_time = time.time()
    
    # 确定检索范围
    if search_request.kb_uuids:
        # 指定知识库UUID
        kbs = db.query(KnowledgeBase).filter(
            KnowledgeBase.uuid.in_(search_request.kb_uuids),
            KnowledgeBase.deleted_at.is_(None)
        ).all()
        
        kb_ids = [kb.id for kb in kbs]
        
        # 权限检查
        from app.api.knowledge_bases import check_kb_permission
        for kb in kbs:
            if not check_kb_permission(current_user, kb, 'read', db):
                return error_response(message=f"无权访问知识库：{kb.name}", code=403)
    else:
        # 检索用户所有可访问的知识库
        kb_ids = get_accessible_kb_ids(current_user, db)
    
    if not kb_ids:
        return success_response(data=KnowledgeSearchResponse(
            query=search_request.query,
            results=[],
            total_chunks_searched=0,
            retrieval_time_ms=0,
            avg_similarity=None
        ).model_dump())
    
    # 根据检索模式执行检索
    if search_request.retrieval_mode == 'vector':
        # 纯向量检索
        results = await vector_search(
            search_request.query,
            kb_ids,
            search_request.top_k,
            search_request.similarity_threshold,
            db
        )
    elif search_request.retrieval_mode == 'keyword':
        # 纯关键词检索
        results = keyword_search(
            search_request.query,
            kb_ids,
            search_request.top_k,
            db
        )
    else:
        # 混合检索（向量+关键词）
        vector_results = await vector_search(
            search_request.query,
            kb_ids,
            search_request.top_k,
            search_request.similarity_threshold,
            db
        )
        
        keyword_results = keyword_search(
            search_request.query,
            kb_ids,
            search_request.top_k // 2,
            db
        )
        
        # 合并结果（去重）
        seen_chunks = set()
        results = []
        
        # 先添加向量检索结果
        for r in vector_results:
            if r['chunk'].id not in seen_chunks:
                results.append(r)
                seen_chunks.add(r['chunk'].id)
        
        # 再添加关键词检索结果
        for r in keyword_results:
            if r['chunk'].id not in seen_chunks and len(results) < search_request.top_k:
                results.append(r)
                seen_chunks.add(r['chunk'].id)
        
        # 重新排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        results = results[:search_request.top_k]
    
    # 转换为响应格式
    search_results = []
    total_similarity = 0.0
    
    for r in results:
        chunk = r['chunk']
        doc = r['document']
        kb = r['knowledge_base']
        similarity = r['similarity_score']
        
        search_results.append(SearchResultItem(
            chunk_id=chunk.id,
            chunk_uuid=chunk.uuid,
            content=chunk.content,
            similarity_score=similarity,
            document_id=doc.id,
            document_uuid=doc.uuid,
            document_title=doc.title,
            knowledge_base_id=kb.id,
            knowledge_base_uuid=kb.uuid,
            knowledge_base_name=kb.name,
            meta_data=chunk.meta_data
        ))
        
        total_similarity += similarity
    
    # 计算检索耗时
    retrieval_time_ms = int((time.time() - start_time) * 1000)
    
    # 计算平均相似度
    avg_similarity = total_similarity / len(search_results) if search_results else None
    
    # 记录检索日志（后续实现）
    # TODO: 记录到 aiot_kb_retrieval_logs
    
    response = KnowledgeSearchResponse(
        query=search_request.query,
        results=search_results,
        total_chunks_searched=len(kb_ids),
        retrieval_time_ms=retrieval_time_ms,
        avg_similarity=avg_similarity
    )
    
    return success_response(data=response.model_dump())


@router.get("/suggestions", response_model=dict)
async def get_search_suggestions(
    keyword: str = Query(..., min_length=1),
    kb_uuids: Optional[List[str]] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取搜索建议（基于文档标题和内容）"""
    # 确定检索范围
    if kb_uuids:
        kbs = db.query(KnowledgeBase).filter(
            KnowledgeBase.uuid.in_(kb_uuids),
            KnowledgeBase.deleted_at.is_(None)
        ).all()
        kb_ids = [kb.id for kb in kbs]
    else:
        kb_ids = get_accessible_kb_ids(current_user, db)
    
    if not kb_ids:
        return success_response(data={"suggestions": []})
    
    # 查询匹配的文档标题
    documents = db.query(Document.title, func.count(Document.id).label('count')).filter(
        Document.knowledge_base_id.in_(kb_ids),
        Document.title.like(f"%{keyword}%"),
        Document.deleted_at.is_(None)
    ).group_by(Document.title).limit(limit).all()
    
    suggestions = [{"text": title, "type": "document", "count": count} for title, count in documents]
    
    return success_response(data={"suggestions": suggestions})

