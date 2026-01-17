from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.device import Device
from app.models.product import Product
from app.models.device_sensor import DeviceSensor
from app.models.user import User
from app.models.device_binding_history import DeviceBindingHistory
from sqlalchemy import or_, func, desc, func, desc
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceList, 
    DeviceRegister, DevicePreRegister, DeviceDataUpload, DeviceStatusUpdate,
    DeviceWithProductInfo, DeviceProductReport, DeviceProductSwitch, DeviceResponseWithStatus,
    DeviceMacRegister, DeviceMacRegisterResponse
)
from app.services.device_product_service import DeviceProductService
from app.api.auth import get_current_user, verify_internal_or_user
from app.core.constants import ErrorMessages, SuccessMessages
from app.core.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员
    
    管理员权限判断规则：
    1. platform_admin 角色（平台管理员）
    """
    判断用户是否为管理员
    基于角色判断，更安全且易于管理
    """
    return user.role in ['platform_admin', 'super_admin', 'admin']


def get_accessible_product_ids(db: Session, user: User) -> List[int]:
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


def can_access_device(device: Device, user: User, db: Session = None) -> bool:
    """检查用户是否有权限访问设备（读取和使用）
    
    包括：
    1. 管理员可以访问所有设备
    2. 设备所有者可以访问
    3. 学生通过PBL小组授权可以访问（只能使用，不能配置）
    """
    if is_admin_user(user):
        # 管理员可以访问所有设备
        return True
    
    # 设备所有者可以访问
    if device.user_id == user.id:
        return True
    
    # PBL模块已删除，不再支持PBL授权
    
    return False


def can_configure_device(device: Device, user: User, db: Session = None) -> bool:
    """检查用户是否有权限配置设备（修改配置、设置预设指令等）
    
    注意：学生即使通过PBL授权可以使用设备，也不能配置设备
    只有设备所有者和管理员可以配置设备
    
    包括：
    1. 管理员可以配置所有设备
    2. 设备所有者可以配置自己的设备
    3. 学生即使有PBL授权也不能配置设备
    """
    if is_admin_user(user):
        # 管理员可以配置所有设备
        return True
    
    # 只有设备所有者可以配置设备
    if device.user_id == user.id:
        return True
    
    # 学生即使通过PBL授权可以使用设备，也不能配置设备
    return False

@router.post("/", response_model=DeviceResponse)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新设备"""
    # 检查产品是否存在
    product = db.query(Product).filter(
        Product.id == device.product_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="产品不存在"
        )
    
    # 检查设备名称是否已存在
    existing_device = db.query(Device).filter(
        Device.name == device.name,
        Device.product_id == device.product_id
    ).first()
    
    if existing_device:
        raise HTTPException(
            status_code=400,
            detail=f"设备名称 {device.name} 在该产品中已存在"
        )
    
    # 生成UUID
    device_uuid = str(uuid.uuid4())
    
    # 创建设备（user_id 从当前用户获取，确保不为None）
    device_data = device.model_dump()
    device_data['user_id'] = current_user.id  # 确保user_id设置为当前用户ID
    db_device = Device(
        **device_data,
        uuid=device_uuid
    )
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return db_device

@router.get("", response_model=List[DeviceList])
def get_devices(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    page: Optional[int] = Query(None, ge=1, description="页码（从1开始）"),
    page_size: Optional[int] = Query(None, ge=1, le=1000, description="每页记录数"),
    keyword: Optional[str] = Query(None, description="搜索关键词（name或sn）"),
    product_id: Optional[int] = Query(None, description="产品ID筛选"),
    is_online: Optional[bool] = Query(None, description="在线状态筛选"),
    is_active: Optional[bool] = Query(None, description="激活状态筛选"),
    device_status: Optional[str] = Query(None, description="设备状态筛选：pending/bound/active/offline/error"),
    has_error: Optional[bool] = Query(None, description="是否有故障（error_count>0）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    exclude_grouped: Optional[bool] = Query(None, description="排除已在设备组中的设备"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备列表 - 数据权限控制：只返回用户注册的设备，管理员可以看到所有设备"""
    # 支持page/page_size参数（转换为skip/limit）
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size
    
    # 支持keyword参数（映射到search）
    if keyword:
        search = keyword
    
    query = db.query(Device)
    
    # 数据权限过滤
    if is_admin_user(current_user):
        # 平台管理员可以看到所有设备
        pass
    elif current_user.role == 'school_admin' and current_user.school_id:
        # 学校管理员只能看到明确归属于本校的设备
        query = query.filter(Device.school_id == current_user.school_id)
    elif current_user.role == 'student':
        # 学生：只能看到自己注册的设备（PBL模块已删除）
        query = query.filter(Device.user_id == current_user.id)
    else:
        # 普通用户只能看到自己注册的设备
        query = query.filter(Device.user_id == current_user.id)
    
    # 应用筛选条件
    if product_id:
        query = query.filter(Device.product_id == product_id)
    
    if is_online is not None:
        query = query.filter(Device.is_online == is_online)
    
    if is_active is not None:
        query = query.filter(Device.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Device.name.like(search_pattern)) |
            (Device.uuid.like(search_pattern)) |
            (Device.device_id.like(search_pattern)) |
            (Device.location.like(search_pattern)) |
            (Device.group_name.like(search_pattern))
        )
    
    # 排除已在设备组中的设备
    if exclude_grouped:
        from app.models.device_group import DeviceGroupMember
        # 使用子查询找出所有在设备组中的设备ID
        grouped_device_ids = db.query(DeviceGroupMember.device_id).filter(
            DeviceGroupMember.left_at.is_(None)  # 只查询未离开的设备
        ).subquery()
        # 排除这些设备
        query = query.filter(~Device.id.in_(grouped_device_ids))
    
    # 分页
    devices = query.offset(skip).limit(limit).all()
    
    return devices

from datetime import timezone, timedelta
from app.core.config import settings

# 北京时区常量 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间（不带时区信息，用于存储到数据库）"""
    from datetime import datetime
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)

def check_and_update_device_offline_status(device: Device, db: Session) -> bool:
    """
    检查设备是否超时并自动更新为离线状态
    
    Args:
        device: 设备对象
        db: 数据库会话
        
    Returns:
        bool: 如果设备状态被更新为离线，返回True；否则返回False
    """
    # 如果设备已经标记为离线，不需要检查
    if not device.is_online:
        return False
    
    # 如果没有最后在线时间，无法判断，保持原状态
    if not device.last_seen:
        return False
    
    # 计算超时时间（分钟转秒）
    timeout_seconds = settings.device_offline_timeout_minutes * 60
    
    # 计算时间差
    now = get_beijing_now()
    time_diff = (now - device.last_seen).total_seconds()
    
    # 如果超过超时时间，设置为离线
    if time_diff > timeout_seconds:
        device.is_online = False
        db.commit()
        logger.debug(
            f"设备 {device.uuid} ({device.name}) 超时离线: "
            f"最后在线时间 {device.last_seen}, 已超时 {int(time_diff/60)} 分钟"
        )
        return True
    
    return False

def format_datetime_beijing(dt):
    """格式化datetime对象为北京时间（UTC+8）
    
    Args:
        dt: datetime对象（数据库中存储的北京时间，无时区信息）
        
    Returns:
        str: ISO格式的时间字符串，带有+08:00时区偏移，例如：2025-11-15T13:30:00+08:00
    """
    if dt is None:
        return None
    
    # 如果dt没有时区信息，添加北京时区
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING_TZ)
    
    # 返回ISO格式字符串，包含时区偏移 (+08:00)
    return dt.isoformat()

