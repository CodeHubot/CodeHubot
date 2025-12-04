"""
工作流相关的Pydantic模式定义
用于API请求和响应的数据验证
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============================================================================
# 工作流节点和边 Schemas
# ============================================================================

class WorkflowNode(BaseModel):
    """工作流节点Schema"""
    id: str = Field(..., description="节点ID（唯一标识）")
    type: str = Field(..., description="节点类型（start/llm/http/knowledge/intent/string/end）")
    label: str = Field(..., description="节点标签（显示名称）")
    position: Dict[str, float] = Field(..., description="节点位置（x, y坐标）")
    data: Dict[str, Any] = Field(default_factory=dict, description="节点数据（配置信息）")
    
    @validator('type')
    def validate_node_type(cls, v):
        valid_types = ['start', 'llm', 'http', 'knowledge', 'intent', 'string', 'end']
        if v not in valid_types:
            raise ValueError(f'节点类型必须是{valid_types}之一')
        return v


class WorkflowEdge(BaseModel):
    """工作流边Schema"""
    id: str = Field(..., description="边ID（唯一标识）")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    sourceHandle: Optional[str] = Field(None, description="源节点句柄")
    targetHandle: Optional[str] = Field(None, description="目标节点句柄")
    label: Optional[str] = Field(None, description="边标签（可选）")


# ============================================================================
# 工作流 Schemas
# ============================================================================

class WorkflowBase(BaseModel):
    """工作流基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    nodes: List[WorkflowNode] = Field(..., min_items=2, description="节点列表（至少包含开始和结束节点）")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="边列表")
    config: Optional[Dict[str, Any]] = Field(None, description="工作流配置（超时、重试等）")


class WorkflowCreate(WorkflowBase):
    """创建工作流的模式"""
    pass


class WorkflowUpdate(BaseModel):
    """更新工作流的模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    nodes: Optional[List[WorkflowNode]] = Field(None, description="节点列表")
    edges: Optional[List[WorkflowEdge]] = Field(None, description="边列表")
    config: Optional[Dict[str, Any]] = Field(None, description="工作流配置")
    is_active: Optional[int] = Field(None, description="是否激活（1=激活，0=禁用）")
    is_public: Optional[int] = Field(None, description="是否公开（1=公开，0=私有）")


class WorkflowResponse(WorkflowBase):
    """工作流响应模式"""
    id: int
    uuid: str = Field(..., description="唯一标识UUID")
    user_id: int
    is_active: int
    is_public: int
    execution_count: int = 0
    success_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """工作流列表响应模式"""
    total: int
    items: List[WorkflowResponse]


# ============================================================================
# 工作流执行 Schemas
# ============================================================================

class WorkflowExecutionCreate(BaseModel):
    """创建工作流执行记录的模式"""
    input: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工作流输入参数")


class NodeExecutionResult(BaseModel):
    """节点执行结果Schema"""
    node_id: str = Field(..., description="节点ID")
    node_type: str = Field(..., description="节点类型")
    status: str = Field(..., description="执行状态（success/failed/skipped）")
    output: Optional[Dict[str, Any]] = Field(None, description="节点输出")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[int] = Field(None, description="执行时间（毫秒）")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行记录响应模式"""
    id: int
    execution_id: str = Field(..., description="执行唯一标识UUID")
    workflow_id: int
    status: str = Field(..., description="执行状态（pending/running/completed/failed）")
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    node_executions: Optional[List[NodeExecutionResult]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行记录列表响应模式"""
    total: int
    items: List[WorkflowExecutionResponse]


# ============================================================================
# 工作流验证 Schemas
# ============================================================================

class ValidationResult(BaseModel):
    """工作流验证结果Schema"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")


# ============================================================================
# 工作流执行请求 Schemas
# ============================================================================

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求Schema"""
    input: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工作流输入参数")
    async_execution: bool = Field(True, description="是否异步执行（默认True）")


class WorkflowExecuteResponse(BaseModel):
    """执行工作流响应Schema"""
    execution_id: str = Field(..., description="执行唯一标识UUID")
    task_id: Optional[str] = Field(None, description="Celery任务ID（异步执行时）")
    status: str = Field(..., description="执行状态（pending/running）")
    message: str = Field(..., description="响应消息")
    output: Optional[Dict[str, Any]] = Field(None, description="执行输出")
    node_executions: Optional[List[NodeExecutionResult]] = Field(None, description="节点执行详情")
    execution_time: Optional[int] = Field(None, description="执行耗时(ms)")
    error_message: Optional[str] = Field(None, description="错误信息")

