"""
工作流管理API接口
"""
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowExecutionCreate, WorkflowExecutionResponse, WorkflowExecutionListResponse,
    ValidationResult, WorkflowExecuteRequest, WorkflowExecuteResponse,
    WorkflowNode, WorkflowEdge
)
from app.api.auth import get_current_user
from app.models.user import User
from app.services.workflow_validator import WorkflowValidator
from app.services.workflow_executor import WorkflowExecutor
from app.utils.timezone import get_beijing_time_naive

logger = logging.getLogger(__name__)

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员（基于角色判断）"""
    return user.role in ['platform_admin', 'super_admin', 'team_admin', 'admin']


def can_access_workflow(workflow: Workflow, user: User) -> bool:
    """判断用户是否可以访问工作流"""
    if is_admin_user(user):
        return True
    # 普通用户：只能访问自己创建的或公开的工作流
    return workflow.user_id == user.id or workflow.is_public == 1


def can_edit_workflow(workflow: Workflow, user: User) -> bool:
    """判断用户是否可以编辑工作流"""
    if is_admin_user(user):
        return True
    # 普通用户：只能编辑自己创建的工作流
    return workflow.user_id == user.id


@router.get("/", response_model=WorkflowListResponse)
@router.get("", response_model=WorkflowListResponse)
def get_workflows(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    is_active: Optional[int] = Query(None, description="是否激活筛选（1=激活，0=禁用）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流列表"""
    query = db.query(Workflow).filter(Workflow.is_deleted == 0)
    
    # 权限过滤：普通用户只能看到自己创建的或公开的工作流
    if not is_admin_user(current_user):
        query = query.filter(
            or_(
                Workflow.user_id == current_user.id,
                Workflow.is_public == 1
            )
        )
    
    # 状态过滤
    if is_active is not None:
        query = query.filter(Workflow.is_active == is_active)
    
    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                Workflow.name.contains(search),
                Workflow.description.contains(search)
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页查询
    workflows = query.order_by(Workflow.created_at.desc()).offset(skip).limit(limit).all()
    
    # 转换为响应格式
    items = [WorkflowResponse.model_validate(wf) for wf in workflows]
    
    return WorkflowListResponse(total=total, items=items)


@router.post("/", response_model=WorkflowResponse)
@router.post("", response_model=WorkflowResponse)
def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作流"""
    # 验证工作流结构
    validator = WorkflowValidator()
    validation_result = validator.validate(workflow.nodes, workflow.edges)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流验证失败: {', '.join(validation_result.errors)}"
        )
    
    # 创建工作流
    workflow_data = workflow.model_dump()
    workflow_data['user_id'] = current_user.id
    
    db_workflow = Workflow(**workflow_data)
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    return WorkflowResponse.model_validate(db_workflow)


@router.get("/{workflow_uuid}", response_model=WorkflowResponse)
def get_workflow(
    workflow_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情"""
    workflow = db.query(Workflow).filter(
        Workflow.uuid == workflow_uuid,
        Workflow.is_deleted == 0
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 权限检查
    if not can_access_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作流"
        )
    
    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_uuid}", response_model=WorkflowResponse)
