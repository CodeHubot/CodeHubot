from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive

class DeviceBindingHistory(Base):
    """
    设备绑定历史记录模型
    记录每个MAC地址设备被哪些用户绑定过的历史
    """
    __tablename__ = "aiot_device_binding_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # MAC地址（核心字段，用于追踪设备）
    mac_address = Column(String(17), nullable=False, index=True, comment="设备MAC地址")
    
    # 设备信息（记录绑定时的设备信息）
    device_uuid = Column(String(36), nullable=True, index=True, comment="设备UUID（解绑后可能为空）")
    device_id = Column(String(100), nullable=True, comment="设备ID")
    device_name = Column(String(100), nullable=True, comment="设备名称")
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=False, index=True, comment="绑定用户ID")
    user_email = Column(String(255), nullable=True, comment="用户邮箱（冗余字段，便于查询）")
    user_username = Column(String(50), nullable=True, comment="用户名（冗余字段，便于查询）")
    
    # 产品信息
    product_id = Column(Integer, ForeignKey("aiot_core_products.id"), nullable=True, comment="产品ID")
    product_code = Column(String(100), nullable=True, comment="产品编码")
    product_name = Column(String(200), nullable=True, comment="产品名称（冗余字段，便于查询）")
    
    # 绑定/解绑操作
    action = Column(String(20), nullable=False, comment="操作类型：bind/unbind")
    action_time = Column(DateTime, nullable=False, default=get_beijing_time_naive, index=True, comment="操作时间")
    
    # 备注信息
    notes = Column(Text, nullable=True, comment="备注信息（如解绑原因等）")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="记录创建时间")
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])
    
    # 创建复合索引：MAC地址 + 操作时间，便于按MAC地址查询历史记录
    __table_args__ = (
        Index('idx_mac_action_time', 'mac_address', 'action_time'),
    )
    
    def __repr__(self):
        return f"<DeviceBindingHistory(mac={self.mac_address}, user_id={self.user_id}, action={self.action}, time={self.action_time})>"

