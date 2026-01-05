from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    planning = 'planning'
    in_progress = 'in-progress'
    review = 'review'
    completed = 'completed'

# --- Course Schemas ---
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    duration: Optional[str] = None
    difficulty: Optional[str] = None

class Course(CourseBase):
    id: int
    uuid: str
    
    class Config:
        from_attributes = True

# --- Project Schemas ---

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: int
    group_id: Optional[int] = None
    repo_url: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.planning
    progress: Optional[int] = 0

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress: Optional[int] = None
    repo_url: Optional[str] = None

class ProjectInDBBase(ProjectBase):
    id: int
    uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Project(ProjectInDBBase):
    course: Optional[Course] = None

class ProjectList(BaseModel):
    total: int
    items: List[Project]

# --- Unit Schemas ---
class UnitBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0
    status: Optional[str] = 'locked'
    open_from: Optional[datetime] = None  # 单元开放时间
    learning_guide: Optional[Any] = None  # 支持 dict 或 list 类型

class UnitCreate(UnitBase):
    course_uuid: str

class UnitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None
    open_from: Optional[datetime] = None  # 单元开放时间
    learning_guide: Optional[Any] = None  # 支持 dict 或 list 类型

class Unit(UnitBase):
    id: int
    uuid: str
    course_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- Resource Schemas ---
class ResourceBase(BaseModel):
    type: str  # 'video', 'document', 'link'
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    duration: Optional[int] = None
    order: Optional[int] = 0
    video_id: Optional[str] = None
    video_cover_url: Optional[str] = None

class ResourceCreate(ResourceBase):
    unit_id: Optional[int] = None
    unit_uuid: Optional[str] = None

class ResourceUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    duration: Optional[int] = None
    order: Optional[int] = None
    video_id: Optional[str] = None
    video_cover_url: Optional[str] = None

class Resource(ResourceBase):
    id: int
    uuid: str
    unit_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: Optional[str] = 'analysis'  # 'analysis', 'coding', 'design', 'deployment'
    difficulty: Optional[str] = 'easy'  # 'easy', 'medium', 'hard'
    estimated_time: Optional[str] = None
    order: Optional[int] = 0  # 顺序（与资源统一排序）
    requirements: Optional[Any] = None  # 支持 dict 或 list 类型
    prerequisites: Optional[Any] = None  # 支持 dict 或 list 类型

class TaskCreate(TaskBase):
    unit_id: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_time: Optional[str] = None
    order: Optional[int] = None  # 顺序（与资源统一排序）
    requirements: Optional[Any] = None  # 支持 dict 或 list 类型
    prerequisites: Optional[Any] = None  # 支持 dict 或 list 类型

class Task(TaskBase):
    id: int
    uuid: str
    unit_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- School Course Schemas ---
class SchoolCourseStatus(str, Enum):
    """学校课程状态"""
    active = 'active'
    inactive = 'inactive'
    archived = 'archived'

class SchoolCourseBase(BaseModel):
    """学校课程基础模型"""
    school_id: int
    course_id: int
    status: Optional[SchoolCourseStatus] = SchoolCourseStatus.active
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_students: Optional[int] = None
    remarks: Optional[str] = None

class SchoolCourseCreate(SchoolCourseBase):
    """创建学校课程分配"""
    pass

