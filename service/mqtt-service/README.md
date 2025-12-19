# AIOT MQTT 独立服务

## 📖 简介

MQTT服务已从主backend中分离出来，作为独立服务运行。

**架构优势：**
- ✅ 不影响主backend的HTTP请求性能
- ✅ 可独立扩展和重启
- ✅ 专注于MQTT消息处理
- ✅ 更好的资源隔离
- ✅ 支持多种数据格式（HTTP API 格式和 MQTT 简单格式）
- ✅ 自动重连和错误恢复
- ✅ 数据验证和清理
- ✅ 性能监控和统计

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
- 不再依赖 paho-mqtt 库

**MQTT服务（本服务）：**
- 专门监听MQTT消息
- 处理设备数据上报
- 更新设备状态到数据库
- 支持传感器数据存储（与 HTTP API 格式兼容）

## 📦 安装部署

### 方式一：Docker 部署（推荐）

最简单的部署方式，包含完整的服务栈（MySQL、Mosquitto、后端、前端、MQTT服务）。

```bash
cd docker
cp .env.example .env
# 编辑 .env 配置文件
nano .env

# 启动所有服务（包含 MQTT 服务）
docker-compose -f docker-compose.with-mqtt.yml up -d

# 查看服务状态
docker-compose -f docker-compose.with-mqtt.yml ps

# 查看 MQTT 服务日志
docker-compose -f docker-compose.with-mqtt.yml logs -f mqtt-service
```

### 方式二：Systemd 服务部署

适合已有数据库和 MQTT Broker 的环境。

#### 1. 准备环境

```bash
cd service/mqtt-service

# 复制并编辑环境配置
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

#### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv /opt/codehubot/venv
source /opt/codehubot/venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 测试运行

```bash
# 测试数据库连接
python3 -c "
from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
db.execute(text('SELECT 1'))
print('✅ 数据库连接正常')
"

# 运行服务（测试）
python main.py
```

#### 4. 安装为系统服务

```bash
# 使用安装脚本（推荐）
sudo bash install.sh

# 或手动安装
sudo cp mqtt-service.service /etc/systemd/system/
sudo systemctl daemon-reload
```

#### 5. 启动服务

```bash
# 启用开机自启
sudo systemctl enable mqtt-service

# 启动服务
sudo systemctl start mqtt-service

# 查看状态
sudo systemctl status mqtt-service

# 查看日志
sudo journalctl -u mqtt-service -f
```

### 方式三：开发模式

适合本地开发和调试。

```bash
cd service/mqtt-service

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
nano .env

# 直接运行
python main.py
```

## 🔧 功能特性

### 支持的MQTT主题

| 主题 | 说明 | 示例 |
|------|------|------|
| `devices/{uuid}/data` | 传感器数据上报 | 温度、湿度等 |
| `devices/{uuid}/status` | 设备状态更新 | 在线、离线等 |
| `devices/{uuid}/heartbeat` | 设备心跳 | 保持活跃 |

### 数据格式支持

MQTT 服务支持两种数据格式，自动识别并转换为统一的存储格式：

#### 1. HTTP API 格式（推荐）

与后端 HTTP API `/api/devices/data/upload` 完全兼容：

```json
{
  "sensors": [
    {
      "sensor_name": "temperature",
      "value": 25.5,
      "unit": "°C",
      "timestamp": "2025-12-19T14:30:00+08:00"
    },
    {
      "sensor_name": "humidity",
      "value": 60,
      "unit": "%"
    }
  ],
  "status": {
    "ip_address": "192.168.1.100",
    "rssi": -50,
    "battery": 95
  },
  "location": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "timestamp": "2025-12-19T14:30:00+08:00"
}
```

#### 2. MQTT 简单格式

适合资源受限的设备（如 ESP32）：

```json
{
  "temperature": 25.5,
  "humidity": 60,
  "light": 850
}
```

自动转换为标准格式存储：
```json
{
  "sensors": {
    "temperature": {"value": 25.5, "unit": "", "timestamp": "..."},
    "humidity": {"value": 60, "unit": "", "timestamp": "..."},
    "light": {"value": 850, "unit": "", "timestamp": "..."}
  },
  "upload_timestamp": "..."
}
```

### 数据处理流程

1. **传感器数据** (`data`)
   - 支持 HTTP API 格式和 MQTT 简单格式
   - 自动验证传感器名称和数值
   - 转换为统一的存储格式
   - 更新 `last_report_data` 字段
   - 更新 `last_seen` 时间
   - 设置 `is_online = True`

2. **设备状态** (`status`)
   - 合并到 `last_report_data.status` 字段
   - 更新 `device_status` 字段
   - 更新 `last_seen` 时间

3. **心跳数据** (`heartbeat`)
   - 更新 `last_seen` 时间
   - 更新 `last_heartbeat` 时间
   - 设置 `is_online = True`

### 数据验证

- **传感器名称**：只允许小写字母、数字、下划线，长度 1-50，不能以数字开头
- **传感器值**：必须是数字类型（int 或 float）
- **位置信息**：纬度 -90~90，经度 -180~180
- **JSON 格式**：自动检查和修复

### 错误处理

- **自动重连**：断线后使用指数退避算法自动重连
- **错误恢复**：数据库操作失败自动回滚
- **日志记录**：详细的错误日志和堆栈信息
- **优雅降级**：部分数据错误不影响整体服务

### 性能监控

- **实时统计**：总消息数、成功数、失败数、成功率
- **定时报告**：每 5 分钟自动打印统计信息
- **运行时长**：显示服务运行时间
- **连接状态**：MQTT 连接状态监控

## 📊 监控和日志

### 查看日志

```bash
# Docker 部署
docker-compose -f docker-compose.with-mqtt.yml logs -f mqtt-service

