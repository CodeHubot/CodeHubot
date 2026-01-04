from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.api.auth import get_current_user
from app.core.security import verify_password, get_password_hash
from app.core.constants import ErrorMessages, SuccessMessages
from app.core.response import success_response
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员"""
    return user.email == "admin@aiot.com" or user.username == "admin" or user.role == "admin"

class ProfileUpdate(BaseModel):
    username: str = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户个人信息"""
    return current_user

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户个人信息"""
    if profile_data.username and profile_data.username != current_user.username:
        # 检查新用户名是否已被使用
        existing_user = db.query(User).filter(User.username == profile_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用"
            )
        current_user.username = profile_data.username
    
    db.commit()
    db.refresh(current_user)
    
    return success_response(data=current_user, message="个人信息更新成功")

@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return success_response(data={"success": True}, message="密码修改成功")

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    # 获取设备统计
    total_devices = db.query(Device).filter(Device.user_id == current_user.id).count()
    online_devices = db.query(Device).filter(
        Device.user_id == current_user.id,
        Device.is_online == True
    ).count()
    
    # 计算登录天数（简化计算，基于注册时间）
    if current_user.created_at:
        days_since_registration = (datetime.utcnow() - current_user.created_at).days
        login_days = min(days_since_registration + 1, 100)  # 假设最多100天
    else:
        login_days = 1
    
    return success_response(data={
        "device_count": total_devices,
        "online_count": online_devices,
        "login_days": login_days
    })

# ==================== 用户管理接口（仅管理员） ====================

@router.get("/list")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    username: Optional[str] = Query(None, description="用户名筛选"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表 - 仅管理员可访问"""
    # 权限检查：只有管理员可以访问
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问用户列表"
        )
    
    query = db.query(User)
    
    # 应用筛选条件
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern)
            )
        )
    
    # 先获取总数
    total = query.count()
    
    # 分页查询
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # 转换为UserResponse格式，去除password_hash
    user_responses = [UserResponse.model_validate(user) for user in users]
    
    return success_response(data={
        "items": user_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    })

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户 - 仅管理员可访问"""
    # 权限检查：只有管理员可以创建用户
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权创建用户"
        )
    
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.EMAIL_EXISTS
        )
    
    # 检查用户名是否已存在
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.USERNAME_EXISTS
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email or None,  # 空字符串转为 None
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role if user_data.role else 'user'
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"✅ 管理员 {current_user.username} 创建用户: {user_data.email} (ID: {db_user.id})")
    
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息 - 仅管理员可访问"""
    # 权限检查：只有管理员可以更新用户
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新用户"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.USER_NOT_FOUND
        )
    
    # 不能修改自己的状态
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的账户状态"
        )
    
    # 更新字段
    if user_update.username is not None:
        # 检查新用户名是否已被使用
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.USERNAME_EXISTS
            )
        user.username = user_update.username
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ 管理员 {current_user.username} 更新用户: {user.email} (ID: {user_id})")
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户 - 仅管理员可访问"""
    # 权限检查：只有管理员可以删除用户
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除用户"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.USER_NOT_FOUND
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    # 不能删除管理员账户（可选，根据需求决定）
    if is_admin_user(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除管理员账户"
        )
    
    # 检查用户是否有设备
    device_count = db.query(Device).filter(Device.user_id == user_id).count()
    if device_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该用户还有 {device_count} 个设备，请先解绑或删除设备后再删除用户"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"✅ 管理员 {current_user.username} 删除用户: {user.email} (ID: {user_id})")
    
    return success_response(message=SuccessMessages.DELETE_SUCCESS)

@router.put("/{user_id}/toggle-status", response_model=UserResponse)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换用户启用/禁用状态 - 仅管理员可访问"""
    # 权限检查：只有管理员可以切换用户状态
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改用户状态"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.USER_NOT_FOUND
        )
    
    # 不能修改自己的状态
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的账户状态"
        )
    
    # 切换状态
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ 管理员 {current_user.username} {'启用' if user.is_active else '禁用'}用户: {user.email} (ID: {user_id})")
    
    return user

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., description="新密码"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置用户密码 - 仅管理员可访问"""
    # 权限检查：只有管理员可以重置密码
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权重置用户密码"
        )
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.USER_NOT_FOUND
        )
    
    # 验证密码强度（使用UserCreate的验证逻辑）
    from app.schemas.user import UserCreate
    try:
        # 临时创建UserCreate对象来验证密码
        temp_user = UserCreate(email=user.email, username=user.username, password=new_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码不符合要求: {str(e)}"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    logger.info(f"✅ 管理员 {current_user.username} 重置用户密码: {user.email} (ID: {user_id})")
    
    return success_response(message="密码重置成功")
