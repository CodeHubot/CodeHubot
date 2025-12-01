"""
交互日志数据模型
支持TimescaleDB时序数据库优化
"""

from app.utils.timezone import get_beijing_time_naive
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from ..core.database import Base


class InteractionLog(Base):
    """交互日志表 - 时序数据优化"""
    
    __tablename__ = "aiot_interaction_logs"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 时间戳 - 时序数据库的分区键
    # 注意：使用 DateTime 而非 DateTime(timezone=True) 以兼容 MySQL 5.7
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # 设备信息
    device_id = Column(String(50), nullable=False, index=True)
    
    # 交互类型
    interaction_type = Column(String(20), nullable=False, index=True)
    # 可能的值：data_upload, data_download, command, heartbeat, config_update, firmware_update
    
    # 数据方向
    direction = Column(String(10), nullable=False)
    # inbound: 设备到服务器, outbound: 服务器到设备
    
    # 状态
    status = Column(String(10), nullable=False, index=True)
    # success, failed, timeout, pending
    
    # 性能指标
    data_size = Column(BigInteger, default=0)  # 数据大小（字节）
    response_time = Column(Integer)  # 响应时间（毫秒）
    
    # 错误信息
    error_code = Column(String(20))
    error_message = Column(Text)
    
    # 请求和响应数据（JSON格式，支持查询）
    request_data = Column(JSON)
    response_data = Column(JSON)
    
    # 网络信息
    client_ip = Column(String(45))  # 支持IPv4和IPv6
    user_agent = Column(Text)
    
    # 会话信息
    session_id = Column(String(100))
    
    # 创建时间
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<InteractionLog(id={self.id}, device_id='{self.device_id}', type='{self.interaction_type}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'interaction_type': self.interaction_type,
            'direction': self.direction,
            'status': self.status,
            'data_size': self.data_size,
            'response_time': self.response_time,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'client_ip': str(self.client_ip) if self.client_ip else None,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InteractionStatsHourly(Base):
    """小时级交互统计表"""
    
    __tablename__ = "aiot_interaction_stats_hourly"
    
    # 复合主键
    timestamp = Column(DateTime, primary_key=True)
    device_id = Column(String(50), primary_key=True)
    interaction_type = Column(String(20), primary_key=True)
    
    # 统计数据
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    
    # 性能统计
    avg_response_time = Column(Integer)  # 平均响应时间（毫秒）
    max_response_time = Column(Integer)  # 最大响应时间
    min_response_time = Column(Integer)  # 最小响应时间
    
    # 数据量统计
    total_data_size = Column(BigInteger, default=0)
    avg_data_size = Column(BigInteger, default=0)
    
    # 更新时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<InteractionStatsHourly(timestamp={self.timestamp}, device_id='{self.device_id}', type='{self.interaction_type}')>"
    
    @property
    def success_rate(self):
        """成功率"""
        if self.total_count == 0:
            return 0
        return round(self.success_count / self.total_count * 100, 2)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'interaction_type': self.interaction_type,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'timeout_count': self.timeout_count,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'max_response_time': self.max_response_time,
            'min_response_time': self.min_response_time,
            'total_data_size': self.total_data_size,
            'avg_data_size': self.avg_data_size,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class InteractionStatsDaily(Base):
    """日级交互统计表"""
    
    __tablename__ = "aiot_interaction_stats_daily"
    
    # 复合主键
    date = Column(DateTime, primary_key=True)
    device_id = Column(String(50), primary_key=True)
    
    # 统计数据
    total_interactions = Column(Integer, default=0)
    successful_interactions = Column(Integer, default=0)
    failed_interactions = Column(Integer, default=0)
    
    # 交互类型统计
    data_upload_count = Column(Integer, default=0)
    data_download_count = Column(Integer, default=0)
    command_count = Column(Integer, default=0)
    heartbeat_count = Column(Integer, default=0)
    
    # 性能统计
    avg_response_time = Column(Integer)
    total_data_transferred = Column(BigInteger, default=0)
    
    # 在线时长（分钟）
    online_duration = Column(Integer, default=0)
    
    # 更新时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<InteractionStatsDaily(date={self.date}, device_id='{self.device_id}')>"
    
    @property
    def success_rate(self):
        """成功率"""
        if self.total_interactions == 0:
            return 0
        return round(self.successful_interactions / self.total_interactions * 100, 2)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'device_id': self.device_id,
            'total_interactions': self.total_interactions,
            'successful_interactions': self.successful_interactions,
            'failed_interactions': self.failed_interactions,
            'success_rate': self.success_rate,
            'data_upload_count': self.data_upload_count,
            'data_download_count': self.data_download_count,
            'command_count': self.command_count,
            'heartbeat_count': self.heartbeat_count,
            'avg_response_time': self.avg_response_time,
            'total_data_transferred': self.total_data_transferred,
            'online_duration': self.online_duration,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }