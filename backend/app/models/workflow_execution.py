from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class WorkflowExecution(Base):
    """
    工作流执行记录模型 - 用于记录工作流的执行历史
    支持执行状态跟踪、结果存储、错误记录等功能
    """
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True, comment="执行记录ID")
    execution_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="执行唯一标识UUID")
    workflow_id = Column(Integer, ForeignKey("workflow_main.id"), nullable=False, comment="工作流ID")
    
    # 执行状态
    status = Column(String(20), default="pending", comment="执行状态（pending/running/completed/failed）")
    
    # 输入输出
    input = Column(JSON, comment="工作流输入参数（JSON对象）")
    output = Column(JSON, comment="工作流输出结果（JSON对象）")
    error_message = Column(Text, comment="错误信息（执行失败时）")
    
    # 节点执行记录
    node_executions = Column(JSON, comment="节点执行记录（JSON数组）")
    
    # 时间信息
    started_at = Column(DateTime, comment="开始执行时间")
    completed_at = Column(DateTime, comment="完成执行时间")
    execution_time = Column(Integer, comment="执行时间（毫秒）")
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    # 关系
    workflow = relationship("Workflow", back_populates="executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"

