from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.product import Product
from app.api.auth import get_current_user
from app.core.response import success_response

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员（通过邮箱判断）"""
    return user.email == "admin@aiot.com" or user.username == "admin"


def get_accessible_product_ids(db: Session, user: User):
    """获取用户有权限访问的产品ID列表"""
    if is_admin_user(user):
        # 管理员可以访问所有产品
        products = db.query(Product.id).all()
        return [p.id for p in products]
    else:
        # 普通用户：只能访问系统内置产品和自己创建的产品
        products = db.query(Product.id).filter(
            or_(
                Product.is_system == True,
                Product.creator_id == user.id
            )
        ).all()
        return [p.id for p in products]

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘统计数据 - 数据权限控制：只统计用户注册的设备，管理员统计所有设备"""
    
    # 数据权限过滤：管理员可以看到所有设备，普通用户只能看到自己注册的设备
    query = db.query(Device)
    if not is_admin_user(current_user):
        query = query.filter(Device.user_id == current_user.id)
    
    # 获取用户的设备统计
    total_devices = query.count()
    
    # 在线设备数（最近5分钟有心跳的设备）
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    online_devices_query = db.query(Device)
    if not is_admin_user(current_user):
        online_devices_query = online_devices_query.filter(Device.user_id == current_user.id)
    online_devices = online_devices_query.filter(
        Device.is_online == True,
        Device.last_seen >= five_minutes_ago
    ).count()
    
    # 离线设备数
    offline_devices = total_devices - online_devices
    
    # 今日新增设备
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_devices_query = db.query(Device)
    if not is_admin_user(current_user):
        today_devices_query = today_devices_query.filter(Device.user_id == current_user.id)
    today_devices = today_devices_query.filter(
        Device.created_at >= today_start
    ).count()
    
    # 产品类型统计（基于设备权限）
    product_types_query = db.query(
        Product.category,
        func.count(Device.id).label('count')
    ).join(Device, Device.product_id == Product.id)
    if not is_admin_user(current_user):
        product_types_query = product_types_query.filter(Device.user_id == current_user.id)
    product_types = product_types_query.group_by(Product.category).all()
    
    product_type_stats = [
        {"type": product_type, "count": count}
        for product_type, count in product_types
    ]
    
    return success_response(data={
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "today_devices": today_devices,
        "product_types": product_type_stats,
        "alerts": 0  # 暂时设为0，后续可以添加告警逻辑
    })

@router.get("/recent-devices")
async def get_recent_devices(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近设备列表 - 数据权限控制：只返回用户注册的设备，管理员可以看到所有设备"""
    
    # 数据权限过滤：管理员可以看到所有设备，普通用户只能看到自己注册的设备
    query = db.query(Device).join(Product)
    if not is_admin_user(current_user):
        query = query.filter(Device.user_id == current_user.id)
    
    recent_devices = query.order_by(Device.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": device.id,
            "name": device.name,
            "product_name": device.product.name if device.product else None,
            "product_category": device.product.category if device.product else None,
            "is_online": device.is_online,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_at": device.created_at.isoformat() if device.created_at else None
        }
        for device in recent_devices
    ]

@router.get("/recent-interactions")
async def get_recent_interactions(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近交互记录（模拟数据）- 数据权限控制：只返回用户注册的设备，管理员可以看到所有设备"""
    
    # 数据权限过滤：管理员可以看到所有设备，普通用户只能看到自己注册的设备
    query = db.query(Device)
    if not is_admin_user(current_user):
        query = query.filter(Device.user_id == current_user.id)
    
    user_devices = query.all()
    
    if not user_devices:
        return []
    
    # 模拟最近的交互数据
    interactions = []
    for i, device in enumerate(user_devices[:limit]):
        interactions.append({
            "id": f"interaction_{i+1}",
            "device_id": device.device_id,
            "device_name": device.name,
            "type": "data_upload" if i % 2 == 0 else "command",
            "description": f"设备 {device.name} 上传传感器数据" if i % 2 == 0 else f"向设备 {device.name} 发送控制指令",
            "status": "success" if i % 3 != 0 else "failed",
            "timestamp": (datetime.utcnow() - timedelta(minutes=i*5)).isoformat()
        })
    
    return interactions