"""
Embedding服务
支持通义千问等Embedding模型
"""
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding服务基类"""
    
    def __init__(self):
        self.model_name = None
        self.dimension = 1536  # 默认维度
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        对单个文本进行向量化
        
        Args:
            text: 待向量化的文本
        
        Returns:
            List[float]: 向量（如果失败返回None）
        """
        raise NotImplementedError
    
    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量向量化文本
        
        Args:
            texts: 待向量化的文本列表
        
        Returns:
            List[Optional[List[float]]]: 向量列表
        """
        raise NotImplementedError
    
    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            float: 相似度（0-1）
        """
        import numpy as np
        
        # 转换为numpy数组
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # 计算余弦相似度
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # 归一化到0-1
        return float((similarity + 1) / 2)


class QwenEmbeddingService(EmbeddingService):
    """
    阿里云通义千问Embedding服务
    使用 text-embedding-v4 模型（最新版本，性能更好）
    """
    
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings", model: str = "text-embedding-v4"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model
        self.dimension = 1536  # v4 模型维度
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        对单个文本进行向量化
        使用 text-embedding-v4 的 compatible-mode API
        """
        if not text or not text.strip():
            logger.warning("文本为空，跳过向量化")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "input": text  # v4 使用 OpenAI 兼容格式，直接传文本
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # v4 使用 OpenAI 兼容格式的响应
                # {"data": [{"embedding": [...], "index": 0}], "model": "...", "usage": {...}}
                if result.get("data") and len(result["data"]) > 0:
                    return result["data"][0].get("embedding")
                
                # 兼容旧格式（以防万一）
                if result.get("output") and result["output"].get("embeddings"):
                    embeddings = result["output"]["embeddings"]
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0].get("embedding")
                
                logger.error(f"通义千问Embedding响应格式错误: {result}")
                return None
        
        except httpx.HTTPStatusError as e:
            logger.error(f"通义千问Embedding HTTP错误: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"通义千问Embedding失败: {str(e)}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量向量化文本
        使用 text-embedding-v4 的 compatible-mode API
        """
        if not texts:
            return []
        
        # v4 支持批量请求（建议最多25条）
        batch_size = 25
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.base_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model_name,
                            "input": batch  # v4 使用 OpenAI 兼容格式，直接传文本列表
                        }
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # v4 使用 OpenAI 兼容格式的响应
                    if result.get("data"):
                        # 按 index 排序确保顺序正确
                        data_items = sorted(result["data"], key=lambda x: x.get("index", 0))
                        batch_embeddings = [item.get("embedding") for item in data_items]
                        all_embeddings.extend(batch_embeddings)
                    # 兼容旧格式
                    elif result.get("output") and result["output"].get("embeddings"):
                        embeddings = result["output"]["embeddings"]
                        batch_embeddings = [e.get("embedding") for e in embeddings]
                        all_embeddings.extend(batch_embeddings)
                    else:
                        logger.error(f"批量向量化响应格式错误: {result}")
                        all_embeddings.extend([None] * len(batch))
            
            except Exception as e:
                logger.error(f"批量向量化失败: {str(e)}")
                all_embeddings.extend([None] * len(batch))
            
            # 避免请求过快
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return all_embeddings


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI Embedding服务
    备用方案
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1/embeddings", model: str = "text-embedding-ada-002"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model
        self.dimension = 1536
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """对单个文本进行向量化"""
        if not text or not text.strip():
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "input": text[:8000]  # OpenAI限制
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("data") and len(result["data"]) > 0:
                    return result["data"][0].get("embedding")
                
                return None
        
        except Exception as e:
            logger.error(f"OpenAI Embedding失败: {str(e)}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量向量化文本"""
        # OpenAI支持批量，但每次最多2048条
        # 为简化，这里逐个处理
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
            await asyncio.sleep(0.05)  # 避免限流
        
        return embeddings


class EmbeddingServiceFactory:
    """Embedding服务工厂"""
    
    @staticmethod
    def create(
        provider: str = "qwen",
        api_key: Optional[str] = None,
        **kwargs
    ) -> EmbeddingService:
        """
        创建Embedding服务实例
        
        Args:
            provider: 服务提供商（qwen/openai）
            api_key: API密钥
            **kwargs: 其他配置参数
        
        Returns:
            EmbeddingService: Embedding服务实例
        """
        if provider == "qwen":
            if not api_key:
                # 从环境变量读取（确保环境变量已加载）
                import os
                from dotenv import load_dotenv
                load_dotenv(override=False)  # 加载 .env 文件
                
                api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
                
                # 调试日志
                if api_key:
                    logger.info(f"✅ 成功从环境变量获取 API 密钥（长度: {len(api_key)}）")
                else:
                    logger.error("❌ 环境变量中未找到 DASHSCOPE_API_KEY 或 QWEN_API_KEY")
            
            if not api_key:
                raise ValueError("需要提供通义千问API密钥")
            
            return QwenEmbeddingService(api_key=api_key, **kwargs)
        
        elif provider == "openai":
            if not api_key:
                import os
                from dotenv import load_dotenv
                load_dotenv(override=False)  # 加载 .env 文件
                
                api_key = os.getenv("OPENAI_API_KEY")
                
                # 调试日志
                if api_key:
                    logger.info(f"✅ 成功从环境变量获取 OpenAI API 密钥")
                else:
                    logger.error("❌ 环境变量中未找到 OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("需要提供OpenAI API密钥")
            
            return OpenAIEmbeddingService(api_key=api_key, **kwargs)
        
        else:
            raise ValueError(f"不支持的Embedding服务提供商: {provider}")


# 全局Embedding服务实例（单例）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    force_new: bool = False
) -> EmbeddingService:
    """
    获取Embedding服务实例（单例模式）
    
    Args:
        provider: 服务提供商（qwen/openai），默认qwen
        api_key: API密钥
        force_new: 是否强制创建新实例
    
    Returns:
        EmbeddingService: Embedding服务实例
    """
    global _embedding_service
    
    if _embedding_service is None or force_new:
        provider = provider or "qwen"
        _embedding_service = EmbeddingServiceFactory.create(
            provider=provider,
            api_key=api_key
        )
    
    return _embedding_service


# ============================================================================
# 文档向量化流程
# ============================================================================

async def embed_document(
    document_id: int,
    db: Session,
    embedding_service: Optional[EmbeddingService] = None,
    batch_size: int = 10  # 每批处理的文本块数量
):
    """
    对文档进行向量化（包括切分和嵌入）
    增强版：支持批量处理、断点续传、自动重试
    
    Args:
        document_id: 文档ID
        db: 数据库会话
        embedding_service: Embedding服务实例（可选）
        batch_size: 每批处理的文本块数量（默认10）
    """
    from app.models.document import Document, DocumentChunk
    from app.models.knowledge_base import KnowledgeBase
    from app.utils.document_parser import parse_and_split_document
    from app.utils.timezone import get_beijing_time_naive
    import time
    
    # 获取文档
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"文档不存在: {document_id}")
        return
    
    # 获取知识库配置
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.knowledge_base_id).first()
    if not kb:
        logger.error(f"知识库不存在: {doc.knowledge_base_id}")
        return
    
    try:
        # 更新状态
        doc.embedding_status = 'processing'
        db.commit()
        
        # 读取文件内容
        from app.api.ai.kb_documents import read_file_from_disk
        logger.info(f"读取文档文件: {doc.file_url}")
        file_content = read_file_from_disk(doc.file_url)
        logger.info(f"文件读取成功，大小: {len(file_content)} bytes")
        
        # 获取切分参数
        chunk_size = kb.chunk_size or 500
        chunk_overlap = kb.chunk_overlap or 50
        split_mode = 'fixed'  # 默认模式
        
        # 从文档 metadata 中读取切分配置
        if doc.meta_data and isinstance(doc.meta_data, dict):
            split_mode = doc.meta_data.get('split_mode', 'fixed')
            # 如果是自定义模式，使用文档中保存的参数
            if split_mode == 'custom':
                chunk_size = doc.meta_data.get('chunk_size', chunk_size)
                chunk_overlap = doc.meta_data.get('chunk_overlap', chunk_overlap)
        
        logger.info(f"切分参数: mode={split_mode}, size={chunk_size}, overlap={chunk_overlap}")
        
        # 解析和切分文档
        logger.info(f"[步骤1/4] 开始解析和切分文档 {doc.id}")
        
        try:
            _, chunks_data = parse_and_split_document(
                file_content,
                doc.file_type,
                chunk_size,
                chunk_overlap,
                split_mode
            )
        except Exception as parse_error:
            logger.error(f"文档 {doc.id} 解析或切分失败: {str(parse_error)}", exc_info=True)
            doc.embedding_status = 'failed'
            doc.embedding_error = f"文档解析失败: {str(parse_error)}"
            db.commit()
            return
        
        total_chunks = len(chunks_data)
        logger.info(f"[步骤1/4] 文档 {doc.id} 切分完成: {total_chunks} 个文本块")
        
        # 检查文本块数量，如果太多则警告
        if total_chunks > 200:
            logger.warning(f"文档 {doc.id} 文本块数量较多 ({total_chunks})，将使用批量处理")
        
        # 删除旧的文本块
        logger.info(f"[步骤2/4] 清理旧的文本块记录...")
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.commit()
        logger.info(f"[步骤2/4] 旧文本块清理完成")
        
        # 获取Embedding服务
        logger.info(f"[步骤3/4] 初始化向量化服务...")
        if embedding_service is None:
            embedding_service = get_embedding_service()
        logger.info(f"[步骤3/4] 向量化服务就绪，准备处理 {total_chunks} 个文本块")
        
        # 批量向量化（分批处理，避免超时和内存问题）
        chunk_objects = []
        failed_indices = []
        
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = chunks_data[batch_start:batch_end]
            
            logger.info(f"文档 {doc.id}: 处理批次 {batch_start//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} "
                       f"({batch_start+1}-{batch_end}/{total_chunks})")
            
            # 提取文本
            texts = [chunk['content'] for chunk in batch_chunks]
            logger.info(f"批次 {batch_start//batch_size + 1}: 准备向量化 {len(texts)} 个文本块")
            
            # 向量化（带重试）
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"批次 {batch_start//batch_size + 1}: 调用向量化API (尝试 {attempt + 1}/{max_retries})")
                    embeddings = await embedding_service.embed_texts(texts)
                    logger.info(f"批次 {batch_start//batch_size + 1}: 向量化API调用成功，获得 {len(embeddings)} 个向量")
                    
                    # 创建文本块记录
                    for i, (chunk_data, embedding) in enumerate(zip(batch_chunks, embeddings)):
                        actual_index = batch_start + i
                        
                        chunk = DocumentChunk(
                            document_id=doc.id,
                            knowledge_base_id=doc.knowledge_base_id,
                            content=chunk_data['content'],
                            chunk_index=actual_index,
                            char_count=chunk_data['char_count'],
                            token_count=chunk_data['token_count'],
                            embedding_vector=embedding,  # JSON格式存储
                            meta_data=chunk_data.get('metadata')
                        )
                        
                        chunk_objects.append(chunk)
                        db.add(chunk)
                    
                    # 提交当前批次
                    db.commit()
                    logger.info(f"文档 {doc.id}: 批次 {batch_start//batch_size + 1} 处理成功")
                    break  # 成功则跳出重试循环
                    
                except Exception as batch_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"文档 {doc.id}: 批次 {batch_start//batch_size + 1} 失败，"
                                      f"将在 {retry_delay} 秒后重试 (尝试 {attempt + 1}/{max_retries}): {str(batch_error)}")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error(f"文档 {doc.id}: 批次 {batch_start//batch_size + 1} 多次重试失败: {str(batch_error)}")
                        failed_indices.extend(range(batch_start, batch_end))
                        break
            
            # 批次间短暂延迟，避免API限流
            if batch_end < total_chunks:
                await asyncio.sleep(0.5)
        
        # 更新文档状态
        logger.info(f"[步骤4/4] 更新文档状态...")
        if not failed_indices:
            doc.embedding_status = 'completed'
            doc.chunk_count = len(chunk_objects)
            doc.embedded_at = get_beijing_time_naive()
            doc.embedding_error = None
            logger.info(f"[步骤4/4] ✅ 文档 {doc.id} 向量化完成，共 {len(chunk_objects)} 个文本块")
        else:
            doc.embedding_status = 'failed'
            doc.chunk_count = len(chunk_objects)
            doc.embedding_error = f"部分文本块向量化失败: {len(failed_indices)} 个（{failed_indices[:10]}...）"
            logger.error(f"[步骤4/4] ❌ 文档 {doc.id} 部分向量化失败，成功 {len(chunk_objects)}/{total_chunks}")
        
        # 更新知识库统计
        kb.chunk_count = (kb.chunk_count or 0) + len(chunk_objects)
        kb.last_updated_at = get_beijing_time_naive()
        
        db.commit()
        logger.info(f"[步骤4/4] 数据库更新完成")
    
    except Exception as e:
        logger.error(f"文档 {doc.id} 向量化失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        doc.embedding_status = 'failed'
        doc.embedding_error = str(e)
        db.commit()

