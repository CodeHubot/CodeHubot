"""
知识库管理API
提供知识库的CRUD操作、权限管理、共享管理等
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.models.user import User
from app.models.school import School
from app.models.course_model import Course
from app.models.agent import Agent
from app.models.knowledge_base import KnowledgeBase, AgentKnowledgeBase, KBPermission, KBSharing
from app.models.document import Document
from app.schemas.knowledge_base_schema import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse, 
    KnowledgeBaseListResponse, KnowledgeBaseStatistics,
    AgentKnowledgeBaseCreate, AgentKnowledgeBaseUpdate, AgentKnowledgeBaseResponse,
    KBPermissionCreate, KBPermissionResponse,
    KBSharingCreate, KBSharingResponse
)
from app.utils.timezone import get_beijing_time_naive

router = APIRouter()


# ============================================================================
# 权限检查辅助函数
# ============================================================================

def is_admin_user(user: User) -> bool:
    """检查是否是管理员"""
    return user.role in ['platform_admin', 'school_admin']


def get_kb_school_id(kb: KnowledgeBase, db: Session) -> Optional[int]:
    """获取知识库关联的学校ID"""
    if kb.scope_type == 'school':
        return kb.scope_id
    elif kb.scope_type == 'course':
        course = db.query(Course).filter(Course.id == kb.scope_id).first()
        return course.school_id if course else None
    elif kb.scope_type == 'agent':
        agent = db.query(Agent).filter(Agent.id == kb.scope_id).first()
        if agent:
            agent_owner = db.query(User).filter(User.id == agent.user_id).first()
            return agent_owner.school_id if agent_owner else None
    elif kb.scope_type == 'personal':
        # 个人知识库：通过scope_id（用户ID）获取用户的学校ID
        user = db.query(User).filter(User.id == kb.scope_id).first()
        return user.school_id if user else None
    return None


def check_kb_permission(user: User, kb: KnowledgeBase, required_permission: str, db: Session) -> bool:
    """
    检查用户对知识库的权限
    
    Args:
        user: 当前用户
        kb: 知识库
        required_permission: 所需权限（read/write/manage/delete）
        db: 数据库会话
    
    Returns:
        bool: 是否有权限
    """
    # 1. 平台管理员拥有所有权限
    if user.role == 'platform_admin':
        return True
    
    # 2. 检查是否是所有者
    if kb.owner_id == user.id:
        return True
    
    # 2.1 检查个人知识库权限（scope_id是用户ID）
    if kb.scope_type == 'personal':
        # 个人知识库：只有scope_id对应的用户有完全权限
        if kb.scope_id == user.id:
            return True
        # 简化：只有public才允许其他人只读访问
        if kb.access_level == 'public' and required_permission == 'read':
            return True
        # private则完全不可访问
        return False
    
    # 2.2 检查智能体知识库权限
    if kb.scope_type == 'agent' and kb.scope_id:
        agent = db.query(Agent).filter(Agent.id == kb.scope_id).first()
        if agent and agent.user_id == user.id:
            return True
    
    # 3. 检查学校管理员权限
    if user.role == 'school_admin':
        if kb.scope_type == 'system':
            # 学校管理员对系统级知识库只有只读权限
            return required_permission == 'read'
        elif kb.scope_type in ['school', 'course']:
            # 学校管理员对本校知识库有管理权限
            kb_school_id = get_kb_school_id(kb, db)
            if kb_school_id and user.school_id == kb_school_id:
                return True
    
    # 4. 检查教师权限
    if user.role == 'teacher':
        if kb.scope_type == 'course':
            # 检查是否是该课程的任课教师
            from app.models.course_model import CourseTeacher
            is_teacher = db.query(CourseTeacher).filter(
                CourseTeacher.course_id == kb.scope_id,
                CourseTeacher.teacher_id == user.id,
                CourseTeacher.deleted_at.is_(None)
            ).first()
            if is_teacher and required_permission in ['read', 'write']:
                return True
    
    # 5. 检查访问级别
    if kb.access_level == 'public' and required_permission == 'read':
        return True
    
    # 6. 检查显式授权
    permission = db.query(KBPermission).filter(
        KBPermission.knowledge_base_id == kb.id,
        or_(
            KBPermission.user_id == user.id,
            KBPermission.role == user.role
        ),
        or_(
            KBPermission.expires_at.is_(None),
            KBPermission.expires_at > get_beijing_time_naive()
        )
    ).first()
    
    if permission:
        # 权限等级：admin > manage > write > read
        permission_levels = {'read': 1, 'write': 2, 'manage': 3, 'admin': 4, 'delete': 4}
        user_level = permission_levels.get(permission.permission_type, 0)
        required_level = permission_levels.get(required_permission, 0)
        if user_level >= required_level:
            return True
    
    # 7. 检查共享权限
    sharing = db.query(KBSharing).filter(
        KBSharing.knowledge_base_id == kb.id,
        or_(
            KBSharing.user_id == user.id,
            and_(KBSharing.school_id == user.school_id, user.school_id.isnot(None)),
            and_(KBSharing.course_id.in_(
                db.query(Course.id).join(
                    CourseTeacher, Course.id == CourseTeacher.course_id
                ).filter(CourseTeacher.teacher_id == user.id)
            ) if user.role == 'teacher' else False)
        ),
        KBSharing.is_active == True,
        or_(
            KBSharing.expires_at.is_(None),
            KBSharing.expires_at > get_beijing_time_naive()
        )
    ).first()
    
    if sharing:
        if sharing.share_type == 'editable':
            return required_permission in ['read', 'write']
        elif sharing.share_type in ['read_only', 'reference']:
            return required_permission == 'read'
    
    # 默认：无权限
    return False


# ============================================================================
# 知识库CRUD API
# ============================================================================

@router.post("", response_model=dict)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库"""
    # 权限检查
    if kb_data.scope_type == 'system':
        if current_user.role != 'platform_admin':
            return error_response(message="只有平台管理员可以创建系统级知识库", code=403)
    elif kb_data.scope_type == 'school':
        if current_user.role not in ['platform_admin', 'school_admin']:
            return error_response(message="只有平台管理员或学校管理员可以创建学校级知识库", code=403)
        if current_user.role == 'school_admin':
            # 学校管理员只能为自己的学校创建
            if kb_data.scope_id != current_user.school_id:
                return error_response(message="只能为本校创建知识库", code=403)
    elif kb_data.scope_type == 'course':
        if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
            return error_response(message="只有管理员或教师可以创建课程级知识库", code=403)
        # 验证课程归属
        if kb_data.scope_id:
            course = db.query(Course).filter(Course.id == kb_data.scope_id).first()
            if not course:
                return error_response(message="课程不存在", code=404)
            if current_user.role == 'school_admin' and course.school_id != current_user.school_id:
                return error_response(message="只能为本校课程创建知识库", code=403)
            elif current_user.role == 'teacher':
                # 检查是否是任课教师
                from app.models.course_model import CourseTeacher
                is_teacher = db.query(CourseTeacher).filter(
                    CourseTeacher.course_id == course.id,
                    CourseTeacher.teacher_id == current_user.id,
                    CourseTeacher.deleted_at.is_(None)
                ).first()
                if not is_teacher:
                    return error_response(message="只能为自己任教的课程创建知识库", code=403)
    elif kb_data.scope_type == 'agent':
        # 验证智能体归属
        if kb_data.scope_id:
            agent = db.query(Agent).filter(Agent.id == kb_data.scope_id).first()
            if not agent:
                return error_response(message="智能体不存在", code=404)
            if agent.user_id != current_user.id and current_user.role != 'platform_admin':
                return error_response(message="只能为自己的智能体创建知识库", code=403)
    elif kb_data.scope_type == 'personal':
        # 个人知识库：scope_id必须是当前用户ID
        if kb_data.scope_id and kb_data.scope_id != current_user.id:
            return error_response(message="个人知识库只能创建给自己", code=403)
        # 自动设置为当前用户ID
        kb_data.scope_id = current_user.id
    
    # 自动设置访问级别（简化：根据scope_type自动决定）
    if not kb_data.access_level:
        access_level_map = {
            'system': 'public',    # 系统级 → 所有人可见
            'school': 'protected', # 学校级 → 本校可见
            'course': 'protected', # 课程级 → 课程可见
            'personal': 'private'  # 个人级 → 仅自己可见
        }
        kb_data.access_level = access_level_map.get(kb_data.scope_type, 'private')
    
    # 创建知识库
    kb = KnowledgeBase(
        name=kb_data.name,
        description=kb_data.description,
        icon=kb_data.icon,
        scope_type=kb_data.scope_type,
        scope_id=kb_data.scope_id,
        parent_kb_id=kb_data.parent_kb_id,
        owner_id=current_user.id,
        access_level=kb_data.access_level,
        chunk_size=kb_data.chunk_size,
        chunk_overlap=kb_data.chunk_overlap,
        embedding_model_id=kb_data.embedding_model_id,
        tags=kb_data.tags,
        meta_data=kb_data.meta_data
    )
    
    db.add(kb)
    db.commit()
    db.refresh(kb)
    
    return success_response(
        data={"uuid": kb.uuid, "id": kb.id, "name": kb.name},
        message="知识库创建成功"
    )


