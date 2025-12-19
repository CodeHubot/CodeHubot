# 外部数据库部署指南

本文档说明如何使用已有的 MySQL 数据库服务进行 CodeHubot 部署，而不使用 Docker 容器部署 MySQL。

## 📋 适用场景

- 已有独立的 MySQL 数据库服务器
- 使用云数据库服务（如阿里云 RDS、腾讯云 CDB 等）
- 需要数据持久化在 Docker 之外
- 多环境共享同一数据库

## 🚀 快速开始

### 1. 准备外部 MySQL 数据库

#### 1.1 确保 MySQL 服务运行

```bash
# 检查 MySQL 是否运行
mysql --version
# 或
systemctl status mysql  # Linux
brew services list | grep mysql  # macOS
```

**支持版本**: MySQL 5.7 或 8.0

#### 1.2 创建数据库和用户

```sql
-- 1. 登录 MySQL（使用 root 或有权限的账号）
mysql -u root -p

-- 2. 创建数据库
CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 创建用户（允许从任何主机连接）
CREATE USER 'aiot_user'@'%' IDENTIFIED BY 'aiot_password';

-- 4. 授予权限
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'%';

-- 5. 刷新权限
FLUSH PRIVILEGES;

-- 6. 验证权限
SHOW GRANTS FOR 'aiot_user'@'%';
```

**安全建议**：
- 生产环境请使用强密码
- 如果知道具体的客户端 IP，将 `'%'` 替换为具体 IP（如 `'192.168.1.100'`）

#### 1.3 导入数据库结构

```bash
# 方式1：本地 MySQL
mysql -u aiot_user -p aiot_admin < SQL/init_database.sql

# 方式2：远程 MySQL
mysql -h 192.168.1.100 -P 3306 -u aiot_user -p aiot_admin < SQL/init_database.sql
```

**验证导入成功**：

```sql
-- 登录数据库
mysql -h HOST -u aiot_user -p aiot_admin

-- 查看表
SHOW TABLES;

-- 应该看到类似输出：
-- +----------------------------------+
-- | Tables_in_aiot_admin             |
-- +----------------------------------+
-- | aiot_core_users                  |
-- | aiot_core_devices                |
-- | pbl_courses                      |
-- | ...                              |
-- +----------------------------------+
```

#### 1.4 配置 MySQL 远程访问（如果需要）

**如果 MySQL 在远程服务器上，需要允许远程连接**：

```bash
# 编辑 MySQL 配置文件
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf  # Ubuntu/Debian
# 或
sudo nano /etc/my.cnf  # CentOS/RHEL

# 找到 bind-address 配置，修改为：
bind-address = 0.0.0.0

# 重启 MySQL
sudo systemctl restart mysql
```

**防火墙配置**（如果启用了防火墙）：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 3306/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
```

### 2. 配置环境变量

```bash
# 1. 复制外部数据库配置模板
cd /path/to/CodeHubot
cp docker/.env.external-db.example docker/.env

# 2. 编辑配置文件
nano docker/.env
# 或
vim docker/.env
```

**必须修改的配置**：

```bash
# ==================== 外部数据库配置 ====================
EXTERNAL_DB_HOST=192.168.1.100          # MySQL 服务器地址
EXTERNAL_DB_PORT=3306                   # MySQL 端口
EXTERNAL_DB_USER=aiot_user              # 数据库用户名
EXTERNAL_DB_PASSWORD=aiot_password      # 数据库密码
EXTERNAL_DB_NAME=aiot_admin             # 数据库名称

# ==================== JWT配置 ====================
# ⚠️ 生产环境必须修改！
SECRET_KEY=your-generated-secret-key
INTERNAL_API_KEY=your-generated-api-key
```

**生成密钥**：

```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 INTERNAL_API_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**可选配置**：

```bash
# 阿里云 API 密钥（用于知识库向量化）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key

# 管理员账号（首次部署自动创建）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
ADMIN_EMAIL=admin@example.com

# 通义千问大模型配置
QWEN_API_KEY=sk-your-qwen-api-key
```

### 3. 部署应用

#### 3.1 使用部署脚本（推荐）

```bash
# 完整部署（构建镜像 + 启动服务）
./deploy.sh deploy-external-db

# 仅构建镜像
./deploy.sh build-external-db

# 启动服务（已有镜像时）
./deploy.sh start-external-db
```

#### 3.2 手动部署

```bash
cd docker

# 构建镜像
docker-compose -f docker-compose.external-db.yml build

# 启动服务
docker-compose -f docker-compose.external-db.yml up -d

# 查看服务状态
docker-compose -f docker-compose.external-db.yml ps

# 查看日志
docker-compose -f docker-compose.external-db.yml logs -f
```

### 4. 验证部署

#### 4.1 检查服务状态

```bash
# 使用部署脚本
./deploy.sh status-external-db

# 或手动检查
docker-compose -f docker/docker-compose.external-db.yml ps
```

**预期输出**：所有服务状态为 `Up`

