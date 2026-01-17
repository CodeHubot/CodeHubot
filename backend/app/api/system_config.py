"""
系统配置管理 API
用于管理系统级别的配置项
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.system_config import SystemConfig
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigInDB,
    SystemConfigPublic,
    ModuleConfigResponse,
    ModuleConfigUpdate,
    PlatformConfigResponse,
    PlatformConfigUpdate,
    PoliciesConfigResponse,
    PoliciesConfigUpdate,
    DeviceMqttConfigResponse,
    DeviceMqttConfigUpdate
)
from app.core.deps import get_current_user
from app.models.user import User
from app.core.response import success_response

router = APIRouter()


def is_platform_admin(current_user: User) -> bool:
    """检查是否为平台管理员"""
    return current_user.role == "platform_admin"


def get_config_value(db: Session, key: str, default: str = None) -> Optional[str]:
    """获取配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    return config.config_value if config else default


def set_config_value(db: Session, key: str, value: str, config_type: str = "string", 
                     description: str = None, category: str = "system", is_public: bool = False):
    """设置配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if config:
        config.config_value = value
        if description:
            config.description = description
    else:
        config = SystemConfig(
            config_key=key,
            config_value=value,
            config_type=config_type,
            description=description,
            category=category,
            is_public=is_public
        )
        db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _get_module_config_data(db: Session) -> ModuleConfigResponse:
    """内部函数：获取模块配置数据"""
    def get_bool_config(key: str, default: bool = True) -> bool:
        value = get_config_value(db, key, str(default).lower())
        return value.lower() in ('true', '1', 'yes') if value else default
    
    return ModuleConfigResponse(
        enable_user_registration=get_bool_config("enable_user_registration", True),
        enable_device_module=get_bool_config("enable_device_module", True),
        enable_ai_module=get_bool_config("enable_ai_module", True),
        enable_pbl_module=get_bool_config("enable_pbl_module", True)
    )


def _get_platform_config_data(db: Session, include_policies: bool = False) -> PlatformConfigResponse:
    """内部函数：获取平台配置数据"""
    def get_string_config(key: str, default: str = "") -> str:
        value = get_config_value(db, key, default)
        return value if value else default
    
    def get_bool_config(key: str, default: bool = False) -> bool:
        value = get_config_value(db, key, str(default).lower())
        return value.lower() in ('true', '1', 'yes') if value else default
    
    response_data = {
        "platform_name": get_string_config("platform_name", "CodeHubot"),
        "platform_description": get_string_config("platform_description", "智能物联网管理平台"),
        "enable_user_registration": get_bool_config("enable_user_registration", False)
    }
    
    # 只有明确请求时才返回协议内容，以节省网络流量
    if include_policies:
        response_data["user_agreement"] = get_string_config("user_agreement", "")
        response_data["privacy_policy"] = get_string_config("privacy_policy", "")
    
    return PlatformConfigResponse(**response_data)


def _get_policies_config_data(db: Session) -> PoliciesConfigResponse:
    """内部函数：获取协议配置数据"""
    def get_text_config(key: str, default: str = "") -> str:
        value = get_config_value(db, key, default)
        return value if value else default
    
    return PoliciesConfigResponse(
        user_agreement=get_text_config("user_agreement", ""),
        privacy_policy=get_text_config("privacy_policy", "")
    )


@router.get("/configs", response_model=List[SystemConfigInDB])
async def get_all_configs(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有系统配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以查看系统配置"
        )
    
    query = db.query(SystemConfig)
    if category:
        query = query.filter(SystemConfig.category == category)
    
    configs = query.all()
    return configs


@router.get("/configs/public", response_model=List[SystemConfigPublic])
async def get_public_configs(
    exclude_policies: bool = Query(True, description="是否排除用户协议和隐私政策（默认true以节省流量）"),
    db: Session = Depends(get_db)
):
    """
    获取公开的系统配置（无需认证）
    用于前端判断是否显示某些功能模块
    
    参数:
        exclude_policies: 是否排除用户协议和隐私政策（默认true）
                         这些大体积内容可通过 /policies 接口单独获取
    """
    query = db.query(SystemConfig).filter(SystemConfig.is_public == True)
    
    # 默认排除大体积的协议配置，以节省网络流量
    if exclude_policies:
        query = query.filter(
            ~SystemConfig.config_key.in_(['user_agreement', 'privacy_policy'])
        )
    
    configs = query.all()
    return configs


@router.get("/configs/{config_key}", response_model=SystemConfigInDB)
async def get_config(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个配置项（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以查看系统配置"
        )
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在"
        )
    
    return config


@router.post("/configs", response_model=SystemConfigInDB)
async def create_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建系统配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以创建系统配置"
        )
    
    # 检查配置键是否已存在
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == config.config_key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置项 {config.config_key} 已存在"
        )
    
    db_config = SystemConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/configs/{config_key}", response_model=SystemConfigInDB)
async def update_config(
    config_key: str,
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新系统配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新系统配置"
        )
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在"
        )
    
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/configs/{config_key}")
async def delete_config(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除系统配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以删除系统配置"
        )
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 {config_key} 不存在"
        )
    
    db.delete(config)
    db.commit()
    return success_response(message=f"配置项 {config_key} 已删除")


# ==================== 模块配置专用接口 ====================

@router.get("/modules", response_model=ModuleConfigResponse)
async def get_module_config(db: Session = Depends(get_db)):
    """
    获取模块配置（公开接口，无需认证）
    返回各个模块的启用状态
    """
    return _get_module_config_data(db)


@router.put("/modules", response_model=ModuleConfigResponse)
async def update_module_config(
    module_config: ModuleConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新模块配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新模块配置"
        )
    
    update_data = module_config.model_dump(exclude_unset=True)
    
    config_mapping = {
        "enable_user_registration": ("是否开启用户注册", "module"),
        "enable_device_module": ("是否开启设备管理模块", "module"),
        "enable_ai_module": ("是否开启AI模块", "module"),
        "enable_pbl_module": ("是否开启PBL模块", "module")
    }
    
    for key, value in update_data.items():
        description, category = config_mapping[key]
        set_config_value(
            db=db,
            key=key,
            value=str(value).lower(),
            config_type="boolean",
            description=description,
            category=category,
            is_public=True
        )
    
    # 返回更新后的配置
    return _get_module_config_data(db)


@router.post("/modules/init")
async def init_module_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    初始化模块配置（仅平台管理员）
    如果配置不存在，则创建默认配置
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以初始化模块配置"
        )
    
    default_configs = [
        ("enable_user_registration", "false", "boolean", "是否开启用户注册", "module", True),
        ("enable_device_module", "true", "boolean", "是否开启设备管理模块", "module", True),
        ("enable_ai_module", "true", "boolean", "是否开启AI模块", "module", True),
        ("enable_pbl_module", "true", "boolean", "是否开启PBL模块", "module", True),
        ("platform_name", "CodeHubot", "string", "平台名称", "system", True),
        ("platform_description", "智能物联网管理平台", "string", "平台描述", "system", True),
    ]
    
    created_count = 0
    for key, value, config_type, description, category, is_public in default_configs:
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if not existing:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                config_type=config_type,
                description=description,
                category=category,
                is_public=is_public
            )
            db.add(config)
            created_count += 1
    
    db.commit()
    
    return success_response(
        message=f"模块配置初始化完成，创建了 {created_count} 个配置项",
        data={"created_count": created_count}
    )


# ==================== 平台配置专用接口 ====================

@router.get("/platform", response_model=PlatformConfigResponse)
async def get_platform_config(
    include_policies: bool = Query(False, description="是否包含用户协议和隐私政策（默认false以节省流量）"),
    db: Session = Depends(get_db)
):
    """
    获取平台配置（公开接口，无需认证）
    返回平台名称、描述、注册开关等基础信息
    
    参数:
        include_policies: 是否包含用户协议和隐私政策（默认false）
                         如需获取协议内容，请使用 /policies 接口或设置此参数为true
    """
    return _get_platform_config_data(db, include_policies)


@router.put("/platform", response_model=PlatformConfigResponse)
async def update_platform_config(
    platform_config: PlatformConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新平台配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新平台配置"
        )
    
    update_data = platform_config.model_dump(exclude_unset=True)
    
    config_mapping = {
        "platform_name": ("平台名称", "system", "string"),
        "platform_description": ("平台描述", "system", "string"),
        "enable_user_registration": ("是否开启用户注册", "module", "boolean")
    }
    
    for key, value in update_data.items():
        description, category, config_type = config_mapping[key]
        # boolean 类型转换为字符串 "true" 或 "false"
        if config_type == "boolean":
            value = str(value).lower()
        set_config_value(
            db=db,
            key=key,
            value=str(value),
            config_type=config_type,
            description=description,
            category=category,
            is_public=True
        )
    
    # 返回更新后的配置
    return await get_platform_config(db)


# ==================== 协议配置专用接口 ====================

@router.get("/policies", response_model=PoliciesConfigResponse)
async def get_policies_config(db: Session = Depends(get_db)):
    """
    获取协议配置（公开接口，无需认证）
    返回用户协议和隐私政策内容
    """
    def get_text_config(key: str, default: str = "") -> str:
        value = get_config_value(db, key, default)
        return value if value else default
    
    return PoliciesConfigResponse(
        user_agreement=get_text_config("user_agreement", ""),
        privacy_policy=get_text_config("privacy_policy", "")
    )


@router.put("/policies", response_model=PoliciesConfigResponse)
async def update_policies_config(
    policies_config: PoliciesConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新协议配置（仅平台管理员）
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新协议配置"
        )
    
    update_data = policies_config.model_dump(exclude_unset=True)
    
    config_mapping = {
        "user_agreement": ("用户协议内容", "policy", "text"),
        "privacy_policy": ("隐私政策内容", "policy", "text")
    }
    
    for key, value in update_data.items():
        description, category, config_type = config_mapping[key]
        set_config_value(
            db=db,
            key=key,
            value=str(value) if value else "",
            config_type=config_type,
            description=description,
            category=category,
            is_public=True
        )
    
    # 返回更新后的配置
    return await get_policies_config(db)


# ==================== 设备MQTT配置专用接口 ====================

@router.get("/device-mqtt", response_model=DeviceMqttConfigResponse)
async def get_device_mqtt_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备MQTT配置（仅平台管理员）
    返回设备连接MQTT Broker的配置信息
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以查看设备MQTT配置"
        )
    
    def get_string_config(key: str, default: str = "") -> str:
        value = get_config_value(db, key, default)
        return value if value else default
    
    def get_int_config(key: str, default: int = 1883) -> int:
        value = get_config_value(db, key, str(default))
        try:
            return int(value) if value else default
        except ValueError:
            return default
    
    def get_bool_config(key: str, default: bool = False) -> bool:
        value = get_config_value(db, key, str(default).lower())
        return value.lower() in ('true', '1', 'yes') if value else default
    
    return DeviceMqttConfigResponse(
        device_mqtt_broker=get_string_config("device_mqtt_broker", "mqtt.example.com"),
        device_mqtt_port=get_int_config("device_mqtt_port", 1883),
        device_mqtt_use_ssl=get_bool_config("device_mqtt_use_ssl", False)
    )


@router.put("/device-mqtt", response_model=DeviceMqttConfigResponse)
async def update_device_mqtt_config(
    mqtt_config: DeviceMqttConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新设备MQTT配置（仅平台管理员）
    更新后config-service需要刷新配置缓存才能生效
    """
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新设备MQTT配置"
        )
    
    update_data = mqtt_config.model_dump(exclude_unset=True)
    
    config_mapping = {
        "device_mqtt_broker": ("设备连接的MQTT Broker地址", "device", "string"),
        "device_mqtt_port": ("设备连接的MQTT Broker端口", "device", "integer"),
        "device_mqtt_use_ssl": ("设备连接MQTT是否使用SSL/TLS", "device", "boolean")
    }
    
    for key, value in update_data.items():
        description, category, config_type = config_mapping[key]
        # 布尔值转字符串
        if isinstance(value, bool):
            value = str(value).lower()
        # 整数转字符串
        elif isinstance(value, int):
            value = str(value)
        
        set_config_value(
            db=db,
            key=key,
            value=value,
            config_type=config_type,
            description=description,
            category=category,
            is_public=False  # 设备MQTT配置不公开
        )
    
    # 返回更新后的配置
    return await get_device_mqtt_config(db, current_user)
