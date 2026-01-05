"""
临时附件上传API
用户选择文件后立即上传到临时目录，获取file_token
提交作业时将file_token一起提交，后端统一处理
"""
from fastapi import APIRouter, File, UploadFile, Depends, status
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import os
import logging
from typing import List

from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_user
from ...models.admin import User

router = APIRouter()
logger = logging.getLogger(__name__)

# 临时上传目录
TEMP_UPLOAD_DIR = Path("uploads/temp-attachments")
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 永久存储目录
PERMANENT_UPLOAD_DIR = Path("uploads/task-attachments")
PERMANENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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


@router.post("/upload-temp")
async def upload_temp_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    临时上传附件（不需要progress_id）
    
    工作流程：
    1. 用户选择文件后立即调用此接口
    2. 文件保存到临时目录
    3. 返回file_token（临时文件标识）
    4. 提交作业时将file_token一起提交
    
    Returns:
        {
            "file_token": "uuid-xxx-yyy",
            "filename": "原始文件名.docx",
            "file_type": "word",
            "file_size": 12345
        }
    """
    logger.info(f"用户 {current_user.id} 临时上传附件: {file.filename}")
    
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
    
    # 生成临时文件标识（file_token）
    file_token = str(uuid.uuid4())
    file_ext = get_file_extension(file.filename)
    file_type = get_file_type(file_ext)
    
    # 临时文件名：{user_id}_{file_token}{ext}
    temp_filename = f"{current_user.id}_{file_token}{file_ext}"
    temp_file_path = TEMP_UPLOAD_DIR / temp_filename
    
    # 保存到临时目录
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"临时文件保存成功: {temp_file_path}")
    except Exception as e:
        logger.error(f"保存临时文件失败: {str(e)}", exc_info=True)
        return error_response(
            message=f"文件保存失败: {str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return success_response(
        data={
            'file_token': file_token,
            'filename': file.filename,
            'file_type': file_type,
            'file_ext': file_ext,
            'file_size': file_size
        },
        message="文件上传成功"
    )


@router.delete("/temp/{file_token}")
def delete_temp_attachment(
    file_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除临时附件
    
    场景：用户在提交前移除了某个文件
    """
    logger.info(f"用户 {current_user.id} 删除临时附件: {file_token}")
    
    # 查找并删除临时文件（所有扩展名）
    deleted = False
    for ext in ['.doc', '.docx', '.pdf']:
        temp_filename = f"{current_user.id}_{file_token}{ext}"
        temp_file_path = TEMP_UPLOAD_DIR / temp_filename
        
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
                logger.info(f"临时文件删除成功: {temp_file_path}")
                deleted = True
                break
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")
    
    if not deleted:
        logger.warning(f"临时文件不存在: {file_token}")
    
    return success_response(
        data={'file_token': file_token},
        message="文件删除成功"
    )


def move_temp_to_permanent(user_id: int, file_token: str, file_ext: str) -> str:
    """
    将临时文件移动到永久目录
    
    Args:
        user_id: 用户ID
        file_token: 临时文件标识
        file_ext: 文件扩展名
        
    Returns:
        永久文件名（UUID）
        
    Raises:
        FileNotFoundError: 临时文件不存在
    """
    temp_filename = f"{user_id}_{file_token}{file_ext}"
    temp_file_path = TEMP_UPLOAD_DIR / temp_filename
    
    if not temp_file_path.exists():
        raise FileNotFoundError(f"临时文件不存在: {temp_filename}")
    
    # 生成永久文件名
    permanent_filename = f"{uuid.uuid4()}{file_ext}"
    permanent_file_path = PERMANENT_UPLOAD_DIR / permanent_filename
    
    # 移动文件
    try:
        import shutil
        shutil.move(str(temp_file_path), str(permanent_file_path))
        logger.info(f"文件移动成功: {temp_filename} → {permanent_filename}")
        return permanent_filename
    except Exception as e:
        logger.error(f"文件移动失败: {str(e)}", exc_info=True)
        raise


def cleanup_temp_files(user_id: int, file_tokens: List[str]):
    """
    清理未使用的临时文件
    
    在提交失败或取消时调用
    """
    for file_token in file_tokens:
        for ext in ['.doc', '.docx', '.pdf']:
            temp_filename = f"{user_id}_{file_token}{ext}"
            temp_file_path = TEMP_UPLOAD_DIR / temp_filename
            
            if temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                    logger.info(f"清理临时文件: {temp_filename}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")

