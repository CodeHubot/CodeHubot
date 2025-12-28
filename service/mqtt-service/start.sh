#!/bin/bash

# MQTT 服务快速启动脚本

set -e

echo "=========================================="
echo "🚀 启动 MQTT 服务"
echo "=========================================="

# 检查环境配置
if [ ! -f .env ]; then
    echo "❌ 错误：未找到 .env 文件"
    echo "请先复制 env.example 为 .env 并配置"
    echo ""
    echo "  cp env.example .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

echo "✅ 配置文件已加载"
echo ""
echo "📊 配置信息："
echo "  MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
echo "  数据库: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 python3"
    exit 1
fi

echo "✅ Python 环境: $(python3 --version)"

# 检查依赖
if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "⚠️ 依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

echo "✅ 依赖检查通过"
echo ""

# 测试数据库连接
echo "🔍 测试数据库连接..."
python3 -c "
from database import SessionLocal
from sqlalchemy import text
try:
    db = SessionLocal()
    db.execute(text('SELECT 1'))
    db.close()
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
" || exit 1

echo ""
echo "=========================================="
echo "🚀 启动 MQTT 服务..."
echo "=========================================="
echo ""
echo "提示：按 Ctrl+C 停止服务"
echo ""

# 启动服务
python3 main.py





