"""
学校用户管理 API
用于学校管理员管理本校的教师和学生
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
import uuid as uuid_lib

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...core.security import get_password_hash
from ...models.admin import Admin, User
from ...models.school import School
from ...models.pbl import PBLClass
from ...core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class UserCreate(BaseModel):
    """创建用户请求模型"""
    role: str = Field(..., description="角色: teacher/student")
    name: str = Field(..., min_length=2, max_length=50, description="姓名")
    password: str = Field(..., min_length=6, description="密码")
    gender: Optional[str] = Field(None, description="性别: male/female")
    teacher_number: Optional[str] = Field(None, description="教师工号")
    student_number: Optional[str] = Field(None, description="学生学号")
    class_id: Optional[int] = Field(None, description="班级ID（学生必填）")
    subject: Optional[str] = Field(None, description="学科（教师）")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[str] = Field(None, description="邮箱")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    role: Optional[str] = Field(None, description="角色: teacher/student")
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="姓名")
    gender: Optional[str] = Field(None, description="性别: male/female")
    teacher_number: Optional[str] = Field(None, description="教师工号")
    student_number: Optional[str] = Field(None, description="学生学号")
    class_id: Optional[int] = Field(None, description="班级ID")
    subject: Optional[str] = Field(None, description="学科（教师）")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[str] = Field(None, description="邮箱")
    is_active: Optional[bool] = Field(None, description="是否启用")


@router.post("")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    创建用户（教师或学生）
    权限：学校管理员只能为自己的学校创建用户
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    # 获取学校信息
    school = db.query(School).filter(School.id == current_admin.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="您关联的学校不存在"
        )
    
    # 验证角色
    if user_data.role not in ['teacher', 'student']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 teacher 或 student"
        )
    
    # 生成用户名
    if user_data.role == 'teacher':
        if not user_data.teacher_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="教师工号不能为空"
            )
        username = f"{school.school_code}_T_{user_data.teacher_number}"
        
        # 检查教师工号是否重复
        existing = db.query(User).filter(
            User.school_id == school.id,
            User.teacher_number == user_data.teacher_number,
            User.deleted_at == None
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该教师工号已存在"
            )
    else:  # student
        if not user_data.student_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生学号不能为空"
            )
        if not user_data.class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生必须指定班级"
            )
        
        # 验证班级是否属于该学校
        class_obj = db.query(PBLClass).filter(
            PBLClass.id == user_data.class_id,
            PBLClass.school_id == school.id
        ).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="班级不存在或不属于该学校"
            )
        
        username = f"{school.school_code}_S_{user_data.student_number}"
        
        # 检查学号是否重复
        existing = db.query(User).filter(
            User.school_id == school.id,
            User.student_number == user_data.student_number,
            User.deleted_at == None
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该学生学号已存在"
            )
    
    # 检查用户名是否重复
    existing_username = db.query(User).filter(
        User.username == username,
        User.deleted_at == None
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    new_user = User(
        uuid=str(uuid_lib.uuid4()),
        username=username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        name=user_data.name,
        real_name=user_data.name,
        gender=user_data.gender,
        school_id=school.id,
        is_active=True
    )
    
    # 设置角色特定字段
    if user_data.role == 'teacher':
        new_user.teacher_number = user_data.teacher_number
        new_user.subject = user_data.subject
    else:
        new_user.student_number = user_data.student_number
        new_user.class_id = user_data.class_id
    
    # 设置可选字段
    if user_data.phone:
        new_user.phone = user_data.phone
    if user_data.email:
        new_user.email = user_data.email
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(
            f"创建用户成功 - 角色: {user_data.role}, 姓名: {user_data.name}, "
            f"用户名: {username}, 学校: {school.school_name}, "
            f"操作者: {current_admin.username}"
        )
        
        return success_response(
            message="创建成功",
            data={
                'id': new_user.id,
                'uuid': new_user.uuid,
                'username': username,
                'name': new_user.name,
                'role': new_user.role
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )


@router.put("/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    更新用户信息
    权限：学校管理员只能更新自己学校的用户
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    # 查找用户
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只能更新自己学校的用户
    if user.school_id != current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新该用户"
        )
    
    # 更新字段
    if user_data.name is not None:
        user.name = user_data.name
        user.real_name = user_data.name
    
    if user_data.gender is not None:
        user.gender = user_data.gender
    
    if user_data.phone is not None:
        user.phone = user_data.phone
    
    if user_data.email is not None:
        user.email = user_data.email
    
    if user_data.is_active is not None:
        # 防止管理员禁用自己
        if user.id == current_admin.id and not user_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用自己的账号"
            )
        user.is_active = user_data.is_active
    
    # 角色特定字段更新
    if user.role == 'teacher':
        if user_data.teacher_number is not None:
            # 检查工号是否重复
            existing = db.query(User).filter(
                User.id != user_id,
                User.school_id == user.school_id,
                User.teacher_number == user_data.teacher_number,
                User.deleted_at == None
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该教师工号已存在"
                )
            user.teacher_number = user_data.teacher_number
        
        if user_data.subject is not None:
            user.subject = user_data.subject
    
    elif user.role == 'student':
        if user_data.student_number is not None:
            # 检查学号是否重复
            existing = db.query(User).filter(
                User.id != user_id,
                User.school_id == user.school_id,
                User.student_number == user_data.student_number,
                User.deleted_at == None
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该学生学号已存在"
                )
            user.student_number = user_data.student_number
        
        if user_data.class_id is not None:
            # 验证班级
            class_obj = db.query(PBLClass).filter(
                PBLClass.id == user_data.class_id,
                PBLClass.school_id == user.school_id
            ).first()
            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="班级不存在或不属于该学校"
                )
            user.class_id = user_data.class_id
    
    try:
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"更新用户成功 - 用户ID: {user_id}, 姓名: {user.name}, "
            f"操作者: {current_admin.username}"
        )
        
        return success_response(message="更新成功")
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    删除用户（软删除）
    权限：学校管理员只能删除自己学校的用户
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    # 查找用户
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查
    if user.school_id != current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该用户"
        )
    
    # 防止删除自己
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )
    
    try:
        from datetime import datetime
        user.deleted_at = datetime.now()
        db.commit()
        
        logger.info(
            f"删除用户成功 - 用户ID: {user_id}, 姓名: {user.name}, "
            f"操作者: {current_admin.username}"
        )
        
        return success_response(message="删除成功")
    except Exception as e:
        db.rollback()
        logger.error(f"删除用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

