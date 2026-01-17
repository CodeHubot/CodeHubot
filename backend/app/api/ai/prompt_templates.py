"""
提示词模板API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateList
)

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员（基于角色判断）"""
    return user.role in ['platform_admin', 'super_admin', 'admin']

@router.get("/", response_model=PromptTemplateList)
def get_prompt_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取提示词模板列表（权限隔离）
    
    - 返回系统模板（is_system=1）和当前用户创建的个人模板
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认50，最大100）
    - **category**: 按分类筛选（可选）
    - **difficulty**: 按难度筛选（可选）
    - **is_active**: 按激活状态筛选（可选）
    """
    # 构建查询 - 只返回系统模板或当前用户的模板，并排除已删除的
    query = db.query(PromptTemplate).filter(
        PromptTemplate.is_deleted == 0,
        (PromptTemplate.is_system == True) | 
        (PromptTemplate.user_id == current_user.id)
    )
    
    # 应用筛选条件
    if category:
        query = query.filter(PromptTemplate.category == category)
    if difficulty:
        query = query.filter(PromptTemplate.difficulty == difficulty)
    if is_active is not None:
        query = query.filter(PromptTemplate.is_active == is_active)
    
    # 排序：系统模板优先，然后按sort_order和id排序
    query = query.order_by(
        PromptTemplate.is_system.desc(),
        PromptTemplate.sort_order,
        PromptTemplate.id
    )
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{template_uuid}", response_model=PromptTemplateResponse)
def get_prompt_template(
    template_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个提示词模板详情（权限隔离）
    
    - 只能查看系统模板或自己创建的模板
    - **template_uuid**: 模板UUID
    """
    template = db.query(PromptTemplate).filter(
        PromptTemplate.uuid == template_uuid,
        PromptTemplate.is_deleted == 0,
        (PromptTemplate.is_system == True) | 
        (PromptTemplate.user_id == current_user.id)
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在或无权访问"
        )
    
    return template

@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_template(
    template_data: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建提示词模板
    
    - 管理员可以创建系统模板（is_system=True）或个人模板
    - 普通用户只能创建个人模板（is_system=False）
    """
    # 创建模板数据
    template_dict = template_data.dict()
    
    # 权限检查：只有管理员可以创建系统模板
    if template_dict.get('is_system', False):
        if not is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以创建系统模板"
            )
        # 系统模板不设置user_id
        template_dict['user_id'] = None
    else:
        # 个人模板设置当前用户ID
        template_dict['user_id'] = current_user.id
        template_dict['is_system'] = False
    
    # 创建模板
    template = PromptTemplate(**template_dict)
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.put("/{template_uuid}", response_model=PromptTemplateResponse)
def update_prompt_template(
    template_uuid: str,
    template_data: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新提示词模板（权限隔离）
    
    - 管理员可以更新所有模板
    - 普通用户只能更新自己创建的个人模板
    - 普通用户不能将个人模板改为系统模板
    """
    # 查找模板（排除已删除）
    template = db.query(PromptTemplate).filter(
        PromptTemplate.uuid == template_uuid,
        PromptTemplate.is_deleted == 0
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 权限检查
    is_admin = is_admin_user(current_user)
    
    # 系统模板只有管理员可以修改
    if template.is_system and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改系统模板"
        )
    
    # 个人模板只能由创建者或管理员修改
    if not template.is_system and template.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此模板"
        )
    
    # 更新字段
    update_data = template_data.dict(exclude_unset=True)
    
    # 普通用户不能将个人模板改为系统模板
    if 'is_system' in update_data and update_data['is_system'] and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建系统模板"
        )
    
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template

@router.delete("/{template_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt_template(
    template_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除提示词模板（软删除 + 权限隔离）
    
    - 管理员可以删除所有模板
    - 普通用户只能删除自己创建的个人模板
    - 采用软删除，不物理删除数据
    """
    # 查找模板（排除已删除）
    template = db.query(PromptTemplate).filter(
        PromptTemplate.uuid == template_uuid,
        PromptTemplate.is_deleted == 0
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 权限检查
    is_admin = is_admin_user(current_user)
    
    # 系统模板只有管理员可以删除
    if template.is_system and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除系统模板"
        )
    
    # 个人模板只能由创建者或管理员删除
    if not template.is_system and template.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此模板"
        )
    
    # 软删除：标记为已删除
    template.is_deleted = 1
    db.commit()
    
    return None

