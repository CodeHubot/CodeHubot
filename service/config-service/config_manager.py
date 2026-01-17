"""
配置管理模块
用于从数据库动态读取系统配置，支持缓存机制
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class SystemConfig(Base):
    """系统配置表（映射core_system_config）"""
    __tablename__ = "core_system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    config_type = Column(String(20), nullable=False, default="string")
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, default="system")
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class ConfigManager:
    """配置管理器 - 支持从数据库读取配置和内存缓存"""
    
    def __init__(self, db_session_factory, cache_ttl: int = 300):
        """
        初始化配置管理器
        
        Args:
            db_session_factory: SQLAlchemy SessionLocal工厂
            cache_ttl: 缓存过期时间（秒），默认300秒（5分钟）
        """
        self.db_session_factory = db_session_factory
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_time: Dict[str, datetime] = {}
        logger.info(f"配置管理器已初始化，缓存TTL: {cache_ttl}秒")
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_time:
            return False
        
        elapsed = (datetime.now() - self._cache_time[key]).total_seconds()
        return elapsed < self.cache_ttl
    
    def _get_from_db(self, key: str, db: Session) -> Optional[str]:
        """从数据库获取配置值"""
        try:
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            
            if config:
                # 缓存配置值和类型
                self._cache[key] = {
                    'value': config.config_value,
                    'type': config.config_type
                }
                self._cache_time[key] = datetime.now()
                logger.debug(f"从数据库读取配置: {key} = {config.config_value}")
                return config.config_value
            else:
                logger.warning(f"配置项不存在: {key}")
                return None
        except Exception as e:
            logger.error(f"读取配置失败 {key}: {e}")
            return None
    
    def get_string(self, key: str, default: str = None, env_fallback: str = None) -> str:
        """
        获取字符串类型配置
        
        优先级: 
        1. 数据库配置（有缓存则使用缓存）
        2. 环境变量（如果指定了env_fallback）
        3. 默认值
        
        Args:
            key: 配置键
            default: 默认值
            env_fallback: 环境变量名（作为fallback）
        """
        # 检查缓存
        if self._is_cache_valid(key):
            return self._cache[key]['value'] or default
        
        # 从数据库读取
        db = self.db_session_factory()
        try:
            value = self._get_from_db(key, db)
            if value is not None:
                return value
        finally:
            db.close()
        
        # Fallback到环境变量
        if env_fallback:
            env_value = os.getenv(env_fallback)
            if env_value:
                logger.info(f"使用环境变量 {env_fallback} = {env_value}")
                return env_value
        
        # 返回默认值
        logger.debug(f"使用默认值 {key} = {default}")
        return default
    
    def get_int(self, key: str, default: int = 0, env_fallback: str = None) -> int:
        """获取整数类型配置"""
        value = self.get_string(key, str(default), env_fallback)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"配置 {key} 值 '{value}' 不是有效整数，使用默认值 {default}")
            return default
    
    def get_bool(self, key: str, default: bool = False, env_fallback: str = None) -> bool:
        """获取布尔类型配置"""
        value = self.get_string(key, str(default), env_fallback)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return default
    
    def refresh(self, key: str = None):
        """
        刷新配置缓存
        
        Args:
            key: 指定刷新的配置键，如果为None则清空所有缓存
        """
        if key:
            self._cache.pop(key, None)
            self._cache_time.pop(key, None)
            logger.info(f"已刷新配置缓存: {key}")
        else:
            self._cache.clear()
            self._cache_time.clear()
            logger.info("已清空所有配置缓存")
    
    def get_all_device_configs(self) -> Dict[str, Any]:
        """获取所有设备相关配置（用于批量读取）"""
        db = self.db_session_factory()
        try:
            configs = db.query(SystemConfig).filter(
                SystemConfig.category == 'device'
            ).all()
            
            result = {}
            for config in configs:
                # 类型转换
                if config.config_type == 'integer':
                    result[config.config_key] = int(config.config_value) if config.config_value else 0
                elif config.config_type == 'boolean':
                    result[config.config_key] = config.config_value.lower() in ('true', '1', 'yes') if config.config_value else False
                else:
                    result[config.config_key] = config.config_value
                
                # 更新缓存
                self._cache[config.config_key] = {
                    'value': config.config_value,
                    'type': config.config_type
                }
                self._cache_time[config.config_key] = datetime.now()
            
            logger.info(f"批量加载设备配置 {len(result)} 项")
            return result
        finally:
            db.close()
