"""
数据库模型（简化版，只包含MQTT服务需要的模型）
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Device(Base):
    """设备模型"""
    __tablename__ = "device_main"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    device_status = Column(String(20), default="pending")
    is_online = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    last_report_data = Column(JSON, nullable=True, comment="最后上报数据")
    product_id = Column(Integer, ForeignKey("device_products.id"), nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    product = relationship("Product", back_populates="devices")


class Product(Base):
    """产品模型"""
    __tablename__ = "device_products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    sensor_types = Column(JSON, nullable=True)
    control_types = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    devices = relationship("Device", back_populates="product")

