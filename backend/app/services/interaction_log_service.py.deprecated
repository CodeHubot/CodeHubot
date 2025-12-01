"""
交互日志服务 - 优化版本
支持异步写入、批量处理、缓存和数据归档
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间（不带时区信息，用于存储到数据库）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.dialects.postgresql import insert

from ..core.database import get_async_session
from ..core.config import settings
from ..models.interaction_log import InteractionLog
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LogEntry:
    """日志条目数据类"""
    device_id: str
    interaction_type: str
    direction: str
    status: str
    data_size: int = 0
    response_time: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = get_beijing_now()


class InteractionLogBuffer:
    """日志缓冲区 - 批量写入优化"""
    
    def __init__(self, batch_size: int = 1000, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: List[LogEntry] = []
        self.last_flush = time.time()
        self._lock = asyncio.Lock()
        self._flush_task = None
        
    async def add_log(self, log_entry: LogEntry):
        """添加日志到缓冲区"""
        async with self._lock:
            self.buffer.append(log_entry)
            
            # 检查是否需要刷新
            should_flush = (
                len(self.buffer) >= self.batch_size or
                time.time() - self.last_flush > self.flush_interval
            )
            
            if should_flush and (self._flush_task is None or self._flush_task.done()):
                self._flush_task = asyncio.create_task(self._flush())
    
    async def _flush(self):
        """刷新缓冲区到数据库"""
        if not self.buffer:
            return
            
        async with self._lock:
            batch = self.buffer.copy()
            self.buffer.clear()
            self.last_flush = time.time()
        
        try:
            await self._batch_insert(batch)
            logger.info(f"成功写入 {len(batch)} 条日志")
        except Exception as e:
            logger.error(f"批量写入日志失败: {e}")
            # 可以考虑重试机制或写入备用存储
    
    async def _batch_insert(self, logs: List[LogEntry]):
        """批量插入数据库"""
        async with get_async_session() as session:
            try:
                # 转换为字典列表
                log_dicts = [asdict(log) for log in logs]
                
                # 使用PostgreSQL的批量插入
                stmt = insert(InteractionLog).values(log_dicts)
                await session.execute(stmt)
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                raise e
    
    async def force_flush(self):
        """强制刷新缓冲区"""
        if self._flush_task and not self._flush_task.done():
            await self._flush_task
        await self._flush()


class InteractionLogCache:
    """日志缓存管理"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_config = {
            'recent_logs': {'ttl': 300, 'max_items': 100},
            'stats_cache': {'ttl': 3600},
            'device_status': {'ttl': 60},
        }
    
    async def cache_recent_logs(self, device_id: str, logs: List[Dict]):
        """缓存设备最近的日志"""
        key = f"logs:recent:{device_id}"
        config = self.cache_config['recent_logs']
        
        # 只保留最新的日志
        logs_to_cache = logs[-config['max_items']:]
        
        await self.redis.setex(
            key, 
            config['ttl'], 
            json.dumps(logs_to_cache, default=str)
        )
    
    async def get_recent_logs(self, device_id: str) -> Optional[List[Dict]]:
        """获取缓存的最近日志"""
        key = f"logs:recent:{device_id}"
        cached = await self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_stats(self, stats_type: str, period: str, data: Dict):
        """缓存统计数据"""
        key = f"stats:{stats_type}:{period}"
        config = self.cache_config['stats_cache']
        
        await self.redis.setex(
            key,
            config['ttl'],
            json.dumps(data, default=str)
        )
    
    async def get_cached_stats(self, stats_type: str, period: str) -> Optional[Dict]:
        """获取缓存的统计数据"""
        key = f"stats:{stats_type}:{period}"
        cached = await self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def update_device_status(self, device_id: str, status: Dict):
        """更新设备状态缓存"""
        key = f"device:status:{device_id}"
        config = self.cache_config['device_status']
        
        await self.redis.setex(
            key,
            config['ttl'],
            json.dumps(status, default=str)
        )


