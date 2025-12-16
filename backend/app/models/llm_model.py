from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, DECIMAL
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class LLMModel(Base):
    """
    大模型配置模型 - 用于管理各种大语言模型的配置
    支持国产大模型和国际主流模型
    """
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    name = Column(String(100), nullable=False, comment="模型名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    provider = Column(String(50), nullable=False, comment="提供商")
    model_type = Column(String(50), default="chat", comment="模型类型")
    api_base = Column(String(500), comment="API基础URL")
    api_key = Column(String(500), comment="API密钥")
    api_version = Column(String(50), comment="API版本")
    max_tokens = Column(Integer, default=4096, comment="最大token数")
    temperature = Column(DECIMAL(3, 2), default=0.70, comment="温度参数")
    top_p = Column(DECIMAL(3, 2), default=0.90, comment="top_p参数")
    enable_deep_thinking = Column(Integer, default=0, comment="是否启用深度思考")
    frequency_penalty = Column(DECIMAL(3, 2), default=0.00, comment="频率惩罚参数")
    presence_penalty = Column(DECIMAL(3, 2), default=0.00, comment="存在惩罚参数")
    config = Column(JSON, comment="其他配置参数")
    description = Column(Text, comment="模型描述")
    is_active = Column(Integer, default=1, comment="是否激活")
    is_default = Column(Integer, default=0, comment="是否默认模型")
    is_system = Column(Integer, default=0, comment="是否系统内置")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    def __repr__(self):
        return f"<LLMModel(id={self.id}, name='{self.name}', provider='{self.provider}')>"

