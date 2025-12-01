from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator, Field
from typing import Optional
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 数据库配置（必须配置）
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    
    # 数据库连接URL（自动构建，无需手动配置）
    database_url: Optional[str] = None
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 服务器配置
    server_base_url: str = "http://localhost:8000"  # 服务器基础URL，用于生成固件下载链接等
    firmware_base_url: Optional[str] = None  # 固件下载基础URL（可选，默认使用server_base_url）
    
    # JWT配置（必须从环境变量读取）
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=15,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="access token有效期（分钟）"
    )
    refresh_token_expire_minutes: int = Field(
        default=45,
        validation_alias="REFRESH_TOKEN_EXPIRE_MINUTES",
        description="refresh token有效期（分钟）"
    )
    
    # 内部API密钥（用于内部服务调用，可选）
    internal_api_key: Optional[str] = None
    
    # MQTT配置（必须从环境变量读取）
    mqtt_broker_host: str
    mqtt_broker_port: int = 1883
    mqtt_username: str
    mqtt_password: str
    
    # 邮件服务配置（可选）
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_tls: bool = True
    mail_ssl: bool = False
    use_credentials: bool = True
    validate_certs: bool = True
    
    # 交互日志配置
    log_batch_size: int = 1000  # 批量写入大小
    log_flush_interval: float = 5.0  # 刷新间隔（秒）
    log_retention_days: int = 90  # 日志保留天数
    log_compression_enabled: bool = True  # 启用压缩
    log_archive_enabled: bool = True  # 启用归档
    
    # 缓存配置
    cache_recent_logs_ttl: int = 300  # 最近日志缓存时间（秒）
    cache_stats_ttl: int = 3600  # 统计数据缓存时间（秒）
    cache_device_status_ttl: int = 60  # 设备状态缓存时间（秒）
    
    # 设备离线超时配置
    device_offline_timeout_minutes: int = 5  # 设备离线超时时间（分钟），超过此时间未收到数据则自动设置为离线
    
    # 性能配置
    max_concurrent_writes: int = 10  # 最大并发写入数
    query_timeout: int = 30  # 查询超时时间（秒）
    connection_pool_size: int = 20  # 连接池大小
    
    # 环境配置
    environment: str = "development"  # development, production, testing
    
    # 日志级别配置
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量，避免部署时出错
    
    @model_validator(mode='after')
    def build_database_url(self):
        """从独立配置项构建数据库URL"""
        self.database_url = f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return self
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()
    
    def _validate_security_settings(self):
        """验证安全配置"""
        # 验证JWT密钥强度
        if len(self.secret_key) < 32:
            logger.error("SECRET_KEY必须至少32个字符！")
            raise ValueError("SECRET_KEY必须至少32个字符以确保安全性")
        
        # 生产环境必须使用强密钥
        if self.environment == "production":
            if "your-secret-key" in self.secret_key.lower() or "change" in self.secret_key.lower():
                raise ValueError("生产环境禁止使用默认密钥！")
        
        # 输出Token配置信息（用于调试）
        logger.info(f"🔑 Token有效期 - Access: {self.access_token_expire_minutes}分钟, Refresh: {self.refresh_token_expire_minutes}分钟")
        
        logger.info("✅ 安全配置验证通过")
    
    @property
    def get_firmware_base_url(self) -> str:
        """获取固件下载基础URL"""
        return self.firmware_base_url or self.server_base_url

# 创建全局settings实例
try:
    settings = Settings()
except Exception as e:
    logger.error(f"❌ 配置加载失败: {e}")
    logger.info("💡 提示：请确保 .env 文件已正确配置所有必需的环境变量")
    logger.info("💡 参考 env.example 文件创建 .env")
    raise
