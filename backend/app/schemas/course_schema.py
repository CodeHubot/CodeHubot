"""
课程管理模块的Schema定义
包含：课程、选课、教师-课程关联、分组的请求和响应Schema
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ============================================================================
# 课程 Schemas
# ============================================================================

class CourseCreate(BaseModel):
    """创建课程Schema"""
    school_id: int = Field(..., description="所属学校ID")
    course_name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    course_code: Optional[str] = Field(None, max_length=20, description="课程编号")
    academic_year: Optional[str] = Field(None, max_length=20, description="学年")
    semester: Optional[str] = Field(None, description="学期：spring/fall")
    max_students: int = Field(100, ge=1, le=500, description="最大学生人数")
    credits: Optional[Decimal] = Field(0, ge=0, le=10, description="学分")
    description: Optional[str] = Field(None, description="课程描述")
    
    @validator('semester')
    def validate_semester(cls, v):
        if v and v not in ['spring', 'fall']:
            raise ValueError('学期必须是spring或fall')
        return v


class CourseUpdate(BaseModel):
    """更新课程Schema"""
    course_name: Optional[str] = Field(None, min_length=1, max_length=100, description="课程名称")
    course_code: Optional[str] = Field(None, max_length=20, description="课程编号")
    academic_year: Optional[str] = Field(None, max_length=20, description="学年")
    semester: Optional[str] = Field(None, description="学期：spring/fall")
    max_students: Optional[int] = Field(None, ge=1, le=500, description="最大学生人数")
    credits: Optional[Decimal] = Field(None, ge=0, le=10, description="学分")
    description: Optional[str] = Field(None, description="课程描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('semester')
    def validate_semester(cls, v):
        if v and v not in ['spring', 'fall']:
            raise ValueError('学期必须是spring或fall')
        return v


class CourseResponse(BaseModel):
    """课程响应Schema"""
    id: int
    uuid: str
    school_id: int
    course_name: str
    course_code: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    student_count: int = 0
    max_students: int = 100
    teacher_count: int = 0
    teachers: List[dict] = []  # 任课教师列表
    credits: Optional[Decimal] = 0
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """课程列表响应Schema（简化版）"""
    id: int
    uuid: str
    school_id: int
    course_name: str
    course_code: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    student_count: int = 0
    max_students: int = 100
    teacher_count: int = 0
    teachers: List[dict] = []  # 任课教师列表
    device_groups: List[dict] = []  # 授权的设备组列表
    total_devices: int = 0  # 总设备数
    group_count: int = 0  # 学生分组数量
    credits: Optional[Decimal] = 0
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseStatistics(BaseModel):
    """课程统计Schema"""
    total_courses: int
    active_courses: int
    total_students: int
    total_teachers: int
    avg_students_per_course: float


# ============================================================================
# 选课 Schemas（新增）
# ============================================================================

class CourseEnrollRequest(BaseModel):
    """学生选课请求Schema"""
    student_id: int = Field(..., description="学生ID")


class CourseEnrollBatchRequest(BaseModel):
    """批量选课请求Schema"""
    student_ids: List[int] = Field(..., description="学生ID列表")


class CourseEnrollmentUpdate(BaseModel):
    """更新选课状态Schema"""
    status: Optional[str] = Field(None, description="状态：enrolled/completed/dropped")
    score: Optional[Decimal] = Field(None, ge=0, le=100, description="成绩")
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['enrolled', 'completed', 'dropped']:
            raise ValueError('状态必须是enrolled、completed或dropped')
        return v


class CourseEnrollmentResponse(BaseModel):
    """选课记录响应Schema"""
    id: int
    course_id: int
    course_name: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    enrolled_at: datetime
    status: str
    score: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseEnrollmentListResponse(BaseModel):
    """选课列表响应Schema（简化版）"""
    id: int
    course_id: int
    course_name: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    status: str
    score: Optional[Decimal] = None
    enrolled_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 教师-课程关联 Schemas
# ============================================================================

class CourseTeacherAdd(BaseModel):
    """添加课程教师Schema"""
    teacher_id: int = Field(..., description="教师ID")


class CourseTeacherBatchAdd(BaseModel):
    """批量添加课程教师Schema"""
    teacher_ids: List[int] = Field(..., description="教师ID列表")


class CourseTeacherResponse(BaseModel):
    """课程教师响应Schema"""
    id: int
    course_id: int
    teacher_id: int
    teacher_name: Optional[str] = None
    teacher_username: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseTeacherListResponse(BaseModel):
    """课程教师列表响应Schema"""
    id: int
    teacher_id: int
    teacher_name: Optional[str] = None
    teacher_username: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# 课程分组 Schemas
# ============================================================================

class CourseGroupCreate(BaseModel):
    """创建课程分组Schema"""
    course_id: int = Field(..., description="所属课程ID")
    group_name: str = Field(..., min_length=1, max_length=100, description="小组名称")
    group_number: Optional[int] = Field(None, description="小组编号")
    leader_id: Optional[int] = Field(None, description="组长ID")
    description: Optional[str] = Field(None, description="小组描述")


class CourseGroupUpdate(BaseModel):
    """更新课程分组Schema"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=100, description="小组名称")
    group_number: Optional[int] = Field(None, description="小组编号")
    leader_id: Optional[int] = Field(None, description="组长ID")
    description: Optional[str] = Field(None, description="小组描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class CourseGroupResponse(BaseModel):
    """课程分组响应Schema"""
    id: int
    uuid: str
    course_id: int
    school_id: int
    group_name: str
    group_number: Optional[int] = None
    leader_id: Optional[int] = None
    leader_name: Optional[str] = None
    member_count: int = 0
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CourseGroupListResponse(BaseModel):
    """课程分组列表响应Schema"""
    id: int
    uuid: str
    course_id: int
    group_name: str
    group_number: Optional[int] = None
    leader_name: Optional[str] = None
    member_count: int = 0
    is_active: bool = True
    
    class Config:
        from_attributes = True


# ============================================================================
# 分组成员 Schemas
# ============================================================================

class GroupMemberAdd(BaseModel):
    """添加分组成员Schema"""
    student_id: int = Field(..., description="学生ID")
    is_leader: bool = Field(False, description="是否为组长")


class GroupMemberBatchAdd(BaseModel):
    """批量添加分组成员Schema"""
    student_ids: List[int] = Field(..., description="学生ID列表")


class GroupMemberResponse(BaseModel):
    """分组成员响应Schema"""
    id: int
    group_id: int
    course_id: int
    student_id: int
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    is_leader: bool = False
    joined_at: datetime
    
    class Config:
        from_attributes = True


class GroupMemberListResponse(BaseModel):
    """分组成员列表响应Schema"""
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    is_leader: bool = False
    joined_at: datetime
    
    class Config:
        from_attributes = True
