#!/bin/bash
# ========================================
# 紧急停止 Celery Worker 脚本
# 用于服务器卡死时强制终止所有 Celery 进程
# ========================================

echo "=========================================="
echo "🚨 紧急停止 Celery Worker"
echo "=========================================="

# 1. 查找所有 Celery 进程
echo ""
echo "1. 查找 Celery 进程..."
ps aux | grep -E "celery.*worker" | grep -v grep

# 2. 强制终止所有 Celery 进程
echo ""
echo "2. 强制终止 Celery 进程..."
pkill -9 -f "celery.*worker"

# 等待2秒
sleep 2

# 3. 确认是否还有 Celery 进程
echo ""
echo "3. 确认是否还有残留进程..."
REMAINING=$(ps aux | grep -E "celery.*worker" | grep -v grep | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 所有 Celery 进程已停止"
else
    echo "⚠️  还有 $REMAINING 个进程未停止，尝试更强力的终止..."
    ps aux | grep -E "celery.*worker" | grep -v grep | awk '{print $2}' | xargs -I {} sudo kill -9 {}
    sleep 2
    
    REMAINING=$(ps aux | grep -E "celery.*worker" | grep -v grep | wc -l)
    if [ "$REMAINING" -eq 0 ]; then
        echo "✅ 所有 Celery 进程已强制停止"
    else
        echo "❌ 仍有进程无法停止，可能需要重启服务器"
        ps aux | grep -E "celery.*worker" | grep -v grep
    fi
fi

# 4. 清理 Celery 队列（可选）
echo ""
read -p "是否清理 Redis 中的 Celery 队列？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理 Celery 队列..."
    redis-cli FLUSHDB
    echo "✅ Celery 队列已清理"
fi

# 5. 重置数据库中的 processing 状态
echo ""
read -p "是否重置数据库中的 processing 状态？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "请输入 MySQL root 密码："
    read -s MYSQL_PASSWORD
    
    mysql -u root -p"$MYSQL_PASSWORD" aiot_admin << 'EOF'
UPDATE aiot_documents
SET embedding_status = 'failed',
    embedding_error = '任务中断：系统维护',
    updated_at = NOW()
WHERE embedding_status = 'processing';

SELECT CONCAT('✅ 已重置 ', ROW_COUNT(), ' 个文档的状态') AS result;
EOF
fi

echo ""
echo "=========================================="
echo "✅ 紧急停止完成"
echo "=========================================="
echo ""
echo "后续步骤："
echo "1. git pull origin main  # 拉取修复代码"
echo "2. cd backend && nohup celery -A app.core.celery_app worker --loglevel=info --concurrency=2 > logs/celery_worker.log 2>&1 &"
echo "3. tail -f logs/celery_worker.log  # 查看日志"

