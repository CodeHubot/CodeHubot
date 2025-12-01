#!/bin/bash
# Celery Worker 启动脚本

# 切换到项目目录
cd "$(dirname "$0")/.."

# 激活虚拟环境（如果使用）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 创建日志目录
mkdir -p logs

# 启动 Celery Worker
echo "🚀 启动 Celery Worker..."
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid \
    --detach

echo "✅ Celery Worker 已启动"
echo "📝 日志文件: logs/celery_worker.log"
echo "📋 PID文件: logs/celery_worker.pid"
echo ""
echo "查看日志: tail -f logs/celery_worker.log"
echo "停止Worker: celery -A app.core.celery_app control shutdown"


