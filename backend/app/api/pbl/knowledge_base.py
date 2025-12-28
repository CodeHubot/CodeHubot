"""
单元知识库API
用于检索单元相关知识，支持RAG（检索增强生成）
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_, text
from datetime import datetime
import uuid

from app.core.deps import get_db, get_current_user
from app.core.response import success_response
from app.models.knowledge_base import UnitKnowledgeBase, KnowledgeUsageLog
from app.models.user import User

router = APIRouter()


@router.get("/units/{unit_uuid}/search")
def search_unit_knowledge(
    unit_uuid: str,
    query: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="返回结果数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检索单元知识库
    
    - 支持关键词全文检索
    - 按优先级和质量评分排序
    - 用于AI回答时提供上下文
    """
    # 构建全文检索查询
    # 方式1：使用MATCH AGAINST（MySQL全文索引）
    search_query = db.query(UnitKnowledgeBase).filter(
        UnitKnowledgeBase.unit_uuid == unit_uuid,
        UnitKnowledgeBase.status == 'active',
        UnitKnowledgeBase.is_public == True
    )
    
    # 尝试使用全文检索
    try:
        # MySQL FULLTEXT search
        search_query = search_query.filter(
            or_(
                text(f"MATCH(title, keywords) AGAINST(:query IN BOOLEAN MODE)").bindparams(query=query),
                text(f"MATCH(content) AGAINST(:query IN BOOLEAN MODE)").bindparams(query=query)
            )
        )
    except Exception as e:
        # 如果全文检索失败，使用LIKE查询
        search_pattern = f"%{query}%"
        search_query = search_query.filter(
            or_(
                UnitKnowledgeBase.title.like(search_pattern),
                UnitKnowledgeBase.keywords.like(search_pattern),
                UnitKnowledgeBase.content.like(search_pattern)
            )
        )
    
    # 排序和限制
    results = search_query.order_by(
        desc(UnitKnowledgeBase.priority),
        desc(UnitKnowledgeBase.quality_score),
        desc(UnitKnowledgeBase.usage_count)
    ).limit(limit).all()
    
    # 格式化返回结果
    knowledge_list = [
        {
            "uuid": k.uuid,
            "title": k.title,
            "content": k.content,
            "summary": k.summary,
            "category": k.category,
            "tags": k.tags,
            "source_url": k.source_url,
            "quality_score": float(k.quality_score) if k.quality_score else 0,
            "usage_count": k.usage_count
        }
        for k in results
    ]
    
    return success_response(data=knowledge_list)


