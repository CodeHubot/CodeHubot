#!/bin/bash

# ==========================================
# CodeHubot 自动化部署脚本
# 功能：自动构建和部署所有服务
# 支持两种模式：
#   1. 标准模式（默认）：使用Docker容器部署MySQL
#   2. 外部数据库模式：使用已有的MySQL服务
# ==========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR}/docker"

# 部署模式（默认为标准模式）
DEPLOY_MODE="${DEPLOY_MODE:-standard}"  # standard 或 external-db
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

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

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行，请启动 Docker"
        exit 1
    fi
    
    log_info "依赖检查通过 ✓"
}

# 检查环境配置文件
check_env_file() {
    log_info "检查环境配置文件... (模式: ${DEPLOY_MODE})"
    
    ENV_FILE="${DOCKER_DIR}/.env"
    ENV_EXAMPLE="${DOCKER_DIR}/.env.example"
    
    # 外部数据库模式使用不同的示例文件
    if [ "${DEPLOY_MODE}" == "external-db" ]; then
        ENV_EXAMPLE="${DOCKER_DIR}/.env.external-db.example"
    fi
    
    if [ ! -f "${ENV_FILE}" ]; then
        log_warn ".env 文件不存在，从示例文件创建..."
        
        if [ ! -f "${ENV_EXAMPLE}" ]; then
            log_error "示例配置文件不存在: ${ENV_EXAMPLE}"
            exit 1
        fi
        
        cp "${ENV_EXAMPLE}" "${ENV_FILE}"
        log_warn "已创建 .env 文件，请编辑 ${ENV_FILE} 并设置必要的配置"
        log_warn "特别是 SECRET_KEY 和 INTERNAL_API_KEY 需要生成新的密钥"
        
        if [ "${DEPLOY_MODE}" == "external-db" ]; then
            log_warn "外部数据库模式还需要配置："
            log_warn "  - EXTERNAL_DB_HOST（外部MySQL主机地址）"
            log_warn "  - EXTERNAL_DB_PORT（外部MySQL端口）"
            log_warn "  - EXTERNAL_DB_USER（数据库用户名）"
            log_warn "  - EXTERNAL_DB_PASSWORD（数据库密码）"
            log_warn "  - EXTERNAL_DB_NAME（数据库名称）"
        fi
        exit 1
    fi
    
    # 检查必要的配置项
    source "${ENV_FILE}"
    
    if [ -z "${SECRET_KEY}" ] || [ "${SECRET_KEY}" == "your-very-long-secret-key-at-least-32-characters-long" ]; then
        log_error "SECRET_KEY 未配置或使用默认值，请生成新的密钥"
        log_info "生成方法: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        exit 1
    fi
    
    if [ -z "${INTERNAL_API_KEY}" ] || [ "${INTERNAL_API_KEY}" == "your-internal-api-key-change-me" ]; then
        log_error "INTERNAL_API_KEY 未配置或使用默认值，请生成新的密钥"
        log_info "生成方法: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        exit 1
    fi
    
    # 外部数据库模式需要额外检查数据库配置
    if [ "${DEPLOY_MODE}" == "external-db" ]; then
        if [ -z "${EXTERNAL_DB_HOST}" ]; then
            log_error "EXTERNAL_DB_HOST 未配置，请设置外部MySQL主机地址"
            exit 1
        fi
        
        if [ -z "${EXTERNAL_DB_USER}" ]; then
            log_error "EXTERNAL_DB_USER 未配置，请设置数据库用户名"
            exit 1
        fi
        
        if [ -z "${EXTERNAL_DB_PASSWORD}" ]; then
            log_error "EXTERNAL_DB_PASSWORD 未配置，请设置数据库密码"
            exit 1
        fi
        
        if [ -z "${EXTERNAL_DB_NAME}" ]; then
            log_error "EXTERNAL_DB_NAME 未配置，请设置数据库名称"
            exit 1
        fi
        
        log_info "外部数据库配置: ${EXTERNAL_DB_USER}@${EXTERNAL_DB_HOST}:${EXTERNAL_DB_PORT:-3306}/${EXTERNAL_DB_NAME}"
    fi
    
    log_info "环境配置文件检查通过 ✓"
}

