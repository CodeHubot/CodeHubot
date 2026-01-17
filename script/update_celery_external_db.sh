#!/bin/bash

################################################################################
# CodeHubot Celery Worker 更新脚本 (使用外部数据库配置)
# 用途: 快速更新 Celery Worker 服务，加载最新后端代码
# 作者: CodeHubot Team
# 日期: 2024-12-29
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印分隔线
print_separator() {
    echo "========================================"
}

# 检查是否在项目根目录
check_project_root() {
    if [ ! -f "docker/docker-compose.external-db.yml" ]; then
        print_error "未找到 docker/docker-compose.external-db.yml"
        print_error "请在项目根目录下运行此脚本"
        exit 1
    fi
}

# 主流程
main() {
    print_separator
    print_info "CodeHubot Celery Worker 更新脚本"
    print_info "使用配置: docker-compose.external-db.yml"
    print_separator
    echo ""

    # 1. 检查项目根目录
    print_info "检查项目目录..."
    check_project_root
    print_success "项目目录检查通过"
    echo ""

    # 2. 拉取最新代码
    print_separator
    print_info "正在拉取最新代码..."
    print_separator
    
    git pull origin main
    
    if [ $? -ne 0 ]; then
        print_error "代码拉取失败，请检查网络连接或 Git 仓库状态"
        exit 1
    fi
    
    print_success "代码拉取成功"
    echo ""

    # 3. 显示最新提交信息
    print_info "最新提交信息:"
    git log -1 --pretty=format:"%h - %s (%an, %ar)" 
    echo ""
    echo ""

    # 4. 重新构建 Celery Worker 镜像（包含最新代码）
    print_separator
    print_info "正在重新构建 Celery Worker 镜像..."
    print_warning "这可能需要几分钟时间，请耐心等待..."
    print_info "注意：构建期间 Celery Worker 继续运行，不会中断"
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml build --no-cache celery_worker
    
    if [ $? -ne 0 ]; then
        print_error "Celery Worker 镜像构建失败，服务继续使用旧版本"
        print_error "请检查错误信息后重试"
        exit 1
    fi
    
    print_success "Celery Worker 镜像构建成功"
    echo ""

    # 5. 检查 Celery Worker 服务状态
    print_separator
    print_info "检查 Celery Worker 当前状态..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml ps celery_worker
    echo ""

    # 6. 停止旧的 Celery Worker 服务
    print_separator
    print_info "正在停止旧的 Celery Worker 服务..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml stop celery_worker
    
    if [ $? -ne 0 ]; then
        print_warning "停止 Celery Worker 失败（可能服务未运行）"
    else
        print_success "旧的 Celery Worker 已停止"
    fi
    echo ""

    # 7. 启动新的 Celery Worker 服务
    print_separator
    print_info "正在启动新的 Celery Worker 服务..."
    print_warning "使用新构建的镜像启动服务"
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml up -d celery_worker
    
    if [ $? -ne 0 ]; then
        print_error "Celery Worker 启动失败"
        print_error "请检查日志: docker-compose -f docker/docker-compose.external-db.yml logs celery_worker"
        exit 1
    fi
    
    print_success "新的 Celery Worker 已启动"
    echo ""

    # 8. 等待服务启动
    print_info "等待 Celery Worker 完全启动..."
    sleep 5
    echo ""

    # 9. 检查服务状态
    print_separator
    print_info "检查 Celery Worker 服务状态..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml ps celery_worker
    echo ""

    # 10. 显示服务日志
    print_separator
    print_info "Celery Worker 服务日志（最后 20 行）:"
    print_separator
    docker-compose -f docker/docker-compose.external-db.yml logs --tail=20 celery_worker
    echo ""

    # 11. 完成
    print_separator
    print_success "✅ Celery Worker 更新完成！"
    print_separator
    echo ""
    
    print_info "更新流程说明:"
    echo "  - ✅ 拉取最新后端代码"
    echo "  - ✅ 重新构建 Docker 镜像（包含最新代码）"
    echo "  - ✅ 停止旧的 Celery Worker 服务"
    echo "  - ✅ 启动新的 Celery Worker 服务"
    echo "  - 📊 服务中断时间: 约 5-8 秒"
    echo ""
    
    print_info "Celery Worker 主要功能:"
    echo "  - 📄 文档异步向量化"
    echo "  - 🔄 知识库批量处理"
    echo "  - ⚙️  后台任务执行"
    echo ""
    
    print_info "验证更新:"
    echo "  - 查看实时日志: docker-compose -f docker/docker-compose.external-db.yml logs -f celery_worker"
    echo "  - 查看服务状态: docker-compose -f docker/docker-compose.external-db.yml ps celery_worker"
    echo "  - 测试文档上传: 访问知识库页面，上传测试文档"
    echo ""
    
    print_info "常见问题排查:"
    echo "  1. 如果文档上传后无法向量化:"
    echo "     - 检查 Celery Worker 日志是否有错误"
    echo "     - 确认 Redis 服务正常运行"
    echo "     - 检查后端代码是否已更新"
    echo ""
    echo "  2. 如果 Celery Worker 无法启动:"
    echo "     - 检查 Redis 连接: docker-compose -f docker/docker-compose.external-db.yml ps redis"
    echo "     - 查看详细日志: docker-compose -f docker/docker-compose.external-db.yml logs --tail=50 celery_worker"
    echo "     - 检查环境变量配置是否正确"
    echo ""
    
    print_info "其他 Celery Worker 管理命令:"
    echo "  - 停止服务: docker-compose -f docker/docker-compose.external-db.yml stop celery_worker"
    echo "  - 启动服务: docker-compose -f docker/docker-compose.external-db.yml start celery_worker"
    echo "  - 查看日志: docker-compose -f docker/docker-compose.external-db.yml logs -f celery_worker"
    echo "  - 重启服务: docker-compose -f docker/docker-compose.external-db.yml restart celery_worker"
    echo ""
}

# 捕获错误
trap 'print_error "脚本执行过程中发生错误！"; exit 1' ERR

# 执行主流程
main

exit 0