```
NAME                        STATUS              PORTS
codehubot-backend          Up 2 minutes        
codehubot-celery-worker    Up 2 minutes        
codehubot-config-service   Up 2 minutes        0.0.0.0:8001->8001/tcp
codehubot-flower           Up 2 minutes        0.0.0.0:5555->5555/tcp
codehubot-frontend         Up 2 minutes        0.0.0.0:80->80/tcp
codehubot-mqtt             Up 2 minutes        0.0.0.0:1883->1883/tcp
codehubot-mqtt-service     Up 2 minutes        
codehubot-plugin-service   Up 2 minutes        0.0.0.0:9000->9000/tcp
codehubot-redis            Up 2 minutes        
```

#### 4.2 测试数据库连接

```bash
# 从容器内测试数据库连接
docker exec -it codehubot-backend bash -c "python3 -c \"
from sqlalchemy import create_engine
import os
db_url = f'mysql+pymysql://{os.getenv(\"DB_USER\")}:{os.getenv(\"DB_PASSWORD\")}@{os.getenv(\"DB_HOST\")}:{os.getenv(\"DB_PORT\")}/{os.getenv(\"DB_NAME\")}'
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute('SELECT COUNT(*) FROM aiot_core_users')
    print(f'Users count: {result.scalar()}')
    print('Database connection successful!')
\""
```

#### 4.3 访问服务

```bash
# 前端
open http://localhost:80

# 后端 API 文档
open http://localhost:8000/docs

# Celery 监控面板
open http://localhost:5555/flower
# 默认账号: admin / 密码: admin
```

## 📊 服务列表

### 应用服务

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| frontend | codehubot-frontend | 80 | 前端服务 |
| backend | codehubot-backend | 8000 | 后端 API |
| config-service | codehubot-config-service | 8001 | 配置服务 |
| plugin-service | codehubot-plugin-service | 9000 | 插件服务 |
| mqtt-service | codehubot-mqtt-service | - | MQTT 消息处理 |
| celery_worker | codehubot-celery-worker | - | 异步任务处理 |
| flower | codehubot-flower | 5555 | Celery 监控 |

### 基础服务

| 服务 | 说明 | 访问方式 |
|------|------|----------|
| MySQL | 外部数据库 | 直接连接外部 MySQL |
| Redis | 缓存服务 | 仅容器内部访问 |
| MQTT | 消息代理 | localhost:1883 |

## 🔧 常用操作

### 查看日志

```bash
# 查看所有服务日志
./deploy.sh logs-external-db

# 查看特定服务日志
./deploy.sh logs-external-db backend
./deploy.sh logs-external-db frontend

# 或手动查看
docker-compose -f docker/docker-compose.external-db.yml logs -f backend
```

### 重启服务

```bash
# 重启所有服务
./deploy.sh restart-external-db

# 重启特定服务
docker-compose -f docker/docker-compose.external-db.yml restart backend

# 重启基础服务
docker-compose -f docker/docker-compose.external-db.yml restart redis mqtt
```

### 停止服务

```bash
# 停止所有服务
./deploy.sh stop-external-db

# 或手动停止
docker-compose -f docker/docker-compose.external-db.yml down
```

### 进入容器调试

```bash
# 进入后端容器
docker exec -it codehubot-backend bash

# 进入前端容器
docker exec -it codehubot-frontend sh

# 进入配置服务容器
docker exec -it codehubot-config-service bash
```

### 执行数据库更新脚本

```bash
# 如果有新的数据库更新脚本（如 SQL/update/xx_update.sql）
mysql -h EXTERNAL_DB_HOST -u aiot_user -p aiot_admin < SQL/update/xx_update.sql
```

## ⚠️ 注意事项

### 1. 数据库版本兼容性

- **支持**: MySQL 5.7、8.0
- **不支持**: MySQL 8.0+ 独有特性（如 `ADD COLUMN IF NOT EXISTS`）
- 所有 SQL 脚本已针对 5.7-8.0 兼容性优化

### 2. 网络连接

**Docker 容器访问外部 MySQL**：

- 如果 MySQL 在本机：使用 `host.docker.internal` 或本机 IP（不要用 `localhost`）
  ```bash
  # macOS/Windows
  EXTERNAL_DB_HOST=host.docker.internal
  
  # Linux（推荐使用实际 IP）
  EXTERNAL_DB_HOST=192.168.1.100
  ```

- 如果 MySQL 在远程服务器：直接使用 IP 或域名
  ```bash
  EXTERNAL_DB_HOST=db.example.com
  ```

### 3. 防火墙配置

确保 Docker 容器可以访问 MySQL 服务器的 3306 端口。

### 4. 数据备份

**外部数据库模式下，数据不在 Docker 卷中，请定期备份**：

```bash
# 备份数据库
mysqldump -h EXTERNAL_DB_HOST -u aiot_user -p aiot_admin > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -h EXTERNAL_DB_HOST -u aiot_user -p aiot_admin < backup_20240101.sql
```