# 生成密钥（如果需要）
generate_secrets() {
    log_info "检查密钥配置..."
    
    ENV_FILE="${DOCKER_DIR}/.env"
    
    if [ -f "${ENV_FILE}" ]; then
        source "${ENV_FILE}"
        
        # 如果密钥未配置，生成新的
        if [ -z "${SECRET_KEY}" ] || [ "${SECRET_KEY}" == "your-very-long-secret-key-at-least-32-characters-long" ]; then
            log_info "生成 SECRET_KEY..."
            NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_SECRET}/" "${ENV_FILE}"
            else
                # Linux
                sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_SECRET}/" "${ENV_FILE}"
            fi
            
            log_info "已生成 SECRET_KEY"
        fi
        
        if [ -z "${INTERNAL_API_KEY}" ] || [ "${INTERNAL_API_KEY}" == "your-internal-api-key-change-me" ]; then
            log_info "生成 INTERNAL_API_KEY..."
            NEW_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/^INTERNAL_API_KEY=.*/INTERNAL_API_KEY=${NEW_API_KEY}/" "${ENV_FILE}"
            else
                # Linux
                sed -i "s/^INTERNAL_API_KEY=.*/INTERNAL_API_KEY=${NEW_API_KEY}/" "${ENV_FILE}"
            fi
            
            log_info "已生成 INTERNAL_API_KEY"
        fi
    fi
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务... (使用: ${COMPOSE_FILE})"
    
    cd "${DOCKER_DIR}"
    
    if [ -f "${COMPOSE_FILE}" ]; then
        docker-compose -f "${COMPOSE_FILE}" down 2>/dev/null || true
        log_info "已停止现有服务"
    fi
}

# 清理卷（删除所有数据卷）
clean_volumes() {
    log_warn "警告：此操作将删除所有数据卷，包括数据库、Redis、MQTT 的所有数据！"
    read -p "确认删除所有数据卷？(yes/no): " confirm
    
    if [ "${confirm}" != "yes" ]; then
        log_info "已取消操作"
        return
    fi
    
    log_info "停止服务..."
    stop_services
    
    log_info "删除数据卷..."
    cd "${DOCKER_DIR}"
    
    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        log_info "已删除所有数据卷"
    fi
    
    # 手动删除卷（如果 docker-compose down -v 没有完全删除）
    log_info "清理残留卷..."
    docker volume ls | grep -E "(docker_mysql_data|docker_redis_data|docker_mqtt_data|docker_mqtt_logs)" | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true
    
    log_info "数据卷清理完成 ✓"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像... (模式: ${DEPLOY_MODE})"
    
    cd "${DOCKER_DIR}"
    
    # 检查是否使用国内镜像源
    source "${DOCKER_DIR}/.env" 2>/dev/null || true
    if [ "${USE_CHINA_MIRROR:-false}" = "true" ]; then
        log_info "使用国内镜像源加速构建..."
    fi
    
    log_info "构建后端服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build backend
    
    log_info "构建配置服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build config-service
    
    log_info "构建前端服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build frontend
    
    log_info "构建插件后端服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build plugin-backend-service
    
    log_info "构建插件服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build plugin-service
    
    log_info "构建MQTT独立服务镜像..."
    docker-compose -f "${COMPOSE_FILE}" build mqtt-service
    
    log_info "构建Celery Worker镜像..."
    docker-compose -f "${COMPOSE_FILE}" build celery_worker
    
    log_info "构建Flower监控镜像..."
    docker-compose -f "${COMPOSE_FILE}" build flower
    
    log_info "所有镜像构建完成 ✓"
}