@router.get("/with-product-info", response_model=List[DeviceWithProductInfo])
def get_devices_with_product_info(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取包含产品信息的设备列表 - 数据权限控制：管理员可以看到所有设备，学生可以看到授权设备"""
    try:
        # 使用ORM的joinedload预加载产品信息和用户信息，避免N+1查询问题
        query = db.query(Device).options(joinedload(Device.product), joinedload(Device.user))
        
        # 数据权限过滤
        if is_admin_user(current_user):
            # 平台管理员可以看到所有设备
            pass
        elif current_user.role == 'school_admin' and current_user.school_id:
            # 学校管理员只能看到明确归属于本校的设备
            query = query.filter(Device.school_id == current_user.school_id)
        elif current_user.role == 'student':
            # 学生：只能看到自己注册的设备（PBL模块已删除）
            query = query.filter(Device.user_id == current_user.id)
        else:
            # 普通用户只能看到自己注册的设备
            query = query.filter(Device.user_id == current_user.id)
        
        devices = (
            query
            .order_by(Device.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # 构造响应数据
        result = []
        for device in devices:
            # 检查设备是否超时，自动更新为离线状态
            check_and_update_device_offline_status(device, db)
            
            # 安全地获取设备状态（如果是枚举，转换为字符串）
            device_status_value = None
            if device.device_status:
                if hasattr(device.device_status, 'value'):
                    device_status_value = device.device_status.value
                else:
                    device_status_value = str(device.device_status)
            
            # 安全地获取产品信息（处理解绑产品的情况）
            product_name = None
            product_code = None
            product_category = None
            if device.product:
                product_name = device.product.name
                product_code = device.product.product_code
                product_category = device.product.category
            
            # 安全地获取用户信息（处理解绑设备的情况，user_id可能为None）
            owner_username = None
            owner_email = None
            owner_name = None
            if device.user:
                owner_username = device.user.username
                owner_email = device.user.email
                owner_name = device.user.username or device.user.email
            
            device_dict = {
                "id": device.id,
                "name": device.name,
                "device_id": device.device_id,
                "uuid": device.uuid,
                "product_id": device.product_id,
                "mac_address": device.mac_address,  # MAC地址
                "device_mac": device.mac_address or "",  # 设备MAC（用于显示，空值处理）
                "ip_address": device.ip_address,    # 添加IP地址
                "location": device.location,
                "group_name": device.group_name,
                "is_active": device.is_active,
                "is_online": device.is_online,
                "error_count": device.error_count or 0,
                "last_seen": format_datetime_beijing(device.last_seen),  # 格式化为北京时间
                "created_at": format_datetime_beijing(device.created_at),  # 格式化为北京时间
                "updated_at": format_datetime_beijing(device.updated_at),  # 格式化为北京时间
                "description": device.description,
                "device_status": device_status_value,
                "device_secret": device.device_secret,  # DeviceResponse需要的字段
                "user_id": device.user_id,  # DeviceResponse需要的字段（可能为None，表示已解绑）
                # 从关联的产品对象获取信息（安全处理None情况）
                "product_name": product_name,
                "product_code": product_code,
                "product_category": product_category,
                # 从关联的用户对象获取信息（安全处理None情况，包括解绑设备）
                "owner_username": owner_username,
                "owner_email": owner_email,
                "owner_name": owner_name
            }
            result.append(device_dict)
        
        logger.debug(f"获取设备列表成功，共 {len(result)} 条")
        return result
        
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.OPERATION_FAILED
        )


@router.get("/{device_uuid}", response_model=DeviceResponse)
def get_device(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个设备详情 - 数据权限控制：只能访问自己注册的设备，管理员可以看到所有设备"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查：管理员可以访问所有设备，普通用户只能访问自己注册的设备
    if not can_access_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权访问该设备"
        )
    
    # 检查设备是否超时，自动更新为离线状态
    check_and_update_device_offline_status(device, db)
    
    return device

@router.put("/{device_uuid}", response_model=DeviceResponse)
def update_device(
    device_uuid: str,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新设备信息 - 数据权限控制：只能更新自己注册的设备，管理员可以更新所有设备
    
    注意：学生即使通过PBL授权可以使用设备，也不能更新设备信息
    """
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 配置权限检查：只有设备所有者和管理员可以更新设备信息
    if not can_configure_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权更新该设备（学生只能使用授权设备，不能配置设备）"
        )
    
    # 如果更新产品，检查产品是否存在且用户有权限访问
    if device_update.product_id is not None:
        accessible_product_ids = get_accessible_product_ids(db, current_user)
        if device_update.product_id not in accessible_product_ids:
            raise HTTPException(
                status_code=403,
                detail="无权使用该产品"
            )
        
        product = db.query(Product).filter(
            Product.id == device_update.product_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail="产品不存在"
            )
    
    # 更新字段
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    db.commit()
    db.refresh(device)
    
    return device


@router.put("/{device_uuid}/set-school")
def set_device_school(
    device_uuid: str,
    school_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    设置设备归属学校
    - 设备所有者可以将设备设置为学校设备
    - 学校管理员可以将设备设置为本校设备
    - 设置为NULL表示转为个人设备
    
    注意：学生即使通过PBL授权可以使用设备，也不能设置设备学校归属
    """
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 配置权限检查：只有设备所有者和管理员可以设置设备学校归属
    is_owner = device.user_id == current_user.id
    is_school_admin_of_target = (
        current_user.role == 'school_admin' and 
        current_user.school_id == school_id
    )
    
    if not (is_owner or is_school_admin_of_target or is_admin_user(current_user)):
        raise HTTPException(
            status_code=403,
            detail="无权设置该设备的学校归属（学生只能使用授权设备，不能配置设备）"
        )
    
    # 如果设置为学校设备，验证学校存在
    if school_id is not None:
        from app.models.school import School
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise HTTPException(status_code=404, detail="学校不存在")
    
    # 更新设备的学校归属
    device.school_id = school_id
    db.commit()
    db.refresh(device)
    
    message = "设备已设置为学校设备" if school_id else "设备已设置为个人设备"
    return success_response(
        message=message,
        data={"device_uuid": device_uuid, "school_id": school_id}
    )


@router.delete("/{device_uuid}")
def delete_device(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除设备 - 数据权限控制：只能删除自己注册的设备，管理员可以删除所有设备"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查：管理员可以删除所有设备，普通用户只能删除自己注册的设备
    if not can_access_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权删除该设备"
        )
    
    db.delete(device)
    db.commit()
    
    return success_response(message="设备删除成功")


@router.get("/statistics/overview")
def get_devices_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备统计概览 - 数据权限控制：管理员统计所有设备，学生可以统计授权设备"""
    try:
        # 数据权限过滤
        if is_admin_user(current_user):
            # 平台管理员统计所有设备
            stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_devices,
                    SUM(CASE WHEN is_online = 1 THEN 1 ELSE 0 END) as online_devices,
                    SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as error_devices,
                    AVG(error_count) as avg_error_count
                FROM device_main
            """)).fetchone()
        elif current_user.role == 'school_admin' and current_user.school_id:
            # 学校管理员统计本校设备
            stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_devices,
                    SUM(CASE WHEN is_online = 1 THEN 1 ELSE 0 END) as online_devices,
                    SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as error_devices,
                    AVG(error_count) as avg_error_count
                FROM device_main
                WHERE school_id = :school_id
            """), {"school_id": current_user.school_id}).fetchone()
        elif current_user.role == 'student':
            # 学生：只统计自己注册的设备（PBL模块已删除）
            stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_devices,
                    SUM(CASE WHEN is_online = 1 THEN 1 ELSE 0 END) as online_devices,
                    SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as error_devices,
                    AVG(error_count) as avg_error_count
                FROM device_main
                WHERE user_id = :user_id
            """), {"user_id": current_user.id}).fetchone()
        else:
            # 普通用户只统计自己注册的设备
            stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_devices,
                    SUM(CASE WHEN is_online = 1 THEN 1 ELSE 0 END) as online_devices,
                    SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as error_devices,
                    AVG(error_count) as avg_error_count
                FROM device_main
                WHERE user_id = :user_id
            """), {"user_id": current_user.id}).fetchone()
        
        if stats:
            return success_response(data={
                "total_devices": int(stats.total_devices or 0),
                "active_devices": int(stats.active_devices or 0),
                "online_devices": int(stats.online_devices or 0),
                "error_devices": int(stats.error_devices or 0),
                "avg_error_count": float(stats.avg_error_count or 0)
            })
        else:
            return success_response(data={
                "total_devices": 0,
                "active_devices": 0,
                "online_devices": 0,
                "error_devices": 0,
                "avg_error_count": 0.0
            })
    except Exception as e:
        logger.error(f"获取设备统计失败: {e}", exc_info=True)
        return success_response(data={
            "total_devices": 0,
            "active_devices": 0,
            "online_devices": 0,
            "error_devices": 0,
            "avg_error_count": 0.0
        })


@router.get("/by-product/{product_id}")
def get_devices_by_product(
    product_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定产品的所有设备 - 数据权限控制：只返回用户注册的设备，管理员可以看到所有设备"""
    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 权限检查：普通用户只能访问系统内置产品和自己创建的产品
    accessible_product_ids = get_accessible_product_ids(db, current_user)
    if product_id not in accessible_product_ids:
        raise HTTPException(
            status_code=403,
            detail="无权访问该产品"
        )
    
    # 数据权限过滤：管理员可以看到所有设备，普通用户只能看到自己注册的设备
    if is_admin_user(current_user):
        devices = db.execute(text("""
            SELECT d.*
            FROM device_main d
            WHERE d.product_id = :product_id
            ORDER BY d.created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"product_id": product_id, "limit": limit, "skip": skip}).fetchall()
    else:
        devices = db.execute(text("""
            SELECT d.*
            FROM device_main d
            WHERE d.product_id = :product_id AND d.user_id = :user_id
            ORDER BY d.created_at DESC
        LIMIT :limit OFFSET :skip
    """), {"product_id": product_id, "user_id": current_user.id, "limit": limit, "skip": skip}).fetchall()
    
    # 将 Row 对象转换为字典
    return success_response(data=[dict(device._mapping) for device in devices])


@router.post("/{device_uuid}/activate")
def activate_device(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """激活设备
    
    注意：学生即使通过PBL授权可以使用设备，也不能激活/停用设备
    只有设备所有者和管理员可以激活设备
    """
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 配置权限检查：只有设备所有者和管理员可以激活设备
    if not can_configure_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权激活该设备（学生只能使用授权设备，不能配置设备）"
        )
    
    device.is_active = True
    db.commit()
    
    return success_response(message="设备激活成功")