class SchoolCourseUpdate(BaseModel):
    """更新学校课程分配"""
    status: Optional[SchoolCourseStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_students: Optional[int] = None
    remarks: Optional[str] = None

class SchoolCourse(SchoolCourseBase):
    """学校课程返回模型"""
    id: int
    uuid: str
    assigned_by: Optional[int] = None
    assigned_at: datetime
    current_students: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SchoolCourseWithDetails(SchoolCourse):
    """学校课程详情（包含课程信息）"""
    course: Optional[Course] = None

# --- Learning Progress Schemas ---
class LearningProgressTrack(BaseModel):
    """学习进度追踪请求"""
    course_uuid: str
    unit_uuid: Optional[str] = None
    resource_uuid: Optional[str] = None
    task_uuid: Optional[str] = None
    progress_type: str = 'resource_view'  # video_watch, document_read, task_submit, etc.
    progress_value: int = 0  # 0-100
    time_spent: int = 0  # 秒
    metadata: Optional[dict] = None


# --- Template School Permission Schemas ---
class TemplateSchoolPermissionBase(BaseModel):
    """课程模板学校开放权限基础模型"""
    template_id: int
    school_id: int
    is_active: Optional[int] = 1
    can_customize: Optional[int] = 1
    max_instances: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    remarks: Optional[str] = None


class TemplateSchoolPermissionCreate(TemplateSchoolPermissionBase):
    """创建模板开放权限"""
    pass


class TemplateSchoolPermissionUpdate(BaseModel):
    """更新模板开放权限"""
    is_active: Optional[int] = None
    can_customize: Optional[int] = None
    max_instances: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    remarks: Optional[str] = None


class TemplateSchoolPermission(TemplateSchoolPermissionBase):
    """模板开放权限返回模型"""
    id: int
    uuid: str
    current_instances: int
    granted_by: int
    granted_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateSchoolPermissionWithDetails(TemplateSchoolPermission):
    """模板开放权限详情（包含模板和学校信息）"""
    template: Optional[dict] = None
    school: Optional[dict] = None


# --- Course Template Schemas ---
class CourseTemplateBase(BaseModel):
    """课程模板基础模型"""
    template_code: str
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    duration: Optional[str] = None
    difficulty: Optional[str] = 'beginner'
    category: Optional[str] = None
    version: Optional[str] = '1.0.0'
    is_public: Optional[int] = 1


class CourseTemplateCreate(CourseTemplateBase):
    """创建课程模板"""
    pass


class CourseTemplateUpdate(BaseModel):
    """更新课程模板"""
    template_code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    duration: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    is_public: Optional[int] = None


class CourseTemplate(CourseTemplateBase):
    """课程模板返回模型"""
    id: int
    uuid: str
    creator_id: Optional[int] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# --- Unit Template Schemas ---
class UnitTemplateBase(BaseModel):
    """单元模板基础模型"""
    template_code: str
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0
    learning_objectives: Optional[Any] = None
    key_concepts: Optional[Any] = None
    estimated_duration: Optional[str] = None


class UnitTemplateCreate(UnitTemplateBase):
    """创建单元模板"""
    course_template_uuid: str


class UnitTemplateUpdate(BaseModel):
    """更新单元模板"""
    template_code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    learning_objectives: Optional[Any] = None
    key_concepts: Optional[Any] = None
    estimated_duration: Optional[str] = None


class UnitTemplate(UnitTemplateBase):
    """单元模板返回模型"""
    id: int
    uuid: str
    course_template_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# --- Resource Template Schemas ---
class ResourceTemplateBase(BaseModel):
    """资源模板基础模型"""
    template_code: str
    type: str  # 'video', 'document', 'link', 'interactive', 'quiz'
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0
    url: Optional[str] = None
    content: Optional[str] = None
    video_id: Optional[str] = None
    video_cover_url: Optional[str] = None
    duration: Optional[int] = None
    default_max_views: Optional[int] = None
    is_preview_allowed: Optional[int] = 1
    meta_data: Optional[Any] = None


class ResourceTemplateCreate(ResourceTemplateBase):
    """创建资源模板"""
    unit_template_uuid: str


class ResourceTemplateUpdate(BaseModel):
    """更新资源模板"""
    template_code: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    url: Optional[str] = None
    content: Optional[str] = None
    video_id: Optional[str] = None
    video_cover_url: Optional[str] = None
    duration: Optional[int] = None
    default_max_views: Optional[int] = None
    is_preview_allowed: Optional[int] = None
    meta_data: Optional[Any] = None


class ResourceTemplate(ResourceTemplateBase):
    """资源模板返回模型"""
    id: int
    uuid: str
    unit_template_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# --- Task Template Schemas ---
class TaskTemplateBase(BaseModel):
    """任务模板基础模型"""
    template_code: str
    title: str
    description: Optional[str] = None
    type: Optional[str] = 'analysis'  # 'analysis', 'coding', 'design', 'deployment', 'research', 'presentation'
    difficulty: Optional[str] = 'easy'  # 'easy', 'medium', 'hard'
    order: Optional[int] = 0
    requirements: Optional[Any] = None
    deliverables: Optional[Any] = None
    evaluation_criteria: Optional[Any] = None
    estimated_time: Optional[str] = None
    estimated_hours: Optional[int] = None
    prerequisites: Optional[Any] = None
    required_resources: Optional[Any] = None
    hints: Optional[Any] = None
    reference_materials: Optional[Any] = None
    meta_data: Optional[Any] = None


class TaskTemplateCreate(TaskTemplateBase):
    """创建任务模板"""
    unit_template_uuid: str


class TaskTemplateUpdate(BaseModel):
    """更新任务模板"""
    template_code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    order: Optional[int] = None
    requirements: Optional[Any] = None
    deliverables: Optional[Any] = None
    evaluation_criteria: Optional[Any] = None
    estimated_time: Optional[str] = None
    estimated_hours: Optional[int] = None
    prerequisites: Optional[Any] = None
    required_resources: Optional[Any] = None
    hints: Optional[Any] = None
    reference_materials: Optional[Any] = None
    meta_data: Optional[Any] = None


class TaskTemplate(TaskTemplateBase):
    """任务模板返回模型"""
    id: int
    uuid: str
    unit_template_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# --- Course Template with Details ---
class CourseTemplateWithDetails(CourseTemplate):
    """课程模板详情（包含单元、资源、任务）"""
    units: Optional[List['UnitTemplateWithDetails']] = None


class UnitTemplateWithDetails(UnitTemplate):
    """单元模板详情（包含资源和任务）"""
    resources: Optional[List[ResourceTemplate]] = None
    tasks: Optional[List[TaskTemplate]] = None


# --- Task Attachment Schemas ---
class TaskAttachmentBase(BaseModel):
    """作业附件基础Schema"""
    filename: str
    file_type: str  # word/pdf
    file_ext: str  # .doc/.docx/.pdf
    file_size: int  # 字节


class TaskAttachmentCreate(TaskAttachmentBase):
    """创建作业附件"""
    progress_id: int
    stored_filename: str
    file_url: str


class TaskAttachment(TaskAttachmentBase):
    """作业附件响应"""
    id: int
    uuid: str
    progress_id: int
    user_id: int
    stored_filename: str
    file_url: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