# 启动服务
start_services() {
    log_info "启动所有服务... (模式: ${DEPLOY_MODE})"
    
    cd "${DOCKER_DIR}"
    
    # 加载环境变量
    source "${DOCKER_DIR}/.env"
    
    if [ "${DEPLOY_MODE}" == "external-db" ]; then
        # 外部数据库模式：只启动Redis和MQTT
        log_info "启动基础服务（Redis, MQTT）..."
        docker-compose -f "${COMPOSE_FILE}" up -d redis mqtt
        
        # 等待基础服务就绪
        log_info "等待基础服务就绪..."
        sleep 5
        
        # 测试外部数据库连接
        log_info "测试外部数据库连接: ${EXTERNAL_DB_HOST}:${EXTERNAL_DB_PORT:-3306}/${EXTERNAL_DB_NAME}"
        
        # 使用mysql客户端测试（如果可用）
        if command -v mysql &> /dev/null; then
            if mysql -h"${EXTERNAL_DB_HOST}" -P"${EXTERNAL_DB_PORT:-3306}" -u"${EXTERNAL_DB_USER}" -p"${EXTERNAL_DB_PASSWORD}" -e "USE ${EXTERNAL_DB_NAME}; SELECT 1;" &>/dev/null; then
                log_info "外部数据库连接成功 ✓"
            else
                log_error "外部数据库连接失败，请检查配置和网络连接"
                log_info "连接信息: mysql -h ${EXTERNAL_DB_HOST} -P ${EXTERNAL_DB_PORT:-3306} -u ${EXTERNAL_DB_USER} -p"
                exit 1
            fi
        else
            log_warn "未安装mysql客户端，跳过数据库连接测试"
            log_warn "如果后续服务启动失败，请检查数据库配置"
        fi
        
    else
        # 标准模式：启动MySQL, Redis, MQTT
        log_info "启动基础服务（MySQL, Redis, MQTT）..."
        docker-compose -f "${COMPOSE_FILE}" up -d mysql redis mqtt
        
        # 等待基础服务就绪
        log_info "等待基础服务就绪..."
        sleep 10
        
        # 检查 MySQL 是否就绪
        log_info "检查 MySQL 服务..."
        for i in {1..30}; do
            if docker-compose -f "${COMPOSE_FILE}" exec -T mysql mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-root_password}" --silent 2>/dev/null; then
                log_info "MySQL 已就绪 ✓"
                break
            fi
            if [ $i -eq 30 ]; then
                log_error "MySQL 启动超时"
                exit 1
            fi
            sleep 2
        done
        
        # 初始化数据库（如果需要）
        log_info "检查数据库初始化..."
        sleep 5  # 等待 MySQL 完全启动
        
        # 检查数据库是否已初始化
        if ! docker-compose -f "${COMPOSE_FILE}" exec -T mysql mysql -u"${MYSQL_USER:-aiot_user}" -p"${MYSQL_PASSWORD:-aiot_password}" "${MYSQL_DATABASE:-aiot_admin}" -e "SHOW TABLES LIKE 'aiot_core_users';" 2>/dev/null | grep -q "aiot_core_users"; then
            log_info "初始化数据库..."
            if [ -f "${SCRIPT_DIR}/SQL/init_database.sql" ]; then
                docker-compose -f "${COMPOSE_FILE}" exec -T mysql mysql -u"${MYSQL_USER:-aiot_user}" -p"${MYSQL_PASSWORD:-aiot_password}" "${MYSQL_DATABASE:-aiot_admin}" < "${SCRIPT_DIR}/SQL/init_database.sql" 2>/dev/null || {
                    log_warn "数据库初始化脚本执行失败，可能数据库已存在，继续..."
                }
                log_info "数据库初始化完成 ✓"
            else
                log_warn "数据库初始化脚本不存在: ${SCRIPT_DIR}/SQL/init_database.sql"
            fi
        else
            log_info "数据库已存在，跳过初始化"
        fi
    fi
    
    # 启动应用服务
    log_info "启动应用服务..."
    log_info "  - Backend (HTTP API)"
    log_info "  - Config Service (配置服务)"
    log_info "  - Frontend (前端)"
    log_info "  - Plugin Backend Service (插件后端服务)"
    log_info "  - Plugin Service (插件服务)"
    log_info "  - MQTT Service (设备消息处理)"
    log_info "  - Celery Worker (异步任务)"
    log_info "  - Flower (任务监控)"
    
    if [ "${DEPLOY_MODE}" == "external-db" ]; then
        # 外部数据库模式：不启动phpMyAdmin
        docker-compose -f "${COMPOSE_FILE}" up -d \
            backend \
            config-service \
            frontend \
            plugin-backend-service \
            plugin-service \
            mqtt-service \
            celery_worker \
            flower
    else
        # 标准模式：启动phpMyAdmin
        log_info "  - phpMyAdmin (数据库管理)"
        docker-compose -f "${COMPOSE_FILE}" up -d \
            backend \
            config-service \
            frontend \
            plugin-backend-service \
            plugin-service \
            mqtt-service \
            celery_worker \
            flower \
            phpmyadmin
    fi
    
    log_info "所有服务启动完成 ✓"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态... (模式: ${DEPLOY_MODE})"
    
    cd "${DOCKER_DIR}"
    
    docker-compose -f "${COMPOSE_FILE}" ps
    
    log_info ""
    log_info "服务健康检查..."
    
    # 加载环境变量
    source "${DOCKER_DIR}/.env"
    
    # 检查后端服务
    if curl -f http://localhost:${BACKEND_PORT:-8000}/health &>/dev/null; then
        log_info "后端服务: ✓ 健康"
    elif docker-compose -f "${COMPOSE_FILE}" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" >/dev/null 2>&1; then
        log_info "后端服务: ✓ 健康 (仅内部网络访问)"
    else
        log_warn "后端服务: ✗ 未响应（可能需要等待服务完全启动）"
    fi
    
    # 检查配置服务
    if curl -f http://localhost:${CONFIG_SERVICE_PORT:-8001}/health &>/dev/null; then
        log_info "配置服务: ✓ 健康"
    else
        log_warn "配置服务: ✗ 未响应（可能需要等待服务完全启动）"
    fi
    
    # 检查前端服务
    if curl -f http://localhost:${FRONTEND_PORT:-80}/ &>/dev/null; then
        log_info "前端服务: ✓ 健康"
    else
        log_warn "前端服务: ✗ 未响应（可能需要等待服务完全启动）"
    fi
    
    # 检查插件后端服务（内部服务，不对外暴露）
    if docker-compose -f "${COMPOSE_FILE}" exec -T plugin-backend-service python -c "import urllib.request; urllib.request.urlopen('http://localhost:9002/health')" >/dev/null 2>&1; then
        log_info "插件后端服务: ✓ 健康"
    else
        log_warn "插件后端服务: ✗ 未响应（可能需要等待服务完全启动）"
    fi
    
    # 检查插件服务
    if curl -f http://localhost:${PLUGIN_SERVICE_PORT:-9000}/ &>/dev/null; then
        log_info "插件服务: ✓ 健康"
    else
        log_warn "插件服务: ✗ 未响应（可能需要等待服务完全启动）"
    fi
    
    # 检查MQTT服务
    if docker-compose -f "${COMPOSE_FILE}" ps mqtt-service | grep -q "Up"; then
        log_info "MQTT服务: ✓ 运行中"
    else
        log_warn "MQTT服务: ✗ 未运行"
    fi
    
    # 检查Celery Worker
    if docker-compose -f "${COMPOSE_FILE}" ps celery_worker | grep -q "Up"; then
        log_info "Celery Worker: ✓ 运行中"
    else
        log_warn "Celery Worker: ✗ 未运行"
    fi
    
    # 检查Flower监控（检查进程和端口）
    if ! docker-compose -f "${COMPOSE_FILE}" ps flower | grep -q "Up"; then
        log_warn "Flower监控: ✗ 容器未运行"
    else
        # 检查进程
        if docker-compose -f "${COMPOSE_FILE}" exec -T flower pgrep -f "celery.*flower" >/dev/null 2>&1; then
            log_info "Flower监控: ✓ 运行中"
            log_info "  访问地址: http://localhost:${FLOWER_PORT:-5555}/flower"
            log_info "  默认账号: admin / 密码: admin"
            log_info "  修改账号: 在.env中设置 FLOWER_BASIC_AUTH=用户名:密码"
        # 检查端口（即使进程检查失败，端口监听也说明服务在运行）
        elif command -v nc >/dev/null 2>&1 && nc -z localhost ${FLOWER_PORT:-5555} 2>/dev/null; then
            log_info "Flower监控: ✓ 运行中（端口已监听）"
            log_info "  访问地址: http://localhost:${FLOWER_PORT:-5555}/flower"
            log_info "  默认账号: admin / 密码: admin"
            log_info "  修改账号: 在.env中设置 FLOWER_BASIC_AUTH=用户名:密码"
        # 检查容器日志中是否有启动成功的标志
        elif docker-compose -f "${COMPOSE_FILE}" logs flower 2>&1 | grep -q "Visit me at"; then
            log_info "Flower监控: ✓ 运行中（日志显示已启动）"
            log_info "  访问地址: http://localhost:${FLOWER_PORT:-5555}/flower"
            log_info "  默认账号: admin / 密码: admin"
            log_info "  修改账号: 在.env中设置 FLOWER_BASIC_AUTH=用户名:密码"
        else
            log_warn "Flower监控: ✗ 可能未完全启动"
            log_warn "  查看日志: docker-compose -f ${COMPOSE_FILE} logs flower"
            log_warn "  如果日志显示'Visit me at'，说明服务已启动，请稍等片刻"
        fi
    fi
    
    # 只在标准模式下检查 phpMyAdmin
    if [ "${DEPLOY_MODE}" != "external-db" ]; then
        if curl -f http://localhost:${PHPMYADMIN_PORT:-8081}/ &>/dev/null; then
            log_info "phpMyAdmin: ✓ 健康"
        else
            log_warn "phpMyAdmin: ✗ 未响应（可能需要等待服务完全启动）"
        fi
    fi
}

