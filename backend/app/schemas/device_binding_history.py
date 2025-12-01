from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DeviceBindingHistoryBase(BaseModel):
    """设备绑定历史基础Schema"""
    mac_address: str = Field(..., description="设备MAC地址")
    device_uuid: Optional[str] = Field(None, description="设备UUID")
    device_id: Optional[str] = Field(None, description="设备ID")
    device_name: Optional[str] = Field(None, description="设备名称")
    user_id: int = Field(..., description="用户ID")
    user_email: Optional[str] = Field(None, description="用户邮箱")
    user_username: Optional[str] = Field(None, description="用户名")
    product_id: Optional[int] = Field(None, description="产品ID")
    product_code: Optional[str] = Field(None, description="产品编码")
    product_name: Optional[str] = Field(None, description="产品名称")
    action: str = Field(..., description="操作类型：bind/unbind")
    action_time: datetime = Field(..., description="操作时间")
    notes: Optional[str] = Field(None, description="备注信息")

class DeviceBindingHistoryResponse(DeviceBindingHistoryBase):
    """设备绑定历史响应Schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeviceBindingHistoryListResponse(BaseModel):
    """设备绑定历史列表响应Schema"""
    mac_address: str
    total_bindings: int = Field(..., description="总绑定次数")
    total_unbindings: int = Field(..., description="总解绑次数")
    first_bind_time: Optional[datetime] = Field(None, description="首次绑定时间")
    last_action_time: Optional[datetime] = Field(None, description="最后操作时间")
    current_user_id: Optional[int] = Field(None, description="当前绑定用户ID（如果已绑定）")
    current_user_email: Optional[str] = Field(None, description="当前绑定用户邮箱")
    history: List[DeviceBindingHistoryResponse] = Field(default_factory=list, description="历史记录列表")
    
    class Config:
        from_attributes = True

