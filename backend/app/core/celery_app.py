"""
Celery 应用配置
用于异步任务处理（如文档向量化）
"""
from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 创建 Celery 应用
celery_app = Celery(
    'codehubot',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.embedding_tasks']
)

# Celery 配置
celery_app.conf.update(
    # 任务结果过期时间（秒）
    result_expires=3600,
    
    # 任务序列化方式
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # 时区设置
    timezone='Asia/Shanghai',
    enable_utc=False,
    
    # 任务时间限制
    task_time_limit=3600,  # 硬限制1小时
    task_soft_time_limit=3000,  # 软限制50分钟
    
    # 任务重试配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # worker丢失时重新入队
    
    # 并发控制
    worker_prefetch_multiplier=1,  # 每次只拉取1个任务
    worker_max_tasks_per_child=50,  # 每个worker最多处理50个任务后重启
    
    # 日志
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery 应用已初始化")


