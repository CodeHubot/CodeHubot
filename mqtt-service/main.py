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
        
        logger.info(f"初始化MQTT服务 - Broker: {self.broker_host}:{self.broker_port}")
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
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
            logger.error(f"❌ MQTT连接失败，错误代码: {rc}")
    
    def on_disconnect(self, client, userdata, rc, properties=None, reasonCode=None):
        """MQTT断开连接回调"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"⚠️ MQTT意外断开连接，错误代码: {rc}")
        else:
            logger.info("📴 MQTT正常断开连接")
    
    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
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
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON解析失败: {e}")
            else:
                logger.warning(f"⚠️ 主题格式不正确: {topic}")
                    
        except Exception as e:
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
                
                # 更新设备最后上报数据
                device.last_report_data = data
                device.last_seen = get_beijing_now()
                device.is_online = True
                logger.debug(f"传感器数据已更新到设备表")
                
            elif message_type == "status":
                # 设备状态更新
                logger.info(f"📡 处理设备状态: {data}")
                
                # 更新设备状态数据
                device.last_report_data = data
                device.last_seen = get_beijing_now()
                device.is_online = True
                logger.debug(f"设备状态已更新到设备表")
                
                # 更新设备状态信息
                if "status" in data:
                    device.device_status = data["status"]
                
            elif message_type == "heartbeat":
                # 心跳数据
                logger.debug(f"💓 处理心跳数据")
                
                # 更新设备心跳数据
                device.last_seen = get_beijing_now()
                device.is_online = True
                logger.debug(f"设备心跳已更新到设备表")
                
                device.is_online = True
                device.last_heartbeat = get_beijing_now()
            
            # 提交数据库更改
            db.commit()
            logger.info(f"✅ 设备数据已更新: {device.name}")
            
        except Exception as e:
            logger.error(f"❌ 处理设备消息失败: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    def start(self):
        """启动MQTT服务"""
        try:
            # 创建MQTT客户端
            self.client = mqtt.Client(
                client_id=f"mqtt_service_{int(time.time())}",
                protocol=mqtt.MQTTv311
            )
            
            # 设置回调
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # 设置认证（如果需要）
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                logger.info("🔑 已设置MQTT认证")
            
            # 连接到MQTT Broker
            logger.info(f"🔌 正在连接到MQTT Broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # 启动循环
            logger.info("🚀 MQTT服务已启动")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("⚠️ 收到中断信号，正在关闭MQTT服务...")
            self.stop()
        except Exception as e:
            logger.error(f"❌ MQTT服务启动失败: {e}", exc_info=True)
            sys.exit(1)
    
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

