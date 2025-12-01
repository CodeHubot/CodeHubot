#!/bin/bash
# ==============================================
# 停止所有CodeHubot服务
# ==============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR}/docker"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 显示标题
echo ""
echo -e "${BLUE}=============================================="
echo -e "🛑 停止所有 CodeHubot 服务"
echo -e "=============================================="
echo -e "${NC}"

# 检查docker-compose文件是否存在
if [ ! -f "${DOCKER_DIR}/docker-compose.prod.yml" ]; then
    log_error "找不到 docker-compose.prod.yml 文件"
    exit 1
fi

# Step 1: 显示当前运行的服务
log_step "1. 检查当前运行的服务..."
echo ""
cd "${DOCKER_DIR}"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Step 2: 停止所有服务
log_step "2. 停止所有服务..."
docker-compose -f docker-compose.prod.yml stop

log_info "✓ 所有服务已停止"
echo ""

# Step 3: 移除容器（可选）
read -p "是否要移除所有容器？(y/n，默认n): " remove_containers
if [ "$remove_containers" = "y" ] || [ "$remove_containers" = "Y" ]; then
    log_step "3. 移除所有容器..."
    docker-compose -f docker-compose.prod.yml rm -f
    log_info "✓ 所有容器已移除"
else
    log_info "容器已保留，可使用 'bash start-all.sh' 快速重启"
fi
echo ""

# Step 4: 显示最终状态
log_step "4. 最终状态..."
echo ""
docker-compose -f docker-compose.prod.yml ps
echo ""

# 显示总结
echo -e "${GREEN}=============================================="
echo -e "✅ 停止完成！"
echo -e "=============================================="
echo -e "${NC}"

echo "📝 后续操作："
echo "   - 重新启动: bash start-all.sh"
echo "   - 完整部署: bash deploy.sh deploy"
echo "   - 查看日志: cd docker && docker-compose -f docker-compose.prod.yml logs [服务名]"
echo ""
