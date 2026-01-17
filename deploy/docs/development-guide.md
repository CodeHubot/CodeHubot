# 开发环境配置指南

> 本地开发环境快速搭建

---

## 🎯 开发模式说明

基础服务用Docker，应用服务本地运行，方便调试和热重载。

**优势**：
- ✅ 代码修改立即生效
- ✅ 方便断点调试
- ✅ 快速迭代开发

---

## 🚀 快速开始

### 1. 启动基础服务

```bash
cd docker
docker-compose up -d mysql redis mqtt
```

### 2. 配置后端

```bash
cd backend
cp env.example .env
# 编辑 .env 文件

# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py
```

### 3. 配置前端

```bash
cd frontend
cp .env.development.example .env.development
# 编辑 .env.development

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 配置MQTT服务（可选）

```bash
cd service/mqtt-service
cp env.example .env
# 编辑 .env

pip install -r requirements.txt
python main.py
```

### 5. 配置Config服务（可选）

```bash
cd service/config-service
cp env.example .env
# 编辑 .env

pip install -r requirements.txt
python main.py
```

---

## 📝 配置说明

### 后端配置（backend/.env）

```bash
# 数据库连接（Docker中的MySQL）
DB_HOST=localhost
DB_PORT=3306
DB_USER=aiot_user
DB_PASSWORD=aiot_password
DB_NAME=aiot_admin

# MQTT连接（Docker中的MQTT）
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# JWT密钥（开发环境可用示例值）
SECRET_KEY=dev-secret-key-at-least-32-characters-long
INTERNAL_API_KEY=dev-internal-api-key

# Redis连接
REDIS_URL=redis://localhost:6379

# 服务器配置
SERVER_BASE_URL=http://localhost:8000
```

### 前端配置（frontend/.env.development）

```bash
# 后端API地址
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🔧 开发工具推荐

### Python开发

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8
```

### 前端开发

```bash
# VSCode插件推荐
- Vue Language Features (Volar)
- ESLint
- Prettier
```

---

## 🐛 调试技巧

### 后端调试

**VSCode launch.json**：
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 前端调试

```bash
# 开发模式（支持热重载）
npm run dev

# 构建测试
npm run build
npm run preview
```

### 数据库调试

```bash
# 进入Docker中的MySQL
docker exec -it codehubot-mysql mysql -uroot -p

# 或使用MySQL客户端
mysql -h127.0.0.1 -uaiot_user -p aiot_admin
```

---

## 📊 常用命令

### 数据库管理

```bash
# 重置数据库
mysql -h127.0.0.1 -uroot -p aiot_admin < SQL/init_database.sql

# 备份数据库
mysqldump -h127.0.0.1 -uroot -p aiot_admin > backup.sql
```

### 代码质量

```bash
# Python代码格式化
cd backend
black .
flake8 .

# 前端代码检查
cd frontend
npm run lint
npm run lint:fix
```

### 清理缓存

```bash
# Python缓存
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 前端缓存
cd frontend
rm -rf node_modules dist .vite
npm install
```

---

## 🔄 热重载说明

### 后端热重载

```bash
# uvicorn 自动重载
python main.py  # 代码修改后自动重启
```

### 前端热重载

```bash
# Vite 自动刷新
npm run dev  # 代码修改后自动刷新浏览器
```

---

## ❓ 常见问题

### 端口冲突

```bash
# 修改后端端口（main.py）
uvicorn.run(app, host="0.0.0.0", port=8001)

# 修改前端端口（vite.config.js）
server: { port: 3001 }
```

### 数据库连接失败

```bash
# 检查MySQL是否启动
docker ps | grep mysql

# 启动MySQL
docker-compose -f docker/docker-compose.yml up -d mysql
```

### 依赖安装失败

```bash
# Python依赖
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# 前端依赖
rm -rf node_modules package-lock.json
npm install
```

---

## 🔗 相关文档

- [Docker部署](docker-deployment.md) - 生产环境部署
- [快速参考](quick-reference.md) - 常用命令
- [环境变量说明](../../docs/环境变量配置说明.md)

---

**更新时间**：2026-01-15
