"""
知识库检索节点执行器
从知识库中检索相关内容
"""
import logging
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentChunk
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


async def execute_knowledge_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str],
    db_session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    执行知识库检索节点
    
    Args:
        node_data: 节点配置数据，包含：
            - kb_uuid: 知识库UUID
            - query: 查询文本（支持变量替换）
            - top_k: 返回数量（默认5）
            - similarity_threshold: 相似度阈值（默认0.7）
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        db_session: 数据库会话
        
    Returns:
        Dict[str, Any]: 节点输出，包含：
            - results: 检索结果列表
            - total: 结果总数
    """
    if not db_session:
        raise ValueError("知识库检索节点执行需要数据库会话")
    
    # 获取节点配置
    kb_uuid = node_data.get("kb_uuid")
    query = node_data.get("query", "")
    top_k = node_data.get("top_k", 5)
    similarity_threshold = node_data.get("similarity_threshold", 0.7)
    
    if not kb_uuid:
        raise ValueError("知识库检索节点必须配置知识库UUID")
    
    if not query:
        raise ValueError("知识库检索节点必须配置查询文本")
    
    # 对查询文本进行变量替换
    query = replace_variables(query)
    
    # 查询知识库
    kb = db_session.query(KnowledgeBase).filter(KnowledgeBase.uuid == kb_uuid).first()
    if not kb:
        raise ValueError(f"知识库不存在: {kb_uuid}")
    
    # 获取Embedding服务
    embedding_service = get_embedding_service()
    
    # 对查询文本进行向量化
    query_vector = await embedding_service.embed_text(query)
    if not query_vector:
        raise ValueError("查询文本向量化失败")
    
    # 获取所有已向量化的文档块
    chunks = db_session.query(DocumentChunk).filter(
        DocumentChunk.knowledge_base_id == kb.id,
        DocumentChunk.embedding_vector.isnot(None)
    ).all()
    
    if not chunks:
        logger.warning(f"知识库 {kb.name} 中没有已向量化的文档块")
        return {
            "results": [],
            "total": 0
        }
    
    # 计算相似度
    results = []
    for chunk in chunks:
        if chunk.embedding_vector:
            similarity = embedding_service.calculate_similarity(
                query_vector,
                chunk.embedding_vector
            )
            
            if similarity >= similarity_threshold:
                # 获取文档信息
                doc = db_session.query(Document).filter(Document.id == chunk.document_id).first()
                
                results.append({
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "similarity": similarity,
                    "document_title": doc.title if doc else None,
                    "document_id": chunk.document_id
                })
    
    # 按相似度排序并取top_k
    results.sort(key=lambda x: x["similarity"], reverse=True)
    results = results[:top_k]
    
    logger.info(f"知识库检索完成，找到 {len(results)} 个结果")
    
    return {
        "results": results,
        "total": len(results)
    }

