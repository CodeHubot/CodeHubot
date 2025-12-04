#!/bin/bash
# 验证所有服务状态

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 完整验证所有服务..."
echo ""

# 1. 容器状态
echo "=== 1. 容器状态 ==="
docker ps --format "table {{.Names}}\t{{.Status}}" | grep codehubot
echo ""

# 2. Celery Worker详细日志
echo "=== 2. Celery Worker 日志（最近20行）==="
docker logs codehubot-celery-worker 2>&1 | tail -20
echo ""

# 3. Flower日志
echo "=== 3. Flower 日志（最近20行）==="
docker logs codehubot-flower 2>&1 | tail -20
echo ""

# 4. 验证Flower访问
echo "=== 4. 验证Flower访问 ==="
echo "等待Flower完全启动（10秒）..."
sleep 10

if curl -s http://localhost:5555/flower > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Flower可访问: http://localhost:5555/flower${NC}"
else
    echo -e "${YELLOW}⚠️  Flower暂时不可访问，可能还在启动中${NC}"
    echo "请稍后访问浏览器: http://localhost:5555/flower"
fi
echo ""

# 5. 验证其他关键服务
echo "=== 5. 验证其他服务 ==="

# Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: http://localhost:8000${NC}"
elif docker exec codehubot-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: 运行正常 (仅内部网络访问)${NC}"
else
    echo -e "${RED}❌ Backend不可访问${NC}"
fi

# Frontend
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: http://localhost:8080${NC}"
else
    echo -e "${RED}❌ Frontend不可访问${NC}"
fi

# Config Service
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Config Service: http://localhost:8001${NC}"
else
    echo -e "${RED}❌ Config Service不可访问${NC}"
fi

# Plugin Service
if curl -s http://localhost:9000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Plugin Service: http://localhost:9000${NC}"
else
    echo -e "${RED}❌ Plugin Service不可访问${NC}"
fi

# phpMyAdmin
if curl -s http://localhost:8081/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ phpMyAdmin: http://localhost:8081${NC}"
else
    echo -e "${RED}❌ phpMyAdmin不可访问${NC}"
fi

echo ""
echo "🎊 验证完成！"