# 显示服务信息
show_info() {
    log_info ""
    log_info "=========================================="
    log_info "部署完成！(模式: ${DEPLOY_MODE})"
    log_info "=========================================="
    log_info ""
    # 加载环境变量
    source "${DOCKER_DIR}/.env" 2>/dev/null || true
    
    log_info "服务访问地址："
    log_info "  前端:          http://localhost:${FRONTEND_PORT:-80}"
    log_info "  后端API:       http://localhost:${BACKEND_PORT:-8000}"
    log_info "  配置服务:      http://localhost:${CONFIG_SERVICE_PORT:-8001}"
    log_info "  插件服务:      http://localhost:${PLUGIN_SERVICE_PORT:-9000}"
    log_info "  Flower监控:    http://localhost:${FLOWER_PORT:-5555}/flower"
    log_info "                (默认账号: admin / 密码: admin)"
    log_info ""
    log_info "内部服务（仅容器内访问）："
    log_info "  插件后端服务:  http://plugin-backend-service:9002"
    
    if [ "${DEPLOY_MODE}" != "external-db" ]; then
        log_info "  phpMyAdmin:    http://localhost:${PHPMYADMIN_PORT:-8081}"
    fi
    
    log_info ""
    log_info "后台服务："
    log_info "  MQTT服务:      处理设备消息（无HTTP接口）"
    log_info "  Celery Worker: 处理异步任务（无HTTP接口）"
    log_info ""
    log_info "基础服务："
    
    if [ "${DEPLOY_MODE}" == "external-db" ]; then
        log_info "  MySQL:         外部数据库 (${EXTERNAL_DB_HOST}:${EXTERNAL_DB_PORT:-3306}/${EXTERNAL_DB_NAME})"
    else
        log_info "  MySQL:         仅内部访问（不对外暴露，安全考虑）"
        log_info "                 可通过phpMyAdmin访问: http://localhost:${PHPMYADMIN_PORT:-8081}"
    fi
    
    log_info "  Redis:         仅内部访问（不对外暴露，安全考虑）"
    log_info "  MQTT Broker:   localhost:${MQTT_PORT:-1883}"
    log_info ""
    log_info "管理命令："
    log_info "  查看日志: cd docker && docker-compose -f ${COMPOSE_FILE} logs -f [服务名]"
    log_info "  停止服务: cd docker && docker-compose -f ${COMPOSE_FILE} down"
    log_info "  重启服务: cd docker && docker-compose -f ${COMPOSE_FILE} restart [服务名]"
    log_info ""
}

