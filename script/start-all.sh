#!/bin/bash
# 一键启动所有AIOT服务

echo "=========================================="
echo "🚀 启动 AIOT 微服务架构"
echo "=========================================="

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查基础服务
check_service() {
    echo -n "检查 $1... "
    if systemctl is-active --quiet $2; then
        echo -e "${GREEN}✓ 运行中${NC}"
        return 0
    else
        echo -e "${RED}✗ 未运行${NC}"
        return 1
    fi
}

echo ""
echo "📊 检查基础服务..."
check_service "MySQL" "mysql" || echo "  请先启动: sudo systemctl start mysql"
check_service "Redis" "redis" || echo "  请先启动: sudo systemctl start redis"
check_service "Mosquitto" "mosquitto" || echo "  请先启动: sudo systemctl start mosquitto"

echo ""
echo "=========================================="
echo "🔧 启动应用服务..."
echo "=========================================="

# 1. Backend
echo ""
echo -e "${YELLOW}1️⃣  启动Backend (8000)...${NC}"
cd "$PROJECT_ROOT/backend"
nohup python main.py > logs/backend_nohup.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend 已启动 (PID: $BACKEND_PID)${NC}"
sleep 2

# 2. MQTT服务
echo ""
echo -e "${YELLOW}2️⃣  启动MQTT服务...${NC}"
cd "$PROJECT_ROOT/service/mqtt-service"
nohup python main.py > logs/mqtt_nohup.log 2>&1 &
MQTT_PID=$!
echo -e "${GREEN}✅ MQTT服务 已启动 (PID: $MQTT_PID)${NC}"
sleep 2

# 3. Celery Worker
echo ""
echo -e "${YELLOW}3️⃣  启动Celery Worker...${NC}"
cd "$PROJECT_ROOT/service/celery-service"
nohup bash start_worker.sh > logs/worker_nohup.log 2>&1 &
WORKER_PID=$!
echo -e "${GREEN}✅ Celery Worker 已启动 (PID: $WORKER_PID)${NC}"
sleep 2

# 4. Flower
echo ""
echo -e "${YELLOW}4️⃣  启动Flower监控 (5555)...${NC}"
cd "$PROJECT_ROOT/service/celery-service"
nohup bash start_flower.sh > logs/flower_nohup.log 2>&1 &
FLOWER_PID=$!
echo -e "${GREEN}✅ Flower 已启动 (PID: $FLOWER_PID)${NC}"
sleep 2

# 5. Plugin Backend
echo ""
echo -e "${YELLOW}5️⃣  启动Plugin Backend (9002)...${NC}"
cd "$PROJECT_ROOT/service/plugin-backend-service"
nohup python main.py > logs/plugin_backend_nohup.log 2>&1 &
PLUGIN_BACKEND_PID=$!
echo -e "${GREEN}✅ Plugin Backend 已启动 (PID: $PLUGIN_BACKEND_PID)${NC}"
sleep 2

# 6. Plugin Service
echo ""
echo -e "${YELLOW}6️⃣  启动Plugin Service (9000)...${NC}"
cd "$PROJECT_ROOT/service/plugin-service"
nohup python main.py > logs/plugin_service_nohup.log 2>&1 &
PLUGIN_SERVICE_PID=$!
echo -e "${GREEN}✅ Plugin Service 已启动 (PID: $PLUGIN_SERVICE_PID)${NC}"
sleep 2

echo ""
echo "=========================================="
echo "✅ 所有服务启动完成！"
echo "=========================================="
echo ""
echo "📍 服务地址："
echo "  - Backend API:        http://localhost:8000"
echo "  - Flower监控:         http://localhost:5555/flower"
echo "  - Plugin Backend:     http://localhost:9002 (内部服务)"
echo "  - Plugin Service:     http://localhost:9000"
echo ""
echo "📊 进程ID："
echo "  - Backend:            $BACKEND_PID"
echo "  - MQTT服务:           $MQTT_PID"
echo "  - Celery Worker:      $WORKER_PID"
echo "  - Flower:             $FLOWER_PID"
echo "  - Plugin Backend:     $PLUGIN_BACKEND_PID"
echo "  - Plugin Service:     $PLUGIN_SERVICE_PID"
echo ""
echo "📝 查看日志："
echo "  - Backend:            tail -f backend/logs/backend_nohup.log"
echo "  - MQTT:               tail -f service/mqtt-service/logs/mqtt_nohup.log"
echo "  - Celery:             tail -f service/celery-service/logs/worker_nohup.log"
echo "  - Flower:             tail -f service/celery-service/logs/flower_nohup.log"
echo "  - Plugin Backend:     tail -f service/plugin-backend-service/logs/plugin_backend_nohup.log"
echo "  - Plugin Service:     tail -f service/plugin-service/logs/plugin_service_nohup.log"
echo ""
echo "🛑 停止所有服务："
echo "  bash 停止所有服务.sh"
echo ""
echo "=========================================="

