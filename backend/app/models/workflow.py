from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class Workflow(Base):
    """
    工作流模型 - 用于创建和管理工作流
    支持可视化编辑、DAG验证、执行等功能
    """
    __tablename__ = "workflow_main"
    
    id = Column(Integer, primary_key=True, index=True, comment="工作流ID")
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    name = Column(String(100), nullable=False, comment="工作流名称")
    description = Column(Text, comment="工作流描述")
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, comment="创建用户ID")
    
    # 工作流结构（JSON格式）
    nodes = Column(JSON, nullable=False, comment="节点列表（JSON数组）")
    edges = Column(JSON, nullable=False, comment="边列表（JSON数组）")
    config = Column(JSON, comment="工作流配置（超时、重试等）")
    
    # 状态
    is_active = Column(Integer, default=1, comment="是否激活（1=激活，0=禁用）")
    is_public = Column(Integer, default=0, comment="是否公开（1=公开，0=私有）")
    
    # 统计信息
    execution_count = Column(Integer, default=0, comment="执行次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    # 关系
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', uuid='{self.uuid}')>"

