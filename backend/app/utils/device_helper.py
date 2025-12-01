"""
设备状态更新辅助函数
用于替代交互日志记录，直接更新设备表的最后状态
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.device import Device


def update_device_report(
    db: Session,
    device_id: str,
    report_data: Optional[Dict[str, Any]] = None,
    is_online: bool = True
) -> bool:
    """
    更新设备上报数据（超级精简版）
    
    Args:
        db: 数据库会话
        device_id: 设备ID
        report_data: 上报数据（字典）
        is_online: 是否在线（默认True）
    
    Returns:
        bool: 是否成功
    
    示例:
        # MQTT消息处理
        data = json.loads(payload)
        update_device_report(db, device_id="device123", report_data=data)
        
        # HTTP API
        update_device_report(db, device_id="device456", report_data=request_data)
    """
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id
        ).first()
        
        if not device:
            return False
        
        # 只需要更新3个字段
        device.last_seen = datetime.now()
        device.is_online = is_online
        
        if report_data:
            device.last_report_data = report_data
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"更新设备状态失败: {e}")
        return False


def get_device_last_data(
    db: Session,
    device_id: str,
    key: Optional[str] = None
) -> Any:
    """
    获取设备最后上报的数据
    
    Args:
        db: 数据库会话
        device_id: 设备ID
        key: 要提取的键（可选），如 "temperature"
    
    Returns:
        如果指定key，返回对应的值；否则返回完整的 last_report_data
    
    示例:
        # 获取完整数据
        data = get_device_last_data(db, "device123")
        # 返回: {"temperature": 25.5, "humidity": 60}
        
        # 获取特定字段
        temp = get_device_last_data(db, "device123", key="temperature")
        # 返回: 25.5
    """
    try:
        device = db.query(Device).filter(
            Device.device_id == device_id
        ).first()
        
        if not device or not device.last_report_data:
            return None
        
        if key:
            return device.last_report_data.get(key)
        else:
            return device.last_report_data
        
    except Exception as e:
        print(f"获取设备数据失败: {e}")
        return None