class InteractionLogService:
    """交互日志服务 - 主服务类"""
    
    def __init__(self):
        self.buffer = InteractionLogBuffer(
            batch_size=settings.LOG_BATCH_SIZE,
            flush_interval=settings.LOG_FLUSH_INTERVAL
        )
        self.redis_client = None
        self.cache = None
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
            
        # 初始化Redis连接
        self.redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.cache = InteractionLogCache(self.redis_client)
        self._initialized = True
        
        logger.info("交互日志服务初始化完成")
    
    async def log_interaction(self, log_entry: LogEntry):
        """记录交互日志（异步）"""
        if not self._initialized:
            await self.initialize()
        
        # 添加到缓冲区进行批量写入
        await self.buffer.add_log(log_entry)
        
        # 更新设备状态缓存
        if self.cache:
            status = {
                'last_interaction': log_entry.timestamp.isoformat(),
                'last_status': log_entry.status,
                'last_type': log_entry.interaction_type
            }
            await self.cache.update_device_status(log_entry.device_id, status)
    
    async def get_device_logs(
        self,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """获取设备日志（带缓存优化）"""
        
        # 尝试从缓存获取最近日志
        if not start_time and not end_time and limit <= 100:
            cached_logs = await self.cache.get_recent_logs(device_id)
            if cached_logs:
                return {
                    'logs': cached_logs[:limit],
                    'total': len(cached_logs),
                    'from_cache': True
                }
        
        # 从数据库查询
        async with get_async_session() as session:
            query = select(InteractionLog).where(InteractionLog.device_id == device_id)
            
            # 添加时间范围过滤
            if start_time:
                query = query.where(InteractionLog.timestamp >= start_time)
            if end_time:
                query = query.where(InteractionLog.timestamp <= end_time)
            if interaction_type:
                query = query.where(InteractionLog.interaction_type == interaction_type)
            if status:
                query = query.where(InteractionLog.status == status)
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total = await session.scalar(count_query)
            
            # 分页查询
            query = query.order_by(InteractionLog.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            logs = result.scalars().all()
            
            # 转换为字典格式
            log_dicts = [
                {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'device_id': log.device_id,
                    'interaction_type': log.interaction_type,
                    'direction': log.direction,
                    'status': log.status,
                    'data_size': log.data_size,
                    'response_time': log.response_time,
                    'error_code': log.error_code,
                    'error_message': log.error_message,
                    'client_ip': str(log.client_ip) if log.client_ip else None,
                    'session_id': log.session_id
                }
                for log in logs
            ]
            
            # 缓存最近的日志
            if not start_time and not end_time:
                await self.cache.cache_recent_logs(device_id, log_dicts)
            
            return {
                'logs': log_dicts,
                'total': total,
                'from_cache': False
            }
    
    async def get_interaction_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        device_id: Optional[str] = None,
        group_by: str = 'hour'
    ) -> Dict[str, Any]:
        """获取交互统计（带缓存）"""
        
        # 生成缓存键
        cache_key_parts = [
            device_id or 'all',
            group_by,
            start_time.strftime('%Y%m%d%H') if start_time else 'all',
            end_time.strftime('%Y%m%d%H') if end_time else 'all'
        ]
        cache_key = '_'.join(cache_key_parts)
        
        # 尝试从缓存获取
        cached_stats = await self.cache.get_cached_stats('interaction', cache_key)
        if cached_stats:
            return cached_stats
        
        # 从数据库查询
        async with get_async_session() as session:
            # 构建时间分组函数
            time_trunc_map = {
                'hour': "DATE_TRUNC('hour', timestamp)",
                'day': "DATE_TRUNC('day', timestamp)",
                'week': "DATE_TRUNC('week', timestamp)",
                'month': "DATE_TRUNC('month', timestamp)"
            }
            
            time_trunc = time_trunc_map.get(group_by, time_trunc_map['hour'])
            
            # 构建查询
            query = f"""
            SELECT 
                {time_trunc} as time_period,
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE status = 'success') as success_count,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                AVG(response_time) as avg_response_time,
                SUM(data_size) as total_data_size,
                COUNT(DISTINCT device_id) as unique_devices
            FROM aiot_interaction_logs
            WHERE 1=1
            """
            
            params = []
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)
            if device_id:
                query += " AND device_id = %s"
                params.append(device_id)
            
            query += f" GROUP BY {time_trunc} ORDER BY time_period DESC"
            
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            # 格式化结果
            stats = []
            for row in rows:
                stats.append({
                    'time_period': row.time_period.isoformat(),
                    'total_count': row.total_count,
                    'success_count': row.success_count,
                    'failed_count': row.failed_count,
                    'success_rate': round(row.success_count / row.total_count * 100, 2) if row.total_count > 0 else 0,
                    'avg_response_time': round(row.avg_response_time, 2) if row.avg_response_time else 0,
                    'total_data_size': row.total_data_size or 0,
                    'unique_devices': row.unique_devices
                })
            
            result_data = {
                'stats': stats,
                'summary': {
                    'total_interactions': sum(s['total_count'] for s in stats),
                    'overall_success_rate': round(
                        sum(s['success_count'] for s in stats) / 
                        sum(s['total_count'] for s in stats) * 100, 2
                    ) if sum(s['total_count'] for s in stats) > 0 else 0,
                    'total_data_transferred': sum(s['total_data_size'] for s in stats)
                }
            }
            
            # 缓存结果
            await self.cache.cache_stats('interaction', cache_key, result_data)
            
            return result_data
    
    async def cleanup_old_logs(self, days_to_keep: int = 90):
        """清理旧日志"""
        cutoff_date = get_beijing_now() - timedelta(days=days_to_keep)
        
        async with get_async_session() as session:
            # 先统计要删除的记录数
            count_query = select(func.count()).where(
                InteractionLog.timestamp < cutoff_date
            )
            count = await session.scalar(count_query)
            
            if count > 0:
                # 删除旧记录
                delete_query = text(
                    "DELETE FROM aiot_interaction_logs WHERE timestamp < :cutoff_date"
                )
                await session.execute(delete_query, {'cutoff_date': cutoff_date})
                await session.commit()
                
                logger.info(f"清理了 {count} 条旧日志记录")
            else:
                logger.info("没有需要清理的旧日志")
    
    async def shutdown(self):
        """关闭服务"""
        if self.buffer:
            await self.buffer.force_flush()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("交互日志服务已关闭")


# 全局服务实例
interaction_log_service = InteractionLogService()


# 便捷函数
async def log_device_interaction(
    device_id: str,
    interaction_type: str,
    direction: str = 'inbound',
    status: str = 'success',
    **kwargs
):
    """记录设备交互的便捷函数"""
    log_entry = LogEntry(
        device_id=device_id,
        interaction_type=interaction_type,
        direction=direction,
        status=status,
        **kwargs
    )
    await interaction_log_service.log_interaction(log_entry)


# 上下文管理器
@asynccontextmanager
async def interaction_log_context():
    """交互日志服务上下文管理器"""
    await interaction_log_service.initialize()
    try:
        yield interaction_log_service
    finally:
        await interaction_log_service.shutdown()