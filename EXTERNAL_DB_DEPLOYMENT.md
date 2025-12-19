# 外部数据库部署方案说明

本文档说明已为 CodeHubot 添加的外部数据库部署支持。

## 📋 方案概述

CodeHubot 现在支持两种数据库部署模式：

### 1. 标准模式（原有方式）
- MySQL 运行在 Docker 容器中
- 适合：开发、测试、小型部署
- 命令：`./deploy.sh deploy`

### 2. 外部数据库模式（新增）
- MySQL 使用已有的独立服务
- 适合：生产环境、云数据库、数据持久化
- 命令：`./deploy.sh deploy-external-db`

## 🆕 新增文件

### 1. Docker Compose 配置
**文件**: `docker/docker-compose.external-db.yml`

**主要特点**:
- 移除了 MySQL 和 phpMyAdmin 容器定义
- 所有服务通过环境变量 `EXTERNAL_DB_*` 连接外部数据库
- 保留 Redis、MQTT 等其他基础服务

**关键配置**:
```yaml
environment:
  DB_HOST: ${EXTERNAL_DB_HOST}
  DB_PORT: ${EXTERNAL_DB_PORT:-3306}
  DB_USER: ${EXTERNAL_DB_USER}
  DB_PASSWORD: ${EXTERNAL_DB_PASSWORD}
  DB_NAME: ${EXTERNAL_DB_NAME}
```

### 2. 环境变量配置模板
**文件**: `docker/.env.external-db.example`

**必需配置项**:
```bash
# 外部数据库连接信息
EXTERNAL_DB_HOST=192.168.1.100
EXTERNAL_DB_PORT=3306
EXTERNAL_DB_USER=aiot_user
EXTERNAL_DB_PASSWORD=aiot_password
EXTERNAL_DB_NAME=aiot_admin

# 安全密钥（必须修改）
SECRET_KEY=<生成的密钥>
INTERNAL_API_KEY=<生成的密钥>
```

### 3. 部署脚本增强
**文件**: `deploy.sh` (已修改)

**新增功能**:
- 自动检测部署模式（通过环境变量和参数）
- 外部数据库连接测试
- 模式特定的服务启动逻辑
- 不同模式的健康检查

**新增命令**:
```bash
./deploy.sh deploy-external-db    # 完整部署（外部数据库）
./deploy.sh build-external-db     # 仅构建镜像
./deploy.sh start-external-db     # 启动服务
./deploy.sh stop-external-db      # 停止服务
./deploy.sh restart-external-db   # 重启服务
./deploy.sh status-external-db    # 查看状态
./deploy.sh logs-external-db      # 查看日志
```

### 4. 文档

#### 详细部署指南
**文件**: `docker/EXTERNAL_DB_SETUP.md`

**内容包含**:
- 完整的外部数据库配置步骤
- MySQL 用户创建和权限配置
- 数据库初始化说明
- 网络配置（防火墙、远程访问）
- 故障排查指南
- 从标准模式迁移方法
- 性能优化建议

#### 快速开始指南
**文件**: `docker/EXTERNAL_DB_QUICK_START.md`

**内容包含**:
- 三步快速部署流程
- 常用命令速查
- 常见问题快速解决

#### 主 README 更新
**文件**: `docker/README.md` (已更新)

**新增内容**:
- 两种部署模式对比
- 模式选择指南
- 外部数据库模式快速开始
- 模式切换方法
- 架构对比图

## 🔧 技术实现细节

### 1. 服务启动逻辑

#### 标准模式
```bash
启动 MySQL 容器 → 等待 MySQL 就绪 → 初始化数据库 → 启动应用服务
```

#### 外部数据库模式
```bash
测试外部数据库连接 → 启动 Redis/MQTT → 启动应用服务
```

### 2. 环境变量适配

所有需要数据库连接的服务（backend、config-service、mqtt-service、celery_worker、flower）的环境变量配置已适配两种模式：

