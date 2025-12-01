#!/bin/bash
# 停止所有 Celery 服务

echo "🛑 停止 Celery 服务..."

# 停止Worker
echo "停止 Celery Worker..."
pkill -f "celery.*worker"

# 停止Flower
echo "停止 Flower..."
pkill -f "celery.*flower"

echo "✅ 所有 Celery 服务已停止"

