# 外部数据库模式 - 快速开始

## 🎯 三步快速部署

### 步骤 1：准备外部数据库

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
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/init_database.sql
```

### 步骤 2：配置环境变量

```bash
# 复制配置模板
cp docker/.env.external-db.example docker/.env

# 编辑配置（修改以下内容）
nano docker/.env
```

**必须修改的配置**：

```bash
# 外部数据库配置
EXTERNAL_DB_HOST=192.168.1.100      # 你的 MySQL 地址
EXTERNAL_DB_PORT=3306
EXTERNAL_DB_USER=aiot_user
EXTERNAL_DB_PASSWORD=aiot_password
EXTERNAL_DB_NAME=aiot_admin

# 生成并设置密钥（生产环境必须！）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
INTERNAL_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 步骤 3：启动服务

```bash
# 一键部署
./deploy.sh deploy-external-db

# 或分步执行
./deploy.sh build-external-db    # 构建镜像
./deploy.sh start-external-db    # 启动服务
```

等待约 30 秒，访问：http://localhost

---

## 🔧 常用命令

```bash
# 查看状态
./deploy.sh status-external-db

# 查看日志
./deploy.sh logs-external-db [服务名]

# 重启服务
./deploy.sh restart-external-db

# 停止服务
./deploy.sh stop-external-db
```

---

## ⚠️ 常见问题

### 问题：本机 MySQL 连接失败

```bash
# macOS/Windows - 使用特殊域名
EXTERNAL_DB_HOST=host.docker.internal

# Linux - 使用宿主机 IP（不要用 localhost）
EXTERNAL_DB_HOST=192.168.1.100
```

### 问题：防火墙阻止连接

```bash
# Ubuntu
sudo ufw allow 3306/tcp

# CentOS
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
```

### 问题：MySQL 远程连接被拒绝

```bash
# 编辑 MySQL 配置
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 修改 bind-address
bind-address = 0.0.0.0

# 重启 MySQL
sudo systemctl restart mysql
```

---

## 📚 详细文档

查看完整文档：[EXTERNAL_DB_SETUP.md](EXTERNAL_DB_SETUP.md)

---

## 🆚 模式对比

| 特性 | 标准模式 | 外部数据库模式 |
|------|----------|----------------|
| 命令 | `./deploy.sh deploy` | `./deploy.sh deploy-external-db` |
| MySQL | Docker 容器 | 独立服务 |
| 配置文件 | `.env.example` | `.env.external-db.example` |
| compose 文件 | `docker-compose.prod.yml` | `docker-compose.external-db.yml` |

---

**快速切换模式**：

```bash
# 切换到外部数据库模式
cp docker/.env.external-db.example docker/.env
# 编辑 docker/.env
./deploy.sh deploy-external-db

# 切换回标准模式
cp docker/.env.example docker/.env
# 编辑 docker/.env
./deploy.sh deploy
```
