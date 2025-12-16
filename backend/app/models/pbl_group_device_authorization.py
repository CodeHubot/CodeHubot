"""
PBL小组设备授权模型
用于教师将设备授权给班级小组
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib


class PBLGroupDeviceAuthorization(Base):
    """PBL小组设备授权模型"""
    __tablename__ = "pbl_group_device_authorizations"
    
    id = Column(Integer, primary_key=True, index=True, comment="授权ID")
    uuid = Column(String(36), unique=True, nullable=False, index=True, 
                   default=lambda: str(uuid_lib.uuid4()), comment="UUID唯一标识")
    
    # 关联信息
    group_id = Column(Integer, ForeignKey("pbl_groups.id"), nullable=False, index=True, comment="小组ID")
    device_id = Column(Integer, ForeignKey("device_main.id"), nullable=False, index=True, comment="设备ID")
    authorized_by = Column(Integer, ForeignKey("core_users.id"), nullable=False, index=True, comment="授权人ID（教师）")
    
    # 授权信息
    authorized_at = Column(DateTime, default=get_beijing_time_naive, nullable=False, comment="授权时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间（NULL表示永久有效）")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    notes = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系（注意：PBLGroup模型可能不存在，使用字符串表名）
    # group = relationship("PBLGroup", foreign_keys=[group_id])  # 如果PBL模型不存在，注释掉
    device = relationship("Device", foreign_keys=[device_id])
    authorizer = relationship("User", foreign_keys=[authorized_by])
    
    def __repr__(self):
        return f"<PBLGroupDeviceAuthorization(id={self.id}, group_id={self.group_id}, device_id={self.device_id})>"
