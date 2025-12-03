"""
系统默认配置初始化模块
在应用启动时自动创建默认的大模型和产品配置
"""
import logging
import os
import json
import uuid as uuid_lib
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.llm_model import LLMModel
from app.models.product import Product

logger = logging.getLogger(__name__)


def init_default_llm_model(db: Session) -> bool:
    """
    初始化默认大模型（通义千问）
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 是否成功创建或已存在
    """
    # 从环境变量读取配置
    qwen_api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
    qwen_api_base = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    qwen_model_name = os.getenv("QWEN_MODEL_NAME", "qwen-turbo")
    qwen_display_name = os.getenv("QWEN_DISPLAY_NAME", "通义千问-Turbo")
    qwen_max_tokens = int(os.getenv("QWEN_MAX_TOKENS", "8192"))
    qwen_temperature = float(os.getenv("QWEN_TEMPERATURE", "0.20"))
    qwen_top_p = float(os.getenv("QWEN_TOP_P", "0.90"))
    
    # 如果没有设置API密钥，跳过初始化
    if not qwen_api_key:
        logger.info("⚠️  未设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY 环境变量，跳过默认大模型初始化")
        return False
    
    # 检查默认模型是否已存在
    existing_model = db.query(LLMModel).filter(
        LLMModel.is_default == 1,
        LLMModel.is_active == 1
    ).first()
    
    if existing_model:
        logger.info(f"ℹ️  默认大模型已存在: {existing_model.display_name} (ID: {existing_model.id})")
        # 更新API密钥（如果环境变量有变化）
        if qwen_api_key and existing_model.api_key != qwen_api_key:
            existing_model.api_key = qwen_api_key
            existing_model.api_base = qwen_api_base
            db.commit()
            logger.info(f"✅ 已更新默认大模型API配置: {existing_model.display_name}")
        return True
    
    # 创建默认大模型
    try:
        default_model = LLMModel(
            uuid=str(uuid_lib.uuid4()),
            name=qwen_model_name,
            display_name=qwen_display_name,
            provider="qwen",
            model_type="chat",
            api_base=qwen_api_base,
            api_key=qwen_api_key,
            api_version="",
            max_tokens=qwen_max_tokens,
            temperature=qwen_temperature,
            top_p=qwen_top_p,
            enable_deep_thinking=0,
            frequency_penalty=0.00,
            presence_penalty=0.00,
            config=None,
            description="阿里云通义千问大语言模型，性能强劲，响应快速，适合对话场景",
            is_active=1,
            is_default=1,  # 设置为默认模型
            is_system=1,   # 系统内置
            sort_order=1
        )
        db.add(default_model)
        db.commit()
        db.refresh(default_model)
        
        logger.info(f"✅ 默认大模型创建成功: {qwen_display_name} (ID: {default_model.id})")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建默认大模型失败: {e}", exc_info=True)
        return False


def init_default_product(db: Session) -> bool:
    """
    初始化默认产品（ESP32-S3开发板）
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 是否成功创建或已存在
    """
    # 从环境变量读取配置
    product_code = os.getenv("DEFAULT_PRODUCT_CODE", "ESP-32-S3-01")
    product_name = os.getenv("DEFAULT_PRODUCT_NAME", "标准开发板")
    
    # 默认传感器配置
    sensor_types_json = os.getenv("DEFAULT_PRODUCT_SENSORS")
    if sensor_types_json:
        try:
            sensor_types = json.loads(sensor_types_json)
        except:
            sensor_types = None
    else:
        # 默认配置
        sensor_types = {
            "DHT11_humidity": {
                "name": "DHT11湿度",
                "type": "DHT11",
                "enabled": True,
                "data_field": "humidity"
            },
            "DHT11_temperature": {
                "name": "DHT11温度",
                "type": "DHT11",
                "enabled": True,
                "data_field": "temperature"
            }
        }
    
    # 默认控制端口配置
    control_ports_json = os.getenv("DEFAULT_PRODUCT_CONTROLS")
    if control_ports_json:
        try:
            control_ports = json.loads(control_ports_json)
        except:
            control_ports = None
    else:
        # 默认配置
        control_ports = {
            "led_1": {
                "name": "LED1",
                "type": "LED",
                "enabled": True,
                "device_id": 1
            },
            "led_2": {
                "name": "LED2",
                "type": "LED",
                "enabled": True,
                "device_id": 2
            },
            "led_3": {
                "name": "LED3",
                "type": "LED",
                "enabled": True,
                "device_id": 3
            },
            "led_4": {
                "name": "LED4",
                "type": "LED",
                "enabled": True,
                "device_id": 4
            }
        }
    
    # 检查默认产品是否已存在
    existing_product = db.query(Product).filter(
        Product.product_code == product_code
    ).first()
    
    if existing_product:
        logger.info(f"ℹ️  默认产品已存在: {product_code} - {product_name} (ID: {existing_product.id})")
        return True
    
    # 创建默认产品
    try:
        default_product = Product(
            product_code=product_code,
            name=product_name,
            description="",
            category=None,
            sensor_types=sensor_types,
            control_ports=control_ports,
            device_capabilities=None,
            default_device_config=None,
            communication_protocols=None,
            power_requirements=None,
            firmware_version=None,
            hardware_version=None,
            is_active=True,
            version="1.0",
            manufacturer=None,
            manufacturer_code=None,
            total_devices=0,
            is_system=True,  # 系统内置
            creator_id=None,
            is_shared=False
        )
        db.add(default_product)
        db.commit()
        db.refresh(default_product)
        
        logger.info(f"✅ 默认产品创建成功: {product_code} - {product_name} (ID: {default_product.id})")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建默认产品失败: {e}", exc_info=True)
        return False


def init_defaults_on_startup():
    """
    应用启动时初始化默认配置
    """
    try:
        db = SessionLocal()
        try:
            init_default_llm_model(db)
            init_default_product(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ 初始化默认配置时发生错误: {e}", exc_info=True)

