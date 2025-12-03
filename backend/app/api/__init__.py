from fastapi import APIRouter
from app.api import (
    auth, devices, users, products, dashboard, firmware, agents, 
    plugins, llm_models, chat, prompt_templates, schools, user_management, courses, device_groups,
    knowledge_bases, kb_documents, kb_search, workflows
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(products.router, prefix="/products", tags=["产品管理"])
api_router.include_router(devices.router, prefix="/devices", tags=["设备管理"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["固件管理"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体管理"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["插件管理"])
api_router.include_router(llm_models.router, prefix="/llm-models", tags=["模型配置"])
api_router.include_router(chat.router, prefix="/chat", tags=["智能体对话"])
api_router.include_router(prompt_templates.router, prefix="/prompt-templates", tags=["提示词模板"])
api_router.include_router(schools.router, tags=["学校管理"])
api_router.include_router(user_management.router, tags=["用户管理模块"])
api_router.include_router(courses.router, tags=["课程管理"])
api_router.include_router(device_groups.router, tags=["设备分组管理"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["知识库管理"])
api_router.include_router(kb_documents.router, prefix="/kb-documents", tags=["知识库文档管理"])
api_router.include_router(kb_search.router, prefix="/knowledge-bases", tags=["知识库检索"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["工作流管理"])