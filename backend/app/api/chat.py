"""
智能体对话 API 接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.agent import Agent
from app.models.plugin import Plugin
from app.models.llm_model import LLMModel
from app.models.device import Device
from app.api.auth import get_current_user
from app.models.user import User
from app.services.llm_service import create_llm_service
from app.services.plugin_service import PluginService

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: user, assistant, system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    agent_uuid: str = Field(..., description="智能体UUID")
    message: str = Field(..., description="用户消息")
    history: List[ChatMessage] = Field(default=[], description="历史消息")


class FunctionCall(BaseModel):
    name: str = Field(..., description="函数名称")
    arguments: Dict[str, Any] = Field(..., description="函数参数")


class PluginCallInfo(BaseModel):
    """插件调用信息"""
    plugin_name: str = Field(..., description="插件名称")
    function_name: str = Field(..., description="函数名称")
    arguments: Dict[str, Any] = Field(..., description="调用参数")
    result: str = Field(..., description="调用结果")


class KnowledgeSourceInfo(BaseModel):
    """知识库检索来源信息"""
    knowledge_base_name: str = Field(..., description="知识库名称")
    document_title: str = Field(..., description="文档标题")
    chunk_content: str = Field(..., description="文本块内容")
    similarity: float = Field(..., description="相似度")
    chunk_index: int = Field(..., description="文本块序号")


class TokenUsage(BaseModel):
    """Token使用量"""
    prompt_tokens: int = Field(..., description="输入Token数")
    completion_tokens: int = Field(..., description="输出Token数")
    total_tokens: int = Field(..., description="总Token数")


class ChatResponse(BaseModel):
    response: str = Field(..., description="智能体回复")
    function_call: Optional[FunctionCall] = None
    token_usage: Optional[TokenUsage] = Field(None, description="Token使用量")
    plugin_calls: Optional[List[PluginCallInfo]] = Field(default=[], description="插件调用信息")
    knowledge_sources: Optional[List[KnowledgeSourceInfo]] = Field(default=[], description="知识库检索来源")


class ChatDeviceResponse(BaseModel):
    """聊天页面设备响应模型（轻量级）"""
    uuid: str = Field(..., description="设备UUID")
    name: str = Field(..., description="设备名称")
    device_id: Optional[str] = Field(None, description="设备ID")
    is_online: bool = Field(..., description="是否在线")
    is_active: bool = Field(..., description="是否激活")
    
    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与智能体对话
    
    流程：
    1. 获取智能体配置（提示词、插件、模型）
    2. 解析插件为 Function Calling 格式
    3. 构建完整消息（系统提示词 + 历史消息 + 用户消息）
    4. 调用大模型获取回复
    5. 如果模型返回函数调用，执行函数并再次调用模型
    6. 返回最终回复
    """
    
    # 1. 获取智能体
    agent = db.query(Agent).filter(Agent.uuid == request.agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    # 权限检查：普通用户只能使用自己的智能体，管理员可以使用所有智能体
    from app.api.agents import is_admin_user
    if not is_admin_user(current_user) and agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权使用此智能体")
    
    # 2. 获取智能体关联的插件
    plugins = []
    if agent.plugin_ids:
        try:
            plugin_ids = agent.plugin_ids if isinstance(agent.plugin_ids, list) else eval(agent.plugin_ids)
            plugins = db.query(Plugin).filter(
                Plugin.id.in_(plugin_ids),
                Plugin.is_active == 1
            ).all()
        except Exception as e:
            print(f"解析插件 ID 失败: {e}")
    
    # 3. 获取智能体关联的大模型
    llm_model = None
    if agent.llm_model_id:
        llm_model = db.query(LLMModel).filter(
            LLMModel.id == agent.llm_model_id,
            LLMModel.is_active == 1
        ).first()
    
    # 如果没有配置模型，使用默认模型
    if not llm_model:
        llm_model = db.query(LLMModel).filter(
            LLMModel.is_default == 1,
            LLMModel.is_active == 1
        ).first()
    
    if not llm_model:
        raise HTTPException(status_code=400, detail="未配置可用的大模型")
    
    # 4. 解析插件为 Function Calling 格式
    plugin_service = PluginService()
    functions = plugin_service.parse_openapi_to_functions(plugins)
    
    # 5. 检索知识库（如果智能体关联了知识库）
    knowledge_sources = []
    knowledge_context = ""
    
    try:
        from app.models.knowledge_base import KnowledgeBase, AgentKnowledgeBase
        from app.models.document import Document, DocumentChunk
        from app.services.embedding_service import get_embedding_service
        import numpy as np
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 查询智能体关联的知识库
        kb_associations = db.query(AgentKnowledgeBase).filter(
            AgentKnowledgeBase.agent_id == agent.id,
            AgentKnowledgeBase.is_enabled == 1
        ).order_by(AgentKnowledgeBase.priority.desc()).all()
        
        if kb_associations:
            logger.info(f"[知识库检索] 智能体 {agent.name} 关联了 {len(kb_associations)} 个知识库")
            
            # 对用户消息进行向量化
            embedding_service = get_embedding_service()
            query_vector = await embedding_service.embed_text(request.message)
            
            if query_vector:
                logger.info(f"[知识库检索] 用户消息向量化成功")
                
                # 在每个关联的知识库中检索
                all_results = []
                for assoc in kb_associations:
                    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == assoc.knowledge_base_id).first()
                    if not kb:
                        continue
                    
                    logger.info(f"[知识库检索] 在知识库 '{kb.name}' 中检索...")
                    
                    # 获取该知识库的所有已向量化文本块
                    chunks = db.query(DocumentChunk).filter(
                        DocumentChunk.knowledge_base_id == kb.id,
                        DocumentChunk.embedding_vector.isnot(None)
                    ).all()
                    
                    logger.info(f"[知识库检索] 找到 {len(chunks)} 个已向量化文本块")
                    
                    # 收集所有相似度用于调试
                    similarities = []
                    threshold = float(assoc.similarity_threshold) if assoc.similarity_threshold else 0.7
                    
                    for chunk in chunks:
                        if chunk.embedding_vector:
                            # 使用embedding_service的calculate_similarity方法（已归一化到0-1）
                            # 与测试界面保持一致
                            similarity = embedding_service.calculate_similarity(
                                query_vector,
                                chunk.embedding_vector
                            )
                            similarities.append(similarity)
                            
                            # 只保留相似度高于阈值的结果
                            if similarity >= threshold:
                                doc = db.query(Document).filter(Document.id == chunk.document_id).first()
                                if doc:
                                    all_results.append({
                                        'kb_name': kb.name,
                                        'doc_title': doc.title,
                                        'chunk_content': chunk.content,
                                        'similarity': similarity,
                                        'chunk_index': chunk.chunk_index
                                    })
                    
                    # 输出相似度统计信息
                    if similarities:
                        max_sim = max(similarities)
                        min_sim = min(similarities)
                        avg_sim = sum(similarities) / len(similarities)
                        above_threshold = sum(1 for s in similarities if s >= threshold)
                        logger.info(f"[知识库检索] 相似度统计 - 最高:{max_sim:.4f}, 最低:{min_sim:.4f}, 平均:{avg_sim:.4f}, 阈值:{threshold}, 超过阈值:{above_threshold}个")
                        # 输出前5个最高相似度
                        top5 = sorted(similarities, reverse=True)[:5]
                        logger.info(f"[知识库检索] Top5相似度: {[f'{s:.4f}' for s in top5]}")
                
                # 排序并取top_k
                all_results.sort(key=lambda x: x['similarity'], reverse=True)
                max_results = max([assoc.top_k for assoc in kb_associations]) if kb_associations else 5
                top_results = all_results[:max_results]
                
                logger.info(f"[知识库检索] 共找到 {len(all_results)} 个相关结果，取前 {len(top_results)} 个")
                
                # 构建知识库上下文
                if top_results:
                    knowledge_parts = ["\n\n[参考知识库内容]"]
                    for idx, result in enumerate(top_results, 1):
                        knowledge_parts.append(
                            f"\n{idx}. 来自《{result['doc_title']}》(相似度:{result['similarity']:.0%}):\n{result['chunk_content']}"
                        )
                        knowledge_sources.append(KnowledgeSourceInfo(
                            knowledge_base_name=result['kb_name'],
                            document_title=result['doc_title'],
                            chunk_content=result['chunk_content'][:200] + "..." if len(result['chunk_content']) > 200 else result['chunk_content'],
                            similarity=round(result['similarity'], 4),
                            chunk_index=result['chunk_index']
                        ))
                    knowledge_context = "\n".join(knowledge_parts)
                    logger.info(f"[知识库检索] 构建知识库上下文成功，共{len(knowledge_sources)}条")
            else:
                logger.warning("[知识库检索] 用户消息向量化失败")
    except Exception as e:
        import traceback
        logger.error(f"[知识库检索] 检索失败: {str(e)}")
        logger.error(traceback.format_exc())
        # 检索失败不影响对话，继续执行
    
    # 6. 构建消息列表
    messages = []
    
    # 添加系统提示词
    system_content = agent.system_prompt if agent.system_prompt else "你是一个智能助手。"
    
    # 如果有知识库检索结果，添加到系统提示词中
    if knowledge_context:
        system_content += knowledge_context
        system_content += "\n\n请基于以上参考内容回答用户问题。如果参考内容中没有相关信息，可以使用你的知识进行回答，但请说明这不是来自参考资料。"
    
        messages.append({
            "role": "system",
        "content": system_content
        })
    
    # 添加插件能力说明
    if functions:
        function_descriptions = []
        for func in functions:
            func_desc = f"- {func['name']}: {func['description']}"
            function_descriptions.append(func_desc)
        
        plugin_prompt = (
            "\n\n你可以调用以下工具来帮助用户：\n" +
            "\n".join(function_descriptions) +
            "\n\n当需要使用工具时，请明确说明要调用哪个工具。"
        )
        
        if messages:
            messages[0]["content"] += plugin_prompt
        else:
            messages.append({
                "role": "system",
                "content": "你是一个智能助手。" + plugin_prompt
            })
    
    # 添加历史消息
    for msg in request.history:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": request.message
    })
    
    # 6. 调用大模型
    llm_service = create_llm_service(llm_model)
    
    # 用于收集插件调用信息
    plugin_calls_info = []
    # 用于累计 token 使用量
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    
    try:
        # 首次调用
        result = llm_service.chat(
            messages=messages,
            functions=functions if functions else None,
            function_call="auto" if functions else None
        )
        
        # 累计第一次调用的 token
        if "usage" in result:
            usage = result["usage"]
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)
        
        # 7. 处理函数调用
        if "function_call" in result:
            function_call = result["function_call"]
            function_name = function_call["name"]
            function_args = function_call["arguments"]
            
            # 查找插件名称
            plugin_name = "未知插件"
            for func in functions:
                if func.get("name") == function_name:
                    plugin_name = func.get("metadata", {}).get("plugin_name", "未知插件")
                    break
            
            # 执行函数
            function_result = plugin_service.call_function(
                function_name=function_name,
                arguments=function_args,
                functions=functions
            )
            
            # 记录插件调用信息
            plugin_calls_info.append(PluginCallInfo(
                plugin_name=plugin_name,
                function_name=function_name,
                arguments=function_args,
                result=plugin_service.format_function_result(function_result)
            ))
            
            # 将函数调用结果添加到消息历史
            # 注意：arguments 必须是 JSON 字符串，不能是对象
            import json
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": json.dumps(function_args, ensure_ascii=False) if isinstance(function_args, dict) else function_args
                }
            })
            
            messages.append({
                "role": "function",
                "name": function_name,
                "content": plugin_service.format_function_result(function_result)
            })
            
            # 再次调用模型，让它基于函数结果生成回复
            result = llm_service.chat(messages=messages)
            
            # 累计第二次调用的 token
            if "usage" in result:
                usage = result["usage"]
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)
                total_tokens += usage.get("total_tokens", 0)
        
        # 8. 返回回复
        token_usage = None
        if total_tokens > 0:
            token_usage = TokenUsage(
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=total_tokens
            )
        
        response = ChatResponse(
            response=result.get("response", "抱歉，我现在无法回答这个问题。"),
            function_call=result.get("function_call"),
            token_usage=token_usage,
            plugin_calls=plugin_calls_info if plugin_calls_info else [],
            knowledge_sources=knowledge_sources if knowledge_sources else []
        )
        
        return response
    
    except Exception as e:
        print(f"调用大模型失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"调用大模型失败: {str(e)}"
        )


@router.get("/my-devices", response_model=List[ChatDeviceResponse])
async def get_my_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的设备列表（轻量级，专用于聊天页面）
    
    只返回必要的字段：uuid、name、device_id、is_online、is_active
    用于聊天页面的设备选择下拉框
    """
    try:
        # 直接从数据库查询用户的设备
        devices = db.query(Device).filter(
            Device.user_id == current_user.id,
            Device.is_active == True
        ).order_by(
            Device.is_online.desc(),  # 在线设备优先
            Device.name.asc()          # 按名称排序
        ).all()
        
        return devices
    except Exception as e:
        print(f"获取设备列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取设备列表失败: {str(e)}"
        )