# Systemd 服务
sudo journalctl -u mqtt-service -f

# 或查看日志文件
tail -f /var/log/codehubot/mqtt-service.log
tail -f /var/log/codehubot/mqtt-service-error.log

# 开发模式
tail -f mqtt_service.log
```

### 日志级别

- **INFO**: 正常运行信息（连接、消息处理、统计）
- **WARNING**: 警告信息（设备不存在、数据格式错误）
- **ERROR**: 错误信息（数据库连接失败、MQTT断线）
- **DEBUG**: 调试信息（详细的数据处理过程）

### 统计信息

服务每 5 分钟自动打印统计信息：

```
======================================================================
📊 MQTT服务统计信息
======================================================================
  运行时间: 2:30:15
  连接状态: ✅ 已连接
  总消息数: 1523
  成功处理: 1520
  处理失败: 3
  成功率: 99.80%
  最后消息: 2025-12-19 14:30:00
======================================================================
```

### 服务管理命令

```bash
# 查看服务状态
sudo systemctl status mqtt-service

# 启动服务
sudo systemctl start mqtt-service

# 停止服务
sudo systemctl stop mqtt-service

# 重启服务
sudo systemctl restart mqtt-service

# 查看服务是否启用
sudo systemctl is-enabled mqtt-service

# 禁用开机自启
sudo systemctl disable mqtt-service
```

## 🔍 测试

### 测试MQTT连接

#### 方式一：HTTP API 格式

```bash
# 发布传感器数据（完整格式）
mosquitto_pub -h localhost -t "devices/test-device-uuid/data" \
  -m '{
    "sensors": [
      {"sensor_name": "temperature", "value": 25.5, "unit": "°C"},
      {"sensor_name": "humidity", "value": 60, "unit": "%"}
    ],
    "status": {
      "ip_address": "192.168.1.100",
      "rssi": -50
    },
    "timestamp": "2025-12-19T14:30:00+08:00"
  }'
```

#### 方式二：MQTT 简单格式

```bash
# 发布传感器数据（简单格式）
mosquitto_pub -h localhost -t "devices/test-device-uuid/data" \
  -m '{"temperature": 25.5, "humidity": 60, "light": 850}'
```

#### 发布设备状态

```bash
# 设备状态更新
mosquitto_pub -h localhost -t "devices/test-device-uuid/status" \
  -m '{"status": "online", "battery": 95, "signal": "good"}'
```

#### 发布心跳

```bash
# 心跳数据
mosquitto_pub -h localhost -t "devices/test-device-uuid/heartbeat" \
  -m '{"timestamp": "2025-12-19T14:30:00+08:00"}'
```

#### 订阅主题（查看消息）

```bash
# 订阅所有设备主题
mosquitto_sub -h localhost -t "devices/#"

# 订阅特定设备
mosquitto_sub -h localhost -t "devices/test-device-uuid/#"
```

### 验证数据库更新

```sql
-- 查看设备最新数据
SELECT 
    device_id,
    name,
    is_online,
    last_seen,
    JSON_PRETTY(last_report_data) as last_data
FROM device_main
WHERE uuid = 'test-device-uuid'
LIMIT 1;

-- 查看传感器数据
SELECT 
    device_id,
    name,
    JSON_EXTRACT(last_report_data, '$.sensors') as sensors,
    JSON_EXTRACT(last_report_data, '$.upload_timestamp') as upload_time
