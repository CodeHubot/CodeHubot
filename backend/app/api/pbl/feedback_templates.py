"""
反馈评语模板管理 API
用于管理作业批改的评语模板
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Table, MetaData, Column, BigInteger, String, Text, Integer, TIMESTAMP
from sqlalchemy.sql import select
from typing import Optional
from pydantic import BaseModel, Field

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...models.admin import Admin
from ...core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class FeedbackTemplateCreate(BaseModel):
    """创建反馈模板请求模型"""
    category: str = Field(..., description="分类: excellent/good/average/need_improve")
    title: str = Field(..., min_length=1, max_length=100, description="模板标题")
    content: str = Field(..., min_length=1, description="模板内容")


class FeedbackTemplateUpdate(BaseModel):
    """更新反馈模板请求模型"""
    category: Optional[str] = Field(None, description="分类")
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="模板标题")
    content: Optional[str] = Field(None, min_length=1, description="模板内容")
    is_active: Optional[bool] = Field(None, description="是否启用")


@router.get("")
def get_feedback_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取评语模板列表
    权限：学校管理员只能查看自己学校的模板
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        return error_response(
            message="您的账号未关联任何学校",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 动态访问评语模板表
        metadata = MetaData()
        feedback_templates = Table(
            'pbl_feedback_templates',
            metadata,
            Column('id', BigInteger, primary_key=True),
            Column('uuid', String(36)),
            Column('school_id', Integer),
            Column('category', String(50)),
            Column('title', String(100)),
            Column('content', Text),
            Column('is_active', Integer),
            Column('created_by', Integer),
            Column('created_at', TIMESTAMP),
            Column('updated_at', TIMESTAMP),
            autoload_with=db.get_bind()
        )
        
        # 构建查询
        query = select(feedback_templates).where(
            feedback_templates.c.school_id == current_admin.school_id,
            feedback_templates.c.is_active == 1
        )
        
        if category:
            query = query.where(feedback_templates.c.category == category)
        
        query = query.order_by(feedback_templates.c.category, feedback_templates.c.id)
        
        # 执行查询
        result = db.execute(query)
        templates = []
        
        for row in result:
            templates.append({
                'id': row.id,
                'uuid': row.uuid,
                'category': row.category,
                'title': row.title,
                'content': row.content,
                'is_active': row.is_active,
                'created_at': row.created_at.isoformat() if row.created_at else None
            })
        
        return success_response(data=templates)
        
    except Exception as e:
        logger.error(f"获取评语模板失败: {str(e)}", exc_info=True)
        return error_response(
            message="获取评语模板失败",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("")
def create_feedback_template(
    template_data: FeedbackTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    创建评语模板
    权限：学校管理员只能为自己学校创建模板
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    try:
        from datetime import datetime
        import uuid as uuid_lib
        
        # 动态访问评语模板表
        metadata = MetaData()
        feedback_templates = Table(
            'pbl_feedback_templates',
            metadata,
            Column('id', BigInteger, primary_key=True),
            Column('uuid', String(36)),
            Column('school_id', Integer),
            Column('category', String(50)),
            Column('title', String(100)),
            Column('content', Text),
            Column('is_active', Integer),
            Column('created_by', Integer),
            Column('created_at', TIMESTAMP),
            Column('updated_at', TIMESTAMP),
            autoload_with=db.get_bind()
        )
        
        # 插入新模板
        insert_stmt = feedback_templates.insert().values(
            uuid=str(uuid_lib.uuid4()),
            school_id=current_admin.school_id,
            category=template_data.category,
            title=template_data.title,
            content=template_data.content,
            is_active=1,
            created_by=current_admin.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.execute(insert_stmt)
        db.commit()
        
        logger.info(
            f"创建评语模板成功 - 标题: {template_data.title}, "
            f"分类: {template_data.category}, 操作者: {current_admin.username}"
        )
        
        return success_response(message="创建成功")
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建评语模板失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建评语模板失败"
        )


@router.put("/{template_id}")
def update_feedback_template(
    template_id: int,
    template_data: FeedbackTemplateUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    更新评语模板
    权限：学校管理员只能更新自己学校的模板
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    try:
        from datetime import datetime
        
        # 动态访问评语模板表
        metadata = MetaData()
        feedback_templates = Table(
            'pbl_feedback_templates',
            metadata,
            Column('id', BigInteger, primary_key=True),
            Column('uuid', String(36)),
            Column('school_id', Integer),
            Column('category', String(50)),
            Column('title', String(100)),
            Column('content', Text),
            Column('is_active', Integer),
            Column('created_by', Integer),
            Column('created_at', TIMESTAMP),
            Column('updated_at', TIMESTAMP),
            autoload_with=db.get_bind()
        )
        
        # 检查模板是否存在且属于当前学校
        select_stmt = select(feedback_templates).where(
            feedback_templates.c.id == template_id,
            feedback_templates.c.school_id == current_admin.school_id
        )
        
        result = db.execute(select_stmt)
        template = result.first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在或无权访问"
            )
        
        # 构建更新数据
        update_data = {'updated_at': datetime.now()}
        
        if template_data.category is not None:
            update_data['category'] = template_data.category
        if template_data.title is not None:
            update_data['title'] = template_data.title
        if template_data.content is not None:
            update_data['content'] = template_data.content
        if template_data.is_active is not None:
            update_data['is_active'] = 1 if template_data.is_active else 0
        
        # 更新模板
        update_stmt = feedback_templates.update().where(
            feedback_templates.c.id == template_id
        ).values(**update_data)
        
        db.execute(update_stmt)
        db.commit()
        
        logger.info(
            f"更新评语模板成功 - ID: {template_id}, 操作者: {current_admin.username}"
        )
        
        return success_response(message="更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新评语模板失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新评语模板失败"
        )


@router.delete("/{template_id}")
def delete_feedback_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    删除评语模板（软删除）
    权限：学校管理员只能删除自己学校的模板
    """
    # 检查管理员是否关联学校
    if not current_admin.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您的账号未关联任何学校"
        )
    
    try:
        from datetime import datetime
        
        # 动态访问评语模板表
        metadata = MetaData()
        feedback_templates = Table(
            'pbl_feedback_templates',
            metadata,
            Column('id', BigInteger, primary_key=True),
            Column('uuid', String(36)),
            Column('school_id', Integer),
            Column('category', String(50)),
            Column('title', String(100)),
            Column('content', Text),
            Column('is_active', Integer),
            Column('created_by', Integer),
            Column('created_at', TIMESTAMP),
            Column('updated_at', TIMESTAMP),
            autoload_with=db.get_bind()
        )
        
        # 检查模板是否存在且属于当前学校
        select_stmt = select(feedback_templates).where(
            feedback_templates.c.id == template_id,
            feedback_templates.c.school_id == current_admin.school_id
        )
        
        result = db.execute(select_stmt)
        template = result.first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在或无权访问"
            )
        
        # 软删除：设置 is_active = 0
        update_stmt = feedback_templates.update().where(
            feedback_templates.c.id == template_id
        ).values(
            is_active=0,
            updated_at=datetime.now()
        )
        
        db.execute(update_stmt)
        db.commit()
        
        logger.info(
            f"删除评语模板成功 - ID: {template_id}, 操作者: {current_admin.username}"
        )
        
        return success_response(message="删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除评语模板失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除评语模板失败"
        )