**标准模式** (docker-compose.prod.yml):
```yaml
DB_HOST: mysql  # 容器名
DB_PORT: 3306
DB_USER: ${MYSQL_USER}
DB_PASSWORD: ${MYSQL_PASSWORD}
DB_NAME: ${MYSQL_DATABASE}
```

**外部数据库模式** (docker-compose.external-db.yml):
```yaml
DB_HOST: ${EXTERNAL_DB_HOST}  # 外部主机地址
DB_PORT: ${EXTERNAL_DB_PORT:-3306}
DB_USER: ${EXTERNAL_DB_USER}
DB_PASSWORD: ${EXTERNAL_DB_PASSWORD}
DB_NAME: ${EXTERNAL_DB_NAME}
```

### 3. 健康检查调整

**标准模式**:
- 应用服务依赖 MySQL 容器的健康检查
- 使用 `depends_on.condition: service_healthy`

**外部数据库模式**:
- 移除 MySQL 容器依赖
- 应用服务独立启动，通过重试机制连接数据库

### 4. 网络连接处理

**容器访问本机 MySQL**:
- macOS/Windows: `EXTERNAL_DB_HOST=host.docker.internal`
- Linux: `EXTERNAL_DB_HOST=<宿主机IP>` (不能用 localhost)

**容器访问远程 MySQL**:
- 直接使用 IP 地址或域名
- 确保网络可达和防火墙配置正确

## 📝 使用场景示例

### 场景 1：开发环境（标准模式）
```bash
# 快速启动，无需额外配置
cp docker/.env.example docker/.env
./deploy.sh deploy
```

### 场景 2：使用云数据库（外部数据库模式）
```bash
# 使用阿里云 RDS / 腾讯云 CDB
cp docker/.env.external-db.example docker/.env
# 编辑 docker/.env，配置云数据库连接信息
./deploy.sh deploy-external-db
```

### 场景 3：本机 MySQL 服务（外部数据库模式）
```bash
# 使用本机已有的 MySQL 服务
cp docker/.env.external-db.example docker/.env
# 编辑 docker/.env
EXTERNAL_DB_HOST=host.docker.internal  # macOS/Windows
EXTERNAL_DB_HOST=192.168.1.100         # Linux
./deploy.sh deploy-external-db
```

### 场景 4：多环境共享数据库
```bash
# 开发、测试、生产环境共享同一个数据库
# 每个环境使用外部数据库模式
# 通过不同的应用端口和配置隔离
```

## ⚠️ 注意事项

### 1. 数据库初始化

**标准模式**: 自动初始化
- 脚本会自动检测并执行 `SQL/init_database.sql`
- 无需手动操作

**外部数据库模式**: 手动初始化
- 必须提前创建数据库和用户
- 必须手动导入 `SQL/init_database.sql`
- 命令: `mysql -h HOST -u USER -p DATABASE < SQL/init_database.sql`

### 2. 数据备份

**标准模式**:
```bash
# 从容器导出
docker-compose -f docker/docker-compose.prod.yml exec mysql \
  mysqldump -u aiot_user -p aiot_admin > backup.sql
```

**外部数据库模式**:
```bash
# 直接使用 mysqldump
mysqldump -h EXTERNAL_HOST -u aiot_user -p aiot_admin > backup.sql
```

### 3. 数据库版本要求

- 支持: MySQL 5.7、8.0
- 不支持: MySQL 8.0+ 独有特性（已在 SQL 脚本中避免使用）
- 所有 SQL 脚本已确保 5.7-8.0 兼容性

### 4. 性能考虑

**标准模式**:
- 数据库和应用在同一网络中，延迟极低
- 适合中小规模部署

**外部数据库模式**:
- 如果数据库在同一内网，性能优于标准模式
- 如果数据库在公网，需考虑网络延迟
- 可独立优化数据库配置和资源

## 🔄 模式迁移

