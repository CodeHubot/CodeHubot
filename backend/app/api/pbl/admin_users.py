"""
学校用户管理 API
用于学校管理员管理本校的教师和学生
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from pydantic import BaseModel, Field, validator
import re
import csv
import io

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

# 常见弱密码列表
WEAK_PASSWORDS = {
    '12345678', '123456789', '11111111', '00000000',
    'password', 'Password', 'password123', 'Password123',
    'qwerty123', 'abc12345', 'abcd1234', '1qaz2wsx',
    '88888888', '66666666', '11223344', '12341234'
}


def validate_password_strength(password: str, username: str = None) -> Tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 密码
        username: 用户名（可选，用于检查是否与密码相同）
    
    Returns:
        (是否通过, 错误信息)
    """
    # 1. 长度检查：至少8位
    if len(password) < 8:
        return False, "密码长度不能少于8位"
    
    # 2. 不能是常见弱密码
    if password.lower() in WEAK_PASSWORDS:
        return False, "密码过于简单，请使用更复杂的密码"
    
    # 3. 不能与用户名相同
    if username and password.lower() == username.lower():
        return False, "密码不能与用户名相同"
    
    # 4. 复杂度检查：至少包含大小写字母、数字、特殊字符中的2种
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password))
    
    complexity_count = sum([has_lower, has_upper, has_digit, has_special])
    
    if complexity_count < 2:
        return False, "密码必须包含大小写字母、数字、特殊字符中的至少2种"
    
    return True, ""


class UserCreate(BaseModel):
    """创建用户请求模型"""
    role: str = Field(..., description="角色: teacher/student")
    name: str = Field(..., min_length=2, max_length=50, description="姓名")
    password: str = Field(..., min_length=8, description="密码（至少8位，包含大小写字母、数字、特殊字符中至少2种）")
    gender: Optional[str] = Field(None, description="性别: male/female")
    teacher_number: Optional[str] = Field(None, description="教师工号")
    student_number: Optional[str] = Field(None, description="学生学号")
    class_id: Optional[int] = Field(None, description="班级ID（学生必填）")
    subject: Optional[str] = Field(None, description="学科（教师）")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[str] = Field(None, description="邮箱")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


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


@router.get("/list")
def get_user_list(
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取用户列表
    权限：学校管理员只能查看自己学校的用户
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    # 构建查询
    query = db.query(User).filter(
        User.school_id == current_admin.school_id,
        User.deleted_at == None
    )
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    else:
        # 默认只查询教师和学生
        query = query.filter(User.role.in_(['teacher', 'student']))
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.name.like(f'%{keyword}%')) |
            (User.real_name.like(f'%{keyword}%')) |
            (User.username.like(f'%{keyword}%')) |
            (User.teacher_number.like(f'%{keyword}%')) |
            (User.student_number.like(f'%{keyword}%'))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    users = query.order_by(User.id.desc()).offset(skip).limit(limit).all()
    
    # 序列化结果
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'name': user.name or user.real_name,
            'real_name': user.real_name,
            'role': user.role,
            'teacher_number': user.teacher_number,
            'student_number': user.student_number,
            'gender': user.gender,
            'subject': user.subject,
            'phone': user.phone,
            'email': user.email,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    return success_response(data={
        'items': result,
        'total': total,
        'skip': skip,
        'limit': limit
    })


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
    
    # 生成用户名（格式：工号/学号@学校代码）
    if user_data.role == 'teacher':
        if not user_data.teacher_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="教师工号不能为空"
            )
        username = f"{user_data.teacher_number}@{school.school_code}"
        
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
        
        username = f"{user_data.student_number}@{school.school_code}"
        
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
    
    # 再次验证密码强度（包括与用户名的对比）
    is_valid, error_msg = validate_password_strength(user_data.password, username)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 创建用户
    new_user = User(
        username=username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        name=user_data.name,
        real_name=user_data.name,
        gender=user_data.gender,
        school_id=school.id,
        is_active=True,
        need_change_password=True  # 首次登录需要修改密码
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


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    new_password: str = Field(..., min_length=8, description="新密码（至少8位）")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    重置用户密码
    权限：学校管理员只能重置自己学校用户的密码
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
            detail="无权重置该用户密码"
        )
    
    # 再次验证密码强度（包括与用户名的对比）
    is_valid, error_msg = validate_password_strength(reset_data.new_password, user.username)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # 更新密码
        user.password_hash = get_password_hash(reset_data.new_password)
        # 设置首次登录需要修改密码
        user.need_change_password = True
        
        db.commit()
        
        logger.info(
            f"重置用户密码成功 - 用户ID: {user_id}, 用户名: {user.username}, "
            f"操作者: {current_admin.username}"
        )
        
        return success_response(message="密码重置成功，用户下次登录时需要修改密码")
    except Exception as e:
        db.rollback()
        logger.error(f"重置用户密码失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败"
        )


