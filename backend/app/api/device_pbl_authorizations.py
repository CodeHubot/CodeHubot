"""
PBL小组设备授权API
用于教师将设备授权给班级小组
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import uuid as uuid_lib
import logging

from app.core.database import get_db
from app.models.device import Device
from app.models.user import User
from app.models.pbl_group_device_authorization import PBLGroupDeviceAuthorization
from app.schemas.pbl_group_device_authorization import (
    PBLGroupDeviceAuthorizationCreate,
    PBLGroupDeviceAuthorizationUpdate,
    PBLGroupDeviceAuthorizationResponse,
    PBLGroupDeviceAuthorizationListResponse,
    PBLGroupDeviceAuthorizationBatchResponse,
    PBLAuthorizableGroupResponse,
    PBLAuthorizableGroupsResponse,
    PBLGroupDeviceAuthorizationRevokeRequest
)
from app.api.auth import get_current_user
from app.core.constants import ErrorMessages, SuccessMessages

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["设备PBL授权"])


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员"""
    return user.email == "admin@aiot.com" or user.username == "admin"


@router.post("/{device_uuid}/pbl-authorizations", response_model=PBLGroupDeviceAuthorizationBatchResponse)
async def create_pbl_device_authorizations(
    device_uuid: str,
    auth_data: PBLGroupDeviceAuthorizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """授权设备给多个小组（批量）"""
    # 权限检查：只有管理员和教师可以授权设备
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以授权设备"
        )
    
    # 查询设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 检查设备所有权（教师只能授权自己注册的设备）
    if current_user.role == 'teacher':
        if device.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能授权自己注册的设备"
            )
    
    # 验证小组（从PBL表直接查询）
    # 1. 查询教师所在的班级
    teacher_classes = db.execute(text("""
        SELECT class_id FROM pbl_class_teachers 
        WHERE teacher_id = :teacher_id
    """), {"teacher_id": current_user.id}).fetchall()
    
    if not teacher_classes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不是任何班级的教师，无法授权设备"
        )
    
    class_ids = [c[0] for c in teacher_classes]
    
    # 2. 查询这些班级的课程
    courses = db.execute(text("""
        SELECT id FROM pbl_courses 
        WHERE class_id IN :class_ids
    """), {"class_ids": tuple(class_ids)}).fetchall()
    
    course_ids = [c[0] for c in courses] if courses else []
    
    if not course_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您所在的班级没有课程，无法授权设备"
        )
    
    # 3. 验证小组是否属于这些课程
    valid_groups = db.execute(text("""
        SELECT id, name FROM pbl_groups 
        WHERE id IN :group_ids 
          AND course_id IN :course_ids
          AND is_active = 1
    """), {
        "group_ids": tuple(auth_data.group_ids),
        "course_ids": tuple(course_ids)
    }).fetchall()
    
    valid_group_ids = [g[0] for g in valid_groups]
    
    if len(valid_group_ids) != len(auth_data.group_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分小组不属于您授课的课程或不存在"
        )
    
    # 4. 检查设备是否属于本校
    if device.school_id != current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能授权本校设备"
        )
    
    # 5. 批量创建授权记录
    created_authorizations = []
    success_count = 0
    failed_count = 0
    
    for group_id in valid_group_ids:
        # 检查是否已存在授权
        existing = db.query(PBLGroupDeviceAuthorization).filter(
            PBLGroupDeviceAuthorization.group_id == group_id,
            PBLGroupDeviceAuthorization.device_id == device.id
        ).first()
        
        if existing:
            # 如果已存在，更新授权信息
            existing.expires_at = auth_data.expires_at
            existing.notes = auth_data.notes
            existing.is_active = True
            existing.updated_at = datetime.now()
            created_authorizations.append(existing)
            success_count += 1
        else:
            # 创建新授权
            authorization = PBLGroupDeviceAuthorization(
                group_id=group_id,
                device_id=device.id,
                authorized_by=current_user.id,
                expires_at=auth_data.expires_at,
                notes=auth_data.notes
            )
            db.add(authorization)
            created_authorizations.append(authorization)
            success_count += 1
    
    db.commit()
    
    # 刷新对象以获取关联数据
    for auth in created_authorizations:
        db.refresh(auth)
    
    # 构造响应数据
    auth_responses = []
    for auth in created_authorizations:
        # 查询小组信息
        group_info = db.execute(text("""
            SELECT g.name, g.course_id, c.title as course_name, 
                   c.class_id, cl.name as class_name
            FROM pbl_groups g
            JOIN pbl_courses c ON g.course_id = c.id
            JOIN pbl_classes cl ON c.class_id = cl.id
            WHERE g.id = :group_id
        """), {"group_id": auth.group_id}).fetchone()
        
        is_expired = False
        if auth.expires_at:
            is_expired = auth.expires_at < datetime.now()
        
        auth_responses.append(PBLGroupDeviceAuthorizationResponse(
            id=auth.id,
            uuid=auth.uuid,
            group_id=auth.group_id,
            group_name=group_info[0] if group_info else None,
            device_id=auth.device_id,
            device_name=device.name,
            device_uuid=device.uuid,
            authorized_by=auth.authorized_by,
            authorized_by_name=current_user.username,
            authorized_at=auth.authorized_at,
            expires_at=auth.expires_at,
            is_active=auth.is_active,
            notes=auth.notes,
            is_expired=is_expired,
            created_at=auth.created_at,
            updated_at=auth.updated_at
        ))
    
    return PBLGroupDeviceAuthorizationBatchResponse(
        total=len(auth_data.group_ids),
        success=success_count,
        failed=failed_count,
        authorizations=auth_responses
    )


