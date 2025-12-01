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
    """判断用户是否为管理员"""
    return user.email == "admin@aiot.com" or user.username == "admin" or user.role == "admin"

@router.get("/", response_model=PromptTemplateList)
def get_prompt_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db)
):
    """
    获取提示词模板列表
    
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认50，最大100）
    - **category**: 按分类筛选（可选）
    - **difficulty**: 按难度筛选（可选）
    - **is_active**: 按激活状态筛选（可选）
    """
    # 构建查询
    query = db.query(PromptTemplate)
    
    # 应用筛选条件
    if category:
        query = query.filter(PromptTemplate.category == category)
    if difficulty:
        query = query.filter(PromptTemplate.difficulty == difficulty)
    if is_active is not None:
        query = query.filter(PromptTemplate.is_active == is_active)
    
    # 排序
    query = query.order_by(PromptTemplate.sort_order, PromptTemplate.id)
    
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

@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个提示词模板详情
    
    - **template_id**: 模板ID
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    return template

@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_template(
    template_data: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建提示词模板（仅管理员）
    
    需要管理员权限
    """
    # 检查权限
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限创建模板"
        )
    
    # 创建模板
    template = PromptTemplate(**template_data.dict())
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.put("/{template_id}", response_model=PromptTemplateResponse)
def update_prompt_template(
    template_id: int,
    template_data: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新提示词模板（仅管理员）
    
    需要管理员权限
    """
    # 检查权限
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新模板"
        )
    
    # 查找模板
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 更新字段
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除提示词模板（仅管理员）
    
    需要管理员权限
    """
    # 检查权限
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除模板"
        )
    
    # 查找模板
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 删除模板
    db.delete(template)
    db.commit()
    
    return None

