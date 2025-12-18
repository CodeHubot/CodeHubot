# Docker 容器化部署

## 概述

CodeHubot 平台采用 Docker 容器化技术实现一键部署,所有服务通过 Docker Compose 编排管理。这确保了开发、测试、生产环境的一致性。

## Docker 架构

### 容器组成

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: aiot-network              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Frontend   │  │   Backend    │  │     MQTT     │      │
│  │  Nginx:80    │  │  Python:8000 │  │  Mosquitto   │      │
│  │              │  │              │  │  1883/9001   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    MySQL     │  │    Redis     │  │    Celery    │      │
│  │    3306      │  │    6379      │  │   Worker     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Plugin-      │  │   Config     │                        │
│  │ Service      │  │   Service    │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
CodeHubot/
├── docker/                          # Docker 配置目录
│   ├── docker-compose.yml           # 开发环境编排
│   ├── docker-compose.prod.yml      # 生产环境编排
│   ├── docker-compose.plugin.yml    # 插件服务编排
│   ├── .env.example                 # 环境变量示例
│   ├── mosquitto.conf               # MQTT 配置
│   └── verify-env.sh                # 环境检查脚本
├── backend/
│   ├── Dockerfile                   # 后端镜像构建
│   ├── requirements.txt             # Python 依赖
│   └── ...
├── frontend/
│   ├── Dockerfile                   # 前端镜像构建
│   ├── nginx.conf                   # Nginx 配置
│   └── ...
├── service/
│   ├── mqtt-service/
│   │   └── Dockerfile
│   ├── celery-service/
│   │   └── Dockerfile
│   └── ...
├── deploy.sh                        # 一键部署脚本
├── start-all.sh                     # 启动所有服务
├── stop-all.sh                      # 停止所有服务
└── update_and_deploy.sh             # 更新并重新部署
```

## Dockerfile 配置

### 后端 Dockerfile

**文件位置**: `backend/Dockerfile`

```dockerfile
# 使用官方 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**优化点**：
- ✅ 使用 slim 镜像减小体积
- ✅ 分层缓存优化构建速度
- ✅ 清理 apt 缓存
- ✅ 使用 `--no-cache-dir` 减小镜像

### 前端 Dockerfile

**文件位置**: `frontend/Dockerfile`

```dockerfile
# 第一阶段：构建
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源码
COPY . .

# 构建生产版本
RUN npm run build

# 第二阶段：运行
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
```

**优化点**：
- ✅ 多阶段构建减小最终镜像
- ✅ 使用 alpine 镜像
- ✅ 使用 `npm ci` 确保依赖一致
- ✅ 仅复制构建产物

## Docker Compose 配置

### 开发环境配置

**文件位置**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: codehubot-mysql
    environment:
      MYSQL_DATABASE: aiot_admin
      MYSQL_USER: aiot_user
      MYSQL_PASSWORD: aiot_password
      MYSQL_ROOT_PASSWORD: root_password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init-databases.sql:/docker-entrypoint-initdb.d/init-databases.sql:ro
    ports:
      - "3306:3306"
    command: --default-authentication-plugin=mysql_native_password
    networks:
      - aiot-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存服务
  redis:
    image: redis:7-alpine
    container_name: codehubot-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - aiot-network
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # MQTT 服务
  mqtt:
    image: eclipse-mosquitto:2.0
    container_name: codehubot-mqtt
    ports:
      - "1883:1883"  # MQTT
      - "9001:9001"  # WebSocket
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - mqtt_data:/mosquitto/data
      - mqtt_logs:/mosquitto/log
    networks:
      - aiot-network
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-h", "localhost", "-t", "$$SYS/health", "-C", "1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 后端服务
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: codehubot-backend
    env_file:
      - ../backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ../backend:/app
    networks:
      - aiot-network
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # 前端服务
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: codehubot-frontend
    ports:
      - "3000:80"
    networks:
      - aiot-network
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
  mqtt_data:
  mqtt_logs:

networks:
  aiot-network:
    driver: bridge
