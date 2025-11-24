# CodeHubot 部署快速参考

本文档提供常用的部署命令和配置信息快速参考。

## 服务端口

- **后端服务**: 8000
- **配置服务**: 8001
- **插件服务**: 9000
- **MQTT 服务**: 1883 (Docker 容器)
- **前端**: 80 (通过 Nginx)

## 常用命令

### 服务管理

```bash
# 查看服务状态
sudo systemctl status codehubot-backend
sudo systemctl status codehubot-config
sudo systemctl status codehubot-plugin

# 重启服务
sudo systemctl restart codehubot-backend
sudo systemctl restart codehubot-config
sudo systemctl restart codehubot-plugin

# 查看服务日志
sudo journalctl -u codehubot-backend -f
```

### MQTT 容器管理

```bash
cd /opt/codehubot/docker

# 启动/停止/重启
docker-compose up -d mqtt
docker-compose stop mqtt
docker-compose restart mqtt

# 查看状态和日志
docker-compose ps mqtt
docker-compose logs -f mqtt
```

### 健康检查

```bash
curl http://localhost:8000/health  # 后端
curl http://localhost:8001/health # 配置服务
curl http://localhost:9000/        # 插件服务
```

## 配置文件位置

- **后端**: `/opt/codehubot/backend/.env`
- **配置服务**: `/opt/codehubot/config-service/.env`
- **插件服务**: `/opt/codehubot/plugin-service/.env`
- **MQTT**: `/opt/codehubot/docker/mosquitto.conf`

## 关键配置

### 后端服务 (.env)

```bash
DATABASE_URL=mysql+pymysql://aiot_user:password@localhost:3306/aiot_admin
SECRET_KEY=your-secret-key-at-least-32-characters
INTERNAL_API_KEY=your-internal-api-key
MQTT_BROKER_HOST=localhost
MQTT_USERNAME=
MQTT_PASSWORD=
```

### 插件服务 (.env)

```bash
BACKEND_URL=http://localhost:8000
BACKEND_API_KEY=your-internal-api-key  # 必须与后端 INTERNAL_API_KEY 一致
```

## 数据库操作

```bash
# 连接数据库
mysql -u aiot_user -p aiot_admin

# 备份数据库
mysqldump -u aiot_user -p aiot_admin > backup.sql

# 恢复数据库
mysql -u aiot_user -p aiot_admin < backup.sql
```

## 代码更新

### 后端更新

```bash
cd /opt/codehubot/backend
git pull
pip install -r requirements.txt
sudo systemctl restart codehubot-backend
```

### 前端更新

```bash
cd /opt/codehubot/frontend
git pull
npm install
npm run build
sudo systemctl restart nginx
```

## 生成密钥

```bash
# 生成 SECRET_KEY 或 INTERNAL_API_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 故障排查

```bash
# 查看服务状态和日志
sudo systemctl status <service-name>
sudo journalctl -u <service-name> -f

# 检查端口占用
sudo lsof -i :8000

# 检查数据库连接
mysql -u aiot_user -p
```

---

更多详细信息请参考 [完整部署指南](./deployment-guide.md)
