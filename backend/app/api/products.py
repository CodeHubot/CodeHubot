"""
产品管理API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, 
    ProductList, ProductSummary
)
from app.api.auth import get_current_user
from app.models.user import User
from app.core.response import success_response

router = APIRouter()


def is_admin_user(user: User) -> bool:
    """判断用户是否为管理员
    
    管理员权限判断规则：
    1. platform_admin 角色（平台管理员）
    """
    判断用户是否为管理员
    基于角色判断，更安全且易于管理
    """
    return user.role in ['platform_admin', 'super_admin', 'admin']


def can_access_product(product: Product, user: User) -> bool:
    """判断用户是否可以访问产品
    访问规则：
    1. 管理员：可以访问所有产品
    2. 系统内置产品：所有用户可以访问
    3. 用户创建的产品：
       - 创建者自己可以访问
       - 已共享的产品：所有用户可以访问
       - 未共享的产品：只有创建者可以访问
    """
    if is_admin_user(user):
        return True
    # 系统内置产品：所有用户可访问
    if product.is_system:
        return True
    # 用户创建的产品
    if product.creator_id == user.id:
        return True  # 创建者可访问
    # 已共享的产品：所有用户可访问
    if product.is_shared:
        return True
    return False


def can_edit_product(product: Product, user: User) -> bool:
    """判断用户是否可以编辑产品
    编辑规则：
    1. 管理员：可以编辑所有产品
    2. 系统内置产品：只有管理员可以编辑
    3. 用户创建的产品：只有创建者可以编辑（无论是否共享）
    """
    if is_admin_user(user):
        return True
    # 系统内置产品：只有管理员可编辑
    if product.is_system:
        return False
    # 用户创建的产品：只有创建者可编辑
    return product.creator_id == user.id


@router.post("", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新产品
    
    **产品编码（product_code）规范：**
    - 最大长度：64字符
    - 格式建议：硬件型号-功能-版本（如：ESP32-S3-TempSensor-01）
    - 必须全局唯一
    - ⚠️ 重要：必须与固件端 DEVICE_PRODUCT_ID 完全一致
    - 创建后不可修改
    
    **权限说明：**
    - 管理员：可以创建系统内置产品或普通产品
    - 普通用户：只能创建普通产品（非系统内置）
    """
    # 检查产品编号是否已存在
    existing_product = db.query(Product).filter(
        Product.product_code == product.product_code
    ).first()
    
    if existing_product:
        raise HTTPException(
            status_code=400,
            detail=f"产品编码 {product.product_code} 已存在，请使用不同的产品编码"
        )
    
    # 创建产品数据
    product_data = product.model_dump()
    
    # 权限检查：只有管理员可以创建系统内置产品
    if product_data.get('is_system', False):
        if not is_admin_user(current_user):
            raise HTTPException(
                status_code=403,
                detail="只有管理员可以创建系统内置产品"
            )
        # 系统内置产品不设置creator_id
        product_data['creator_id'] = None
    else:
        # 普通用户创建的产品
        product_data['is_system'] = False
        product_data['creator_id'] = current_user.id
    
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


@router.get("", response_model=List[ProductList])
def get_products(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    is_active: Optional[str] = Query(None, description="是否激活筛选"),
    is_system: Optional[bool] = Query(None, description="是否系统内建筛选（仅管理员）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_field: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query(None, description="排序顺序(asc/desc)"),
    include_shared: Optional[bool] = Query(True, description="是否包含共享产品（普通用户可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取产品列表 - 权限控制：
    - 管理员：可以看到所有产品（系统内置 + 所有用户创建的）
      - 可通过 is_system 参数筛选：True=仅系统内建，False=仅用户创建，None=全部
    - 普通用户：
      - 默认（include_shared=False）：只看到系统内置产品和自己创建的产品
      - 开启共享（include_shared=True）：额外看到其他用户共享的产品
    """
    query = db.query(Product)
    
    # 权限过滤
    if is_admin_user(current_user):
        # 管理员：看到所有产品，可通过 is_system 筛选
        if is_system is not None:
            query = query.filter(Product.is_system == is_system)
    else:
        # 普通用户：根据include_shared参数决定是否包含共享产品
        if include_shared:
            query = query.filter(
                (Product.is_system == True) |  # 系统内置产品
                (Product.creator_id == current_user.id) |  # 自己创建的产品
                (Product.is_shared == True)  # 其他用户共享的产品
            )
        else:
            query = query.filter(
                (Product.is_system == True) |  # 系统内置产品
                (Product.creator_id == current_user.id)  # 自己创建的产品（不包含共享产品）
            )
    
    if is_active is not None and is_active != "":
        # 将字符串转换为布尔值
        if is_active.lower() in ['true', '1', 'yes', 'on']:
            query = query.filter(Product.is_active == True)
        elif is_active.lower() in ['false', '0', 'no', 'off']:
            query = query.filter(Product.is_active == False)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.name.like(search_pattern)) |
            (Product.product_code.like(search_pattern)) |
            (Product.description.like(search_pattern))
        )
    
    # 应用排序
    if sort_field and sort_order:
        if hasattr(Product, sort_field):
            column = getattr(Product, sort_field)
            if sort_order.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # 默认按创建时间排序
            query = query.order_by(Product.created_at.desc())
    else:
        # 默认按创建时间排序
        query = query.order_by(Product.created_at.desc())
    
    # 分页
    products = query.offset(skip).limit(limit).all()
    
    return products


