"""
课程模板学校开放权限管理 API
仅供平台管理员使用
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from ...core.deps import get_db, get_current_admin
from ...core.response import success_response
from ...models.pbl import PBLTemplateSchoolPermission, PBLCourseTemplate
from ...models.admin import Admin
from ...models.school import School
from ...schemas.pbl import (
    TemplateSchoolPermissionCreate,
    TemplateSchoolPermissionUpdate,
    TemplateSchoolPermission,
    TemplateSchoolPermissionWithDetails
)

router = APIRouter()


def check_platform_admin(current_user: Admin):
    """检查是否为平台管理员"""
    if current_user.role != 'platform_admin':
        raise HTTPException(status_code=403, detail="仅平台管理员可以访问")
    return current_user


@router.post("/template-permissions", response_model=dict)
async def create_template_permission(
    permission_data: TemplateSchoolPermissionCreate,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    创建课程模板开放权限
    平台管理员将模板课程开放给指定学校
    """
    check_platform_admin(current_user)
    
    # 检查模板是否存在
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.id == permission_data.template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="课程模板不存在")
    
    # 检查学校是否存在
    school = db.query(School).filter(School.id == permission_data.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    # 检查是否已存在权限记录
    existing = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.template_id == permission_data.template_id,
        PBLTemplateSchoolPermission.school_id == permission_data.school_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该学校已有此模板的开放权限")
    
    # 创建权限记录
    permission = PBLTemplateSchoolPermission(
        uuid=str(uuid.uuid4()),
        template_id=permission_data.template_id,
        school_id=permission_data.school_id,
        is_active=permission_data.is_active,
        can_customize=permission_data.can_customize,
        max_instances=permission_data.max_instances,
        valid_from=permission_data.valid_from,
        valid_until=permission_data.valid_until,
        remarks=permission_data.remarks,
        granted_by=current_user.id,
        current_instances=0
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return success_response(
        data={
            "id": permission.id,
            "uuid": permission.uuid,
            "template_title": template.title,
            "school_name": school.school_name
        },
        message=f"已成功将课程模板「{template.title}」开放给「{school.school_name}」"
    )


@router.get("/template-permissions", response_model=dict)
async def list_template_permissions(
    template_id: Optional[int] = Query(None, description="模板ID"),
    school_id: Optional[int] = Query(None, description="学校ID"),
    is_active: Optional[int] = Query(None, description="是否激活"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    获取课程模板开放权限列表
    支持按模板、学校筛选
    """
    check_platform_admin(current_user)
    
    query = db.query(PBLTemplateSchoolPermission)
    
    # 筛选条件
    if template_id:
        query = query.filter(PBLTemplateSchoolPermission.template_id == template_id)
    if school_id:
        query = query.filter(PBLTemplateSchoolPermission.school_id == school_id)
    if is_active is not None:
        query = query.filter(PBLTemplateSchoolPermission.is_active == is_active)
    
    # 分页
    total = query.count()
    permissions = query.order_by(
        PBLTemplateSchoolPermission.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取关联的模板和学校信息
    result = []
    for perm in permissions:
        template = db.query(PBLCourseTemplate).filter(
            PBLCourseTemplate.id == perm.template_id
        ).first()
        school = db.query(School).filter(School.id == perm.school_id).first()
        
        result.append({
            "id": perm.id,
            "uuid": perm.uuid,
            "template_id": perm.template_id,
            "template_title": template.title if template else None,
            "template_difficulty": template.difficulty if template else None,
            "school_id": perm.school_id,
            "school_name": school.school_name if school else None,
            "is_active": perm.is_active,
            "can_customize": perm.can_customize,
            "max_instances": perm.max_instances,
            "current_instances": perm.current_instances,
            "valid_from": perm.valid_from,
            "valid_until": perm.valid_until,
            "granted_by": perm.granted_by,
            "granted_at": perm.granted_at,
            "remarks": perm.remarks,
            "created_at": perm.created_at,
            "updated_at": perm.updated_at
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result
    })


@router.get("/template-permissions/{permission_uuid}", response_model=dict)
async def get_template_permission(
    permission_uuid: str,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """获取单个模板开放权限详情"""
    check_platform_admin(current_user)
    
    permission = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.uuid == permission_uuid
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="权限记录不存在")
    
    # 获取关联信息
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.id == permission.template_id
    ).first()
    school = db.query(School).filter(School.id == permission.school_id).first()
    
    return success_response(data={
        "id": permission.id,
        "uuid": permission.uuid,
        "template": {
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "difficulty": template.difficulty,
            "cover_image": template.cover_image
        } if template else None,
        "school": {
            "id": school.id,
            "name": school.school_name,
            "code": school.school_code
        } if school else None,
        "is_active": permission.is_active,
        "can_customize": permission.can_customize,
        "max_instances": permission.max_instances,
        "current_instances": permission.current_instances,
        "valid_from": permission.valid_from,
        "valid_until": permission.valid_until,
        "granted_by": permission.granted_by,
        "granted_at": permission.granted_at,
        "remarks": permission.remarks,
        "created_at": permission.created_at,
        "updated_at": permission.updated_at
    })


@router.put("/template-permissions/{permission_uuid}", response_model=dict)
async def update_template_permission(
    permission_uuid: str,
    permission_data: TemplateSchoolPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """更新模板开放权限"""
    check_platform_admin(current_user)
    
    permission = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.uuid == permission_uuid
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="权限记录不存在")
    
    # 更新字段
    update_data = permission_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)
    
    db.commit()
    db.refresh(permission)
    
    return success_response(
        data={
            "id": permission.id,
            "uuid": permission.uuid
        },
        message="权限更新成功"
    )


@router.delete("/template-permissions/{permission_uuid}", response_model=dict)
async def delete_template_permission(
    permission_uuid: str,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """删除模板开放权限"""
    check_platform_admin(current_user)
    
    permission = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.uuid == permission_uuid
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="权限记录不存在")
    
    # 检查是否已有课程实例
    if permission.current_instances > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"该权限下已有 {permission.current_instances} 个课程实例，无法删除"
        )
    
    db.delete(permission)
    db.commit()
    
    return success_response(message="权限删除成功")


@router.post("/template-permissions/batch-grant", response_model=dict)
async def batch_grant_permissions(
    template_id: int,
    school_ids: List[int],
    is_active: int = 1,
    can_customize: int = 1,
    max_instances: Optional[int] = None,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
    remarks: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    批量开放模板给多个学校
    """
    check_platform_admin(current_user)
    
    # 检查模板是否存在
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.id == template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="课程模板不存在")
    
    success_count = 0
    failed_schools = []
    
    for school_id in school_ids:
        # 检查学校是否存在
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            failed_schools.append({"school_id": school_id, "reason": "学校不存在"})
            continue
        
        # 检查是否已存在
        existing = db.query(PBLTemplateSchoolPermission).filter(
            PBLTemplateSchoolPermission.template_id == template_id,
            PBLTemplateSchoolPermission.school_id == school_id
        ).first()
        
        if existing:
            failed_schools.append({
                "school_id": school_id, 
                "school_name": school.school_name,
                "reason": "已存在权限记录"
            })
            continue
        
        # 创建权限
        permission = PBLTemplateSchoolPermission(
            uuid=str(uuid.uuid4()),
            template_id=template_id,
            school_id=school_id,
            is_active=is_active,
            can_customize=can_customize,
            max_instances=max_instances,
            valid_from=valid_from,
            valid_until=valid_until,
            remarks=remarks,
            granted_by=current_user.id,
            current_instances=0
        )
        
        db.add(permission)
        success_count += 1
    
    db.commit()
    
    return success_response(
        data={
            "template_title": template.title,
            "success_count": success_count,
            "failed_count": len(failed_schools),
            "failed_schools": failed_schools
        },
        message=f"成功开放给 {success_count} 个学校"
    )
