"""
Celery 任务模块
"""
from app.tasks.embedding_tasks import embed_document_task

__all__ = ['embed_document_task']


