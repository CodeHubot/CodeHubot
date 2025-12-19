# Docker 部署说明

本目录包含 CodeHubot 系统的 Docker 容器化部署配置。

## 📁 文件说明

- `docker-compose.yml` - 开发环境配置（仅包含基础服务：MySQL、Redis、MQTT）
- `docker-compose.prod.yml` - 生产环境配置（包含所有服务，含 MySQL 容器）
- `docker-compose.external-db.yml` - 外部数据库模式配置（使用已有 MySQL 服务）
- `.env.example` - 标准模式环境变量配置示例
- `.env.external-db.example` - 外部数据库模式环境变量配置示例
- `mosquitto.conf` - MQTT 服务配置

## 🚀 快速开始

### 部署模式选择

CodeHubot 支持两种部署模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **标准模式** | MySQL 运行在 Docker 容器中 | 开发、测试、小型部署 |
| **外部数据库模式** | 使用已有的 MySQL 服务 | 生产环境、云数据库、数据持久化 |

### 模式 1：标准模式（MySQL 容器化）

#### 1.1 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑配置文件
vim .env
```

#### 1.2 使用部署脚本（推荐）

```bash
# 从项目根目录执行
cd ..
./deploy.sh deploy
```

#### 1.3 手动部署

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 模式 2：外部数据库模式（使用已有 MySQL）

#### 2.1 准备外部 MySQL 数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aiot_user'@'%' IDENTIFIED BY 'aiot_password';
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'%';
FLUSH PRIVILEGES;
EXIT;

# 导入数据结构
cd ..
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/init_database.sql
```

#### 2.2 配置环境变量

```bash
# 复制外部数据库配置模板
cp .env.external-db.example .env

# 编辑配置，设置外部数据库连接信息
vim .env
# 必须修改：EXTERNAL_DB_HOST、EXTERNAL_DB_USER、EXTERNAL_DB_PASSWORD、EXTERNAL_DB_NAME
# 必须修改：SECRET_KEY、INTERNAL_API_KEY（使用生产环境密钥）
```

#### 2.3 使用部署脚本（推荐）

```bash
# 从项目根目录执行
cd ..
./deploy.sh deploy-external-db
```

#### 2.4 手动部署

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.external-db.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.external-db.yml ps

# 查看日志
docker-compose -f docker-compose.external-db.yml logs -f
```

## 📚 详细文档

- [标准模式部署文档](../deploy/docs/docker-deployment.md) - 完整的 Docker 部署指南
- [外部数据库模式详细指南](EXTERNAL_DB_SETUP.md) - 外部数据库模式完整配置
- [外部数据库模式快速开始](EXTERNAL_DB_QUICK_START.md) - 三步快速部署

## 🔧 常用命令

### 标准模式命令

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart [服务名]

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f [服务名]

# 进入容器
docker-compose -f docker-compose.prod.yml exec [服务名] sh

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 外部数据库模式命令

```bash
# 使用部署脚本（推荐）
../deploy.sh deploy-external-db   # 完整部署
../deploy.sh start-external-db    # 启动服务
../deploy.sh stop-external-db     # 停止服务
../deploy.sh restart-external-db  # 重启服务
../deploy.sh status-external-db   # 查看状态
../deploy.sh logs-external-db     # 查看日志

# 或手动执行
docker-compose -f docker-compose.external-db.yml up -d
docker-compose -f docker-compose.external-db.yml down
docker-compose -f docker-compose.external-db.yml restart [服务名]
docker-compose -f docker-compose.external-db.yml logs -f [服务名]
docker-compose -f docker-compose.external-db.yml ps
```

## 🏗️ 服务架构

### 标准模式架构

```
┌─────────────┐
│  Frontend   │ (Nginx + Vue.js)
│   Port: 80  │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌─────▼─────────┐
│   Backend   │  │ Config Service │
│ Port: 8000  │  │  Port: 8001    │
└──────┬──────┘  └────────────────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
┌──────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│  MySQL   │ │ Redis  │ │  MQTT  │ │ Celery │
│  (容器)   │ │Port:6379│ │Port:1883│ │ Worker │
└──────────┘ └────────┘ └────────┘ └────────┘
```

### 外部数据库模式架构

```
┌─────────────┐
│  Frontend   │ (Nginx + Vue.js)
│   Port: 80  │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌─────▼─────────┐
│   Backend   │  │ Config Service │
│ Port: 8000  │  │  Port: 8001    │
└──────┬──────┘  └────────────────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
┌──────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│  MySQL   │ │ Redis  │ │  MQTT  │ │ Celery │
│ (外部服务) │ │Port:6379│ │Port:1883│ │ Worker │
└──────────┘ └────────┘ └────────┘ └────────┘
     ↑
     └─ 独立 MySQL 服务器 / 云数据库
