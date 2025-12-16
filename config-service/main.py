"""
设备配置服务 (Device Provisioning Service)
轻量级独立服务，为物联网设备提供配置信息

功能：
1. 根据MAC地址获取设备UUID和凭证
2. 提供MQTT服务器配置信息
3. 检测固件更新
4. 提供设备初始化所需的所有配置
"""

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import logging
import time
import hashlib
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置 ====================
# 从环境变量读取配置
# 从独立配置项构建数据库连接URL
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "3306")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

if not all([db_host, db_user, db_password, db_name]):
    raise ValueError("数据库配置不完整：请提供 DB_HOST、DB_USER、DB_PASSWORD、DB_NAME（DB_PORT 可选，默认 3306）")

DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.example.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USE_SSL = os.getenv("MQTT_USE_SSL", "false").lower() == "true"
API_SERVER = os.getenv("API_SERVER", "http://api.example.com")
OTA_SERVER = os.getenv("OTA_SERVER", "http://ota.example.com")

# 速率限制配置
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# ==================== 数据库模型 ====================
Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DeviceRecord(Base):
    """设备记录"""
    __tablename__ = "device_main"
    
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(17), unique=True, index=True, nullable=False)
    device_id = Column(String(64), unique=True, nullable=False)
    uuid = Column(String(36), unique=True, nullable=False)
    device_secret = Column(String(64), nullable=False)
    product_id = Column(String(64), nullable=True, index=True)  # 产品标识符（字符串）
    firmware_version = Column(String(32), nullable=True)
    hardware_version = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FirmwareVersion(Base):
    """固件版本"""
    __tablename__ = "device_firmware_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(64), nullable=True, index=True)  # 产品编码（与主backend保持一致）
    version = Column(String(32), unique=True, nullable=False)
    firmware_url = Column(String(512), nullable=False)  # 与主backend字段名一致
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # 与主backend字段名一致
    description = Column(String(1024), nullable=True)
    release_notes = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True)
    is_latest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessLog(Base):
    """访问日志（简单的速率限制）"""
    __tablename__ = "aiot_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), index=True)
    endpoint = Column(String(128))
    mac_address = Column(String(17), nullable=True)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_agent = Column(String(256), nullable=True)


# 创建表（已禁用，直接在数据库中初始化）
# Base.metadata.create_all(bind=engine)


