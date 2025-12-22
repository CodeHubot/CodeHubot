#!/bin/bash

################################################################################
# CodeHubot 前端更新脚本 (使用外部数据库配置)
# 用途: 快速更新前端服务，使用 docker-compose.external-db.yml
# 作者: CodeHubot Team
# 日期: 2024-12-22
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
    print_info "CodeHubot 前端更新脚本 (外部数据库配置)"
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

    # 4. 重新构建前端镜像（在服务运行时构建，减少中断时间）
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

    # 5. 停止旧的前端服务
    print_separator
    print_info "正在停止旧的前端服务..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml stop frontend
    
    if [ $? -ne 0 ]; then
        print_warning "停止前端服务失败（可能服务未运行）"
    else
        print_success "旧的前端服务已停止"
    fi
    echo ""

    # 6. 启动新的前端服务
    print_separator
    print_info "正在启动新的前端服务..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml up -d frontend
    
    if [ $? -ne 0 ]; then
        print_error "前端服务启动失败"
        print_error "请检查日志: docker-compose -f docker/docker-compose.external-db.yml logs frontend"
        exit 1
    fi
    
    print_success "新的前端服务已启动"
    echo ""

    # 7. 等待服务启动
    print_info "等待前端服务完全启动..."
    sleep 5
    echo ""

    # 8. 检查服务状态
    print_separator
    print_info "检查前端服务状态..."
    print_separator
    
    docker-compose -f docker/docker-compose.external-db.yml ps frontend
    echo ""

    # 9. 显示前端日志
    print_separator
    print_info "前端服务日志（最后 20 行）:"
    print_separator
    docker-compose -f docker/docker-compose.external-db.yml logs --tail=20 frontend
    echo ""

    # 10. 完成
    print_separator
    print_success "✅ 前端更新完成！"
    print_separator
    echo ""
    
    print_info "更新流程说明:"
    echo "  - ✅ 先构建新镜像（旧服务继续运行）"
    echo "  - ✅ 构建成功后停止旧服务"
    echo "  - ✅ 立即启动新服务"
    echo "  - 📊 服务中断时间: 约 5-10 秒"
    echo ""
    
    print_info "验证更新:"
    echo "  - 访问前端页面: http://localhost (或你的服务器地址)"
    echo "  - 查看实时日志: docker-compose -f docker/docker-compose.external-db.yml logs -f frontend"
    echo "  - 查看服务状态: docker-compose -f docker/docker-compose.external-db.yml ps"
    echo ""
    
    print_info "如果页面没有更新，请尝试:"
    echo "  1. 清除浏览器缓存（Ctrl+F5 或 Cmd+Shift+R）"
    echo "  2. 使用隐私/无痕浏览模式访问"
    echo ""
}

# 捕获错误
trap 'print_error "脚本执行过程中发生错误！"; exit 1' ERR

# 执行主流程
main

exit 0

