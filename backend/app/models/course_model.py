"""
课程管理模块的数据模型
包含：课程(Course)、教师-课程关联(CourseTeacher)、学生-课程关联(CourseStudent)、课程分组(CourseGroup)、分组成员(GroupMember)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class Course(Base):
    """课程模型"""
    __tablename__ = "aiot_courses"
    
    id = Column(Integer, primary_key=True, index=True, comment="课程ID")
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid_lib.uuid4()), comment='UUID，用于外部API访问')
    school_id = Column(Integer, ForeignKey("core_schools.id"), nullable=False, index=True, comment="所属学校ID")
    course_name = Column(String(100), nullable=False, comment="课程名称")
    course_code = Column(String(20), comment="课程编号")
    academic_year = Column(String(20), index=True, comment="学年")
    semester = Column(SQLEnum('spring', 'fall', name='semester_enum'), comment="学期")
    student_count = Column(Integer, default=0, comment="选课学生人数")
    max_students = Column(Integer, default=100, comment="最大学生人数")
    teacher_count = Column(Integer, default=0, comment="授课教师人数")
    credits = Column(Numeric(3, 1), default=0, comment="学分")
    description = Column(Text, comment="课程描述")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    school = relationship("School", back_populates="courses")
    course_teachers = relationship("CourseTeacher", back_populates="course", cascade="all, delete-orphan")
    course_students = relationship("CourseStudent", back_populates="course", cascade="all, delete-orphan")
    groups = relationship("CourseGroup", back_populates="course", cascade="all, delete-orphan")
    group_members = relationship("GroupMember", back_populates="course", cascade="all, delete-orphan")
    device_authorizations = relationship("CourseDeviceAuthorization", back_populates="course", cascade="all, delete-orphan")


class CourseTeacher(Base):
    """教师-课程关联模型（多对多关系）"""
    __tablename__ = "aiot_course_teachers"
    
    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=False, index=True, comment="课程ID")
    teacher_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, index=True, comment="教师ID")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    course = relationship("Course", back_populates="course_teachers")
    teacher = relationship("User", back_populates="teaching_courses")


class CourseStudent(Base):
    """学生-课程关联模型（多对多关系 - 选课记录）"""
    __tablename__ = "aiot_course_students"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=False, index=True, comment="课程ID")
    student_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, index=True, comment="学生ID")
    enrolled_at = Column(DateTime, default=get_beijing_time_naive, comment="选课时间")
    status = Column(SQLEnum('enrolled', 'completed', 'dropped', name='course_status_enum'), default='enrolled', index=True, comment="状态")
    score = Column(Numeric(5, 2), comment="成绩")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    course = relationship("Course", back_populates="course_students")
    student = relationship("User", back_populates="enrolled_courses")


class CourseGroup(Base):
    """课程分组模型"""
    __tablename__ = "aiot_course_groups"
    
    id = Column(Integer, primary_key=True, index=True, comment="小组ID")
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid_lib.uuid4()), comment='UUID，用于外部API访问')
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=False, index=True, comment="所属课程ID")
    school_id = Column(Integer, ForeignKey("core_schools.id"), nullable=False, index=True, comment="所属学校ID")
    group_name = Column(String(100), nullable=False, comment="小组名称")
    group_number = Column(Integer, comment="小组编号")
    leader_id = Column(Integer, ForeignKey("core_users.id"), nullable=True, index=True, comment="组长ID")
    leader_name = Column(String(100), comment="组长姓名")
    member_count = Column(Integer, default=0, comment="成员人数")
    description = Column(Text, comment="小组描述")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    course = relationship("Course", back_populates="groups")
    school = relationship("School", back_populates="course_groups")
    leader = relationship("User", foreign_keys=[leader_id], back_populates="led_course_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """小组成员模型"""
    __tablename__ = "aiot_group_members"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    group_id = Column(Integer, ForeignKey("aiot_course_groups.id"), nullable=False, index=True, comment="小组ID")
    course_id = Column(Integer, ForeignKey("aiot_courses.id"), nullable=False, index=True, comment="课程ID")
    school_id = Column(Integer, ForeignKey("core_schools.id"), nullable=False, index=True, comment="学校ID")
    student_id = Column(Integer, ForeignKey("core_users.id"), nullable=False, index=True, comment="学生ID")
    student_name = Column(String(100), comment="学生姓名")
    student_number = Column(String(50), comment="学号")
    is_leader = Column(Boolean, default=False, index=True, comment="是否为组长")
    joined_at = Column(DateTime, default=get_beijing_time_naive, comment="加入时间")
    left_at = Column(DateTime, nullable=True, comment="离开时间")
    created_at = Column(DateTime, default=get_beijing_time_naive, comment="创建时间")
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, comment="更新时间")
    
    # 关系
    group = relationship("CourseGroup", back_populates="members")
    course = relationship("Course", back_populates="group_members")
    school = relationship("School", back_populates="group_members")
    student = relationship("User", back_populates="group_memberships")
