from fastapi import APIRouter
from app.api import (
    auth, devices, users, products, dashboard, firmware, 
    user_management, courses, device_groups, system_config
)
from app.api.ai import router as ai_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(products.router, prefix="/products", tags=["产品管理"])
api_router.include_router(devices.router, prefix="/devices", tags=["设备管理"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["固件管理"])
api_router.include_router(user_management.router, tags=["用户管理模块"])
api_router.include_router(courses.router, tags=["课程管理"])
api_router.include_router(device_groups.router, tags=["设备分组管理"])

# 系统配置管理路由
api_router.include_router(system_config.router, prefix="/system-config", tags=["系统配置"])

# AI系统路由
api_router.include_router(ai_router, prefix="/ai", tags=["AI智能系统"])