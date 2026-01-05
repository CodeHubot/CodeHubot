"""
PBL系统API路由
自动整合所有PBL相关的API端点
"""
from fastapi import APIRouter

# 创建PBL主路由
pbl_router = APIRouter()

# 尝试导入所有PBL endpoint
# 注意：认证相关接口已统一到 /api/auth，不再需要单独的 auth router
# 学生端路由

try:
    from app.api.pbl.student_courses import router as student_courses_router
    pbl_router.include_router(student_courses_router, prefix="/student", tags=["PBL-学生课程"])
except ImportError as e:
    print(f"警告: 无法导入student_courses: {e}")

try:
    from app.api.pbl.student_tasks import router as student_tasks_router
    pbl_router.include_router(student_tasks_router, prefix="/student", tags=["PBL-学生任务"])
except ImportError as e:
    print(f"警告: 无法导入student_tasks: {e}")

try:
    from app.api.pbl.student_attachments import router as student_attachments_router
    pbl_router.include_router(student_attachments_router, prefix="/student/attachments", tags=["PBL-学生附件"])
except ImportError as e:
    print(f"警告: 无法导入student_attachments: {e}")

try:
    from app.api.pbl.temp_attachments import router as temp_attachments_router
    pbl_router.include_router(temp_attachments_router, prefix="/student/temp-attachments", tags=["PBL-临时附件"])
except ImportError as e:
    print(f"警告: 无法导入temp_attachments: {e}")

try:
    from app.api.pbl.student_club import router as student_club_router
    pbl_router.include_router(student_club_router, prefix="/student/club", tags=["PBL-学生社团"])
except ImportError as e:
    print(f"警告: 无法导入student_club: {e}")

# 教师端路由

try:
    from app.api.pbl.teacher_courses import router as teacher_courses_router
    pbl_router.include_router(teacher_courses_router, prefix="/teacher", tags=["PBL-教师课程"])
except ImportError as e:
    print(f"警告: 无法导入teacher_courses: {e}")

# 管理员路由

try:
    from app.api.pbl.admin_courses import router as admin_courses_router
    pbl_router.include_router(admin_courses_router, prefix="/admin/courses", tags=["PBL-管理员课程管理"])
except ImportError as e:
    print(f"警告: 无法导入admin_courses: {e}")

try:
    from app.api.pbl.admin_tasks import router as admin_tasks_router
    pbl_router.include_router(admin_tasks_router, prefix="/admin/tasks", tags=["PBL-任务管理"])
except ImportError as e:
    print(f"警告: 无法导入admin_tasks: {e}")

try:
    from app.api.pbl.admin_units import router as admin_units_router
    pbl_router.include_router(admin_units_router, prefix="/admin/units", tags=["PBL-单元管理"])
except ImportError as e:
    print(f"警告: 无法导入admin_units: {e}")

try:
    from app.api.pbl.admin_resources import router as admin_resources_router
    pbl_router.include_router(admin_resources_router, prefix="/admin/resources", tags=["PBL-资源管理"])
except ImportError as e:
    print(f"警告: 无法导入admin_resources: {e}")

try:
    from app.api.pbl.admin_users import router as admin_users_router
    pbl_router.include_router(admin_users_router, prefix="/admin/users", tags=["PBL-用户管理"])
except ImportError as e:
    print(f"警告: 无法导入admin_users: {e}")

try:
    from app.api.pbl.feedback_templates import router as feedback_templates_router
    pbl_router.include_router(feedback_templates_router, prefix="/admin/feedback-templates", tags=["PBL-评语模板"])
except ImportError as e:
    print(f"警告: 无法导入feedback_templates: {e}")

# 其他PBL功能路由
try:
    from app.api.pbl.schools import router as schools_router
    pbl_router.include_router(schools_router, prefix="/admin/schools", tags=["PBL-学校管理"])
except ImportError as e:
    print(f"警告: 无法导入schools: {e}")

try:
    from app.api.pbl.classes_groups import router as classes_groups_router
    pbl_router.include_router(classes_groups_router, prefix="/admin/classes-groups", tags=["PBL-小组管理"])
except ImportError as e:
    print(f"警告: 无法导入classes_groups: {e}")

try:
    from app.api.pbl.video_play import router as video_play_router
    pbl_router.include_router(video_play_router, prefix="/video", tags=["PBL-视频播放"])
except ImportError as e:
    print(f"警告: 无法导入video_play: {e}")

try:
    from app.api.pbl.video_progress import router as video_progress_router
    pbl_router.include_router(video_progress_router, prefix="/video/progress", tags=["PBL-视频进度"])
except ImportError as e:
    print(f"警告: 无法导入video_progress: {e}")

try:
    from app.api.pbl.available_templates import router as available_templates_router
    pbl_router.include_router(available_templates_router, prefix="/admin/available-templates", tags=["PBL-可用模板"])
except ImportError as e:
    print(f"警告: 无法导入available_templates: {e}")

try:
    from app.api.pbl.template_permissions import router as template_permissions_router
    pbl_router.include_router(template_permissions_router, prefix="/admin", tags=["PBL-模板权限"])
except ImportError as e:
    print(f"警告: 无法导入template_permissions: {e}")

try:
    from app.api.pbl.club_classes import router as club_classes_router
    pbl_router.include_router(club_classes_router, prefix="/admin/club", tags=["PBL-班级管理"])
except ImportError as e:
    print(f"警告: 无法导入club_classes: {e}")

try:
    from app.api.pbl.class_analytics import router as class_analytics_router
    pbl_router.include_router(class_analytics_router, prefix="/class-analytics", tags=["PBL-班级分析"])
except ImportError as e:
    print(f"警告: 无法导入class_analytics: {e}")

try:
    from app.api.pbl.channel_schools import router as channel_schools_router
    pbl_router.include_router(channel_schools_router, prefix="/channel", tags=["PBL-渠道学校"])
except ImportError as e:
    print(f"警告: 无法导入channel_schools: {e}")

try:
    from app.api.pbl.channel_management import router as channel_management_router
    pbl_router.include_router(channel_management_router, prefix="/channel-management", tags=["PBL-渠道管理"])
except ImportError as e:
    print(f"警告: 无法导入channel_management: {e}")

try:
    from app.api.pbl.learning_progress import router as learning_progress_router
    pbl_router.include_router(learning_progress_router, prefix="/student/learning-progress", tags=["PBL-学习进度"])
except ImportError as e:
    print(f"警告: 无法导入learning_progress: {e}")

try:
    from app.api.pbl.ai_chat import router as ai_chat_router
    pbl_router.include_router(ai_chat_router, prefix="/ai-chat", tags=["PBL-AI对话"])
except ImportError as e:
    print(f"警告: 无法导入ai_chat: {e}")

# AI学习助手路由（Phase 1）
try:
    from app.api.pbl.learning_assistant import router as learning_assistant_router
    pbl_router.include_router(learning_assistant_router, prefix="/learning-assistant", tags=["PBL-AI学习助手"])
except ImportError as e:
    print(f"警告: 无法导入learning_assistant: {e}")

try:
    from app.api.pbl.learning_assistant_teacher import router as learning_assistant_teacher_router
    pbl_router.include_router(learning_assistant_teacher_router, prefix="/learning-assistant/teacher", tags=["PBL-AI学习助手-教师"])
except ImportError as e:
    print(f"警告: 无法导入learning_assistant_teacher: {e}")

print(f"✓ PBL路由注册完成，已注册 {len(pbl_router.routes)} 个路由")
