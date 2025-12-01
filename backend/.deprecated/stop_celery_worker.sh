#!/bin/bash
# Celery Worker 停止脚本

cd "$(dirname "$0")/.."

echo "🛑 停止 Celery Worker..."

# 方式1: 使用 Celery 命令
celery -A app.core.celery_app control shutdown

# 方式2: 使用 PID 文件
if [ -f "logs/celery_worker.pid" ]; then
    pid=$(cat logs/celery_worker.pid)
    if ps -p $pid > /dev/null 2>&1; then
        kill -TERM $pid
        echo "✅ 已发送停止信号到进程 $pid"
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $pid > /dev/null 2>&1; then
                echo "✅ Worker 已停止"
                break
            fi
            echo "⏳ 等待 Worker 停止..."
            sleep 1
        done
        
        # 如果还没停止，强制终止
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid
            echo "⚠️  强制终止 Worker"
        fi
    else
        echo "⚠️  进程 $pid 不存在"
    fi
    rm -f logs/celery_worker.pid
else
    echo "⚠️  PID 文件不存在"
fi

echo "✅ 完成"