FROM device_main
WHERE last_report_data IS NOT NULL
ORDER BY last_seen DESC
LIMIT 10;
```

### 使用测试脚本

项目提供了完整的测试脚本：

```bash
# HTTP API 测试（后端）
cd backend
python test_sensor_upload.py

# MQTT 测试脚本（可以自己创建）
cd service/mqtt-service
python test_mqtt_publish.py
```

## ⚠️ 故障排除

### 问题1：MQTT连接失败

**错误：** `❌ MQTT连接失败: 用户名或密码错误`

**解决：**
```bash
# 1. 检查MQTT Broker是否运行
sudo systemctl status mosquitto

# 2. 检查端口
netstat -tlnp | grep 1883

# 3. 测试连接
mosquitto_sub -h localhost -t test

# 4. 检查认证配置
cat /etc/mosquitto/mosquitto.conf

# 5. 检查 .env 配置
cat .env | grep MQTT
```

### 问题2：数据库连接失败

**错误：** `❌ 数据库连接失败`

**解决：**
```bash
# 1. 检查MySQL服务
sudo systemctl status mysql

# 2. 测试数据库连接
mysql -h localhost -u root -p aiot_admin

# 3. 检查.env配置
cat .env | grep DB_

# 4. 检查防火墙
sudo ufw status

# 5. 检查数据库用户权限
mysql -u root -p -e "SHOW GRANTS FOR 'root'@'%';"
```

### 问题3：设备不存在

**警告：** `⚠️ 设备不存在: xxx`

**原因：** MQTT消息中的UUID在数据库中不存在

**解决：**
```bash
# 1. 检查设备UUID是否正确
# 2. 在数据库中添加该设备
# 3. 确认设备已注册

# 查询数据库中的设备
mysql -u root -p aiot_admin -e "
SELECT uuid, device_id, name 
FROM device_main 
WHERE uuid = 'your-device-uuid';
"
```

### 问题4：服务频繁重启

**解决：**
```bash
# 1. 查看详细日志
sudo journalctl -u mqtt-service -n 100

# 2. 检查资源使用
top -p $(pgrep -f mqtt-service)

# 3. 检查系统日志
sudo tail -f /var/log/syslog | grep mqtt

# 4. 临时禁用自动重启（调试用）
sudo systemctl edit mqtt-service
# 添加: Restart=no

# 5. 手动运行查看错误
cd /opt/codehubot/service/mqtt-service
source /opt/codehubot/venv/bin/activate
python main.py
```

### 问题5：JSON 解析失败

**错误：** `❌ JSON解析失败: Expecting value: line 1 column 1 (char 0)`

**原因：** MQTT 消息不是有效的 JSON 格式

**解决：**
```bash
# 1. 检查发送的消息格式
mosquitto_sub -h localhost -t "devices/#" -v

# 2. 确保消息是有效的 JSON
echo '{"temperature": 25.5}' | jq .

# 3. 检查设备端的数据序列化
```

### 问题6：数据验证失败

**警告：** `⚠️ 传感器名称格式不正确，跳过: 123abc`

**原因：** 传感器名称不符合命名规范

**规范：**
- 只能包含小写字母、数字、下划线
- 长度 1-50 字符
- 不能以数字开头
- 示例：`temperature`, `humidity`, `sensor_1`

### 问题7：Docker 容器无法启动

**解决：**
```bash
# 1. 查看容器日志
docker-compose -f docker-compose.with-mqtt.yml logs mqtt-service

# 2. 检查环境变量
docker-compose -f docker-compose.with-mqtt.yml config

# 3. 检查网络连接
docker network ls
docker network inspect codehubot_codehubot-network

# 4. 重新构建镜像
docker-compose -f docker-compose.with-mqtt.yml build mqtt-service

# 5. 清理并重新启动
docker-compose -f docker-compose.with-mqtt.yml down -v
docker-compose -f docker-compose.with-mqtt.yml up -d
```

### 问题8：性能下降

**症状：** 消息处理延迟增加

**解决：**
```bash
# 1. 查看统计信息（在日志中）
grep "📊 MQTT服务统计" /var/log/codehubot/mqtt-service.log

# 2. 检查数据库性能
mysql -u root -p aiot_admin -e "SHOW PROCESSLIST;"

# 3. 检查慢查询
mysql -u root -p aiot_admin -e "
SELECT * FROM device_main 
WHERE last_seen > NOW() - INTERVAL 1 HOUR;
"

