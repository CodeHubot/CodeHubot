"""
智能体相关的Pydantic模式定义
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AgentBase(BaseModel):
    """智能体基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    plugin_ids: Optional[List[int]] = Field(default_factory=list, description="关联的插件 ID 列表")


class AgentCreate(AgentBase):
    """创建智能体的模式"""
    pass


class AgentUpdate(BaseModel):
    """更新智能体的模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    plugin_ids: Optional[List[int]] = Field(None, description="关联的插件 ID 列表")
    llm_model_id: Optional[int] = Field(None, description="关联的大模型ID")
    is_active: Optional[int] = Field(None, description="是否激活（1=激活，0=禁用）")


class AgentResponse(AgentBase):
    """智能体响应模式"""
    id: int
    uuid: str = Field(..., description="唯一标识UUID")
    user_id: int
    is_active: int
    is_system: int
    llm_model_id: Optional[int] = Field(None, description="关联的大模型ID")
    created_at: datetime
    updated_at: datetime
    
    # 所有者信息
    owner_nickname: Optional[str] = Field(None, description="所有者昵称")
    owner_username: Optional[str] = Field(None, description="所有者用户名")
    
    class Config:
        from_attributes = True


class AgentList(BaseModel):
    """智能体列表响应模式"""
    total: int
    items: List[AgentResponse]