# ==================== 依赖注入 ====================
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 请求/响应模型 ====================
class DeviceInfoRequest(BaseModel):
    """设备信息查询请求"""
    mac_address: str = Field(..., description="设备MAC地址", pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    product_id: str = Field(..., description="产品标识符（如：ESP32-S3-Dev-01）", min_length=1, max_length=64)
    firmware_version: str = Field(..., description="当前固件版本", min_length=1)


class DeviceInfoResponse(BaseModel):
    """设备信息响应 - 精简版，只返回固件端需要的字段"""
    # 设备基本信息
    device_id: str = Field(..., description="设备ID")
    device_uuid: str = Field(..., description="设备UUID")
    mac_address: str = Field(..., description="MAC地址")
    product_id: Optional[str] = Field(None, description="产品标识符")
    
    # MQTT配置（包含所有MQTT连接所需信息，包括password）
    mqtt_config: Dict[str, Any] = Field(..., description="MQTT配置")
    
    # 固件更新信息（可选）
    firmware_update: Optional[Dict[str, Any]] = Field(None, description="固件更新信息")


class FirmwareCheckRequest(BaseModel):
    """固件更新检查请求"""
    mac_address: str = Field(..., description="设备MAC地址")
    current_version: str = Field(..., description="当前固件版本")
    product_id: Optional[str] = Field(None, description="产品标识符", max_length=64)


class FirmwareCheckResponse(BaseModel):
    """固件更新检查响应"""
    update_available: bool = Field(..., description="是否有更新")
    current_version: str = Field(..., description="当前版本")
    latest_version: Optional[str] = Field(None, description="最新版本")
    download_url: Optional[str] = Field(None, description="下载地址")
    file_size: Optional[int] = Field(None, description="文件大小")
    checksum: Optional[str] = Field(None, description="文件校验和")
    changelog: Optional[str] = Field(None, description="更新日志")
    message: str = Field(..., description="响应消息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="服务器时间")
    version: str = Field(..., description="服务版本")


# ==================== 速率限制 ====================
class SimpleRateLimiter:
    """简单的内存速率限制器"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def _get_key(self, ip: str, identifier: str = "") -> str:
        """生成速率限制key"""
        return hashlib.md5(f"{ip}:{identifier}".encode()).hexdigest()
    
    def check(self, ip: str, identifier: str = "", max_requests: int = 10, window: int = 60) -> bool:
        """
        检查速率限制
        
        Args:
            ip: IP地址
            identifier: 额外标识符（如MAC地址）
            max_requests: 时间窗口内最大请求数
            window: 时间窗口（秒）
            
        Returns:
            True: 允许请求
            False: 超过限制
        """
        key = self._get_key(ip, identifier)
        now = time.time()
        
        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if now - t < window]
        else:
            self.requests[key] = []
        
        # 检查是否超过限制
        if len(self.requests[key]) >= max_requests:
            return False
        
        # 记录本次请求
        self.requests[key].append(now)
        return True
    
    def cleanup(self):
        """清理过期记录"""
        now = time.time()
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if now - t < 3600]
            if not self.requests[key]:
                del self.requests[key]


rate_limiter = SimpleRateLimiter()


# ==================== FastAPI应用 ====================
app = FastAPI(
    title="设备配置服务",
    description="为物联网设备提供配置信息的轻量级服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 设备端可能来自任何IP
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ==================== API端点 ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


def _get_device_info_impl(
    mac_address: str,
    product_id: str,
    firmware_version: str,
    client_ip: str,
    user_agent: str,
    db: Session
) -> DeviceInfoResponse:
    """
    获取设备配置的内部实现（供GET和POST共用）
    
    Args:
        mac_address: 设备MAC地址
        product_id: 产品标识符（必需，如：ESP32-S3-Dev-01）
        firmware_version: 固件版本（必需，用于OTA检查和设备管理）
        client_ip: 客户端IP
        user_agent: User Agent
        db: 数据库会话
    """
    start_time = time.time()
    
    # 速率限制检查
    if not rate_limiter.check(client_ip, mac_address, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW):
        logger.warning(f"速率限制: IP={client_ip}, MAC={mac_address}")
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")
    
    # 查询设备
    device = db.query(DeviceRecord).filter(
        DeviceRecord.mac_address == mac_address
    ).first()
    
    if not device:
        # 记录失败日志
        log = AccessLog(
            ip_address=client_ip,
            endpoint="/device/info",
            mac_address=mac_address,
            success=False,
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
        
        logger.warning(f"设备未找到: MAC={mac_address}, IP={client_ip}")
        
        # 固定延迟，防止时序攻击
        elapsed = time.time() - start_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        
        raise HTTPException(status_code=404, detail="设备未注册")
    
    if not device.is_active:
        raise HTTPException(status_code=403, detail="设备已被禁用")
    
    # 更新设备信息
    device.last_seen = datetime.utcnow()
    if firmware_version:
        device.firmware_version = firmware_version
    # product_id 是设备的固定属性，不需要更新
    
    # 检查固件更新
    firmware_update = None
    if firmware_version:
        latest_firmware = db.query(FirmwareVersion).filter(
            FirmwareVersion.is_active == True,
            FirmwareVersion.product_code == device.product_id
        ).order_by(FirmwareVersion.created_at.desc()).first()
        
        if latest_firmware and latest_firmware.version != firmware_version:
            firmware_update = {
                "available": True,
                "version": latest_firmware.version,
                "download_url": latest_firmware.firmware_url,  # 使用正确的字段名
                "file_size": latest_firmware.file_size,
                "checksum": latest_firmware.file_hash,  # 使用正确的字段名
                "changelog": latest_firmware.release_notes  # 使用正确的字段名
            }
    
    # 记录成功日志
    log = AccessLog(
        ip_address=client_ip,
        endpoint="/device/info",
        mac_address=mac_address,
        success=True,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    
    logger.info(
        f"设备配置查询成功: "
        f"MAC={mac_address}, "
        f"DeviceID={device.device_id}, "
        f"IP={client_ip}"
    )
    
    # 构建MQTT配置（精简版，只包含固件需要的字段）
    mqtt_config = {
        "broker": MQTT_BROKER,
        "port": MQTT_PORT,
        "username": device.device_id,
        "password": device.device_secret,  # device_secret在这里使用，不需要单独返回
        "use_ssl": MQTT_USE_SSL,
        "topics": {
            "data": f"devices/{device.uuid}/data",
            "control": f"devices/{device.uuid}/control",
            "status": f"devices/{device.uuid}/status",
            "heartbeat": f"devices/{device.uuid}/heartbeat"
        }
    }
    
    # 构建响应数据（精简版，只返回固件实际需要的字段）
    # 注意：product_id 可能是整数或字符串，统一转换为字符串
    product_id_str = str(device.product_id) if device.product_id is not None else None
    
    response_data = {
        "device_id": device.device_id,
        "device_uuid": device.uuid,
        "mac_address": device.mac_address,
        "product_id": product_id_str,
        "mqtt_config": mqtt_config,
        "firmware_update": firmware_update
    }
    
    # 调试日志
    logger.info(f"准备返回响应数据，device_id={response_data.get('device_id')}, product_id={response_data.get('product_id')}")
    
    try:
        return DeviceInfoResponse(**response_data)
    except Exception as e:
        import json
        logger.error(f"❌ DeviceInfoResponse 验证失败")
        logger.error(f"错误详情: {str(e)}")
        logger.error(f"响应数据JSON: {json.dumps(response_data, ensure_ascii=False, default=str, indent=2)}")
        # 打印每个字段的类型
        for key, value in response_data.items():
            logger.error(f"  {key}: {type(value).__name__} = {repr(value)[:100]}")
        raise HTTPException(status_code=500, detail=f"数据验证失败: {str(e)}")


@app.get("/device/info", response_model=DeviceInfoResponse)
async def get_device_info_by_get(
    mac: str = Query(..., description="设备MAC地址", regex=r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$"),
    product_id: str = Query(..., description="产品标识符/产品编码（如：ESP32-S3-Dev-01）", min_length=1, max_length=64),
    firmware_version: str = Query(..., description="当前固件版本", min_length=1),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    获取设备完整配置信息 (GET方式 - 推荐)
    
    设备启动后调用此接口，一次性获取所有需要的配置。
    
    必需参数:
    - mac: 设备MAC地址
    - product_id: 产品标识符/产品编码（字符串，如："ESP32-S3-Dev-01"，最长64字符）
    - firmware_version: 当前固件版本（服务器用于判断是否需要OTA）
    
    OTA逻辑:
    - 设备上报当前版本
    - 服务器判断是否需要更新
    - 如果需要，返回 firmware_update.download_url
    - 设备判断：有URL就更新，没有就跳过
    
    示例: GET /device/info?mac=AA:BB:CC:DD:EE:FF&product_id=ESP32-S3-Dev-01&firmware_version=1.0.0
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    return _get_device_info_impl(
        mac_address=mac,
        product_id=product_id,
        firmware_version=firmware_version,
        client_ip=client_ip,
        user_agent=user_agent,
        db=db
    )


@app.post("/device/info", response_model=DeviceInfoResponse)
async def get_device_info_by_post(
    request: Request,
    device_req: DeviceInfoRequest,
    db: Session = Depends(get_db)
):
    """
    获取设备完整配置信息 (POST方式 - 兼容)
    
    POST方式保留用于向后兼容，推荐使用GET方式
    
    必需字段:
    - mac_address: 设备MAC地址
    - product_id: 产品标识符/产品编码（字符串，如："ESP32-S3-Dev-01"，最长64字符）
    - firmware_version: 当前固件版本（服务器用于判断是否需要OTA）
    
    OTA逻辑:
    - 设备上报当前版本
    - 服务器判断是否需要更新
    - 如果需要，返回 firmware_update.download_url
    - 设备判断：有URL就更新，没有就跳过
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    return _get_device_info_impl(
        mac_address=device_req.mac_address,
        product_id=device_req.product_id,
        firmware_version=device_req.firmware_version,
        client_ip=client_ip,
        user_agent=user_agent,
        db=db
    )


@app.post("/firmware/check", response_model=FirmwareCheckResponse)
async def check_firmware_update(
    request: Request,
    firmware_req: FirmwareCheckRequest,
    db: Session = Depends(get_db)
):
    """
    检查固件更新
    
    设备可以定期调用此接口检查是否有新的固件版本
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 速率限制
    if not rate_limiter.check(client_ip, f"fw_{firmware_req.mac_address}", 5, 300):
        raise HTTPException(status_code=429, detail="请求过于频繁")
    
    # 查询设备
    device = db.query(DeviceRecord).filter(
        DeviceRecord.mac_address == firmware_req.mac_address
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="设备未注册")
    
    # 查询最新固件
    product_id = firmware_req.product_id or device.product_id
    latest_firmware = db.query(FirmwareVersion).filter(
        FirmwareVersion.is_active == True,
        FirmwareVersion.product_code == product_id
    ).order_by(FirmwareVersion.created_at.desc()).first()
    
    if not latest_firmware:
        return FirmwareCheckResponse(
            update_available=False,
            current_version=firmware_req.current_version,
            message="暂无可用固件"
        )
    
    # 比较版本
    update_available = latest_firmware.version != firmware_req.current_version
    
    logger.info(
        f"固件检查: MAC={firmware_req.mac_address}, "
        f"当前={firmware_req.current_version}, "
        f"最新={latest_firmware.version}, "
        f"需更新={update_available}"
    )
    
    return FirmwareCheckResponse(
        update_available=update_available,
        current_version=firmware_req.current_version,
        latest_version=latest_firmware.version if update_available else None,
        download_url=latest_firmware.firmware_url if update_available else None,  # 使用正确的字段名
        file_size=latest_firmware.file_size if update_available else None,
        checksum=latest_firmware.file_hash if update_available else None,  # 使用正确的字段名
        changelog=latest_firmware.release_notes if update_available else None,  # 使用正确的字段名
        message="有新版本可用" if update_available else "已是最新版本"
    )


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "AIOT Device Provisioning Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "device_info_get": "GET /device/info?mac=AA:BB:CC:DD:EE:FF (推荐)",
            "device_info_post": "POST /device/info (兼容)",
            "firmware_check": "POST /firmware/check"
        },
        "example": "curl http://localhost:8001/device/info?mac=AA:BB:CC:DD:EE:FF"
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    
    logger.info(f"🚀 启动设备配置服务，端口: {port}")
    logger.info(f"📡 MQTT服务器: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"🌐 API服务器: {API_SERVER}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

