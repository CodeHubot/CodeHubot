# CodeHubot 本地开发环境部署指南

本文档提供 CodeHubot 物联网设备服务系统在本地开发环境的部署和运行说明。

## 📋 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [详细配置](#详细配置)
4. [开发工具](#开发工具)
5. [常见问题](#常见问题)

---

## 🔧 环境要求

### 必需软件

- **Python**: 3.11+ (推荐使用 pyenv 管理 Python 版本)
- **Node.js**: 18+ (推荐使用 nvm 管理 Node.js 版本)
- **Docker**: 20.10+ (用于运行 MySQL、Redis、MQTT 服务)
- **Docker Compose**: 2.0+ (用于编排容器服务)
- **Git**: 用于克隆和更新代码

### 说明

- **MySQL、Redis、MQTT** 均使用 Docker 容器部署，无需本地安装
- 所有服务通过 Docker Compose 统一管理，简化部署流程

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url> CodeHubot
cd CodeHubot
```

### 2. 启动基础服务（MySQL、Redis、MQTT）

使用 Docker Compose 一键启动所有基础服务：

```bash
cd docker

# 启动所有服务（MySQL、Redis、MQTT）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

**服务说明**：
- **MySQL**: 端口 3306，自动创建 `aiot_admin` 和 `aiot_device` 数据库
- **Redis**: 端口 6379，用于缓存（可选）
- **MQTT**: 端口 1883（MQTT），9001（WebSocket）

**默认配置**（可在 `docker/docker-compose.yml` 中修改）：
- MySQL 用户名: `aiot_user`
- MySQL 密码: `aiot_password`
- MySQL Root 密码: `root_password`

**Docker 服务管理命令**：

```bash
cd docker

# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用，会删除所有数据）
docker-compose down -v

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f          # 所有服务
docker-compose logs -f mysql    # MySQL 日志
docker-compose logs -f redis    # Redis 日志
docker-compose logs -f mqtt     # MQTT 日志

# 重启服务
docker-compose restart          # 所有服务
docker-compose restart mysql   # 仅 MySQL
docker-compose restart redis   # 仅 Redis
docker-compose restart mqtt    # 仅 MQTT

# 进入容器
docker-compose exec mysql bash
docker-compose exec redis sh
```

### 3. 导入数据库结构

等待 MySQL 容器完全启动（约 10-30 秒），然后导入数据库结构：

```bash
# 等待 MySQL 就绪
docker-compose exec mysql mysqladmin ping -h localhost -u root -proot_password

# 导入数据库结构
docker-compose exec -T mysql mysql -uaiot_user -paiot_password aiot_admin < ../SQL/init_database.sql

# 验证数据库
docker-compose exec mysql mysql -uaiot_user -paiot_password -e "SHOW DATABASES;"
```

**提示**: 如果导入失败，可以稍等片刻后重试，确保 MySQL 完全启动。

### 4. 配置后端服务

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

**最小配置**（`.env` 文件）：

```bash
# 数据库配置（使用 Docker 容器）
DB_HOST=localhost
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password  # 与 docker-compose.yml 中的配置一致
DB_NAME=aiot_admin

# Redis 配置（使用 Docker 容器，可选）
REDIS_URL=redis://localhost:6379

# JWT 配置
SECRET_KEY=your-very-long-secret-key-at-least-32-characters-long
ALGORITHM=HS256

# MQTT 配置（使用 Docker 容器）
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=  # 当前配置允许匿名访问，可以留空
MQTT_PASSWORD=  # 当前配置允许匿名访问，可以留空

# 服务器配置
SERVER_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

**注意**: 
- 数据库密码需要与 `docker/docker-compose.yml` 中的 `MYSQL_PASSWORD` 保持一致（默认: `aiot_password`）
- 如果需要修改 Docker 服务配置，编辑 `docker/docker-compose.yml` 后执行 `docker-compose up -d` 重启服务

**生成 SECRET_KEY**：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. 启动后端服务

```bash
cd backend

# 确保虚拟环境已激活
source venv/bin/activate  # Windows: venv\Scripts\activate

# 启动服务（开发模式，支持热重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

**验证后端服务**：

```bash
# 健康检查
curl http://localhost:8000/health

# API 文档
open http://localhost:8000/docs
```

### 7. 配置前端服务

```bash
cd frontend

# 安装依赖
npm install

# 复制环境变量文件
cp .env.example .env
cp .env.development.example .env.development

# 编辑开发环境配置（可选，已有默认值）
nano .env.development
```

**开发环境配置**（`.env.development`，可选）：

```bash
# API 基础地址（使用 Vite 代理）
VITE_API_BASE_URL=/api

# 调试模式
VITE_DEBUG_MODE=true
```

### 8. 启动前端服务

```bash
cd frontend

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:3001` 启动（或配置的端口）。

**访问前端**：

打开浏览器访问 `http://localhost:3001`

**默认管理员账号**：
- 邮箱: `admin@aiot.com`
- 用户名: `admin`
- 密码: `admin123`

---

## ⚙️ 详细配置

### Docker 服务配置

#### 修改服务配置

编辑 `docker/docker-compose.yml` 可以修改服务配置：

```yaml
services:
  mysql:
    environment:
      MYSQL_PASSWORD: aiot_password      # 修改数据库密码
      MYSQL_ROOT_PASSWORD: root_password # 修改 root 密码
    ports:
      - "3306:3306"  # 修改端口映射，例如 "3307:3306"
  
  redis:
    ports:
      - "6379:6379"  # 修改端口映射，例如 "6380:6379"
  
  mqtt:
    ports:
      - "1883:1883"  # 修改端口映射，例如 "1884:1883"
      - "9001:9001"  # WebSocket 端口
```

**修改后重启服务**：

```bash
cd docker
docker-compose down
docker-compose up -d
```

#### 数据持久化

所有数据都存储在 Docker 数据卷中，即使容器删除数据也不会丢失：

```bash
# 查看数据卷
docker volume ls | grep codehubot

# 备份数据卷（可选）
docker run --rm -v codehubot_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz /data
```

#### 服务健康检查

所有服务都配置了健康检查，可以使用以下命令检查：

```bash
cd docker

# 检查 MySQL 健康状态
docker-compose exec mysql mysqladmin ping -h localhost -u root -proot_password

# 检查 Redis 健康状态
docker-compose exec redis redis-cli ping

# 检查 MQTT 健康状态（需要安装 mosquitto-clients）
mosquitto_pub -h localhost -p 1883 -t test -m "ping"
```

### 后端服务配置

#### 数据库配置

```bash
# backend/.env
DB_HOST=localhost
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password  # 与 docker-compose.yml 中的 MYSQL_PASSWORD 一致
DB_NAME=aiot_admin
```

#### Redis 配置（可选）

```bash
# backend/.env
REDIS_URL=redis://localhost:6379
```

**注意**: Redis 服务已通过 Docker 启动，无需额外配置。

#### MQTT 配置

```bash
# backend/.env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=  # 当前配置允许匿名访问，可以留空
MQTT_PASSWORD=  # 当前配置允许匿名访问，可以留空
```

**注意**: MQTT 服务已通过 Docker 启动，配置在 `docker/mosquitto.conf` 中。

### 前端服务配置

#### Vite 代理配置

前端开发服务器已配置代理，所有 `/api` 请求会自动代理到后端服务。

配置位置：`frontend/vite.config.js`

```javascript
server: {
  port: 3001,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### 配置服务（可选）

如果需要测试设备配置服务：

```bash
cd config-service

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
nano .env
```

**配置**（`config-service/.env`）：

```bash
# 数据库配置（使用 aiot_device 数据库，Docker 容器）
DB_HOST=localhost
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password  # 与 docker-compose.yml 中的配置一致
DB_NAME=aiot_device

# MQTT 配置
MQTT_BROKER=localhost
MQTT_PORT=1883

# API 服务器
API_SERVER=http://localhost:8000
OTA_SERVER=http://localhost:8000

# 服务端口
PORT=8001
```

**启动配置服务**：

```bash
python main.py
```

### 插件服务（可选）

如果需要测试插件服务：

```bash
cd plugin-service

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
nano .env
```

**配置**（`plugin-service/.env`）：

```bash
# 后端服务地址
BACKEND_URL=http://localhost:8000

# 后端 API 密钥（必须与后端 INTERNAL_API_KEY 一致）
BACKEND_API_KEY=your-internal-api-key

# 开发模式
RELOAD=true
DEBUG_MODE=true
CORS_ORIGINS=*
```

**启动插件服务**：

```bash
python main.py
```

---

## 🛠️ 开发工具

### 推荐开发工具

- **IDE**: VS Code, PyCharm, WebStorm
- **API 测试**: Postman, Insomnia, 或直接使用 Swagger UI (`http://localhost:8000/docs`)
- **数据库管理**: MySQL Workbench, DBeaver, TablePlus
- **MQTT 客户端**: MQTT.fx, MQTT Explorer

### VS Code 推荐扩展

- Python
- ESLint
- Prettier
- Vue Language Features (Volar)
- MySQL
- Docker

### 调试技巧

#### 后端调试

```bash
# 使用 Python 调试器
python -m pdb main.py

# 或使用 IDE 的调试功能
# 在代码中添加断点，使用 IDE 的调试模式启动
```

#### 前端调试

```bash
# 使用浏览器开发者工具
# Chrome DevTools / Firefox DevTools

# 查看网络请求
# 打开浏览器开发者工具 -> Network 标签

# 查看 Vue 组件状态
# 安装 Vue DevTools 浏览器扩展
```

### 热重载

- **后端**: 使用 `uvicorn --reload` 或 `python main.py`（已包含热重载）
- **前端**: Vite 默认支持热重载，修改代码后自动刷新

---

## ❓ 常见问题

### 1. Docker 服务启动失败

**问题**: `docker-compose up` 失败或服务无法启动

**解决方案**:
- 检查 Docker 是否运行
- 检查端口是否被占用
- 查看服务日志

```bash
# 检查 Docker 状态
docker ps

# 检查端口占用
# macOS/Linux
lsof -i :3306  # MySQL
lsof -i :6379  # Redis
lsof -i :1883  # MQTT

# 查看服务日志
cd docker
docker-compose logs mysql
docker-compose logs redis
docker-compose logs mqtt

# 重启服务
docker-compose restart
```

### 2. 数据库连接失败

**问题**: `Can't connect to MySQL server`

**解决方案**:
- 检查 MySQL 容器是否运行
- 检查数据库用户名和密码是否正确（与 docker-compose.yml 一致）
- 等待 MySQL 完全启动（首次启动需要 10-30 秒）

```bash
# 检查 MySQL 容器状态
cd docker
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 等待 MySQL 就绪
docker-compose exec mysql mysqladmin ping -h localhost -u root -proot_password

# 测试连接
docker-compose exec mysql mysql -uaiot_user -paiot_password -e "SHOW DATABASES;"
```

### 3. MQTT 连接失败

**问题**: `Connection refused` 或 `Connection timeout`

**解决方案**:
- 检查 MQTT 容器是否运行
- 检查端口是否正确（默认 1883）
- 查看 MQTT 日志

```bash
# 检查 MQTT 容器状态
cd docker
docker-compose ps mqtt

# 查看 MQTT 日志
docker-compose logs mqtt

# 测试连接（需要安装 mosquitto-clients）
# macOS: brew install mosquitto
# Linux: sudo apt-get install mosquitto-clients
mosquitto_pub -h localhost -p 1883 -t test -m "hello"
mosquitto_sub -h localhost -p 1883 -t test
```

### 4. Redis 连接失败

**问题**: `Connection refused` 或无法连接 Redis

**解决方案**:
- 检查 Redis 容器是否运行
- 检查端口是否正确（默认 6379）

```bash
# 检查 Redis 容器状态
cd docker
docker-compose ps redis

# 查看 Redis 日志
docker-compose logs redis

# 测试连接
docker-compose exec redis redis-cli ping
```

### 5. 前端无法连接后端

**问题**: 前端请求返回 404 或连接失败

**解决方案**:
- 检查后端服务是否启动（`http://localhost:8000/health`）
- 检查 Vite 代理配置是否正确
- 检查浏览器控制台的错误信息
- 检查 CORS 配置（开发环境通常已配置）

```bash
# 测试后端服务
curl http://localhost:8000/health

# 检查后端日志
# 查看后端服务的控制台输出
```

### 6. Docker 端口被占用

**问题**: `port is already allocated` 或 `Address already in use`

**解决方案**:
- 查找占用端口的进程并关闭
- 或修改 docker-compose.yml 中的端口映射

```bash
# 查找占用端口的进程
# macOS/Linux
lsof -i :3306  # MySQL
lsof -i :6379  # Redis
lsof -i :1883  # MQTT

# 关闭进程
kill -9 <PID>

# 或修改 docker-compose.yml 中的端口映射
# 例如将 MySQL 端口改为 3307:3306
```

### 7. Docker 数据卷问题

**问题**: 数据丢失或需要重置数据

**解决方案**:
- 删除数据卷重新开始
- 备份数据卷

```bash
cd docker

# 停止并删除所有数据卷（谨慎使用，会删除所有数据）
docker-compose down -v

# 备份 MySQL 数据
docker-compose exec mysql mysqldump -uaiot_user -paiot_password aiot_admin > backup.sql

# 恢复 MySQL 数据
docker-compose exec -T mysql mysql -uaiot_user -paiot_password aiot_admin < backup.sql
```

### 8. Python 依赖安装失败

**问题**: `pip install` 失败

**解决方案**:
- 使用国内镜像源
- 升级 pip
- 检查 Python 版本

```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级 pip
pip install --upgrade pip

# 检查 Python 版本
python --version  # 需要 3.11+
```

### 9. Node.js 依赖安装失败

**问题**: `npm install` 失败

**解决方案**:
- 使用国内镜像源
- 清除缓存
- 检查 Node.js 版本

```bash
# 使用国内镜像源
npm install --registry=https://registry.npmmirror.com

# 或设置全局镜像
npm config set registry https://registry.npmmirror.com

# 清除缓存
npm cache clean --force

# 检查 Node.js 版本
node --version  # 需要 18+
```

### 10. 数据库迁移问题

**问题**: 数据库结构不匹配

**解决方案**:
- 重新导入数据库结构
- 检查 MySQL 容器是否正常运行

```bash
# 重新导入数据库（使用 Docker）
cd docker
docker-compose exec -T mysql mysql -uaiot_user -paiot_password aiot_admin < ../SQL/init_database.sql

# 或直接使用 mysql 客户端
docker-compose exec mysql mysql -uaiot_user -paiot_password aiot_admin < /path/to/SQL/init_database.sql
```

---

## 📝 开发流程建议

### 1. 代码规范

- **Python**: 遵循 PEP 8，使用 Black 格式化
- **JavaScript/Vue**: 遵循 ESLint 规则，使用 Prettier 格式化

### 2. Git 工作流

```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/your-feature-name
```

### 3. 测试

- **后端**: 使用 pytest 编写单元测试
- **前端**: 使用 Vitest 或 Jest 编写单元测试

### 4. 代码审查

- 提交 Pull Request 前进行自我审查
- 确保代码符合项目规范
- 确保所有测试通过

---

## 🔗 相关资源

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **项目 README**: 查看项目根目录的 README.md
- **部署指南**: 查看 `deploy/docs/deployment-guide.md`

---

## 💡 提示

1. **使用虚拟环境**: 强烈建议为每个 Python 服务使用独立的虚拟环境
2. **环境变量**: 不要将 `.env` 文件提交到 Git，使用 `.env.example` 作为模板
3. **日志级别**: 开发环境建议使用 `DEBUG` 或 `INFO` 级别，方便调试
4. **热重载**: 充分利用开发服务器的热重载功能，提高开发效率
5. **API 文档**: 使用 Swagger UI 测试 API，比 Postman 更方便

---

**最后更新**: 2025-01-XX