```

### 生产环境配置

**文件位置**: `docker/docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: codehubot-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # SSL 证书
      - frontend_static:/usr/share/nginx/html
    networks:
      - aiot-network
    depends_on:
      - backend
      - frontend
    restart: always

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    deploy:
      replicas: 2  # 2个实例实现负载均衡
      resources:
        limits:
          cpus: '1'
          memory: 2G
    environment:
      - ENV=production
    restart: always

  # ... 其他服务配置类似
```

## 环境变量配置

### .env 文件

**文件位置**: `backend/.env`

```bash
# 数据库配置
DB_HOST=mysql
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password
DB_NAME=aiot_admin

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# MQTT 配置
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 应用配置
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]

# 大模型配置
DEEPSEEK_API_KEY=your-api-key
QIANWEN_API_KEY=your-api-key
```

### 环境变量验证

**文件位置**: `docker/verify-env.sh`

```bash
#!/bin/bash

# 检查必需的环境变量
required_vars=(
  "DB_HOST"
  "DB_PORT"
  "DB_USER"
  "DB_PASSWORD"
  "SECRET_KEY"
)

missing_vars=()

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    missing_vars+=("$var")
  fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
  echo "❌ 缺少必需的环境变量:"
  printf '%s\n' "${missing_vars[@]}"
  exit 1
fi

echo "✅ 环境变量检查通过"
```

## 部署脚本

### 一键部署

**文件位置**: `deploy.sh`

```bash
#!/bin/bash

set -e

echo "🚀 开始部署 CodeHubot 平台..."

# 1. 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未安装 Docker Compose"
    exit 1
fi

# 2. 检查环境变量
if [ ! -f "backend/.env" ]; then
    echo "⚠️  未找到 .env 文件，从示例复制..."
    cp backend/env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件配置必要参数"
    exit 1
fi

# 3. 停止现有容器
echo "🛑 停止现有容器..."
docker-compose -f docker/docker-compose.yml down

# 4. 拉取最新镜像
echo "📥 拉取最新镜像..."
docker-compose -f docker/docker-compose.yml pull

# 5. 构建自定义镜像
echo "🔨 构建应用镜像..."
docker-compose -f docker/docker-compose.yml build

# 6. 启动服务
echo "🚀 启动服务..."
docker-compose -f docker/docker-compose.yml up -d

# 7. 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 10

# 8. 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker/docker-compose.yml ps

# 9. 显示访问地址
echo ""
echo "✅ 部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 前端访问: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### 更新部署

**文件位置**: `update_and_deploy.sh`

```bash
#!/bin/bash

set -e

echo "🔄 开始更新部署..."

# 1. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 2. 备份数据库
echo "💾 备份数据库..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec codehubot-mysql mysqldump -u root -proot_password aiot_admin > "backups/$BACKUP_FILE"
echo "✅ 数据库已备份: $BACKUP_FILE"

# 3. 重新构建并启动
echo "🔨 重新构建镜像..."
docker-compose -f docker/docker-compose.yml up -d --build

# 4. 执行数据库迁移（如果有）
if [ -d "SQL/update" ]; then
    echo "📊 检查数据库更新..."
    for sql_file in SQL/update/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "执行: $sql_file"
            docker exec -i codehubot-mysql mysql -u root -proot_password aiot_admin < "$sql_file"
        fi
    done
fi

# 5. 重启服务
echo "🔄 重启服务..."
docker-compose -f docker/docker-compose.yml restart

echo "✅ 更新部署完成！"
```

## 常用命令

### 启动服务

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 启动特定服务
docker-compose -f docker/docker-compose.yml up -d backend

# 前台启动（查看日志）
docker-compose -f docker/docker-compose.yml up
```

### 停止服务

```bash
# 停止所有服务
docker-compose -f docker/docker-compose.yml down

# 停止并删除卷（⚠️ 会删除数据）
docker-compose -f docker/docker-compose.yml down -v

# 停止特定服务
docker-compose -f docker/docker-compose.yml stop backend
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker/docker-compose.yml logs

