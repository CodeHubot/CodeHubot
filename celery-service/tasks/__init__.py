"""
Celery 任务模块
"""
from .embedding_tasks import embed_document_task
from .preset_tasks import execute_preset_sequence_task

__all__ = [
    'embed_document_task',
    'execute_preset_sequence_task'
]

