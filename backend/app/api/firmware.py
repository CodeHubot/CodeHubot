from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
import logging
from datetime import datetime
import hashlib
import os
import shutil

from app.core.database import get_db
from app.core.config import settings
from app.models.firmware import Firmware
from app.models.user import User
from app.schemas.firmware import (
    FirmwareCreate, FirmwareUpdate, FirmwareResponse, 
    OTACheckRequest, OTACheckResponse
)
from app.api.auth import get_current_user
from app.core.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


def is_platform_admin(user: User) -> bool:
    """判断用户是否为平台管理员"""
    return user.role == 'platform_admin'


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    返回值: 1 表示 version1 > version2, -1 表示 version1 < version2, 0 表示相等
    """
    def normalize_version(v):
        return [int(x) for x in v.split('.')]
    
    try:
        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)
        
        # 补齐长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        return 0
    except ValueError:
        # 如果版本号格式不正确，按字符串比较
        if version1 > version2:
            return 1
        elif version1 < version2:
            return -1
        return 0

@router.post("/check", response_model=OTACheckResponse)
def check_firmware_update(
    request: OTACheckRequest,
    db: Session = Depends(get_db)
):
    """
    检查固件更新 - 供ESP32设备调用
    """
    logger.info(f"OTA检测请求: 产品={request.product_code}, 产品版本={request.product_version}, 固件版本={request.firmware_version}")
    
    try:
        # 查找该产品的最新激活固件版本（优先使用is_latest标记）
        latest_firmware = db.query(Firmware).filter(
            and_(
                Firmware.product_code == request.product_code,
                Firmware.is_active == True,
                Firmware.is_latest == True
            )
        ).first()
        
        # 如果没有标记为最新的版本，则按创建时间查找最新的
        if not latest_firmware:
            latest_firmware = db.query(Firmware).filter(
                and_(
                    Firmware.product_code == request.product_code,
                    Firmware.is_active == True
                )
            ).order_by(desc(Firmware.created_at)).first()
        
        if not latest_firmware:
            logger.warning(f"未找到产品 {request.product_code} 的固件版本")
            return OTACheckResponse(
                has_update=False,
                firmware_url=None,
                latest_version=None
            )
        
        # 比较版本号
        version_comparison = compare_versions(latest_firmware.version, request.firmware_version)
        
        if version_comparison > 0:
            # 有新版本
            logger.info(f"发现新版本: {latest_firmware.version} > {request.firmware_version}")
            return OTACheckResponse(
                has_update=True,
                firmware_url=latest_firmware.firmware_url,
                latest_version=latest_firmware.version,
                file_size=latest_firmware.file_size,
                file_hash=latest_firmware.file_hash,
                description=latest_firmware.description,
                release_notes=latest_firmware.release_notes
            )
        else:
            # 没有新版本
            logger.info(f"当前版本已是最新: {request.firmware_version}")
            return OTACheckResponse(
                has_update=False,
                firmware_url=None,
                latest_version=latest_firmware.version
            )
            
    except Exception as e:
        logger.error(f"OTA检测失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTA检测失败: {str(e)}"
        )

@router.post("/upload", response_model=FirmwareResponse, summary="上传固件文件")
async def upload_firmware(
    file: UploadFile = File(...),
    product_code: str = None,
    version: str = None,
    description: str = None,
    release_notes: str = None,
    is_latest: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传固件文件并创建固件记录
    权限：仅平台管理员
    """
    # 权限检查：只有平台管理员可以上传固件
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以上传固件"
        )
    
    try:
        # 验证文件类型
        if not file.filename.endswith('.bin'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持 .bin 格式的固件文件"
            )
        
        # 创建上传目录
        upload_dir = os.path.join("static", "firmware")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{product_code}_{version}_{timestamp}.bin" if product_code and version else f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 计算文件哈希
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 如果设置为最新版本，先将其他版本设为非最新
        if is_latest and product_code:
            db.query(Firmware).filter(
                Firmware.product_code == product_code
            ).update({"is_latest": False})
        
        # 创建固件记录
        firmware_data = {
            "product_code": product_code or "UNKNOWN",
            "version": version or "1.0.0",
            "firmware_url": f"{settings.get_firmware_base_url}/static/firmware/{filename}",
            "file_size": file_size,
            "file_hash": file_hash,
            "description": description or f"固件文件 {filename}",
            "release_notes": release_notes,
            "is_active": True,
            "is_latest": is_latest
        }
        
        logger.info(f"固件URL生成: {firmware_data['firmware_url']}")
        
        db_firmware = Firmware(**firmware_data)
        db.add(db_firmware)
        db.commit()
        db.refresh(db_firmware)
        
        return db_firmware
        
    except Exception as e:
        # 如果出错，删除已上传的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        logger.error(f"上传固件文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传固件文件失败: {str(e)}"
        )