# 主函数
main() {
    log_info "=========================================="
    log_info "CodeHubot 自动化部署脚本"
    log_info "=========================================="
    log_info ""
    
    # 解析命令行参数
    ACTION="${1:-deploy}"
    
    # 处理外部数据库模式的命令
    case "${ACTION}" in
        deploy-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="deploy"
            ;;
        build-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="build"
            ;;
        start-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="start"
            ;;
        stop-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="stop"
            ;;
        restart-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="restart"
            ;;
        status-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="status"
            ;;
        logs-external-db)
            DEPLOY_MODE="external-db"
            COMPOSE_FILE="docker-compose.external-db.yml"
            ACTION="logs"
            ;;
    esac
    
    case "${ACTION}" in
        deploy)
            check_dependencies
            check_env_file
            generate_secrets
            stop_services
            build_images
            start_services
            log_info "等待所有服务完全启动..."
            # 倒计时30秒
            for i in {30..1}; do
                printf "\r${GREEN}[INFO]${NC} 等待服务启动中... 剩余 ${YELLOW}%2d${NC} 秒" $i
                sleep 1
            done
            echo ""
            check_services
            show_info
            ;;
        build)
            check_dependencies
            build_images
            ;;
        start)
            check_dependencies
            check_env_file
            start_services
            log_info "等待所有服务完全启动..."
            # 倒计时30秒
            for i in {30..1}; do
                printf "\r${GREEN}[INFO]${NC} 等待服务启动中... 剩余 ${YELLOW}%2d${NC} 秒" $i
                sleep 1
            done
            echo ""
            check_services
            show_info
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_dependencies
            check_env_file
            stop_services
            start_services
            log_info "等待所有服务完全启动..."
            # 倒计时30秒
            for i in {30..1}; do
                printf "\r${GREEN}[INFO]${NC} 等待服务启动中... 剩余 ${YELLOW}%2d${NC} 秒" $i
                sleep 1
            done
            echo ""
            check_services
            show_info
            ;;
        status)
            check_dependencies
            check_services
            ;;
        logs)
            cd "${DOCKER_DIR}"
            docker-compose -f "${COMPOSE_FILE}" logs -f "${2:-}"
            ;;
        clean)
            check_dependencies
            clean_volumes
            ;;
        *)
            echo "用法: $0 {deploy|build|start|stop|restart|status|logs [服务名]|clean}"
            echo ""
            echo "标准模式命令（使用Docker MySQL）："
            echo "  deploy  - 完整部署（停止、构建、启动）"
            echo "  build   - 仅构建镜像"
            echo "  start   - 启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  status  - 查看服务状态"
            echo "  logs    - 查看日志（可指定服务名）"
            echo "  clean   - 删除所有数据卷（会清空所有数据）"
            echo ""
            echo "外部数据库模式命令（使用已有MySQL）："
            echo "  deploy-external-db  - 完整部署（不包含MySQL容器）"
            echo "  build-external-db   - 仅构建镜像"
            echo "  start-external-db   - 启动服务"
            echo "  stop-external-db    - 停止服务"
            echo "  restart-external-db - 重启服务"
            echo "  status-external-db  - 查看服务状态"
            echo "  logs-external-db    - 查看日志（可指定服务名）"
            echo ""
            echo "外部数据库模式使用前："
            echo "  1. 复制环境配置: cp docker/.env.external-db.example docker/.env"
            echo "  2. 编辑 docker/.env，配置外部数据库连接信息"
            echo "  3. 确保外部数据库已创建并导入了初始结构（SQL/init_database.sql）"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"

