"""
提示词模板模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class PromptTemplate(Base):
    """提示词模板模型"""
    __tablename__ = "llm_prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(255), comment="模板描述")
    content = Column(Text, nullable=False, comment="提示词内容")
    category = Column(String(50), comment="分类标签")
    tags = Column(JSON, comment="标签数组")
    difficulty = Column(String(20), comment="难度等级")
    suitable_for = Column(String(100), comment="适用场景")
    requires_plugin = Column(Boolean, default=False, comment="是否需要插件")
    recommended_temperature = Column(DECIMAL(3, 2), default=0.70, comment="推荐Temperature")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