# 查看特定服务日志
docker-compose -f docker/docker-compose.yml logs backend

# 实时查看日志
docker-compose -f docker/docker-compose.yml logs -f backend

# 查看最近100行日志
docker-compose -f docker/docker-compose.yml logs --tail=100 backend
```

### 进入容器

```bash
# 进入后端容器
docker exec -it codehubot-backend bash

# 进入数据库容器
docker exec -it codehubot-mysql mysql -u root -p

# 进入 Redis 容器
docker exec -it codehubot-redis redis-cli
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker/docker-compose.yml restart

# 重启特定服务
docker-compose -f docker/docker-compose.yml restart backend
```

### 查看服务状态

```bash
# 查看服务运行状态
docker-compose -f docker/docker-compose.yml ps

# 查看资源使用
docker stats
```

## 数据持久化

### 卷挂载

```yaml
volumes:
  # 数据库数据持久化
  mysql_data:
    driver: local
  
  # Redis 数据持久化
  redis_data:
    driver: local
  
  # MQTT 数据持久化
  mqtt_data:
    driver: local
  
  # MQTT 日志
  mqtt_logs:
    driver: local
```

### 数据备份

```bash
# 备份 MySQL
docker exec codehubot-mysql mysqldump -u root -proot_password aiot_admin > backup.sql

# 备份 Redis
docker exec codehubot-redis redis-cli SAVE
docker cp codehubot-redis:/data/dump.rdb ./backup/

# 备份卷
docker run --rm -v mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz /data
```

### 数据恢复

```bash
# 恢复 MySQL
docker exec -i codehubot-mysql mysql -u root -proot_password aiot_admin < backup.sql

# 恢复 Redis
docker cp backup/dump.rdb codehubot-redis:/data/
docker-compose restart redis
```

## 健康检查

### Docker Compose 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s      # 每30秒检查一次
  timeout: 10s       # 超时时间10秒
  retries: 3         # 重试3次
  start_period: 40s  # 启动后40秒开始检查
```

### 后端健康检查端点

```python
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": check_database_connection(),
            "redis": check_redis_connection(),
            "mqtt": check_mqtt_connection()
        }
    }
```

## 网络配置

### 自定义网络

```yaml
networks:
  aiot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 服务间通信

```python
# 使用服务名作为主机名
DB_HOST=mysql  # 而不是 localhost
REDIS_HOST=redis
MQTT_BROKER_HOST=mqtt
```

## 生产环境优化

### 1. 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 2. 日志配置

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. 重启策略

```yaml
services:
  backend:
    restart: always  # 总是重启
    # restart: unless-stopped  # 除非手动停止
    # restart: on-failure  # 失败时重启
```

### 4. 安全加固

```yaml
services:
  mysql:
    environment:
      # 使用强密码
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
    secrets:
      - mysql_root_password

secrets:
  mysql_root_password:
    file: ./secrets/mysql_root_password.txt
```

## 常见问题

### 1. 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend

# 检查容器状态
docker ps -a

# 查看容器配置
docker inspect codehubot-backend
```

### 2. 网络连接问题

```bash
# 检查网络
docker network ls
docker network inspect aiot-network

# 测试服务连通性
docker exec codehubot-backend ping mysql
```

### 3. 数据库连接失败

```bash
# 检查 MySQL 是否就绪
docker exec codehubot-mysql mysqladmin ping

# 检查环境变量
docker exec codehubot-backend env | grep DB_
```

### 4. 端口冲突

```bash
# 查看端口占用
lsof -i:3306

# 修改 docker-compose.yml 中的端口映射
ports:
  - "3307:3306"  # 将主机端口改为 3307
```

## 相关文档

- [Nginx配置](./Nginx配置.md) - Nginx 反向代理配置
- [环境配置](./环境配置.md) - 环境变量详细说明
- [服务监控](./服务监控.md) - 监控和日志管理
- [备份恢复](./备份恢复.md) - 数据备份和恢复策略