```

## ⚠️ 注意事项

### 通用注意事项

1. **首次部署**：确保已配置 `.env` 文件，特别是 `SECRET_KEY` 和 `INTERNAL_API_KEY`
2. **端口冲突**：确保所需端口未被占用
3. **资源要求**：
   - 标准模式：建议至少 4GB RAM 和 20GB 磁盘空间
   - 外部数据库模式：建议至少 2GB RAM（不含 MySQL）

### 标准模式注意事项

- **数据持久化**：所有数据存储在 Docker 数据卷中，删除容器不会删除数据
- **数据库访问**：可通过 phpMyAdmin (http://localhost:8081) 管理数据库
- **数据备份**：使用 `docker-compose exec mysql mysqldump ...` 或备份 Docker 卷

### 外部数据库模式注意事项

- **网络连接**：确保 Docker 容器可以访问外部 MySQL 服务
  - 本机 MySQL：使用 `host.docker.internal` (macOS/Windows) 或宿主机 IP (Linux)
  - 远程 MySQL：使用 IP 地址或域名
- **数据库版本**：支持 MySQL 5.7 或 8.0
- **防火墙配置**：确保 MySQL 端口（默认 3306）允许访问
- **数据备份**：直接使用 `mysqldump` 备份外部数据库

## 🔄 模式切换

### 从标准模式切换到外部数据库模式

```bash
# 1. 导出现有数据
docker-compose -f docker-compose.prod.yml exec mysql \
  mysqldump -u aiot_user -p aiot_admin > backup.sql

# 2. 导入到外部数据库
mysql -h EXTERNAL_HOST -u aiot_user -p aiot_admin < backup.sql

# 3. 停止标准模式
docker-compose -f docker-compose.prod.yml down

# 4. 配置外部数据库模式
cp .env.external-db.example .env
vim .env  # 修改外部数据库配置

# 5. 启动外部数据库模式
docker-compose -f docker-compose.external-db.yml up -d
```

### 从外部数据库模式切换到标准模式

```bash
# 1. 导出外部数据库数据
mysqldump -h EXTERNAL_HOST -u aiot_user -p aiot_admin > backup.sql

# 2. 停止外部数据库模式
docker-compose -f docker-compose.external-db.yml down

# 3. 配置标准模式
cp .env.example .env
vim .env  # 修改配置

# 4. 启动标准模式
docker-compose -f docker-compose.prod.yml up -d

# 5. 导入数据（等待 MySQL 启动后）
sleep 30
docker-compose -f docker-compose.prod.yml exec -T mysql \
  mysql -u aiot_user -p aiot_admin < backup.sql
```

## 🔍 故障排查

### 通用问题

如果遇到问题，请：

1. 查看服务日志：`docker-compose -f [compose文件] logs [服务名]`
2. 检查服务状态：`docker-compose -f [compose文件] ps`
3. 参考 [部署文档](../deploy/docs/docker-deployment.md) 的故障排查部分

### 外部数据库模式常见问题

#### 问题 1：容器无法连接外部数据库

```bash
# 检查网络连接
docker exec -it codehubot-backend ping EXTERNAL_DB_HOST

# 检查配置
cat .env | grep EXTERNAL_DB

# 测试数据库连接
mysql -h EXTERNAL_DB_HOST -u EXTERNAL_DB_USER -p
```

#### 问题 2：本机 MySQL 使用 localhost 无法连接

```bash
# macOS/Windows - 使用特殊域名
EXTERNAL_DB_HOST=host.docker.internal

# Linux - 使用宿主机 IP（不要用 localhost）
EXTERNAL_DB_HOST=192.168.1.100
```

#### 问题 3：权限不足

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'%';
FLUSH PRIVILEGES;
```

完整的故障排查指南请参考 [EXTERNAL_DB_SETUP.md](EXTERNAL_DB_SETUP.md#故障排查)

## 📊 性能对比

| 指标 | 标准模式 | 外部数据库模式 |
|------|----------|----------------|
| 启动时间 | ~30秒（含 MySQL） | ~15秒（不含 MySQL） |
| 内存占用 | ~2GB（含 MySQL） | ~1GB（不含 MySQL） |
| 数据库性能 | 取决于容器资源 | 取决于外部 MySQL 配置 |
| 适合人数 | <100 并发用户 | 可扩展（取决于数据库） |

## 💡 最佳实践

### 开发环境

- 使用**标准模式**
- 快速启动，无需额外配置
- 数据隔离，便于测试

### 生产环境

- 使用**外部数据库模式**
- 数据库独立部署，便于维护和备份
- 可使用云数据库服务（如阿里云 RDS）
- 更好的性能和可扩展性

### 混合部署

- 开发/测试环境使用标准模式
- 预生产/生产环境使用外部数据库模式
- 数据导入导出实现环境迁移
