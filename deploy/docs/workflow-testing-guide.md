# 工作流系统测试部署指南

本文档说明如何在另一台电脑上下载代码并部署系统进行测试。

## 📋 前置要求

### 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+ 或 CentOS 7+) 或 macOS
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.0+

### 必需软件安装

#### 1. 安装 Docker 和 Docker Compose

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

**macOS:**
```bash
# 使用 Homebrew 安装
brew install docker docker-compose

# 或下载 Docker Desktop (包含 Docker Compose)
# https://www.docker.com/products/docker-desktop
```

#### 2. 安装 Git

```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git
```

## 🚀 快速部署步骤

### 步骤 1: 克隆代码

```bash
# 克隆项目（使用你的 fork 仓库地址）
git clone https://github.com/zhangqx2025/CodeHubot.git
cd CodeHubot

# 切换到工作流功能分支
git checkout feature/workflow-system

# 或直接克隆指定分支
git clone -b feature/workflow-system https://github.com/zhangqx2025/CodeHubot.git
cd CodeHubot
```

### 步骤 2: 配置环境变量

```bash
# 进入 docker 目录
cd docker

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
# 注意：Windows 用户可以使用记事本或其他编辑器
nano .env
# 或
vim .env
```

**必须配置的环境变量：**

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=your_root_password_here
MYSQL_PASSWORD=your_db_password_here
MYSQL_USER=aiot_user
MYSQL_DATABASE=aiot_admin

# JWT 密钥（必须修改，使用以下命令生成）
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_generated_secret_key_here

# 内部 API 密钥（必须修改）
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
INTERNAL_API_KEY=your_generated_api_key_here

# 阿里云 API 密钥（用于向量化功能）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 服务器基础 URL（根据实际情况修改）
SERVER_BASE_URL=http://localhost:8000
```

**生成密钥的方法：**

```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 INTERNAL_API_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤 3: 执行自动化部署

```bash
# 返回项目根目录
cd ..

# 给部署脚本添加执行权限
chmod +x deploy.sh

# 执行完整部署（会自动构建镜像、启动服务、初始化数据库）
./deploy.sh deploy
```

**部署脚本会自动执行：**
1. ✅ 检查依赖（Docker、Docker Compose）
2. ✅ 检查环境配置文件
3. ✅ 生成密钥（如果未配置）
4. ✅ 停止现有服务
5. ✅ 构建所有 Docker 镜像
6. ✅ 启动基础服务（MySQL、Redis、MQTT）
7. ✅ 初始化数据库（执行 `SQL/init_database.sql`，包含工作流表）
8. ✅ 启动应用服务（Backend、Frontend、Celery 等）
9. ✅ 检查服务状态

### 步骤 4: 验证部署

部署完成后，脚本会显示服务访问地址：

```
服务访问地址：
  前端:          http://localhost:80
  后端API:       http://localhost:8000
  配置服务:      http://localhost:8001
  插件服务:      http://localhost:9000
  Flower监控:    http://localhost:5555/flower
  phpMyAdmin:    http://localhost:8081
```

**手动验证服务：**

```bash
# 查看所有服务状态
cd docker
docker-compose -f docker-compose.prod.yml ps

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost:80
```

## 🧪 测试工作流功能

### 1. 访问前端

打开浏览器访问：`http://localhost:80`

### 2. 登录系统

使用管理员账号登录（如果没有账号，需要先注册）

### 3. 测试工作流功能

1. **创建工作流**
   - 点击左侧菜单 "工作流管理"
   - 点击 "创建工作流" 按钮
   - 输入工作流名称
   - 在编辑器中添加节点和连线

2. **验证工作流**
   - 在编辑器中点击 "验证" 按钮
   - 检查验证结果

3. **执行工作流**
   - 在工作流列表中点击 "执行" 按钮
   - 输入执行参数（JSON 格式）
   - 查看执行结果

4. **查看执行历史**
   - 在工作流列表中点击 "执行历史" 按钮
   - 查看历史执行记录

## 🔧 常用管理命令

### 查看服务状态

