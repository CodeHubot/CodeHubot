# 开发环境服务配置说明

## 概述

`docker-compose.dev-services.yml` 是专门为本地开发前后端源代码而设计的配置文件。

**特点：**
- 只启动支持服务（MySQL、Redis、MQTT、Celery等）
- **不启动前后端容器**，前后端需要在本地手动启动以实现热更新调试
- 开放所有必要端口供本地代码访问
- 使用独立的数据卷和网络，不影响生产环境

## 快速开始

### 1. 启动开发环境服务

```bash
# 方式1: 使用部署脚本（推荐）
bash script/deploy.sh start-dev-services

# 方式2: 直接使用 docker-compose
cd docker
docker-compose -f docker-compose.dev-services.yml up -d
```

### 2. 启动后端（在新的终端）

```bash
cd backend

# 确保已安装依赖
pip install -r requirements.txt

# 启动后端（带热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端访问地址：http://localhost:8000

### 3. 启动前端（在新的终端）

```bash
cd frontend

# 确保已安装依赖
npm install

# 启动前端开发服务器
npm run dev
```

前端访问地址：http://localhost:5173 (Vite默认端口)

## 已启动的支持服务

### 基础服务

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| MySQL | codehubot-mysql-dev | 3306 | 数据库服务 |
| Redis | codehubot-redis-dev | 6379 | 缓存服务 |
| MQTT | codehubot-mqtt-dev | 1883, 9001 | 消息队列 |

### 业务服务

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| MQTT Service | codehubot-mqtt-service-dev | - | 设备消息处理 |
| Celery Worker | codehubot-celery-worker-dev | - | 异步任务处理 |
| Flower | codehubot-flower-dev | 5555 | Celery监控面板 |
| Config Service | codehubot-config-service-dev | 8001 | 配置管理服务 |
| Plugin Backend | codehubot-plugin-backend-service-dev | 9002 | 插件后端服务 |
| Plugin Service | codehubot-plugin-service-dev | 9000 | 插件服务 |
| phpMyAdmin | codehubot-phpmyadmin-dev | 8081 | 数据库管理界面 |

## 服务访问地址

### Web界面

- **Flower（Celery监控）**: http://localhost:5555
  - 用户名: admin
  - 密码: admin

- **phpMyAdmin（数据库管理）**: http://localhost:8081
  - 服务器: mysql
  - 用户名: aiot_user
  - 密码: aiot_password

- **Config Service（配置服务）**: http://localhost:8001

- **Plugin Service（插件服务）**: http://localhost:9000

### 数据库连接

**MySQL连接信息：**
```
Host: localhost
Port: 3306
Database: aiot_admin
Username: aiot_user
Password: aiot_password
```

**Redis连接信息：**
```
Host: localhost
Port: 6379
Password: (无)
```

**MQTT连接信息：**
```
Host: localhost
Port: 1883 (TCP)
Port: 9001 (WebSocket)
Username: (无)
Password: (无)
```

## 后端环境变量配置

确保后端的环境变量正确配置以连接到Docker服务：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password
DB_NAME=aiot_admin

# Redis配置
REDIS_URL=redis://localhost:6379

# MQTT配置
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
```

## 常用命令

### 管理开发环境服务

```bash
# 启动服务
bash script/deploy.sh start-dev-services

# 停止服务
bash script/deploy.sh stop-dev-services

# 重启服务
bash script/deploy.sh restart-dev-services

# 查看服务状态
bash script/deploy.sh status-dev-services

# 查看服务日志
bash script/deploy.sh logs-dev-services

# 查看特定服务的日志
bash script/deploy.sh logs-dev-services mysql
```

### 直接使用 docker-compose

```bash
cd docker

# 启动所有服务
docker-compose -f docker-compose.dev-services.yml up -d

# 停止所有服务
docker-compose -f docker-compose.dev-services.yml down

# 查看日志
docker-compose -f docker-compose.dev-services.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.dev-services.yml restart redis

# 查看服务状态
docker-compose -f docker-compose.dev-services.yml ps
```

