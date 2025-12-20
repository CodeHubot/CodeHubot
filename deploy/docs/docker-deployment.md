# CodeHubot 容器化自动部署指南

本文档介绍如何使用 Docker 和 Docker Compose 自动化部署 CodeHubot 系统的所有服务。

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [部署流程](#部署流程)
- [服务管理](#服务管理)
- [故障排查](#故障排查)
- [生产环境建议](#生产环境建议)

## 🔧 系统要求

### 必需软件

- **Docker**: 版本 20.10 或更高
- **Docker Compose**: 版本 2.0 或更高（或 Docker Desktop 内置的 compose）
- **Python 3**: 用于生成密钥（可选，脚本会自动生成）

### 系统资源

- **CPU**: 至少 2 核
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 20GB 可用空间

### 端口要求

确保以下端口未被占用：

- `80` - 前端服务（HTTP）
- `8000` - 后端 API 服务
- `8001` - 配置服务
- `3306` - MySQL 数据库
- `6379` - Redis 缓存
- `1883` - MQTT 服务
- `9001` - MQTT WebSocket

## 🚀 快速开始

### 0. 本地运行说明

**✅ 是的，完全可以在本地机器上运行！**

所有配置都支持本地部署，无需修改任何代码。本文档同时适用于本地和生产环境部署。

### 1. 克隆代码库

```bash
git clone <repository-url>
cd CodeHubot
```

### 2. 配置环境变量

```bash
# 进入 docker 目录
cd docker

# 复制环境变量示例文件
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用你喜欢的编辑器
```

**重要配置项：**

- `SECRET_KEY`: JWT 密钥（至少 32 个字符）
- `INTERNAL_API_KEY`: 内部 API 密钥
- `MYSQL_PASSWORD`: MySQL 用户密码
- `MYSQL_ROOT_PASSWORD`: MySQL root 密码

**生成密钥：**

```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 INTERNAL_API_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 执行部署脚本

```bash
# 返回项目根目录
cd ..

# 执行部署脚本
./deploy.sh deploy
```

部署脚本会自动完成以下操作：

1. ✅ 检查依赖（Docker、Docker Compose）
2. ✅ 检查环境配置文件
3. ✅ 生成必要的密钥（如果未配置）
4. ✅ 停止现有服务
5. ✅ 构建所有 Docker 镜像
6. ✅ 启动所有服务
7. ✅ 初始化数据库
8. ✅ 检查服务健康状态

### 4. 验证部署

部署完成后，访问以下地址验证服务：

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **配置服务**: http://localhost:8001
- **插件服务**: http://localhost:9000
- **API 文档**: http://localhost:8000/docs
- **插件服务文档**: http://localhost:9000/docs

## ⚙️ 详细配置

### 环境变量说明

编辑 `docker/.env` 文件，配置以下环境变量：

#### 数据库配置

```bash
MYSQL_DATABASE=aiot_admin          # 数据库名称
MYSQL_USER=aiot_user              # 数据库用户
MYSQL_PASSWORD=your_password       # 数据库密码
MYSQL_ROOT_PASSWORD=root_password  # Root 密码
MYSQL_PORT=3306                    # MySQL 端口
```

#### Redis 配置

```bash
REDIS_PORT=6379  # Redis 端口
```

#### MQTT 配置

```bash
MQTT_PORT=1883      # MQTT 端口
MQTT_WS_PORT=9001   # MQTT WebSocket 端口
MQTT_USERNAME=      # MQTT 用户名（可选）
MQTT_PASSWORD=      # MQTT 密码（可选）
```

#### 服务端口配置

```bash
BACKEND_PORT=8000         # 后端服务端口
CONFIG_SERVICE_PORT=8001  # 配置服务端口
FRONTEND_PORT=80          # 前端服务端口
PLUGIN_SERVICE_PORT=9000  # 插件服务端口
```

#### 服务器配置

```bash
SERVER_BASE_URL=http://localhost:8000  # 服务器基础 URL
BACKEND_URL=http://backend:8000         # 内部后端服务地址
```

#### JWT 配置

```bash
SECRET_KEY=your-secret-key-here        # JWT 密钥（必须）
ALGORITHM=HS256                        # JWT 算法
ACCESS_TOKEN_EXPIRE_MINUTES=15         # Access Token 有效期
REFRESH_TOKEN_EXPIRE_MINUTES=45       # Refresh Token 有效期
```

#### 内部 API 密钥

```bash
INTERNAL_API_KEY=your-api-key-here  # 内部 API 密钥（必须）
```

#### 环境配置

```bash
ENVIRONMENT=production  # 环境：development/production/testing
LOG_LEVEL=INFO         # 日志级别：DEBUG/INFO/WARNING/ERROR
```

#### 构建加速配置（可选）

```bash
# 如果构建镜像时网络较慢，可以启用国内镜像源加速
USE_CHINA_MIRROR=true  # 设置为 true 使用清华大学镜像源

# 或使用自定义镜像源
# PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
```

**注意**: 如果不在中国，使用国内镜像源可能反而变慢，建议保持 `USE_CHINA_MIRROR=false`

#### 插件服务配置

```bash
PLUGIN_SERVICE_PORT=9000        # 插件服务端口
PLUGIN_CORS_ENABLED=true        # 是否启用CORS
PLUGIN_CORS_ORIGINS=*           # 允许的来源（*表示所有）
PLUGIN_REQUEST_TIMEOUT=30       # 请求超时时间（秒）
PLUGIN_DEBUG_MODE=false         # 调试模式（生产环境建议false）
```

## 📦 部署流程

### 完整部署流程

```bash
./deploy.sh deploy
```

这个命令会执行完整的部署流程：

1. **检查依赖** - 验证 Docker 和 Docker Compose 是否安装
2. **检查配置** - 验证环境配置文件是否存在且配置正确
3. **生成密钥** - 如果密钥未配置，自动生成
4. **停止服务** - 停止现有的容器服务
5. **构建镜像** - 构建所有服务的 Docker 镜像
6. **启动服务** - 按顺序启动所有服务
7. **初始化数据库** - 执行数据库初始化脚本
8. **健康检查** - 检查所有服务的健康状态

### 分步部署

如果需要分步执行，可以使用以下命令：

```bash
# 仅构建镜像
./deploy.sh build

# 仅启动服务
./deploy.sh start

# 仅停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs              # 查看所有服务日志
./deploy.sh logs backend      # 查看后端服务日志
./deploy.sh logs frontend     # 查看前端服务日志
```

## 🛠️ 服务管理

### 使用 Docker Compose 管理

进入 `docker` 目录，使用 Docker Compose 命令管理服务：

```bash
cd docker

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f [服务名]

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart [服务名]

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 停止并删除数据卷（谨慎使用）
docker-compose -f docker-compose.prod.yml down -v
```

### 服务列表

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| mysql | codehubot-mysql | 3306 | MySQL 数据库 |
| redis | codehubot-redis | 6379 | Redis 缓存 |
| mqtt | codehubot-mqtt | 1883, 9001 | MQTT 消息代理 |
| backend | codehubot-backend | 8000 | 后端 API 服务 |
| config-service | codehubot-config-service | 8001 | 配置服务 |
| frontend | codehubot-frontend | 80 | 前端 Web 服务 |
| plugin-service | codehubot-plugin-service | 9000 | 插件服务（供外部插件调用） |

## 🔍 故障排查

### 常见问题

#### 1. 端口被占用

**错误信息：**
```
Error: bind: address already in use
```

**解决方法：**
- 检查端口占用：`lsof -i :端口号` 或 `netstat -tulpn | grep 端口号`
- 修改 `docker/.env` 中的端口配置
- 停止占用端口的服务

#### 2. 数据库连接失败

**错误信息：**
```
Error: Can't connect to MySQL server
```

**解决方法：**
- 检查 MySQL 容器是否正常运行：`docker ps | grep mysql`
- 检查数据库配置是否正确
- 等待 MySQL 完全启动（约 30 秒）
- 查看 MySQL 日志：`docker-compose -f docker-compose.prod.yml logs mysql`

#### 3. 镜像构建失败

**错误信息：**
```
Error: failed to build image
```

**解决方法：**
- 检查 Dockerfile 语法
- 检查网络连接（需要下载依赖）
- 清理 Docker 缓存：`docker system prune -a`
- 查看详细错误日志

#### 4. 服务无法访问

**解决方法：**
- 检查服务是否运行：`./deploy.sh status`
- 检查防火墙设置
- 查看服务日志：`./deploy.sh logs [服务名]`
- 检查健康检查：`curl http://localhost:端口/health`

#### 5. 数据库初始化失败

**解决方法：**
- 检查 SQL 脚本路径是否正确
- 检查数据库用户权限
- 手动执行初始化脚本：
  ```bash
  cd docker
  docker-compose -f docker-compose.prod.yml exec -T mysql mysql -uaiot_user -paiot_password aiot_admin < ../../SQL/init_database.sql
  ```

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs backend
./deploy.sh logs frontend
./deploy.sh logs mysql

# 实时查看日志
cd docker
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### 数据备份

#### 备份数据库

```bash
# 备份 MySQL 数据
docker exec codehubot-mysql mysqldump -uaiot_user -paiot_password aiot_admin > backup.sql

# 备份数据卷
docker run --rm -v codehubot_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz /data
```

#### 备份上传文件

**重要**: 上传的文件（固件、资源文件等）存储在 Docker Volume 中，需要定期备份：

```bash
# 备份上传文件目录
docker run --rm -v docker_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz /data

# 备份静态文件（固件）
docker run --rm -v docker_static_data:/data -v $(pwd):/backup alpine tar czf /backup/static-backup.tar.gz /data

# 备份知识库文档
docker run --rm -v docker_knowledge_bases_data:/data -v $(pwd):/backup alpine tar czf /backup/kb-backup.tar.gz /data
```

**一键备份所有上传文件**：

```bash
# 创建备份脚本
cat > backup-files.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 开始备份上传文件..."
docker run --rm -v docker_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/$BACKUP_DIR/uploads.tar.gz /data
echo "✅ 上传文件备份完成"

echo "📦 开始备份静态文件..."
docker run --rm -v docker_static_data:/data -v $(pwd):/backup alpine tar czf /backup/$BACKUP_DIR/static.tar.gz /data
echo "✅ 静态文件备份完成"

echo "📦 开始备份知识库..."
docker run --rm -v docker_knowledge_bases_data:/data -v $(pwd):/backup alpine tar czf /backup/$BACKUP_DIR/kb.tar.gz /data
echo "✅ 知识库备份完成"

echo "🎉 所有文件备份完成！备份位置: $BACKUP_DIR"
EOF

chmod +x backup-files.sh
./backup-files.sh
```

#### 恢复数据库

```bash
# 恢复 MySQL 数据
docker exec -i codehubot-mysql mysql -uaiot_user -paiot_password aiot_admin < backup.sql
```

#### 恢复上传文件

```bash
# 恢复上传文件
docker run --rm -v docker_uploads_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/uploads-backup.tar.gz --strip 1"

# 恢复静态文件
docker run --rm -v docker_static_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/static-backup.tar.gz --strip 1"

# 恢复知识库文档
docker run --rm -v docker_knowledge_bases_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/kb-backup.tar.gz --strip 1"
```

## 📁 文件上传持久化说明

后端服务使用以下 Docker Volume 持久化上传文件：

| Volume 名称 | 挂载路径 | 用途 |
|-----------|---------|-----|
| `uploads_data` | `/app/uploads` | 资源文件（视频、文档） |
| `static_data` | `/app/static` | 固件文件（.bin） |
| `knowledge_bases_data` | `/app/backend/data/knowledge-bases` | AI 知识库文档 |

**重要提示**：
- 容器重启后，上传的文件不会丢失
- 定期备份这些 Volume，避免数据丢失
- 监控磁盘使用情况：`docker system df -v`

详细配置说明请参考：[文件上传持久化配置说明](../../docs/文件上传持久化配置说明.md)

## 🏭 生产环境建议

### 安全配置

1. **修改默认密码**
   - 修改所有默认密码（数据库、Redis、MQTT）
   - 使用强密码生成器生成密码

2. **配置 HTTPS**
   - 使用 Nginx 反向代理配置 SSL 证书
   - 修改 `SERVER_BASE_URL` 为 HTTPS 地址

3. **限制网络访问**
   - 使用防火墙限制数据库和 Redis 的访问
   - 仅允许必要的端口对外开放

4. **定期更新**
   - 定期更新 Docker 镜像
   - 关注安全公告

### 性能优化

1. **资源配置**
   - 根据实际负载调整容器资源限制
   - 配置数据库连接池大小

2. **数据持久化**
   - 确保数据卷正确挂载
   - 定期备份数据

3. **监控告警**
   - 配置服务监控
   - 设置告警规则

### 高可用部署

1. **负载均衡**
   - 使用 Nginx 或 HAProxy 做负载均衡
   - 配置多个后端实例

2. **数据库主从**
   - 配置 MySQL 主从复制
   - 实现读写分离

3. **容器编排**
   - 考虑使用 Kubernetes 进行容器编排
   - 实现自动扩缩容

## 📝 更新部署

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并部署
./deploy.sh deploy
```

### 更新单个服务

```bash
cd docker

# 重新构建特定服务
docker-compose -f docker-compose.prod.yml build [服务名]

# 重启服务
docker-compose -f docker-compose.prod.yml up -d [服务名]
```

## 📚 相关文档

- [开发环境指南](./development-guide.md) - 本地开发环境配置（基础服务Docker，应用服务本地运行）
- [手动部署指南](./manual-deployment.md) - 传统手动部署方式（不使用Docker容器化）
- [构建优化指南](./build-optimization.md) - Docker 镜像构建速度优化
- [快速参考](./quick-reference.md) - 常用命令和配置速查

## 🆘 获取帮助

如果遇到问题，请：

1. 查看本文档的故障排查部分
2. 查看服务日志
3. 检查 GitHub Issues
4. 联系技术支持

---

**最后更新**: 2025-01-XX
**版本**: 1.0.0