@router.post("/batch-import/students")
async def batch_import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    批量导入学生
    CSV格式：name, student_number, class_name, gender, password
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
    
    # 读取文件内容
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8-sig')  # 处理BOM
        csv_reader = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        logger.error(f"读取CSV文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件格式错误，请使用UTF-8编码的CSV文件"
        )
    
    # 预加载所有班级
    classes = db.query(PBLClass).filter(
        PBLClass.school_id == school.id
    ).all()
    class_dict = {cls.class_name: cls for cls in classes}
    
    success_count = 0
    error_count = 0
    errors = []
    row_num = 1
    
    for row in csv_reader:
        row_num += 1
        try:
            name = row.get('name', '').strip()
            student_number = row.get('student_number', '').strip()
            class_name = row.get('class_name', '').strip()
            gender = row.get('gender', '').strip()
            password = row.get('password', '').strip() or '123456'  # 默认密码
            
            # 必填字段验证
            if not name or not student_number or not class_name or not gender:
                errors.append({
                    'row': row_num,
                    'error': '缺少必填字段（姓名/学号/班级/性别）'
                })
                error_count += 1
                continue
            
            # 性别转换
            gender_map = {'男': 'male', '女': 'female'}
            gender_value = gender_map.get(gender)
            if not gender_value:
                errors.append({
                    'row': row_num,
                    'error': f'性别格式错误：{gender}，应填写"男"或"女"'
                })
                error_count += 1
                continue
            
            # 查找班级
            class_obj = class_dict.get(class_name)
            if not class_obj:
                errors.append({
                    'row': row_num,
                    'error': f'班级不存在：{class_name}'
                })
                error_count += 1
                continue
            
            # 检查学号是否重复
            existing = db.query(User).filter(
                User.school_id == school.id,
                User.student_number == student_number,
                User.deleted_at == None
            ).first()
            if existing:
                errors.append({
                    'row': row_num,
                    'error': f'学号已存在：{student_number}'
                })
                error_count += 1
                continue
            
            # 生成用户名：学号@学校代码
            username = f"{student_number}@{school.school_code}"
            
            # 检查用户名是否重复
            existing_username = db.query(User).filter(
                User.username == username,
                User.deleted_at == None
            ).first()
            if existing_username:
                errors.append({
                    'row': row_num,
                    'error': f'用户名已存在：{username}'
                })
                error_count += 1
                continue
            
            # 验证密码强度
            is_valid, error_msg = validate_password_strength(password, username)
            if not is_valid:
                errors.append({
                    'row': row_num,
                    'error': f'密码不符合要求：{error_msg}'
                })
                error_count += 1
                continue
            
            # 创建用户
            new_user = User(
                username=username,
                password_hash=get_password_hash(password),
                role='student',
                name=name,
                real_name=name,
                gender=gender_value,
                student_number=student_number,
                class_id=class_obj.id,
                school_id=school.id,
                is_active=True,
                need_change_password=True  # 首次登录需要修改密码
            )
            db.add(new_user)
            success_count += 1
            
        except Exception as e:
            logger.error(f"处理第{row_num}行时出错: {str(e)}")
            errors.append({
                'row': row_num,
                'error': str(e)
            })
            error_count += 1
    
    # 提交事务
    try:
        db.commit()
        logger.info(
            f"批量导入学生完成 - 成功: {success_count}, 失败: {error_count}, "
            f"操作者: {current_admin.username}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"批量导入学生失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量导入失败"
        )
    
    return success_response(
        data={
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # 只返回前10条错误
        },
        message=f"导入完成，成功 {success_count} 条，失败 {error_count} 条"
    )


