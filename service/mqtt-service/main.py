"""
AIOT MQTT 独立服务
专门处理设备MQTT消息，不影响主backend性能
"""
import json
import logging
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal, engine
from models import Device, Product, Base
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mqtt_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间（不带时区信息）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


class MQTTService:
    """MQTT服务"""
    
    def __init__(self):
        """初始化MQTT服务"""
        self.broker_host = settings.MQTT_BROKER
        self.broker_port = settings.MQTT_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.reconnect_count = 0
        self.max_reconnect_delay = 300  # 最大重连延迟（秒）
        
        # 统计信息
        self.stats = {
            "total_messages": 0,
            "success_messages": 0,
            "failed_messages": 0,
            "last_message_time": None,
            "start_time": get_beijing_now()
        }
        
        logger.info(f"初始化MQTT服务 - Broker: {self.broker_host}:{self.broker_port}")
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
            self.reconnect_count = 0  # 重置重连计数
            logger.info(f"🎉 MQTT连接成功 - Broker: {self.broker_host}:{self.broker_port}")
            
            # 订阅所有设备的主题
            topics = [
                "devices/+/data",      # 传感器数据
                "devices/+/status",    # 设备状态
                "devices/+/heartbeat", # 心跳数据
            ]
            
            for topic in topics:
                result, mid = client.subscribe(topic, qos=1)
                logger.info(f"📡 订阅主题: {topic}")
        else:
            self.is_connected = False
            error_messages = {
                1: "协议版本不正确",
                2: "客户端ID无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            error_msg = error_messages.get(rc, f"未知错误代码: {rc}")
            logger.error(f"❌ MQTT连接失败: {error_msg}")
    
    def on_disconnect(self, client, userdata, rc, properties=None, reasonCode=None):
        """MQTT断开连接回调"""
        self.is_connected = False
        if rc != 0:
            self.reconnect_count += 1
            # 计算重连延迟（指数退避）
            delay = min(2 ** self.reconnect_count, self.max_reconnect_delay)
            logger.warning(f"⚠️ MQTT意外断开连接，错误代码: {rc}，{delay}秒后尝试重连（第{self.reconnect_count}次）")
            
            # 等待后重连
            time.sleep(delay)
            try:
                logger.info("🔄 尝试重新连接MQTT Broker...")
                client.reconnect()
            except Exception as e:
                logger.error(f"❌ 重连失败: {e}")
        else:
            logger.info("📴 MQTT正常断开连接")
    
    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        self.stats["total_messages"] += 1
        self.stats["last_message_time"] = get_beijing_now()
        
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"📨 收到MQTT消息 - 主题: {topic}")
            
            # 解析主题获取设备ID
            topic_parts = topic.split('/')
            
            if len(topic_parts) >= 3 and topic_parts[0] == 'devices':
                device_uuid = topic_parts[1]
                message_type = topic_parts[2]
                
                # 解析JSON数据
                try:
                    data = json.loads(payload)
                    self.process_device_message(device_uuid, message_type, data)
                    self.stats["success_messages"] += 1
                except json.JSONDecodeError as e:
                    self.stats["failed_messages"] += 1
                    logger.error(f"❌ JSON解析失败: {e}, payload: {payload[:100]}")
                except Exception as e:
                    self.stats["failed_messages"] += 1
                    logger.error(f"❌ 处理消息失败: {e}", exc_info=True)
            else:
                self.stats["failed_messages"] += 1
                logger.warning(f"⚠️ 主题格式不正确: {topic}")
                    
        except Exception as e:
            self.stats["failed_messages"] += 1
            logger.error(f"❌ 处理MQTT消息时出错: {e}", exc_info=True)
    
    def process_device_message(self, device_uuid: str, message_type: str, data: Dict[str, Any]):
        """处理设备消息"""
        db = SessionLocal()
        try:
            # 查找设备
            device = db.query(Device).filter(
                Device.uuid == device_uuid
            ).first()
            
            if not device:
                logger.warning(f"⚠️ 设备不存在: {device_uuid}")
                return
            
            logger.info(f"✅ 找到设备: {device.name} (ID: {device.device_id})")
            
            # 根据消息类型处理
            if message_type == "data":
                # 传感器数据上报
                logger.info(f"📊 处理传感器数据: {data}")
                
                # 兼容两种数据格式：
                # 1. HTTP API 格式: {"sensors": [...], "status": {...}, "location": {...}}
                # 2. MQTT 简单格式: {"temperature": 25.5, "humidity": 60}
                
                if "sensors" in data:
                    # HTTP API 格式 - 转换为标准存储格式
                    self._process_http_format_data(device, data)
                else:
                    # MQTT 简单格式 - 直接存储
                    self._process_mqtt_format_data(device, data)
                
                device.last_seen = get_beijing_now()
                device.is_online = True
                logger.debug(f"传感器数据已更新到设备表")
                
            elif message_type == "status":
                # 设备状态更新
                logger.info(f"📡 处理设备状态: {data}")
                
                # 更新或合并状态数据
                if device.last_report_data:
                    # 合并到现有数据
                    if "status" not in device.last_report_data:
                        device.last_report_data["status"] = {}
                    device.last_report_data["status"].update(data)
                else:
                    # 首次上报
                    device.last_report_data = {"status": data}
                
                device.last_seen = get_beijing_now()
                device.is_online = True
                logger.debug(f"设备状态已更新到设备表")
                
                # 更新设备状态字段
                if "status" in data:
                    device.device_status = data["status"]
                
            elif message_type == "heartbeat":
                # 心跳数据
                logger.debug(f"💓 处理心跳数据")
                
                # 更新设备心跳数据
                device.last_seen = get_beijing_now()
                device.last_heartbeat = get_beijing_now()
                device.is_online = True
                logger.debug(f"设备心跳已更新到设备表")
            
            # 提交数据库更改
            db.commit()
            logger.info(f"✅ 设备数据已更新: {device.name}")
            
        except Exception as e:
            logger.error(f"❌ 处理设备消息失败: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    def _process_http_format_data(self, device: Device, data: Dict[str, Any]):
        """处理 HTTP API 格式的传感器数据"""
        now = get_beijing_now()
        
        # 初始化或获取现有数据
        if not device.last_report_data:
            device.last_report_data = {}
        
        # 确保 sensors 字典存在
        if "sensors" not in device.last_report_data:
            device.last_report_data["sensors"] = {}
        
        # 处理传感器数据列表
        sensors_list = data.get("sensors", [])
        valid_count = 0
        
        for sensor in sensors_list:
            sensor_name = sensor.get("sensor_name")
            sensor_value = sensor.get("value")
            
            # 验证传感器数据
            if not sensor_name or sensor_value is None:
                logger.warning(f"⚠️ 传感器数据不完整，跳过: {sensor}")
                continue
            
            # 验证传感器名称格式
            if not self._validate_sensor_name(sensor_name):
                logger.warning(f"⚠️ 传感器名称格式不正确，跳过: {sensor_name}")
                continue
            
            # 验证传感器值
            if not isinstance(sensor_value, (int, float)):
                logger.warning(f"⚠️ 传感器值必须是数字，跳过: {sensor_name}={sensor_value}")
                continue
            
            device.last_report_data["sensors"][sensor_name] = {
                "value": sensor_value,
                "unit": sensor.get("unit", ""),
                "timestamp": sensor.get("timestamp", now.isoformat())
            }
            valid_count += 1
            logger.debug(f"  - {sensor_name}: {sensor_value} {sensor.get('unit', '')}")
        
        # 更新状态信息
        if "status" in data and isinstance(data["status"], dict):
            device.last_report_data["status"] = data["status"]
        
        # 更新位置信息
        if "location" in data and isinstance(data["location"], dict):
            location = data["location"]
            # 验证经纬度
            if self._validate_location(location):
                device.last_report_data["location"] = location
            else:
                logger.warning(f"⚠️ 位置信息格式不正确: {location}")
        
        # 更新时间戳
        device.last_report_data["upload_timestamp"] = data.get("timestamp", now.isoformat())
        
        logger.info(f"✅ 成功处理 {valid_count} 个传感器数据")
    
    def _process_mqtt_format_data(self, device: Device, data: Dict[str, Any]):
        """处理 MQTT 简单格式的传感器数据"""
        now = get_beijing_now()
        
        # 初始化或获取现有数据
        if not device.last_report_data:
            device.last_report_data = {}
        
        # 确保 sensors 字典存在
        if "sensors" not in device.last_report_data:
            device.last_report_data["sensors"] = {}
        
        # 将简单键值对转换为标准格式
        valid_count = 0
        
        for key, value in data.items():
            # 跳过特殊字段
            if key in ["timestamp", "status", "location"]:
                continue
            
            # 验证传感器名称
            if not self._validate_sensor_name(key):
                logger.warning(f"⚠️ 传感器名称格式不正确，跳过: {key}")
                continue
            
            # 只处理数值类型的传感器数据
            if isinstance(value, (int, float)):
                device.last_report_data["sensors"][key] = {
                    "value": value,
                    "unit": "",
                    "timestamp": now.isoformat()
                }
                valid_count += 1
                logger.debug(f"  - {key}: {value}")
        
        # 更新时间戳
        device.last_report_data["upload_timestamp"] = data.get("timestamp", now.isoformat())
        
        logger.info(f"✅ 成功处理 {valid_count} 个传感器数据")
    
    def _validate_sensor_name(self, name: str) -> bool:
        """验证传感器名称格式
        
        规则：
        - 只能包含小写字母、数字、下划线
        - 长度在 1-50 之间
        - 不能以数字开头
        """
        import re
        if not name or len(name) > 50:
            return False
        return bool(re.match(r'^[a-z_][a-z0-9_]*$', name))
    
    def _validate_location(self, location: Dict[str, Any]) -> bool:
        """验证位置信息格式
        
        规则：
        - 必须包含 latitude 和 longitude
        - latitude: -90 到 90
        - longitude: -180 到 180
        """
        try:
            lat = location.get("latitude")
            lon = location.get("longitude")
            
            if lat is None or lon is None:
                return False
            
            lat = float(lat)
            lon = float(lon)
            
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, TypeError):
            return False
    
    def start(self):
        """启动MQTT服务"""
        try:
            # 创建MQTT客户端
            self.client = mqtt.Client(
                client_id=f"mqtt_service_{int(time.time())}",
                protocol=mqtt.MQTTv311,
                clean_session=True
            )
            
            # 设置回调
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # 设置认证（如果需要）
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                logger.info("🔑 已设置MQTT认证")
            
            # 启用自动重连
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            
            # 连接到MQTT Broker
            logger.info(f"🔌 正在连接到MQTT Broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # 启动统计定时器
            self._start_stats_timer()
            
            # 启动循环
            logger.info("🚀 MQTT服务已启动")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("⚠️ 收到中断信号，正在关闭MQTT服务...")
            self.stop()
        except Exception as e:
            logger.error(f"❌ MQTT服务启动失败: {e}", exc_info=True)
            sys.exit(1)
    
    def _start_stats_timer(self):
        """启动统计定时器（每5分钟打印一次统计信息）"""
        import threading
        
        def print_stats():
            while self.client and self.is_connected:
                time.sleep(300)  # 5分钟
                self._print_stats()
        
        stats_thread = threading.Thread(target=print_stats, daemon=True)
        stats_thread.start()
    
    def _print_stats(self):
        """打印统计信息"""
        uptime = get_beijing_now() - self.stats["start_time"]
        success_rate = 0
        if self.stats["total_messages"] > 0:
            success_rate = (self.stats["success_messages"] / self.stats["total_messages"]) * 100
        
        logger.info("=" * 70)
        logger.info("📊 MQTT服务统计信息")
        logger.info("=" * 70)
        logger.info(f"  运行时间: {uptime}")
        logger.info(f"  连接状态: {'✅ 已连接' if self.is_connected else '❌ 未连接'}")
        logger.info(f"  总消息数: {self.stats['total_messages']}")
        logger.info(f"  成功处理: {self.stats['success_messages']}")
        logger.info(f"  处理失败: {self.stats['failed_messages']}")
        logger.info(f"  成功率: {success_rate:.2f}%")
        if self.stats["last_message_time"]:
            logger.info(f"  最后消息: {self.stats['last_message_time']}")
        logger.info("=" * 70)
    
    def stop(self):
        """停止MQTT服务"""
        if self.client:
            logger.info("🛑 正在断开MQTT连接...")
            self.client.disconnect()
            self.client.loop_stop()
            logger.info("✅ MQTT服务已停止")


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("🚀 启动 AIOT MQTT 独立服务")
    logger.info("=" * 70)
    logger.info(f"📊 配置信息:")
    logger.info(f"  - MQTT Broker: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    logger.info(f"  - 数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info("=" * 70)
    
    # 创建数据库表（已禁用，直接在数据库中初始化）
    # try:
    #     Base.metadata.create_all(bind=engine)
    #     logger.info("✅ 数据库表检查完成")
    # except Exception as e:
    #     logger.error(f"❌ 数据库连接失败: {e}")
    #     sys.exit(1)
    
    # 简单测试数据库连接
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 启动MQTT服务
    service = MQTTService()
    service.start()


if __name__ == "__main__":
    main()