@router.post("/{device_uuid}/deactivate")
def deactivate_device(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停用设备
    
    注意：学生即使通过PBL授权可以使用设备，也不能停用设备
    只有设备所有者和管理员可以停用设备
    """
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 配置权限检查：只有设备所有者和管理员可以停用设备
    if not can_configure_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权停用该设备（学生只能使用授权设备，不能配置设备）"
        )
    
    device.is_active = False
    db.commit()
    
    return success_response(message="设备停用成功")


@router.get("/{device_uuid}/product-info")
def get_device_product_info(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备的产品信息 - 数据权限控制：只能访问自己注册的设备，管理员可以看到所有设备"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查：管理员可以访问所有设备，普通用户只能访问自己注册的设备
    if not can_access_device(device, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="无权访问该设备"
        )
    
    device_info = db.execute(text("""
        SELECT 
            d.id, d.name, d.uuid,
            p.id as product_id, p.name as product_name, p.product_code,
            p.category as product_category, p.firmware_version, p.hardware_version,
            p.manufacturer
        FROM device_main d
        LEFT JOIN device_products p ON d.product_id = p.id
        WHERE d.uuid = :device_uuid
    """), {"device_uuid": device_uuid}).fetchone()
    
    if not device_info:
        raise HTTPException(status_code=404, detail="设备信息不存在")
    
    # 将 Row 对象转换为字典
    return success_response(data=dict(device_info._mapping))

@router.post("/{device_uuid}/heartbeat")
async def device_heartbeat(
    device_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设备心跳（模拟设备在线状态更新）"""
    device = db.query(Device).filter(
        Device.uuid == device_uuid,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 更新设备在线状态和最后心跳时间
    device.is_online = True
    device.last_seen = get_beijing_now()
    
    db.commit()
    
    return success_response(message="心跳更新成功")

@router.post("/pre-register", response_model=DeviceResponseWithStatus)
async def pre_register_device(
    device_data: DevicePreRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """前端页面预注册设备 - 输入MAC地址，生成UUID，绑定产品
    
    支持已解绑设备重新注册：
    - 如果MAC地址对应的设备已解绑（user_id为None），允许重新绑定新产品和用户
    - 如果MAC地址对应的设备已绑定其他用户，则拒绝注册
    - 如果MAC地址不存在，创建新设备记录
    
    支持所有用户注册设备：
    - 所有用户都可以注册设备
    - 教师注册的设备自动设置school_id
    - 设备归注册用户所有（user_id = 注册用户ID）
    """
    # 教师注册设备时必须关联学校
    if current_user.role == 'teacher' and not current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="教师账号未关联学校，无法注册设备"
        )
    # 检查MAC地址是否已存在
    existing_device = db.query(Device).filter(Device.mac_address == device_data.mac_address).first()
    
    if existing_device:
        # 设备已存在，检查是否已解绑
        if existing_device.user_id is not None:
            # 设备已绑定其他用户，不允许重新注册
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该MAC地址已被其他用户注册，无法重新注册"
            )
        # 设备已解绑（user_id为None），允许重新绑定
        logger.info(
            f"检测到已解绑设备，MAC地址: {device_data.mac_address}, "
            f"原设备UUID: {existing_device.uuid}, 将重新绑定到用户: {current_user.id}"
        )
    
    # 验证产品是否存在且激活
    product = db.query(Product).filter(Product.id == device_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="所选产品不存在"
        )
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="所选产品已停用，请选择其他产品"
        )
    
    from app.models.device import DeviceStatus
    
    if existing_device and existing_device.user_id is None:
        # 重新绑定已解绑的设备 - 必须生成新的UUID和密钥
        old_device_id = existing_device.device_id
        old_uuid = existing_device.uuid
        
        # 生成新的设备ID、UUID和密钥
        device_id = f"AIOT-ESP32-{uuid.uuid4().hex[:8].upper()}"
        device_uuid = str(uuid.uuid4())
        device_secret = uuid.uuid4().hex
        
        # 更新设备信息
        existing_device.name = device_data.name
        existing_device.description = device_data.description
        existing_device.device_id = device_id  # 更新设备ID
        existing_device.uuid = device_uuid  # 更新UUID
        existing_device.device_secret = device_secret  # 更新密钥
        existing_device.product_id = device_data.product_id  # 重新绑定产品
        existing_device.user_id = current_user.id  # 重新绑定用户
        existing_device.device_status = DeviceStatus.BOUND.value
        existing_device.updated_at = get_beijing_now()
        existing_device.is_online = False  # 重置在线状态
        
        # 设置学校ID（教师注册的设备自动关联学校）
        if current_user.school_id:
            existing_device.school_id = current_user.school_id
        
        # 如果产品有默认配置，应用到设备
        if product.default_device_config:
            if 'device_sensor_config' in product.default_device_config:
                existing_device.device_sensor_config = product.default_device_config.get('device_sensor_config')
            if 'device_control_config' in product.default_device_config:
                existing_device.device_control_config = product.default_device_config.get('device_control_config')
        
        db_device = existing_device
        
        logger.info(
            f"✅ 已解绑设备重新绑定成功: {device_data.name} "
            f"(MAC: {device_data.mac_address}, 旧UUID: {old_uuid} -> 新UUID: {device_uuid}) "
            f"- 用户: {current_user.username} ({current_user.id}) "
            f"- 产品: {product.name} ({product.product_code})"
        )
    else:
        # 创建新设备记录
        device_id = f"AIOT-ESP32-{uuid.uuid4().hex[:8].upper()}"
        device_uuid = str(uuid.uuid4())
        device_secret = uuid.uuid4().hex
        
        db_device = Device(
            name=device_data.name,
            description=device_data.description,
            device_id=device_id,
            uuid=device_uuid,
            device_secret=device_secret,
            mac_address=device_data.mac_address,
            product_id=device_data.product_id,  # 直接绑定产品
            user_id=current_user.id,
            device_status=DeviceStatus.BOUND.value,  # 已绑定产品，状态为BOUND (使用.value获取字符串)
            is_online=False
        )
        
        # 设置学校ID（教师注册的设备自动关联学校）
        if current_user.school_id:
            db_device.school_id = current_user.school_id
        
        # 如果产品有默认配置，应用到设备
        if product.default_device_config:
            if 'device_sensor_config' in product.default_device_config:
                db_device.device_sensor_config = product.default_device_config.get('device_sensor_config')
            if 'device_control_config' in product.default_device_config:
                db_device.device_control_config = product.default_device_config.get('device_control_config')
        
        db.add(db_device)
        
        # 更新产品的设备总数
        product.total_devices = (product.total_devices or 0) + 1
        
        logger.info(
            f"✅ 新设备注册成功: {device_data.name} "
            f"(MAC: {device_data.mac_address}, UUID: {device_uuid}) "
            f"- 用户: {current_user.username} ({current_user.id}) "
            f"- 产品: {product.name} ({product.product_code})"
        )
    
    db.commit()
    # 注意：不使用 db.refresh()，避免ENUM大小写不匹配问题
    # 直接返回创建的对象，字段值已经正确
    # db.refresh(db_device)
    
    return db_device

@router.post("/mac/lookup", response_model=DeviceMacRegisterResponse)
async def lookup_device_by_mac(
    mac_data: DeviceMacRegister,
    db: Session = Depends(get_db)
):
    """设备通过MAC地址查询UUID和凭证 - 设备端调用"""
    # 查找MAC地址对应的设备
    device = db.query(Device).filter(Device.mac_address == mac_data.mac_address).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该MAC地址未注册，请先在管理页面注册设备"
        )
    
    # 更新设备信息（如果提供了）
    if mac_data.firmware_version:
        device.firmware_version = mac_data.firmware_version
    if mac_data.hardware_version:
        device.hardware_version = mac_data.hardware_version
    
    # 更新最后查询时间
    device.last_seen = get_beijing_now()
    device.updated_at = get_beijing_now()
    
    db.commit()
    db.refresh(device)
    
    return DeviceMacRegisterResponse(
        device_id=device.device_id,
        device_uuid=device.uuid,
        device_secret=device.device_secret,
        mac_address=device.mac_address,
        message="设备信息查询成功",
        registered_at=device.updated_at
    )

