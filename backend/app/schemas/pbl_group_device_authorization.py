"""
PBL小组设备授权Schema定义
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# ============================================================================
# PBL小组设备授权 Schemas
# ============================================================================

class PBLGroupDeviceAuthorizationCreate(BaseModel):
    """创建PBL小组设备授权Schema"""
    group_ids: List[int] = Field(..., min_items=1, description="小组ID列表（支持批量授权）")
    expires_at: Optional[datetime] = Field(None, description="过期时间（可选，NULL表示永久有效）")
    notes: Optional[str] = Field(None, description="备注")


class PBLGroupDeviceAuthorizationUpdate(BaseModel):
    """更新PBL小组设备授权Schema"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注")


class PBLGroupDeviceAuthorizationResponse(BaseModel):
    """PBL小组设备授权响应Schema"""
    id: int
    uuid: str
    group_id: int
    group_name: Optional[str] = None
    device_id: int
    device_name: Optional[str] = None
    device_uuid: Optional[str] = None
    authorized_by: int
    authorized_by_name: Optional[str] = None
    authorized_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    notes: Optional[str] = None
    is_expired: bool = False  # 计算字段：是否已过期
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PBLGroupDeviceAuthorizationListResponse(BaseModel):
    """PBL小组设备授权列表响应Schema"""
    total: int
    page: int = 1
    page_size: int = 20
    authorizations: List[PBLGroupDeviceAuthorizationResponse]


class PBLGroupDeviceAuthorizationBatchResponse(BaseModel):
    """批量授权响应Schema"""
    total: int
    success: int
    failed: int
    authorizations: List[PBLGroupDeviceAuthorizationResponse]


class PBLAuthorizableGroupResponse(BaseModel):
    """可授权的小组响应Schema（用于前端选择）"""
    group_id: int
    group_name: str
    course_id: int
    course_name: str
    class_id: int
    class_name: str
    member_count: int = 0


class PBLAuthorizableGroupsResponse(BaseModel):
    """可授权的小组列表响应Schema"""
    classes: List[dict]  # 嵌套结构：班级 -> 课程 -> 小组


class PBLGroupDeviceAuthorizationRevokeRequest(BaseModel):
    """撤销授权请求Schema"""
    group_ids: Optional[List[int]] = Field(None, description="要撤销的小组ID列表（可选，不提供则撤销所有）")
