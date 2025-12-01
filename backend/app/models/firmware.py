from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.utils.timezone import get_beijing_time_naive

Base = declarative_base()

class Firmware(Base):
    """固件版本模型"""
    __tablename__ = "aiot_core_firmware_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), nullable=False, index=True, comment="产品代号")
    version = Column(String(20), nullable=False, comment="固件版本号")
    firmware_url = Column(String(500), nullable=False, comment="固件下载URL")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_hash = Column(String(64), nullable=True, comment="文件SHA256哈希值")
    description = Column(Text, nullable=True, comment="版本描述")
    release_notes = Column(Text, nullable=True, comment="发布说明")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_latest = Column(Boolean, default=False, comment="是否为最新版本")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    def __repr__(self):
        return f"<Firmware(product_code='{self.product_code}', version='{self.version}')>"