@router.get("/summary", response_model=List[ProductSummary])
def get_products_summary(
    is_active: bool = Query(True, description="是否只返回激活的产品"),
    include_shared: Optional[bool] = Query(False, description="是否包含共享产品（普通用户可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取产品摘要信息 - 权限控制：
    - 管理员：可以看到所有产品（系统内置 + 用户创建的）
    - 普通用户：
      - 默认（include_shared=False）：只看到系统内置产品和自己创建的产品
      - 开启共享（include_shared=True）：额外看到其他用户共享的产品
    """
    query = db.query(Product)
    
    # 权限过滤
    if is_admin_user(current_user):
        # 管理员：看到所有产品
        pass
    else:
        # 普通用户：根据include_shared参数决定是否包含共享产品
        if include_shared:
            query = query.filter(
                (Product.is_system == True) |  # 系统内置产品
                (Product.creator_id == current_user.id) |  # 自己创建的产品
                (Product.is_shared == True)  # 其他用户共享的产品
            )
        else:
            query = query.filter(
                (Product.is_system == True) |  # 系统内置产品
                (Product.creator_id == current_user.id)  # 自己创建的产品（不包含共享产品）
            )
    
    if is_active:
        query = query.filter(Product.is_active == True)
    
    products = query.all()
    return products


@router.get("/categories")
def get_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有产品类别"""
    categories = db.execute(text("""
        SELECT DISTINCT category, COUNT(*) as count
        FROM device_products
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC, category
    """)).fetchall()
    
    return success_response(data=[
        {"category": cat[0], "count": cat[1]} 
        for cat in categories
    ])


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个产品详情 - 权限控制：
    - 管理员：可以查看所有产品
    - 系统内置产品：所有用户可以查看
    - 用户创建的产品：创建者和已共享的产品其他用户可以查看
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 使用can_access_product检查访问权限
    if not can_access_product(product, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权访问该产品"
        )
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新产品信息 - 只有创建者和管理员可以编辑"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 检查编辑权限（不是访问权限）
    if not can_edit_product(product, current_user):
        raise HTTPException(
            status_code=403, 
            detail="无权编辑该产品（系统内置产品只有管理员可编辑，用户创建的产品只有创建者可编辑）"
        )
    
    # 更新字段
    update_data = product_update.model_dump(exclude_unset=True)
    
    # 权限控制：只有管理员可以修改 is_system
    if 'is_system' in update_data:
        if not is_admin_user(current_user):
            update_data.pop('is_system', None)  # 普通用户不能修改系统内置标志
    
    # 不允许修改 creator_id
    update_data.pop('creator_id', None)
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除产品 - 只有创建者和管理员可以删除"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 检查删除权限（不是访问权限）
    if not can_edit_product(product, current_user):
        raise HTTPException(
            status_code=403, 
            detail="无权删除该产品（系统内置产品只有管理员可删除，用户创建的产品只有创建者可删除）"
        )
    
    # 检查是否有关联的设备
    device_count = db.execute(text("""
        SELECT COUNT(*) FROM device_main WHERE product_id = :product_id
    """), {"product_id": product_id}).scalar()
    
    if device_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除产品，存在 {device_count} 个关联的设备"
        )
    
    db.delete(product)
    db.commit()
    
    return success_response(message="产品删除成功")


@router.get("/{product_id}/devices")
def get_product_devices(
    product_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取产品的所有设备 - 权限控制"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    # 权限检查：普通用户只能访问系统内置产品和自己创建的产品
    if not can_access_product(product, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权访问该产品"
        )
    
    # 获取设备信息
    devices = db.execute(text("""
        SELECT id, name, uuid, is_online, is_active, 
               last_seen, location, group_name, error_count, created_at
        FROM device_main 
        WHERE product_id = :product_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """), {"product_id": product_id, "limit": limit, "skip": skip}).fetchall()
    
    # 将 Row 对象转换为字典
    return success_response(data=[dict(device._mapping) for device in devices])