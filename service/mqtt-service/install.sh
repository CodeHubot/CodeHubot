#!/bin/bash

# MQTT 服务安装脚本
# 用途：将 MQTT 服务安装为 systemd 服务

set -e

echo "=========================================="
echo "AIOT MQTT 服务安装脚本"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 用户或 sudo 运行此脚本"
    exit 1
fi

# 配置变量
SERVICE_NAME="mqtt-service"
SERVICE_FILE="mqtt-service.service"
INSTALL_DIR="/opt/codehubot/service/mqtt-service"
LOG_DIR="/var/log/codehubot"
VENV_PATH="/opt/codehubot/venv"

echo ""
echo "📦 安装配置："
echo "  服务名称: $SERVICE_NAME"
echo "  安装目录: $INSTALL_DIR"
echo "  日志目录: $LOG_DIR"
echo "  虚拟环境: $VENV_PATH"
echo ""

# 1. 创建安装目录
echo "1️⃣ 创建安装目录..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"

# 2. 复制服务文件
echo "2️⃣ 复制服务文件..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# 3. 检查环境配置文件
echo "3️⃣ 检查环境配置..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚠️ 未找到 .env 文件，从 env.example 复制..."
    cp "$INSTALL_DIR/env.example" "$INSTALL_DIR/.env"
    echo "❗ 请编辑 $INSTALL_DIR/.env 配置数据库和MQTT连接信息"
    echo "   然后重新运行此脚本"
    exit 1
else
    echo "✅ 找到 .env 配置文件"
fi

# 4. 安装 Python 依赖
echo "4️⃣ 安装 Python 依赖..."
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install -r "$INSTALL_DIR/requirements.txt"
echo "✅ 依赖安装完成"

# 5. 设置文件权限
echo "5️⃣ 设置文件权限..."
chown -R www-data:www-data "$INSTALL_DIR"
chown -R www-data:www-data "$LOG_DIR"
chmod 644 "$INSTALL_DIR/.env"
chmod 755 "$INSTALL_DIR"/*.py

# 6. 安装 systemd 服务
echo "6️⃣ 安装 systemd 服务..."
cp "$INSTALL_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_FILE"
systemctl daemon-reload
echo "✅ 服务文件已安装"

# 7. 测试数据库连接
echo "7️⃣ 测试数据库连接..."
cd "$INSTALL_DIR"
source "$VENV_PATH/bin/activate"
python3 -c "
from database import SessionLocal, engine
from sqlalchemy import text
try:
    db = SessionLocal()
    db.execute(text('SELECT 1'))
    db.close()
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 数据库连接测试失败，请检查配置"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ MQTT 服务安装完成！"
echo "=========================================="
echo ""
echo "📝 后续操作："
echo ""
echo "1️⃣ 启用服务（开机自启）："
echo "   sudo systemctl enable $SERVICE_NAME"
echo ""
echo "2️⃣ 启动服务："
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "3️⃣ 查看服务状态："
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "4️⃣ 查看日志："
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   或"
echo "   sudo tail -f $LOG_DIR/mqtt-service.log"
echo ""
echo "5️⃣ 停止服务："
echo "   sudo systemctl stop $SERVICE_NAME"
echo ""
echo "6️⃣ 重启服务："
echo "   sudo systemctl restart $SERVICE_NAME"
echo ""
echo "=========================================="