@router.get("/{device_uuid}/pbl-authorizations", response_model=PBLGroupDeviceAuthorizationListResponse)
async def get_pbl_device_authorizations(
    device_uuid: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否只显示有效授权"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询设备已授权的小组"""
    # 查询设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限检查：只有设备所有者或管理员可以查看授权列表
    if current_user.role == 'teacher' and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己设备的授权列表"
        )
    
    # 查询授权记录
    query = db.query(PBLGroupDeviceAuthorization).filter(
        PBLGroupDeviceAuthorization.device_id == device.id
    )
    
    if is_active is not None:
        query = query.filter(PBLGroupDeviceAuthorization.is_active == is_active)
    
    # 分页
    total = query.count()
    authorizations = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 构造响应数据
    auth_responses = []
    for auth in authorizations:
        # 查询小组信息
        group_info = db.execute(text("""
            SELECT g.name, g.course_id, c.title as course_name, 
                   c.class_id, cl.name as class_name
            FROM pbl_groups g
            JOIN pbl_courses c ON g.course_id = c.id
            JOIN pbl_classes cl ON c.class_id = cl.id
            WHERE g.id = :group_id
        """), {"group_id": auth.group_id}).fetchone()
        
        # 查询授权人信息
        authorizer = db.query(User).filter(User.id == auth.authorized_by).first()
        
        is_expired = False
        if auth.expires_at:
            is_expired = auth.expires_at < datetime.now()
        
        auth_responses.append(PBLGroupDeviceAuthorizationResponse(
            id=auth.id,
            uuid=auth.uuid,
            group_id=auth.group_id,
            group_name=group_info[0] if group_info else None,
            device_id=auth.device_id,
            device_name=device.name,
            device_uuid=device.uuid,
            authorized_by=auth.authorized_by,
            authorized_by_name=authorizer.username if authorizer else None,
            authorized_at=auth.authorized_at,
            expires_at=auth.expires_at,
            is_active=auth.is_active,
            notes=auth.notes,
            is_expired=is_expired,
            created_at=auth.created_at,
            updated_at=auth.updated_at
        ))
    
    return PBLGroupDeviceAuthorizationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        authorizations=auth_responses
    )


