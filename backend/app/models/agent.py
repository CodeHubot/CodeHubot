from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class Agent(Base):
    """
    智能体模型 - 用于创建和管理 AI 智能体
    目前只支持提示词和插件配置
    """
    __tablename__ = "agent_main"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    name = Column(String(100), nullable=False, comment="智能体名称")
    description = Column(Text, comment="智能体描述")
    
    # 系统提示词
    system_prompt = Column(Text, comment="系统提示词")
    
    # 关联的插件（JSON 数组，存储插件 ID）
    plugin_ids = Column(JSON, default=list, comment="关联的插件 ID 列表")
    
    # 关联的大模型
    llm_model_id = Column(Integer, ForeignKey("llm_models.id"), comment="关联的大模型ID")
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="创建用户 ID")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活（1=激活，0=禁用）")
    is_system = Column(Integer, default=0, comment="是否系统内置（1=是，0=否）")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

