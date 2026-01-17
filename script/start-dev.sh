#!/bin/bash

# ==========================================
# CodeHubot 本地开发环境快速启动脚本
# ==========================================
# 用途：一键启动开发环境的所有支持服务
# 说明：前后端需要在单独的终端中手动启动
# ==========================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}=========================================="
echo "🔧 CodeHubot 开发环境启动"
echo -e "==========================================${NC}"
echo ""

# 调用主部署脚本
bash "${SCRIPT_DIR}/deploy.sh" start-dev-services

echo ""
echo -e "${GREEN}=========================================="
echo "✓ 开发环境准备就绪"
echo -e "==========================================${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo ""
echo "1️⃣  在新终端启动后端："
echo -e "   ${BLUE}cd ${PROJECT_ROOT}/backend${NC}"
echo -e "   ${BLUE}uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "2️⃣  在另一个终端启动前端："
echo -e "   ${BLUE}cd ${PROJECT_ROOT}/frontend${NC}"
echo -e "   ${BLUE}npm run dev${NC}"
echo ""
echo -e "${YELLOW}访问地址：${NC}"
echo "   - 前端: http://localhost:5173"
echo "   - 后端API: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - Flower监控: http://localhost:5555"
echo "   - phpMyAdmin: http://localhost:8081"
echo ""
