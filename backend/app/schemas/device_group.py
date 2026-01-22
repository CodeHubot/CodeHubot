"""
设备分组和授权Schema定义
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# ============================================================================
# 设备分组 Schemas
# ============================================================================

class DeviceGroupCreate(BaseModel):
    """创建设备组Schema"""
    group_name: str = Field(..., min_length=1, max_length=100, description="设备组名称")
    group_code: Optional[str] = Field(None, max_length=50, description="设备组编号")
    description: Optional[str] = Field(None, description="描述")


class DeviceGroupUpdate(BaseModel):
    """更新设备组Schema"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=100, description="设备组名称")
    group_code: Optional[str] = Field(None, max_length=50, description="设备组编号")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class DeviceGroupResponse(BaseModel):
    """设备组响应Schema"""
    id: int
    uuid: str
    team_id: int
    group_name: str
    group_code: Optional[str] = None
    description: Optional[str] = None
    device_count: int = 0
    is_active: bool = True
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceGroupListResponse(BaseModel):
    """设备组列表响应Schema"""
    id: int
    uuid: str
    team_id: int
    group_name: str
    group_code: Optional[str] = None
    device_count: int = 0
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 设备分组成员 Schemas
# ============================================================================

class DeviceGroupMemberAdd(BaseModel):
    """添加设备到组Schema"""
    device_id: int = Field(..., description="设备ID")


class DeviceGroupMemberBatchAdd(BaseModel):
    """批量添加设备到组Schema"""
    device_ids: List[int] = Field(..., description="设备ID列表")


class DeviceGroupMemberResponse(BaseModel):
    """设备组成员响应Schema"""
    id: int
    group_id: int
    device_id: int
    device_name: Optional[str] = None
    device_mac: Optional[str] = None
    joined_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 课程设备授权 Schemas
# ============================================================================

class CourseDeviceAuthorizationCreate(BaseModel):
    """创建课程设备授权Schema"""
    device_group_id: int = Field(..., description="设备组ID")
    expires_at: datetime = Field(..., description="过期时间")
    notes: Optional[str] = Field(None, description="备注")
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v <= datetime.now():
            raise ValueError('过期时间必须大于当前时间')
        return v


class CourseDeviceAuthorizationUpdate(BaseModel):
    """更新课程设备授权Schema"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注")
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v and v <= datetime.now():
            raise ValueError('过期时间必须大于当前时间')
        return v


class CourseDeviceAuthorizationResponse(BaseModel):
    """课程设备授权响应Schema"""
    id: int
    uuid: str
    course_id: int
    course_name: Optional[str] = None
    device_group_id: int
    device_group_name: Optional[str] = None
    device_count: Optional[int] = 0
    authorized_by: int
    authorized_by_name: Optional[str] = None
    authorized_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseDeviceAuthorizationListResponse(BaseModel):
    """课程设备授权列表响应Schema"""
    id: int
    uuid: str
    device_group_id: int
    device_group_name: Optional[str] = None
    device_count: Optional[int] = 0
    authorized_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    is_expired: bool = False
    
    class Config:
        from_attributes = True


# ============================================================================
# 已授权设备 Schema
# ============================================================================

class AuthorizedDeviceResponse(BaseModel):
    """已授权设备响应Schema"""
    device_id: int
    device_name: str
    device_mac: Optional[str] = None
    device_status: Optional[str] = None
    group_name: str
    authorization_expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

