"""
学校可用课程模板 API
供学校管理员查看平台开放给本校的课程模板
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
from datetime import datetime
from app.utils.timezone import get_beijing_time_naive
import uuid

from ...core.deps import get_db, get_current_admin
from ...core.response import success_response
from ...models.pbl import (
    PBLTemplateSchoolPermission, 
    PBLCourseTemplate,
    PBLCourse,
    PBLUnitTemplate,
    PBLResourceTemplate,
    PBLTaskTemplate
)
from ...models.admin import Admin

router = APIRouter()


def check_school_admin(current_user: Admin):
    """检查是否为学校管理员或教师"""
    if current_user.role not in ['school_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="仅学校管理员或教师可以访问")
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="用户未关联学校")
    return current_user


@router.get("", response_model=dict)
async def list_available_templates(
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    category: Optional[str] = Query(None, description="类别筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    获取学校可用的课程模板列表
    仅显示平台已开放给本学校的模板
    """
    check_school_admin(current_user)
    
    # 查询开放给本学校的模板权限
    now = get_beijing_time_naive()
    permission_query = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.school_id == current_user.school_id,
        PBLTemplateSchoolPermission.is_active == 1,
        or_(
            PBLTemplateSchoolPermission.valid_from.is_(None),
            PBLTemplateSchoolPermission.valid_from <= now
        ),
        or_(
            PBLTemplateSchoolPermission.valid_until.is_(None),
            PBLTemplateSchoolPermission.valid_until >= now
        )
    )
    
    # 获取模板ID列表
    template_ids = [p.template_id for p in permission_query.all()]
    
    if not template_ids:
        return success_response(data={
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": []
        })
    
    # 查询模板
    query = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.id.in_(template_ids)
    )
    
    # 筛选条件
    if difficulty:
        query = query.filter(PBLCourseTemplate.difficulty == difficulty)
    if category:
        query = query.filter(PBLCourseTemplate.category == category)
    if search:
        query = query.filter(
            or_(
                PBLCourseTemplate.title.like(f"%{search}%"),
                PBLCourseTemplate.description.like(f"%{search}%")
            )
        )
    
    # 分页
    total = query.count()
    templates = query.order_by(
        PBLCourseTemplate.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    # 组装结果
    result = []
    for template in templates:
        # 获取权限信息
        permission = db.query(PBLTemplateSchoolPermission).filter(
            PBLTemplateSchoolPermission.template_id == template.id,
            PBLTemplateSchoolPermission.school_id == current_user.school_id
        ).first()
        
        # 统计本校已创建的实例数
        instance_count = db.query(PBLCourse).filter(
            PBLCourse.template_id == template.id,
            PBLCourse.school_id == current_user.school_id
        ).count()
        
        # 检查是否可以继续创建实例
        can_create_instance = True
        if permission and permission.max_instances is not None:
            can_create_instance = instance_count < permission.max_instances
        
        result.append({
            "id": template.id,
            "uuid": template.uuid,
            "title": template.title,
            "description": template.description,
            "cover_image": template.cover_image,
            "duration": template.duration,
            "difficulty": template.difficulty,
            "category": template.category,
            "version": template.version,
            "usage_count": template.usage_count,
            "permission": {
                "id": permission.id if permission else None,
                "uuid": permission.uuid if permission else None,
                "can_customize": permission.can_customize if permission else None,
                "max_instances": permission.max_instances if permission else None,
                "current_instances": instance_count,
                "can_create_instance": can_create_instance,
                "valid_from": permission.valid_from if permission else None,
                "valid_until": permission.valid_until if permission else None,
                "remarks": permission.remarks if permission else None
            } if permission else None,
            "created_at": template.created_at,
            "updated_at": template.updated_at
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result
    })


@router.get("/{template_uuid}", response_model=dict)
async def get_available_template_detail(
    template_uuid: str,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    获取可用模板详情
    包括模板内容和权限信息
    """
    check_school_admin(current_user)
    
    # 查询模板
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.uuid == template_uuid
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限
    now = get_beijing_time_naive()
    permission = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.template_id == template.id,
        PBLTemplateSchoolPermission.school_id == current_user.school_id,
        PBLTemplateSchoolPermission.is_active == 1,
        or_(
            PBLTemplateSchoolPermission.valid_from.is_(None),
            PBLTemplateSchoolPermission.valid_from <= now
        ),
        or_(
            PBLTemplateSchoolPermission.valid_until.is_(None),
            PBLTemplateSchoolPermission.valid_until >= now
        )
    ).first()
    
    if not permission:
        raise HTTPException(status_code=403, detail="您的学校无权访问此模板")
    
    # 统计已创建实例
    instance_count = db.query(PBLCourse).filter(
        PBLCourse.template_id == template.id,
        PBLCourse.school_id == current_user.school_id
    ).count()
    
    can_create_instance = True
    if permission.max_instances is not None:
        can_create_instance = instance_count < permission.max_instances
    
    # 查询单元模板及其资源和任务
    units = db.query(PBLUnitTemplate).filter(
        PBLUnitTemplate.course_template_id == template.id
    ).order_by(PBLUnitTemplate.order).all()
    
    units_data = []
    for unit in units:
        # 查询单元的资源
        resources = db.query(PBLResourceTemplate).filter(
            PBLResourceTemplate.unit_template_id == unit.id
        ).order_by(PBLResourceTemplate.order).all()
        
        # 查询单元的任务
        tasks = db.query(PBLTaskTemplate).filter(
            PBLTaskTemplate.unit_template_id == unit.id
        ).order_by(PBLTaskTemplate.order).all()
        
        units_data.append({
            "id": unit.id,
            "uuid": unit.uuid,
            "template_code": unit.template_code,
            "title": unit.title,
            "description": unit.description,
            "order": unit.order,
            "learning_objectives": unit.learning_objectives,
            "key_concepts": unit.key_concepts,
            "estimated_duration": unit.estimated_duration,
            "resources_count": len(resources),
            "tasks_count": len(tasks),
            "resources": [
                {
                    "id": res.id,
                    "uuid": res.uuid,
                    "template_code": res.template_code,
                    "resource_type": res.type,
                    "title": res.title,
                    "description": res.description,
                    "order": res.order,
                    "url": res.url,
                    "video_id": res.video_id,
                    "video_cover_url": res.video_cover_url,
                    "duration": res.duration,
                    "is_preview_allowed": res.is_preview_allowed
                }
                for res in resources
            ],
            "tasks": [
                {
                    "id": task.id,
                    "uuid": task.uuid,
                    "template_code": task.template_code,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.type,
                    "difficulty": task.difficulty,
                    "order": task.order,
                    "requirements": task.requirements,
                    "deliverables": task.deliverables,
                    "evaluation_criteria": task.evaluation_criteria,
                    "estimated_time": task.estimated_time,
                    "estimated_hours": task.estimated_hours
                }
                for task in tasks
            ]
        })
    
    return success_response(data={
        "id": template.id,
        "uuid": template.uuid,
        "title": template.title,
        "description": template.description,
        "cover_image": template.cover_image,
        "duration": template.duration,
        "difficulty": template.difficulty,
        "category": template.category,
        "version": template.version,
        "is_public": template.is_public,
        "usage_count": template.usage_count,
        "permission": {
            "id": permission.id,
            "uuid": permission.uuid,
            "can_customize": permission.can_customize,
            "max_instances": permission.max_instances,
            "current_instances": instance_count,
            "can_create_instance": can_create_instance,
            "valid_from": permission.valid_from,
            "valid_until": permission.valid_until,
            "remarks": permission.remarks
        },
        "units": units_data,
        "created_at": template.created_at,
        "updated_at": template.updated_at
    })


@router.post("/{template_uuid}/create-course", response_model=dict)
async def create_course_from_template(
    template_uuid: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """
    基于模板创建课程实例
    """
    check_school_admin(current_user)
    
    # 查询模板
    template = db.query(PBLCourseTemplate).filter(
        PBLCourseTemplate.uuid == template_uuid
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限
    now = get_beijing_time_naive()
    permission = db.query(PBLTemplateSchoolPermission).filter(
        PBLTemplateSchoolPermission.template_id == template.id,
        PBLTemplateSchoolPermission.school_id == current_user.school_id,
        PBLTemplateSchoolPermission.is_active == 1,
        or_(
            PBLTemplateSchoolPermission.valid_from.is_(None),
            PBLTemplateSchoolPermission.valid_from <= now
        ),
        or_(
            PBLTemplateSchoolPermission.valid_until.is_(None),
            PBLTemplateSchoolPermission.valid_until >= now
        )
    ).first()
    
    if not permission:
        raise HTTPException(status_code=403, detail="您的学校无权使用此模板")
    
    # 检查实例数限制
    instance_count = db.query(PBLCourse).filter(
        PBLCourse.template_id == template.id,
        PBLCourse.school_id == current_user.school_id
    ).count()
    
    if permission.max_instances is not None and instance_count >= permission.max_instances:
        raise HTTPException(
            status_code=400, 
            detail=f"已达到最大实例数限制（{permission.max_instances}）"
        )
    
    # 创建课程
    course = PBLCourse(
        uuid=str(uuid.uuid4()),
        template_id=template.id,
        template_version=template.version,
        permission_id=permission.id,
        title=title or template.title,
        description=description or template.description,
        cover_image=template.cover_image,
        duration=template.duration,
        difficulty=template.difficulty,
        status='draft',
        creator_id=current_user.id,
        school_id=current_user.school_id,
        class_id=class_id,
        is_customized=0,
        sync_with_template=1
    )
    
    db.add(course)
    
    # 更新权限的实例计数
    permission.current_instances = instance_count + 1
    
    db.commit()
    db.refresh(course)
    
    return success_response(
        message=f"成功基于模板「{template.title}」创建课程",
        data={
            "course_id": course.id,
            "course_uuid": course.uuid,
            "course_title": course.title,
            "template_title": template.title
        }
    )
