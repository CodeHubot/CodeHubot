"""
MQTT客户端服务
用于接收设备上报的数据
"""
import json
import logging
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.product import Product
# from app.models.interaction_log import InteractionLog  # 已删除，改为更新设备表
from app.core.config import settings
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间（不带时区信息，用于存储到数据库）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)

class MQTTService:
    def __init__(self):
        """从配置文件读取MQTT连接信息"""
        self.broker_host = settings.mqtt_broker_host
        self.broker_port = settings.mqtt_broker_port
        self.username = settings.mqtt_username
        self.password = settings.mqtt_password
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        
        logger.info(f"初始化MQTT服务 - Broker: {self.broker_host}:{self.broker_port}")
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"🎉 MQTT客户端连接成功 - Broker: {self.broker_host}:{self.broker_port}")
            
            # 订阅所有设备的主题
            topics = [
                "devices/+/data",      # 传感器数据
                "devices/+/status",    # 设备状态
                "devices/+/heartbeat", # 心跳数据
            ]
            
            for topic in topics:
                result, mid = client.subscribe(topic, qos=1)
                logger.info(f"📡 订阅主题: {topic}, result={result}, mid={mid}")
                
        else:
            self.is_connected = False
            logger.error(f"❌ MQTT连接失败，错误代码: {rc}")
    
    def on_disconnect(self, client, userdata, rc, properties=None, reasonCode=None):
        """MQTT断开连接回调 - 兼容paho-mqtt 1.x和2.x版本"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"⚠️ MQTT意外断开连接，错误代码: {rc}")
        else:
            logger.info("📴 MQTT客户端正常断开连接")
    
    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"📨 收到MQTT消息 - 主题: {topic}")
            logger.debug(f"📨 消息内容: {payload}")
            
            # 解析主题获取设备ID
            topic_parts = topic.split('/')
            logger.info(f"🔍 解析主题: parts={topic_parts}")
            
            if len(topic_parts) >= 3 and topic_parts[0] == 'devices':
                device_uuid = topic_parts[1]
                message_type = topic_parts[2]
                
                logger.info(f"🔍 提取信息: device_uuid={device_uuid}, message_type={message_type}")
                
                # 解析JSON数据
                try:
                    data = json.loads(payload)
                    logger.info(f"🔍 JSON解析成功，调用process_device_message...")
                    self.process_device_message(device_uuid, message_type, data)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON解析失败: {e}")
            else:
                logger.warning(f"⚠️ 主题格式不正确: {topic}")
                    
        except Exception as e:
            logger.error(f"❌ 处理MQTT消息时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _parse_sensor_data(self, device: Device, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据产品配置解析传感器数据
        
        固件发送格式：
        {"device_id":"xxx","sensor":"DHT11","temperature":24.4,"humidity":39.0,"timestamp":12345}
        
        转换为产品配置的key格式：
        {"DHT11_temperature": 24.4, "DHT11_humidity": 39.0}
        """
        if not device.product:
            logger.warning(f"设备 {device.device_id} 没有关联产品，无法解析传感器数据")
            return {}
        
        sensor_type = data.get("sensor")
        if not sensor_type:
            logger.warning(f"传感器数据缺少 'sensor' 字段")
            return {}
        
        # 获取产品的传感器配置
        sensor_types = device.product.sensor_types
        
        logger.info(f"🔍 原始产品配置类型: {type(sensor_types)}")
        logger.info(f"🔍 原始产品配置内容（前500字符）: {str(sensor_types)[:500]}")
        
        if not sensor_types:
            logger.warning(f"产品 {device.product.name} 没有配置传感器类型")
            return {}
        
        # sensor_types可能是字典或字符串，需要处理
        if isinstance(sensor_types, str):
            try:
                sensor_types = json.loads(sensor_types)
            except json.JSONDecodeError as e:
                logger.error(f"解析产品sensor_types失败: {e}")
                return {}
        
        if not isinstance(sensor_types, dict):
            logger.error(f"sensor_types格式不正确，应该是字典类型，实际是: {type(sensor_types)}")
            return {}
        
        logger.debug(f"产品 {device.product.name} 的传感器配置: {sensor_types}")
        
        parsed_data = {}
        
        # 遍历产品配置的传感器类型，找到匹配的并提取数据
        for key, config in sensor_types.items():
            if not isinstance(config, dict):
                logger.warning(f"传感器配置 {key} 格式不正确: {config}")
                continue
                
            config_type = config.get("type")
            logger.debug(f"检查传感器配置: key={key}, config_type={config_type}, sensor_type={sensor_type}")
            logger.debug(f"完整配置: {config}")
            
            if config_type == sensor_type:
                data_field = config.get("data_field")
                logger.info(f"🔍 找到匹配配置: {key}, data_field={data_field}, 传感器数据字段={list(data.keys())}")
                
                if data_field and data_field in data:
                    # 使用配置的key作为数据键
                    value = data[data_field]
                    parsed_data[key] = value
                    logger.info(f"✓ 映射成功: {sensor_type}.{data_field} -> {key} = {value}")
                    
                    # 对于雨水传感器，同时保存level字段（如果存在）
                    if sensor_type == "RAIN_SENSOR" and "level" in data:
                        level_field = config.get("level_field", "level")
                        parsed_data[f"{key}_level"] = data["level"]
                        logger.info(f"✓ 雨水传感器level字段: {key}_level = {data['level']}")
                else:
                    logger.warning(f"数据字段 {data_field} 不存在于传感器数据中，可用字段: {list(data.keys())}")
        
        if not parsed_data:
            logger.warning(f"未找到匹配的传感器配置。传感器类型: {sensor_type}, 产品配置: {list(sensor_types.keys())}")
        
        return parsed_data
    
    def process_device_message(self, device_uuid: str, message_type: str, data: Dict[str, Any]):
        """处理设备消息"""
        logger.info(f"🔧 process_device_message: device_uuid={device_uuid}, message_type={message_type}, data_keys={list(data.keys())}")
        try:
            db = SessionLocal()
            
            # 查找设备 - 使用uuid字段，并预加载产品信息
            from sqlalchemy.orm import joinedload
            device = db.query(Device).options(joinedload(Device.product)).filter(Device.uuid == device_uuid).first()
            if not device:
                logger.warning(f"⚠️ 未找到设备: {device_uuid}")
                return
            
            logger.info(f"🔧 找到设备: {device.device_id}, 准备处理消息类型: {message_type}")
            
            # 更新设备最后在线时间和在线状态（北京时间）
            device.last_seen = get_beijing_now()
            device.is_online = True  # 收到任何消息都表示设备在线
            
            if message_type == "data":
                # 处理传感器数据
                logger.info(f"🌡️ 设备 {device_uuid} 传感器数据: {data}")
                
                # 解析传感器数据并根据产品配置映射（用于日志输出）
                try:
                    parsed_data = self._parse_sensor_data(device, data)
                    if parsed_data:
                        logger.info(f"📊 解析后的传感器数据: {parsed_data}")
                except Exception as parse_error:
                    logger.error(f"解析传感器数据失败: {parse_error}")
                
                # 更新设备最后上报数据（已优化：改为直接更新设备表）
                try:
                    device.last_report_data = data
                    device.last_seen = get_beijing_now()
                    device.is_online = True
                    logger.debug(f"传感器数据已更新到设备表")
                except Exception as log_error:
                    logger.error(f"更新传感器数据失败: {log_error}")
                
            elif message_type == "status":
                # 处理设备状态
                logger.info(f"📊 设备 {device_uuid} 状态更新: {data}")
                
                # 更新设备状态数据（已优化：改为直接更新设备表）
                try:
                    device.last_report_data = data
                    device.last_seen = get_beijing_now()
                    device.is_online = True
                    logger.debug(f"设备状态已更新到设备表")
                except Exception as log_error:
                    logger.error(f"更新设备状态失败: {log_error}")
                
                # 更新设备状态信息
                if 'wifi_status' in data:
                    device.is_online = data['wifi_status'] == 'Connected'
                elif 'mqtt_connected' in data:
                    device.is_online = data.get('mqtt_connected', False)
                
            elif message_type == "heartbeat":
                # 处理心跳数据
                logger.info(f"💓 设备 {device_uuid} 心跳: {data}")
                
                # 更新设备心跳数据（已优化：改为直接更新设备表）
                try:
                    # 心跳不需要保存完整数据，只更新时间和在线状态
                    device.last_seen = get_beijing_now()
                    device.is_online = True
                    logger.debug(f"设备心跳已更新到设备表")
                except Exception as log_error:
                    logger.error(f"更新设备心跳失败: {log_error}")
                
                device.is_online = True
                # 更新最后心跳时间（北京时间）
                device.last_heartbeat = get_beijing_now()
                
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ 处理设备消息时出错: {e}")
            db.rollback()
        finally:
            db.close()
    
    def start(self):
        """启动MQTT客户端"""
        try:
            # 兼容 paho-mqtt 1.x 和 2.x 版本
            try:
                # paho-mqtt 2.0+ 使用 CallbackAPIVersion
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError:
                # paho-mqtt 1.x 使用旧的 API
                self.client = mqtt.Client()
            
            self.client.username_pw_set(self.username, self.password)
            
            # 设置回调函数
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # 连接到MQTT broker
            logger.info(f"🔄 正在连接MQTT Broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # 启动循环
            self.client.loop_start()
            logger.info("🚀 MQTT客户端服务已启动")
            
        except Exception as e:
            logger.error(f"❌ 启动MQTT客户端失败: {e}")
    
    def stop(self):
        """停止MQTT客户端"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🛑 MQTT客户端服务已停止")

# 全局MQTT服务实例
mqtt_service = MQTTService()