# 4. 优化数据库索引
mysql -u root -p aiot_admin -e "
SHOW INDEX FROM device_main;
"

# 5. 增加资源限制
sudo systemctl edit mqtt-service
# 修改: MemoryLimit=1G, CPUQuota=100%
```

## 📈 性能优化

### 数据库连接池

已配置连接池优化性能：
- 初始连接数：5
- 最大溢出：10
- 连接回收：3600秒
- 预检查：启用

### MQTT QoS

使用 QoS=1 确保消息至少送达一次，平衡性能和可靠性。

### 自动重连

- **指数退避算法**：重连延迟从 2 秒开始，每次翻倍，最大 300 秒
- **无限重试**：持续尝试重连，不会因网络波动而停止服务
- **状态恢复**：重连成功后自动重新订阅主题

### 资源限制

Systemd 服务配置了资源限制：
- 内存限制：512M
- CPU 限制：50%
- 防止资源占用过高

### 批量处理建议

- **合并上报**：多个传感器数据在一条消息中发送
- **上报频率**：建议 30 秒 ~ 5 分钟
- **心跳分离**：高频心跳（每 10 秒）与低频数据上报分开

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
| **资源使用** | 中等 | 低 |
| **重启影响** | 影响HTTP请求 | 不影响HTTP |
| **扩展性** | 垂直扩展 | 水平扩展 |

## 📝 注意事项

### 1. 服务实例管理

**确保只有一个MQTT服务实例运行**
- ✅ 避免重复处理消息
- ✅ 避免数据库并发冲突
- ❌ 如需高可用，需要使用 MQTT 客户端 ID 和共享订阅

### 2. 主backend MQTT 依赖

**主backend不再需要MQTT**
- ❌ 检查 `backend/requirements.txt` 已移除 `paho-mqtt`
- ❌ 检查 `backend/main.py` 已移除MQTT相关代码
- ✅ 避免端口冲突
- ✅ 减少backend依赖

### 3. 数据库表一致性

**MQTT服务使用简化的模型定义**
- ✅ 只更新必要的字段 (`last_report_data`, `last_seen`, `is_online` 等)
- ✅ 不创建新表
- ✅ 与后端共享数据库
- ⚠️ 确保数据格式兼容

### 4. 数据格式兼容性

**两种数据格式都受支持**
- ✅ HTTP API 格式：完整、标准化
- ✅ MQTT 简单格式：轻量、易用
- ✅ 自动转换为统一存储格式
- ⚠️ 推荐使用 HTTP API 格式

### 5. 安全考虑

**生产环境建议**
- 🔒 启用 MQTT 认证（用户名/密码）
- 🔒 使用 SSL/TLS 加密（端口 8883）
- 🔒 限制数据库访问权限
- 🔒 定期更新依赖包
- 🔒 监控异常连接和消息

### 6. 监控和告警

**建议监控指标**
- 📊 消息处理成功率
- 📊 MQTT 连接状态
- 📊 数据库连接状态
- 📊 内存和 CPU 使用率
- 📊 重连次数和频率

### 7. 日志管理

**日志文件会持续增长**
- 🔄 使用 logrotate 定期清理
- 🔄 或使用 systemd 的日志大小限制
- 🔄 建议保留最近 7 天日志

```bash
# /etc/logrotate.d/mqtt-service
/var/log/codehubot/mqtt-service*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

## 🔗 相关服务

- **主Backend**: 端口 8000 - HTTP API 服务
- **MQTT Broker**: 端口 1883 (MQTT) / 9001 (WebSocket)
- **MySQL**: 端口 3306 - 数据库服务
- **MQTT Service**: 无端口暴露 - 内部消息处理

## 🔄 升级和维护

### 升级服务

```bash
# Systemd 方式
cd /opt/codehubot/service/mqtt-service
git pull
source /opt/codehubot/venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mqtt-service

# Docker 方式
cd docker
git pull
docker-compose -f docker-compose.with-mqtt.yml build mqtt-service
docker-compose -f docker-compose.with-mqtt.yml up -d mqtt-service
```

### 备份和恢复

**服务本身无状态，只需要备份：**
- `.env` 配置文件
- 数据库（由主backend负责）
- 日志文件（可选）

```bash
# 备份配置
cp .env .env.backup.$(date +%Y%m%d)

# 恢复配置
cp .env.backup.20251219 .env
sudo systemctl restart mqtt-service
```

### 版本回滚

```bash
# Git 回滚
cd /opt/codehubot/service/mqtt-service
git log --oneline -10
git checkout <commit-hash>
sudo systemctl restart mqtt-service

# Docker 回滚
docker-compose -f docker-compose.with-mqtt.yml down
git checkout <commit-hash>
docker-compose -f docker-compose.with-mqtt.yml up -d
```

