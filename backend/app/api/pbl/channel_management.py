"""
渠道管理API - 供渠道管理员使用
管理渠道商账号和学校分配关系
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from pydantic import BaseModel, Field
import logging

from ...core.deps import get_db, get_current_channel_manager
from ...core.response import success_response, error_response
from ...core.security import get_password_hash
from ...models.admin import Admin
from ...models.pbl import ChannelSchoolRelation, PBLCourse
from ...models.user import User
from ...schemas.user import UserResponse
from ...utils.timezone import get_beijing_time_naive

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schemas ====================

class ChannelPartnerCreate(BaseModel):
    """创建渠道商请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    name: str = Field(..., max_length=100, description="渠道商名称")
    company_name: Optional[str] = Field(None, max_length=200, description="公司名称")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")


class ChannelPartnerUpdate(BaseModel):
    """更新渠道商信息"""
    name: Optional[str] = Field(None, max_length=100, description="渠道商名称")
    company_name: Optional[str] = Field(None, max_length=200, description="公司名称")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")
    is_active: Optional[bool] = Field(None, description="是否启用")


class AssignSchoolRequest(BaseModel):
    """分配学校请求"""
    channel_partner_uuid: str = Field(..., description="渠道商UUID")
    school_uuids: List[str] = Field(..., description="学校UUID列表")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, description="新密码")


class SchoolCreate(BaseModel):
    """创建学校请求"""
    school_code: str = Field(..., min_length=2, max_length=50, description="学校代码（如 BJ-YCZX）")
    school_name: str = Field(..., min_length=2, max_length=200, description="学校名称")
    province: Optional[str] = Field(None, max_length=50, description="省份")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    district: Optional[str] = Field(None, max_length=50, description="区/县")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    max_teachers: int = Field(100, description="最大教师数")
    max_students: int = Field(1000, description="最大学生数")
    max_devices: int = Field(500, description="最大设备数")
    license_expire_at: Optional[str] = Field(None, description="授权到期时间（YYYY-MM-DD）")


# ==================== API Endpoints ====================

