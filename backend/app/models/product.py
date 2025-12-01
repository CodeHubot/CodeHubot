from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive

class Product(Base):
    """
    产品模型 - 定义设备的传感器类型和被控端口类型
    简化的两层架构：产品直接关联设备UUID
    """
    __tablename__ = "aiot_core_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(64), unique=True, index=True, nullable=False, comment="产品编码/产品标识符（如：ESP32-S3-Dev-01，与固件product_id一致）")
    name = Column(String(100), nullable=False, comment="产品名称")
    description = Column(Text, comment="产品描述")
    category = Column(String(50), nullable=True, comment="产品类别（已废弃，保留用于兼容性）")
    
    # 产品规格定义 - 传感器配置
    sensor_types = Column(JSON, nullable=False, comment="传感器类型配置")
    # 示例: {
    #   "DHT11_temperature": {
    #     "type": "DHT11", "pin": 4, "unit": "°C", "name": "温度传感器",
    #     "range": {"min": -40, "max": 80}, "accuracy": 2.0, "enabled": true
    #   },
    #   "DHT11_humidity": {
    #     "type": "DHT11", "pin": 4, "unit": "%", "name": "湿度传感器", 
    #     "range": {"min": 0, "max": 100}, "accuracy": 5.0, "enabled": true
    #   },
    #   "DS18B20_temperature": {
    #     "type": "DS18B20", "pin": 5, "unit": "°C", "name": "防水温度传感器",
    #     "range": {"min": -55, "max": 125}, "accuracy": 0.5, "enabled": true
    #   }
    # }
    
    # 产品规格定义 - 控制端口配置
    control_ports = Column(JSON, nullable=False, comment="被控端口类型配置")
    # 示例: {
    #   "led": {
    #     "type": "LED", "pin": 2, "voltage": "3.3V", "name": "状态指示灯",
    #     "pwm_capable": true, "max_current": "20mA", "enabled": true
    #   },
    #   "relay": {
    #     "type": "RELAY", "pin": 3, "voltage": "5V", "name": "继电器控制",
    #     "max_current": "10A", "switching_voltage": "250V", "enabled": true
    #   }
    # }
    
    # 设备能力配置
    device_capabilities = Column(JSON, comment="设备能力配置")
    # 示例: {
    #   "sensors": ["temperature", "humidity"],
    #   "actuators": ["led", "relay"],
    #   "communication": ["wifi", "mqtt", "http"],
    #   "ota_support": true,
    #   "deep_sleep": true,
    #   "watchdog": true
    # }
    
    # 默认设备配置模板
    default_device_config = Column(JSON, comment="默认设备配置模板")
    # 示例: {
    #   "device_sensor_config": {
    #     "dht11": {"pin": 4, "enabled": true},
    #     "ds18b20": {"pin": 5, "enabled": true}
    #   },
    #   "device_control_config": {
    #     "led": {"pin": 2, "enabled": true},
    #     "relay": {"pin": 3, "enabled": true}
    #   },
    #   "sampling_interval": 10,
    #   "heartbeat_interval": 30,
    #   "data_retention_days": 30
    # }
    
    communication_protocols = Column(JSON, comment="支持的通信协议")
    # 示例: ["WiFi", "Bluetooth", "MQTT", "HTTP"]
    
    power_requirements = Column(JSON, comment="电源要求")
    # 示例: {"voltage": "5V", "current": "500mA", "power": "2.5W"}
    
    # 产品版本和固件信息
    firmware_version = Column(String(50), comment="默认固件版本")
    hardware_version = Column(String(50), comment="硬件版本")
    
    # 产品状态
    is_active = Column(Boolean, default=True, comment="产品是否激活")
    version = Column(String(20), default="1.0", comment="产品版本")
    
    # 制造商信息
    manufacturer = Column(String(100), comment="制造商")
    manufacturer_code = Column(String(50), comment="制造商代码")
    
    # 统计信息
    total_devices = Column(Integer, default=0, comment="该产品的设备总数")
    
    # 产品权限控制
    is_system = Column(Boolean, default=False, comment="是否为系统内置产品")
    creator_id = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=True, comment="创建者ID（用户创建的产品）")
    is_shared = Column(Boolean, default=False, comment="是否共享给其他用户（用户创建的产品可选择共享）")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    # 关系 - 直接关联设备
    devices = relationship("Device", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(product_code='{self.product_code}', name='{self.name}')>"