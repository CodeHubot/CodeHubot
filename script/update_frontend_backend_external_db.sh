#!/bin/bash

################################################################################
# CodeHubot 前端+后端更新脚本 (使用外部数据库配置)
# 用途: 同时更新 Frontend 和 Backend 服务
# 说明: 
#   - 包含: frontend, backend
#   - 不包含: celery-worker (请使用 update_celery_external_db.sh)
# 使用: docker-compose.external-db.yml
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
    print_info "CodeHubot 前端+后端更新脚本"
    print_info "更新服务: Frontend + Backend"
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

    # 4. 构建后端镜像（在服务运行时构建）
    print_separator
    print_info "正在重新构建后端镜像..."
    print_warning "这可能需要几分钟时间，请耐心等待..."
    print_info "注意：构建期间后端服务继续运行，不会中断"
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml build --no-cache backend
    
    if [ $? -ne 0 ]; then
        print_error "后端镜像构建失败，服务继续使用旧版本"
        print_error "请检查错误信息后重试"
        exit 1
    fi
    
    print_success "后端镜像构建成功"
    echo ""

    # 5. 构建前端镜像
    print_separator
    print_info "正在重新构建前端镜像..."
    print_warning "这可能需要几分钟时间，请耐心等待..."
    print_info "注意：构建期间前端服务继续运行，不会中断"
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml build --no-cache frontend
    
    if [ $? -ne 0 ]; then
        print_error "前端镜像构建失败，服务继续使用旧版本"
        print_error "请检查错误信息后重试"
        exit 1
    fi
    
    print_success "前端镜像构建成功"
    echo ""

    # 6. 停止旧服务
    print_separator
    print_info "正在停止旧服务..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml stop backend frontend
    
    if [ $? -ne 0 ]; then
        print_warning "停止服务失败（可能服务未运行）"
    else
        print_success "旧服务已停止"
    fi
    echo ""

    # 7. 启动新服务
    print_separator
    print_info "正在启动新服务..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml up -d backend frontend
    
    if [ $? -ne 0 ]; then
        print_error "服务启动失败"
        print_error "请检查日志: docker-compose -f docker/docker-compose.external-db.yml logs backend frontend"
        exit 1
    fi
    
    print_success "新服务已启动"
    echo ""

    # 8. 等待服务启动
    print_info "等待服务完全启动..."
    sleep 8
    echo ""

    # 9. 检查服务状态
    print_separator
    print_info "检查服务状态..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml ps backend frontend
    echo ""

    # 10. 显示服务日志
    print_separator
    print_info "后端服务日志（最后 10 行）:"
    print_separator
    docker-compose -f docker/docker-compose.external-db.yml logs --tail=10 backend
    echo ""
    
    print_separator
    print_info "前端服务日志（最后 10 行）:"
    print_separator
    docker-compose -f docker/docker-compose.external-db.yml logs --tail=10 frontend
    echo ""

    # 11. 完成
    print_separator
    print_success "✅ 前后端更新完成！"
    print_separator
    echo ""
    
    print_info "更新流程说明:"
    echo "  - ✅ 先构建新镜像（旧服务继续运行）"
    echo "  - ✅ 构建成功后停止旧服务"
    echo "  - ✅ 立即启动新服务"
    echo "  - 📊 服务中断时间: 约 8-10 秒"
    echo ""
    
    print_info "验证更新:"
    echo "  - 后端API: http://localhost:8000 (或你的服务器地址)"
    echo "  - 前端页面: http://localhost (或你的服务器地址)"
    echo "  - 查看实时日志: docker-compose -f docker/docker-compose.external-db.yml logs -f backend frontend"
    echo "  - 查看服务状态: docker-compose -f docker/docker-compose.external-db.yml ps"
    echo ""
    
    print_info "如果页面没有更新，请尝试:"
    echo "  1. 清除浏览器缓存（Ctrl+F5 或 Cmd+Shift+R）"
    echo "  2. 使用隐私/无痕浏览模式访问"
    echo ""
    
    print_info "其他服务管理命令:"
    echo "  - 重启服务: docker-compose -f docker/docker-compose.external-db.yml restart backend frontend"
    echo "  - 查看所有服务: docker-compose -f docker/docker-compose.external-db.yml ps"
    echo "  - 停止所有服务: docker-compose -f docker/docker-compose.external-db.yml stop"
    echo ""
    
    print_info "如需更新其他服务:"
    echo "  - Celery Worker: ./update_celery_external_db.sh"
    echo "  - 仅前端: ./update_frontend_external_db.sh"
    echo ""
}

# 捕获错误
trap 'print_error "脚本执行过程中发生错误！"; exit 1' ERR

# 执行主流程
main

exit 0

