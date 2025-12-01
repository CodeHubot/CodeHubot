from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class School(Base):
    """学校模型"""
    __tablename__ = "aiot_schools"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid_lib.uuid4()), comment='UUID，用于外部API访问')
    school_code = Column(String(50), unique=True, nullable=False, index=True, comment='学校代码（如 BJ-YCZX）')
    school_name = Column(String(200), nullable=False, comment='学校名称')
    province = Column(String(50), comment='省份')
    city = Column(String(50), comment='城市')
    district = Column(String(50), comment='区/县')
    address = Column(String(500), comment='详细地址')
    contact_person = Column(String(100), comment='联系人')
    contact_phone = Column(String(20), comment='联系电话')
    contact_email = Column(String(255), comment='联系邮箱')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否激活')
    license_expire_at = Column(Date, comment='授权到期时间')
    max_teachers = Column(Integer, default=100, comment='最大教师数')
    max_students = Column(Integer, default=1000, comment='最大学生数')
    max_devices = Column(Integer, default=500, comment='最大设备数')
    
    # 时间戳 - 使用北京时间
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)
    
    # 关系
    # users = relationship("User", back_populates="school")
    courses = relationship("Course", back_populates="school", cascade="all, delete-orphan")
    course_groups = relationship("CourseGroup", back_populates="school", cascade="all, delete-orphan")
    group_members = relationship("GroupMember", back_populates="school", cascade="all, delete-orphan")
    device_groups = relationship("DeviceGroup", back_populates="school", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="school")