@router.post("/batch-import/teachers")
async def batch_import_teachers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    批量导入教师
    CSV格式：name, teacher_number, subject, gender, password
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
    
    # 读取文件内容
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8-sig')  # 处理BOM
        csv_reader = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        logger.error(f"读取CSV文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件格式错误，请使用UTF-8编码的CSV文件"
        )
    
    success_count = 0
    error_count = 0
    errors = []
    row_num = 1
    
    for row in csv_reader:
        row_num += 1
        try:
            name = row.get('name', '').strip()
            teacher_number = row.get('teacher_number', '').strip()
            subject = row.get('subject', '').strip()
            gender = row.get('gender', '').strip()
            password = row.get('password', '').strip() or '123456'  # 默认密码
            
            # 必填字段验证
            if not name or not teacher_number or not gender:
                errors.append({
                    'row': row_num,
                    'error': '缺少必填字段（姓名/工号/性别）'
                })
                error_count += 1
                continue
            
            # 性别转换
            gender_map = {'男': 'male', '女': 'female'}
            gender_value = gender_map.get(gender)
            if not gender_value:
                errors.append({
                    'row': row_num,
                    'error': f'性别格式错误：{gender}，应填写"男"或"女"'
                })
                error_count += 1
                continue
            
            # 检查工号是否重复
            existing = db.query(User).filter(
                User.school_id == school.id,
                User.teacher_number == teacher_number,
                User.deleted_at == None
            ).first()
            if existing:
                errors.append({
                    'row': row_num,
                    'error': f'工号已存在：{teacher_number}'
                })
                error_count += 1
                continue
            
            # 生成用户名：工号@学校代码
            username = f"{teacher_number}@{school.school_code}"
            
            # 检查用户名是否重复
            existing_username = db.query(User).filter(
                User.username == username,
                User.deleted_at == None
            ).first()
            if existing_username:
                errors.append({
                    'row': row_num,
                    'error': f'用户名已存在：{username}'
                })
                error_count += 1
                continue
            
            # 验证密码强度
            is_valid, error_msg = validate_password_strength(password, username)
            if not is_valid:
                errors.append({
                    'row': row_num,
                    'error': f'密码不符合要求：{error_msg}'
                })
                error_count += 1
                continue
            
            # 创建用户
            new_user = User(
                username=username,
                password_hash=get_password_hash(password),
                role='teacher',
                name=name,
                real_name=name,
                gender=gender_value,
                teacher_number=teacher_number,
                subject=subject or None,
                school_id=school.id,
                is_active=True,
                need_change_password=True  # 首次登录需要修改密码
            )
            db.add(new_user)
            success_count += 1
            
        except Exception as e:
            logger.error(f"处理第{row_num}行时出错: {str(e)}")
            errors.append({
                'row': row_num,
                'error': str(e)
            })
            error_count += 1
    
    # 提交事务
    try:
        db.commit()
        logger.info(
            f"批量导入教师完成 - 成功: {success_count}, 失败: {error_count}, "
            f"操作者: {current_admin.username}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"批量导入教师失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量导入失败"
        )
    
    return success_response(
        data={
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # 只返回前10条错误
        },
        message=f"导入完成，成功 {success_count} 条，失败 {error_count} 条"
    )

