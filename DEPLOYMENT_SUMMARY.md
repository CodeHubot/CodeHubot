# CodeHubot 容器化自动部署 - 文件清单

本文档列出了所有为容器化自动部署创建的文件。

## 📦 创建的文件

### 1. Docker 配置文件

#### `config-service/Dockerfile`
- **说明**: 配置服务的 Docker 镜像构建文件
- **端口**: 8001
- **基础镜像**: python:3.11-slim

#### `frontend/Dockerfile` 
- **说明**: 前端服务的 Docker 镜像构建文件（多阶段构建，生产环境）
- **端口**: 80 (Nginx)
- **构建阶段**: 
  - 构建阶段: node:18-alpine
  - 生产阶段: nginx:alpine

#### `docker/docker-compose.prod.yml`
- **说明**: 生产环境的 Docker Compose 配置文件
- **包含服务**: MySQL, Redis, MQTT, Backend, Config-Service, Frontend, Plugin-Service
- **功能**: 
  - 服务编排
  - 健康检查
  - 网络配置
  - 数据卷管理

#### `docker/.env.example`
- **说明**: 环境变量配置示例文件
- **用途**: 作为 `.env` 文件的模板

### 2. 部署脚本

#### `deploy.sh`
- **说明**: 自动化部署脚本
- **功能**:
  - 依赖检查
  - 环境配置检查
  - 自动生成密钥
  - 构建 Docker 镜像
  - 启动所有服务
  - 数据库初始化
  - 健康检查
- **命令**:
  - `./deploy.sh deploy` - 完整部署
  - `./deploy.sh build` - 仅构建镜像
  - `./deploy.sh start` - 启动服务
  - `./deploy.sh stop` - 停止服务
  - `./deploy.sh restart` - 重启服务
  - `./deploy.sh status` - 查看状态
  - `./deploy.sh logs [服务名]` - 查看日志

### 3. 文档

#### `deploy/docs/docker-deployment.md`
- **说明**: 完整的 Docker 部署文档
- **内容**:
  - 系统要求
  - 快速开始指南
  - 详细配置说明
  - 部署流程
  - 服务管理
  - 故障排查
  - 生产环境建议

#### `docker/README.md` (已更新)
- **说明**: Docker 目录的快速参考文档
- **内容**: 常用命令和快速开始指南

## 🚀 快速使用

### 1. 首次部署

```bash
# 1. 配置环境变量
cd docker
cp .env.example .env
vim .env  # 编辑配置，特别是 SECRET_KEY 和 INTERNAL_API_KEY

# 2. 返回项目根目录并执行部署
cd ..
./deploy.sh deploy
```

### 2. 查看服务状态

```bash
./deploy.sh status
```

### 3. 查看日志

```bash
./deploy.sh logs          # 所有服务
./deploy.sh logs backend  # 后端服务
./deploy.sh logs frontend # 前端服务
```

## 📋 服务列表

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| MySQL | codehubot-mysql | 3306 | 数据库 |
| Redis | codehubot-redis | 6379 | 缓存 |
| MQTT | codehubot-mqtt | 1883, 9001 | 消息代理 |
| Backend | codehubot-backend | 8000 | 后端 API |
| Config-Service | codehubot-config-service | 8001 | 配置服务 |
| Frontend | codehubot-frontend | 80 | 前端 Web |
| Plugin-Service | codehubot-plugin-service | 9000 | 插件服务（对外接口） |
| **Plugin-Backend-Service** | **codehubot-plugin-backend** | **9001** | **插件后端服务（直接访问数据库和MQTT）** |

## 🔧 配置要点

### 必需配置项

1. **SECRET_KEY**: JWT 密钥（至少 32 个字符）
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **INTERNAL_API_KEY**: 内部 API 密钥
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **数据库密码**: MYSQL_PASSWORD 和 MYSQL_ROOT_PASSWORD

### 可选配置项

- 服务端口（如果默认端口被占用）
- MQTT 认证信息
- 日志级别
- 环境类型

## 📚 相关文档

- [Docker 部署详细文档](deploy/docs/docker-deployment.md)
- [开发环境指南](deploy/docs/development-guide.md)
- [手动部署指南](deploy/docs/manual-deployment.md)

## ⚠️ 注意事项

1. **新架构**: plugin-backend-service (端口9001) 为新增服务，直接访问数据库和MQTT
2. **插件服务**: plugin-service (端口9000) 调用 plugin-backend-service，不再直接调用 backend
3. **数据持久化**: 所有数据存储在 Docker 数据卷中
4. **端口冲突**: 确保所需端口未被占用（特别是新增的 9001 端口）
5. **资源要求**: 建议至少 4GB RAM
6. **服务依赖**: plugin-backend-service 依赖 MySQL 和 MQTT，确保这两个服务先启动

