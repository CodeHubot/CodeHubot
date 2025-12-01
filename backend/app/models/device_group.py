"""
设备分组和授权模型
用于学校管理员管理设备并授权给课程使用
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib


class DeviceGroup(Base):
    """设备分组模型"""
    __tablename__ = "aiot_device_groups"
    
    id = Column(Integer, primary_key=True, index=True, comment="分组ID")
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid_lib.uuid4()), comment='UUID')
    school_id = Column(Integer, ForeignKey("aiot_schools.id"), nullable=False, index=True, comment="所属学校ID")
    group_name = Column(String(100), nullable=False, comment="设备组名称")
    group_code = Column(String(50), comment="设备组编号")
    description = Column(Text, comment="描述")
    device_count = Column(Integer, default=0, comment="设备数量")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    created_by = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=True, comment="创建人ID")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    school = relationship("School", back_populates="device_groups")
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("DeviceGroupMember", back_populates="group", cascade="all, delete-orphan")
    authorizations = relationship("CourseDeviceAuthorization", back_populates="device_group", cascade="all, delete-orphan")


class DeviceGroupMember(Base):
    """设备分组成员模型"""
    __tablename__ = "aiot_device_group_members"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    group_id = Column(Integer, ForeignKey("aiot_device_groups.id"), nullable=False, index=True, comment="设备组ID")
    device_id = Column(Integer, ForeignKey("aiot_core_devices.id"), nullable=False, index=True, comment="设备ID")
    joined_at = Column(DateTime, default=get_beijing_time_naive, comment="加入时间")
    left_at = Column(DateTime, nullable=True, comment="离开时间")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    
    # 关系
    group = relationship("DeviceGroup", back_populates="members")
    device = relationship("Device", back_populates="group_memberships")


class CourseDeviceAuthorization(Base):
    """课程设备授权模型"""
    __tablename__ = "aiot_course_device_authorizations"
    
    id = Column(Integer, primary_key=True, index=True, comment="授权ID")
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid_lib.uuid4()), comment='UUID')
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=False, index=True, comment="课程ID")
    device_group_id = Column(Integer, ForeignKey("aiot_device_groups.id"), nullable=False, index=True, comment="设备组ID")
    authorized_by = Column(Integer, ForeignKey("aiot_core_users.id"), nullable=False, comment="授权人ID")
    authorized_at = Column(DateTime, default=get_beijing_time_naive, comment="授权时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    course = relationship("Course", back_populates="device_authorizations")
    device_group = relationship("DeviceGroup", back_populates="authorizations")
    authorizer = relationship("User", foreign_keys=[authorized_by])

