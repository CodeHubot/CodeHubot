from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Plugin(Base):
    """
    插件模型 - 存储 OpenAI 格式的插件定义（OpenAPI 3.0.0）
    """
    __tablename__ = "aiot_plugins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="插件名称")
    description = Column(Text, comment="插件描述")
    
    # OpenAPI 规范（JSON 格式，符合 OpenAI 插件格式）
    openapi_spec = Column(JSON, nullable=False, comment="OpenAPI 3.0.0 规范（JSON）")
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=False, comment="创建用户 ID")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活（1=激活，0=禁用）")
    is_system = Column(Integer, default=0, comment="是否系统内置（1=是，0=否）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Plugin(id={self.id}, name='{self.name}')>"

