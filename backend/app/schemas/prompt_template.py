"""
提示词模板Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class PromptTemplateBase(BaseModel):
    """提示词模板基础Schema"""
    name: str = Field(..., max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=255, description="模板描述")
    content: str = Field(..., description="提示词内容")
    category: Optional[str] = Field(None, max_length=50, description="分类标签")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    difficulty: Optional[str] = Field(None, max_length=20, description="难度等级：easy/medium/hard")
    suitable_for: Optional[str] = Field(None, max_length=100, description="适用场景")
    requires_plugin: bool = Field(False, description="是否需要插件")
    recommended_temperature: Optional[Decimal] = Field(0.70, description="推荐Temperature参数")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否激活")

class PromptTemplateCreate(PromptTemplateBase):
    """创建提示词模板Schema"""
    pass

class PromptTemplateUpdate(BaseModel):
    """更新提示词模板Schema"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = Field(None, max_length=20)
    suitable_for: Optional[str] = Field(None, max_length=100)
    requires_plugin: Optional[bool] = None
    recommended_temperature: Optional[Decimal] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class PromptTemplateResponse(PromptTemplateBase):
    """提示词模板响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PromptTemplateList(BaseModel):
    """提示词模板列表响应"""
    items: List[PromptTemplateResponse]
    total: int
    page: int = 1
    page_size: int = 50