@router.post("/", response_model=FirmwareResponse, summary="创建固件版本")
def create_firmware(
    firmware: FirmwareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建固件版本
    权限：仅平台管理员
    """
    # 权限检查：只有平台管理员可以创建固件
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以创建固件版本"
        )
    
    try:
        # 检查是否已存在相同产品和版本的固件
        existing_firmware = db.query(Firmware).filter(
            and_(
                Firmware.product_code == firmware.product_code,
                Firmware.version == firmware.version
            )
        ).first()
        
        if existing_firmware:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"产品 {firmware.product_code} 的版本 {firmware.version} 已存在"
            )
        
        # 如果设置为最新版本，需要将其他版本的is_latest设为False
        if firmware.is_latest:
            db.query(Firmware).filter(
                Firmware.product_code == firmware.product_code
            ).update({"is_latest": False})
        
        # 创建新固件记录
        db_firmware = Firmware(**firmware.dict())
        db.add(db_firmware)
        db.commit()
        db.refresh(db_firmware)
        
        logger.info(f"创建固件版本成功: {firmware.product_code} v{firmware.version}")
        return db_firmware
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建固件版本失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建固件版本失败: {str(e)}"
        )

@router.get("/", response_model=List[FirmwareResponse])
def get_firmware_list(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    product_code: Optional[str] = Query(None, description="产品代号筛选"),
    is_active: Optional[bool] = Query(None, description="激活状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取固件版本列表"""
    try:
        query = db.query(Firmware)
        
        if product_code:
            query = query.filter(Firmware.product_code == product_code)
        
        if is_active is not None:
            query = query.filter(Firmware.is_active == is_active)
        
        firmware_list = query.order_by(desc(Firmware.created_at)).offset(skip).limit(limit).all()
        
        return firmware_list
        
    except Exception as e:
        logger.error(f"获取固件列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取固件列表失败: {str(e)}"
        )

@router.get("/{firmware_id}", response_model=FirmwareResponse)
def get_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定固件版本信息"""
    firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
    
    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="固件版本不存在"
        )
    
    return firmware

@router.put("/{firmware_id}", response_model=FirmwareResponse)
def update_firmware(
    firmware_id: int,
    firmware_update: FirmwareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新固件版本信息
    权限：仅平台管理员
    """
    # 权限检查：只有平台管理员可以更新固件
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以更新固件版本"
        )
    
    try:
        firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
        
        if not firmware:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="固件版本不存在"
            )
        
        # 如果设置为最新版本，需要将其他版本的is_latest设为False
        if firmware_update.is_latest:
            db.query(Firmware).filter(
                and_(
                    Firmware.product_code == firmware.product_code,
                    Firmware.id != firmware_id
                )
            ).update({"is_latest": False})
        
        # 更新固件信息
        update_data = firmware_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            for key, value in update_data.items():
                setattr(firmware, key, value)
        
        db.commit()
        db.refresh(firmware)
        
        logger.info(f"更新固件版本成功: ID={firmware_id}")
        return firmware
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新固件版本失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新固件版本失败: {str(e)}"
        )

@router.delete("/{firmware_id}")
def delete_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除固件版本
    权限：仅平台管理员
    """
    # 权限检查：只有平台管理员可以删除固件
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有平台管理员可以删除固件版本"
        )
    
    try:
        firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
        
        if not firmware:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="固件版本不存在"
            )
        
        db.delete(firmware)
        db.commit()
        
        logger.info(f"删除固件版本成功: ID={firmware_id}")
        return success_response(message="固件版本删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除固件版本失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除固件版本失败: {str(e)}"
        )