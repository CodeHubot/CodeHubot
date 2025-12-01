from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import enum

class DeviceStatus(str, enum.Enum):
    """设备状态枚举"""
    PENDING = "pending"        # 待绑定产品
    BOUND = "bound"           # 已绑定产品
    ACTIVE = "active"         # 激活状态
    OFFLINE = "offline"       # 离线状态
    ERROR = "error"           # 错误状态

class Device(Base):
    """
    设备模型 - 每个具体的设备实例
    简化的两层架构：设备直接关联产品，UUID作为唯一标识符
    """
    __tablename__ = "aiot_core_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False, comment="设备UUID - 唯一标识符")
    device_id = Column(String(100), unique=True, index=True, nullable=False, comment="设备ID - 用于设备注册验证")
    
    # 关联信息
    product_id = Column(Integer, ForeignKey("aiot_core_products.id"), nullable=True, comment="关联产品ID（动态绑定，可为空）")
    user_id = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=False, comment="关联用户ID")
    school_id = Column(Integer, ForeignKey("aiot_schools.id"), nullable=True, index=True, comment="所属学校ID（用于教学场景）")
    
    # 设备基本信息
    name = Column(String(100), nullable=False, comment="设备名称")
    description = Column(Text, comment="设备描述")
    device_secret = Column(String(255), nullable=False, comment="设备密钥")
    
    # 设备版本信息
    firmware_version = Column(String(50), comment="设备固件版本")
    hardware_version = Column(String(50), comment="设备硬件版本")
    
    # 设备状态（使用String而非Enum，避免MySQL ENUM大小写问题）
    device_status = Column(
        String(20),
        default=DeviceStatus.PENDING.value,  # 使用.value获取字符串值
        comment="设备状态: pending/bound/active/offline/error"
    )
    is_online = Column(Boolean, default=False, comment="是否在线")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_seen = Column(DateTime, comment="最后在线时间")
    
    # 动态产品绑定信息
    product_code = Column(String(100), comment="设备上报的产品编码/产品标识符（对应固件端product_id）")
    product_version = Column(String(50), comment="设备上报的产品版本")
    last_product_report = Column(DateTime, comment="最后产品信息上报时间")
    product_switch_count = Column(Integer, default=0, comment="产品切换次数")
    auto_created_product = Column(Boolean, default=False, comment="是否为自动创建的产品")
    
    # 网络信息
    ip_address = Column(String(45), comment="IP地址，支持IPv6")
    mac_address = Column(String(17), comment="MAC地址")
    
    # 位置和分组信息
    location = Column(String(200), comment="设备位置")
    group_name = Column(String(100), comment="设备分组")
    room = Column(String(100), comment="所在房间")
    floor = Column(String(50), comment="所在楼层")
    
    # 设备特定配置（覆盖产品默认配置）
    device_sensor_config = Column(JSON, comment="设备特定传感器配置")
    device_control_config = Column(JSON, comment="设备特定控制配置")
    device_settings = Column(JSON, comment="设备个性化设置")
    
    # 生产和质量信息
    production_date = Column(DateTime, comment="生产日期")
    serial_number = Column(String(100), comment="设备序列号")
    quality_grade = Column(String(10), default="A", comment="质量等级：A/B/C")
    
    # 运行状态信息
    last_heartbeat = Column(DateTime, comment="最后心跳时间")
    error_count = Column(Integer, default=0, comment="错误计数")
    # last_error = Column(Text, comment="最后错误信息")  # 已删除，未使用
    last_report_data = Column(JSON, comment="最后上报数据（JSON格式）")
    uptime = Column(Integer, default=0, comment="运行时间（秒）")
    
    # 维护信息
    installation_date = Column(DateTime, comment="安装日期")
    warranty_expiry = Column(DateTime, comment="保修到期日期")
    last_maintenance = Column(DateTime, comment="最后维护时间")
    next_maintenance = Column(DateTime, comment="下次维护时间")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    # 关系
    product = relationship("Product", back_populates="devices")
    user = relationship("User", back_populates="devices")
    school = relationship("School", foreign_keys=[school_id])
    group_memberships = relationship("DeviceGroupMember", back_populates="device", cascade="all, delete-orphan")
    
    # 数据验证
    @validates('device_status')
    def validate_device_status(self, key, value):
        """验证device_status值，确保只能是有效的状态"""
        if value is None:
            return DeviceStatus.PENDING.value
        
        # 如果是DeviceStatus枚举，获取其值
        if isinstance(value, DeviceStatus):
            return value.value
        
        # 如果是字符串，验证是否有效
        valid_values = [status.value for status in DeviceStatus]
        if value not in valid_values:
            raise ValueError(
                f"Invalid device_status: {value}. "
                f"Must be one of: {', '.join(valid_values)}"
            )
        return value
    
    # 便捷属性
    @property
    def product_name(self):
        return self.product.name if self.product else None

# 添加反向关系
from app.models.user import User
User.devices = relationship("Device", back_populates="user")
