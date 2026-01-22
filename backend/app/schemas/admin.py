from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    full_name: Optional[str] = None
    is_super_admin: bool = False
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """将空字符串转换为 None"""
        if v == '':
            return None
        return v

class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """将空字符串转换为 None"""
        if v == '':
            return None
        return v

class AdminResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    name: Optional[str] = None  # 姓名
    real_name: Optional[str] = None  # 真实姓名
    nickname: Optional[str] = None  # 昵称
    full_name: Optional[str] = None  # 兼容性字段，优先使用 name 或 real_name
    phone: Optional[str] = None  # 手机号
    is_active: bool
    is_super_admin: bool = True  # platform_admin 角色视为超级管理员
    role: str = 'platform_admin'  # 角色
    team_id: Optional[int] = None  # 所属团队ID
    team_uuid: Optional[str] = None  # 所属团队UUID
    team_name: Optional[str] = None  # 团队名称
    last_login: Optional[datetime] = None  # 最后登录时间
    created_at: datetime
    updated_at: datetime
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """将空字符串转换为 None"""
        if v == '':
            return None
        return v
    
    class Config:
        from_attributes = True
        # 允许访问模型属性（如 full_name 和 is_super_admin 属性）
        populate_by_name = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    admin: AdminResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
