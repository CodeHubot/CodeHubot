"""
插件管理API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plugin import Plugin
from app.schemas.plugin import (
    PluginCreate, PluginUpdate, PluginResponse, PluginList
)
from app.api.auth import get_current_user
from app.models.user import User
from app.core.response import success_response

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员"""
    return user.email == "admin@aiot.com" or user.username == "admin" or user.role == "admin"


def can_access_plugin(plugin: Plugin, user: User) -> bool:
    """判断用户是否可以访问插件"""
    if is_admin_user(user):
        return True
    # 系统内置插件：所有用户可以访问
    if plugin.is_system == 1:
        return True
    # 用户创建的插件：只有创建者可以访问
    return plugin.user_id == user.id


def can_edit_plugin(plugin: Plugin, user: User) -> bool:
    """判断用户是否可以编辑插件"""
    if is_admin_user(user):
        return True
    # 系统内置插件：只有管理员可编辑
    if plugin.is_system == 1:
        return False
    # 用户创建的插件：只有创建者可编辑
    return plugin.user_id == user.id


def validate_openapi_spec(openapi_spec: dict) -> bool:
    """验证 OpenAPI 规范格式"""
    if not isinstance(openapi_spec, dict):
        return False
    
    # 检查必需字段
    if "openapi" not in openapi_spec:
        return False
    
    if "info" not in openapi_spec:
        return False
    
    if "paths" not in openapi_spec:
        return False
    
    # 检查 info 字段
    info = openapi_spec.get("info", {})
    if not isinstance(info, dict) or "title" not in info:
        return False
    
    return True


@router.post("", response_model=PluginResponse)
def create_plugin(
    plugin: PluginCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新插件"""
    # 验证 OpenAPI 规范格式
    if not validate_openapi_spec(plugin.openapi_spec):
        raise HTTPException(
            status_code=400,
            detail="OpenAPI 规范格式无效，必须包含 openapi、info、paths 字段"
        )
    
    # 创建插件数据
    plugin_data = plugin.model_dump()
    plugin_data['user_id'] = current_user.id
    plugin_data['is_system'] = 0  # 普通用户创建的非系统插件
    
    db_plugin = Plugin(**plugin_data)
    db.add(db_plugin)
    db.commit()
    db.refresh(db_plugin)
    
    return db_plugin


@router.get("", response_model=PluginList)
def get_plugins(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    is_active: Optional[int] = Query(None, description="是否激活筛选（1=激活，0=禁用）"),
    is_system: Optional[bool] = Query(None, description="是否系统内建筛选（仅管理员）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件列表"""
    query = db.query(Plugin)
    
    # 权限过滤
    if is_admin_user(current_user):
        # 管理员：看到所有插件
        if is_system is not None:
            query = query.filter(Plugin.is_system == (1 if is_system else 0))
    else:
        # 普通用户：只看到系统内置插件和自己创建的
        query = query.filter(
            (Plugin.is_system == 1) | (Plugin.user_id == current_user.id)
        )
    
    # 激活状态筛选
    if is_active is not None:
        query = query.filter(Plugin.is_active == is_active)
    
    # 搜索
    if search:
        query = query.filter(
            (Plugin.name.contains(search)) | 
            (Plugin.description.contains(search))
        )
    
    # 总数
    total = query.count()
    
    # 排序和分页
    query = query.order_by(Plugin.created_at.desc())
    plugins = query.offset(skip).limit(limit).all()
    
    return PluginList(total=total, items=plugins)


@router.get("/{plugin_uuid}", response_model=PluginResponse)
def get_plugin(
    plugin_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件详情（通过UUID）"""
    plugin = db.query(Plugin).filter(Plugin.uuid == plugin_uuid).first()
    
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if not can_access_plugin(plugin, current_user):
        raise HTTPException(status_code=403, detail="无权访问此插件")
    
    return plugin


@router.put("/{plugin_uuid}", response_model=PluginResponse)
def update_plugin(
    plugin_uuid: str,
    plugin_update: PluginUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新插件（通过UUID）"""
    plugin = db.query(Plugin).filter(Plugin.uuid == plugin_uuid).first()
    
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if not can_edit_plugin(plugin, current_user):
        raise HTTPException(status_code=403, detail="无权编辑此插件")
    
    # 如果更新了 openapi_spec，验证格式
    if plugin_update.openapi_spec is not None:
        if not validate_openapi_spec(plugin_update.openapi_spec):
            raise HTTPException(
                status_code=400,
                detail="OpenAPI 规范格式无效，必须包含 openapi、info、paths 字段"
            )
    
    # 更新字段
    update_data = plugin_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plugin, field, value)
    
    db.commit()
    db.refresh(plugin)
    
    return plugin


@router.delete("/{plugin_uuid}")
def delete_plugin(
    plugin_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除插件（通过UUID）"""
    plugin = db.query(Plugin).filter(Plugin.uuid == plugin_uuid).first()
    
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if not can_edit_plugin(plugin, current_user):
        raise HTTPException(status_code=403, detail="无权删除此插件")
    
    # 系统内置插件不允许删除
    if plugin.is_system == 1:
        raise HTTPException(status_code=400, detail="系统内置插件不允许删除")
    
    # 检查是否有智能体在使用此插件
    from app.models.agent import Agent
    agents_using_plugin = db.query(Agent).filter(
        Agent.plugin_ids.contains([plugin.id])
    ).count()
    
    if agents_using_plugin > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：有 {agents_using_plugin} 个智能体正在使用此插件"
        )
    
    db.delete(plugin)
    db.commit()
    
    return success_response(message="插件已删除")

