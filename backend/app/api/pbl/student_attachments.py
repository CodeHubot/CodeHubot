"""
学生作业附件管理API
支持上传、删除、下载Word和PDF附件
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
from urllib.parse import quote
import uuid
import os
import logging

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_user
from ...models.admin import User
from ...models.pbl import PBLTaskProgress, PBLTaskAttachment
from ...schemas.pbl import TaskAttachment

router = APIRouter()
logger = logging.getLogger(__name__)

# 配置上传目录
UPLOAD_DIR = Path("uploads/task-attachments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'word': ['.doc', '.docx'],
    'pdf': ['.pdf']
}

# 文件大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）"""
    return os.path.splitext(filename)[1].lower()


def get_file_type(ext: str) -> str:
    """根据扩展名判断文件类型"""
    if ext in ALLOWED_EXTENSIONS['word']:
        return 'word'
    elif ext in ALLOWED_EXTENSIONS['pdf']:
        return 'pdf'
    return 'unknown'


def is_allowed_file(filename: str) -> bool:
    """检查文件是否允许上传"""
    ext = get_file_extension(filename)
    all_allowed = ALLOWED_EXTENSIONS['word'] + ALLOWED_EXTENSIONS['pdf']
    return ext in all_allowed


@router.post("/upload")
async def upload_attachment(
    progress_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传作业附件
    
    Args:
        progress_id: 任务进度ID
        file: 上传的文件（Word或PDF）
        
    Returns:
        附件信息
        
    Raises:
        HTTPException: 文件类型不支持、文件过大、权限错误等
    """
    logger.info(f"用户 {current_user.id} 上传附件，进度ID: {progress_id}")
    
    # 验证任务进度是否存在且属于当前用户
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.id == progress_id,
        PBLTaskProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        return error_response(
            message="任务进度不存在或无权访问",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查文件名
    if not file.filename:
        return error_response(
            message="文件名不能为空",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查文件类型
    if not is_allowed_file(file.filename):
        return error_response(
            message="不支持的文件格式，仅支持Word(.doc, .docx)和PDF(.pdf)格式",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 读取文件内容
    try:
        file_content = await file.read()
        file_size = len(file_content)
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"读取文件失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # 检查文件大小
    if file_size > MAX_FILE_SIZE:
        return error_response(
            message=f"文件大小超过限制（最大10MB）",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if file_size == 0:
        return error_response(
            message="文件内容为空",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 生成唯一文件名
    file_ext = get_file_extension(file.filename)
    file_type = get_file_type(file_ext)
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"文件保存成功: {file_path}")
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"文件保存失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # 创建附件记录
    file_url = f"/uploads/task-attachments/{unique_filename}"
    attachment = PBLTaskAttachment(
        progress_id=progress_id,
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=unique_filename,
        file_type=file_type,
        file_ext=file_ext,
        file_size=file_size,
        file_url=file_url
    )
    
    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        logger.info(f"附件记录创建成功 - ID: {attachment.id}, UUID: {attachment.uuid}")
        
        return success_response(
            data={
                'id': attachment.id,
                'uuid': attachment.uuid,
                'filename': attachment.filename,
                'file_type': attachment.file_type,
                'file_ext': attachment.file_ext,
                'file_size': attachment.file_size,
                'file_url': attachment.file_url,
                'created_at': attachment.created_at.isoformat() if attachment.created_at else None
            },
            message="附件上传成功"
        )
    except Exception as e:
        db.rollback()
        # 删除已保存的文件
        if file_path.exists():
            os.remove(file_path)
        logger.error(f"创建附件记录失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"附件上传失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/{attachment_uuid}")
def delete_attachment(
    attachment_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    软删除作业附件（标记为已删除，不物理删除）
    
    Args:
        attachment_uuid: 附件UUID
        
    Returns:
        删除成功消息
        
    Raises:
        HTTPException: 附件不存在或无权删除
        
    Note:
        - 使用软删除，不会真正删除文件和数据库记录
        - 只标记 is_deleted=1 和记录删除时间
        - 保留审计追踪，防止误删除
    """
    from datetime import datetime
    
    logger.info(f"用户 {current_user.id} 软删除附件: {attachment_uuid}")
    
    # 查询附件（包括已删除的）
    attachment = db.query(PBLTaskAttachment).filter(
        PBLTaskAttachment.uuid == attachment_uuid
    ).first()
    
    if not attachment:
        return error_response(
            message="附件不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 检查是否已删除
    if attachment.is_deleted:
        return error_response(
            message="附件已被删除",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查权限（只能删除自己的附件）
    if attachment.user_id != current_user.id:
        return error_response(
            message="无权删除此附件",
            code=403,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # 软删除：标记为已删除，不删除物理文件
    try:
        attachment.is_deleted = 1
        attachment.deleted_at = datetime.now()
        attachment.deleted_by = current_user.id
        
        db.commit()
        logger.info(f"附件软删除成功 - UUID: {attachment_uuid}, 文件保留: {attachment.stored_filename}")
        
        return success_response(
            data={
                'uuid': attachment_uuid,
                'filename': attachment.filename,
                'deleted_at': attachment.deleted_at.isoformat() if attachment.deleted_at else None
            },
            message="附件已删除"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"软删除附件失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"删除附件失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/{attachment_uuid}/download")
def download_attachment(
    attachment_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载作业附件
    
    Args:
        attachment_uuid: 附件UUID
        
    Returns:
        文件下载响应
        
    Raises:
        HTTPException: 附件不存在或文件不存在
    """
    logger.info(f"用户 {current_user.id} 下载附件: {attachment_uuid}")
    
    # 查询附件（只允许下载未删除的附件）
    attachment = db.query(PBLTaskAttachment).filter(
        PBLTaskAttachment.uuid == attachment_uuid,
        PBLTaskAttachment.is_deleted == 0  # 不能下载已删除的附件
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在或已被删除"
        )
    
    # 检查文件是否存在
    file_path = UPLOAD_DIR / attachment.stored_filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 设置Content-Type
    content_type_map = {
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pdf': 'application/pdf'
    }
    content_type = content_type_map.get(attachment.file_ext, 'application/octet-stream')
    
    # URL 编码文件名（支持中文）
    # RFC 5987: filename*=UTF-8''encoded_filename
    encoded_filename = quote(attachment.filename, safe='')
    
    # 返回文件
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=attachment.filename,  # 使用原始文件名（浏览器兼容）
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/progress/{progress_id}")
def get_attachments_by_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定任务进度的所有附件
    
    Args:
        progress_id: 任务进度ID
        
    Returns:
        附件列表
    """
    logger.info(f"用户 {current_user.id} 获取进度 {progress_id} 的附件列表")
    
    # 验证任务进度是否存在且属于当前用户
    progress = db.query(PBLTaskProgress).filter(
        PBLTaskProgress.id == progress_id,
        PBLTaskProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        return error_response(
            message="任务进度不存在或无权访问",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 查询附件列表（只返回未删除的附件）
    attachments = db.query(PBLTaskAttachment).filter(
        PBLTaskAttachment.progress_id == progress_id,
        PBLTaskAttachment.is_deleted == 0  # 只查询未删除的附件
    ).order_by(PBLTaskAttachment.created_at.desc()).all()
    
    result = []
    for attachment in attachments:
        result.append({
            'id': attachment.id,
            'uuid': attachment.uuid,
            'filename': attachment.filename,
            'file_type': attachment.file_type,
            'file_ext': attachment.file_ext,
            'file_size': attachment.file_size,
            'file_url': attachment.file_url,
            'created_at': attachment.created_at.isoformat() if attachment.created_at else None
        })
    
    return success_response(data=result)

