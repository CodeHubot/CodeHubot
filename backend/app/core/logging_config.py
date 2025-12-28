"""
日志配置模块
提供统一的日志获取接口
"""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
        level: 日志级别（可选），默认为 INFO
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果logger还没有handler，添加默认handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # 设置日志级别
    if level is not None:
        logger.setLevel(level)
    elif logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    
    return logger


# 预配置常用的日志记录器
def setup_logging(level: int = logging.INFO):
    """设置全局日志配置
    
    Args:
        level: 日志级别，默认为 INFO
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )







