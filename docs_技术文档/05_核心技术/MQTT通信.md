# MQTT 通信

## 概述

MQTT (Message Queuing Telemetry Transport) 是一种轻量级的发布/订阅模式的消息传输协议，专为物联网设备设计。CodeHubot 平台使用 MQTT 实现设备与服务器之间的双向实时通信。

## 为什么选择 MQTT？

### 优势

| 特性 | MQTT | HTTP/REST |
|------|------|-----------|
| **协议开销** | 极小（2字节） | 较大（几百字节） |
| **连接方式** | 长连接 | 短连接 |
| **实时性** | 推送，毫秒级 | 轮询，秒级 |
| **带宽消耗** | 很低 | 较高 |
| **电池续航** | 友好 | 不友好 |
| **海量连接** | 支持 | 受限 |
| **双向通信** | 原生支持 | 需WebSocket |

### 适用场景

- ✅ 物联网设备控制
- ✅ 实时数据上报
- ✅ 设备状态监控
- ✅ 固件 OTA 升级
- ✅ 消息推送

## MQTT 基础概念

### 1. 发布/订阅模式

```
发布者 (Publisher)
    ↓ 发布消息到主题
MQTT Broker (Mosquitto)
    ↓ 转发消息
订阅者 (Subscriber)
```

**特点**：
- 发布者和订阅者解耦
- 支持一对多通信
- 异步消息传递

### 2. 主题 (Topic)

MQTT 使用分层主题结构，类似文件路径：

```
device/12345/status          # 设备状态
device/12345/command         # 设备命令
device/12345/data/temperature # 温度数据
device/12345/data/humidity    # 湿度数据
```

**通配符**：
- `+`: 单层通配符 (例: `device/+/status` 匹配所有设备的状态)
- `#`: 多层通配符 (例: `device/12345/#` 匹配该设备的所有主题)

### 3. QoS (服务质量等级)

| QoS | 名称 | 描述 | 使用场景 |
|-----|------|------|---------|
| **0** | 至多一次 | 消息可能丢失，不重传 | 传感器数据（容忍丢失） |
| **1** | 至少一次 | 保证送达，可能重复 | 设备状态（重要但可容忍重复） |
| **2** | 恰好一次 | 保证送达且不重复 | 支付指令（严格要求） |

### 4. 保留消息 (Retained Message)

```python
# 发布保留消息
client.publish("device/12345/status", "online", retain=True)

# 新订阅者会立即收到最后的保留消息
```

**用途**：
- 设备在线状态
- 设备配置信息
- 最新传感器数据

## 系统架构

### MQTT 通信架构

```
┌─────────────────────────────────────────────────────────────┐
│                         ESP32 设备                           │
├─────────────────────────────────────────────────────────────┤
│  WiFi连接 → MQTT客户端 → 订阅/发布消息                       │
└────────────────────────┬────────────────────────────────────┘
                         │ MQTT (1883)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Mosquitto Broker                           │
├─────────────────────────────────────────────────────────────┤
│  - 消息路由                                                  │
│  - 客户端认证                                                │
│  - 主题订阅管理                                              │
└────────────────────────┬────────────────────────────────────┘
                         │ MQTT (1883)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend MQTT Service                      │
├─────────────────────────────────────────────────────────────┤
│  - 订阅设备主题                                              │
│  - 处理设备消息                                              │
│  - 发送控制命令                                              │
│  - 更新数据库                                                │
└─────────────────────────────────────────────────────────────┘
```

## Mosquitto 配置

### Docker 部署

**文件位置**: `docker/docker-compose.yml`

```yaml
mqtt:
  image: eclipse-mosquitto:2.0
  container_name: codehubot-mqtt
  ports:
    - "1883:1883"  # MQTT 端口
    - "9001:9001"  # WebSocket 端口
  volumes:
    - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
    - mqtt_data:/mosquitto/data
    - mqtt_logs:/mosquitto/log
  networks:
    - aiot-network
  restart: unless-stopped
```

### Mosquitto 配置文件

**文件位置**: `docker/mosquitto.conf`

```conf
# 基础配置
listener 1883
protocol mqtt

# WebSocket 支持
listener 9001
protocol websockets

# 认证配置
allow_anonymous false
password_file /mosquitto/config/pwfile

# 持久化配置
persistence true
persistence_location /mosquitto/data/

# 日志配置
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all

# ACL 访问控制（可选）
# acl_file /mosquitto/config/aclfile
```

### 创建用户认证

```bash
# 进入 Mosquitto 容器
docker exec -it codehubot-mqtt sh

# 创建密码文件
mosquitto_passwd -c /mosquitto/config/pwfile mqtt_user

# 添加更多用户
mosquitto_passwd -b /mosquitto/config/pwfile device_user device_password

# 重启 Mosquitto
docker restart codehubot-mqtt
```

## 主题设计

### 主题命名规范

```
{domain}/{device_id}/{message_type}[/{sub_type}]
```

**示例**：

