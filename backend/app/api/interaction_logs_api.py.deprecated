"""
交互日志API - 使用优化的日志服务
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.interaction_log_service import (
    interaction_log_service,
    log_device_interaction,
    LogEntry
)
from ..core.auth import get_current_user
from ..schemas.user import User

router = APIRouter(prefix="/api/interaction-logs", tags=["交互日志"])


class LogQueryParams(BaseModel):
    """日志查询参数"""
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interaction_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class LogCreateRequest(BaseModel):
    """创建日志请求"""
    device_id: str
    interaction_type: str
    direction: str = "inbound"
    status: str = "success"
    data_size: int = 0
    response_time: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    request_data: Optional[dict] = None
    response_data: Optional[dict] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class StatsQueryParams(BaseModel):
    """统计查询参数"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    device_id: Optional[str] = None
    group_by: str = Field(default="hour", regex="^(hour|day|week|month)$")


@router.post("/", summary="记录交互日志")
async def create_interaction_log(
    log_request: LogCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    记录设备交互日志（异步处理）
    """
    try:
        # 创建日志条目
        log_entry = LogEntry(
            device_id=log_request.device_id,
            interaction_type=log_request.interaction_type,
            direction=log_request.direction,
            status=log_request.status,
            data_size=log_request.data_size,
            response_time=log_request.response_time,
            error_code=log_request.error_code,
            error_message=log_request.error_message,
            request_data=log_request.request_data,
            response_data=log_request.response_data,
            client_ip=log_request.client_ip,
            user_agent=log_request.user_agent,
            session_id=log_request.session_id
        )
        
        # 异步记录日志
        background_tasks.add_task(
            interaction_log_service.log_interaction,
            log_entry
        )
        
        return {
            "success": True,
            "message": "日志记录请求已提交",
            "log_id": f"pending_{datetime.utcnow().timestamp()}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录日志失败: {str(e)}")


@router.get("/", summary="查询交互日志")
async def get_interaction_logs(
    device_id: Optional[str] = Query(None, description="设备ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interaction_type: Optional[str] = Query(None, description="交互类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(100, le=1000, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user)
):
    """
    查询交互日志（支持缓存优化）
    """
    try:
        # 确保服务已初始化
        if not interaction_log_service._initialized:
            await interaction_log_service.initialize()
        
        result = await interaction_log_service.get_device_logs(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            interaction_type=interaction_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "data": result['logs'],
            "total": result['total'],
            "from_cache": result.get('from_cache', False),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": result['total'] > offset + limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询日志失败: {str(e)}")


@router.get("/stats", summary="获取交互统计")
async def get_interaction_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    device_id: Optional[str] = Query(None, description="设备ID"),
    group_by: str = Query("hour", regex="^(hour|day|week|month)$", description="分组方式"),
    current_user: User = Depends(get_current_user)
):
    """
    获取交互统计数据（支持缓存）
    """
    try:
        # 确保服务已初始化
        if not interaction_log_service._initialized:
            await interaction_log_service.initialize()
        
        # 如果没有指定时间范围，默认查询最近24小时
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        result = await interaction_log_service.get_interaction_stats(
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            group_by=group_by
        )
        
        return {
            "success": True,
            "data": result['stats'],
            "summary": result['summary'],
            "query_params": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "device_id": device_id,
                "group_by": group_by
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/device/{device_id}", summary="获取设备日志")
async def get_device_logs(
    device_id: str,
    hours: int = Query(24, ge=1, le=168, description="查询小时数"),
    interaction_type: Optional[str] = Query(None, description="交互类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(100, le=1000, description="限制数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定设备的交互日志
    """
    try:
        # 确保服务已初始化
        if not interaction_log_service._initialized:
            await interaction_log_service.initialize()
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        end_time = datetime.utcnow()
        
        result = await interaction_log_service.get_device_logs(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            interaction_type=interaction_type,
            status=status,
            limit=limit,
            offset=0
        )
        
        return {
            "success": True,
            "device_id": device_id,
            "data": result['logs'],
            "total": result['total'],
            "from_cache": result.get('from_cache', False),
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备日志失败: {str(e)}")


@router.get("/device/{device_id}/stats", summary="获取设备统计")
async def get_device_stats(
    device_id: str,
    days: int = Query(7, ge=1, le=90, description="查询天数"),
    group_by: str = Query("day", regex="^(hour|day|week)$", description="分组方式"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定设备的统计数据
    """
    try:
        # 确保服务已初始化
        if not interaction_log_service._initialized:
            await interaction_log_service.initialize()
        
        start_time = datetime.utcnow() - timedelta(days=days)
        end_time = datetime.utcnow()
        
        result = await interaction_log_service.get_interaction_stats(
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            group_by=group_by
        )
        
        return {
            "success": True,
            "device_id": device_id,
            "data": result['stats'],
            "summary": result['summary'],
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备统计失败: {str(e)}")


@router.post("/batch", summary="批量记录日志")
async def create_batch_logs(
    logs: List[LogCreateRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    批量记录交互日志
    """
    if len(logs) > 1000:
        raise HTTPException(status_code=400, detail="批量日志数量不能超过1000条")
    
    try:
        # 转换为LogEntry对象
        log_entries = []
        for log_request in logs:
            log_entry = LogEntry(
                device_id=log_request.device_id,
                interaction_type=log_request.interaction_type,
                direction=log_request.direction,
                status=log_request.status,
                data_size=log_request.data_size,
                response_time=log_request.response_time,
                error_code=log_request.error_code,
                error_message=log_request.error_message,
                request_data=log_request.request_data,
                response_data=log_request.response_data,
                client_ip=log_request.client_ip,
                user_agent=log_request.user_agent,
                session_id=log_request.session_id
            )
            log_entries.append(log_entry)
        
        # 异步批量记录
        async def batch_log_task():
            for log_entry in log_entries:
                await interaction_log_service.log_interaction(log_entry)
        
        background_tasks.add_task(batch_log_task)
        
        return {
            "success": True,
            "message": f"批量日志记录请求已提交，共{len(logs)}条",
            "batch_id": f"batch_{datetime.utcnow().timestamp()}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量记录日志失败: {str(e)}")


@router.delete("/cleanup", summary="清理旧日志")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=7, le=365, description="保留天数"),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    清理旧的交互日志（管理员功能）
    """
    # 这里可以添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 异步清理
        background_tasks.add_task(
            interaction_log_service.cleanup_old_logs,
            days_to_keep
        )
        
        return {
            "success": True,
            "message": f"旧日志清理任务已启动，将保留最近{days_to_keep}天的数据"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动清理任务失败: {str(e)}")


# 便捷的日志记录装饰器
def log_api_interaction(interaction_type: str, direction: str = "inbound"):
    """API交互日志装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            status = "success"
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                error_message = str(e)
                raise
            finally:
                end_time = datetime.utcnow()
                response_time = int((end_time - start_time).total_seconds() * 1000)
                
                # 记录日志（这里需要从请求中获取设备ID等信息）
                # 实际使用时需要根据具体的API结构来获取这些信息
                await log_device_interaction(
                    device_id="api_call",  # 需要从请求中获取
                    interaction_type=interaction_type,
                    direction=direction,
                    status=status,
                    response_time=response_time,
                    error_message=error_message
                )
        
        return wrapper
    return decorator