@router.post("/usage-log")
def log_knowledge_usage(
    knowledge_uuid: str,
    message_uuid: Optional[str] = None,
    session_id: Optional[int] = None,
    query_text: Optional[str] = None,
    relevance_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    记录知识点使用
    
    - AI使用知识点回答时调用
    - 用于统计知识点使用情况
    - 优化知识库质量
    """
    # 查找知识点
    knowledge = db.query(UnitKnowledgeBase).filter(
        UnitKnowledgeBase.uuid == knowledge_uuid
    ).first()
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识点不存在")
    
    # 创建使用记录
    usage_log = KnowledgeUsageLog(
        knowledge_id=knowledge.id,
        knowledge_uuid=knowledge_uuid,
        message_uuid=message_uuid,
        session_id=session_id,
        user_id=current_user.id,
        query_text=query_text,
        relevance_score=relevance_score,
        match_type='keyword',
        used_at=datetime.now()
    )
    
    db.add(usage_log)
    
    # 更新知识点使用计数
    knowledge.usage_count += 1
    
    db.commit()
    
    return success_response(message="使用记录已保存")


@router.get("/units/{unit_uuid}/popular")
def get_popular_knowledge(
    unit_uuid: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单元热门知识点
    
    - 按使用次数排序
    - 显示有帮助率
    - 用于推荐和优化
    """
    popular = db.query(
        UnitKnowledgeBase.uuid,
        UnitKnowledgeBase.title,
        UnitKnowledgeBase.category,
        UnitKnowledgeBase.usage_count,
        UnitKnowledgeBase.helpful_count,
        (UnitKnowledgeBase.helpful_count * 100.0 / func.nullif(UnitKnowledgeBase.usage_count, 0)).label('helpful_rate')
    ).filter(
        UnitKnowledgeBase.unit_uuid == unit_uuid,
        UnitKnowledgeBase.status == 'active',
        UnitKnowledgeBase.usage_count > 0
    ).order_by(
        desc(UnitKnowledgeBase.usage_count)
    ).limit(limit).all()
    
    results = [
        {
            "uuid": p.uuid,
            "title": p.title,
            "category": p.category,
            "usage_count": p.usage_count,
            "helpful_count": p.helpful_count,
            "helpful_rate": round(float(p.helpful_rate) if p.helpful_rate else 0, 2)
        }
        for p in popular
    ]
    
    return success_response(data=results)


@router.get("/units/{unit_uuid}/categories")
def get_knowledge_categories(
    unit_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单元知识库分类统计
    
    - 返回各分类的知识点数量
    - 用于导航和筛选
    """
    categories = db.query(
        UnitKnowledgeBase.category,
        func.count(UnitKnowledgeBase.id).label('count')
    ).filter(
        UnitKnowledgeBase.unit_uuid == unit_uuid,
        UnitKnowledgeBase.status == 'active',
        UnitKnowledgeBase.category.isnot(None)
    ).group_by(
        UnitKnowledgeBase.category
    ).all()
    
    result = [
        {"category": c.category, "count": c.count}
        for c in categories
    ]
    
    return success_response(data=result)


@router.get("/knowledge/{knowledge_uuid}")
def get_knowledge_detail(
    knowledge_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识点详情
    
    - 返回完整的知识点信息
    - 用于展示参考来源
    """
    knowledge = db.query(UnitKnowledgeBase).filter(
        UnitKnowledgeBase.uuid == knowledge_uuid,
        UnitKnowledgeBase.status == 'active'
    ).first()
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识点不存在")
    
    return success_response(data={
        "uuid": knowledge.uuid,
        "title": knowledge.title,
        "content": knowledge.content,
        "content_type": knowledge.content_type,
        "summary": knowledge.summary,
        "category": knowledge.category,
        "tags": knowledge.tags,
        "source_type": knowledge.source_type,
        "source_url": knowledge.source_url,
        "quality_score": float(knowledge.quality_score) if knowledge.quality_score else 0,
        "usage_count": knowledge.usage_count,
        "helpful_count": knowledge.helpful_count,
        "created_at": knowledge.created_at
    })


# ===== 管理API（仅管理员） =====

@router.post("/knowledge")
def create_knowledge(
    unit_uuid: str,
    title: str,
    content: str,
    category: Optional[str] = None,
    keywords: Optional[str] = None,
    priority: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建知识点
    
    - 仅管理员和教师可用
    - 用于构建单元知识库
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="无权限")
    
    knowledge = UnitKnowledgeBase(
        uuid=str(uuid.uuid4()),
        unit_uuid=unit_uuid,
        title=title,
        content=content,
        category=category,
        keywords=keywords,
        priority=priority,
        status='active',
        created_by=current_user.id
    )
    
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    
    return success_response(
        data={"uuid": knowledge.uuid},
        message="知识点创建成功"
    )


@router.put("/knowledge/{knowledge_uuid}")
def update_knowledge(
    knowledge_uuid: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    keywords: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新知识点
    
    - 仅管理员和教师可用
    """
    # 权限检查
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="无权限")
    
    knowledge = db.query(UnitKnowledgeBase).filter(
        UnitKnowledgeBase.uuid == knowledge_uuid
    ).first()
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识点不存在")
    
    # 更新字段
    if title is not None:
        knowledge.title = title
    if content is not None:
        knowledge.content = content
    if category is not None:
        knowledge.category = category
    if keywords is not None:
        knowledge.keywords = keywords
    if priority is not None:
        knowledge.priority = priority
    if status is not None:
        knowledge.status = status
    
    knowledge.updated_by = current_user.id
    
    db.commit()
    
    return success_response(message="知识点更新成功")