## 📚 常见问题 FAQ

### Q1: 为什么要分离 MQTT 服务？

A: 主要原因：
1. **性能隔离**：MQTT 消息处理不影响 HTTP API 性能
2. **独立扩展**：可以单独扩展 MQTT 服务
3. **故障隔离**：MQTT 服务崩溃不影响主服务
4. **资源优化**：各服务专注自己的职责

### Q2: MQTT 服务和 HTTP API 哪个更好？

A: 各有优势：
- **MQTT**：实时性好、开销小，适合高频上报
- **HTTP**：简单易用、易调试，适合低频上报
- **建议**：根据设备能力和场景选择

### Q3: 支持 MQTT 5.0 吗？

A: 当前使用 MQTT 3.1.1，因为：
- 兼容性更好
- paho-mqtt 库稳定支持
- 如需升级到 MQTT 5.0，只需修改 `protocol=mqtt.MQTTv5`

### Q4: 如何实现 MQTT 服务高可用？

A: 推荐方案：
1. 使用共享订阅（MQTT 5.0 特性）
2. 部署多个实例，使用不同的客户端 ID
3. 通过 MQTT Broker 集群实现高可用
4. 使用 Kubernetes 部署和自动重启

### Q5: 数据会丢失吗？

A: 正常情况不会：
- QoS=1 保证消息至少送达一次
- 数据库事务保证数据一致性
- 自动重连机制保证服务可用性
- 建议：关键数据使用 QoS=2

### Q6: 如何查看实时消息？

A: 多种方式：
```bash
# 方式1：查看服务日志
sudo journalctl -u mqtt-service -f | grep "📨 收到MQTT消息"

# 方式2：订阅 MQTT 主题
mosquitto_sub -h localhost -t "devices/#" -v

# 方式3：查看数据库更新
watch -n 1 "mysql -u root -p$DB_PASSWORD aiot_admin -e '
SELECT device_id, last_seen, is_online 
FROM device_main 
ORDER BY last_seen DESC LIMIT 5;'"
```

### Q7: 传感器数据如何存储历史记录？

A: 当前版本只存储最新数据，如需历史数据：
1. **时序数据库**：InfluxDB、TimescaleDB（推荐）
2. **独立历史表**：添加 `device_history` 表
3. **前端缓存**：在前端实时缓存数据
4. **日志采集**：通过 Logstash/Fluentd 采集日志

---

**服务正常运行标志：**
```
======================================================================
🚀 启动 AIOT MQTT 独立服务
======================================================================
📊 配置信息:
  - MQTT Broker: localhost:1883
  - 数据库: localhost:3306/aiot_admin
======================================================================
✅ 数据库连接正常
🔌 正在连接到MQTT Broker: localhost:1883
🎉 MQTT连接成功 - Broker: localhost:1883
📡 订阅主题: devices/+/data
📡 订阅主题: devices/+/status
📡 订阅主题: devices/+/heartbeat
🚀 MQTT服务已启动
```

## 💡 最佳实践

### 设备端最佳实践

1. **合理的上报频率**
   ```cpp
   // ❌ 不推荐：过于频繁
   delay(1000); // 1秒一次
   
   // ✅ 推荐：根据数据变化上报
   if (abs(temp - lastTemp) > 0.5) {
       publishData();
   }
   delay(60000); // 最少60秒检查一次
   ```

2. **使用心跳保持连接**
   ```cpp
   // 每30秒发送心跳
   if (millis() - lastHeartbeat > 30000) {
       publishHeartbeat();
       lastHeartbeat = millis();
   }
   ```

3. **批量上报数据**
   ```json
   {
     "sensors": [
       {"sensor_name": "temperature", "value": 25.5},
       {"sensor_name": "humidity", "value": 60},
       {"sensor_name": "pressure", "value": 1013.25}
     ]
   }
   ```

### 服务端最佳实践

1. **监控关键指标**
   - 消息成功率 > 99%
   - MQTT 连接稳定
   - 数据库响应时间 < 100ms

2. **设置合理的资源限制**
   - 内存限制：512M ~ 1G
   - CPU 限制：50% ~ 100%

3. **定期清理日志**
   - 保留最近 7 天
   - 使用 logrotate

4. **备份配置文件**
   - 定期备份 `.env`
   - 版本控制配置变更

---

有问题请查看日志或提交 Issue！

**最后更新：** 2025-12-19