@router.get("/partners")
def get_channel_partners(
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """获取所有渠道商列表（含统计数据）"""
    # 查询所有渠道商
    partners = db.query(Admin).filter(
        Admin.role == 'channel_partner'
    ).all()
    
    result = []
    for partner in partners:
        # 统计该渠道商负责的学校数量
        school_count = db.query(func.count(ChannelSchoolRelation.id)).filter(
            ChannelSchoolRelation.channel_partner_id == partner.id,
            ChannelSchoolRelation.is_active == 1
        ).scalar()
        
        # 统计课程数（通过关联学校）
        course_count = db.query(func.count(PBLCourse.id)).join(
            ChannelSchoolRelation,
            ChannelSchoolRelation.school_id == PBLCourse.school_id
        ).filter(
            ChannelSchoolRelation.channel_partner_id == partner.id,
            ChannelSchoolRelation.is_active == 1
        ).scalar()
        
        partner_data = UserResponse.model_validate(partner).model_dump(mode='json')
        partner_data.update({
            'school_count': school_count or 0,
            'course_count': course_count or 0
        })
        result.append(partner_data)
    
    logger.info(f"返回 {len(result)} 个渠道商")
    return success_response(data=result)


@router.post("/partners")
def create_channel_partner(
    partner_data: ChannelPartnerCreate,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """创建渠道商账号"""
    logger.info(f"渠道管理员 {current_manager.username} 创建渠道商: {partner_data.username}")
    
    # 检查用户名是否已存在
    existing_user = db.query(Admin).filter(Admin.username == partner_data.username).first()
    if existing_user:
        logger.warning(f"用户名 {partner_data.username} 已存在")
        return error_response(message="用户名已存在", code=400)
    
    # 检查邮箱是否已存在（如果提供）
    if partner_data.email:
        existing_email = db.query(Admin).filter(Admin.email == partner_data.email).first()
        if existing_email:
            logger.warning(f"邮箱 {partner_data.email} 已存在")
            return error_response(message="邮箱已被使用", code=400)
    
    # 创建渠道商账号
    new_partner = Admin(
        username=partner_data.username,
        password_hash=get_password_hash(partner_data.password),
        name=partner_data.name,
        company_name=partner_data.company_name,
        phone=partner_data.phone,
        email=partner_data.email,
        role='channel_partner',
        is_active=True,
        created_at=get_beijing_time_naive(),
        updated_at=get_beijing_time_naive()
    )
    
    db.add(new_partner)
    db.commit()
    db.refresh(new_partner)
    
    logger.info(f"✅ 渠道商创建成功: {new_partner.username} (ID: {new_partner.id})")
    
    partner_response = UserResponse.model_validate(new_partner)
    return success_response(
        data=partner_response.model_dump(mode='json'),
        message="渠道商创建成功"
    )


@router.get("/partners/{partner_uuid}")
def get_channel_partner_detail(
    partner_uuid: str,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """获取渠道商详情（含负责的学校列表）"""
    # 查询渠道商
    partner = db.query(Admin).filter(
        Admin.uuid == partner_uuid,
        Admin.role == 'channel_partner'
    ).first()
    
    if not partner:
        return error_response(message="渠道商不存在", code=404)
    
    # 查询负责的学校
    from ...models.school import School
    relations = db.query(
        ChannelSchoolRelation.id,
        ChannelSchoolRelation.school_id,
        School.uuid.label('school_uuid'),
        School.school_name.label('school_name'),
        ChannelSchoolRelation.is_active,
        ChannelSchoolRelation.created_at
    ).join(
        School, School.id == ChannelSchoolRelation.school_id
    ).filter(
        ChannelSchoolRelation.channel_partner_id == partner.id
    ).all()
    
    schools = [
        {
            'relation_id': r.id,
            'school_id': r.school_id,
            'school_uuid': r.school_uuid,
            'school_name': r.school_name,
            'is_active': r.is_active,
            'assigned_at': r.created_at.isoformat() if r.created_at else None
        }
        for r in relations
    ]
    
    partner_data = UserResponse.model_validate(partner).model_dump(mode='json')
    partner_data['schools'] = schools
    
    return success_response(data=partner_data)


@router.put("/partners/{partner_uuid}")
def update_channel_partner(
    partner_uuid: str,
    partner_data: ChannelPartnerUpdate,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """更新渠道商信息"""
    logger.info(f"渠道管理员 {current_manager.username} 更新渠道商: {partner_uuid}")
    
    # 查询渠道商
    partner = db.query(Admin).filter(
        Admin.uuid == partner_uuid,
        Admin.role == 'channel_partner'
    ).first()
    
    if not partner:
        return error_response(message="渠道商不存在", code=404)
    
    # 更新字段
    update_data = partner_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partner, field, value)
    
    partner.updated_at = get_beijing_time_naive()
    db.commit()
    db.refresh(partner)
    
    logger.info(f"✅ 渠道商更新成功: {partner.username} (ID: {partner.id})")
    
    partner_response = UserResponse.model_validate(partner)
    return success_response(
        data=partner_response.model_dump(mode='json'),
        message="渠道商信息更新成功"
    )


@router.post("/partners/{partner_uuid}/reset-password")
def reset_partner_password(
    partner_uuid: str,
    request: ResetPasswordRequest,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """重置渠道商密码"""
    logger.info(f"渠道管理员 {current_manager.username} 重置渠道商密码: {partner_uuid}")
    
    # 查询渠道商
    partner = db.query(Admin).filter(
        Admin.uuid == partner_uuid,
        Admin.role == 'channel_partner'
    ).first()
    
    if not partner:
        return error_response(message="渠道商不存在", code=404)
    
    # 更新密码
    partner.password_hash = get_password_hash(request.new_password)
    partner.updated_at = get_beijing_time_naive()
    db.commit()
    
    logger.info(f"✅ 渠道商密码重置成功: {partner.username}")
    return success_response(message="密码重置成功")


@router.post("/assign-schools")
def assign_schools_to_partner(
    request: AssignSchoolRequest,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """为渠道商分配学校"""
    logger.info(f"渠道管理员 {current_manager.username} 为渠道商 {request.channel_partner_uuid} 分配学校: {request.school_uuids}")
    
    # 验证渠道商是否存在（通过UUID）
    partner = db.query(Admin).filter(
        Admin.uuid == request.channel_partner_uuid,
        Admin.role == 'channel_partner'
    ).first()
    
    if not partner:
        return error_response(message="渠道商不存在", code=404)
    
    # 验证学校是否存在（通过UUID）
    from ...models.school import School
    schools = db.query(School).filter(School.uuid.in_(request.school_uuids)).all()
    if len(schools) != len(request.school_uuids):
        return error_response(message="部分学校不存在", code=404)
    
    # 为每个学校创建关联（如果不存在）
    added_count = 0
    for school in schools:
        # 检查是否已存在关联
        existing = db.query(ChannelSchoolRelation).filter(
            ChannelSchoolRelation.channel_partner_id == partner.id,
            ChannelSchoolRelation.school_id == school.id
        ).first()
        
        if existing:
            # 如果已存在但被禁用，则重新启用
            if not existing.is_active:
                existing.is_active = 1
                existing.updated_at = get_beijing_time_naive()
                added_count += 1
        else:
            # 创建新关联
            new_relation = ChannelSchoolRelation(
                channel_partner_id=partner.id,
                school_id=school.id,
                is_active=1,
                created_at=get_beijing_time_naive(),
                updated_at=get_beijing_time_naive()
            )
            db.add(new_relation)
            added_count += 1
    
    db.commit()
    
    logger.info(f"✅ 成功为渠道商分配 {added_count} 所学校")
    return success_response(
        data={'added_count': added_count},
        message=f"成功分配 {added_count} 所学校"
    )


@router.delete("/partners/{partner_uuid}/schools/{school_uuid}")
def remove_school_from_partner(
    partner_uuid: str,
    school_uuid: str,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """解除渠道商与学校的关联"""
    logger.info(f"渠道管理员 {current_manager.username} 解除渠道商 {partner_uuid} 与学校 {school_uuid} 的关联")
    
    # 查询渠道商获取 ID
    partner = db.query(Admin).filter(
        Admin.uuid == partner_uuid,
        Admin.role == 'channel_partner'
    ).first()
    
    if not partner:
        return error_response(message="渠道商不存在", code=404)
    
    # 查询学校获取 ID
    from ...models.school import School
    school = db.query(School).filter(School.uuid == school_uuid).first()
    
    if not school:
        return error_response(message="学校不存在", code=404)
    
    # 查找关联
    relation = db.query(ChannelSchoolRelation).filter(
        ChannelSchoolRelation.channel_partner_id == partner.id,
        ChannelSchoolRelation.school_id == school.id
    ).first()
    
    if not relation:
        return error_response(message="关联不存在", code=404)
    
    # 软删除：设置为不活跃
    relation.is_active = 0
    relation.updated_at = get_beijing_time_naive()
    db.commit()
    
    logger.info(f"✅ 成功解除渠道商与学校的关联")
    return success_response(message="关联已解除")


@router.post("/schools")
def create_school(
    school_data: SchoolCreate,
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """创建学校"""
    logger.info(f"渠道管理员 {current_manager.username} 创建学校: {school_data.school_name}")
    
    from ...models.school import School
    from datetime import datetime
    
    # 检查学校代码是否已存在
    existing_school = db.query(School).filter(School.school_code == school_data.school_code).first()
    if existing_school:
        logger.warning(f"学校代码 {school_data.school_code} 已存在")
        return error_response(message="学校代码已存在", code=400)
    
    # 检查学校名称是否已存在
    existing_name = db.query(School).filter(School.school_name == school_data.school_name).first()
    if existing_name:
        logger.warning(f"学校名称 {school_data.school_name} 已存在")
        return error_response(message="学校名称已存在", code=400)
    
    # 处理授权到期时间
    license_expire_at = None
    if school_data.license_expire_at:
        try:
            license_expire_at = datetime.strptime(school_data.license_expire_at, '%Y-%m-%d').date()
        except ValueError:
            return error_response(message="授权到期时间格式错误，应为 YYYY-MM-DD", code=400)
    
    # 创建学校
    new_school = School(
        school_code=school_data.school_code,
        school_name=school_data.school_name,
        province=school_data.province,
        city=school_data.city,
        district=school_data.district,
        address=school_data.address,
        contact_person=school_data.contact_person,
        contact_phone=school_data.contact_phone,
        contact_email=school_data.contact_email,
        max_teachers=school_data.max_teachers,
        max_students=school_data.max_students,
        max_devices=school_data.max_devices,
        license_expire_at=license_expire_at,
        is_active=True,
        created_at=get_beijing_time_naive(),
        updated_at=get_beijing_time_naive()
    )
    
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    
    logger.info(f"✅ 学校创建成功: {new_school.school_name} (ID: {new_school.id})")
    
    result = {
        'id': new_school.id,
        'uuid': new_school.uuid,
        'school_code': new_school.school_code,
        'school_name': new_school.school_name,
        'province': new_school.province,
        'city': new_school.city,
        'district': new_school.district,
        'address': new_school.address,
        'contact_person': new_school.contact_person,
        'contact_phone': new_school.contact_phone,
        'contact_email': new_school.contact_email,
        'max_teachers': new_school.max_teachers,
        'max_students': new_school.max_students,
        'max_devices': new_school.max_devices,
        'license_expire_at': new_school.license_expire_at.isoformat() if new_school.license_expire_at else None,
        'is_active': new_school.is_active,
        'created_at': new_school.created_at.isoformat() if new_school.created_at else None
    }
    
    return success_response(data=result, message="学校创建成功")


@router.get("/schools")
def get_schools(
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """获取所有学校列表（含渠道商分配信息）"""
    from ...models.school import School
    schools = db.query(School).all()
    
    result = []
    for school in schools:
        # 统计分配给该学校的渠道商数量
        partner_count = db.query(func.count(ChannelSchoolRelation.id)).filter(
            ChannelSchoolRelation.school_id == school.id,
            ChannelSchoolRelation.is_active == 1
        ).scalar()
        
        school_data = {
            'id': school.id,
            'uuid': school.uuid,
            'school_code': school.school_code,
            'school_name': school.school_name,
            'province': school.province,
            'city': school.city,
            'district': school.district,
            'address': school.address,
            'contact_person': school.contact_person,
            'contact_phone': school.contact_phone,
            'contact_email': school.contact_email,
            'max_teachers': school.max_teachers,
            'max_students': school.max_students,
            'max_devices': school.max_devices,
            'license_expire_at': school.license_expire_at.isoformat() if school.license_expire_at else None,
            'is_active': school.is_active,
            'partner_count': partner_count or 0,
            'created_at': school.created_at.isoformat() if school.created_at else None
        }
        result.append(school_data)
    
    logger.info(f"返回 {len(result)} 所学校")
    return success_response(data=result)


@router.get("/schools/available")
def get_available_schools(
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """获取所有可分配的学校列表"""
    from ...models.school import School
    schools = db.query(School).all()
    
    result = [
        {
            'id': school.id,
            'uuid': school.uuid,
            'name': school.school_name,
            'created_at': school.created_at.isoformat() if school.created_at else None
        }
        for school in schools
    ]
    
    logger.info(f"返回 {len(result)} 所学校")
    return success_response(data=result)


@router.get("/statistics")
def get_channel_statistics(
    current_manager: Admin = Depends(get_current_channel_manager),
    db: Session = Depends(get_db)
):
    """获取渠道业务统计数据"""
    # 总渠道商数
    total_partners = db.query(func.count(Admin.id)).filter(
        Admin.role == 'channel_partner'
    ).scalar()
    
    # 活跃渠道商数
    active_partners = db.query(func.count(Admin.id)).filter(
        Admin.role == 'channel_partner',
        Admin.is_active == True
    ).scalar()
    
    # 总学校关联数
    total_relations = db.query(func.count(ChannelSchoolRelation.id)).filter(
        ChannelSchoolRelation.is_active == 1
    ).scalar()
    
    # 有渠道商的学校数
    from ...models.school import School
    schools_with_partner = db.query(
        func.count(func.distinct(ChannelSchoolRelation.school_id))
    ).filter(
        ChannelSchoolRelation.is_active == 1
    ).scalar()
    
    statistics = {
        'total_partners': total_partners or 0,
        'active_partners': active_partners or 0,
        'total_relations': total_relations or 0,
        'schools_with_partner': schools_with_partner or 0
    }
    
    logger.info(f"渠道统计: {statistics}")
    return success_response(data=statistics)
