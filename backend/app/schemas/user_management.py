"""
用户管理模块的Schema定义
包含学校管理员、教师、学生的创建和管理相关Schema
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class SchoolAdminCreate(BaseModel):
    """创建学校管理员Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    real_name: str = Field(..., min_length=1, max_length=100, description="真实姓名")
    school_id: int = Field(..., description="所属学校ID")
    teacher_number: str = Field(..., min_length=1, max_length=50, description="工号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class TeacherCreate(BaseModel):
    """创建教师Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    real_name: str = Field(..., min_length=1, max_length=100, description="真实姓名")
    teacher_number: str = Field(..., min_length=1, max_length=50, description="工号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    subject: Optional[str] = Field(None, max_length=50, description="学科")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class StudentCreate(BaseModel):
    """创建学生Schema（简化版：学号、姓名、性别）"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    real_name: str = Field(..., min_length=1, max_length=100, description="真实姓名（必填）")
    gender: str = Field(..., description="性别：male-男, female-女, other-其他")
    student_number: str = Field(..., min_length=1, max_length=50, description="学号（必填）")
    course_ids: Optional[List[int]] = Field(None, description="初始选课列表（可选）")
    
    @validator('gender')
    def validate_gender(cls, v):
        """验证性别"""
        if v not in ['male', 'female', 'other']:
            raise ValueError('性别必须是 male、female 或 other')
        return v

class AssignRoleRequest(BaseModel):
    """分配角色请求Schema（独立用户→教师/学生/学校管理员）"""
    new_role: str = Field(..., description="新角色（teacher/student/school_admin）")
    school_id: Optional[int] = Field(None, description="学校ID（设置学校管理员时必填）")
    teacher_number: Optional[str] = Field(None, max_length=50, description="教师工号")
    student_number: Optional[str] = Field(None, max_length=50, description="学生学号")
    subject: Optional[str] = Field(None, max_length=50, description="教师学科")
    
    @validator('new_role')
    def validate_role(cls, v):
        """验证角色"""
        if v not in ['teacher', 'student', 'school_admin']:
            raise ValueError('new_role必须是teacher、student或school_admin')
        return v
    
    @validator('school_id')
    def validate_school_id(cls, v, values):
        """如果角色是学校管理员，学校ID必填"""
        if values.get('new_role') == 'school_admin' and not v:
            raise ValueError('学校管理员角色必须提供学校ID')
        return v
    
    @validator('teacher_number')
    def validate_teacher_number(cls, v, values):
        """如果角色是教师或学校管理员，工号必填"""
        role = values.get('new_role')
        if role in ['teacher', 'school_admin'] and not v:
            raise ValueError(f'{role}角色必须提供工号')
        return v
    
    @validator('student_number')
    def validate_student_number(cls, v, values):
        """如果角色是学生，学号必填"""
        if values.get('new_role') == 'student' and not v:
            raise ValueError('学生角色必须提供学号')
        return v

class UserSearchQuery(BaseModel):
    """用户搜索查询Schema"""
    keyword: Optional[str] = Field(None, description="搜索关键词（用户名或姓名）")
    role: Optional[str] = Field(None, description="角色筛选")
    school_id: Optional[int] = Field(None, description="学校ID筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

class InstitutionLoginRequest(BaseModel):
    """机构登录请求Schema"""
    school_code: str = Field(..., min_length=2, max_length=50, description="学校代码")
    number: str = Field(..., min_length=1, max_length=50, description="工号或学号")
    password: str = Field(..., min_length=1, description="密码")
    captcha_code: Optional[str] = Field(None, description="验证码（登录失败3次后必填）")

class UserListResponse(BaseModel):
    """用户列表响应Schema"""
    id: int
    username: str
    real_name: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    role: str
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    teacher_number: Optional[str] = None
    student_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    device_count: Optional[int] = 0
    agent_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class AssignRoleResponse(BaseModel):
    """角色分配响应Schema"""
    user_id: int
    username: str
    old_role: str
    new_role: str
    school_id: int
    school_name: Optional[str] = None
    teacher_number: Optional[str] = None
    student_number: Optional[str] = None
    devices_retained: int = 0
    agents_retained: int = 0
    message: str = "角色分配成功"

class BatchImportResult(BaseModel):
    """批量导入结果Schema"""
    total: int = 0
    success: int = 0
    failed: int = 0
    errors: list = []
    
class ImportError(BaseModel):
    """导入错误信息Schema"""
    row: int
    error: str
    data: Optional[dict] = None

