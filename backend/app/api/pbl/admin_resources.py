from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path

from ...db.session import SessionLocal
from ...core.response import success_response, error_response
from ...core.deps import get_db, get_current_admin
from ...models.admin import Admin
from ...models.pbl import PBLResource, PBLUnit
from ...schemas.pbl import ResourceCreate, ResourceUpdate, Resource

router = APIRouter()

def serialize_resource(resource: PBLResource) -> dict:
    """将 Resource 模型转换为字典"""
    return Resource.model_validate(resource).model_dump(mode='json')

def serialize_resources(resources: List[PBLResource]) -> List[dict]:
    """将 Resource 模型列表转换为字典列表"""
    return [serialize_resource(resource) for resource in resources]

# 修复响应模型问题 - 移除response_model，使用success_response包装

# 文件上传配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.md', '.ppt', '.pptx'],
}

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()

def is_allowed_file(filename: str, file_type: str) -> bool:
    """检查文件类型是否允许"""
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS.get(file_type, [])

@router.get("/unit/{unit_uuid}")
def get_resources_by_unit(
    unit_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取学习单元下的所有资料"""
    # 验证单元是否存在
    unit = db.query(PBLUnit).filter(PBLUnit.uuid == unit_uuid).first()
    if not unit:
        return error_response(
            message="学习单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    resources = db.query(PBLResource).filter(PBLResource.unit_id == unit.id).order_by(PBLResource.order).all()
    return success_response(data=serialize_resources(resources))

@router.post("")
def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """创建资料"""
    # 支持通过 unit_id 或 unit_uuid 来创建资源
    unit = None
    if hasattr(resource_data, 'unit_uuid') and resource_data.unit_uuid:
        unit = db.query(PBLUnit).filter(PBLUnit.uuid == resource_data.unit_uuid).first()
    elif hasattr(resource_data, 'unit_id') and resource_data.unit_id:
        unit = db.query(PBLUnit).filter(PBLUnit.id == resource_data.unit_id).first()
    
    if not unit:
        return error_response(
            message="学习单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证资源类型
    if resource_data.type not in ['video', 'document', 'link']:
        return error_response(
            message="无效的资源类型",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    new_resource = PBLResource(
        unit_id=unit.id,
        type=resource_data.type,
        title=resource_data.title,
        description=resource_data.description,
        url=resource_data.url,
        content=resource_data.content,
        duration=resource_data.duration,
        order=resource_data.order or 0,
        video_id=resource_data.video_id,
        video_cover_url=resource_data.video_cover_url
    )
    
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    
    return success_response(data=serialize_resource(new_resource), message="资料创建成功")

@router.post("/upload")
async def upload_resource_file(
    unit_uuid: str,
    file_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """上传资料文件"""
    # 验证单元是否存在
    unit = db.query(PBLUnit).filter(PBLUnit.uuid == unit_uuid).first()
    if not unit:
        return error_response(
            message="学习单元不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 验证文件类型
    if file_type not in ['video', 'document']:
        return error_response(
            message="无效的文件类型",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 检查文件扩展名
    if not is_allowed_file(file.filename, file_type):
        return error_response(
            message=f"不支持的文件格式，允许的格式：{', '.join(ALLOWED_EXTENSIONS[file_type])}",
            code=400,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 生成唯一文件名
    file_ext = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / file_type / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 构建文件URL（相对路径）
        file_url = f"/uploads/{file_type}/{unique_filename}"
        
        return success_response(
            data={
                "filename": file.filename,
                "url": file_url,
                "size": len(content),
                "type": file_type
            },
            message="文件上传成功"
        )
    except Exception as e:
        return error_response(
            message=f"文件上传失败：{str(e)}",
            code=500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{resource_uuid}")
def get_resource(
    resource_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取资料详情"""
    resource = db.query(PBLResource).filter(PBLResource.uuid == resource_uuid).first()
    if not resource:
        return error_response(
            message="资料不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return success_response(data=serialize_resource(resource))

@router.put("/{resource_uuid}")
def update_resource(
    resource_uuid: str,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新资料"""
    resource = db.query(PBLResource).filter(PBLResource.uuid == resource_uuid).first()
    if not resource:
        return error_response(
            message="资料不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 更新字段
    for field, value in resource_data.dict(exclude_unset=True).items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    
    return success_response(data=serialize_resource(resource), message="资料更新成功")

@router.delete("/{resource_uuid}")
def delete_resource(
    resource_uuid: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """删除资料"""
    resource = db.query(PBLResource).filter(PBLResource.uuid == resource_uuid).first()
    if not resource:
        return error_response(
            message="资料不存在",
            code=404,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # 如果资源有文件，删除文件
    if resource.url and resource.url.startswith("/uploads/"):
        file_path = Path(resource.url.lstrip("/"))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass  # 忽略删除文件时的错误
    
    db.delete(resource)
    db.commit()
    
    return success_response(message="资料删除成功")