```
device/ESP32_001/status              # 设备状态
device/ESP32_001/command             # 设备命令
device/ESP32_001/data/temperature    # 温度数据
device/ESP32_001/data/humidity       # 湿度数据
device/ESP32_001/ota/request         # OTA请求
device/ESP32_001/ota/progress        # OTA进度
```

### 系统主题

```
system/broadcast                     # 系统广播
system/devices/online                # 设备上线通知
system/devices/offline               # 设备下线通知
system/alerts                        # 系统告警
```

### 用户主题

```
user/{user_id}/notifications         # 用户通知
user/{user_id}/devices               # 用户设备列表
```

## 后端集成

### MQTT 服务实现

**文件位置**: `backend/app/services/mqtt_service.py`

```python
import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class MQTTService:
    """MQTT 服务"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="codehubot-backend")
        self.client.username_pw_set(
            settings.mqtt_username,
            settings.mqtt_password
        )
        
        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # 消息处理器
        self.handlers: Dict[str, Callable] = {}
    
    def connect(self):
        """连接到 MQTT Broker"""
        try:
            self.client.connect(
                settings.mqtt_broker_host,
                settings.mqtt_broker_port,
                60  # keepalive
            )
            self.client.loop_start()
            logger.info("✅ MQTT 已连接")
        except Exception as e:
            logger.error(f"❌ MQTT 连接失败: {e}")
    
    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("🛑 MQTT 已断开")
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            logger.info("✅ MQTT Broker 连接成功")
            # 订阅所有设备主题
            self.subscribe("device/+/status")
            self.subscribe("device/+/data/#")
        else:
            logger.error(f"❌ MQTT 连接失败，错误码: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0:
            logger.warning(f"⚠️ MQTT 意外断开: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"📨 收到消息: {topic} -> {payload}")
            
            # 查找并执行处理器
            for pattern, handler in self.handlers.items():
                if self._match_topic(pattern, topic):
                    handler(topic, payload)
        
        except Exception as e:
            logger.error(f"❌ 消息处理失败: {e}")
    
    def subscribe(self, topic: str, qos: int = 1):
        """订阅主题"""
        self.client.subscribe(topic, qos)
        logger.info(f"📬 订阅主题: {topic}")
    
    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False):
        """发布消息"""
        result = self.client.publish(topic, payload, qos, retain)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📤 发布消息: {topic} -> {payload}")
        else:
            logger.error(f"❌ 发布失败: {result.rc}")
        return result
    
    def register_handler(self, topic_pattern: str, handler: Callable):
        """注册消息处理器"""
        self.handlers[topic_pattern] = handler
        logger.info(f"📝 注册处理器: {topic_pattern}")
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """匹配主题模式"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) != len(topic_parts):
            if '#' not in pattern:
                return False
        
        for p, t in zip(pattern_parts, topic_parts):
            if p == '#':
                return True
            if p != '+' and p != t:
                return False
        
        return True

# 全局实例
mqtt_service = MQTTService()
```

### 注册消息处理器

```python
from app.services.mqtt_service import mqtt_service
from app.core.database import get_db
from app.models.device import Device

def handle_device_status(topic: str, payload: str):
    """处理设备状态消息"""
    # 解析 topic: device/{device_id}/status
    parts = topic.split('/')
    device_id = parts[1]
    
    # 解析 payload
    data = json.loads(payload)
    status = data.get('status')
    
    # 更新数据库
    db = next(get_db())
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        device.status = status
        device.last_seen = datetime.utcnow()
        db.commit()
        logger.info(f"✅ 设备状态已更新: {device_id} -> {status}")

def handle_device_data(topic: str, payload: str):
    """处理设备数据消息"""
    # 解析 topic: device/{device_id}/data/{data_type}
    parts = topic.split('/')
    device_id = parts[1]
    data_type = parts[3]
    
    # 解析数据
    data = json.loads(payload)
    value = data.get('value')
    timestamp = data.get('timestamp')
    
    # 存储到数据库或时序数据库
    logger.info(f"📊 设备数据: {device_id} - {data_type}: {value}")

# 注册处理器
mqtt_service.register_handler("device/+/status", handle_device_status)
mqtt_service.register_handler("device/+/data/#", handle_device_data)
```

### 在 FastAPI 启动时连接

```python
from fastapi import FastAPI
from app.services.mqtt_service import mqtt_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时连接 MQTT
    mqtt_service.connect()
    yield
    # 关闭时断开 MQTT
    mqtt_service.disconnect()

app = FastAPI(lifespan=lifespan)
```

## ESP32 设备端

### Arduino/ESP-IDF 代码

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

// WiFi 配置
const char* ssid = "your-wifi-ssid";
const char* password = "your-wifi-password";

// MQTT 配置
const char* mqtt_server = "your-server-ip";
const int mqtt_port = 1883;
const char* mqtt_user = "device_user";
const char* mqtt_password = "device_password";

