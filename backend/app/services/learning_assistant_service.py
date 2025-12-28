"""
AI学习助手核心服务
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid as uuid_lib
import hashlib
import logging

from app.models.learning_assistant import (
    LearningAssistantConversation,
    LearningAssistantMessage,
    StudentLearningProfile,
    ContentModerationLog
)
from app.models.pbl import PBLCourse, PBLUnit
from app.services.content_moderation_service import ContentModerationService

logger = logging.getLogger(__name__)


class LearningAssistantService:
    """学习助手核心服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.moderator = ContentModerationService(db)
    
    async def chat(
        self,
        user_id: int,
        message: str,
        context: Dict,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        核心对话方法
        
        Args:
            user_id: 用户ID
            message: 用户消息
            context: 学习上下文
            conversation_id: 会话UUID（可选）
        
        Returns:
            AI回复及相关信息
        """
        
        # 1. 内容安全审核（用户输入）
        moderation_result = await self.moderator.check(
            content=message,
            content_type='user_message'
        )
        
        if moderation_result['status'] == 'blocked':
            # ✅ 即便拦截了，也要保存这条违规消息，以便管理员后续审计
            try:
                # 3.1 获取或创建会话
                conversation = await self._get_or_create_conversation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    context=context
                )
                # 3.2 保存违规消息
                user_message = await self._save_message(
                    conversation_id=conversation.id,
                    role='user',
                    content=message,
                    context_snapshot=context,
                    moderation_result=moderation_result
                )
                # 3.3 记录审计日志
                await self._log_moderation(
                    user_id=user_id,
                    conversation_id=conversation.id,
                    message_id=user_message.id,
                    content_type='user_message',
                    content=message,
                    result=moderation_result
                )
            except Exception as e:
                logger.error(f"保存违规消息失败: {str(e)}")

            return {
                'response': '抱歉，你的消息包含不适当的内容，已被系统拦截。请遵守学习规范。',
                'blocked': True,
                'reason': moderation_result.get('reason'),
                'conversation_id': conversation_id # 尽可能返回ID
            }
        
        # 2. 获取或创建会话
        conversation = await self._get_or_create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            context=context
        )
        
        # 3. 保存用户消息
        user_message = await self._save_message(
            conversation_id=conversation.id,
            role='user',
            content=message,
            context_snapshot=context,
            moderation_result=moderation_result
        )
        
        # 4. 记录审核日志（如果有警告或拦截）
        if moderation_result['status'] in ['warning', 'blocked']:
            await self._log_moderation(
                user_id=user_id,
                conversation_id=conversation.id,
                message_id=user_message.id,
                content_type='user_message',
                content=message,
                result=moderation_result
            )
        
        # 5. 构建完整上下文
        full_context = await self._build_full_context(
            user_id=user_id,
            conversation=conversation,
            current_context=context
        )
        
        # 6. 调用LLM生成回复
        start_time = datetime.now()
        llm_response = await self._call_llm(
            message=message,
            context=full_context,
            conversation_history=await self._get_recent_messages(conversation.id, limit=10)
        )
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # 7. 内容安全审核（AI回复）
        ai_moderation = await self.moderator.check(
            content=llm_response['content'],
            content_type='ai_response'
        )
        
        if ai_moderation['status'] == 'blocked':
            llm_response['content'] = '抱歉，我无法回答这个问题。建议你向老师请教。'
        
        # 8. 保存AI回复
        ai_message = await self._save_message(
            conversation_id=conversation.id,
            role='assistant',
            content=llm_response['content'],
            knowledge_sources=llm_response.get('knowledge_sources'),
            token_usage=llm_response.get('token_usage'),
            model_used=llm_response.get('model'),
            response_time_ms=response_time,
            moderation_result=ai_moderation
        )
        
        # 9. 更新会话统计
        await self._update_conversation_stats(conversation.id)
        
        # 10. 刷新conversation对象以获取最新的message_count
        self.db.refresh(conversation)
        
        # 11. 如果是首次对话，生成智能标题
        suggested_title = None
        if conversation.message_count == 2:  # 2条消息 = 用户首次提问 + AI首次回复
            try:
                suggested_title = await self._generate_conversation_title(
                    user_message=message,
                    ai_response=llm_response['content']
                )
                if suggested_title:
                    conversation.title = suggested_title
                    self.db.commit()
                    logger.info(f"✅ 自动生成会话标题: {suggested_title}")
                else:
                    logger.warning(f"⚠️ 标题生成返回为空")
            except Exception as e:
                logger.error(f"❌ 生成会话标题失败: {str(e)}", exc_info=True)
        
        # 11. 异步更新学生档案
        try:
            await self._update_student_profile(user_id, message, context)
        except Exception as e:
            logger.error(f"更新学生档案失败: {str(e)}")
        
        return {
            'response': llm_response['content'],
            'conversation_id': conversation.uuid,
            'message_id': ai_message.uuid,
            'suggested_title': suggested_title,  # 返回建议的标题
            'knowledge_sources': llm_response.get('knowledge_sources'),
            'token_usage': llm_response.get('token_usage'),
            'blocked': False
        }
    
    async def _get_or_create_conversation(
        self,
        user_id: int,
        conversation_id: Optional[str],
        context: Dict
    ) -> LearningAssistantConversation:
        """获取或创建会话"""
        
        if conversation_id:
            # 查找已存在的活跃会话
            conversation = self.db.query(LearningAssistantConversation).filter(
                LearningAssistantConversation.uuid == conversation_id,
                LearningAssistantConversation.user_id == user_id,
                LearningAssistantConversation.is_active == 1
            ).first()
            
            if conversation:
                return conversation
        
        # 创建新会话
        course_uuid = context.get('course_uuid')
        course_name = context.get('course_name')
        unit_uuid = context.get('unit_uuid')
        unit_name = context.get('unit_name')
        
        # 尝试从数据库获取课程和单元名称（如果前端没传）
        if course_uuid and not course_name:
            course = self.db.query(PBLCourse).filter(PBLCourse.uuid == course_uuid).first()
            if course:
                course_name = course.title
                
        if unit_uuid and not unit_name:
            unit = self.db.query(PBLUnit).filter(PBLUnit.uuid == unit_uuid).first()
            if unit:
                unit_name = unit.title

        conversation = LearningAssistantConversation(
            uuid=str(uuid_lib.uuid4()),
            user_id=user_id,
            title='新的对话',
            course_uuid=course_uuid,
            course_name=course_name,
            unit_uuid=unit_uuid,
            unit_name=unit_name,
            source='course_learning' if course_uuid else 'manual'
        )
        
        # 处理当前资源信息
        if context.get('current_resource'):
            resource = context['current_resource']
            conversation.current_resource_id = resource.get('uuid')
            conversation.current_resource_type = resource.get('type')
            conversation.current_resource_title = resource.get('title')
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation

    def clear_all_conversations(self, user_id: int) -> int:
        """清空所有会话（软删除）"""
        # 更新该用户的所有活跃会话为非活跃
        result = self.db.query(LearningAssistantConversation).filter(
            LearningAssistantConversation.user_id == user_id,
            LearningAssistantConversation.is_active == 1
        ).update({LearningAssistantConversation.is_active: 0}, synchronize_session=False)
        
        self.db.commit()
        return result
    
    async def _save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        context_snapshot: Dict = None,
        knowledge_sources: List = None,
        token_usage: Dict = None,
        model_used: str = None,
        response_time_ms: int = None,
        moderation_result: Dict = None
    ) -> LearningAssistantMessage:
        """保存消息"""
        
        # 计算内容哈希
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 提取审核结果
        was_blocked = 0
        if moderation_result and moderation_result.get('status') == 'blocked':
            was_blocked = 1
            
        message = LearningAssistantMessage(
            uuid=str(uuid_lib.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            content_hash=content_hash,
            context_snapshot=context_snapshot,
            knowledge_sources=knowledge_sources,
            token_usage=token_usage,
            model_used=model_used,
            response_time_ms=response_time_ms,
            moderation_result=moderation_result,
            was_blocked=was_blocked  # ✅ 显式设置拦截状态
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    async def _build_full_context(
        self,
        user_id: int,
        conversation: LearningAssistantConversation,
        current_context: Dict
    ) -> str:
        """构建完整的个性化上下文（严格约束版）"""
        
        # 1. 优先获取数据库中定义的严格系统提示词
        from app.models.agent import Agent
        system_agent = self.db.query(Agent).filter(
            Agent.uuid == 'system-learning-assistant'
        ).first()
        
        # 如果数据库有值，直接用数据库的；否则用代码里的强力兜底
        base_prompt = system_agent.system_prompt if (system_agent and system_agent.system_prompt) else self._get_base_system_prompt()
        
        # 2. 获取学生档案
        profile = await self._get_student_profile(user_id)
        
        # 3. 构建上下文字符串
        context_parts = [
            base_prompt,
            "\n[学生学习状态]"
        ]
        
        if profile:
            context_parts.append(f"总提问数: {profile.total_questions}")
            if profile.weak_points:
                context_parts.append(f"薄弱知识点: {', '.join(profile.weak_points[:5])}")
        
        context_parts.append("\n[当前学习场景]")
        context_parts.append(self._format_current_context(current_context))
        
        return "\n".join(context_parts)
    
    def _get_base_system_prompt(self) -> str:
        """获取强力兜底提示词"""
        return """你是一个专门为【人工智能课程】设计的专业AI学习助手。
【核心禁令】
1. 禁止进行任何形式的情感共情、心理安慰或生活闲聊。
2. 对于任何非AI学习的话题，必须礼貌但冷漠地拒绝，并要求学生提问AI知识点。
3. 只能回答：人工智能、机器学习、Python编程（AI方向）、机器人及本课程知识内容。
4. 回复风格：专业、学术、简洁。禁止回复“我理解你”、“不要气馁”等废话。"""
    
    def _format_current_context(self, context: Dict) -> str:
        """格式化当前学习上下文"""
        parts = []
        
        if context.get('course_name'):
            parts.append(f"课程：{context['course_name']}")
        
        if context.get('unit_name'):
            parts.append(f"单元：{context['unit_name']}")
        
        if context.get('current_resource'):
            resource = context['current_resource']
            parts.append(
                f"当前正在学习：{resource.get('type')} - {resource.get('title')}"
            )
        
        return "\n".join(parts) if parts else "通用学习场景"
    
    async def _call_llm(
        self,
        message: str,
        context: str,
        conversation_history: List[LearningAssistantMessage]
    ) -> Dict:
        """
        调用LLM生成回复
        """
        from app.models.llm_model import LLMModel
        from app.services.llm_service import create_llm_service
        
        # 1. 获取系统学习助手的LLM模型配置
        from app.models.agent import Agent
        
        system_agent = self.db.query(Agent).filter(
            Agent.uuid == 'system-learning-assistant'
        ).first()
        
        # 2. 获取LLM模型（优先使用智能体配置的，否则使用默认模型）
        llm_model = None
        if system_agent and system_agent.llm_model_id:
            llm_model = self.db.query(LLMModel).filter(
                LLMModel.id == system_agent.llm_model_id,
                LLMModel.is_active == 1
            ).first()
        
        # 如果没有配置，使用默认模型
        if not llm_model:
            llm_model = self.db.query(LLMModel).filter(
                LLMModel.is_default == 1,
                LLMModel.is_active == 1
            ).first()
        
        if not llm_model:
            logger.error("未找到可用的LLM模型")
            return {
                'content': '抱歉，系统暂时无法回答。请稍后再试或联系老师。',
                'knowledge_sources': [],
                'token_usage': {'prompt': 0, 'completion': 0, 'total': 0},
                'model': 'unknown'
            }
        
        # 3. 构建消息列表
        messages = [
            {"role": "system", "content": context}
        ]
        
        # 添加历史消息（已按时间升序排列，包含当前用户消息）
        for msg in conversation_history:
            if msg.role in ['user', 'assistant']:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 注意：conversation_history已经包含了刚保存的用户消息，无需再次添加
        
        # 4. 调用LLM服务
        try:
            llm_service = create_llm_service(llm_model)
            response = llm_service.chat(messages=messages)
            
            return {
                'content': response.get('response', '抱歉，我现在无法回答。'),
                'knowledge_sources': [],  # 知识库检索功能待后续实现
                'token_usage': response.get('token_usage', {
                    'prompt': 0,
                    'completion': 0,
                    'total': 0
                }),
                'model': llm_model.name
            }
        
        except Exception as e:
            logger.error(f"调用LLM失败: {str(e)}", exc_info=True)
            return {
                'content': '抱歉，我现在无法回答。请稍后再试或联系老师。',
                'knowledge_sources': [],
                'token_usage': {'prompt': 0, 'completion': 0, 'total': 0},
                'model': llm_model.name
            }
    
    async def _get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 10
    ) -> List[LearningAssistantMessage]:
        """获取最近的消息历史（按时间升序返回）"""
        messages = self.db.query(LearningAssistantMessage).filter(
            LearningAssistantMessage.conversation_id == conversation_id
        ).order_by(
            LearningAssistantMessage.created_at.asc()  # 升序，最早的在前
        ).all()
        
        # 如果消息数量超过限制，只返回最近的limit条
        if len(messages) > limit:
            return messages[-limit:]
        return messages
    
    async def _update_conversation_stats(self, conversation_id: int):
        """更新会话统计信息"""
        conversation = self.db.query(LearningAssistantConversation).get(conversation_id)
        
        if not conversation:
            return
        
        # 统计消息数
        messages = self.db.query(LearningAssistantMessage).filter(
            LearningAssistantMessage.conversation_id == conversation_id
        ).all()
        
        conversation.message_count = len(messages)
        conversation.user_message_count = sum(1 for m in messages if m.role == 'user')
        conversation.ai_message_count = sum(1 for m in messages if m.role == 'assistant')
        conversation.last_message_at = datetime.now()
        
        # 计算平均响应时间
        response_times = [m.response_time_ms for m in messages if m.response_time_ms]
        if response_times:
            conversation.avg_response_time = int(sum(response_times) / len(response_times))
        
        self.db.commit()
    
    async def _get_student_profile(self, user_id: int) -> Optional[StudentLearningProfile]:
        """获取学生档案"""
        profile = self.db.query(StudentLearningProfile).filter(
            StudentLearningProfile.user_id == user_id
        ).first()
        
        if not profile:
            # 创建默认档案
            profile = StudentLearningProfile(
                user_id=user_id,
                total_conversations=0,
                total_messages=0,
                total_questions=0
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        
        return profile
    
    async def _update_student_profile(
        self,
        user_id: int,
        message: str,
        context: Dict
    ):
        """更新学生档案"""
        profile = await self._get_student_profile(user_id)
        
        # 更新统计
        profile.total_messages += 1
        profile.total_questions += 1
        profile.last_active_at = datetime.now()
        
        # 更新学习课程列表
        if context.get('course_uuid'):
            courses = profile.courses_learned or []
            course_ids = [c.get('uuid') for c in courses if isinstance(c, dict)]
            
            if context['course_uuid'] not in course_ids:
                courses.append({
                    'uuid': context['course_uuid'],
                    'name': context.get('course_name'),
                    'last_active': datetime.now().isoformat()
                })
                profile.courses_learned = courses
            
            profile.last_course_uuid = context['course_uuid']
        
        if context.get('unit_uuid'):
            profile.last_unit_uuid = context['unit_uuid']
        
        self.db.commit()
    
    async def _log_moderation(
        self,
        user_id: int,
        conversation_id: int,
        message_id: int,
        content_type: str,
        content: str,
        result: Dict
    ):
        """记录审核日志"""
        log = ContentModerationLog(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            content_type=content_type,
            original_content=content,
            status=result['status'],
            flags=result['flags'],
            risk_score=result['risk_score'],
            sensitive_words=result.get('sensitive_words_found'),
            moderation_service='local'
        )
        
        self.db.add(log)
        self.db.commit()
    
    async def _generate_conversation_title(
        self,
        user_message: str,
        ai_response: str
    ) -> Optional[str]:
        """
        根据首次对话内容，让AI生成一个简短的会话标题
        
        Args:
            user_message: 用户的首次提问
            ai_response: AI的首次回复
            
        Returns:
            生成的标题（不超过20字），如果失败则返回None
        """
        try:
            logger.info(f"🏷️ 开始生成会话标题...")
            logger.debug(f"用户消息: {user_message[:50]}...")
            
            # 构造标题生成提示词（更简洁明确）
            title_prompt = f"""请为以下对话生成一个简短标题（5-15个汉字）。

用户提问：{user_message[:100]}

要求：
1. 只返回标题，不要任何其他内容
2. 不要引号、标点
3. 直接概括主题

标题："""

            messages = [
                {"role": "user", "content": title_prompt}
            ]
            
            # 调用LLM生成标题（使用默认模型）
            from app.models.llm_model import LLMModel
            llm_model = self.db.query(LLMModel).filter(
                LLMModel.is_default == 1,
                LLMModel.is_active == 1
            ).first()
            
            if not llm_model:
                logger.warning("⚠️ 未找到默认LLM模型，无法生成标题")
                return None
            
            logger.info(f"📡 使用模型: {llm_model.display_name} ({llm_model.name})")
            
            from app.services.llm_service import create_llm_service
            llm_service = create_llm_service(llm_model)
            
            response = llm_service.chat(messages)  # ✅ 移除await，chat不是异步方法
            logger.debug(f"LLM返回: {response}")
            
            # 尝试多个可能的键
            title = response.get('response') or response.get('content') or response.get('text') or ''
            title = title.strip()
            
            logger.info(f"🔍 原始标题: '{title}'")
            
            # 清理标题
            # 1. 移除常见的前缀
            for prefix in ['标题：', '标题:', '会话标题：', '会话标题:', '标题为：', '标题为:']:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            # 2. 去除引号、换行、省略号等
            title = title.replace('"', '').replace("'", '').replace('「', '').replace('」', '')
            title = title.replace('\n', ' ').replace('\r', '').strip()
            title = title.rstrip('.')  # 移除末尾的句号
            title = title.rstrip('。')  # 移除末尾的中文句号
            title = title.rstrip('…')  # 移除末尾的省略号
            title = title.rstrip('...')  # 移除末尾的三个点
            title = title.strip()
            
            # 3. 限制长度
            if len(title) > 20:
                title = title[:20]
            
            logger.info(f"✨ 清理后标题: '{title}'")
            
            # 验证标题有效性
            if not title or len(title) < 2:
                logger.warning(f"⚠️ 标题无效（长度: {len(title)}）")
                return None
            
            logger.info(f"✅ 成功生成标题: '{title}'")
            return title
            
        except Exception as e:
            logger.error(f"❌ 生成会话标题时出错: {str(e)}", exc_info=True)
            return None