### 5. 性能优化

**数据库在本机时的性能提示**：

- 使用 Unix Socket 连接更快（如果可能）
- 如果不需要远程访问，`bind-address = 127.0.0.1` 更安全

**数据库在远程时的性能提示**：

- 确保网络延迟低（< 5ms 最佳）
- 考虑使用内网连接而非公网
- 启用持久连接（连接池已内置）

## 🔄 从标准模式迁移到外部数据库模式

### 方案 1：导出再导入（推荐）

```bash
# 1. 导出现有数据
docker-compose -f docker/docker-compose.prod.yml exec mysql \
  mysqldump -u aiot_user -p aiot_admin > backup.sql

# 2. 导入到外部数据库
mysql -h EXTERNAL_DB_HOST -u aiot_user -p aiot_admin < backup.sql

# 3. 停止标准模式
./deploy.sh stop

# 4. 配置外部数据库环境变量
cp docker/.env.external-db.example docker/.env
# 编辑 docker/.env 配置外部数据库

# 5. 启动外部数据库模式
./deploy.sh deploy-external-db
```

### 方案 2：使用数据卷迁移（Linux）

```bash
# 1. 停止服务
./deploy.sh stop

# 2. 复制 MySQL 数据卷到外部 MySQL 数据目录
sudo cp -r /var/lib/docker/volumes/docker_mysql_data/_data/* \
  /var/lib/mysql/

# 3. 修改权限
sudo chown -R mysql:mysql /var/lib/mysql/

# 4. 启动外部数据库模式
./deploy.sh deploy-external-db
```

## 🆚 标准模式 vs 外部数据库模式对比

| 特性 | 标准模式 | 外部数据库模式 |
|------|----------|----------------|
| **MySQL 部署** | Docker 容器 | 独立服务 |
| **数据持久化** | Docker 卷 | MySQL 数据目录 |
| **启动速度** | 较慢（需启动 MySQL） | 较快 |
| **数据库管理** | phpMyAdmin | 外部工具 |
| **备份方式** | Docker 卷备份 | mysqldump |
| **资源占用** | 较高（包含 MySQL） | 较低 |
| **适用场景** | 开发、测试、小型部署 | 生产、大型部署 |

## 📚 相关文档

- [主部署文档](README.md)
- [数据库初始化脚本](../SQL/init_database.sql)
- [环境变量配置说明](.env.external-db.example)

## 🐛 故障排查

### 问题 1：容器无法连接外部数据库

**症状**：后端服务启动失败，日志显示数据库连接错误

**解决方法**：

```bash
# 1. 检查数据库配置
cat docker/.env | grep EXTERNAL_DB

# 2. 测试从宿主机连接数据库
mysql -h EXTERNAL_DB_HOST -P EXTERNAL_DB_PORT -u EXTERNAL_DB_USER -p

# 3. 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 4. 检查 MySQL 是否允许远程连接
mysql -u root -p -e "SELECT host, user FROM mysql.user WHERE user='aiot_user';"
```

### 问题 2：本机 MySQL 使用 localhost 无法连接

**原因**：Docker 容器内的 `localhost` 指向容器自己，不是宿主机

**解决方法**：

```bash
# macOS/Windows - 使用特殊域名
EXTERNAL_DB_HOST=host.docker.internal

# Linux - 使用宿主机 IP
EXTERNAL_DB_HOST=192.168.1.100  # 替换为实际 IP

# 查看本机 IP
ip addr show  # Linux
ifconfig  # macOS
```

### 问题 3：数据库权限不足

**症状**：`Access denied` 错误

**解决方法**：

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'%';
FLUSH PRIVILEGES;

-- 验证权限
SHOW GRANTS FOR 'aiot_user'@'%';
```

### 问题 4：服务启动但无法访问

**检查步骤**：

```bash
# 1. 查看服务状态
docker-compose -f docker/docker-compose.external-db.yml ps

# 2. 查看服务日志
docker-compose -f docker/docker-compose.external-db.yml logs backend

# 3. 检查端口占用
netstat -tuln | grep -E '(80|8000|8001)'

# 4. 测试后端健康检查
curl http://localhost:8000/health
```

## 💡 最佳实践

1. **安全性**
   - 生产环境使用强密码
   - 限制数据库用户的访问来源 IP
   - 定期更新密钥（SECRET_KEY、INTERNAL_API_KEY）

2. **性能优化**
   - 数据库和应用部署在同一内网
   - 启用 MySQL 查询缓存
   - 配置适当的连接池大小

3. **运维管理**
   - 配置自动备份
   - 监控数据库连接数
   - 定期检查磁盘空间

4. **开发建议**
   - 开发环境使用标准模式（简单）
   - 生产环境使用外部数据库模式（稳定）

---

**遇到问题？** 

- 查看日志：`./deploy.sh logs-external-db`
- 检查配置：`cat docker/.env`
- 测试连接：`mysql -h HOST -u USER -p DATABASE`
