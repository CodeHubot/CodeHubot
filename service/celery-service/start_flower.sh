#!/bin/bash
# Flower 监控服务启动脚本

# 设置环境变量
export PYTHONPATH="/app/celery-service:/app/backend:$PYTHONPATH"

# 构建 Redis URL
REDIS_URL="redis://${REDIS_HOST:-redis}:${REDIS_PORT:-6379}/${REDIS_DB:-0}"

# 启动 Flower (按照 celery [celery args] flower [flower args] 的格式)
celery -A celery_app --broker="${REDIS_URL}" flower \
    --port=5555 \
    --basic_auth="${FLOWER_BASIC_AUTH:-admin:admin}" \
    --url_prefix=flower
