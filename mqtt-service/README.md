# AIOT MQTT 独立服务

## 📖 简介

MQTT服务已从主backend中分离出来，作为独立服务运行。

**架构优势：**
- ✅ 不影响主backend的HTTP请求性能
- ✅ 可独立扩展和重启
- ✅ 专注于MQTT消息处理
- ✅ 更好的资源隔离

## 🏗️ 架构

```
设备MQTT客户端
    ↓ MQTT协议
MQTT Broker (Mosquitto)
    ↓ MQTT订阅
MQTT服务 (本服务，端口独立)
    ↓ 数据库写入
MySQL数据库
```

**主backend：**
- 处理HTTP API请求
- 不再监听MQTT消息

**MQTT服务（本服务）：**
- 专门监听MQTT消息
- 处理设备数据上报
- 更新设备状态到数据库

## 📦 安装部署

### 1. 安装依赖

```bash
cd mqtt-service
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp env.example .env
nano .env
```

配置内容：
```env
# MQTT Broker配置
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aiot_admin
DB_USER=root
DB_PASSWORD=your_password
```

### 3. 启动服务

#### 开发模式
```bash
python main.py
```

#### 生产模式（systemd）

创建 `/etc/systemd/system/mqtt-service.service`:

```ini
[Unit]
Description=AIOT MQTT Service
After=network.target mysql.service mosquitto.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/mqtt-service
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/mqtt-service/.env
ExecStart=/path/to/venv/bin/python /path/to/mqtt-service/main.py
Restart=always
RestartSec=5

# 日志
StandardOutput=append:/var/log/mqtt-service.log
StandardError=append:/var/log/mqtt-service-error.log

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-service
sudo systemctl start mqtt-service
sudo systemctl status mqtt-service
```

### 4. Docker部署（推荐）

参见 `Dockerfile` 和 `docker-compose.yml`

## 🔧 功能特性

### 支持的MQTT主题

| 主题 | 说明 | 示例 |
|------|------|------|
| `devices/{uuid}/data` | 传感器数据上报 | 温度、湿度等 |
| `devices/{uuid}/status` | 设备状态更新 | 在线、离线等 |
| `devices/{uuid}/heartbeat` | 设备心跳 | 保持活跃 |

### 数据处理流程

1. **传感器数据** (`data`)
   - 更新 `last_report_data` 字段
   - 更新 `last_seen` 时间
   - 设置 `is_online = True`

2. **设备状态** (`status`)
   - 更新 `last_report_data` 字段
   - 更新 `device_status` 字段
   - 更新 `last_seen` 时间

3. **心跳数据** (`heartbeat`)
   - 更新 `last_seen` 时间
   - 更新 `last_heartbeat` 时间
   - 设置 `is_online = True`

## 📊 监控和日志

### 查看日志

```bash
# systemd服务
sudo journalctl -u mqtt-service -f

# 或查看日志文件
tail -f mqtt_service.log
```

### 日志级别

- **INFO**: 正常运行信息
- **WARNING**: 警告信息（如设备不存在）
- **ERROR**: 错误信息（如数据库连接失败）

## 🔍 测试

### 测试MQTT连接

```bash
# 发布测试消息
mosquitto_pub -h localhost -t "devices/test-device-uuid/data" \
  -m '{"temperature": 25.5, "humidity": 60}'

# 订阅主题（查看消息）
mosquitto_sub -h localhost -t "devices/#"
```

### 验证数据库更新

```sql
SELECT 
    device_id,
    name,
    is_online,
    last_seen,
    JSON_PRETTY(last_report_data) as last_data
FROM aiot_core_devices
WHERE device_id = 'test-device'
ORDER BY last_seen DESC
LIMIT 1;
```

## ⚠️ 故障排除

### 问题1：MQTT连接失败

**错误：** `❌ MQTT连接失败，错误代码: 5`

**解决：**
```bash
# 检查MQTT Broker是否运行
sudo systemctl status mosquitto

# 检查端口
netstat -tlnp | grep 1883

# 测试连接
mosquitto_sub -h localhost -t test
```

### 问题2：数据库连接失败

**错误：** `❌ 数据库连接失败`

**解决：**
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 测试数据库连接
mysql -h localhost -u root -p aiot_admin

# 检查.env配置
cat .env
```

### 问题3：设备不存在

**警告：** `⚠️ 设备不存在: xxx`

**原因：** MQTT消息中的UUID在数据库中不存在

**解决：**
- 检查设备UUID是否正确
- 在数据库中添加该设备

### 问题4：服务频繁重启

**解决：**
```bash
# 查看详细日志
sudo journalctl -u mqtt-service -n 100

# 检查资源使用
top -p $(pgrep -f mqtt-service)
```

## 📈 性能优化

### 数据库连接池

已配置连接池：
- 初始连接数：5
- 最大溢出：10
- 连接回收：3600秒

### MQTT QoS

使用 QoS=1 确保消息至少送达一次

## 🔄 升级和维护

### 升级服务

```bash
cd mqtt-service

# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl restart mqtt-service
```

### 备份和恢复

服务本身无状态，只需要备份：
- `.env` 配置文件
- 数据库（由主backend负责）

## 🚀 与主Backend的对比

| 特性 | 主Backend | MQTT服务 |
|------|----------|---------|
| **HTTP API** | ✅ 处理 | ❌ 不处理 |
| **MQTT消息** | ❌ 不处理 | ✅ 处理 |
| **数据库访问** | ✅ 完整 | ✅ 只读写设备表 |
| **性能影响** | 无MQTT开销 | 专注MQTT |
| **独立部署** | 是 | 是 |

## 📝 注意事项

1. **确保只有一个MQTT服务实例运行**
   - 避免重复处理消息
   - 如需高可用，使用MQTT客户端ID区分

2. **主backend不再启动MQTT服务**
   - 检查 `main.py` 已移除MQTT相关代码
   - 避免端口冲突

3. **数据库表一致性**
   - MQTT服务使用简化的模型定义
   - 只更新必要的字段
   - 不创建新表

## 🔗 相关服务

- **主Backend**: 端口 8000
- **MQTT Broker**: 端口 1883
- **MySQL**: 端口 3306

---

**服务正常运行标志：**
```
🎉 MQTT连接成功 - Broker: localhost:1883
📡 订阅主题: devices/+/data
📡 订阅主题: devices/+/status
📡 订阅主题: devices/+/heartbeat
🚀 MQTT服务已启动
```

有问题请查看日志或联系管理员！

