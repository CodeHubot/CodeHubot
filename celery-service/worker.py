#!/usr/bin/env python3
"""
Celery Worker 启动脚本
用于处理异步任务（如文档向量化）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录和backend目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
backend_dir = project_root / 'backend'

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 在导入 Celery 应用之前，先导入所有模型
# 这样可以确保 SQLAlchemy 的 mapper 在 Worker 启动时就被正确初始化
import app.models  # 从backend导入所有模型

# 导入 Celery 应用
from celery_app import celery_app

if __name__ == '__main__':
    # 启动 Celery Worker
    # 使用worker.start()而不是celery_app.start()
    argv = [
        'worker',
        '--loglevel=INFO',
        '-E',  # 启用事件（用于Flower监控）
    ]
    celery_app.worker_main(argv=argv)

