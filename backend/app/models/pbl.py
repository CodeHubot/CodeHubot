from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime, JSON, DECIMAL, BigInteger, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..db.base_class import Base
from ..utils.timezone import get_beijing_time_naive

def generate_uuid():
    return str(uuid.uuid4())

class PBLCourse(Base):
    __tablename__ = "pbl_courses"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    template_id = Column(BigInteger)  # Foreign Key to pbl_course_templates
    template_version = Column(String(20))
    permission_id = Column(BigInteger)  # Foreign Key to pbl_template_school_permissions
    is_customized = Column(Integer, default=0)
    sync_with_template = Column(Integer, default=1)
    class_id = Column(Integer, ForeignKey("pbl_classes.id"))  # 关联班级
    class_name = Column(String(100))  # 冗余字段
    title = Column(String(200), nullable=False)
    description = Column(Text)
    cover_image = Column(String(255))
    duration = Column(String(50))
    difficulty = Column(Enum('beginner', 'intermediate', 'advanced'), default='beginner')
    status = Column(Enum('draft', 'published', 'archived'), default='draft')
    creator_id = Column(Integer)  # Foreign Key to core_users
    teacher_id = Column(Integer)  # 授课教师ID（Foreign Key to core_users）
    teacher_name = Column(String(100))  # 授课教师姓名（冗余字段）
    school_id = Column(Integer)   # Foreign Key to core_schools
    start_date = Column(Date)  # 课程开始时间
    end_date = Column(Date)  # 课程结束时间
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    units = relationship("PBLUnit", back_populates="course", cascade="all, delete-orphan")
    projects = relationship("PBLProject", back_populates="course")


class PBLCourseTemplate(Base):
    """课程模板表"""
    __tablename__ = "pbl_course_templates"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    template_code = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    cover_image = Column(String(500))
    duration = Column(String(50))
    difficulty = Column(Enum('beginner', 'intermediate', 'advanced'), default='beginner')
    category = Column(String(50))
    version = Column(String(20), default='1.0.0')
    is_public = Column(Integer, default=1)
    creator_id = Column(Integer)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    units = relationship("PBLUnitTemplate", back_populates="course_template", cascade="all, delete-orphan")