@router.get("", response_model=dict)
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope_type: Optional[str] = Query(None),
    scope_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    include_inherited: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库列表"""
    # 构建查询
    query = db.query(KnowledgeBase).filter(KnowledgeBase.deleted_at.is_(None))
    
    # 权限过滤
    if current_user.role != 'platform_admin':
        # 获取用户可访问的知识库ID列表
        accessible_kb_ids = []
        
        # 用户自己创建的
        owned_kbs = db.query(KnowledgeBase.id).filter(
            KnowledgeBase.owner_id == current_user.id,
            KnowledgeBase.deleted_at.is_(None)
        ).all()
        accessible_kb_ids.extend([kb_id for kb_id, in owned_kbs])
        
        # 公开的
        public_kbs = db.query(KnowledgeBase.id).filter(
            KnowledgeBase.access_level == 'public',
            KnowledgeBase.deleted_at.is_(None)
        ).all()
        accessible_kb_ids.extend([kb_id for kb_id, in public_kbs])
        
        # 学校管理员：本校的
        if current_user.role == 'school_admin' and current_user.school_id:
            school_kbs = db.query(KnowledgeBase.id).filter(
                or_(
                    and_(
                        KnowledgeBase.scope_type == 'school',
                        KnowledgeBase.scope_id == current_user.school_id
                    ),
                    and_(
                        KnowledgeBase.scope_type == 'course',
                        KnowledgeBase.scope_id.in_(
                            db.query(Course.id).filter(Course.school_id == current_user.school_id)
                        )
                    )
                ),
                KnowledgeBase.deleted_at.is_(None)
            ).all()
            accessible_kb_ids.extend([kb_id for kb_id, in school_kbs])
        
        # 教师：任课课程的
        if current_user.role == 'teacher':
            from app.models.course_model import CourseTeacher
            teacher_course_ids = db.query(CourseTeacher.course_id).filter(
                CourseTeacher.teacher_id == current_user.id,
                CourseTeacher.deleted_at.is_(None)
            ).all()
            course_ids = [cid for cid, in teacher_course_ids]
            if course_ids:
                course_kbs = db.query(KnowledgeBase.id).filter(
                    KnowledgeBase.scope_type == 'course',
                    KnowledgeBase.scope_id.in_(course_ids),
                    KnowledgeBase.deleted_at.is_(None)
                ).all()
                accessible_kb_ids.extend([kb_id for kb_id, in course_kbs])
        
        # 应用权限过滤
        if accessible_kb_ids:
            query = query.filter(KnowledgeBase.id.in_(list(set(accessible_kb_ids))))
        else:
            # 没有可访问的知识库
            return success_response(data={
                "total": 0,
                "page": page,
                "page_size": page_size,
                "knowledge_bases": []
            })
    
    # 筛选条件
    if scope_type:
        query = query.filter(KnowledgeBase.scope_type == scope_type)
    
    if scope_id:
        query = query.filter(KnowledgeBase.scope_id == scope_id)
    
    if keyword:
        query = query.filter(
            or_(
                KnowledgeBase.name.like(f"%{keyword}%"),
                KnowledgeBase.description.like(f"%{keyword}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    kbs = query.order_by(KnowledgeBase.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    kb_list = []
    for kb in kbs:
        kb_dict = KnowledgeBaseListResponse.from_orm(kb).model_dump()
        
        # 添加所有者姓名
        owner = db.query(User).filter(User.id == kb.owner_id).first()
        kb_dict['owner_name'] = owner.real_name or owner.name or owner.username if owner else None
        
        # 添加作用域名称
        if kb.scope_type == 'school' and kb.scope_id:
            school = db.query(School).filter(School.id == kb.scope_id).first()
            kb_dict['scope_name'] = school.school_name if school else None
        elif kb.scope_type == 'course' and kb.scope_id:
            course = db.query(Course).filter(Course.id == kb.scope_id).first()
            kb_dict['scope_name'] = course.course_name if course else None
        elif kb.scope_type == 'agent' and kb.scope_id:
            agent = db.query(Agent).filter(Agent.id == kb.scope_id).first()
            kb_dict['scope_name'] = agent.name if agent else None
        
        kb_list.append(kb_dict)
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "knowledge_bases": kb_list
    })


@router.get("/{kb_uuid}", response_model=dict)
async def get_knowledge_base(
    kb_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权查看该知识库", code=403)
    
    # 转换为响应格式
    kb_dict = KnowledgeBaseResponse.from_orm(kb).model_dump()
    
    # 添加所有者信息
    owner = db.query(User).filter(User.id == kb.owner_id).first()
    kb_dict['owner_name'] = owner.real_name or owner.name or owner.username if owner else None
    
    # 添加作用域名称
    if kb.scope_type == 'school' and kb.scope_id:
        school = db.query(School).filter(School.id == kb.scope_id).first()
        kb_dict['scope_name'] = school.school_name if school else None
    elif kb.scope_type == 'course' and kb.scope_id:
        course = db.query(Course).filter(Course.id == kb.scope_id).first()
        kb_dict['scope_name'] = course.course_name if course else None
    elif kb.scope_type == 'agent' and kb.scope_id:
        agent = db.query(Agent).filter(Agent.id == kb.scope_id).first()
        kb_dict['scope_name'] = agent.name if agent else None
    
    # 添加父知识库信息
    if kb.parent_kb_id:
        parent_kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb.parent_kb_id
        ).first()
        kb_dict['parent_kb'] = {
            "id": parent_kb.id,
            "uuid": parent_kb.uuid,
            "name": parent_kb.name
        } if parent_kb else None
    
    # 添加权限信息
    kb_dict['permissions'] = {
        "can_read": True,  # 能访问详情就有读权限
        "can_write": check_kb_permission(current_user, kb, 'write', db),
        "can_manage": check_kb_permission(current_user, kb, 'manage', db),
        "can_delete": check_kb_permission(current_user, kb, 'delete', db)
    }
    
    return success_response(data=kb_dict)


@router.put("/{kb_uuid}", response_model=dict)
async def update_knowledge_base(
    kb_uuid: str,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新知识库"""
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    if not check_kb_permission(current_user, kb, 'write', db):
        return error_response(message="无权编辑该知识库", code=403)
    
    # 更新字段
    update_data = kb_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != 're_embed' and hasattr(kb, field):
            setattr(kb, field, value)
    
    kb.last_updated_at = get_beijing_time_naive()
    
    db.commit()
    db.refresh(kb)
    
    return success_response(message="知识库更新成功")


