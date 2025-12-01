"""
文档向量化 Celery 任务
"""
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
import logging
import asyncio

# ✅ 确保所有模型都被导入，避免 SQLAlchemy mapper 初始化问题
import app.models

logger = logging.getLogger(__name__)


@celery_app.task(
    name='embed_document',
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 重试延迟60秒
)
def embed_document_task(self, document_id: int):
    """
    文档向量化 Celery 任务
    
    Args:
        document_id: 文档ID
    
    Returns:
        dict: 处理结果
    """
    from app.services.embedding_service import embed_document
    from app.models.document import Document
    
    # 确保加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        logger.info(f"开始处理文档向量化任务: document_id={document_id}, task_id={self.request.id}")
        
        # 检查文档是否存在
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"文档不存在: {document_id}")
            return {'status': 'error', 'message': '文档不存在'}
        
        # 执行向量化
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(embed_document(document_id, db))
        finally:
            loop.close()
        
        # 刷新状态
        db.refresh(doc)
        
        if doc.embedding_status == 'completed':
            logger.info(f"文档 {document_id} 向量化成功，文本块数: {doc.chunk_count}")
            return {
                'status': 'success',
                'document_id': document_id,
                'chunk_count': doc.chunk_count,
                'message': '向量化完成'
            }
        else:
            error_msg = doc.embedding_error or '未知错误'
            logger.error(f"文档 {document_id} 向量化失败: {error_msg}")
            
            # 如果失败，尝试重试
            if self.request.retries < self.max_retries:
                logger.info(f"将在60秒后重试 (尝试 {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=Exception(error_msg))
            
            return {
                'status': 'failed',
                'document_id': document_id,
                'error': error_msg,
                'message': '向量化失败'
            }
    
    except Exception as e:
        logger.error(f"文档 {document_id} 向量化任务异常: {str(e)}")
        
        # 尝试重试
        if self.request.retries < self.max_retries:
            logger.info(f"任务将重试 (尝试 {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        # 更新文档状态为失败
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.embedding_status = 'failed'
                doc.embedding_error = str(e)
                db.commit()
        except:
            pass
        
        return {
            'status': 'error',
            'document_id': document_id,
            'error': str(e),
            'message': '任务执行异常'
        }
    
    finally:
        db.close()

