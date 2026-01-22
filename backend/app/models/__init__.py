from .user import User
from .product import Product
from .device import Device
from .agent import Agent
from .plugin import Plugin
from .llm_model import LLMModel
from .llm_provider import LLMProvider
from .team import Team
from .firmware import Firmware
from .course_model import Course, CourseTeacher, CourseStudent, CourseGroup, GroupMember
from .knowledge_base import KnowledgeBase, AgentKnowledgeBase, KBPermission, KBSharing, UnitKnowledgeBase, KnowledgeUsageLog
from .document import Document, DocumentChunk
from .kb_analytics import KBRetrievalLog, KBAnalytics
from .device_group import DeviceGroup, DeviceGroupMember
from .device_binding_history import DeviceBindingHistory
# from .interaction_log import InteractionLog, InteractionStatsHourly, InteractionStatsDaily  # 已删除日志表
from .prompt_template import PromptTemplate
from .workflow import Workflow
from .workflow_execution import WorkflowExecution
from .system_config import SystemConfig

# 确保所有模型都被导入，以便 SQLAlchemy 能够正确创建表结构和关系
__all__ = [
    "User", "Product", "Device", "Agent", "Plugin", 
    "LLMModel", "LLMProvider", "Team", "Firmware",
    "Course", "CourseTeacher", "CourseStudent", "CourseGroup", "GroupMember",
    "KnowledgeBase", "AgentKnowledgeBase", "KBPermission", "KBSharing", "UnitKnowledgeBase", "KnowledgeUsageLog",
    "Document", "DocumentChunk",
    "KBRetrievalLog", "KBAnalytics",
    "DeviceGroup", "DeviceGroupMember", "DeviceBindingHistory",
    # "InteractionLog", "InteractionStatsHourly", "InteractionStatsDaily",  # 已删除日志表
    "PromptTemplate",
    "Workflow", "WorkflowExecution",
    "SystemConfig"
]