class PBLUnitTemplate(Base):
    """单元模板表"""
    __tablename__ = "pbl_unit_templates"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    template_code = Column(String(50), nullable=False)
    course_template_id = Column(BigInteger, ForeignKey("pbl_course_templates.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    learning_objectives = Column(JSON)
    key_concepts = Column(JSON)
    estimated_duration = Column(String(50))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    course_template = relationship("PBLCourseTemplate", back_populates="units")
    resources = relationship("PBLResourceTemplate", back_populates="unit_template", cascade="all, delete-orphan")
    tasks = relationship("PBLTaskTemplate", back_populates="unit_template", cascade="all, delete-orphan")


class PBLResourceTemplate(Base):
    """资源模板表"""
    __tablename__ = "pbl_resource_templates"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    template_code = Column(String(50), nullable=False)
    unit_template_id = Column(BigInteger, ForeignKey("pbl_unit_templates.id"), nullable=False)
    type = Column(Enum('video', 'document', 'link', 'interactive', 'quiz'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    url = Column(String(500))
    content = Column(Text)
    video_id = Column(String(100))
    video_cover_url = Column(String(500))
    duration = Column(Integer)
    default_max_views = Column(Integer, default=None)
    is_preview_allowed = Column(Integer, default=1)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    unit_template = relationship("PBLUnitTemplate", back_populates="resources")


class PBLTaskTemplate(Base):
    """任务模板表"""
    __tablename__ = "pbl_task_templates"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    template_code = Column(String(50), nullable=False)
    unit_template_id = Column(BigInteger, ForeignKey("pbl_unit_templates.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(Enum('analysis', 'coding', 'design', 'deployment', 'research', 'presentation'), default='analysis')
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy')
    order = Column(Integer, default=0)
    requirements = Column(JSON)
    deliverables = Column(JSON)
    evaluation_criteria = Column(JSON)
    estimated_time = Column(String(50))
    estimated_hours = Column(Integer)
    prerequisites = Column(JSON)
    required_resources = Column(JSON)
    hints = Column(JSON)
    reference_materials = Column(JSON)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    unit_template = relationship("PBLUnitTemplate", back_populates="tasks")


class PBLUnit(Base):
    __tablename__ = "pbl_units"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    course_id = Column(Integer, ForeignKey("pbl_courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    status = Column(Enum('locked', 'available', 'completed'), default='locked')
    open_from = Column(DateTime, default=None, comment='单元开放时间（NULL表示立即开放）')
    learning_guide = Column(JSON)
    estimated_duration = Column(String(50))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    course = relationship("PBLCourse", back_populates="units")
    resources = relationship("PBLResource", back_populates="unit", cascade="all, delete-orphan")
    tasks = relationship("PBLTask", back_populates="unit", cascade="all, delete-orphan")


class PBLResource(Base):
    __tablename__ = "pbl_resources"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    unit_id = Column(Integer, ForeignKey("pbl_units.id"), nullable=False)
    type = Column(Enum('video', 'document', 'link'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    content = Column(Text) # longtext
    duration = Column(Integer)
    order = Column(Integer, default=0)
    video_id = Column(String(100))
    video_cover_url = Column(String(255))
    max_views = Column(Integer, default=None, comment='最大观看次数（NULL表示不限制，0表示禁止观看，大于0表示限制次数）')
    valid_from = Column(DateTime, default=None, comment='全局有效开始时间（NULL表示立即生效）')
    valid_until = Column(DateTime, default=None, comment='全局有效结束时间（NULL表示永久有效）')
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    unit = relationship("PBLUnit", back_populates="resources")


class PBLTask(Base):
    __tablename__ = "pbl_tasks"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    unit_id = Column(Integer, ForeignKey("pbl_units.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, default=None, comment='任务开始时间')
    deadline = Column(DateTime, default=None, comment='任务截止时间')
    is_required = Column(Integer, default=1, comment='是否必做：1-必做，0-选做')
    publish_status = Column(Enum('draft', 'published'), default='draft', comment='发布状态：draft-草稿，published-已发布')
    type = Column(Enum('analysis', 'coding', 'design', 'deployment'), default='analysis')
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy')
    estimated_time = Column(String(50))
    order = Column(Integer, default=0, nullable=False)  # 顺序（与资源统一排序）
    requirements = Column(JSON)
    prerequisites = Column(JSON)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    unit = relationship("PBLUnit", back_populates="tasks")
    progress = relationship("PBLTaskProgress", back_populates="task")


class PBLProject(Base):
    __tablename__ = "pbl_projects"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    group_id = Column(Integer) # Foreign Key to pbl_groups
    course_id = Column(Integer, ForeignKey("pbl_courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum('planning', 'in-progress', 'review', 'completed'), default='planning')
    progress = Column(Integer, default=0)
    repo_url = Column(String(500))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    course = relationship("PBLCourse", back_populates="projects")


class PBLTaskProgress(Base):
    __tablename__ = "pbl_task_progress"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("pbl_tasks.id"), nullable=False)
    user_id = Column(Integer, nullable=False) # Foreign Key to core_users
    status = Column(Enum('pending', 'in-progress', 'blocked', 'review', 'completed'), default='pending')
    progress = Column(Integer, default=0)
    submission = Column(JSON)
    submitted_at = Column(DateTime, default=None, comment='提交时间')
    score = Column(Integer)
    feedback = Column(Text)
    graded_by = Column(Integer) # Foreign Key to core_users
    graded_at = Column(DateTime)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    task = relationship("PBLTask", back_populates="progress")
    attachments = relationship("PBLTaskAttachment", back_populates="progress", cascade="all, delete-orphan")


class PBLTaskAttachment(Base):
    """作业附件表"""
    __tablename__ = "pbl_task_attachments"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    progress_id = Column(BigInteger, ForeignKey("pbl_task_progress.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    filename = Column(String(255), nullable=False, comment='原始文件名')
    stored_filename = Column(String(255), nullable=False, comment='存储文件名')
    file_type = Column(String(50), nullable=False, comment='文件类型(word/pdf)')
    file_ext = Column(String(20), nullable=False, comment='文件扩展名')
    file_size = Column(BigInteger, nullable=False, comment='文件大小(字节)')
    file_url = Column(String(500), nullable=False, comment='文件访问路径')
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)

    progress = relationship("PBLTaskProgress", back_populates="attachments")


class PBLSchoolCourse(Base):
    """学校课程分配表：平台管理员为学校分配课程"""
    __tablename__ = "pbl_school_courses"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    school_id = Column(Integer, nullable=False)  # Foreign Key to core_schools
    course_id = Column(BigInteger, ForeignKey("pbl_courses.id"), nullable=False)
    assigned_by = Column(Integer)  # Foreign Key to core_users (平台管理员)
    assigned_at = Column(DateTime, default=get_beijing_time_naive)
    status = Column(Enum('active', 'inactive', 'archived'), default='active')
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    max_students = Column(Integer)  # NULL表示无限制
    current_students = Column(Integer, default=0)
    remarks = Column(Text)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLProjectOutput(Base):
    __tablename__ = "pbl_project_outputs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    project_id = Column(Integer, ForeignKey("pbl_projects.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("pbl_tasks.id"))
    user_id = Column(Integer, nullable=False) # Foreign Key to core_users
    group_id = Column(Integer) # Foreign Key to pbl_groups
    output_type = Column(Enum('report', 'code', 'design', 'video', 'presentation', 'model', 'dataset', 'other'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    file_url = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    repo_url = Column(String(500))
    demo_url = Column(String(500))
    thumbnail = Column(String(500))
    meta_data = Column(JSON)
    is_public = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLClass(Base):
    __tablename__ = "pbl_classes"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    school_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    class_type = Column(Enum('club', 'project', 'interest', 'competition', 'regular'), default='regular')
    description = Column(Text)
    grade = Column(String(50))
    academic_year = Column(String(20))
    class_teacher_id = Column(Integer)
    max_students = Column(Integer, default=50)
    current_members = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    is_open = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLClassMember(Base):
    """班级成员表（多对多关系）"""
    __tablename__ = "pbl_class_members"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("pbl_classes.id"), nullable=False)
    student_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    role = Column(Enum('member', 'leader', 'deputy'), default='member')
    joined_at = Column(DateTime, default=get_beijing_time_naive)
    left_at = Column(DateTime)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLClassTeacher(Base):
    """班级教师关联表（多对多关系）"""
    __tablename__ = "pbl_class_teachers"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("pbl_classes.id"), nullable=False)
    teacher_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    role = Column(Enum('main', 'assistant'), default='assistant')  # 教师角色：main-主讲教师，assistant-助教
    subject = Column(String(50))  # 教师在该班级教授的科目
    is_primary = Column(Integer, default=0)  # 是否为班主任
    added_at = Column(DateTime, default=get_beijing_time_naive)  # 添加时间
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLCourseTeacher(Base):
    """课程教师关联表（多对多关系）"""
    __tablename__ = "pbl_course_teachers"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(BigInteger, ForeignKey("pbl_courses.id"), nullable=False)
    teacher_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    subject = Column(String(50))  # 教师在该课程教授的科目
    is_primary = Column(Integer, default=0)  # 是否为主讲教师
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class ChannelSchoolRelation(Base):
    """渠道商与学校关联表"""
    __tablename__ = "pbl_channel_school_relations"

    id = Column(Integer, primary_key=True, index=True)
    channel_partner_id = Column(Integer, nullable=False)  # Foreign Key to core_users (role='channel_partner')
    school_id = Column(Integer, nullable=False)  # Foreign Key to core_schools
    assigned_at = Column(DateTime, default=get_beijing_time_naive)
    is_active = Column(Integer, default=1)
    remarks = Column(String(500))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLClassCourse(Base):
    """班级课程分配表"""
    __tablename__ = "pbl_class_courses"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    class_id = Column(Integer, ForeignKey("pbl_classes.id"), nullable=False)
    course_id = Column(BigInteger, ForeignKey("pbl_courses.id"), nullable=False)
    auto_enroll = Column(Integer, default=1)  # 是否自动为班级成员选课
    assigned_by = Column(Integer, nullable=False)  # Foreign Key to core_users
    assigned_at = Column(DateTime, default=get_beijing_time_naive)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(Enum('active', 'inactive', 'completed'), default='active')
    remarks = Column(String(500))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLGroup(Base):
    __tablename__ = "pbl_groups"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    class_id = Column(Integer, ForeignKey("pbl_classes.id"))
    course_id = Column(Integer, ForeignKey("pbl_courses.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    leader_id = Column(Integer)
    max_members = Column(Integer, default=6)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLGroupMember(Base):
    __tablename__ = "pbl_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("pbl_groups.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    role = Column(Enum('member', 'leader', 'deputy_leader'), default='member')
    joined_at = Column(DateTime, default=get_beijing_time_naive)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLAssessment(Base):
    __tablename__ = "pbl_assessments"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    assessor_id = Column(Integer, nullable=False)
    assessor_role = Column(Enum('teacher', 'student', 'expert', 'self'), nullable=False)
    target_type = Column(Enum('project', 'task', 'output', 'student'), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    student_id = Column(Integer, nullable=False)
    group_id = Column(Integer)
    assessment_type = Column(Enum('formative', 'summative'), default='formative')
    dimensions = Column(JSON, nullable=False)
    total_score = Column(DECIMAL(5, 2))
    max_score = Column(DECIMAL(5, 2), default=100.00)
    comments = Column(Text)
    strengths = Column(Text)
    improvements = Column(Text)
    tags = Column(JSON)
    is_public = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLAssessmentTemplate(Base):
    __tablename__ = "pbl_assessment_templates"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    applicable_to = Column(Enum('project', 'task', 'output'), nullable=False)
    grade_level = Column(String(50))
    dimensions = Column(JSON, nullable=False)
    created_by = Column(Integer)
    is_system = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLDataset(Base):
    __tablename__ = "pbl_datasets"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    data_type = Column(Enum('image', 'text', 'audio', 'video', 'tabular', 'mixed'), nullable=False)
    category = Column(String(50))
    file_url = Column(String(500))
    file_size = Column(BigInteger)
    sample_count = Column(Integer)
    class_count = Column(Integer)
    classes = Column(JSON)
    is_labeled = Column(Integer, default=0)
    label_format = Column(String(50))
    split_ratio = Column(JSON)
    grade_level = Column(String(50))
    applicable_projects = Column(JSON)
    source = Column(String(200))
    license = Column(String(100))
    preview_images = Column(JSON)
    download_count = Column(Integer, default=0)
    creator_id = Column(Integer)
    school_id = Column(Integer)
    is_public = Column(Integer, default=1)
    quality_score = Column(DECIMAL(3, 2))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLEthicsCase(Base):
    __tablename__ = "pbl_ethics_cases"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text)
    grade_level = Column(String(50))
    ethics_topics = Column(JSON, nullable=False)
    difficulty = Column(Enum('basic', 'intermediate', 'advanced'), default='basic')
    discussion_questions = Column(JSON)
    reference_links = Column(JSON)
    cover_image = Column(String(255))
    author = Column(String(100))
    source = Column(String(200))
    is_published = Column(Integer, default=1)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLEthicsActivity(Base):
    __tablename__ = "pbl_ethics_activities"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    case_id = Column(BigInteger, ForeignKey("pbl_ethics_cases.id"))
    course_id = Column(BigInteger, ForeignKey("pbl_courses.id"))
    unit_id = Column(BigInteger, ForeignKey("pbl_units.id"))
    activity_type = Column(Enum('debate', 'case_analysis', 'role_play', 'discussion', 'reflection'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    participants = Column(JSON)
    group_id = Column(Integer)
    facilitator_id = Column(Integer)
    status = Column(Enum('planned', 'ongoing', 'completed', 'cancelled'), default='planned')
    discussion_records = Column(JSON)
    conclusions = Column(Text)
    reflections = Column(JSON)
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLExternalExpert(Base):
    __tablename__ = "pbl_external_experts"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    organization = Column(String(200))
    title = Column(String(100))
    expertise_areas = Column(JSON)
    bio = Column(Text)
    email = Column(String(255))
    phone = Column(String(20))
    avatar = Column(String(255))
    is_active = Column(Integer, default=1)
    participated_projects = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3, 2))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLSocialActivity(Base):
    __tablename__ = "pbl_social_activities"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    activity_type = Column(Enum('company_visit', 'lab_tour', 'workshop', 'competition', 'exhibition', 'volunteer', 'lecture'), nullable=False)
    organizer = Column(String(200))
    partner_organization = Column(String(200))
    location = Column(String(500))
    scheduled_at = Column(DateTime)
    duration = Column(Integer)
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    participants = Column(JSON)
    facilitators = Column(JSON)
    status = Column(Enum('planned', 'registration', 'ongoing', 'completed', 'cancelled'), default='planned')
    photos = Column(JSON)
    summary = Column(Text)
    feedback = Column(JSON)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLStudentPortfolio(Base):
    __tablename__ = "pbl_student_portfolios"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    student_id = Column(Integer, nullable=False)
    school_year = Column(String(20), nullable=False)
    grade_level = Column(String(50), nullable=False)
    completed_projects = Column(JSON)
    achievements = Column(JSON)
    skill_assessment = Column(JSON)
    growth_trajectory = Column(JSON)
    highlights = Column(JSON)
    total_learning_hours = Column(Integer, default=0)
    projects_count = Column(Integer, default=0)
    avg_score = Column(DECIMAL(5, 2))
    teacher_comments = Column(Text)
    self_reflection = Column(Text)
    parent_feedback = Column(Text)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLAchievement(Base):
    __tablename__ = "pbl_achievements"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(255))
    condition = Column(JSON)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLUserAchievement(Base):
    __tablename__ = "pbl_user_achievements"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    achievement_id = Column(BigInteger, ForeignKey("pbl_achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=get_beijing_time_naive)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)


class PBLLearningProgress(Base):
    __tablename__ = "pbl_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    course_id = Column(BigInteger, ForeignKey("pbl_courses.id"), nullable=False)
    unit_id = Column(BigInteger, ForeignKey("pbl_units.id"))
    resource_id = Column(BigInteger, ForeignKey("pbl_resources.id"))
    task_id = Column(BigInteger, ForeignKey("pbl_tasks.id"))
    progress_type = Column(Enum('resource_view', 'video_watch', 'document_read', 'task_submit', 'unit_complete'), nullable=False)
    progress_value = Column(Integer, default=0)
    status = Column(Enum('in_progress', 'completed'), default='in_progress')
    completed_at = Column(DateTime)
    time_spent = Column(Integer, default=0)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLVideoWatchRecord(Base):
    """视频观看记录表"""
    __tablename__ = "pbl_video_watch_records"

    id = Column(BigInteger, primary_key=True, index=True)
    resource_id = Column(BigInteger, ForeignKey("pbl_resources.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    watch_time = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    duration = Column(Integer, default=0, comment='观看时长（秒）')
    completed = Column(Integer, default=0, comment='是否观看完成')
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)


class PBLVideoUserPermission(Base):
    """视频用户权限表 - 个性化观看次数和有效期设置"""
    __tablename__ = "pbl_video_user_permissions"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    resource_id = Column(BigInteger, ForeignKey("pbl_resources.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    max_views = Column(Integer, default=None, comment='该学生对该视频的最大观看次数')
    valid_from = Column(DateTime, default=None, comment='有效开始时间')
    valid_until = Column(DateTime, default=None, comment='有效结束时间')
    reason = Column(String(500), comment='设置原因')
    created_by = Column(Integer, nullable=False, comment='创建者ID')
    is_active = Column(Integer, default=1, comment='是否启用')
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLVideoPlayProgress(Base):
    """视频播放进度追踪表"""
    __tablename__ = "pbl_video_play_progress"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    resource_id = Column(BigInteger, ForeignKey("pbl_resources.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    session_id = Column(String(64), nullable=False, comment='播放会话ID')
    
    # 播放进度信息
    current_position = Column(Integer, default=0, comment='当前播放位置（秒）')
    duration = Column(Integer, default=0, comment='视频总时长（秒）')
    play_duration = Column(Integer, default=0, comment='本次会话累计播放时长（秒）')
    real_watch_duration = Column(Integer, default=0, comment='真实观看时长（秒）')
    
    # 播放状态
    status = Column(String(20), default='playing', comment='播放状态')
    last_event = Column(String(50), comment='最后一次事件')
    last_event_time = Column(DateTime, comment='最后一次事件时间')
    
    # 播放行为统计
    seek_count = Column(Integer, default=0, comment='拖动次数')
    pause_count = Column(Integer, default=0, comment='暂停次数')
    pause_duration = Column(Integer, default=0, comment='累计暂停时长（秒）')
    replay_count = Column(Integer, default=0, comment='重播次数')
    
    # 播放范围
    watched_ranges = Column(Text, comment='已观看的时间段（JSON数组）')
    
    # 完成度
    completion_rate = Column(DECIMAL(5, 2), default=0.00, comment='完成度（百分比）')
    is_completed = Column(Integer, default=0, comment='是否观看完成')
    
    # 客户端信息
    ip_address = Column(String(45), comment='客户端IP地址')
    user_agent = Column(String(500), comment='用户代理')
    device_type = Column(String(50), comment='设备类型')
    
    # 时间信息
    start_time = Column(DateTime, default=get_beijing_time_naive, nullable=False, comment='开始播放时间')
    end_time = Column(DateTime, comment='结束播放时间')
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)


class PBLVideoPlayEvent(Base):
    """视频播放事件表"""
    __tablename__ = "pbl_video_play_events"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, comment='播放会话ID')
    resource_id = Column(BigInteger, ForeignKey("pbl_resources.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Foreign Key to core_users
    event_type = Column(String(50), nullable=False, comment='事件类型')
    event_data = Column(Text, comment='事件数据（JSON格式）')
    position = Column(Integer, default=0, comment='事件发生时的播放位置（秒）')
    timestamp = Column(DateTime, default=get_beijing_time_naive, nullable=False)


class PBLTemplateSchoolPermission(Base):
    """课程模板学校开放权限表"""
    __tablename__ = "pbl_template_school_permissions"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, nullable=False)
    
    # 关联信息
    template_id = Column(BigInteger, ForeignKey("pbl_course_templates.id"), nullable=False)
    school_id = Column(Integer, nullable=False)  # Foreign Key to core_schools
    
    # 权限设置
    is_active = Column(Integer, default=1, comment='是否激活')
    can_customize = Column(Integer, default=1, comment='是否允许自定义修改')
    
    # 使用限制
    max_instances = Column(Integer, default=None, comment='最大创建实例数')
    current_instances = Column(Integer, default=0, comment='当前已创建实例数')
    
    # 有效期设置
    valid_from = Column(DateTime, default=None, comment='有效开始时间')
    valid_until = Column(DateTime, default=None, comment='有效结束时间')
    
    # 管理信息
    granted_by = Column(Integer, nullable=False, comment='授权人ID')
    granted_at = Column(DateTime, default=get_beijing_time_naive, comment='授权时间')
    remarks = Column(Text, comment='备注说明')
    
    # 时间戳
    created_at = Column(DateTime, default=get_beijing_time_naive, nullable=False)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive, nullable=False)
