# CodeHubot 系统部署指南

本文档提供 CodeHubot 物联网设备服务系统的完整部署说明，适用于手动部署到服务器环境。

## 📋 目录

1. [环境准备](#环境准备)
2. [数据库部署](#数据库部署)
3. [MQTT 服务部署](#mqtt-服务部署)
4. [后端服务部署](#后端服务部署)
5. [前端服务部署](#前端服务部署)
6. [配置服务部署](#配置服务部署)
7. [插件服务部署](#插件服务部署)

---

## 🔧 环境准备

### 系统要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+ 或 CentOS 7+)
- **Python**: 3.11+
- **Node.js**: 18+
- **MySQL**: 5.7.8+ 或 8.0+ (需要 5.7.8+ 以支持 JSON 数据类型)
- **Docker**: 20.10+ (用于运行 MQTT 服务)
- **Docker Compose**: 2.0+ (用于编排容器)
- **Redis**: 6.0+ (可选，用于缓存)
- **Nginx**: 1.18+ (用于前端部署以及后端服务的反向代理)

### 创建项目目录

```bash
# 创建项目根目录
sudo mkdir -p /opt/codehubot
sudo chown $USER:$USER /opt/codehubot
cd /opt/codehubot

# 克隆项目（或上传项目文件）
git clone <your-repo-url> .
# 或使用 scp/sftp 上传项目文件
```

---

## 🗄️ 数据库部署

### 1. 创建数据库和用户

**重要**: 确保 MySQL 版本 >= 5.7.8 以支持 JSON 数据类型。

```bash
# 登录 MySQL
sudo mysql -u root -p

# 在 MySQL 中执行以下命令
CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE aiot_device CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建数据库用户（请修改密码）
# 注意：MySQL 5.7 和 8.0 的认证插件可能不同
# MySQL 5.7 默认使用 mysql_native_password
# MySQL 8.0 默认使用 caching_sha2_password
# 如果需要兼容，可以显式指定认证插件
CREATE USER 'aiot_user'@'localhost' IDENTIFIED BY 'your_secure_password';
# 如果是 MySQL 8.0 且需要兼容旧客户端，可以使用：
# CREATE USER 'aiot_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_secure_password';

GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'localhost';
GRANT ALL PRIVILEGES ON aiot_device.* TO 'aiot_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. 导入数据库结构

```bash
cd /opt/codehubot

# 导入主系统数据库
mysql -u aiot_user -p aiot_admin < SQL/init_database.sql
```

### 3. 验证数据库

```bash
# 检查表是否创建成功
mysql -u aiot_user -p aiot_admin -e "SHOW TABLES;"
```

应该看到以下表：
- users
- products
- devices
- device_binding_history
- firmware_versions
- interaction_logs
- interaction_stats_hourly
- interaction_stats_daily

---

## 📡 MQTT 服务部署

MQTT 服务通过 Docker 容器部署，使用项目提供的 Docker Compose 配置。

### 1. 配置 MQTT

```bash
cd /opt/codehubot/docker

# 查看 MQTT 配置文件
cat mosquitto.conf
```

如果需要修改 MQTT 配置（如添加认证），可以编辑 `mosquitto.conf` 文件：

```bash
nano mosquitto.conf
```

**注意**: 当前配置允许匿名访问，生产环境建议添加认证。

### 2. 启动 MQTT 容器

```bash
# 进入 docker 目录
cd /opt/codehubot/docker

# 启动 MQTT 服务（仅启动 MQTT，不启动 MySQL）
docker-compose up -d mqtt

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mqtt
```

### 3. 验证 MQTT 服务

```bash
# 检查容器是否运行
docker ps | grep mqtt

# 检查端口是否监听
sudo netstat -tlnp | grep 1883

# 测试 MQTT 连接（需要安装 mosquitto-clients）
sudo apt install mosquitto-clients -y
mosquitto_pub -h localhost -p 1883 -t test/topic -m "Hello MQTT"
```

### 4. 配置 MQTT 认证（可选，生产环境推荐）

如果需要为 MQTT 添加用户名密码认证：

```bash
cd /opt/codehubot/docker

# 创建密码文件
docker-compose exec mqtt mosquitto_passwd -c /mosquitto/config/passwd mqtt_user

# 输入密码（会提示输入两次）

# 修改 mosquitto.conf 文件
nano mosquitto.conf
```

在 `mosquitto.conf` 中修改：

```
allow_anonymous false
password_file /mosquitto/config/passwd
```

然后重启容器：

```bash
docker-compose restart mqtt
```

**注意**: 如果配置了 MQTT 认证，需要在后端服务的 `.env` 文件中配置 `MQTT_USERNAME` 和 `MQTT_PASSWORD`。

### 5. 配置开机自启（可选）

**注意**: 系统服务配置为可选，用户可根据实际情况自行处理。

---

## 🚀 后端服务部署

### 1. 准备 Python 环境

**注意**: 请根据实际情况创建和配置 Python 虚拟环境。可以使用 `venv`、`virtualenv`、`conda` 等方式。

### 2. 安装依赖

```bash
cd /opt/codehubot/backend

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cd /opt/codehubot/backend

# 复制环境变量示例文件
cp env.example .env

# 编辑配置文件
nano .env
```

根据实际情况修改 `.env` 文件中的配置项：

**必须配置的项**：
- `DATABASE_URL`: 数据库连接URL，使用上面创建的数据库用户和密码
- `SECRET_KEY`: JWT密钥，必须至少32个字符
  - 生成方法：`python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `MQTT_BROKER_HOST`: MQTT服务器地址，如果使用Docker容器部署，使用 `localhost`
- `MQTT_USERNAME`: MQTT用户名（如果MQTT允许匿名访问，可以留空）
- `MQTT_PASSWORD`: MQTT密码（如果MQTT允许匿名访问，可以留空）

**重要配置说明**：
- `SECRET_KEY`: 必须至少32个字符，用于JWT签名
- `INTERNAL_API_KEY`: 用于插件服务调用后端API，如果配置了插件服务，必须与插件服务的 `BACKEND_API_KEY` 保持一致
  - 生成方法：`python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `SERVER_BASE_URL`: 服务器基础URL，用于生成固件下载链接等
- `ENVIRONMENT`: 运行环境，生产环境请设置为 `production`
- `LOG_LEVEL`: 日志级别，生产环境建议使用 `INFO`

**可选配置**：
- `REDIS_URL`: Redis连接URL（如果使用Redis缓存）
- `FIRMWARE_BASE_URL`: 固件下载基础URL（可选，默认使用SERVER_BASE_URL）
- `MAIL_*`: 邮件服务配置（如果不需要邮件功能可以不配置）
- 其他高级配置项通常使用默认值即可

### 4. 测试运行

```bash
# 确保虚拟环境已激活（如果使用虚拟环境）
# source venv/bin/activate

# 测试启动（前台运行）
python main.py
```

如果看到 "🚀 启动物联网设备服务系统" 且没有错误，说明配置正确。

按 `Ctrl+C` 停止服务。

### 5. 配置系统服务（可选）

**注意**: 系统服务配置为可选，用户可根据实际情况自行处理。可以使用 systemd、supervisor、pm2 等方式管理服务。

---

## 🎨 前端服务部署

### 1. 安装依赖

```bash
cd /opt/codehubot/frontend

# 安装 Node.js 依赖
npm install
```

### 2. 配置环境变量

```bash
cd /opt/codehubot/frontend

# 复制公共环境变量示例文件（可选，所有环境共用）
cp .env.example .env

# 复制生产环境变量示例文件
cp .env.production.example .env.production

# 编辑配置文件
nano .env.production
# 如果需要修改公共配置，也可以编辑 .env
nano .env
```

**环境变量文件说明**：
- `.env`: 公共配置，所有环境都会加载（可选）
- `.env.production`: 生产环境特定配置（必需）

根据实际情况修改配置文件中的配置项：

**必须配置的项**（在 `.env.production` 中）：
- `VITE_API_BASE_URL`: 后端 API 基础地址
  - **生产环境使用 Nginx 转发 API**，设置为 `/api`（相对路径）
  - Nginx 会将 `/api` 请求代理到后端服务 `http://127.0.0.1:8000`
  - 这样前后端使用同一域名，避免跨域问题

**可选配置**：
- 在 `.env` 中配置公共项（所有环境共用）：
  - `VITE_APP_TITLE`: 应用标题（用于页面标题和"关于系统"显示）
  - `VITE_APP_VERSION`: 应用版本（在"关于系统"中显示）
  - `VITE_API_TIMEOUT`: API 请求超时时间（毫秒，默认 10000）
- 在 `.env.production` 中配置生产环境特定项：
  - `VITE_DEBUG_MODE`: 是否启用调试模式（生产环境建议设为 `false`）

**生产环境配置示例**：

`.env.production`:
```bash
# 使用 Nginx 反向代理（生产环境标准配置）
VITE_API_BASE_URL=/api
VITE_DEBUG_MODE=false
```

`.env`（可选，公共配置）:
```bash
# 应用标题和版本
VITE_APP_TITLE=CodeHubot 物联网设备管理系统
VITE_APP_VERSION=1.0.0

# API 请求超时时间（毫秒）
VITE_API_TIMEOUT=10000
```

**注意**：
- Vite 会按优先级加载环境变量：`.env` → `.env.production`（后者会覆盖前者）
- 如果后端独立部署在不同域名，才需要设置为完整地址（不推荐）：
```bash
# 仅当后端独立部署时使用（不推荐）
# VITE_API_BASE_URL=https://api.your-domain.com
```

### 3. 构建生产版本

```bash
# 构建前端应用
npm run build
```

构建完成后，会在 `dist/` 目录生成静态文件。

### 4. 配置 Nginx 服务前端

```bash
sudo nano /etc/nginx/sites-available/codehubot-frontend
```

添加以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名或IP

    root /opt/codehubot/frontend/dist;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理到后端
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/codehubot-frontend /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

**注意**: 如果后端和前端使用同一个域名，可以合并到一个 Nginx 配置中。

---

## ⚙️ 配置服务部署

配置服务（config-service）为设备提供配置信息，包括设备UUID、MQTT配置等。

### 1. 准备 Python 环境

**注意**: 请根据实际情况创建和配置 Python 虚拟环境。

### 2. 安装依赖

```bash
cd /opt/codehubot/config-service

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cd /opt/codehubot/config-service

# 复制环境变量示例文件
cp env.example .env

# 编辑配置文件
nano .env
```

根据实际情况修改 `.env` 文件中的配置项：

**必须配置的项**：
- `PROVISIONING_DB_URL`: 数据库连接URL，使用 `aiot_device` 数据库
- `MQTT_BROKER`: MQTT服务器地址，如果使用Docker容器部署，使用 `localhost`
- `API_SERVER`: 后端API服务器地址
- `OTA_SERVER`: OTA固件服务器地址（通常与API_SERVER相同）

**重要配置说明**：
- `PROVISIONING_DB_URL`: 注意使用 `aiot_device` 数据库，不是 `aiot_admin`
- `MQTT_BROKER`: 如果MQTT使用Docker容器部署，使用 `localhost`
- `PORT`: 服务监听端口，默认为 8001

### 4. 配置系统服务（可选）

**注意**: 系统服务配置为可选，用户可根据实际情况自行处理。

### 5. 配置 Nginx 反向代理（可选）

如果需要通过域名访问，可以配置 Nginx：

```nginx
server {
    listen 80;
    server_name config.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🔌 插件服务部署

插件服务（plugin-service）为外部插件（如 Coze、GPT 等）提供设备控制接口。

### 1. 准备 Python 环境

**注意**: 请根据实际情况创建和配置 Python 虚拟环境。

### 2. 安装依赖

```bash
cd /opt/codehubot/plugin-service

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cd /opt/codehubot/plugin-service

# 复制环境变量示例文件
cp env.example .env

# 编辑配置文件
nano .env
```

根据实际情况修改 `.env` 文件中的配置项：

**必须配置的项**：
- `BACKEND_URL`: 后端API服务地址
- `BACKEND_API_KEY`: 后端内部API密钥，**必须与后端服务的 `INTERNAL_API_KEY` 完全一致**

**重要配置说明**：
- `BACKEND_API_KEY`: **必须与后端服务 `.env` 文件中的 `INTERNAL_API_KEY` 完全一致**，否则插件服务无法调用后端API
  - 生成方法：`python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `RELOAD`: 生产环境建议设置为 `false`
- `DEBUG_MODE`: 生产环境建议设置为 `false`
- `CORS_ORIGINS`: 生产环境建议设置为具体域名，而不是 `*`

### 4. 配置系统服务（可选）

**注意**: 系统服务配置为可选，用户可根据实际情况自行处理。

### 5. 配置 Nginx 反向代理（可选）

如果需要通过域名访问，可以配置 Nginx：

```nginx
server {
    listen 80;
    server_name plugin.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🎉 部署完成

现在你可以通过浏览器访问前端界面，开始使用 CodeHubot 系统了。

**默认管理员账号**：
- 邮箱: `admin@aiot.com`
- 用户名: `admin`
- 密码: `admin123`

### 部署检查清单

- [ ] 数据库已创建并导入数据
- [ ] MQTT 服务已启动并可以连接
- [ ] 后端服务已启动，可以访问 `/health` 端点
- [ ] 前端已构建并可以通过 Nginx 访问
- [ ] 配置服务已启动（如果使用）
- [ ] 插件服务已启动（如果使用）
- [ ] 所有服务的环境变量已正确配置

### 服务端口汇总

- **后端服务**: 8000
- **配置服务**: 8001
- **插件服务**: 9000
- **MQTT 服务**: 1883, 9001
- **前端**: 80 (通过 Nginx)