```bash
cd docker
docker-compose -f docker-compose.prod.yml ps
```

### 查看服务日志

```bash
cd docker

# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f celery_worker
```

### 重启服务

```bash
cd docker

# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

### 停止服务

```bash
cd docker
docker-compose -f docker-compose.prod.yml down
```

### 停止并删除数据卷（清空所有数据）

```bash
cd ..
./deploy.sh clean
```

### 重新构建镜像

```bash
cd ..
./deploy.sh build
```

## 🐛 故障排查

### 问题 1: 数据库初始化失败

**症状**: 日志显示数据库连接失败或表不存在

**解决方案**:
```bash
# 手动执行数据库初始化
cd docker
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin

# 在 MySQL 中执行
source /docker-entrypoint-initdb.d/init-databases.sql;

# 或从宿主机执行
cd ..
mysql -h localhost -u aiot_user -p aiot_admin < SQL/init_database.sql
```

### 问题 2: 前端无法访问

**症状**: 浏览器无法打开前端页面

**解决方案**:
```bash
# 检查前端容器是否运行
cd docker
docker-compose -f docker-compose.prod.yml ps frontend

# 查看前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 重启前端服务
docker-compose -f docker-compose.prod.yml restart frontend
```

### 问题 3: 后端 API 返回 500 错误

**症状**: 前端调用 API 时返回 500 错误

**解决方案**:
```bash
# 查看后端日志
cd docker
docker-compose -f docker-compose.prod.yml logs -f backend

# 检查数据库连接
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import engine; engine.connect()"
```

### 问题 4: Vue Flow 依赖安装失败

**症状**: 前端构建时提示 Vue Flow 相关包找不到

**解决方案**:
```bash
# 进入前端目录手动安装依赖
cd frontend
npm install

# 如果使用国内网络，可以使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

### 问题 5: 工作流表不存在

**症状**: 执行工作流时提示表不存在

**解决方案**:
```bash
# 检查数据库表是否存在
cd docker
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin -e "SHOW TABLES LIKE 'aiot_workflow%';"

# 如果表不存在，手动执行迁移脚本
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin < /path/to/SQL/update/01_create_workflow_tables.sql

# 或从宿主机执行
cd ../..
mysql -h localhost -u aiot_user -p aiot_admin < SQL/update/01_create_workflow_tables.sql
```

## 📝 数据库迁移说明

### 如果数据库已存在（已有数据）

如果系统已经运行，数据库已存在，需要手动执行工作流表的迁移脚本：

```bash
# 方法 1: 通过 Docker 执行
cd docker
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin < /path/to/SQL/update/01_create_workflow_tables.sql

# 方法 2: 从宿主机执行（需要 MySQL 客户端）
mysql -h localhost -u aiot_user -p aiot_admin < SQL/update/01_create_workflow_tables.sql

# 方法 3: 通过 phpMyAdmin
# 访问 http://localhost:8081
# 选择 aiot_admin 数据库
# 导入 SQL/update/01_create_workflow_tables.sql 文件
```

### 验证表是否创建成功

```bash
cd docker
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin -e "SHOW TABLES LIKE 'aiot_workflow%';"
```

应该看到：
- `aiot_workflows`
- `aiot_workflow_executions`

## 🔄 更新代码

如果远程代码有更新，需要拉取最新代码：

```bash
# 拉取最新代码
git pull origin feature/workflow-system

# 重新构建和部署
./deploy.sh deploy
```

## 📚 相关文档

- [Docker 部署文档](./docker-deployment.md)
- [手动部署文档](./manual-deployment.md)
- [快速参考](./quick-reference.md)

## 💡 提示

1. **首次部署建议**: 使用 `./deploy.sh deploy` 进行完整部署，会自动处理所有步骤
2. **开发环境**: 如果需要频繁修改代码，可以使用 `./deploy.sh build` 只重新构建镜像
3. **查看日志**: 遇到问题时，首先查看服务日志：`cd docker && docker-compose -f docker-compose.prod.yml logs -f [服务名]`
4. **数据备份**: 在生产环境部署前，建议备份现有数据库

