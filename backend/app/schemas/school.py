from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date

class SchoolCreate(BaseModel):
    """创建学校Schema"""
    school_code: str = Field(..., min_length=2, max_length=50, description="学校代码（如 BJ-YCZX）")
    school_name: str = Field(..., min_length=2, max_length=200, description="学校名称")
    province: Optional[str] = Field(None, max_length=50, description="省份")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    district: Optional[str] = Field(None, max_length=50, description="区/县")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=255, description="联系邮箱")
    license_expire_at: date = Field(..., description="授权到期时间（必填）")
    max_teachers: int = Field(..., ge=1, le=10000, description="最大教师数（必填）")
    max_students: int = Field(..., ge=1, le=100000, description="最大学生数（必填）")
    max_devices: int = Field(..., ge=1, le=50000, description="最大设备数（必填）")
    
    @validator('school_code')
    def validate_school_code(cls, v):
        """验证学校代码格式"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('学校代码只能包含字母、数字、连字符和下划线')
        return v.upper()  # 统一转为大写

class SchoolUpdate(BaseModel):
    """更新学校Schema"""
    school_name: Optional[str] = Field(None, min_length=2, max_length=200)
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    license_expire_at: Optional[date] = None
    max_teachers: Optional[int] = Field(None, ge=1, le=10000)
    max_students: Optional[int] = Field(None, ge=1, le=100000)
    max_devices: Optional[int] = Field(None, ge=1, le=50000)

class SchoolResponse(BaseModel):
    """学校响应Schema"""
    id: int
    uuid: str
    school_code: str
    school_name: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    license_expire_at: Optional[date] = None
    max_teachers: Optional[int] = 100
    max_students: Optional[int] = 1000
    max_devices: Optional[int] = 500
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('max_teachers', pre=True)
    def validate_max_teachers(cls, v):
        """处理 max_teachers NULL 值"""
        return v if v is not None else 100
    
    @validator('max_students', pre=True)
    def validate_max_students(cls, v):
        """处理 max_students NULL 值"""
        return v if v is not None else 1000
    
    @validator('max_devices', pre=True)
    def validate_max_devices(cls, v):
        """处理 max_devices NULL 值"""
        return v if v is not None else 500
    
    @validator('created_at', 'updated_at', pre=True)
    def validate_datetime(cls, v):
        """处理无效的日期时间值"""
        if v is None:
            return datetime.now()
        if isinstance(v, str):
            # 处理 MySQL 的零值日期
            if v.startswith('0000-00-00'):
                return datetime.now()
        return v
    
    class Config:
        from_attributes = True

class SchoolListResponse(BaseModel):
    """学校列表响应Schema"""
    id: int
    uuid: str
    school_code: str
    school_name: str
    province: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    teacher_count: Optional[int] = 0
    student_count: Optional[int] = 0
    device_count: Optional[int] = 0
    max_teachers: Optional[int] = 100
    max_students: Optional[int] = 1000
    max_devices: Optional[int] = 500
    created_at: Optional[datetime] = None
    
    @validator('created_at', pre=True)
    def validate_created_at(cls, v):
        """处理无效的日期时间值"""
        if v is None:
            return datetime.now()
        if isinstance(v, str):
            # 处理 MySQL 的零值日期
            if v.startswith('0000-00-00'):
                return datetime.now()
        return v
    
    @validator('max_teachers', pre=True)
    def validate_max_teachers(cls, v):
        """处理 max_teachers NULL 值"""
        return v if v is not None else 100
    
    @validator('max_students', pre=True)
    def validate_max_students(cls, v):
        """处理 max_students NULL 值"""
        return v if v is not None else 1000
    
    @validator('max_devices', pre=True)
    def validate_max_devices(cls, v):
        """处理 max_devices NULL 值"""
        return v if v is not None else 500
    
    class Config:
        from_attributes = True

class SchoolStatistics(BaseModel):
    """学校统计信息Schema"""
    school_id: int
    school_name: str
    total_teachers: int = 0
    total_students: int = 0
    total_devices: int = 0
    total_agents: int = 0
    active_users: int = 0
    max_teachers: int
    max_students: int
    max_devices: int
    usage_rate: dict = {}  # 使用率统计

