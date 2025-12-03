"""
意图识别节点执行器
识别用户输入的意图
"""
import logging
import asyncio
from typing import Dict, Any, Callable, Optional, List
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


async def execute_intent_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str],
    db_session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    执行意图识别节点
    
    Args:
        node_data: 节点配置数据，包含：
            - input_text: 输入文本（支持变量替换）
            - intent_categories: 意图类别列表，如 ["查询天气", "播放音乐", "控制设备"]
            - recognition_mode: 识别方式（"llm" 或 "keyword"，默认"llm"）
            - agent_uuid: 智能体UUID（LLM识别时需要）
            - keyword_mapping: 关键词映射（关键词识别时需要），格式：{"意图类别": ["关键词1", "关键词2"]}
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        db_session: 数据库会话
        
    Returns:
        Dict[str, Any]: 节点输出，包含：
            - intent: 识别的意图类别
            - confidence: 置信度（0-1）
            - method: 识别方法（"llm" 或 "keyword"）
    """
    # 获取节点配置
    input_text = node_data.get("input_text", "")
    intent_categories = node_data.get("intent_categories", [])
    recognition_mode = node_data.get("recognition_mode", "llm")
    agent_uuid = node_data.get("agent_uuid")
    keyword_mapping = node_data.get("keyword_mapping", {})
    
    if not input_text:
        raise ValueError("意图识别节点必须配置输入文本")
    
    if not intent_categories:
        raise ValueError("意图识别节点必须配置意图类别列表")
    
    # 对输入文本进行变量替换
    input_text = replace_variables(input_text)
    
    # 根据识别方式选择方法
    if recognition_mode == "keyword":
        # 关键词匹配
        return await _recognize_by_keyword(input_text, intent_categories, keyword_mapping)
    elif recognition_mode == "llm":
        # LLM识别
        if not agent_uuid:
            raise ValueError("LLM识别方式需要配置智能体UUID")
        if not db_session:
            raise ValueError("LLM识别需要数据库会话")
        return await _recognize_by_llm(input_text, intent_categories, agent_uuid, db_session)
    else:
        raise ValueError(f"不支持的识别方式: {recognition_mode}")


async def _recognize_by_keyword(
    input_text: str,
    intent_categories: List[str],
    keyword_mapping: Dict[str, List[str]]
) -> Dict[str, Any]:
    """使用关键词匹配识别意图"""
    input_lower = input_text.lower()
    
    # 统计每个意图类别的匹配次数
    scores = {}
    for intent in intent_categories:
        keywords = keyword_mapping.get(intent, [])
        score = sum(1 for keyword in keywords if keyword.lower() in input_lower)
        if score > 0:
            scores[intent] = score
    
    if not scores:
        # 没有匹配到任何意图
        return {
            "intent": None,
            "confidence": 0.0,
            "method": "keyword"
        }
    
    # 选择得分最高的意图
    best_intent = max(scores.items(), key=lambda x: x[1])[0]
    max_score = scores[best_intent]
    total_score = sum(scores.values())
    confidence = min(max_score / total_score, 1.0) if total_score > 0 else 0.0
    
    return {
        "intent": best_intent,
        "confidence": confidence,
        "method": "keyword"
    }


async def _recognize_by_llm(
    input_text: str,
    intent_categories: List[str],
    agent_uuid: str,
    db_session: Session
) -> Dict[str, Any]:
    """使用LLM识别意图"""
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
    
    # 构建提示词
    categories_str = "、".join(intent_categories)
    prompt = f"""请识别以下用户输入的意图类别。

可选的意图类别：{categories_str}

用户输入：{input_text}

请只返回意图类别名称，不要返回其他内容。如果无法确定意图，请返回"未知"。
"""
    
    # 构建消息
    messages = []
    if agent.system_prompt:
        messages.append({"role": "system", "content": agent.system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # 创建LLM服务
    llm_service = LLMService(llm_model)
    
    try:
        # 调用LLM
        result = await asyncio.wait_for(
            asyncio.to_thread(llm_service.chat, messages),
            timeout=30
        )
        
        response = result.get("response", "").strip()
        
        # 检查响应是否匹配某个意图类别
        recognized_intent = None
        for intent in intent_categories:
            if intent in response:
                recognized_intent = intent
                break
        
        if not recognized_intent:
            recognized_intent = "未知"
        
        # LLM识别的置信度设为0.8（可以根据实际情况调整）
        confidence = 0.8 if recognized_intent != "未知" else 0.0
        
        return {
            "intent": recognized_intent,
            "confidence": confidence,
            "method": "llm",
            "raw_response": response
        }
        
    except Exception as e:
        logger.error(f"LLM意图识别失败: {str(e)}", exc_info=True)
        raise

