#!/usr/bin/env python3
"""
MQTT 消息发布测试脚本
用于测试 MQTT 服务的消息处理功能
"""
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime


# MQTT 配置
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = ""  # 如果有认证，填写用户名
MQTT_PASSWORD = ""  # 如果有认证，填写密码

# 测试设备 UUID（请替换为实际的设备 UUID）
TEST_DEVICE_UUID = "your-device-uuid-here"


def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print(f"✅ 成功连接到 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ 连接失败，错误代码: {rc}")


def on_publish(client, userdata, mid):
    """发布回调"""
    print(f"✅ 消息已发布 (mid: {mid})")


def publish_http_format_data(client):
    """发布 HTTP API 格式的传感器数据"""
    print("\n" + "="*70)
    print("📤 发布 HTTP API 格式数据")
    print("="*70)
    
    # 模拟传感器数据
    temperature = round(random.uniform(20.0, 30.0), 2)
    humidity = round(random.uniform(40.0, 80.0), 2)
    light = random.randint(500, 1000)
    
    data = {
        "sensors": [
            {
                "sensor_name": "temperature",
                "value": temperature,
                "unit": "°C",
                "timestamp": datetime.now().isoformat()
            },
            {
                "sensor_name": "humidity",
                "value": humidity,
                "unit": "%",
                "timestamp": datetime.now().isoformat()
            },
            {
                "sensor_name": "light",
                "value": light,
                "unit": "lux",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "status": {
            "ip_address": "192.168.1.100",
            "rssi": random.randint(-80, -30),
            "battery": random.randint(80, 100)
        },
        "location": {
            "latitude": 39.9042,
            "longitude": 116.4074
        },
        "timestamp": datetime.now().isoformat()
    }
    
    topic = f"devices/{TEST_DEVICE_UUID}/data"
    message = json.dumps(data, ensure_ascii=False)
    
    print(f"主题: {topic}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    result = client.publish(topic, message, qos=1)
    result.wait_for_publish()
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ HTTP 格式数据发布成功")
    else:
        print(f"❌ 发布失败，错误: {result.rc}")


def publish_mqtt_simple_format_data(client):
    """发布 MQTT 简单格式的传感器数据"""
    print("\n" + "="*70)
    print("📤 发布 MQTT 简单格式数据")
    print("="*70)
    
    # 简单格式：直接键值对
    data = {
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(40.0, 80.0), 2),
        "light": random.randint(500, 1000),
        "pressure": round(random.uniform(990.0, 1020.0), 2)
    }
    
    topic = f"devices/{TEST_DEVICE_UUID}/data"
    message = json.dumps(data)
    
    print(f"主题: {topic}")
    print(f"数据: {json.dumps(data, indent=2)}")
    
    result = client.publish(topic, message, qos=1)
    result.wait_for_publish()
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ MQTT 简单格式数据发布成功")
    else:
        print(f"❌ 发布失败，错误: {result.rc}")


def publish_status(client):
    """发布设备状态"""
    print("\n" + "="*70)
    print("📤 发布设备状态")
    print("="*70)
    
    data = {
        "status": random.choice(["online", "working", "idle"]),
        "battery": random.randint(80, 100),
        "signal": random.choice(["excellent", "good", "fair"]),
        "temperature": round(random.uniform(35.0, 45.0), 2)
    }
    
    topic = f"devices/{TEST_DEVICE_UUID}/status"
    message = json.dumps(data)
    
    print(f"主题: {topic}")
    print(f"数据: {json.dumps(data, indent=2)}")
    
    result = client.publish(topic, message, qos=1)
    result.wait_for_publish()
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ 状态发布成功")
    else:
        print(f"❌ 发布失败，错误: {result.rc}")


def publish_heartbeat(client):
    """发布心跳"""
    print("\n" + "="*70)
    print("💓 发布心跳")
    print("="*70)
    
    data = {
        "timestamp": datetime.now().isoformat()
    }
    
    topic = f"devices/{TEST_DEVICE_UUID}/heartbeat"
    message = json.dumps(data)
    
    print(f"主题: {topic}")
    print(f"数据: {json.dumps(data, indent=2)}")
    
    result = client.publish(topic, message, qos=1)
    result.wait_for_publish()
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ 心跳发布成功")
    else:
        print(f"❌ 发布失败，错误: {result.rc}")


def test_invalid_data(client):
    """测试无效数据（用于验证数据验证功能）"""
    print("\n" + "="*70)
    print("🧪 测试无效数据（验证数据验证功能）")
    print("="*70)
    
    # 测试1：无效的 JSON
    print("\n测试1: 无效的 JSON 格式")
    topic = f"devices/{TEST_DEVICE_UUID}/data"
    invalid_message = "this is not json"
    client.publish(topic, invalid_message, qos=1)
    print("✅ 已发送无效 JSON（应该被拒绝）")
    
    time.sleep(1)
    
    # 测试2：无效的传感器名称（以数字开头）
    print("\n测试2: 无效的传感器名称")
    data = {
        "123invalid": 25.5,  # 以数字开头
        "UPPERCASE": 60,     # 大写字母
        "valid_sensor": 100  # 有效的
    }
    message = json.dumps(data)
    client.publish(topic, message, qos=1)
    print("✅ 已发送无效传感器名称（应该被过滤）")
    
    time.sleep(1)
    
    # 测试3：无效的传感器值（字符串）
    print("\n测试3: 无效的传感器值")
    data = {
        "temperature": "not a number",  # 字符串
        "humidity": 60                   # 有效的
    }
    message = json.dumps(data)
    client.publish(topic, message, qos=1)
    print("✅ 已发送无效传感器值（应该被过滤）")


def main():
    """主函数"""
    print("="*70)
    print("🚀 MQTT 消息发布测试脚本")
    print("="*70)
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"设备 UUID: {TEST_DEVICE_UUID}")
    print("="*70)
    
    if TEST_DEVICE_UUID == "your-device-uuid-here":
        print("\n❌ 错误：请先修改 TEST_DEVICE_UUID 为实际的设备 UUID")
        print("   可以从数据库查询: SELECT uuid FROM device_main LIMIT 1;")
        return
    
    # 创建 MQTT 客户端
    client = mqtt.Client(
        client_id=f"test_publisher_{int(time.time())}",
        protocol=mqtt.MQTTv311
    )
    
    # 设置回调
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    # 设置认证（如果需要）
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        print("🔑 已设置 MQTT 认证")
    
    # 连接到 MQTT Broker
    try:
        print(f"\n🔌 正在连接到 MQTT Broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)  # 等待连接完成
        
        # 测试各种消息类型
        print("\n" + "="*70)
        print("开始测试...")
        print("="*70)
        
        # 1. HTTP API 格式
        publish_http_format_data(client)
        time.sleep(2)
        
        # 2. MQTT 简单格式
        publish_mqtt_simple_format_data(client)
        time.sleep(2)
        
        # 3. 设备状态
        publish_status(client)
        time.sleep(2)
        
        # 4. 心跳
        publish_heartbeat(client)
        time.sleep(2)
        
        # 5. 无效数据测试
        test_invalid_data(client)
        time.sleep(2)
        
        print("\n" + "="*70)
        print("✅ 所有测试完成！")
        print("="*70)
        print("\n📝 后续操作：")
        print("1. 查看 MQTT 服务日志确认消息已处理")
        print("2. 查询数据库验证数据已更新")
        print("\n查询命令：")
        print(f"mysql -u root -p aiot_admin -e \"")
        print(f"  SELECT device_id, name, is_online, last_seen,")
        print(f"         JSON_PRETTY(last_report_data) as data")
        print(f"  FROM device_main")
        print(f"  WHERE uuid = '{TEST_DEVICE_UUID}';\"")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n👋 断开连接")


if __name__ == "__main__":
    main()





