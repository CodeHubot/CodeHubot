#!/bin/bash
# 验证 .env 文件是否被 Docker Compose 正确读取

echo "=========================================="
echo "🔍 验证 Docker Compose .env 文件读取"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 进入 docker 目录
cd "$(dirname "$0")"

# 1. 检查 .env 文件是否存在
echo "1️⃣  检查 .env 文件是否存在..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env 文件存在${NC}"
else
    echo -e "${RED}❌ .env 文件不存在！${NC}"
    echo "   请先复制: cp .env.example .env"
    exit 1
fi
echo ""

# 2. 检查关键环境变量
echo "2️⃣  检查关键环境变量..."
check_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env | cut -d'=' -f2)
    
    if [ -n "$var_value" ]; then
        # 脱敏显示（只显示前6个字符）
        local display_value="${var_value:0:6}***"
        echo -e "${GREEN}✅ ${var_name}${NC} = ${display_value}"
    else
        echo -e "${RED}❌ ${var_name}${NC} 未设置"
    fi
}

check_var "MYSQL_DATABASE"
check_var "MYSQL_USER"
check_var "MYSQL_PASSWORD"
check_var "REDIS_PORT"
check_var "BACKEND_PORT"
check_var "SECRET_KEY"
check_var "DASHSCOPE_API_KEY"
echo ""

# 3. 使用 docker-compose config 验证配置解析
echo "3️⃣  验证 Docker Compose 配置解析..."
if command -v docker-compose &> /dev/null; then
    echo "   运行: docker-compose -f docker-compose.prod.yml config --services"
    services=$(docker-compose -f docker-compose.prod.yml config --services 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 配置文件解析成功${NC}"
        echo "   检测到以下服务:"
        echo "$services" | sed 's/^/      - /'
    else
        echo -e "${RED}❌ 配置文件解析失败${NC}"
        echo "$services"
    fi
else
    echo -e "${YELLOW}⚠️  docker-compose 命令未找到，跳过此检查${NC}"
fi
echo ""

# 4. 检查环境变量是否被正确替换
echo "4️⃣  检查环境变量替换情况..."
if command -v docker-compose &> /dev/null; then
    echo "   检查 backend 服务的端口配置..."
    backend_port=$(docker-compose -f docker-compose.prod.yml config | grep -A 10 "backend:" | grep "ports:" -A 1 | tail -1 | grep -oP '\d+:\d+' | head -1)
    
    if [ -n "$backend_port" ]; then
        echo -e "${GREEN}✅ Backend 端口映射${NC}: $backend_port"
    else
        echo -e "${YELLOW}⚠️  无法获取端口信息${NC}"
    fi
    
    echo "   检查 Redis URL 配置..."
    redis_url=$(docker-compose -f docker-compose.prod.yml config | grep -oP 'REDIS_URL.*redis://[^"]+' | head -1)
    if [ -n "$redis_url" ]; then
        echo -e "${GREEN}✅ Redis URL${NC}: ${redis_url#REDIS_URL: }"
    fi
fi
echo ""

# 5. 安全检查
echo "5️⃣  安全检查..."
echo "   检查敏感信息是否使用默认值..."

# 检查 SECRET_KEY 是否是示例值
secret_key=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2)
if [[ "$secret_key" == *"qq_ncy9tw3YeRhoAKWHiiaqmgc4fF3uxOLr-X9eugZE"* ]]; then
    echo -e "${RED}⚠️  警告: SECRET_KEY 使用的是示例值！${NC}"
    echo "   生产环境必须修改！"
    echo "   生成新密钥: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
else
    echo -e "${GREEN}✅ SECRET_KEY 已自定义${NC}"
fi

# 检查 DASHSCOPE_API_KEY 是否是示例值
api_key=$(grep "^DASHSCOPE_API_KEY=" .env | cut -d'=' -f2)
if [[ "$api_key" == "sk-your-dashscope-api-key-here" ]]; then
    echo -e "${YELLOW}⚠️  DASHSCOPE_API_KEY 使用的是示例值${NC}"
    echo "   如需使用知识库向量化功能，请配置正确的 API 密钥"
else
    echo -e "${GREEN}✅ DASHSCOPE_API_KEY 已配置${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "✅ 验证完成！"
echo "=========================================="
echo ""
echo "💡 提示："
echo "   - 如果所有检查都通过，说明 .env 文件配置正确"
echo "   - Docker Compose 会自动读取 .env 文件"
echo "   - 启动服务: docker-compose -f docker-compose.prod.yml up -d"
echo "   - 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
