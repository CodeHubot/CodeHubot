#!/usr/bin/env python3
"""
Celery Worker 启动脚本
用于处理异步任务（如文档向量化）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# ✅ 在导入 Celery 应用之前，先导入所有模型
# 这样可以确保 SQLAlchemy 的 mapper 在 Worker 启动时就被正确初始化
# 避免在任务执行时才初始化导致的循环依赖问题
import app.models  # 这会导入 models/__init__.py 中的所有模型

# 导入 Celery 应用
from app.core.celery_app import celery_app

if __name__ == '__main__':
    # 启动 Celery Worker
    celery_app.start()


