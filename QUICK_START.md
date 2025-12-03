# 🚀 快速开始 - 工作流系统测试部署

本文档提供在另一台电脑上快速部署和测试工作流系统的步骤。

## 📋 前置要求

- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Git**: 2.0+
- **Python 3**: 用于生成密钥（可选）

## ⚡ 快速部署（3步完成）

### 步骤 1: 克隆代码

```bash
# 克隆工作流功能分支
git clone -b feature/workflow-system https://github.com/zhangqx2025/CodeHubot.git
cd CodeHubot
```

### 步骤 2: 配置环境变量

```bash
# 进入 docker 目录
cd docker

# 复制环境变量模板
cp .env.example .env

# 生成密钥并编辑配置
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python3 -c "import secrets; print('INTERNAL_API_KEY=' + secrets.token_urlsafe(32))" >> .env

# 编辑 .env 文件，设置以下必需配置：
# - DASHSCOPE_API_KEY: 你的阿里云 API 密钥（用于向量化）
# - MYSQL_ROOT_PASSWORD: MySQL root 密码
# - MYSQL_PASSWORD: MySQL 用户密码
nano .env  # 或使用其他编辑器
```

**必需配置项：**
```bash
# 数据库密码（请修改）
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_PASSWORD=your_db_password

# 阿里云 API 密钥（必需，用于向量化功能）
DASHSCOPE_API_KEY=your_dashscope_api_key

# 服务器 URL（本地测试保持默认即可）
SERVER_BASE_URL=http://localhost:8000
```

### 步骤 3: 执行自动化部署

```bash
# 返回项目根目录
cd ..

# 给部署脚本添加执行权限
chmod +x deploy.sh

# 执行完整部署
./deploy.sh deploy
```

**部署过程说明：**
- 脚本会自动检查依赖
- 自动生成密钥（如果未配置）
- 构建所有 Docker 镜像（首次需要较长时间）
- 启动所有服务
- 自动初始化数据库（包含工作流表）
- 检查服务健康状态

**预计时间：**
- 首次部署：10-20 分钟（取决于网络速度）
- 后续部署：3-5 分钟

## ✅ 验证部署

部署完成后，访问以下地址：

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **phpMyAdmin**: http://localhost:8081

### 测试工作流功能

1. **访问前端**: http://localhost
2. **注册/登录**: 创建账号或使用现有账号登录
3. **进入工作流管理**: 点击左侧菜单 "工作流管理"
4. **创建工作流**: 点击 "创建工作流" 按钮
5. **测试功能**: 
   - 添加节点（从左侧节点库拖拽）
   - 连接节点（从一个节点拖到另一个节点）
   - 配置节点（点击节点打开配置面板）
   - 保存工作流
   - 验证工作流
   - 执行工作流

## 🔧 常用命令

### 查看服务状态
```bash
cd docker
docker-compose -f docker-compose.prod.yml ps
```

### 查看日志
```bash
cd docker

# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 重启服务
```bash
cd docker
docker-compose -f docker-compose.prod.yml restart backend
```

### 停止服务
```bash
cd docker
docker-compose -f docker-compose.prod.yml down
```

### 重新部署
```bash
cd ..
./deploy.sh deploy
```

## 🐛 常见问题

### 1. 端口被占用

**错误**: `port is already allocated`

**解决**: 修改 `docker/.env` 文件中的端口配置，或停止占用端口的服务

### 2. 数据库初始化失败

**解决**: 手动执行数据库初始化
```bash
cd docker
docker-compose -f docker-compose.prod.yml exec mysql mysql -u aiot_user -p aiot_admin < /path/to/SQL/init_database.sql
```

### 3. 前端构建失败（Vue Flow 依赖）

**解决**: 手动安装前端依赖
```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
```

### 4. 工作流表不存在

**解决**: 如果数据库已存在，需要手动执行迁移脚本
```bash
# 通过 phpMyAdmin 导入
# 访问 http://localhost:8081
# 选择 aiot_admin 数据库
# 导入 SQL/update/01_create_workflow_tables.sql

# 或通过命令行
mysql -h localhost -u aiot_user -p aiot_admin < SQL/update/01_create_workflow_tables.sql
```

## 📚 详细文档

- [完整测试部署指南](./deploy/docs/workflow-testing-guide.md)
- [Docker 部署文档](./deploy/docs/docker-deployment.md)
- [手动部署文档](./deploy/docs/manual-deployment.md)

## 💡 提示

1. **首次部署**: 建议使用 `./deploy.sh deploy` 完整部署
2. **查看日志**: 遇到问题时先查看服务日志
3. **数据持久化**: 所有数据存储在 Docker 卷中，删除容器不会删除数据
4. **更新代码**: `git pull` 后执行 `./deploy.sh deploy` 重新部署

