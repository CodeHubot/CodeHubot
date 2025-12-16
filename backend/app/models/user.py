from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive

class User(Base):
    __tablename__ = "core_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)  # 改为可选
    username = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True, comment='姓名')
    real_name = Column(String(100), nullable=True, comment='真实姓名')
    gender = Column(Enum('male', 'female', 'other', name='gender_enum'), nullable=True, comment='性别：male-男, female-女, other-其他')
    nickname = Column(String(50), nullable=True, comment='用户昵称（可选，优先显示）')
    phone = Column(String(20), nullable=True, comment='手机号')
    password_hash = Column(String(255), nullable=False)
    
    # 角色和归属
    role = Column(String(50), default='individual', nullable=False, comment='用户角色：individual/platform_admin/school_admin/teacher/student')
    school_id = Column(Integer, ForeignKey('core_schools.id', ondelete='SET NULL'), nullable=True, index=True, comment='所属学校ID（独立用户为NULL）')
    school_name = Column(String(200), nullable=True, comment='学校名称（冗余字段，便于查询）')
    
    # 机构用户字段
    teacher_number = Column(String(50), nullable=True, index=True, comment='教师工号（仅教师/学校管理员有）')
    student_number = Column(String(50), nullable=True, index=True, comment='学生学号（仅学生有）')
    subject = Column(String(50), nullable=True, comment='教师学科')
    
    # 状态字段
    is_active = Column(Boolean, default=True)
    need_change_password = Column(Boolean, default=False, comment='首次登录需修改密码')
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True, comment='最后登录IP')
    
    # 时间戳 - 使用北京时间
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    deleted_at = Column(DateTime, nullable=True, comment='软删除时间')
    
    # 关系
    # school = relationship("School", back_populates="users")
    # 选课关系（学生-课程多对多）
    enrolled_courses = relationship("CourseStudent", back_populates="student", cascade="all, delete-orphan")
    # 授课关系（教师-课程多对多）
    teaching_courses = relationship("CourseTeacher", back_populates="teacher", cascade="all, delete-orphan")
    # 分组关系
    led_course_groups = relationship("CourseGroup", foreign_keys="CourseGroup.leader_id", back_populates="leader")
    group_memberships = relationship("GroupMember", back_populates="student", cascade="all, delete-orphan")
    # 设备关系
    devices = relationship("Device", back_populates="user")
