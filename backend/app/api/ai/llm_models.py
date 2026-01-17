"""
大模型配置管理API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.llm_model import LLMModel
from app.models.llm_provider import LLMProvider
from app.api.auth import get_current_user
from app.models.user import User
from app.core.response import success_response
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员（基于角色判断）"""
    return user.role in ['platform_admin', 'super_admin', 'admin']


# ============================================================================
# Pydantic Schemas
# ============================================================================

class LLMModelBase(BaseModel):
    model_config = {"protected_namespaces": ()}  # 允许使用model_开头的字段
    
    name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    provider: str = Field(..., description="提供商")
    model_type: str = Field(default="chat", description="模型类型")
    api_base: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    api_version: Optional[str] = Field(None, description="API版本")
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.70, description="温度参数")
    top_p: float = Field(default=0.90, description="top_p参数")
    enable_deep_thinking: int = Field(default=0, description="是否启用深度思考")
    frequency_penalty: Optional[float] = Field(default=0.00, description="频率惩罚参数")
    presence_penalty: Optional[float] = Field(default=0.00, description="存在惩罚参数")
    config: Optional[dict] = Field(None, description="其他配置参数")
    description: Optional[str] = Field(None, description="模型描述")
    is_active: int = Field(default=1, description="是否激活")
    is_default: int = Field(default=0, description="是否默认模型")
    sort_order: int = Field(default=0, description="排序顺序")


class LLMModelCreate(LLMModelBase):
    pass


class LLMModelUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}  # 允许使用model_开头的字段
    
    name: Optional[str] = None
    display_name: Optional[str] = None
    provider: Optional[str] = None
    model_type: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    enable_deep_thinking: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    config: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[int] = None
    is_default: Optional[int] = None
    sort_order: Optional[int] = None


class LLMModelResponse(LLMModelBase):
    id: int
    uuid: str = Field(..., description="唯一标识UUID")
    is_system: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LLMModelList(BaseModel):
    items: List[LLMModelResponse]
    total: int


class LLMProviderResponse(BaseModel):
    """提供商响应模式"""
    id: int
    uuid: str = Field(..., description="唯一标识UUID")
    code: str = Field(..., description="提供商代码")
    name: str = Field(..., description="提供商名称")
    title: str = Field(..., description="完整标题")
    description: Optional[str] = Field(None, description="提供商描述")
    apply_url: Optional[str] = Field(None, description="API申请地址")
    doc_url: Optional[str] = Field(None, description="文档地址")
    default_api_base: Optional[str] = Field(None, description="默认API地址")
    has_free_quota: int = Field(..., description="是否提供免费额度")
    icon: Optional[str] = Field(None, description="图标URL或图标名称")
    tag_type: Optional[str] = Field(None, description="标签类型")
    country: Optional[str] = Field(None, description="国家")
    sort_order: int = Field(..., description="排序顺序")
    is_active: int = Field(..., description="是否启用")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=LLMModelResponse)
def create_llm_model(
    model_data: LLMModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的大模型配置（仅管理员）"""
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="只有管理员可以创建模型配置")
    
    # 检查模型名称是否已存在
    existing = db.query(LLMModel).filter(LLMModel.name == model_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，取消其他模型的默认状态
    if model_data.is_default == 1:
        db.query(LLMModel).filter(LLMModel.is_default == 1).update({"is_default": 0})
    
    # 创建新模型
    db_model = LLMModel(**model_data.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model


@router.get("", response_model=LLMModelList)
def get_llm_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="搜索关键词"),
    provider: Optional[str] = Query(None, description="提供商筛选"),
    is_active: Optional[int] = Query(None, description="激活状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取大模型配置列表"""
    query = db.query(LLMModel).filter(LLMModel.is_deleted == 0)
    
    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                LLMModel.name.contains(search),
                LLMModel.display_name.contains(search),
                LLMModel.description.contains(search)
            )
        )
    
    # 提供商过滤
    if provider:
        query = query.filter(LLMModel.provider == provider)
    
    # 激活状态过滤
    if is_active is not None:
        query = query.filter(LLMModel.is_active == is_active)
    
    # 排序
    query = query.order_by(LLMModel.sort_order.asc(), LLMModel.created_at.desc())
    
    # 获取总数
    total = query.count()
    
    # 分页
    items = query.offset(skip).limit(limit).all()
    
    return {"items": items, "total": total}