@router.delete("/{device_uuid}/pbl-authorizations/{auth_id}")
async def revoke_pbl_device_authorization(
    device_uuid: str,
    auth_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤销单个授权"""
    # 查询设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 查询授权记录
    authorization = db.query(PBLGroupDeviceAuthorization).filter(
        PBLGroupDeviceAuthorization.id == auth_id,
        PBLGroupDeviceAuthorization.device_id == device.id
    ).first()
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="授权记录不存在"
        )
    
    # 权限检查：只有设备所有者或管理员可以撤销授权
    if current_user.role == 'teacher' and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能撤销自己设备的授权"
        )
    
    # 删除授权记录
    db.delete(authorization)
    db.commit()
    
    return {"message": "授权已撤销"}


@router.delete("/{device_uuid}/pbl-authorizations")
async def revoke_pbl_device_authorizations_batch(
    device_uuid: str,
    revoke_data: PBLGroupDeviceAuthorizationRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量撤销授权"""
    # 查询设备
    device = db.query(Device).filter(Device.uuid == device_uuid).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限检查：只有设备所有者或管理员可以撤销授权
    if current_user.role == 'teacher' and device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能撤销自己设备的授权"
        )
    
    # 查询授权记录
    query = db.query(PBLGroupDeviceAuthorization).filter(
        PBLGroupDeviceAuthorization.device_id == device.id
    )
    
    if revoke_data.group_ids:
        query = query.filter(
            PBLGroupDeviceAuthorization.group_id.in_(revoke_data.group_ids)
        )
    
    authorizations = query.all()
    
    # 删除授权记录
    for auth in authorizations:
        db.delete(auth)
    
    db.commit()
    
    return {"message": f"已撤销 {len(authorizations)} 个授权"}


@router.get("/authorizable-groups", response_model=PBLAuthorizableGroupsResponse)
async def get_authorizable_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询教师可授权的小组列表（用于前端选择）"""
    # 权限检查：只有管理员和教师可以查询
    if current_user.role not in ['platform_admin', 'school_admin', 'teacher']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查询可授权的小组"
        )
    
    # 查询教师所在的班级（从PBL表直接查询）
    teacher_classes = db.execute(text("""
        SELECT ct.class_id, c.name as class_name
        FROM pbl_class_teachers ct
        JOIN pbl_classes c ON ct.class_id = c.id
        WHERE ct.teacher_id = :teacher_id
          AND c.is_active = 1
    """), {"teacher_id": current_user.id}).fetchall()
    
    if not teacher_classes:
        return PBLAuthorizableGroupsResponse(classes=[])
    
    class_ids = [c[0] for c in teacher_classes]
    
    # 查询这些班级的课程
    courses = db.execute(text("""
        SELECT id, title, class_id FROM pbl_courses 
        WHERE class_id IN :class_ids
    """), {"class_ids": tuple(class_ids)}).fetchall()
    
    course_ids = [c[0] for c in courses] if courses else []
    
    if not course_ids:
        return PBLAuthorizableGroupsResponse(classes=[])
    
    # 查询这些课程的小组
    groups = db.execute(text("""
        SELECT g.id, g.name, g.course_id, 
               COUNT(gm.id) as member_count
        FROM pbl_groups g
        LEFT JOIN pbl_group_members gm ON g.id = gm.group_id AND gm.is_active = 1
        WHERE g.course_id IN :course_ids
          AND g.is_active = 1
        GROUP BY g.id, g.name, g.course_id
        ORDER BY g.course_id, g.id
    """), {"course_ids": tuple(course_ids)}).fetchall()
    
    # 组装数据：班级 -> 课程 -> 小组
    classes_dict = {}
    for class_id, class_name in teacher_classes:
        if class_id not in classes_dict:
            classes_dict[class_id] = {
                "class_id": class_id,
                "class_name": class_name,
                "courses": {}
            }
    
    for course_id, course_title, course_class_id in courses:
        if course_class_id in classes_dict:
            classes_dict[course_class_id]["courses"][course_id] = {
                "course_id": course_id,
                "course_name": course_title,
                "groups": []
            }
    
    for group_id, group_name, group_course_id, member_count in groups:
        for class_data in classes_dict.values():
            if group_course_id in class_data["courses"]:
                class_data["courses"][group_course_id]["groups"].append({
                    "group_id": group_id,
                    "group_name": group_name,
                    "member_count": member_count
                })
    
    # 转换为列表格式
    classes_list = []
    for class_data in classes_dict.values():
        courses_list = []
        for course_data in class_data["courses"].values():
            courses_list.append(course_data)
        classes_list.append({
            "class_id": class_data["class_id"],
            "class_name": class_data["class_name"],
            "courses": courses_list
        })
    
    return PBLAuthorizableGroupsResponse(classes=classes_list)