@router.delete("/{kb_uuid}", response_model=dict)
async def delete_knowledge_base(
    kb_uuid: str,
    cascade: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库"""
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 权限检查
    if not check_kb_permission(current_user, kb, 'delete', db):
        return error_response(message="无权删除该知识库", code=403)
    
    # 系统内置知识库不能删除
    if kb.is_system:
        return error_response(message="系统内置知识库不能删除", code=403)
    
    # 软删除
    kb.deleted_at = get_beijing_time_naive()
    
    # 如果级联删除，也删除所有文档
    if cascade:
        db.query(Document).filter(
            Document.knowledge_base_id == kb.id,
            Document.deleted_at.is_(None)
        ).update({"deleted_at": get_beijing_time_naive()})
    
    db.commit()
    
    return success_response(message="知识库已删除")


@router.get("/hierarchy-tree", response_model=dict)
async def get_hierarchy_tree(
    scope_type: Optional[str] = Query(None),
    scope_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库层级树"""
    # 构建查询
    query = db.query(KnowledgeBase).filter(KnowledgeBase.deleted_at.is_(None))
    
    # 权限过滤（简化版，实际使用check_kb_permission）
    if current_user.role == 'school_admin' and current_user.school_id:
        query = query.filter(
            or_(
                KnowledgeBase.scope_type == 'system',
                and_(
                    KnowledgeBase.scope_type == 'school',
                    KnowledgeBase.scope_id == current_user.school_id
                ),
                and_(
                    KnowledgeBase.scope_type == 'course',
                    KnowledgeBase.scope_id.in_(
                        db.query(Course.id).filter(Course.school_id == current_user.school_id)
                    )
                )
            )
        )
    
    if scope_type:
        query = query.filter(KnowledgeBase.scope_type == scope_type)
    
    if scope_id:
        query = query.filter(KnowledgeBase.scope_id == scope_id)
    
    all_kbs = query.all()
    
    # 构建树形结构
    def build_tree_node(kb):
        return {
            "id": kb.id,
            "uuid": kb.uuid,
            "name": kb.name,
            "scope_type": kb.scope_type,
            "scope_id": kb.scope_id,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "children": []
        }
    
    # 创建映射
    kb_map = {kb.id: build_tree_node(kb) for kb in all_kbs}
    tree = []
    
    # 构建层级关系
    for kb in all_kbs:
        node = kb_map[kb.id]
        if kb.parent_kb_id and kb.parent_kb_id in kb_map:
            kb_map[kb.parent_kb_id]['children'].append(node)
        else:
            tree.append(node)
    
    return success_response(data={"tree": tree})


@router.get("/statistics/global", response_model=dict)
async def get_global_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取全局统计（仅平台管理员）"""
    if current_user.role != 'platform_admin':
        return error_response(message="只有平台管理员可以查看全局统计", code=403)
    
    total_kbs = db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    system_kbs = db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.scope_type == 'system',
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    school_kbs = db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.scope_type == 'school',
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    course_kbs = db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.scope_type == 'course',
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    agent_kbs = db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.scope_type.in_(['agent', 'personal']),
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    total_documents = db.query(func.count(Document.id)).filter(
        Document.deleted_at.is_(None)
    ).scalar() or 0
    
    total_chunks = db.query(func.sum(KnowledgeBase.chunk_count)).filter(
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    total_size = db.query(func.sum(KnowledgeBase.total_size)).filter(
        KnowledgeBase.deleted_at.is_(None)
    ).scalar() or 0
    
    stats = KnowledgeBaseStatistics(
        total_kbs=total_kbs,
        system_kbs=system_kbs,
        school_kbs=school_kbs,
        course_kbs=course_kbs,
        agent_kbs=agent_kbs,
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_size=total_size
    )
    
    return success_response(data=stats.model_dump())


# ============================================================================
# 智能体知识库关联API
# ============================================================================

@router.get("/agents/{agent_uuid}/available-knowledge-bases", response_model=dict)
async def get_available_knowledge_bases_for_agent(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体可用但未关联的知识库列表"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[可用知识库] 开始查询智能体 {agent_uuid} 的可用知识库")
        
        # 获取智能体
        agent = db.query(Agent).filter(
            Agent.uuid == agent_uuid,
            Agent.is_active == 1
        ).first()
        
        if not agent:
            logger.warning(f"[可用知识库] 智能体不存在: {agent_uuid}")
            return error_response(message="智能体不存在", code=404)
        
        logger.info(f"[可用知识库] 找到智能体: {agent.name} (id={agent.id})")
        
        # 权限检查
        if agent.user_id != current_user.id and current_user.role != 'platform_admin':
            logger.warning(f"[可用知识库] 用户 {current_user.id} 无权查看智能体 {agent.id}")
            return error_response(message="无权查看该智能体", code=403)
        
        # 获取已关联的知识库ID列表
        logger.info(f"[可用知识库] 查询已关联的知识库...")
        associated_kb_ids = db.query(AgentKnowledgeBase.knowledge_base_id).filter(
            AgentKnowledgeBase.agent_id == agent.id
        ).all()
        associated_kb_ids = [item[0] for item in associated_kb_ids]
        logger.info(f"[可用知识库] 已关联 {len(associated_kb_ids)} 个知识库")
        
        # 构建可访问的知识库查询
        logger.info(f"[可用知识库] 构建基础查询...")
        query = db.query(KnowledgeBase).filter(
            KnowledgeBase.deleted_at.is_(None)
        )
        
        # 检查 is_active 字段是否存在
        if hasattr(KnowledgeBase, 'is_active'):
            query = query.filter(KnowledgeBase.is_active == True)
        
        # 排除已关联的知识库
        if associated_kb_ids:
            query = query.filter(~KnowledgeBase.id.in_(associated_kb_ids))
            logger.info(f"[可用知识库] 排除已关联的知识库")
        
        # 根据用户权限过滤
        accessible_kb_ids = []
        
        # 1. 用户创建的知识库
        logger.info(f"[可用知识库] 查询用户创建的知识库...")
        try:
            owner_kbs = query.filter(KnowledgeBase.owner_id == current_user.id).all()
            accessible_kb_ids.extend([kb.id for kb in owner_kbs])
            logger.info(f"[可用知识库] 找到 {len(owner_kbs)} 个用户创建的知识库")
        except Exception as e:
            logger.error(f"[可用知识库] 查询用户创建的知识库失败: {e}")
        
        # 2. 公开知识库
        logger.info(f"[可用知识库] 查询公开知识库...")
        try:
            public_kbs = query.filter(KnowledgeBase.access_level == 'public').all()
            accessible_kb_ids.extend([kb.id for kb in public_kbs])
            logger.info(f"[可用知识库] 找到 {len(public_kbs)} 个公开知识库")
        except Exception as e:
            logger.error(f"[可用知识库] 查询公开知识库失败: {e}")
        
        # 3. 学校级/课程级知识库（根据用户学校）
        if current_user.school_id:
            logger.info(f"[可用知识库] 查询学校级知识库 (school_id={current_user.school_id})...")
            try:
                school_kbs = query.filter(
                    KnowledgeBase.scope_type == 'school',
                    KnowledgeBase.scope_id == current_user.school_id
                ).all()
                accessible_kb_ids.extend([kb.id for kb in school_kbs])
                logger.info(f"[可用知识库] 找到 {len(school_kbs)} 个学校级知识库")
            except Exception as e:
                logger.error(f"[可用知识库] 查询学校级知识库失败: {e}")
            
            # 课程级知识库（用户有权限的课程）
            if current_user.role == 'teacher':
                logger.info(f"[可用知识库] 查询教师课程的知识库...")
                try:
                    from app.models.course_model import CourseTeacher
                    course_ids = db.query(CourseTeacher.course_id).filter(
                        CourseTeacher.teacher_id == current_user.id,
                        CourseTeacher.deleted_at.is_(None)
                    ).all()
                    course_ids = [item[0] for item in course_ids]
                    logger.info(f"[可用知识库] 教师任教 {len(course_ids)} 个课程")
                    
                    if course_ids:
                        course_kbs = query.filter(
                            KnowledgeBase.scope_type == 'course',
                            KnowledgeBase.scope_id.in_(course_ids)
                        ).all()
                        accessible_kb_ids.extend([kb.id for kb in course_kbs])
                        logger.info(f"[可用知识库] 找到 {len(course_kbs)} 个课程级知识库")
                except Exception as e:
                    logger.error(f"[可用知识库] 查询课程级知识库失败: {e}")
        
        # 4. 系统级知识库
        logger.info(f"[可用知识库] 查询系统级知识库...")
        try:
            system_kbs = query.filter(KnowledgeBase.scope_type == 'system').all()
            accessible_kb_ids.extend([kb.id for kb in system_kbs])
            logger.info(f"[可用知识库] 找到 {len(system_kbs)} 个系统级知识库")
        except Exception as e:
            logger.error(f"[可用知识库] 查询系统级知识库失败: {e}")
        
        # 去重并获取知识库详情
        accessible_kb_ids = list(set(accessible_kb_ids))
        logger.info(f"[可用知识库] 去重后共 {len(accessible_kb_ids)} 个可访问知识库")
        
        if accessible_kb_ids:
            available_kbs = query.filter(KnowledgeBase.id.in_(accessible_kb_ids)).all()
        else:
            available_kbs = []
        
        logger.info(f"[可用知识库] 最终可用知识库数量: {len(available_kbs)}")
        
        # 构建响应
        result = []
        for kb in available_kbs:
            try:
                result.append({
                    "uuid": kb.uuid,
                    "name": kb.name,
                    "description": kb.description,
                    "scope_type": kb.scope_type,
                    "document_count": kb.document_count or 0,
                    "chunk_count": kb.chunk_count or 0,
                    "created_at": kb.created_at.isoformat() if kb.created_at else None,
                    "updated_at": kb.updated_at.isoformat() if kb.updated_at else None
                })
            except Exception as e:
                logger.error(f"[可用知识库] 序列化知识库 {kb.id} 失败: {e}")
        
        logger.info(f"[可用知识库] 查询完成，返回 {len(result)} 个可用知识库")
        return success_response(data={"knowledge_bases": result, "total": len(result)})
    
    except Exception as e:
        logger.error(f"[可用知识库] 查询失败: {str(e)}", exc_info=True)
        return error_response(message=f"查询失败: {str(e)}", code=500)


@router.get("/agents/{agent_uuid}/knowledge-bases", response_model=dict)
async def list_agent_knowledge_bases(
    agent_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体关联的知识库列表"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[智能体知识库] 开始查询智能体 {agent_uuid} 的关联知识库")
        
        # 获取智能体
        agent = db.query(Agent).filter(
            Agent.uuid == agent_uuid,
            Agent.is_active == 1
        ).first()
        
        if not agent:
            logger.warning(f"[智能体知识库] 智能体不存在: {agent_uuid}")
            return error_response(message="智能体不存在", code=404)
        
        logger.info(f"[智能体知识库] 找到智能体: {agent.name} (id={agent.id})")
        
        # 权限检查（只有所有者或管理员可以查看）
        if agent.user_id != current_user.id and current_user.role != 'platform_admin':
            logger.warning(f"[智能体知识库] 用户 {current_user.id} 无权查看智能体 {agent.id}")
            return error_response(message="无权查看该智能体", code=403)
        
        # 查询关联的知识库
        logger.info(f"[智能体知识库] 开始查询关联表...")
        associations = db.query(AgentKnowledgeBase).filter(
            AgentKnowledgeBase.agent_id == agent.id
        ).all()
        
        logger.info(f"[智能体知识库] 找到 {len(associations)} 个关联记录")
        
        result_list = []
        for idx, assoc in enumerate(associations):
            logger.info(f"[智能体知识库] 处理关联 {idx+1}/{len(associations)}: kb_id={assoc.knowledge_base_id}")
            
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == assoc.knowledge_base_id).first()
            if kb and kb.deleted_at is None:
                logger.info(f"[智能体知识库] 找到知识库: {kb.name}")
                try:
                    result_list.append(AgentKnowledgeBaseResponse(
                        id=assoc.id,
                        agent_id=assoc.agent_id,
                        knowledge_base_id=kb.id,
                        knowledge_base_uuid=kb.uuid,
                        knowledge_base_name=kb.name,
                        priority=assoc.priority,
                        is_enabled=assoc.is_enabled,
                        top_k=assoc.top_k,
                        similarity_threshold=float(assoc.similarity_threshold) if assoc.similarity_threshold else 0.70,
                        retrieval_mode=assoc.retrieval_mode,
                        document_count=kb.document_count,
                        is_inherited=False,
                        created_at=assoc.created_at,
                        updated_at=assoc.updated_at
                    ).model_dump())
                    logger.info(f"[智能体知识库] 成功序列化关联 {idx+1}")
                except Exception as e:
                    logger.error(f"[智能体知识库] 序列化关联 {idx+1} 失败: {str(e)}", exc_info=True)
                    raise
            else:
                logger.warning(f"[智能体知识库] 知识库 {assoc.knowledge_base_id} 不存在或已删除，跳过")
        
        # 按优先级排序
        result_list.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"[智能体知识库] 查询完成，返回 {len(result_list)} 个知识库")
        return success_response(data={"knowledge_bases": result_list})
    
    except Exception as e:
        logger.error(f"[智能体知识库] 查询失败: {str(e)}", exc_info=True)
        return error_response(message=f"查询失败: {str(e)}", code=500)


@router.post("/agents/{agent_uuid}/knowledge-bases", response_model=dict)
async def add_agent_knowledge_base(
    agent_uuid: str,
    assoc_data: AgentKnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为智能体添加知识库关联"""
    # 获取智能体
    agent = db.query(Agent).filter(
        Agent.uuid == agent_uuid,
        Agent.is_active == 1
    ).first()
    
    if not agent:
        return error_response(message="智能体不存在", code=404)
    
    # 权限检查
    if agent.user_id != current_user.id and current_user.role != 'platform_admin':
        return error_response(message="无权编辑该智能体", code=403)
    
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == assoc_data.knowledge_base_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 检查用户是否有权访问该知识库
    if not check_kb_permission(current_user, kb, 'read', db):
        return error_response(message="无权访问该知识库", code=403)
    
    # 检查是否已关联
    existing = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent.id,
        AgentKnowledgeBase.knowledge_base_id == kb.id
    ).first()
    
    if existing:
        return error_response(message="该知识库已关联到智能体", code=400)
    
    # 创建关联
    assoc = AgentKnowledgeBase(
        agent_id=agent.id,
        knowledge_base_id=kb.id,
        priority=assoc_data.priority,
        is_enabled=assoc_data.is_enabled,
        top_k=assoc_data.top_k,
        similarity_threshold=assoc_data.similarity_threshold,
        retrieval_mode=assoc_data.retrieval_mode
    )
    
    db.add(assoc)
    db.commit()
    
    return success_response(message="知识库关联成功")


