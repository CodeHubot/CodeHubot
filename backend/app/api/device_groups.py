"""
设备分组管理API
提供设备分组的CRUD操作和设备成员管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.api.auth import get_current_user
from app.models.user import User
from app.models.school import School
from app.models.device import Device
from app.models.device_group import DeviceGroup, DeviceGroupMember
from app.schemas.device_group import (
    DeviceGroupCreate, DeviceGroupUpdate, DeviceGroupResponse, DeviceGroupListResponse,
    DeviceGroupMemberAdd, DeviceGroupMemberBatchAdd, DeviceGroupMemberResponse
)
from app.utils.timezone import get_beijing_time_naive

router = APIRouter(prefix="/device-groups", tags=["设备分组管理"])

# ============================================================================
# 权限检查函数
# ============================================================================

def check_school_admin(current_user: User = Depends(get_current_user)):
    """检查当前用户是否为学校管理员"""
    if current_user.role not in ['platform_admin', 'school_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学校管理员才能执行此操作"
        )
    return current_user


# ============================================================================
# 设备分组管理 APIs
# ============================================================================

@router.post("", response_model=dict)
async def create_device_group(
    group_data: DeviceGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """创建设备组"""
    school_id = current_user.school_id
    
    # 检查设备组名称是否重复
    existing = db.query(DeviceGroup).filter(
        DeviceGroup.school_id == school_id,
        DeviceGroup.group_name == group_data.group_name,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if existing:
        return error_response(message="设备组名称已存在", code=400)
    
    # 创建设备组
    device_group = DeviceGroup(
        school_id=school_id,
        group_name=group_data.group_name,
        group_code=group_data.group_code,
        description=group_data.description,
        created_by=current_user.id,
        is_active=True
    )
    
    db.add(device_group)
    db.commit()
    db.refresh(device_group)
    
    return success_response(
        data=DeviceGroupResponse.from_orm(device_group).model_dump(),
        message="设备组创建成功"
    )


@router.get("", response_model=dict)
async def list_device_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备组列表"""
    # 权限控制：只能看到本校的设备组
    school_id = current_user.school_id
    if not school_id:
        return success_response(data={
            "total": 0,
            "page": page,
            "page_size": page_size,
            "device_groups": []
        })
    
    # 构建查询
    query = db.query(DeviceGroup).filter(
        DeviceGroup.school_id == school_id,
        DeviceGroup.deleted_at.is_(None)
    )
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                DeviceGroup.group_name.like(f"%{keyword}%"),
                DeviceGroup.group_code.like(f"%{keyword}%")
            )
        )
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(DeviceGroup.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    device_groups = query.order_by(DeviceGroup.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式，并实时统计设备数量
    group_list = []
    for g in device_groups:
        # 实时统计该设备组的设备数量（只统计未离开的设备）
        actual_device_count = db.query(func.count(DeviceGroupMember.id)).filter(
            DeviceGroupMember.group_id == g.id,
            DeviceGroupMember.left_at.is_(None)
        ).scalar() or 0
        
        group_data = DeviceGroupListResponse.from_orm(g).model_dump()
        group_data['device_count'] = actual_device_count  # 使用实时统计的数量
        group_list.append(group_data)
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "device_groups": group_list
    })