@router.post("/register")
async def register_device(
    register_data: DeviceRegister,
    db: Session = Depends(get_db)
):
    """设备注册接口 - 设备首次连接时调用，支持动态产品绑定"""
    # 验证设备ID和密钥
    device = db.query(Device).filter(
        Device.device_id == register_data.device_id,
        Device.device_secret == register_data.device_secret
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备ID或密钥无效"
        )
    
    # 更新设备基本信息
    device.firmware_version = register_data.firmware_version
    device.hardware_version = register_data.hardware_version
    device.ip_address = register_data.ip_address
    device.mac_address = register_data.mac_address
    device.is_online = True
    device.last_seen = get_beijing_now()
    device.updated_at = get_beijing_now()
    
    # 如果设备还没有绑定产品，且提供了产品信息，则进行动态绑定
    from app.models.device import DeviceStatus
    response_data = {
        "message": "设备注册成功",
        "device_id": device.device_id,
        "registered_at": device.updated_at,
        "device_status": device.device_status.value if device.device_status else "PENDING"
    }
    
    # 检查是否需要进行产品绑定
    if (device.device_status == DeviceStatus.PENDING.value and 
        register_data.product_code):
        
        try:
            # 使用设备产品服务处理产品绑定
            device_product_service = DeviceProductService(db)
            
            result = device_product_service.handle_product_report(
                device=device,
                product_code=register_data.product_code,
                product_version=register_data.product_version or '1.0',
                device_capabilities=register_data.device_capabilities,
                sensor_config=register_data.device_sensor_config,
                control_config=register_data.device_control_config
            )
            
            response_data.update({
                "product_binding": {
                    "product_id": result["product_id"],
                    "product_name": result["product_name"],
                    "binding_type": result["binding_type"]
                },
                "device_status": device.device_status.value
            })
            
        except Exception as e:
            # 产品绑定失败，但设备注册仍然成功
            response_data["product_binding_error"] = f"产品绑定失败: {str(e)}"
    else:
        # 更新设备配置信息（如果没有产品绑定）
        if register_data.device_sensor_config:
            device.device_sensor_config = register_data.device_sensor_config
        if register_data.device_control_config:
            device.device_control_config = register_data.device_control_config
        # 注意：device_capabilities 是产品级别的配置，不在设备级别设置
    
    db.commit()
    db.refresh(device)
    
    return response_data

@router.get("/{device_uuid}/config")
async def get_device_config(
    device_uuid: str,
    limit: int = Query(20, ge=1, le=200, description="返回最近的传感器数据条数"),
    db: Session = Depends(get_db)
):
    """获取设备配置信息 - 无权限校验
    
    ⚠️  新架构说明：
    - 新版插件服务使用 plugin-backend-service，不再调用此接口
    - 此接口主要供前端或其他内部服务使用
    - 保留此接口以支持前端和兼容性
    - 已移除权限校验，任何人都可以访问
    """
    # 使用joinedload预加载产品信息，避免N+1查询问题
    device = db.query(Device).options(joinedload(Device.product)).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限校验已移除 - 允许任何人访问设备配置
    logger.info(f"🔓 访问设备配置（无权限校验）: device_uuid={device_uuid}")

    # 直接从 device_sensors 表获取最新数据（按时间倒序，limit 条）
    sensor_rows = db.query(DeviceSensor).filter(
        DeviceSensor.device_uuid == device_uuid
    ).order_by(DeviceSensor.timestamp.desc()).limit(limit).all()

    if sensor_rows:
        data_list = []
        latest_by_sensor = {}
        for row in sensor_rows:
            item = {
                "sensor_name": row.sensor_name,
                "value": row.sensor_value,
                "unit": row.sensor_unit or "",
                "sensor_type": row.sensor_type or "",
                "timestamp": row.timestamp.isoformat() if row.timestamp else None
            }
            data_list.append(item)
            if row.sensor_name not in latest_by_sensor:
                latest_by_sensor[row.sensor_name] = item

        return success_response(data={
            "device_uuid": device_uuid,
            "device_name": device.name,
            "latest": latest_by_sensor,
            "logs": data_list,
            "count": len(data_list)
        })
    
    # 从 device_settings 中获取用户自定义的预设指令
    device_settings = device.device_settings or {}
    device_preset_commands = device_settings.get("preset_commands", [])
    
    return success_response(data={
        "device_sensor_config": device.device_sensor_config or {},
        "device_control_config": device.device_control_config or {},
        "device_preset_commands": device_preset_commands,
        "firmware_version": device.firmware_version,
        "hardware_version": device.hardware_version,
        "product_sensor_types": device.product.sensor_types if device.product else {},
        "product_control_ports": device.product.control_ports if device.product else {},
        "device_capabilities": device.product.device_capabilities if device.product else {}
    })

