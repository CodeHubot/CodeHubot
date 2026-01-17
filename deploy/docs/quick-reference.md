# 快速参考手册

> 常用命令和配置速查

---

## 🔌 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 8080 | Web界面 |
| 后端API | 8000 | 主服务 |
| 配置服务 | 8001 | 设备配置 |
| 插件服务 | 9000 | 插件管理 |
| MQTT | 1883 | 设备通信 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |

---

## 🐳 Docker命令

### 基本操作

```bash
# 一键部署
./deploy.sh

# 查看服务状态
docker-compose -f docker/docker-compose.yml ps

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f [服务名]

# 重启服务
docker-compose -f docker/docker-compose.yml restart [服务名]

# 停止所有服务
docker-compose -f docker/docker-compose.yml down
```

### 常用服务名
- `backend` - 后端服务
- `frontend` - 前端服务
- `mqtt-service` - MQTT消息处理
- `config-service` - 配置服务
- `mysql` - 数据库
- `redis` - 缓存
- `mqtt` - MQTT Broker

---

## 📝 配置文件位置

### Docker部署
- 环境变量：`docker/.env`
- 数据库初始化：`SQL/init_database.sql`
- MQTT配置：`docker/mosquitto.conf`

### 本地开发
- 后端：`backend/.env`
- MQTT服务：`service/mqtt-service/.env`
- 配置服务：`service/config-service/.env`
- 前端：`frontend/.env.development`

---

## 🔍 健康检查

```bash
# 后端服务
curl http://localhost:8000/api/health

# 配置服务
curl http://localhost:8001/health

# 插件服务
curl http://localhost:9000/

# 前端
curl http://localhost:8080
```

---

## 🛠️ 故障排查

### 服务无法启动

```bash
# 1. 查看日志
docker-compose -f docker/docker-compose.yml logs [服务名]

# 2. 检查端口占用
lsof -i:8000  # 后端
lsof -i:3306  # MySQL

# 3. 检查配置
docker-compose -f docker/docker-compose.yml config
```

### 数据库连接失败

```bash
# 检查MySQL状态
docker-compose -f docker/docker-compose.yml ps mysql

# 进入MySQL容器
docker-compose -f docker/docker-compose.yml exec mysql mysql -uroot -p

# 测试连接
mysql -h127.0.0.1 -uaiot_user -p aiot_admin
```

### MQTT连接问题

```bash
# 检查MQTT状态
docker-compose -f docker/docker-compose.yml ps mqtt

# 查看MQTT日志
docker-compose -f docker/docker-compose.yml logs mqtt

# 测试MQTT连接（需安装mosquitto-clients）
mosquitto_sub -h localhost -t '#' -v
```

---

## 🔑 关键环境变量

### 必须配置

```bash
# JWT密钥（生产环境必改！）
SECRET_KEY=your-secret-key-here

# 内部API密钥
INTERNAL_API_KEY=your-internal-api-key-here

# 阿里云密钥（AI功能需要）
DASHSCOPE_API_KEY=sk-your-key-here

# 设备MQTT地址（设备需要连接的地址）
DEVICE_MQTT_BROKER=mqtt.example.com
```

### 数据库配置

```bash
# Docker内置MySQL
MYSQL_USER=aiot_user
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=aiot_admin

# 外部MySQL
EXTERNAL_DB_HOST=192.168.1.100
EXTERNAL_DB_PORT=3306
EXTERNAL_DB_USER=aiot_user
EXTERNAL_DB_PASSWORD=your-password
EXTERNAL_DB_NAME=aiot_admin
```

---

## 📊 数据库管理

### 备份

```bash
# 导出数据库
docker-compose -f docker/docker-compose.yml exec mysql \
  mysqldump -uroot -p aiot_admin > backup_$(date +%Y%m%d).sql

# 或使用Docker外部命令
mysqldump -h127.0.0.1 -uroot -p aiot_admin > backup.sql
```

### 恢复

```bash
# 导入数据库
docker-compose -f docker/docker-compose.yml exec -T mysql \
  mysql -uroot -p aiot_admin < backup.sql

# 或
mysql -h127.0.0.1 -uroot -p aiot_admin < backup.sql
```

### 初始化

```bash
# 首次部署自动初始化
# 手动初始化
mysql -h127.0.0.1 -uroot -p aiot_admin < SQL/init_database.sql
```

---

## 🔒 安全检查清单

部署前务必检查：

- [ ] SECRET_KEY 已修改（不是示例值）
- [ ] INTERNAL_API_KEY 已修改
- [ ] 数据库密码已修改
- [ ] 管理员密码已修改（首次登录后）
- [ ] 阿里云密钥已配置
- [ ] DEVICE_MQTT_BROKER 已配置

---

## 📞 获取帮助

- 📖 [完整部署文档](README.md)
- 📖 [环境变量说明](../../docs/环境变量配置说明.md)
- 📖 [快速开始指南](../../QUICK_START.md)
- 💬 [提交Issue](https://gitee.com/codehubot/CodeHubot/issues)
- 📖 [查看文档](../README.md)
- 🌐 [Gitee仓库](https://gitee.com/codehubot/CodeHubot)

---

**更新时间**：2026-01-15