@router.get("/providers", response_model=List[LLMProviderResponse])
def get_llm_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有提供商信息"""
    try:
        providers = db.query(LLMProvider).filter(
            LLMProvider.is_active == 1
        ).order_by(
            LLMProvider.sort_order.asc()
        ).all()
        
        # 调试：打印查询结果
        print(f"查询到 {len(providers)} 个提供商")
        for provider in providers:
            print(f"Provider: id={provider.id}, uuid={provider.uuid}, code={provider.code}, name={provider.name}")
        
        return providers
    except Exception as e:
        print(f"获取提供商列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")


@router.get("/active", response_model=List[LLMModelResponse])
def get_active_llm_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有激活的大模型配置（用于智能体选择）"""
    models = db.query(LLMModel).filter(
        LLMModel.is_active == 1,
        LLMModel.is_deleted == 0
    ).order_by(
        LLMModel.sort_order.asc(),
        LLMModel.created_at.desc()
    ).all()
    
    return models


@router.get("/default", response_model=LLMModelResponse)
def get_default_llm_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取默认的大模型配置"""
    model = db.query(LLMModel).filter(
        LLMModel.is_default == 1,
        LLMModel.is_active == 1,
        LLMModel.is_deleted == 0
    ).first()
    
    if not model:
        # 如果没有设置默认模型，返回第一个激活的模型
        model = db.query(LLMModel).filter(
            LLMModel.is_active == 1,
            LLMModel.is_deleted == 0
        ).order_by(LLMModel.sort_order.asc()).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="没有可用的模型配置")
    
    return model


@router.get("/{model_id}", response_model=LLMModelResponse)
def get_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定ID的大模型配置"""
    model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_deleted == 0
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return model


@router.put("/{model_id}", response_model=LLMModelResponse)
def update_llm_model(
    model_id: int,
    model_update: LLMModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新大模型配置（仅管理员）"""
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="只有管理员可以修改模型配置")
    
    db_model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_deleted == 0
    ).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    # 系统内置模型的某些字段不能修改
    update_data = model_update.model_dump(exclude_unset=True)
    
    # 如果设置为默认模型，取消其他模型的默认状态
    if update_data.get("is_default") == 1:
        db.query(LLMModel).filter(
            LLMModel.id != model_id,
            LLMModel.is_default == 1
        ).update({"is_default": 0})
    
    # 更新模型
    for key, value in update_data.items():
        setattr(db_model, key, value)
    
    db.commit()
    db.refresh(db_model)
    
    return db_model


@router.delete("/{model_id}")
def delete_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除大模型配置（软删除，仅管理员，不能删除系统内置）"""
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="只有管理员可以删除模型配置")
    
    db_model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_deleted == 0
    ).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if db_model.is_system == 1:
        raise HTTPException(status_code=400, detail="系统内置模型不能删除")
    
    # 软删除：标记为已删除
    db_model.is_deleted = 1
    db.commit()
    
    return success_response(message="删除成功")


@router.post("/{model_id}/set-default", response_model=LLMModelResponse)
def set_default_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置默认大模型（仅管理员）"""
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="只有管理员可以设置默认模型")
    
    db_model = db.query(LLMModel).filter(
        LLMModel.id == model_id,
        LLMModel.is_deleted == 0
    ).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if db_model.is_active != 1:
        raise HTTPException(status_code=400, detail="只能设置激活的模型为默认模型")
    
    # 取消其他模型的默认状态
    db.query(LLMModel).filter(LLMModel.is_default == 1).update({"is_default": 0})
    
    # 设置当前模型为默认
    db_model.is_default = 1
    db.commit()
    db.refresh(db_model)
    
    return db_model