## 🗑️ 删除持久化数据

### ⚠️ 警告

**删除持久化数据是不可逆的操作！** 删除后，所有数据将永久丢失，包括：
- 数据库中的所有数据（用户、设备、知识库等）
- Redis 缓存数据
- MQTT 消息数据
- 知识库文档文件

请确保在删除前已做好数据备份！

### 数据卷说明

系统使用以下 Docker 数据卷存储持久化数据：

| 数据卷名称 | 存储内容 | 说明 |
|-----------|---------|------|
| `mysql_data` | MySQL 数据库数据 | 所有业务数据 |
| `redis_data` | Redis 缓存数据 | 会话、缓存等 |
| `mqtt_data` | MQTT 消息数据 | MQTT broker 数据 |
| `mqtt_logs` | MQTT 日志 | MQTT 服务日志 |
| `knowledge_bases_data` | 知识库文档 | 上传的文档文件 |

### 删除方法

#### 方法一：删除所有持久化数据（完全清理）

```bash
# 1. 停止所有服务
./deploy.sh stop

# 或者使用 docker-compose
cd docker
docker-compose -f docker-compose.prod.yml down

# 2. 删除所有数据卷（包括数据）
docker-compose -f docker-compose.prod.yml down -v

# 3. 验证数据卷已删除
docker volume ls | grep codehubot
```

#### 方法二：删除特定数据卷

```bash
# 1. 停止所有服务
./deploy.sh stop

# 2. 删除特定数据卷
docker volume rm codehubot-mysql-data      # 删除 MySQL 数据
docker volume rm codehubot-redis-data      # 删除 Redis 数据
docker volume rm codehubot-mqtt-data       # 删除 MQTT 数据
docker volume rm codehubot-mqtt-logs       # 删除 MQTT 日志
docker volume rm codehubot-knowledge-bases # 删除知识库文档（如果存在）

# 注意：数据卷名称可能因配置而异，请先查看实际名称
docker volume ls
```

#### 方法三：仅删除数据，保留数据卷定义

```bash
# 1. 停止所有服务
./deploy.sh stop

# 2. 进入 MySQL 容器删除数据（示例）
docker run --rm -v codehubot-mysql-data:/data alpine sh -c "rm -rf /data/*"

# 3. 进入 Redis 容器删除数据（示例）
docker run --rm -v codehubot-redis-data:/data alpine sh -c "rm -rf /data/*"

# 4. 重新启动服务（数据卷将重新初始化）
./deploy.sh start
```

### 查看数据卷信息

```bash
# 查看所有数据卷
docker volume ls

# 查看数据卷详细信息
docker volume inspect codehubot-mysql-data

# 查看数据卷使用情况
docker system df -v
```

### 数据备份（删除前建议操作）

```bash
# 1. 备份 MySQL 数据
docker exec codehubot-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} --all-databases > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 备份知识库文档（如果数据卷已挂载）
docker run --rm -v codehubot-knowledge-bases:/data -v $(pwd):/backup alpine tar czf /backup/knowledge_bases_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# 3. 备份 Redis 数据（可选）
docker exec codehubot-redis redis-cli --rdb /data/dump.rdb
docker cp codehubot-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 重新初始化数据

删除数据后，重新部署时会自动初始化：

```bash
# 重新部署（会自动初始化数据库）
./deploy.sh deploy
```

### 常见场景

#### 场景 1：开发环境重置

```bash
# 完全清理并重新部署
./deploy.sh stop
cd docker && docker-compose -f docker-compose.prod.yml down -v
cd .. && ./deploy.sh deploy
```

#### 场景 2：仅重置数据库

```bash
# 停止服务
./deploy.sh stop

# 删除 MySQL 数据卷
docker volume rm codehubot-mysql-data

# 重新启动（数据库会自动初始化）
./deploy.sh start
```

#### 场景 3：清理未使用的数据卷

```bash
# 清理所有未使用的数据卷（谨慎使用！）
docker volume prune

# 查看将被删除的数据卷（不实际删除）
docker volume ls -f dangling=true
```

## 🆘 获取帮助

如遇问题，请：
1. 查看 [Docker 部署文档](deploy/docs/docker-deployment.md) 的故障排查部分
2. 查看服务日志：`./deploy.sh logs [服务名]`
3. 检查服务状态：`./deploy.sh status`

---

**创建时间**: 2025-11-24
**最后更新**: 2025-12-03
**版本**: 1.1.0
