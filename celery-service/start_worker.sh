#!/bin/bash
# 启动 Celery Worker

echo "🚀 启动 Celery Worker..."

# 设置Python路径
export PYTHONPATH="$PWD:$PWD/../backend:$PYTHONPATH"

# 启动Worker
celery -A celery_app worker \
  --loglevel=info \
  --pool=eventlet \
  --concurrency=4 \
  --max-tasks-per-child=50 \
  --logfile=logs/celery_worker.log

echo "✅ Celery Worker 已启动"

