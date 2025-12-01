from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DeviceStatus(str, Enum):
    """设备状态枚举"""
    PENDING = "pending"        # 待绑定产品
    BOUND = "bound"           # 已绑定产品
    ACTIVE = "active"         # 激活状态
    OFFLINE = "offline"       # 离线状态
    ERROR = "error"           # 错误状态

class DeviceBase(BaseModel):
    """设备基础模型 - 支持动态产品绑定的两层架构"""
    name: str
    description: Optional[str] = None
    product_id: Optional[int] = None  # 动态绑定，可为空
    device_secret: str
    user_id: Optional[int] = None  # 支持解绑设备，user_id可为None

class DeviceCreate(DeviceBase):
    """创建设备的模式"""
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None
    production_date: Optional[datetime] = None
    quality_grade: Optional[str] = "A"

class DeviceUpdate(BaseModel):
    """更新设备的模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[int] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None
    production_date: Optional[datetime] = None
    quality_grade: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    group_name: Optional[str] = None
    room: Optional[str] = None
    floor: Optional[str] = None
    device_sensor_config: Optional[Dict[str, Any]] = None
    device_control_config: Optional[Dict[str, Any]] = None
    device_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class DevicePreRegister(BaseModel):
    """前端页面预注册设备时的数据"""
    name: str
    device_type: str = "ESP32"
    mac_address: str
    description: Optional[str] = None
    product_id: int  # 产品ID（必填，通过下拉菜单选择）

class DeviceMacRegister(BaseModel):
    """设备MAC地址注册请求"""
    mac_address: str
    device_type: str = "ESP32"
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None

class DeviceMacRegisterResponse(BaseModel):
    """设备MAC地址注册响应"""
    device_id: str
    device_uuid: str
    device_secret: str
    mac_address: str
    message: str
    registered_at: datetime

class DeviceRegister(BaseModel):
    """设备注册时的配置数据"""
    device_id: str
    device_secret: str
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_sensor_config: Optional[Dict[str, Any]] = None
    device_control_config: Optional[Dict[str, Any]] = None
    device_capabilities: Optional[Dict[str, Any]] = None
    # 动态产品绑定相关字段
    product_code: Optional[str] = None
    product_version: Optional[str] = None

class DeviceResponse(DeviceBase):
    """设备响应模式"""
    id: int
    uuid: str
    device_id: str
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None
    production_date: Optional[datetime] = None
    quality_grade: Optional[str] = None
    is_online: Optional[bool] = None
    is_active: Optional[bool] = None
    last_seen: Optional[datetime] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    group_name: Optional[str] = None
    room: Optional[str] = None
    floor: Optional[str] = None
    device_sensor_config: Optional[dict] = None
    device_control_config: Optional[dict] = None
    device_settings: Optional[dict] = None
    last_heartbeat: Optional[datetime] = None
    error_count: Optional[int] = None
    # last_error: Optional[str] = None  # 已删除，未使用
    last_report_data: Optional[dict] = None
    uptime: Optional[int] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v and not v.isoformat().endswith('Z') and '+' not in v.isoformat() else (v.isoformat() if v else None)
        }


class DeviceWithProductInfo(DeviceResponse):
    """包含产品信息和所有者信息的设备响应模式"""
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    # 设备所有者信息
    owner_username: Optional[str] = None
    owner_email: Optional[str] = None
    owner_name: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v and not v.isoformat().endswith('Z') and '+' not in v.isoformat() else (v.isoformat() if v else None)
        }


class DeviceList(BaseModel):
    """设备列表显示模式"""
    id: int
    name: str
    uuid: str
    product_id: Optional[int] = None  # 动态绑定，可为空
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    mac_address: Optional[str] = None  # MAC地址
    device_mac: Optional[str] = None   # 设备MAC（用于显示）
    ip_address: Optional[str] = None   # IP地址
    device_status: Optional[DeviceStatus] = None
    is_online: Optional[bool] = None
    is_active: Optional[bool] = None
    last_seen: Optional[datetime] = None
    location: Optional[str] = None
    group_name: Optional[str] = None
    error_count: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SensorData(BaseModel):
    """传感器数据"""
    sensor_name: str
    value: float
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None

class DeviceDataUpload(BaseModel):
    """设备数据上传"""
    device_id: str
    device_secret: str
    timestamp: Optional[datetime] = None
    sensors: Optional[List[SensorData]] = None
    status: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, float]] = None  # {"latitude": 0.0, "longitude": 0.0}

class DeviceStatusUpdate(BaseModel):
    """设备状态更新"""
    device_id: str
    device_secret: str
    status: str  # online, offline, error
    ip_address: Optional[str] = None
    rssi: Optional[int] = None
    battery_level: Optional[float] = None
    firmware_version: Optional[str] = None
    timestamp: Optional[datetime] = None

class DeviceProductReport(BaseModel):
    """设备产品信息上报模式"""
    device_id: str
    device_secret: str
    product_code: str
    product_version: str
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class DeviceProductSwitch(BaseModel):
    """设备产品切换模式"""
    device_id: str
    device_secret: str
    new_product_code: str
    new_product_version: str
    reason: Optional[str] = "unknown"
    timestamp: Optional[datetime] = None

class DeviceResponseWithStatus(DeviceResponse):
    """包含设备状态的响应模式"""
    device_status: DeviceStatus
    product_code: Optional[str] = None
    product_version: Optional[str] = None
    last_product_report: Optional[datetime] = None
    product_switch_count: Optional[int] = None
    auto_created_product: Optional[bool] = None

    class Config:
        from_attributes = True
