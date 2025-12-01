from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from app.core.config import settings
from app.core.constants import (
    DB_CONNECTION_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE
)

logger = logging.getLogger(__name__)

# 创建数据库引擎 - 优化连接池配置
engine_kwargs = {
    "pool_pre_ping": True,  # 连接前先ping，确保连接可用
    "pool_recycle": DB_POOL_RECYCLE,  # 1小时后回收连接
    "echo": False,  # 关闭SQL日志输出（避免日志混乱）
    "future": True,  # 使用SQLAlchemy 2.0风格
}

# 根据数据库类型配置
if "sqlite" in settings.database_url:
    # SQLite配置
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # MySQL/PostgreSQL配置
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_size": DB_CONNECTION_POOL_SIZE,  # 连接池大小
        "max_overflow": DB_MAX_OVERFLOW,  # 超出pool_size后最多创建的连接
        "pool_timeout": DB_POOL_TIMEOUT,  # 获取连接的超时时间（秒）
        "connect_args": {
            "connect_timeout": 10,  # 连接超时
            "charset": "utf8mb4",  # 使用utf8mb4编码
            # 兼容 MySQL 5.7 和 8.0
            # MySQL 5.7 需要 5.7.8+ 版本以支持 JSON 数据类型
        }
    })

try:
    engine = create_engine(settings.database_url, **engine_kwargs)
    logger.info("✅ 数据库引擎创建成功")
except Exception as e:
    logger.error(f"❌ 数据库引擎创建失败: {e}", exc_info=True)
    raise

# 监听连接事件（用于调试）
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """连接建立时的回调"""
    logger.debug("数据库连接已建立")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """从连接池获取连接时的回调"""
    logger.debug("从连接池获取连接")

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 避免commit后访问属性时重新查询
)

# 创建基类
Base = declarative_base()

def get_db():
    """获取数据库会话
    
    使用依赖注入提供数据库会话
    自动处理会话的创建和关闭
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"数据库会话异常: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.debug("数据库会话已关闭")
