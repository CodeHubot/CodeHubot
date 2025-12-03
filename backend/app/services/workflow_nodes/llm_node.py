"""
LLM节点执行器
调用大模型生成文本
"""
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


async def execute_llm_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str],
    db_session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    执行LLM节点
    
    Args:
        node_data: 节点配置数据，包含：
            - agent_uuid: 智能体UUID
            - prompt: 提示词（支持变量替换）
            - temperature: 温度参数（可选）
            - max_tokens: 最大Token数（可选）
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        db_session: 数据库会话
        
    Returns:
        Dict[str, Any]: 节点输出，包含：
            - response: 生成的文本
            - usage: Token使用量（如果有）
    """
    if not db_session:
        raise ValueError("LLM节点执行需要数据库会话")
    
    # 获取节点配置
    agent_uuid = node_data.get("agent_uuid")
    prompt = node_data.get("prompt", "")
    temperature = node_data.get("temperature")
    max_tokens = node_data.get("max_tokens")
    
    if not agent_uuid:
        raise ValueError("LLM节点必须配置智能体UUID")
    
    # 查询智能体
    agent = db_session.query(Agent).filter(Agent.uuid == agent_uuid).first()
    if not agent:
        raise ValueError(f"智能体不存在: {agent_uuid}")
    
    # 查询大模型
    if not agent.llm_model_id:
        raise ValueError(f"智能体 {agent.name} 未配置大模型")
    
    llm_model = db_session.query(LLMModel).filter(LLMModel.id == agent.llm_model_id).first()
    if not llm_model:
        raise ValueError(f"大模型不存在: {agent.llm_model_id}")
    
    # 对提示词进行变量替换
    prompt = replace_variables(prompt)
    
    # 构建消息
    messages = []
    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # 创建LLM服务
    llm_service = LLMService(llm_model)
    
    # 设置超时时间（默认60秒）
    timeout = node_data.get("timeout", 60)
    
    try:
        # 调用LLM（使用asyncio.to_thread在异步环境中运行同步函数）
        result = await asyncio.wait_for(
            asyncio.to_thread(llm_service.chat, messages),
            timeout=timeout
        )
        
        output = {
            "response": result.get("response", ""),
            "usage": result.get("usage"),
            "function_call": result.get("function_call")
        }
        
        logger.info(f"LLM节点执行成功，生成文本长度: {len(output['response'])}")
        return output
        
    except asyncio.TimeoutError:
        raise TimeoutError(f"LLM节点执行超时（{timeout}秒）")
    except Exception as e:
        logger.error(f"LLM节点执行失败: {str(e)}", exc_info=True)
        raise