@router.get("/{device_uuid}/full-config")
async def get_device_full_config(
    device_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设备的完整配置信息（包括产品配置）"""
    # 获取设备信息及其关联的产品信息
    device_info = db.execute(text("""
        SELECT 
            d.id, d.name, d.device_id, d.uuid, d.device_status,
            d.is_online, d.last_seen, d.firmware_version, d.hardware_version,
            d.device_sensor_config, d.device_control_config,
            d.product_id, d.product_code, d.product_version,
            p.id as product_id, p.name as product_name, p.product_code as product_code_db,
            p.sensor_types, p.control_ports, p.device_capabilities as product_capabilities,
            p.default_device_config, p.category, p.manufacturer
        FROM device_main d
        LEFT JOIN device_products p ON d.product_id = p.id
        WHERE d.uuid = :device_uuid
    """), {"device_uuid": device_uuid}).fetchone()
    
    if not device_info:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查：管理员可以访问所有设备，普通用户只能访问自己注册的设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    if not can_access_device(device, current_user, db):
        raise HTTPException(status_code=403, detail="无权访问该设备")
    
    if not device_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 构建响应数据
    result = {
        "device_info": {
            "id": device_info.id,
            "name": device_info.name,
            "device_id": device_info.device_id,
            "uuid": device_info.uuid,
            "device_type": device_info.device_type,
            "is_online": device_info.is_online,
            "last_seen": device_info.last_seen.isoformat() if device_info.last_seen else None,
            "firmware_version": device_info.firmware_version,
            "hardware_version": device_info.hardware_version,
            "product_code": device_info.product_code,
            "product_version": device_info.product_version
        },
        "product_info": None,
        "sensor_config": {},
        "control_config": {},
        "device_capabilities": {}
    }
    
    # 如果设备关联了产品，添加产品信息
    if device_info.product_id:
        result["product_info"] = {
            "id": device_info.product_id,
            "name": device_info.product_name,
            "product_code": device_info.product_code_db,
            "category": device_info.category,
            "manufacturer": device_info.manufacturer
        }
        
        # 合并传感器配置：产品配置作为基础，设备配置覆盖
        product_sensor_config = device_info.sensor_types or {}
        device_sensor_config = device_info.device_sensor_config or {}
        result["sensor_config"] = {**product_sensor_config, **device_sensor_config}
        
        # 合并控制配置：产品配置作为基础，设备配置覆盖
        product_control_config = device_info.control_ports or {}
        device_control_config = device_info.device_control_config or {}
        result["control_config"] = {**product_control_config, **device_control_config}
        
        # 设备能力来自产品配置
        product_capabilities = device_info.product_capabilities or {}
        result["device_capabilities"] = product_capabilities
    else:
        # 如果没有关联产品，只使用设备自身的配置
        result["sensor_config"] = device_info.device_sensor_config or {}
        result["control_config"] = device_info.device_control_config or {}
        result["device_capabilities"] = {}  # 没有产品时，capabilities为空
    
    return result

@router.put("/{device_uuid}/config")
async def update_device_config(
    device_uuid: str,
    config_data: dict,
    db: Session = Depends(get_db)
):
    """更新设备配置信息 - 无权限校验"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限校验已移除 - 允许任何人更新设备配置
    logger.info(f"🔓 更新设备配置（无权限校验）: device_uuid={device_uuid}")
    
    # 更新配置字段
    if "device_sensor_config" in config_data:
        device.device_sensor_config = config_data["device_sensor_config"]
    if "device_control_config" in config_data:
        device.device_control_config = config_data["device_control_config"]
    
    # 更新用户自定义的预设指令（保存到 device_settings）
    if "device_preset_commands" in config_data:
        device_settings = device.device_settings or {}
        device_settings["preset_commands"] = config_data["device_preset_commands"]
        device.device_settings = device_settings
        # 标记JSON字段已修改（SQLAlchemy需要）
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(device, "device_settings")
    
    # 注意：device_capabilities 是产品级别的配置，不在设备级别更新
    
    device.updated_at = get_beijing_now()
    
    db.commit()
    db.refresh(device)
    
    return success_response(message="设备配置更新成功")

@router.post("/data/upload")
async def upload_device_data(
    data: DeviceDataUpload,
    db: Session = Depends(get_db)
):
    """设备数据上传 - 存储每个传感器的最后一次数据和上传时间"""
    # 验证设备ID和密钥
    device = db.query(Device).filter(
        Device.device_id == data.device_id,
        Device.device_secret == data.device_secret
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备ID或密钥无效"
        )
    
    # 获取当前时间（北京时间）
    current_time = get_beijing_now()
    
    # 更新设备最后在线时间
    device.last_seen = current_time
    device.is_online = True
    
    # 如果有IP地址信息，更新设备IP
    if hasattr(data, 'status') and data.status and 'ip_address' in data.status:
        device.ip_address = data.status['ip_address']
    
    # 构建传感器数据存储结构
    sensor_data_dict = {}
    if data.sensors:
        for sensor in data.sensors:
            # 使用传感器名称作为key，存储值、单位和时间戳
            sensor_data_dict[sensor.sensor_name] = {
                "value": sensor.value,
                "unit": sensor.unit,
                "timestamp": sensor.timestamp.isoformat() if sensor.timestamp else current_time.isoformat()
            }
    
    # 更新设备的最后上报数据（JSON格式）
    device.last_report_data = {
        "sensors": sensor_data_dict,
        "status": data.status if data.status else {},
        "location": data.location if data.location else {},
        "upload_timestamp": current_time.isoformat()  # 整体上传时间
    }
    
    # 标记JSON字段已修改（SQLAlchemy需要）
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(device, "last_report_data")
    
    db.commit()
    db.refresh(device)
    
    logger.info(
        f"✅ 设备数据上传成功 - 设备: {device.name} ({data.device_id}), "
        f"传感器数量: {len(sensor_data_dict)}, "
        f"传感器: {list(sensor_data_dict.keys())}"
    )
    
    return success_response(
        message="数据上传成功",
        data={
            "device_id": data.device_id,
            "device_name": device.name,
            "upload_timestamp": format_datetime_beijing(current_time),
            "sensors_count": len(sensor_data_dict),
            "sensors_uploaded": list(sensor_data_dict.keys())
        }
    )

@router.post("/status/update")
async def update_device_status(
    status_data: DeviceStatusUpdate,
    db: Session = Depends(get_db)
):
    """设备状态更新"""
    # 验证设备ID和密钥
    device = db.query(Device).filter(
        Device.device_id == status_data.device_id,
        Device.device_secret == status_data.device_secret
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备ID或密钥无效"
        )
    
    # 更新设备状态
    device.is_online = (status_data.status == "online")
    device.last_seen = get_beijing_now()
    
    # 更新其他信息
    if status_data.ip_address:
        device.ip_address = status_data.ip_address
    if status_data.firmware_version:
        device.firmware_version = status_data.firmware_version
    
    db.commit()
    
    return success_response(
        message="设备状态更新成功",
        data={
            "device_id": status_data.device_id,
            "status": status_data.status,
            "timestamp": format_datetime_beijing(get_beijing_now())
        }
    )

@router.post("/product/report")
async def report_product_info(
    product_data: DeviceProductReport,
    db: Session = Depends(get_db)
):
    """设备启动后上报产品信息 - 支持动态产品绑定"""
    # 验证设备ID和密钥
    device = db.query(Device).filter(
        Device.device_id == product_data.device_id,
        Device.device_secret == product_data.device_secret
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备ID或密钥无效"
        )
    
    # 使用设备产品服务处理产品信息上报
    device_product_service = DeviceProductService(db)
    
    try:
        result = device_product_service.handle_product_report(
            device=device,
            product_code=product_data.product_code,
            product_version=product_data.product_version,
            device_capabilities=product_data.capabilities,
            sensor_config=None,  # DeviceProductReport 模式中没有这个字段
            control_config=None  # DeviceProductReport 模式中没有这个字段
        )
        
        db.commit()
        
        return success_response(
            message="产品信息上报成功",
            data={
                "device_id": device.device_id,
                "product_id": result["product_id"],
                "product_name": result["product_name"],
                "binding_type": result["binding_type"],
                "device_status": device.device_status.value,
                "updated_at": get_beijing_now()
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"产品信息处理失败: {str(e)}"
        )

@router.post("/product/switch")
async def switch_product(
    switch_data: DeviceProductSwitch,
    db: Session = Depends(get_db)
):
    """设备产品切换 - 同一MAC地址设备切换到不同产品"""
    # 验证设备ID和密钥
    device = db.query(Device).filter(
        Device.device_id == switch_data.device_id,
        Device.device_secret == switch_data.device_secret
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备ID或密钥无效"
        )
    
    # 使用设备产品服务处理产品切换
    device_product_service = DeviceProductService(db)
    
    try:
        result = device_product_service.handle_product_switch(
            device=device,
            new_product_code=switch_data.new_product_code,
            new_product_version=switch_data.new_product_version,
            device_capabilities=None,  # DeviceProductSwitch 模式中没有这个字段
            sensor_config=None,  # DeviceProductSwitch 模式中没有这个字段
            control_config=None,  # DeviceProductSwitch 模式中没有这个字段
            switch_reason=switch_data.reason
        )
        
        db.commit()
        
        return success_response(
            message="产品切换成功",
            data={
                "device_id": device.device_id,
                "old_product_id": result["old_product_id"],
                "new_product_id": result["new_product_id"],
                "new_product_name": result["new_product_name"],
                "switch_count": device.product_switch_count,
                "device_status": device.device_status.value,
                "switched_at": get_beijing_now()
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"产品切换失败: {str(e)}"
        )

@router.get("/{device_uuid}/product-history")
async def get_device_product_history(
    device_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设备产品切换历史 - 数据权限控制：只能访问自己注册的设备，管理员可以看到所有设备"""
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 数据权限检查：管理员可以访问所有设备，普通用户只能访问自己注册的设备
    if not can_access_device(device, current_user, db):
        raise HTTPException(status_code=403, detail="无权访问该设备")
    
    # 查询产品切换历史
    history_query = text("""
        SELECT 
            dph.*,
            p_old.name as old_product_name,
            p_new.name as new_product_name
        FROM aiot_device_product_history dph
        LEFT JOIN device_products p_old ON dph.old_product_id = p_old.id
        LEFT JOIN device_products p_new ON dph.new_product_id = p_new.id
        WHERE dph.device_id = :device_id
        ORDER BY dph.switched_at DESC
    """)
    
    result = db.execute(history_query, {"device_id": device.id})
    history = result.fetchall()
    
    return success_response(data={
        "device_id": device.id,
        "device_uuid": device.uuid,
        "device_name": device.name,
        "current_product_id": device.product_id,
        "switch_count": device.product_switch_count,
        "history": [
            {
                "id": row.id,
                "old_product_id": row.old_product_id,
                "old_product_name": row.old_product_name,
                "new_product_id": row.new_product_id,
                "new_product_name": row.new_product_name,
                "switch_reason": row.switch_reason,
                "switched_at": row.switched_at,
                "old_config": row.old_config,
                "new_config": row.new_config
            }
            for row in history
        ]
    })

@router.get("/{device_uuid}/sensor-data")
async def get_device_sensor_data(
    device_uuid: str,
    user_or_internal = Depends(verify_internal_or_user),
    db: Session = Depends(get_db)
):
    """获取设备传感器的最后一次数据 - 支持JWT和内部API密钥认证
    
    认证方式：
    1. JWT Token（用户请求，前端调用）
    2. X-Internal-API-Key（内部服务）
    
    返回格式：
    {
        "device_uuid": "xxx",
        "device_name": "设备名称",
        "upload_timestamp": "2025-12-19T14:30:00+08:00",
        "sensors": {
            "temperature": {
                "value": 25.5,
                "unit": "°C",
                "timestamp": "2025-12-19T14:30:00+08:00"
            },
            "humidity": {
                "value": 60,
                "unit": "%",
                "timestamp": "2025-12-19T14:30:00+08:00"
            }
        }
    }
    """
    # 查找设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查：内部API调用跳过权限检查，用户请求需要验证权限
    if user_or_internal != "internal":
        # 用户请求：检查数据权限
        if not can_access_device(device, user_or_internal, db):
            raise HTTPException(status_code=403, detail="无权访问该设备")
    else:
        # 内部API调用：跳过权限检查
        logger.info(f"🔓 内部API调用，跳过权限检查: device_uuid={device_uuid}")
    
    # 获取最后上报的数据
    if not device.last_report_data:
        return success_response(data={
            "device_uuid": device_uuid,
            "device_name": device.name,
            "upload_timestamp": None,
            "sensors": {},
            "status": {},
            "location": {},
            "message": "设备尚未上报数据"
        })
    
    # 返回最后一次上报的所有传感器数据
    return success_response(data={
        "device_uuid": device_uuid,
        "device_name": device.name,
        "upload_timestamp": device.last_report_data.get("upload_timestamp"),
        "sensors": device.last_report_data.get("sensors", {}),
        "status": device.last_report_data.get("status", {}),
        "location": device.last_report_data.get("location", {}),
        "last_seen": format_datetime_beijing(device.last_seen)
    })


@router.get("/{device_uuid}/realtime-data")
async def get_device_realtime_data(
    device_uuid: str,
    limit: int = Query(10, ge=1, le=100, description="返回最近的数据条数"),
    db: Session = Depends(get_db)
):
    """获取设备实时传感器数据 - 无权限校验
    
    ⚠️  已废弃：请使用 /{device_uuid}/sensor-data 接口
    
    ⚠️  新架构说明：
    - 新版插件服务使用 plugin-backend-service 直接访问数据库，不再调用此接口
    - 此接口主要供前端查看实时数据使用
    - 保留此接口以支持前端和兼容性
    - 已移除权限校验，任何人都可以访问
    """
    from sqlalchemy.orm import joinedload
    from datetime import timezone, timedelta
    
    # 查找设备（预加载产品信息）
    device = db.query(Device).options(joinedload(Device.product)).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 权限校验已移除 - 允许任何人访问设备数据
    logger.info(f"🔓 访问设备实时数据（无权限校验）: device_uuid={device_uuid}")
    
    # 统一时区（数据库存北京时间）
    beijing_tz = timezone(timedelta(hours=8))
    
    def _parse_sensor_value(value: str):
        """尝试将字符串转成数字/布尔，便于前端展示"""
        if value is None:
            return None
        v = str(value).strip()
        if v.lower() in ["true", "false"]:
            return v.lower() == "true"
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return value
    
    # 解析产品传感器配置（用于按配置键映射）
    import json
    product_sensor_types = None
    if device.product and device.product.sensor_types:
        sensor_types_raw = device.product.sensor_types
        if isinstance(sensor_types_raw, str):
            try:
                product_sensor_types = json.loads(sensor_types_raw)
            except Exception as e:
                logger.error(f"❌ 解析产品传感器配置失败: {e}")
                product_sensor_types = {}
        else:
            product_sensor_types = sensor_types_raw
        logger.info(f"🔍 产品传感器配置键: {list(product_sensor_types.keys()) if product_sensor_types else []}")
    else:
        logger.warning("⚠️ 设备没有关联产品或产品没有传感器配置")
    
    # 表对 device_uuid + sensor_name 有唯一约束，一个传感器只保留一条最新数据
    # 因此直接全量按时间倒序抓取该设备的所有传感器记录
    sensor_rows = db.query(DeviceSensor).filter(
        DeviceSensor.device_uuid == device_uuid
    ).order_by(DeviceSensor.timestamp.desc()).all()
    
    logger.info(f"🔍 从 device_sensors 取到 {len(sensor_rows)} 条数据 (device_uuid={device_uuid}, requested_limit={limit})")
    
    if not sensor_rows:
        return success_response(data={
            "device_uuid": device_uuid,
            "device_name": device.name,
            "latest": None,
            "data": [],
            "count": 0,
            "message": "device_sensors 表暂无数据"
        })
    
    # 构造返回数据
    # data 列表只返回用户请求的数量；latest 计算使用 fetch_limit 结果
    sensor_data_list = []
    raw_latest_map = {}
    latest_timestamp = None
    
    for row in sensor_rows:
        value = _parse_sensor_value(row.sensor_value)
        row_time = row.timestamp
        if row_time and row_time.tzinfo is None:
            row_time = row_time.replace(tzinfo=beijing_tz)
        
        # 用于列表展示（保持旧格式兼容），仅保留前 limit 条
        if len(sensor_data_list) < limit:
            sensor_data_list.append({
                "timestamp": row_time.isoformat() if row_time else None,
                "data": {row.sensor_name: value},
                "unit": row.sensor_unit or "",
                "sensor_type": row.sensor_type or ""
            })
        
        # 汇总 latest
        if row.sensor_name not in raw_latest_map:
            raw_latest_map[row.sensor_name] = value
            if not latest_timestamp or (row_time and row_time > latest_timestamp):
                latest_timestamp = row_time
    
    # 如果有产品配置，则按配置键映射值，确保前端卡片能直接匹配
    mapped_latest = None
    if product_sensor_types:
        mapped_latest = {key: None for key in product_sensor_types.keys()}
        for key, config in product_sensor_types.items():
            data_field = config.get("data_field")
            cfg_type = (config.get("type") or "").upper()
            # 规则1：sensor_name 与配置key完全一致
            if key in raw_latest_map:
                mapped_latest[key] = raw_latest_map[key]
                continue
            # 规则2：sensor_type一致且 data_field 与 sensor_name 对应
            for row in sensor_rows:
                if (row.sensor_type or "").upper() == cfg_type and data_field and row.sensor_name == data_field:
                    mapped_latest[key] = raw_latest_map.get(row.sensor_name)
                    break
        logger.info(f"✅ 按产品配置映射后的字段: {mapped_latest}")
    
    latest_payload = {
        "timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
        "data": mapped_latest if mapped_latest is not None else raw_latest_map
    }
    
    logger.info(f"✅ 最新数据字段: {list(latest_payload['data'].keys())}, 时间: {latest_timestamp}")
    
    return success_response(data={
        "device_uuid": device_uuid,
        "device_name": device.name,
        "latest": latest_payload,
        "data": sensor_data_list,
        "count": len(sensor_data_list)
    })


@router.get("/{device_uuid}/presets")
async def get_device_presets(
    device_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取设备的预设控制指令 - 根据产品配置动态生成
    只保留基本控制 + 少量典型预设
    """
    # 查找设备并预加载产品信息
    from sqlalchemy.orm import joinedload
    device = db.query(Device).options(joinedload(Device.product)).filter(Device.uuid == device_uuid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 数据权限检查
    if not can_access_device(device, current_user, db):
        raise HTTPException(status_code=403, detail="无权访问该设备")
    
    if not device.product:
        raise HTTPException(status_code=400, detail="设备未关联产品")
    
    presets = []
    control_ports = device.product.control_ports or {}
    
    # 根据产品配置的control_ports动态生成基本控制
    for port_key, port_config in control_ports.items():
        if not isinstance(port_config, dict):
            continue
            
        port_type = port_config.get("type", "").upper()
        port_name = port_config.get("name", port_key)
        device_id = port_config.get("device_id", 1)
        
        # LED/Relay: 开关控制
        if port_type in ["LED", "RELAY"]:
            presets.append({
                "id": f"{port_key}_switch",
                "name": f"{port_name}",
                "type": "device_control",
                "cmd": port_type.lower(),
                "device_type": port_type.lower(),  # 使用小写，与固件期望一致
                "device_id": device_id,
                "description": f"控制{port_name}的开关",
                "control_type": "switch"
            })
        
        # Servo: 速度控制 + 停止按钮
        elif port_type == "SERVO":
            presets.extend([
                {
                    "id": f"{port_key}_speed",
                    "name": f"{port_name} - 速度",
                    "type": "device_control",
                    "cmd": "servo",
                    "device_type": "servo",  # 使用小写，与固件期望一致
                    "device_id": device_id,
                    "description": f"控制{port_name}速度(90=停止)",
                    "control_type": "speed",
                    "min": 0,
                    "max": 180,
                    "default": 90
                },
                {
                    "id": f"{port_key}_stop",
                    "name": f"{port_name} - 停止",
                    "type": "device_control",
                    "cmd": "servo",
                    "device_type": "servo",  # 使用小写，与固件期望一致
                    "device_id": device_id,
                    "description": f"停止{port_name}",
                    "control_type": "stop"
                }
            ])
    
    # 添加少量典型预设指令
    # 只为第一个LED添加闪烁预设作为示例
    first_led = next((p for p in presets if p["cmd"] == "led"), None)
    if first_led:
        presets.append({
            "id": f"{first_led['id']}_blink",
            "name": f"{first_led['name']} - 闪烁",
            "type": "preset",
            "cmd": "preset",
            "device_type": "led",  # 使用小写，与固件期望一致
            "device_id": first_led["device_id"],
            "preset_type": "blink",
            "description": "LED闪烁效果",
            "parameters": {
                "duration": 5,
                "interval": 500
            }
        })
        
        # 添加LED打开5秒后关闭的序列预设
        presets.append({
            "id": f"{first_led['id']}_timed_on_off",
            "name": f"{first_led['name']} - 定时开关",
            "type": "sequence",
            "cmd": "sequence",
            "description": "LED打开后5秒自动关闭",
            "steps": [
                {
                    "command": {
                        "cmd": "led",
                        "device_type": "led",
                        "device_id": first_led["device_id"],
                        "value": 1
                    },
                    "delay": 0
                },
                {
                    "command": {
                        "cmd": "led",
                        "device_type": "led",
                        "device_id": first_led["device_id"],
                        "value": 0
                    },
                    "delay": 5
                }
            ]
        })
    
    # 为第一个继电器添加定时开关预设
    first_relay = next((p for p in presets if p["cmd"] == "relay"), None)
    if first_relay:
        presets.append({
            "id": f"{first_relay['id']}_timed",
            "name": f"{first_relay['name']} - 定时",
            "type": "preset",
            "cmd": "preset",
            "device_type": "relay",  # 使用小写，与固件期望一致
            "device_id": first_relay["device_id"],
            "preset_type": "timed_switch",
            "description": "继电器定时开关",
            "parameters": {
                "duration": 10
            }
        })
        
        # 添加继电器打开10秒后关闭的序列预设
        presets.append({
            "id": f"{first_relay['id']}_timed_on_off",
            "name": f"{first_relay['name']} - 定时开关",
            "type": "sequence",
            "cmd": "sequence",
            "description": "继电器打开后10秒自动关闭",
            "steps": [
                {
                    "command": {
                        "cmd": "relay",
                        "device_type": "relay",
                        "device_id": first_relay["device_id"],
                        "value": 1
                    },
                    "delay": 0
                },
                {
                    "command": {
                        "cmd": "relay",
                        "device_type": "relay",
                        "device_id": first_relay["device_id"],
                        "value": 0
                    },
                    "delay": 10
                }
            ]
        })
    
    # 统一响应格式
    return success_response(data={"presets": presets})


@router.post("/{device_uuid}/control")
async def control_device(
    device_uuid: str,
    control_data: dict,
    user_or_internal = Depends(verify_internal_or_user),
    db: Session = Depends(get_db)
):
    """发送控制命令到设备 - 支持JWT和内部API密钥认证
    
    认证方式：
    1. JWT Token（用户请求）
    2. X-Internal-API-Key（内部服务，如plugin-service）
    
    支持的控制类型：
    1. 单指令控制：直接发送单个控制命令
    2. 序列指令控制：type="sequence"，包含steps数组，支持延迟执行
    
    序列指令示例：
    {
        "type": "sequence",
        "steps": [
            {"command": {"cmd": "led", "device_id": 1, "value": 1}, "delay": 0},
            {"command": {"cmd": "led", "device_id": 1, "value": 0}, "delay": 5}
        ]
    }
    """
    try:
        # 查找设备
        device = db.query(Device).filter(Device.uuid == device_uuid).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 数据权限检查：内部API调用跳过权限检查，用户请求需要验证权限
        if user_or_internal != "internal":
            # 用户请求：检查数据权限
            accessible_product_ids = get_accessible_product_ids(db, user_or_internal)
            if device.product_id not in accessible_product_ids:
                raise HTTPException(status_code=403, detail="无权访问该设备")
        else:
            # 内部API调用：跳过权限检查
            logger.info(f"🔓 内部API调用，跳过权限检查: device_uuid={device_uuid}")
        
        # 检查设备是否在线
        if not device.is_online:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设备离线，无法发送控制命令"
            )
        
        # 检查是否通过preset_key执行预设
        if "preset_key" in control_data:
            preset_key = control_data["preset_key"]
            logger.info(f"🔑 通过preset_key执行预设: {preset_key}")
            
            # 从设备配置中查找预设
            device_settings = device.device_settings or {}
            preset_commands = device_settings.get("preset_commands", [])
            
            # 查找匹配的预设
            target_preset = None
            for preset in preset_commands:
                if preset.get("preset_key") == preset_key:
                    target_preset = preset
                    break
            
            if not target_preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"未找到预设指令: {preset_key}"
                )
            
            logger.info(f"✅ 找到预设指令: {target_preset.get('name', preset_key)}")
            
            # 根据预设类型执行
            if target_preset.get("type") == "sequence" or target_preset.get("preset_type") == "sequence":
                # 执行序列指令（使用Celery异步执行，不阻塞HTTP请求）
                from app.services.preset_sequence_service import preset_sequence_service
                from app.core.celery_app import celery_app
                
                try:
                    steps = preset_sequence_service.parse_sequence_preset(target_preset)
                    
                    # 提交到Celery队列异步执行
                    task = celery_app.send_task(
                        'execute_preset_sequence',
                        args=[device_uuid, steps]
                    )
                    
                    logger.info(f"✅ 预设序列已提交到Celery: task_id={task.id}, steps={len(steps)}")
                    
                    # 立即返回，不等待执行完成
                    return success_response(
                        message="预设序列已提交，正在后台执行",
                        data={
                            "device_uuid": device_uuid,
                            "task_id": task.id,
                            "total_steps": len(steps),
                            "status_url": f"/api/devices/tasks/{task.id}/status"
                        }
                    )
                    
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"预设序列指令格式错误: {str(e)}"
                    )
                except Exception as e:
                    logger.error(f"提交预设序列任务失败: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"提交任务失败: {str(e)}"
                    )
            else:
                # 执行普通预设指令
                preset_command = {
                    "cmd": "preset",
                    "preset_type": target_preset.get("preset_type"),
                    "device_type": target_preset.get("device_type"),
                    "device_id": target_preset.get("device_id"),
                    "parameters": target_preset.get("parameters", {})
                }
                
                # 直接连接MQTT Broker发送预设指令
                import paho.mqtt.client as mqtt
                from app.core.config import settings
                
                control_topic = f"devices/{device_uuid}/control"
                message = json.dumps(preset_command)
                
                try:
                    # 创建临时MQTT客户端
                    mqtt_client = mqtt.Client(
                        client_id=f"preset_client_{device_uuid}_{int(__import__('time').time())}",
                        protocol=mqtt.MQTTv311
                    )
                    
                    # 设置认证
                    if settings.mqtt_username and settings.mqtt_password:
                        mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
                    
                    # 连接到MQTT Broker
                    mqtt_client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
                    
                    # 发布消息
                    result = mqtt_client.publish(control_topic, message, qos=1)
                    
                    # 等待消息发送完成
                    mqtt_client.loop_start()
                    result.wait_for_publish(timeout=5)
                    mqtt_client.loop_stop()
                    mqtt_client.disconnect()
                    
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        logger.info(f"✅ 预设指令发送成功 - 设备: {device_uuid}, 预设: {target_preset.get('name')}")
                        return success_response(
                            message="预设指令发送成功",
                            data={
                                "device_uuid": device_uuid,
                                "preset_key": preset_key,
                                "preset_name": target_preset.get("name"),
                                "topic": control_topic
                            }
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"MQTT消息发送失败，错误代码: {result.rc}"
                        )
                        
                except Exception as mqtt_error:
                    logger.error(f"❌ 预设指令MQTT发送失败: {mqtt_error}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"MQTT服务连接失败: {str(mqtt_error)}"
                    )
        
        # 检查是否是序列指令
        elif control_data.get("type") == "sequence":
            # 执行序列指令（使用Celery异步执行，不阻塞HTTP请求）
            from app.services.preset_sequence_service import preset_sequence_service
            from app.core.celery_app import celery_app
            
            try:
                steps = preset_sequence_service.parse_sequence_preset(control_data)
                
                # 提交到Celery队列异步执行
                task = celery_app.send_task(
                    'execute_preset_sequence',
                    args=[device_uuid, steps]
                )
                
                logger.info(f"✅ 自定义序列已提交到Celery: task_id={task.id}, steps={len(steps)}")
                
                # 立即返回，不等待执行完成
                return success_response(
                    message="序列指令已提交，正在后台执行",
                    data={
                        "device_uuid": device_uuid,
                        "task_id": task.id,
                        "total_steps": len(steps),
                        "status_url": f"/api/devices/tasks/{task.id}/status"
                    }
                )
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"序列指令格式错误: {str(e)}"
                )
            except Exception as e:
                logger.error(f"提交序列任务失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"提交任务失败: {str(e)}"
                )
            except RuntimeError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
        else:
            # 单指令控制 - 直接连接MQTT Broker发送控制指令
            import paho.mqtt.client as mqtt
            import json
            import time
            from app.core.config import settings
            
            # 构建控制主题
            control_topic = f"devices/{device_uuid}/control"
            
            try:
                # 创建临时MQTT客户端
                client_kwargs = {
                    "client_id": f"control_client_{device_uuid}_{int(time.time())}",
                    "protocol": mqtt.MQTTv311,
                    "transport": "tcp"
                }
                callback_api_version = getattr(mqtt, "CallbackAPIVersion", None)
                if callback_api_version:
                    client_kwargs["callback_api_version"] = callback_api_version.VERSION1

                mqtt_client = mqtt.Client(**client_kwargs)
                
                # 设置认证
                if settings.mqtt_username and settings.mqtt_password:
                    mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
                
                # 连接到MQTT Broker
                mqtt_client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
                
                # 发布消息
                message = json.dumps(control_data)
                result = mqtt_client.publish(control_topic, message, qos=1)
                
                # 等待消息发送完成
                mqtt_client.loop_start()
                result.wait_for_publish(timeout=5)
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"✅ 控制命令发送成功 - 设备: {device_uuid}, 命令: {control_data}")
                    return success_response(
                        message="控制命令发送成功",
                        data={
                            "device_uuid": device_uuid,
                            "command": control_data,
                            "topic": control_topic
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"MQTT消息发送失败，错误代码: {result.rc}"
                    )
                    
            except Exception as mqtt_error:
                logger.error(f"❌ MQTT连接或发送失败: {mqtt_error}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"MQTT服务连接失败: {str(mqtt_error)}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送控制命令失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送控制命令失败: {str(e)}"
        )


@router.get("/{device_uuid}/product-config")
async def get_device_product_config(
    device_uuid: str,
    db: Session = Depends(get_db)
):
    """获取设备的产品配置信息（传感器和控制端口配置）- 公开接口，无需认证"""
    try:
        # 查询设备
        device = db.query(Device).filter(Device.uuid == device_uuid).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 查询产品配置
        if not device.product_id:
            return success_response(data={
                "device_id": device.id,
                "device_name": device.name,
                "device_uuid": device.uuid,
                "product_id": None,
                "product_name": None,
                "sensor_types": {},
                "control_ports": {},
                "message": "设备未绑定产品"
            })
        
        product = db.query(Product).filter(Product.id == device.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        return success_response(data={
            "device_id": device.id,
            "device_name": device.name,
            "device_uuid": device.uuid,
            "product_id": product.id,
            "product_name": product.name,
            "product_code": product.product_code,
            "sensor_types": product.sensor_types or {},
            "control_ports": product.control_ports or {},
            "device_capabilities": product.device_capabilities or {},
            "message": "获取成功"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备产品配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备产品配置失败: {str(e)}"
        )

@router.post("/{device_uuid}/unbind")
async def unbind_device(
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解绑设备 - 自动清除所有历史数据
    
    Args:
        device_uuid: 设备UUID
        
    Returns:
        解绑结果
        
    功能说明:
    - 解除设备与当前用户的绑定关系
    - 清空MAC地址和IP地址，防止设备通过MAC地址查询配置信息
    - 自动清除设备的所有历史数据（传感器数据、交互日志等）
    - 解绑后设备可被其他用户重新绑定，重新绑定时会生成新的UUID和密钥
    """
    try:
        # 查找设备
        device = db.query(Device).filter(Device.uuid == device_uuid).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 配置权限检查：只有设备所有者和管理员可以解绑设备
        if not can_configure_device(device, current_user, db):
            logger.warning(f"用户 {current_user.id} 尝试解绑不属于自己的设备 {device_uuid}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权解绑此设备（学生只能使用授权设备，不能解绑设备）"
            )
        
        device_name = device.name
        device_id = device.device_id  # 设备ID字符串，用于删除历史数据
        mac_address = device.mac_address  # 保存MAC地址用于日志
        
        # 记录解绑历史（在清空MAC地址之前）
        try:
            # 获取产品信息（如果存在）
            product = device.product
            unbind_history = DeviceBindingHistory(
                mac_address=mac_address,  # 使用原始MAC地址
                device_uuid=device.uuid,
                device_id=device.device_id,
                device_name=device.name,
                user_id=current_user.id,
                user_email=current_user.email,
                user_username=current_user.username,
                product_id=product.id if product else None,
                product_code=product.product_code if product else None,
                product_name=product.name if product else None,
                action="unbind",
                action_time=get_beijing_now(),
                notes="用户主动解绑设备"
            )
            db.add(unbind_history)
            logger.info(f"✅ 已记录设备解绑历史: MAC={mac_address}, User={current_user.id}")
        except Exception as e:
            logger.error(f"记录设备解绑历史失败: {e}", exc_info=True)
            # 历史记录失败不影响解绑操作
        
        # 解绑设备（清除user_id和相关网络信息）
        device.user_id = None
        device.mac_address = None  # 清空MAC地址，防止设备通过MAC地址查询配置
        device.ip_address = None  # 清空IP地址
        device.updated_at = get_beijing_now()
        device.is_online = False  # 重置在线状态
        
        # 清除设备最后上报数据（已优化：日志表已删除）
        try:
            # 清空设备的最后上报数据
            device.last_report_data = None
            
            logger.info(f"✅ 已清除设备 {device_uuid} 的最后上报数据")
        except Exception as e:
            logger.error(f"清除设备数据失败: {e}", exc_info=True)
            # 数据清除失败不影响解绑操作，但记录错误
        
        db.commit()
        
        logger.info(
            f"✅ 设备解绑成功: {device_name} ({device_id}, UUID: {device_uuid}) "
            f"- 用户: {current_user.username} ({current_user.id}) "
            f"- MAC地址: {mac_address} (已清空) "
            f"- 已清除所有历史数据"
        )
        
        return success_response(
            message="设备解绑成功，所有历史数据已清除",
            data={
                "device_uuid": device_uuid,
                "device_name": device_name,
                "device_id": device_id,
                "data_cleared": True,
                "unbind_time": format_datetime_beijing(get_beijing_now())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 设备解绑失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设备解绑失败: {str(e)}"
        )

@router.get("/binding-history/{mac_address}")
async def get_device_binding_history(
    mac_address: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询指定MAC地址设备的绑定历史记录 - 仅管理员可访问
    
    返回该MAC地址设备被哪些用户绑定过的完整历史记录
    """
    # 权限检查：只有管理员可以查询绑定历史
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询设备绑定历史"
        )
    
    # 查询该MAC地址的所有绑定历史记录
    history_query = db.query(DeviceBindingHistory).filter(
        DeviceBindingHistory.mac_address == mac_address
    ).order_by(desc(DeviceBindingHistory.action_time))
    
    total = history_query.count()
    history_list = history_query.offset(skip).limit(limit).all()
    
    # 统计信息
    bind_count = db.query(func.count(DeviceBindingHistory.id)).filter(
        DeviceBindingHistory.mac_address == mac_address,
        DeviceBindingHistory.action == "bind"
    ).scalar() or 0
    
    unbind_count = db.query(func.count(DeviceBindingHistory.id)).filter(
        DeviceBindingHistory.mac_address == mac_address,
        DeviceBindingHistory.action == "unbind"
    ).scalar() or 0
    
    # 获取首次绑定时间和最后操作时间
    first_bind = db.query(DeviceBindingHistory).filter(
        DeviceBindingHistory.mac_address == mac_address,
        DeviceBindingHistory.action == "bind"
    ).order_by(DeviceBindingHistory.action_time.asc()).first()
    
    last_action = db.query(DeviceBindingHistory).filter(
        DeviceBindingHistory.mac_address == mac_address
    ).order_by(desc(DeviceBindingHistory.action_time)).first()
    
    # 查询当前绑定状态（如果设备已绑定）
    current_device = db.query(Device).filter(Device.mac_address == mac_address).first()
    current_user_id = None
    current_user_email = None
    if current_device and current_device.user_id:
        current_user_id = current_device.user_id
        current_user_obj = db.query(User).filter(User.id == current_device.user_id).first()
        if current_user_obj:
            current_user_email = current_user_obj.email
    
    return success_response(data={
        "mac_address": mac_address,
        "total_bindings": bind_count,
        "total_unbindings": unbind_count,
        "first_bind_time": first_bind.action_time if first_bind else None,
        "last_action_time": last_action.action_time if last_action else None,
        "current_user_id": current_user_id,
        "current_user_email": current_user_email,
        "total_records": total,
        "history": [
            {
                "id": h.id,
                "device_uuid": h.device_uuid,
                "device_id": h.device_id,
                "device_name": h.device_name,
                "user_id": h.user_id,
                "user_email": h.user_email,
                "user_username": h.user_username,
                "product_id": h.product_id,
                "product_code": h.product_code,
                "product_name": h.product_name,
                "action": h.action,
                "action_time": h.action_time,
                "notes": h.notes,
                "created_at": h.created_at
            }
            for h in history_list
        ]
    })

@router.get("/binding-history")
async def list_all_binding_history(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    mac_address: Optional[str] = Query(None, description="MAC地址筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选：bind/unbind"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询所有设备绑定历史记录 - 仅管理员可访问"""
    # 权限检查：只有管理员可以查询绑定历史
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询设备绑定历史"
        )
    
    query = db.query(DeviceBindingHistory)
    
    # 应用筛选条件
    if mac_address:
        query = query.filter(DeviceBindingHistory.mac_address.like(f"%{mac_address}%"))
    
    if user_id:
        query = query.filter(DeviceBindingHistory.user_id == user_id)
    
    if action:
        query = query.filter(DeviceBindingHistory.action == action)
    
    total = query.count()
    history_list = query.order_by(desc(DeviceBindingHistory.action_time)).offset(skip).limit(limit).all()
    
    return success_response(data={
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": h.id,
                "mac_address": h.mac_address,
                "device_uuid": h.device_uuid,
                "device_id": h.device_id,
                "device_name": h.device_name,
                "user_id": h.user_id,
                "user_email": h.user_email,
                "user_username": h.user_username,
                "product_id": h.product_id,
                "product_code": h.product_code,
                "product_name": h.product_name,
                "action": h.action,
                "action_time": h.action_time,
                "notes": h.notes,
                "created_at": h.created_at
            }
            for h in history_list
        ]
    })


@router.get("/tasks/{task_id}/status", summary="查询任务执行状态")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    查询Celery任务执行状态
    
    用途：
    - 查询预设序列执行状态
    - 查询文档向量化状态
    - 查询其他异步任务状态
    
    返回状态：
    - PENDING: 任务等待执行
    - STARTED: 任务已开始
    - PROGRESS: 任务执行中（带进度信息）
    - SUCCESS: 任务成功完成
    - FAILURE: 任务执行失败
    - RETRY: 任务正在重试
    """
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        # 获取任务结果
        task = AsyncResult(task_id, app=celery_app)
        
        # 构建响应
        response = {
            "task_id": task_id,
            "status": task.state,
            "ready": task.ready()  # 是否已完成（无论成功或失败）
        }
        
        # 根据状态添加额外信息
        if task.state == 'PENDING':
            response["message"] = "任务等待执行"
            
        elif task.state == 'STARTED':
            response["message"] = "任务已开始执行"
            
        elif task.state == 'PROGRESS':
            # 执行中，返回进度信息
            response["message"] = "任务执行中"
            if task.info:
                response["progress"] = {
                    "current": task.info.get('current'),
                    "total": task.info.get('total'),
                    "status": task.info.get('status')
                }
                
        elif task.state == 'SUCCESS':
            # 成功完成，返回结果
            response["message"] = "任务执行成功"
            response["result"] = task.result
            
        elif task.state == 'FAILURE':
            # 执行失败，返回错误信息
            response["message"] = "任务执行失败"
            response["error"] = str(task.info)  # task.info包含异常信息
            
        elif task.state == 'RETRY':
            response["message"] = "任务正在重试"
            if task.info:
                response["retry_info"] = str(task.info)
        
        else:
            # 其他未知状态
            response["message"] = f"任务状态: {task.state}"
        
        return response
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询任务状态失败: {str(e)}"
        )
