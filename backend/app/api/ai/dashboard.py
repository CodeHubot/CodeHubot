"""
AI模块Dashboard统计API
提供智能体、工作流、知识库、插件等模块的统计数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response
from app.models.user import User
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.knowledge_base import KnowledgeBase
from app.models.plugin import Plugin
from app.models.prompt_template import PromptTemplate

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员（基于角色判断）"""
    return user.role in ['platform_admin', 'super_admin', 'admin']


@router.get("/stats")
async def get_ai_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取AI模块统计数据
    
    根据用户权限返回不同的统计数据：
    - 管理员：看到所有数据
    - 普通用户：只看到系统和自己创建的数据
    """
    
    is_admin = is_admin_user(current_user)
    
    # 智能体统计
    agent_query = db.query(Agent).filter(Agent.is_deleted == 0)
    if not is_admin:
        # 普通用户只能看到自己创建的智能体
        agent_query = agent_query.filter(Agent.user_id == current_user.id)
    total_agents = agent_query.count()
    
    # 工作流统计
    workflow_query = db.query(Workflow).filter(Workflow.is_deleted == 0)
    if not is_admin:
        # 普通用户只能看到自己创建的工作流
        workflow_query = workflow_query.filter(Workflow.user_id == current_user.id)
    total_workflows = workflow_query.count()
    
    # 知识库统计
    kb_query = db.query(KnowledgeBase).filter(KnowledgeBase.is_deleted == 0)
    if not is_admin:
        # 普通用户只能看到自己创建的知识库
        kb_query = kb_query.filter(KnowledgeBase.owner_id == current_user.id)
    total_knowledge_bases = kb_query.count()
    
    # 插件统计（所有用户都能看到所有插件）
    total_plugins = db.query(Plugin).filter(
        Plugin.is_deleted == 0,
        Plugin.is_active == 1
    ).count()
    
    # 提示词模板统计
    template_query = db.query(PromptTemplate).filter(PromptTemplate.is_deleted == 0)
    if not is_admin:
        # 普通用户只能看到系统模板和自己创建的模板
        template_query = template_query.filter(
            (PromptTemplate.is_system == True) | (PromptTemplate.user_id == current_user.id)
        )
    total_templates = template_query.count()
    
    return success_response(data={
        "agents": total_agents,
        "workflows": total_workflows,
        "knowledge_bases": total_knowledge_bases,
        "plugins": total_plugins,
        "templates": total_templates
    })

