"""
学校管理API
提供学校的CRUD操作，仅限平台管理员使用
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.models.user import User
from app.models.school import School
from app.api.auth import get_current_user
from app.schemas.school import (
    SchoolCreate, SchoolUpdate, SchoolResponse, 
    SchoolListResponse, SchoolStatistics
)

router = APIRouter(prefix="/schools", tags=["schools"])

def check_platform_admin(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为平台管理员"""
    if current_user.role != 'platform_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员才能管理学校"
        )
    return current_user

@router.post("", response_model=dict)
async def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_platform_admin)
):
    """创建学校（仅平台管理员）"""
    
    # 检查学校代码是否已存在
    existing_school = db.query(School).filter(
        School.school_code == school.school_code
    ).first()
    
    if existing_school:
        return error_response(
            message="学校代码已存在",
            code=400
        )
    
    # 创建学校
    db_school = School(
        school_code=school.school_code,
        school_name=school.school_name,
        province=school.province,
        city=school.city,
        district=school.district,
        address=school.address,
        contact_person=school.contact_person,
        contact_phone=school.contact_phone,
        contact_email=school.contact_email,
        license_expire_at=school.license_expire_at,
        max_teachers=school.max_teachers,
        max_students=school.max_students,
        max_devices=school.max_devices,
        is_active=True
    )
    
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    
    return success_response(
        data=SchoolResponse.from_orm(db_school).model_dump(),
        message="学校创建成功"
    )

@router.get("", response_model=dict)
async def list_schools(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    is_active: Optional[bool] = Query(None, description="激活状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_platform_admin)
):
    """获取学校列表（仅平台管理员）"""
    
    # 构建查询
    query = db.query(School)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                School.school_code.like(f"%{keyword}%"),
                School.school_name.like(f"%{keyword}%")
            )
        )
    
    # 筛选条件
    if province:
        query = query.filter(School.province == province)
    if city:
        query = query.filter(School.city == city)
    if is_active is not None:
        query = query.filter(School.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    schools = query.order_by(School.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 获取每个学校的统计信息
    school_list = []
    for school in schools:
        # 统计教师数
        teacher_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role.in_(['teacher', 'school_admin']),
            User.deleted_at.is_(None)
        ).scalar()
        
        # 统计学生数
        student_count = db.query(func.count(User.id)).filter(
            User.school_id == school.id,
            User.role == 'student',
            User.deleted_at.is_(None)
        ).scalar()
        
        school_data = SchoolListResponse.from_orm(school)
        school_data.teacher_count = teacher_count
        school_data.student_count = student_count
        school_data.device_count = 0  # TODO: 实现设备统计
        school_list.append(school_data.model_dump())
    
    return success_response(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "schools": school_list
        }
    )

@router.get("/{school_uuid}", response_model=dict)
async def get_school(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学校详情（通过UUID）"""
    
    # 先通过UUID查找学校
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 平台管理员可以查看所有学校
    # 学校管理员只能查看自己的学校
    if current_user.role == 'platform_admin':
        pass  # 可以查看所有
    elif current_user.role == 'school_admin':
        if current_user.school_id != school.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能查看本校信息"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看学校信息"
        )
    
    return success_response(
        data=SchoolResponse.from_orm(school).model_dump()
    )

@router.put("/{school_uuid}", response_model=dict)
async def update_school(
    school_uuid: str,
    school_update: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新学校信息（通过UUID）"""
    
    # 平台管理员可以更新所有学校
    # 学校管理员只能更新自己的学校（但不能修改某些字段）
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 权限检查
    if current_user.role == 'platform_admin':
        # 平台管理员可以更新所有字段
        pass
    elif current_user.role == 'school_admin':
        if current_user.school_id != school.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能更新本校信息"
            )
        # 学校管理员不能修改以下字段
        if school_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="学校管理员不能修改激活状态"
            )
        if school_update.license_expire_at is not None or \
           school_update.max_teachers is not None or \
           school_update.max_students is not None or \
           school_update.max_devices is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="学校管理员不能修改配额和授权信息"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限更新学校信息"
        )
    
    # 更新字段
    update_data = school_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(school, key, value)
    
    db.commit()
    db.refresh(school)
    
    return success_response(
        data=SchoolResponse.from_orm(school).model_dump(),
        message="学校信息更新成功"
    )

@router.delete("/{school_uuid}", response_model=dict)
async def delete_school(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_platform_admin)
):
    """删除学校（仅平台管理员，通过UUID）"""
    
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 检查是否有关联用户
    user_count = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.deleted_at.is_(None)
    ).scalar()
    
    if user_count > 0:
        return error_response(
            message=f"该学校还有{user_count}个用户，无法删除",
            code=400
        )
    
    # 删除学校
    db.delete(school)
    db.commit()
    
    return success_response(
        message="学校删除成功"
    )

@router.get("/{school_uuid}/statistics", response_model=dict)
async def get_school_statistics(
    school_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学校统计信息（通过UUID）"""
    
    # 先通过UUID查找学校
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 权限检查
    if current_user.role == 'platform_admin':
        pass
    elif current_user.role == 'school_admin':
        if current_user.school_id != school.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能查看本校统计信息"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看学校统计信息"
        )
    
    # 统计教师数
    total_teachers = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role.in_(['teacher', 'school_admin']),
        User.deleted_at.is_(None)
    ).scalar()
    
    # 统计学生数
    total_students = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.role == 'student',
        User.deleted_at.is_(None)
    ).scalar()
    
    # 统计活跃用户数
    active_users = db.query(func.count(User.id)).filter(
        User.school_id == school.id,
        User.is_active == True,
        User.deleted_at.is_(None)
    ).scalar()
    
    # 计算使用率
    usage_rate = {
        "teachers": round(total_teachers / school.max_teachers * 100, 2) if school.max_teachers > 0 else 0,
        "students": round(total_students / school.max_students * 100, 2) if school.max_students > 0 else 0,
    }
    
    statistics = SchoolStatistics(
        school_id=school.id,
        school_name=school.school_name,
        total_teachers=total_teachers,
        total_students=total_students,
        total_devices=0,  # TODO: 统计设备数
        total_agents=0,  # TODO: 统计智能体数
        active_users=active_users,
        max_teachers=school.max_teachers,
        max_students=school.max_students,
        max_devices=school.max_devices,
        usage_rate=usage_rate
    )
    
    return success_response(data=statistics)

