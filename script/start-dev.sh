#!/bin/bash

# ========================================
# CodeHubot 本地开发环境启动脚本
# ========================================

echo "🚀 启动 CodeHubot 本地开发环境"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ========================================
# 1. 检查 Docker 基础服务
# ========================================
echo "📦 检查 Docker 基础服务..."

check_docker_service() {
    local service=$1
    if docker ps | grep -q "$service"; then
        echo -e "${GREEN}✅ $service 正在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service 未运行${NC}"
        return 1
    fi
}

# 检查必需的服务
MYSQL_RUNNING=$(check_docker_service "codehubot-mysql")
REDIS_RUNNING=$(check_docker_service "codehubot-redis")
MQTT_RUNNING=$(check_docker_service "codehubot-mqtt")

# 如果基础服务没有运行，询问是否启动
if ! docker ps | grep -q "codehubot-mysql\|codehubot-redis\|codehubot-mqtt"; then
    echo ""
    echo -e "${YELLOW}基础服务（MySQL/Redis/MQTT）未运行${NC}"
    read -p "是否启动 Docker 基础服务？(y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT/docker"
        docker-compose up -d mysql redis mqtt
        echo -e "${GREEN}✅ Docker 基础服务已启动${NC}"
        sleep 3
    else
        echo -e "${RED}❌ 需要基础服务才能运行，退出${NC}"
        exit 1
    fi
fi

echo ""

# ========================================
# 2. 停止容器中的前后端服务
# ========================================
echo "🛑 停止容器中的前后端服务..."

if docker ps | grep -q "codehubot-backend"; then
    docker stop codehubot-backend
    echo -e "${GREEN}✅ 已停止容器中的后端服务${NC}"
fi

if docker ps | grep -q "codehubot-frontend"; then
    docker stop codehubot-frontend
    echo -e "${GREEN}✅ 已停止容器中的前端服务${NC}"
fi

echo ""

# ========================================
# 3. 询问启动选项
# ========================================
echo "请选择启动模式："
echo "1) 同时启动前端和后端（推荐）"
echo "2) 仅启动后端"
echo "3) 仅启动前端"
read -p "请输入选项 (1/2/3): " -n 1 -r
echo ""
echo ""

START_BACKEND=false
START_FRONTEND=false

case $REPLY in
    1)
        START_BACKEND=true
        START_FRONTEND=true
        ;;
    2)
        START_BACKEND=true
        ;;
    3)
        START_FRONTEND=true
        ;;
    *)
        echo -e "${RED}无效选项，退出${NC}"
        exit 1
        ;;
esac

# ========================================
# 4. 启动后端
# ========================================
if [ "$START_BACKEND" = true ]; then
    echo "🐍 启动后端开发服务器..."
    
    cd "$PROJECT_ROOT/backend"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  未找到虚拟环境，正在创建...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 文件，从示例复制...${NC}"
        cp env.example .env
        echo -e "${YELLOW}⚠️  请编辑 backend/.env 配置必要参数！${NC}"
        read -p "按回车键继续..." 
    fi
    
    # 在新终端启动后端
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell app \"Terminal\"
            do script \"cd '$PROJECT_ROOT/backend' && source venv/bin/activate && echo '🐍 启动后端服务器...' && uvicorn main:app --reload --host 0.0.0.0 --port 8000\"
        end tell"
        echo -e "${GREEN}✅ 后端服务器已在新终端启动${NC}"
        echo -e "   访问: ${GREEN}http://localhost:8000/docs${NC}"
    else
        # Linux
        gnome-terminal -- bash -c "cd '$PROJECT_ROOT/backend' && source venv/bin/activate && echo '🐍 启动后端服务器...' && uvicorn main:app --reload --host 0.0.0.0 --port 8000; exec bash"
        echo -e "${GREEN}✅ 后端服务器已在新终端启动${NC}"
        echo -e "   访问: ${GREEN}http://localhost:8000/docs${NC}"
    fi
    
    sleep 2
fi

# ========================================
# 5. 启动前端
# ========================================
if [ "$START_FRONTEND" = true ]; then
    echo ""
    echo "⚛️  启动前端开发服务器..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️  未找到 node_modules，正在安装依赖...${NC}"
        npm install
    fi
    
    # 在新终端启动前端
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell app \"Terminal\"
            do script \"cd '$PROJECT_ROOT/frontend' && echo '⚛️  启动前端服务器...' && npm run dev\"
        end tell"
        echo -e "${GREEN}✅ 前端服务器已在新终端启动${NC}"
        echo -e "   访问: ${GREEN}http://localhost:3000${NC}"
    else
        # Linux
        gnome-terminal -- bash -c "cd '$PROJECT_ROOT/frontend' && echo '⚛️  启动前端服务器...' && npm run dev; exec bash"
        echo -e "${GREEN}✅ 前端服务器已在新终端启动${NC}"
        echo -e "   访问: ${GREEN}http://localhost:3000${NC}"
    fi
fi

# ========================================
# 6. 总结
# ========================================
echo ""
echo "========================================="
echo -e "${GREEN}✨ 开发环境启动完成！${NC}"
echo "========================================="
echo ""
echo "📝 服务地址："
echo -e "   前端: ${GREEN}http://localhost:3000${NC}"
echo -e "   后端: ${GREEN}http://localhost:8000${NC}"
echo -e "   API文档: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "🔧 Docker 服务："
echo -e "   MySQL: ${GREEN}localhost:3306${NC}"
echo -e "   Redis: ${GREEN}localhost:6379${NC}"
echo -e "   MQTT: ${GREEN}localhost:1883${NC}"
echo ""
echo "💡 提示："
echo "   - 修改代码后会自动重载"
echo "   - 按 Ctrl+C 停止服务"
echo "   - 查看日志请切换到对应终端"
echo ""
echo "📚 更多信息请查看: 本地开发调试指南.md"
echo ""