// 设备 ID
String device_id = "ESP32_001";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // 连接 WiFi
  setup_wifi();
  
  // 配置 MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  Serial.println("连接 WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi 已连接");
  Serial.print("IP 地址: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("连接 MQTT Broker...");
    
    if (client.connect(device_id.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("✅ MQTT 已连接");
      
      // 订阅命令主题
      String command_topic = "device/" + device_id + "/command";
      client.subscribe(command_topic.c_str());
      
      // 发布上线状态
      String status_topic = "device/" + device_id + "/status";
      client.publish(status_topic.c_str(), "{\"status\":\"online\"}", true);
      
    } else {
      Serial.print("❌ 连接失败，错误码: ");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("📨 收到消息: ");
  Serial.println(topic);
  
  // 解析消息
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // 处理命令
  // TODO: 解析 JSON 并执行命令
}

void publish_sensor_data() {
  // 读取传感器
  float temperature = readTemperature();
  
  // 构造 JSON
  String payload = "{\"value\":" + String(temperature) + ",\"timestamp\":" + String(millis()) + "}";
  
  // 发布数据
  String topic = "device/" + device_id + "/data/temperature";
  client.publish(topic.c_str(), payload.c_str());
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // 每10秒上报一次数据
  static unsigned long last_publish = 0;
  if (millis() - last_publish > 10000) {
    publish_sensor_data();
    last_publish = millis();
  }
}
```

## 设备控制 API

### 发送命令到设备

```python
from fastapi import APIRouter, Depends
from app.services.mqtt_service import mqtt_service
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/devices/{device_id}/control")
async def control_device(
    device_id: str,
    command: dict,
    current_user = Depends(get_current_user)
):
    """控制设备"""
    
    # 构造 MQTT 主题
    topic = f"device/{device_id}/command"
    
    # 构造消息
    payload = json.dumps(command)
    
    # 发布命令
    result = mqtt_service.publish(topic, payload)
    
    if result.rc == 0:
        return {"success": True, "message": "命令已发送"}
    else:
        return {"success": False, "message": "命令发送失败"}
```

### 前端调用

```javascript
// 控制设备
async function controlDevice(deviceId, command) {
  const response = await post(`/devices/${deviceId}/control`, {
    action: command.action,
    params: command.params
  })
  
  if (response.success) {
    ElMessage.success('命令已发送')
  }
}

// 示例：打开设备
controlDevice('ESP32_001', {
  action: 'turn_on',
  params: { pin: 2 }
})
```

## 消息格式规范

### 设备状态消息

```json
{
  "status": "online",
  "timestamp": 1735401600,
  "ip": "192.168.1.100",
  "rssi": -45
}
```

### 传感器数据消息

```json
{
  "type": "temperature",
  "value": 25.6,
  "unit": "°C",
  "timestamp": 1735401600
}
```

### 设备命令消息

```json
{
  "action": "set_led",
  "params": {
    "pin": 2,
    "state": 1
  },
  "request_id": "req_123456"
}
```

### 命令响应消息

```json
{
  "request_id": "req_123456",
  "success": true,
  "result": {
    "pin": 2,
    "state": 1
  }
}
```

## 安全措施

### 1. 认证

```python
# 使用用户名/密码认证
client.username_pw_set("device_user", "secure_password")
```

### 2. TLS/SSL 加密

```python
# 配置 SSL/TLS
client.tls_set(
    ca_certs="/path/to/ca.crt",
    certfile="/path/to/client.crt",
    keyfile="/path/to/client.key"
)
client.connect("mqtt.example.com", 8883)
```

### 3. ACL 访问控制

```conf
# mosquitto ACL 文件
user device_user
topic read device/ESP32_001/#
topic write device/ESP32_001/status
topic write device/ESP32_001/data/#

user backend
topic read device/#
topic write device/+/command
```

## 性能优化

### 1. 连接池

```python
# 使用连接池管理多个 MQTT 客户端
class MQTTPool:
    def __init__(self, size=10):
        self.pool = [MQTTClient() for _ in range(size)]
    
    def get_client(self):
        return self.pool.pop()
    
    def return_client(self, client):
        self.pool.append(client)
```

### 2. 批量发布

```python
# 批量发布消息
def publish_batch(messages):
    for topic, payload in messages:
        mqtt_service.publish(topic, payload, qos=0)  # QoS 0 更快
```

### 3. 消息压缩

```python
import gzip

# 压缩大消息
payload = gzip.compress(json.dumps(data).encode())
mqtt_service.publish(topic, payload)
```

## 监控和调试

### MQTT 客户端工具

- **MQTT.fx**: 图形化客户端
- **mosquitto_pub/sub**: 命令行工具
- **MQTT Explorer**: 可视化主题浏览

### 命令行订阅

```bash
# 订阅所有设备状态
mosquitto_sub -h localhost -t "device/+/status" -u mqtt_user -P password

# 订阅所有消息
mosquitto_sub -h localhost -t "#" -u mqtt_user -P password -v
```

### 命令行发布

```bash
# 发布测试消息
mosquitto_pub -h localhost -t "device/ESP32_001/command" -m '{"action":"test"}' -u mqtt_user -P password
```

## 相关文档

- [整体架构设计](../02_系统架构/整体架构设计.md) - 系统架构概览
- [Docker容器化部署](../03_部署运维/Docker容器化部署.md) - MQTT 容器部署
- [设备管理API](../../backend/README.md) - 设备管理接口文档