## 开发工作流

### 典型的开发流程

1. **启动支持服务**
   ```bash
   bash script/deploy.sh start-dev-services
   ```

2. **启动后端（终端1）**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **启动前端（终端2）**
   ```bash
   cd frontend
   npm run dev
   ```

4. **开始开发**
   - 修改后端代码，保存后自动重载
   - 修改前端代码，保存后自动热更新
   - 使用浏览器访问 http://localhost:5173

5. **结束开发**
   - Ctrl+C 停止前后端
   - `bash script/deploy.sh stop-dev-services` 停止支持服务

### 数据库操作

**使用phpMyAdmin（推荐）：**
- 访问 http://localhost:8081
- 图形化管理数据库

**使用命令行：**
```bash
# 连接到MySQL
docker exec -it codehubot-mysql-dev mysql -u aiot_user -paiot_password aiot_admin

# 导入SQL文件
docker exec -i codehubot-mysql-dev mysql -u aiot_user -paiot_password aiot_admin < SQL/your_file.sql
```

### Redis操作

```bash
# 连接到Redis
docker exec -it codehubot-redis-dev redis-cli

# 查看所有键
docker exec -it codehubot-redis-dev redis-cli KEYS '*'

# 清空Redis
docker exec -it codehubot-redis-dev redis-cli FLUSHALL
```

### 查看Celery任务

访问 Flower 监控面板：http://localhost:5555
- 查看正在执行的任务
- 查看任务历史
- 查看Worker状态

## 故障排查

### 端口冲突

如果遇到端口被占用的问题：

```bash
# 查看端口占用情况（macOS/Linux）
lsof -i :3306
lsof -i :6379
lsof -i :8000

# 停止占用端口的进程
kill -9 <PID>
```

### 服务无法启动

```bash
# 查看服务日志
docker-compose -f docker-compose.dev-services.yml logs [service_name]

# 重启服务
docker-compose -f docker-compose.dev-services.yml restart [service_name]

# 重建服务
docker-compose -f docker-compose.dev-services.yml up -d --force-recreate [service_name]
```

### 数据库连接失败

1. 检查MySQL是否正常运行：
   ```bash
   docker ps | grep mysql-dev
   ```

2. 查看MySQL日志：
   ```bash
   docker logs codehubot-mysql-dev
   ```

3. 确认端口3306未被占用

### Redis连接失败

1. 检查Redis是否正常运行：
   ```bash
   docker ps | grep redis-dev
   ```

2. 测试Redis连接：
   ```bash
   docker exec -it codehubot-redis-dev redis-cli ping
   ```

## 与生产环境的区别

| 特性 | 开发环境 | 生产环境 |
|------|----------|----------|
| 前后端 | 本地运行 | Docker容器 |
| 端口开放 | 全部开放 | 仅必要端口 |
| 数据卷 | dev独立卷 | prod独立卷 |
| 网络 | aiot-network-dev | aiot-network |
| 热重载 | 支持 | 不支持 |
| 容器命名 | *-dev后缀 | 无后缀 |

## 注意事项

1. **数据隔离**：开发环境使用独立的数据卷（*_dev），不会影响生产环境数据

2. **端口冲突**：如果同时运行生产环境和开发环境，会有端口冲突

3. **性能**：开发环境优化了启动速度和调试体验，不适合生产使用

4. **安全性**：开发环境使用默认密码，不要用于生产

5. **依赖同步**：确保本地Python和Node.js版本与Docker镜像一致

## 环境要求

- Docker 20.10+
- Docker Compose 1.29+
- Python 3.9+（后端开发）
- Node.js 16+（前端开发）
- 至少4GB可用内存

## 更多资源

- [完整部署文档](../deploy/README.md)
- [开发规范](../docs_开发规范/README.md)
- [API文档](http://localhost:8000/docs)（后端启动后访问）
