"""
系统配置 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SystemConfigBase(BaseModel):
    """系统配置基础Schema"""
    config_key: str = Field(..., description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field(default="string", description="配置类型: string, boolean, integer, json")
    description: Optional[str] = Field(None, description="配置描述")
    category: str = Field(default="system", description="配置分类")
    is_public: bool = Field(default=False, description="是否公开（前端可见）")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置Schema"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置Schema"""
    config_value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class SystemConfigInDB(SystemConfigBase):
    """数据库中的系统配置Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SystemConfigPublic(BaseModel):
    """公开的系统配置Schema（用于前端）"""
    config_key: str
    config_value: Optional[str]
    config_type: str
    
    class Config:
        from_attributes = True


class ModuleConfigResponse(BaseModel):
    """模块配置响应Schema"""
    enable_user_registration: bool = Field(..., description="是否开启用户注册")
    enable_device_module: bool = Field(..., description="是否开启设备管理模块")
    enable_ai_module: bool = Field(..., description="是否开启AI模块")
    enable_pbl_module: bool = Field(..., description="是否开启PBL模块")


class ModuleConfigUpdate(BaseModel):
    """模块配置更新Schema"""
    enable_user_registration: Optional[bool] = Field(None, description="是否开启用户注册")
    enable_device_module: Optional[bool] = Field(None, description="是否开启设备管理模块")
    enable_ai_module: Optional[bool] = Field(None, description="是否开启AI模块")
    enable_pbl_module: Optional[bool] = Field(None, description="是否开启PBL模块")


class PlatformConfigResponse(BaseModel):
    """平台配置响应Schema"""
    platform_name: str = Field(..., description="平台名称")
    platform_description: str = Field(..., description="平台描述")
    enable_user_registration: bool = Field(..., description="是否开启用户注册")
    user_agreement: Optional[str] = Field(None, description="用户协议内容（仅在include_policies=true时返回）")
    privacy_policy: Optional[str] = Field(None, description="隐私政策内容（仅在include_policies=true时返回）")


class PlatformConfigUpdate(BaseModel):
    """平台配置更新Schema"""
    platform_name: Optional[str] = Field(None, min_length=2, max_length=50, description="平台名称")
    platform_description: Optional[str] = Field(None, max_length=200, description="平台描述")
    enable_user_registration: Optional[bool] = Field(None, description="是否开启用户注册")


class PoliciesConfigResponse(BaseModel):
    """协议配置响应Schema"""
    user_agreement: str = Field(default="", description="用户协议内容")
    privacy_policy: str = Field(default="", description="隐私政策内容")


class PoliciesConfigUpdate(BaseModel):
    """协议配置更新Schema"""
    user_agreement: Optional[str] = Field(None, description="用户协议内容")
    privacy_policy: Optional[str] = Field(None, description="隐私政策内容")


class DeviceMqttConfigResponse(BaseModel):
    """设备MQTT配置响应Schema"""
    device_mqtt_broker: str = Field(..., description="MQTT Broker地址（设备连接用）")
    device_mqtt_port: int = Field(..., description="MQTT Broker端口")
    device_mqtt_use_ssl: bool = Field(..., description="是否启用SSL/TLS")
    device_config_server_url: str = Field(..., description="设备配置服务器地址（设备配网时填写）")


class DeviceMqttConfigUpdate(BaseModel):
    """设备MQTT配置更新Schema"""
    device_mqtt_broker: Optional[str] = Field(None, min_length=3, max_length=255, description="MQTT Broker地址")
    device_mqtt_port: Optional[int] = Field(None, ge=1, le=65535, description="MQTT Broker端口")
    device_mqtt_use_ssl: Optional[bool] = Field(None, description="是否启用SSL/TLS")
    device_config_server_url: Optional[str] = Field(None, min_length=3, max_length=255, description="设备配置服务器地址")