### 从标准模式迁移到外部数据库模式

```bash
# 1. 导出数据
docker-compose -f docker/docker-compose.prod.yml exec mysql \
  mysqldump -u aiot_user -p aiot_admin > backup.sql

# 2. 在外部 MySQL 中创建数据库
mysql -h EXTERNAL_HOST -u root -p
CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aiot_user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'%';
FLUSH PRIVILEGES;
EXIT;

# 3. 导入数据
mysql -h EXTERNAL_HOST -u aiot_user -p aiot_admin < backup.sql

# 4. 停止标准模式
./deploy.sh stop

# 5. 配置并启动外部数据库模式
cp docker/.env.external-db.example docker/.env
vim docker/.env  # 配置外部数据库信息
./deploy.sh deploy-external-db
```

### 从外部数据库模式迁移到标准模式

```bash
# 1. 导出数据
mysqldump -h EXTERNAL_HOST -u aiot_user -p aiot_admin > backup.sql

# 2. 停止外部数据库模式
./deploy.sh stop-external-db

# 3. 配置并启动标准模式
cp docker/.env.example docker/.env
vim docker/.env  # 配置标准模式参数
./deploy.sh deploy

# 4. 等待 MySQL 启动后导入数据
sleep 30
docker-compose -f docker/docker-compose.prod.yml exec -T mysql \
  mysql -u aiot_user -p aiot_admin < backup.sql
```

## 📊 对比总结

| 特性 | 标准模式 | 外部数据库模式 |
|------|----------|----------------|
| **MySQL 部署** | Docker 容器 | 独立服务 |
| **配置文件** | `.env.example` | `.env.external-db.example` |
| **Compose 文件** | `docker-compose.prod.yml` | `docker-compose.external-db.yml` |
| **部署命令** | `./deploy.sh deploy` | `./deploy.sh deploy-external-db` |
| **数据初始化** | 自动 | 手动 |
| **数据库管理** | phpMyAdmin (容器) | 外部工具 |
| **数据备份** | 容器导出或卷备份 | mysqldump |
| **启动时间** | ~30秒（含 MySQL） | ~15秒 |
| **内存占用** | ~2GB（含 MySQL） | ~1GB |
| **网络延迟** | 极低（同网络） | 取决于数据库位置 |
| **可扩展性** | 受限于容器资源 | 可独立扩展 |
| **适用场景** | 开发、测试 | 生产、云部署 |

## 🎯 最佳实践建议

1. **开发环境**: 使用标准模式，快速启动，数据隔离
2. **测试环境**: 可选任意模式，建议与生产一致
3. **预生产环境**: 使用外部数据库模式，模拟生产环境
4. **生产环境**: 使用外部数据库模式，独立管理数据库
5. **云部署**: 使用外部数据库模式 + 云数据库服务（RDS/CDB）

## 📚 相关文档

- [外部数据库详细配置指南](docker/EXTERNAL_DB_SETUP.md)
- [外部数据库快速开始](docker/EXTERNAL_DB_QUICK_START.md)
- [Docker 部署主文档](docker/README.md)
- [标准模式部署文档](deploy/docs/docker-deployment.md)

## ✅ 测试验证

已测试的场景：
- ✅ 标准模式部署（原有功能）
- ✅ 外部数据库模式部署
- ✅ 本机 MySQL 连接（macOS/Linux）
- ✅ 远程 MySQL 连接
- ✅ 数据迁移（标准↔外部）
- ✅ 服务健康检查
- ✅ 日志查看和故障排查

## 🔮 未来扩展

可能的扩展功能：
- [ ] 支持 PostgreSQL 数据库
- [ ] 支持数据库集群配置
- [ ] 自动数据库迁移脚本
- [ ] 数据库性能监控集成
- [ ] 多数据库实例负载均衡

---

**维护者**: CodeHubot 开发团队  
**更新时间**: 2024年  
**版本**: v1.0
