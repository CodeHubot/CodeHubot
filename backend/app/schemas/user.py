from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re
from app.core.constants import (
    MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH,
    USERNAME_REGEX, FORBIDDEN_USERNAMES
)

# 定义角色类型
UserRole = Literal['individual', 'platform_admin', 'school_admin', 'teacher', 'student']

class UserCreate(BaseModel):
    """用户注册Schema - 增强输入验证"""
    email: Optional[EmailStr] = Field(None, description="用户邮箱（可选）")
    username: str = Field(
        ...,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="密码"
    )
    role: Optional[str] = Field(default='user', description="用户角色：admin/user")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        # 检查格式
        if not re.match(USERNAME_REGEX, v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        
        # 检查禁用用户名
        if v.lower() in FORBIDDEN_USERNAMES:
            raise ValueError('该用户名不可用')
        
        # 不能全是数字
        if v.isdigit():
            raise ValueError('用户名不能全是数字')
        
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        errors = []
        
        # 检查长度
        if len(v) < MIN_PASSWORD_LENGTH:
            errors.append(f'密码长度至少{MIN_PASSWORD_LENGTH}个字符')
        
        # 检查是否包含字母
        if not re.search(r'[a-zA-Z]', v):
            errors.append('密码必须包含至少一个字母')
        
        # 检查是否包含数字
        if not re.search(r'[0-9]', v):
            errors.append('密码必须包含至少一个数字')
        
        # 检查是否包含空格
        if ' ' in v:
            errors.append('密码不能包含空格')
        
        # 检查常见弱密码
        weak_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 
            'password123', 'admin123', '123456789', '11111111', 
            '88888888', 'aaaaaaaa', 'abcdefgh'
        ]
        if v.lower() in weak_passwords:
            errors.append('密码过于简单，请使用更强的密码')
        
        if errors:
            raise ValueError('密码强度不足：' + '；'.join(errors))
        
        return v

class UserLogin(BaseModel):
    """用户登录Schema - 支持用户名或邮箱登录"""
    email: str = Field(..., description="用户名或邮箱")  # 改为str类型，支持用户名或邮箱
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)
    captcha_code: Optional[str] = Field(None, description="验证码（登录失败3次后必填）")

class UserResponse(BaseModel):
    """用户响应Schema - 不包含敏感信息"""
    id: int
    uuid: Optional[str] = None
    email: Optional[str] = None
    username: str
    name: Optional[str] = None
    real_name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    role: str = 'individual'
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    teacher_number: Optional[str] = None
    student_number: Optional[str] = None
    subject: Optional[str] = None
    company_name: Optional[str] = None
    is_active: bool
    need_change_password: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """登录响应Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15分钟（秒）
    user: UserResponse  # 使用UserResponse确保不返回password_hash

class PasswordReset(BaseModel):
    """密码重置Schema（已弃用 - 改用token验证）"""
    email: EmailStr
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH
    )

class PasswordResetRequest(BaseModel):
    """请求密码重置Schema"""
    email: EmailStr

# 别名：保持向后兼容性
ResetPasswordRequest = PasswordResetRequest

class PasswordResetConfirm(BaseModel):
    """确认密码重置Schema"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="新密码"
    )
    
    @validator('new_password')
    def validate_password(cls, v):
        """验证密码强度 - 复用UserCreate的验证逻辑"""
        errors = []
        
        if len(v) < MIN_PASSWORD_LENGTH:
            errors.append(f'密码长度至少{MIN_PASSWORD_LENGTH}个字符')
        if not re.search(r'[a-zA-Z]', v):
            errors.append('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            errors.append('密码必须包含至少一个数字')
        if ' ' in v:
            errors.append('密码不能包含空格')
        
        weak_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123', 'admin123', '123456789']
        if v.lower() in weak_passwords:
            errors.append('密码过于简单')
        
        if errors:
            raise ValueError('；'.join(errors))
        
        return v

class UserUpdate(BaseModel):
    """用户更新Schema（管理员用）"""
    username: Optional[str] = Field(
        None,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH
    )
    is_active: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    """修改密码请求Schema"""
    old_password: str = Field(..., description="当前密码")
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="新密码"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """验证新密码"""
        errors = []
        
        # 检查新密码是否与旧密码相同
        if 'old_password' in values and v == values['old_password']:
            raise ValueError('新密码不能与当前密码相同')
        
        # 检查长度
        if len(v) < MIN_PASSWORD_LENGTH:
            errors.append(f'密码长度至少{MIN_PASSWORD_LENGTH}个字符')
        
        # 检查是否包含字母
        if not re.search(r'[a-zA-Z]', v):
            errors.append('密码必须包含至少一个字母')
        
        # 检查是否包含数字
        if not re.search(r'[0-9]', v):
            errors.append('密码必须包含至少一个数字')
        
        # 检查是否包含空格
        if ' ' in v:
            errors.append('密码不能包含空格')
        
        # 检查常见弱密码
        weak_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 
            'password123', 'admin123', '123456789', '11111111'
        ]
        if v.lower() in weak_passwords:
            errors.append('密码过于简单，请使用更强的密码')
        
        if errors:
            raise ValueError('；'.join(errors))
        
        return v

class AdminResetPasswordRequest(BaseModel):
    """管理员重置用户密码请求Schema"""
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="新密码"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        errors = []
        
        # 检查长度
        if len(v) < MIN_PASSWORD_LENGTH:
            errors.append(f'密码长度至少{MIN_PASSWORD_LENGTH}个字符')
        
        # 检查是否包含字母
        if not re.search(r'[a-zA-Z]', v):
            errors.append('密码必须包含至少一个字母')
        
        # 检查是否包含数字
        if not re.search(r'[0-9]', v):
            errors.append('密码必须包含至少一个数字')
        
        # 检查是否包含空格
        if ' ' in v:
            errors.append('密码不能包含空格')
        
        # 检查常见弱密码
        weak_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 
            'password123', 'admin123', '123456789', '11111111'
        ]
        if v.lower() in weak_passwords:
            errors.append('密码过于简单，请使用更强的密码')
        
        if errors:
            raise ValueError('；'.join(errors))
        
        return v

class UpdateProfileRequest(BaseModel):
    """修改个人信息请求Schema"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    username: Optional[str] = Field(
        None,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
        description="用户名"
    )
    nickname: Optional[str] = Field(
        None,
        max_length=50,
        description="用户昵称"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if v is None:
            return v
            
        # 检查格式
        if not re.match(USERNAME_REGEX, v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        
        # 检查禁用用户名
        if v.lower() in FORBIDDEN_USERNAMES:
            raise ValueError('该用户名不可用')
        
        # 不能全是数字
        if v.isdigit():
            raise ValueError('用户名不能全是数字')
        
        return v


class TokenResponse(BaseModel):
    """Token响应Schema（PBL模块使用）"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新Token请求Schema（PBL模块使用）"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新Token响应Schema（PBL模块使用）"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class InstitutionLoginRequest(BaseModel):
    """机构登录请求Schema（PBL模块使用）"""
    school_code: str = Field(..., min_length=2, max_length=50, description="学校代码")
    number: str = Field(..., min_length=1, max_length=50, description="工号或学号")
    password: str = Field(..., min_length=1, description="密码")