@router.get("/{group_uuid}", response_model=dict)
async def get_device_group(
    group_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备组详情"""
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权查看该设备组", code=403)
    
    # 实时统计设备数量
    actual_device_count = db.query(func.count(DeviceGroupMember.id)).filter(
        DeviceGroupMember.group_id == device_group.id,
        DeviceGroupMember.left_at.is_(None)
    ).scalar() or 0
    
    group_data = DeviceGroupResponse.from_orm(device_group).model_dump()
    group_data['device_count'] = actual_device_count  # 使用实时统计的数量
    
    return success_response(data=group_data)


@router.put("/{group_uuid}", response_model=dict)
async def update_device_group(
    group_uuid: str,
    group_data: DeviceGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """更新设备组信息"""
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权修改该设备组", code=403)
    
    # 更新字段
    if group_data.group_name is not None:
        device_group.group_name = group_data.group_name
    if group_data.group_code is not None:
        device_group.group_code = group_data.group_code
    if group_data.description is not None:
        device_group.description = group_data.description
    if group_data.is_active is not None:
        device_group.is_active = group_data.is_active
    
    device_group.updated_at = get_beijing_time_naive()
    db.commit()
    db.refresh(device_group)
    
    return success_response(
        data=DeviceGroupResponse.from_orm(device_group).model_dump(),
        message="设备组更新成功"
    )


@router.delete("/{group_uuid}", response_model=dict)
async def delete_device_group(
    group_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """删除设备组（软删除）"""
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权删除该设备组", code=403)
    
    # 软删除
    device_group.deleted_at = get_beijing_time_naive()
    db.commit()
    
    return success_response(message="设备组删除成功")


# ============================================================================
# 设备组成员管理 APIs
# ============================================================================

@router.post("/{group_uuid}/devices", response_model=dict)
async def add_device_to_group(
    group_uuid: str,
    device_data: DeviceGroupMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """添加设备到设备组"""
    # 查找设备组
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权操作该设备组", code=403)
    
    # 检查设备是否存在
    device = db.query(Device).filter(
        Device.id == device_data.device_id
    ).first()
    
    if not device:
        return error_response(message="设备不存在", code=404)
    
    # 检查设备是否明确归属于本校
    if device.school_id != device_group.school_id:
        return error_response(message="该设备未归属于本校，请先在设备管理中设置为学校设备", code=403)
    
    # 检查设备是否已在其他设备组中（一个设备只能属于一个设备组）
    existing_membership = db.query(DeviceGroupMember).join(
        DeviceGroup, DeviceGroupMember.group_id == DeviceGroup.id
    ).filter(
        DeviceGroupMember.device_id == device_data.device_id,
        DeviceGroupMember.left_at.is_(None)  # 只检查未离开的记录
    ).first()
    
    if existing_membership:
        existing_group = db.query(DeviceGroup).filter(
            DeviceGroup.id == existing_membership.group_id
        ).first()
        
        if existing_membership.group_id == device_group.id:
            return error_response(message="设备已在该组中", code=400)
        else:
            return error_response(
                message=f'该设备已在设备组"{existing_group.group_name}"中，一个设备只能属于一个设备组，请先从原设备组移除',
                code=400
            )
    
    # 添加设备到组
    member = DeviceGroupMember(
        group_id=device_group.id,
        device_id=device_data.device_id
    )
    
    db.add(member)
    db.commit()
    
    return success_response(message="设备添加成功")


@router.post("/{group_uuid}/devices/batch", response_model=dict)
async def batch_add_devices_to_group(
    group_uuid: str,
    batch_data: DeviceGroupMemberBatchAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """批量添加设备到设备组"""
    # 查找设备组
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权操作该设备组", code=403)
    
    # 批量添加
    added_count = 0
    skipped_count = 0
    skipped_reasons = []
    
    for device_id in batch_data.device_ids:
        # 检查设备是否存在
        device = db.query(Device).filter(
            Device.id == device_id
        ).first()
        
        if not device:
            skipped_count += 1
            skipped_reasons.append(f"设备ID {device_id}: 设备不存在")
            continue
        
        # 检查设备是否明确归属于本校
        if device.school_id != device_group.school_id:
            skipped_count += 1
            skipped_reasons.append(f'设备"{device.name}": 未归属于本校')
            continue
        
        # 检查设备是否已在任何设备组中（一个设备只能属于一个设备组）
        existing_membership = db.query(DeviceGroupMember).filter(
            DeviceGroupMember.device_id == device_id,
            DeviceGroupMember.left_at.is_(None)
        ).first()
        
        if existing_membership:
            if existing_membership.group_id == device_group.id:
                skipped_count += 1
                skipped_reasons.append(f'设备"{device.name}": 已在当前设备组中')
            else:
                existing_group = db.query(DeviceGroup).filter(
                    DeviceGroup.id == existing_membership.group_id
                ).first()
                skipped_count += 1
                skipped_reasons.append(f'设备"{device.name}": 已在设备组"{existing_group.group_name}"中')
            continue
        
        # 添加到组
        member = DeviceGroupMember(
            group_id=device_group.id,
            device_id=device_id
        )
        db.add(member)
        added_count += 1
    
    db.commit()
    
    result_data = {
        "added": added_count,
        "skipped": skipped_count
    }
    
    # 如果有跳过的设备，添加原因说明
    if skipped_reasons:
        result_data["skipped_reasons"] = skipped_reasons[:10]  # 最多返回10条原因
    
    message = f"批量添加完成，成功{added_count}个，跳过{skipped_count}个"
    if skipped_count > 0:
        message += "（部分设备已在其他设备组中）"
    
    return success_response(data=result_data, message=message)


@router.get("/{group_uuid}/devices", response_model=dict)
async def list_group_devices(
    group_uuid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备组的设备列表"""
    # 查找设备组
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权查看该设备组", code=403)
    
    # 查询设备列表
    query = db.query(DeviceGroupMember, Device).join(
        Device, DeviceGroupMember.device_id == Device.id
    ).filter(
        DeviceGroupMember.group_id == device_group.id,
        DeviceGroupMember.left_at.is_(None)
    )
    
    # 总数
    total = query.count()
    
    # 分页
    members = query.order_by(DeviceGroupMember.joined_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # 转换为响应格式
    device_list = []
    for member, device in members:
        device_list.append({
            "id": member.id,
            "group_id": device_group.id,
            "device_id": device.id,
            "device_name": device.name,
            "device_mac": device.mac_address or "",  # MAC地址，空值处理
            "device_status": device.device_status,
            "is_online": device.is_online,
            "joined_at": member.joined_at
        })
    
    return success_response(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "devices": device_list
    })


@router.delete("/{group_uuid}/devices/{device_id}", response_model=dict)
async def remove_device_from_group(
    group_uuid: str,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_school_admin)
):
    """从设备组移除设备"""
    # 查找设备组
    device_group = db.query(DeviceGroup).filter(
        DeviceGroup.uuid == group_uuid,
        DeviceGroup.deleted_at.is_(None)
    ).first()
    
    if not device_group:
        return error_response(message="设备组不存在", code=404)
    
    # 权限检查
    if current_user.school_id != device_group.school_id:
        return error_response(message="无权操作该设备组", code=403)
    
    # 查找成员记录
    member = db.query(DeviceGroupMember).filter(
        DeviceGroupMember.group_id == device_group.id,
        DeviceGroupMember.device_id == device_id,
        DeviceGroupMember.left_at.is_(None)
    ).first()
    
    if not member:
        return error_response(message="设备不在该组中", code=400)
    
    # 标记离开时间
    member.left_at = get_beijing_time_naive()
    
    db.commit()
    
    return success_response(message="设备移除成功")