def update_workflow(
    workflow_uuid: str,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流"""
    workflow = db.query(Workflow).filter(
        Workflow.uuid == workflow_uuid,
        Workflow.is_deleted == 0
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 权限检查
    if not can_edit_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑该工作流"
        )
    
    # 如果更新了节点或边，需要重新验证
    update_data = workflow_update.model_dump(exclude_unset=True)
    if 'nodes' in update_data or 'edges' in update_data:
        # 将字典转换为WorkflowNode和WorkflowEdge对象
        nodes_data = update_data.get('nodes', workflow.nodes)
        edges_data = update_data.get('edges', workflow.edges)
        
        # 如果nodes是字典列表，转换为WorkflowNode对象
        if nodes_data and isinstance(nodes_data[0], dict):
            nodes = [WorkflowNode(**node) for node in nodes_data]
        else:
            nodes = nodes_data
        
        # 如果edges是字典列表，转换为WorkflowEdge对象
        if edges_data and isinstance(edges_data[0], dict):
            edges = [WorkflowEdge(**edge) for edge in edges_data]
        else:
            edges = edges_data
        
        validator = WorkflowValidator()
        validation_result = validator.validate(nodes, edges)
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工作流验证失败: {', '.join(validation_result.errors)}"
            )
    
    # 更新工作流
    for key, value in update_data.items():
        setattr(workflow, key, value)
    
    db.commit()
    db.refresh(workflow)
    
    return WorkflowResponse.model_validate(workflow)


@router.delete("/{workflow_uuid}")
def delete_workflow(
    workflow_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流（软删除）"""
    workflow = db.query(Workflow).filter(
        Workflow.uuid == workflow_uuid,
        Workflow.is_deleted == 0
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 权限检查
    if not can_edit_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该工作流"
        )
    
    # 软删除：标记为已删除
    workflow.is_deleted = 1
    db.commit()
    
    return success_response(message="工作流删除成功")


@router.post("/{workflow_uuid}/validate", response_model=ValidationResult)
def validate_workflow(
    workflow_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证工作流（DAG验证）"""
    workflow = db.query(Workflow).filter(
        Workflow.uuid == workflow_uuid,
        Workflow.is_deleted == 0
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 权限检查
    if not can_access_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作流"
        )
    
    # 执行验证（将JSON数据转换为WorkflowNode和WorkflowEdge对象）
    nodes = [WorkflowNode(**node) if isinstance(node, dict) else node for node in workflow.nodes]
    edges = [WorkflowEdge(**edge) if isinstance(edge, dict) else edge for edge in workflow.edges]
    
    validator = WorkflowValidator()
    validation_result = validator.validate(nodes, edges)
    
    return validation_result


@router.post("/{workflow_uuid}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(
    workflow_uuid: str,
    execute_request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流（同步执行，后续可改为异步）"""
    workflow = db.query(Workflow).filter(
        Workflow.uuid == workflow_uuid,
        Workflow.is_deleted == 0
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在"
        )
    
    # 权限检查
    if not can_access_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行该工作流"
        )
    
    # 验证工作流（将JSON数据转换为WorkflowNode和WorkflowEdge对象）
    nodes = [WorkflowNode(**node) if isinstance(node, dict) else node for node in workflow.nodes]
    edges = [WorkflowEdge(**edge) if isinstance(edge, dict) else edge for edge in workflow.edges]
    
    validator = WorkflowValidator()
    validation_result = validator.validate(nodes, edges)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流验证失败: {', '.join(validation_result.errors)}"
        )
    
    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status="running",
        input=execute_request.input,
        started_at=get_beijing_time_naive()
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    try:
        # 执行工作流
        executor = WorkflowExecutor()
        result = await executor.execute(
            nodes=nodes,
            edges=edges,
            input_data=execute_request.input,
            config=workflow.config,
            db_session=db
        )
        
        # 更新执行记录
        execution.status = "completed"
        execution.output = result.get("output")
        execution.node_executions = result.get("node_executions")
        execution.completed_at = get_beijing_time_naive()
        execution.execution_time = result.get("execution_time")
        
        # 更新工作流统计
        workflow.execution_count += 1
        workflow.success_count += 1
        
        db.commit()
        
        return WorkflowExecuteResponse(
            execution_id=execution.execution_id,
            status="completed",
            message="工作流执行成功",
            output=execution.output,
            node_executions=execution.node_executions,
            execution_time=execution.execution_time
        )
        
    except Exception as e:
        # 更新执行记录为失败
        execution.status = "failed"
        execution.error_message = str(e)
        execution.completed_at = get_beijing_time_naive()
        
        # 更新工作流统计
        workflow.execution_count += 1
        
        db.commit()
        
        logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"工作流执行失败: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行记录详情"""
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 权限检查：只能查看自己工作流的执行记录
    workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
    if workflow and not can_access_workflow(workflow, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该执行记录"
        )
    
    return WorkflowExecutionResponse.model_validate(execution)


@router.get("/executions", response_model=WorkflowExecutionListResponse)
def get_executions(
    workflow_uuid: Optional[str] = Query(None, description="工作流UUID"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行记录列表"""
    query = db.query(WorkflowExecution)
    
    # 工作流过滤
    if workflow_uuid:
        workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
        if workflow:
            # 权限检查
            if not can_access_workflow(workflow, current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问该工作流的执行记录"
                )
            query = query.filter(WorkflowExecution.workflow_id == workflow.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
    else:
        # 如果没有指定工作流，只返回当前用户可访问的工作流的执行记录
        if not is_admin_user(current_user):
            # 获取用户可访问的工作流ID列表
            accessible_workflows = db.query(Workflow.id).filter(
                or_(
                    Workflow.user_id == current_user.id,
                    Workflow.is_public == 1
                )
            ).all()
            workflow_ids = [wf[0] for wf in accessible_workflows]
            query = query.filter(WorkflowExecution.workflow_id.in_(workflow_ids))
    
    # 状态过滤
    if status_filter:
        query = query.filter(WorkflowExecution.status == status_filter)
    
    # 总数
    total = query.count()
    
    # 分页查询
    executions = query.order_by(WorkflowExecution.created_at.desc()).offset(skip).limit(limit).all()
    
    # 转换为响应格式
    items = [WorkflowExecutionResponse.model_validate(exec) for exec in executions]
    
    return WorkflowExecutionListResponse(total=total, items=items)

