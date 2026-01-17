# 手动部署指南

> 传统方式手动部署CodeHubot（适合需要精细控制的场景）

---

## ⚠️ 注意事项

**推荐使用Docker部署**。手动部署步骤较多，仅适用于：
- 无法使用Docker的环境
- 需要精细控制部署过程
- 特殊的系统环境要求

如使用Docker，请查看[Docker部署指南](docker-deployment.md)。

---

## 📋 系统要求

- **操作系统**：Ubuntu 20.04+ / CentOS 7+ / macOS
- **Python**：3.8+
- **Node.js**：16+
- **MySQL**：5.7+ 或 8.0+
- **Redis**：6.0+
- **Nginx**：1.18+

---

## 🚀 部署步骤

### 1. 安装系统依赖

**Ubuntu/Debian**：
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server nginx
```

**CentOS/RHEL**：
```bash
sudo yum install -y python3 python3-pip nodejs npm mysql-server redis nginx
```

### 2. 配置MySQL数据库

```bash
# 启动MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 登录MySQL
mysql -uroot -p

# 创建数据库和用户
CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aiot_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aiot_admin.* TO 'aiot_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 导入数据库结构
mysql -uaiot_user -p aiot_admin < SQL/init_database.sql
```

### 3. 配置Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. 安装MQTT Broker

```bash
# 使用Docker（推荐）
docker run -d --name mqtt \
  -p 1883:1883 -p 9001:9001 \
  eclipse-mosquitto:2.0

# 或手动安装Mosquitto
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### 5. 部署后端服务

```bash
# 创建部署目录
sudo mkdir -p /opt/codehubot
cd /opt/codehubot

# 复制代码
git clone <repository> .

# 配置后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 测试启动
python main.py

# 配置systemd服务（生产环境）
sudo vim /etc/systemd/system/codehubot-backend.service
```

**systemd服务配置**：
```ini
[Unit]
Description=CodeHubot Backend Service
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/codehubot/backend
Environment="PATH=/opt/codehubot/backend/venv/bin"
ExecStart=/opt/codehubot/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start codehubot-backend
sudo systemctl enable codehubot-backend
sudo systemctl status codehubot-backend
```

### 6. 部署配置服务

```bash
cd /opt/codehubot/service/config-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp env.example .env
# 编辑 .env

# 配置systemd服务
sudo vim /etc/systemd/system/codehubot-config.service
```

**systemd配置类似backend，修改路径即可**

### 7. 部署MQTT服务

```bash
cd /opt/codehubot/service/mqtt-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp env.example .env
# 编辑 .env

# 配置systemd服务
sudo vim /etc/systemd/system/codehubot-mqtt-service.service
```

### 8. 部署前端

```bash
cd /opt/codehubot/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 部署到Nginx
sudo cp -r dist/* /var/www/html/codehubot/
```

### 9. 配置Nginx

```bash
sudo vim /etc/nginx/sites-available/codehubot
```

**Nginx配置**：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/html/codehubot;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 配置服务
    location /config-api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/codehubot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔧 服务管理

### 查看状态

```bash
sudo systemctl status codehubot-backend
sudo systemctl status codehubot-config
sudo systemctl status codehubot-mqtt-service
```

### 查看日志

```bash
sudo journalctl -u codehubot-backend -f
sudo journalctl -u codehubot-config -f
```

### 重启服务

```bash
sudo systemctl restart codehubot-backend
sudo systemctl restart codehubot-config
sudo systemctl restart codehubot-mqtt-service
```

---

## 🔒 生产环境配置

### 配置HTTPS（推荐）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

### 配置防火墙

```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 定时备份

```bash
# 添加备份脚本
sudo vim /opt/codehubot/backup.sh
```

**备份脚本**：
```bash
#!/bin/bash
BACKUP_DIR=/opt/backups/codehubot
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -uaiot_user -p'your_password' aiot_admin > $BACKUP_DIR/db_$DATE.sql

# 备份上传文件
tar czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/codehubot/backend/uploads

# 删除7天前的备份
find $BACKUP_DIR -mtime +7 -delete
```

```bash
# 添加定时任务
sudo crontab -e
# 每天凌晨2点备份
0 2 * * * /opt/codehubot/backup.sh
```

---

## 📊 监控配置

### 进程监控

```bash
# 安装Supervisor（可选）
sudo apt install supervisor

# 配置Supervisor管理服务
sudo vim /etc/supervisor/conf.d/codehubot.conf
```

---

## ❓ 常见问题

### 服务启动失败

```bash
# 查看详细日志
sudo journalctl -u codehubot-backend -n 50

# 检查配置文件
cat /opt/codehubot/backend/.env

# 检查端口占用
sudo lsof -i:8000
```

### 权限问题

```bash
# 修改目录权限
sudo chown -R www-data:www-data /opt/codehubot
sudo chmod -R 755 /opt/codehubot
```

### 数据库连接失败

```bash
# 检查MySQL状态
sudo systemctl status mysql

# 测试连接
mysql -h127.0.0.1 -uaiot_user -p aiot_admin
```

---

## 🔗 相关文档

- [Docker部署](docker-deployment.md) - 推荐的部署方式
- [快速参考](quick-reference.md) - 常用命令
- [开发环境](development-guide.md) - 本地开发配置

---

**更新时间**：2026-01-15