@router.post("/agents/{agent_uuid}/knowledge-bases/batch", response_model=dict)
async def batch_add_agent_knowledge_bases(
    agent_uuid: str,
    knowledge_bases: List[AgentKnowledgeBaseCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量为智能体添加知识库关联"""
    # 获取智能体
    agent = db.query(Agent).filter(
        Agent.uuid == agent_uuid,
        Agent.is_active == 1
    ).first()
    
    if not agent:
        return error_response(message="智能体不存在", code=404)
    
    # 权限检查
    if agent.user_id != current_user.id and current_user.role != 'platform_admin':
        return error_response(message="无权编辑该智能体", code=403)
    
    success_count = 0
    failed_list = []
    
    try:
        for assoc_data in knowledge_bases:
            # 获取知识库
            kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.uuid == assoc_data.knowledge_base_uuid,
                KnowledgeBase.deleted_at.is_(None)
            ).first()
            
            if not kb:
                failed_list.append(f"知识库 {assoc_data.knowledge_base_uuid} 不存在")
                continue
            
            # 检查用户是否有权访问该知识库
            if not check_kb_permission(current_user, kb, 'read', db):
                failed_list.append(f"无权访问知识库 {kb.name}")
                continue
            
            # 检查是否已关联
            existing = db.query(AgentKnowledgeBase).filter(
                AgentKnowledgeBase.agent_id == agent.id,
                AgentKnowledgeBase.knowledge_base_id == kb.id
            ).first()
            
            if existing:
                failed_list.append(f"知识库 {kb.name} 已关联")
                continue
            
            # 创建关联
            assoc = AgentKnowledgeBase(
                agent_id=agent.id,
                knowledge_base_id=kb.id,
                priority=assoc_data.priority,
                is_enabled=assoc_data.is_enabled,
                top_k=assoc_data.top_k,
                similarity_threshold=assoc_data.similarity_threshold,
                retrieval_mode=assoc_data.retrieval_mode
            )
            
            db.add(assoc)
            success_count += 1
        
        db.commit()
        
        result_message = f"成功关联 {success_count} 个知识库"
        if failed_list:
            result_message += f"，失败 {len(failed_list)} 个"
        
        return success_response(
            message=result_message,
            data={"success_count": success_count, "failed_list": failed_list}
        )
    
    except Exception as e:
        db.rollback()
        return error_response(message=f"批量添加失败: {str(e)}", code=500)


@router.put("/agents/{agent_uuid}/knowledge-bases/{kb_uuid}", response_model=dict)
async def update_agent_knowledge_base(
    agent_uuid: str,
    kb_uuid: str,
    assoc_data: AgentKnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新智能体知识库关联配置"""
    # 获取智能体
    agent = db.query(Agent).filter(
        Agent.uuid == agent_uuid,
        Agent.is_active == 1
    ).first()
    
    if not agent:
        return error_response(message="智能体不存在", code=404)
    
    # 权限检查
    if agent.user_id != current_user.id and current_user.role != 'platform_admin':
        return error_response(message="无权编辑该智能体", code=403)
    
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 获取关联
    assoc = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent.id,
        AgentKnowledgeBase.knowledge_base_id == kb.id
    ).first()
    
    if not assoc:
        return error_response(message="关联不存在", code=404)
    
    # 更新字段
    update_data = assoc_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(assoc, field):
            setattr(assoc, field, value)
    
    db.commit()
    
    return success_response(message="关联配置已更新")


@router.delete("/agents/{agent_uuid}/knowledge-bases/{kb_uuid}", response_model=dict)
async def remove_agent_knowledge_base(
    agent_uuid: str,
    kb_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除智能体知识库关联"""
    # 获取智能体
    agent = db.query(Agent).filter(
        Agent.uuid == agent_uuid,
        Agent.is_active == 1
    ).first()
    
    if not agent:
        return error_response(message="智能体不存在", code=404)
    
    # 权限检查
    if agent.user_id != current_user.id and current_user.role != 'platform_admin':
        return error_response(message="无权编辑该智能体", code=403)
    
    # 获取知识库
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.uuid == kb_uuid,
        KnowledgeBase.deleted_at.is_(None)
    ).first()
    
    if not kb:
        return error_response(message="知识库不存在", code=404)
    
    # 删除关联
    db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent.id,
        AgentKnowledgeBase.knowledge_base_id == kb.id
    ).delete()
    
    db.commit()
    
    return success_response(message="知识库关联已移除")

