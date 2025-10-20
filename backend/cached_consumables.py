from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from database import get_db
from models import Consumable, User
from auth import get_current_user, require_admin
from permissions import require_permission, Permissions
from pydantic import BaseModel
from redis_cache import RedisCache, cache_result, invalidate_cache_pattern
from redis_config import redis_config
from cache_config import CacheConfig, CacheType, invalidate_related_caches

# 创建路由器
router = APIRouter(prefix="/consumables", tags=["consumables"])

# 初始化Redis缓存
redis_cache = RedisCache(redis_config)

# Pydantic模型
class ConsumableCreate(BaseModel):
    name: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    specification: Optional[str] = None
    quantity: Optional[int] = 0
    unit: Optional[str] = "个"
    location: Optional[str] = None
    min_stock: Optional[int] = 10
    price: Optional[float] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None

class ConsumableUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    specification: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    min_stock: Optional[int] = None
    price: Optional[float] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None

class ConsumableResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    specification: Optional[str]
    quantity: Optional[int]
    unit: Optional[str]
    location: Optional[str]
    min_stock: Optional[int]
    price: Optional[float]
    supplier: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ConsumableReceive(BaseModel):
    quantity: int
    supplier: Optional[str] = None
    batch_number: Optional[str] = None
    notes: Optional[str] = None

class ConsumableRequest(BaseModel):
    consumable_id: int
    quantity: int
    unit: str
    purpose: str
    notes: Optional[str] = None

class PaginatedConsumableResponse(BaseModel):
    items: List[ConsumableResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# 缓存辅助函数
def serialize_consumable(consumable):
    """序列化耗材对象为字典"""
    return {
        "id": consumable.id,
        "name": consumable.name,
        "category": consumable.category,
        "manufacturer": consumable.manufacturer,
        "model": consumable.model,
        "specification": consumable.specification,
        "quantity": consumable.quantity,
        "unit": consumable.unit,
        "location": consumable.location,
        "min_stock": consumable.min_stock,
        "price": float(consumable.price) if consumable.price else None,
        "supplier": consumable.supplier,
        "notes": consumable.notes,
        "created_at": consumable.created_at.isoformat() if consumable.created_at else None,
        "updated_at": consumable.updated_at.isoformat() if consumable.updated_at else None
    }

def deserialize_consumable(data):
    """反序列化字典为耗材响应对象"""
    if data.get("created_at"):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    if data.get("updated_at"):
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
    return ConsumableResponse(**data)

# 缓存路由处理函数
@router.get("", response_model=PaginatedConsumableResponse)
def get_consumables(
    page: int = 1,
    per_page: int = 50,
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: bool = False,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取耗材列表（带缓存）"""
    # 生成缓存键
    cache_key = CacheConfig.get_cache_key(
        CacheType.CONSUMABLES, 
        f"list:page={page}:per_page={per_page}:category={category}:search={search}:low_stock={low_stock}:sort_by={sort_by}:sort_order={sort_order}"
    )
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return PaginatedConsumableResponse(**cached_data)
    
    # 从数据库查询
    query = db.query(Consumable)
    
    # 应用过滤器
    if category:
        query = query.filter(Consumable.category == category)
    if search:
        query = query.filter(
            Consumable.name.contains(search) |
            Consumable.manufacturer.contains(search) |
            Consumable.model.contains(search)
        )
    if low_stock:
        query = query.filter(Consumable.quantity <= Consumable.min_stock)
    
    # 排序
    if sort_by == "name":
        query = query.order_by(Consumable.name.asc() if sort_order == "asc" else Consumable.name.desc())
    elif sort_by == "quantity":
        query = query.order_by(Consumable.quantity.asc() if sort_order == "asc" else Consumable.quantity.desc())
    elif sort_by == "created_at":
        query = query.order_by(Consumable.created_at.asc() if sort_order == "asc" else Consumable.created_at.desc())
    
    # 分页
    total = query.count()
    consumables = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # 构建响应
    items = [ConsumableResponse.from_orm(consumable) for consumable in consumables]
    pages = (total + per_page - 1) // per_page
    
    result = {
        "items": [item.dict() for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.CONSUMABLES)
    redis_cache.set(cache_key, result, ttl=ttl)
    
    return PaginatedConsumableResponse(**result)

@router.get("/{consumable_id}", response_model=ConsumableResponse)
def get_consumable(
    consumable_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个耗材（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.CONSUMABLES, f"detail:{consumable_id}")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return deserialize_consumable(cached_data)
    
    # 从数据库查询
    consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 序列化并缓存
    data = serialize_consumable(consumable)
    ttl = CacheConfig.get_ttl(CacheType.CONSUMABLES)
    redis_cache.set(cache_key, data, ttl=ttl)
    
    return ConsumableResponse.from_orm(consumable)

@router.post("", response_model=dict)
def create_consumable(
    consumable: ConsumableCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """创建耗材（清除相关缓存）"""
    db_consumable = Consumable(**consumable.dict())
    db.add(db_consumable)
    db.commit()
    db.refresh(db_consumable)
    
    # 清除相关缓存
    patterns = CacheConfig.get_invalidation_patterns(CacheType.CONSUMABLES)
    for pattern in patterns:
        invalidate_cache_pattern(pattern)
    
    return {"message": "耗材创建成功", "id": db_consumable.id}

@router.put("/{consumable_id}", response_model=dict)
def update_consumable(
    consumable_id: int,
    consumable: ConsumableUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """更新耗材（清除相关缓存）"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 更新字段
    for field, value in consumable.dict(exclude_unset=True).items():
        setattr(db_consumable, field, value)
    
    db_consumable.updated_at = datetime.utcnow()
    db.commit()
    
    # 清除相关缓存
    patterns = CacheConfig.get_invalidation_patterns(CacheType.CONSUMABLES)
    for pattern in patterns:
        invalidate_cache_pattern(pattern)
    
    return {"message": "耗材更新成功"}

@router.delete("/{consumable_id}", response_model=dict)
def delete_consumable(
    consumable_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """删除耗材（清除相关缓存）"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    db.delete(db_consumable)
    db.commit()
    
    # 清除相关缓存
    patterns = CacheConfig.get_invalidation_patterns(CacheType.CONSUMABLES)
    for pattern in patterns:
        invalidate_cache_pattern(pattern)
    
    return {"message": "耗材删除成功"}

@router.get("/categories/list", response_model=List[str])
def get_consumable_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取耗材分类列表（带缓存）"""
    cache_key = get_cache_key(CacheType.CONSUMABLES, "categories")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 从数据库查询
    categories = db.query(Consumable.category).filter(Consumable.category.isnot(None)).distinct().all()
    result = [cat[0] for cat in categories if cat[0]]
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.CONSUMABLES)
    redis_cache.set(cache_key, result, ttl=ttl)
    
    return result

@router.get("/low-stock/list", response_model=List[ConsumableResponse])
def get_low_stock_consumables(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取低库存耗材列表（带缓存）"""
    cache_key = get_cache_key(CacheType.CONSUMABLES, "low_stock")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return [deserialize_consumable(item) for item in cached_data]
    
    # 从数据库查询
    consumables = db.query(Consumable).filter(Consumable.quantity <= Consumable.min_stock).all()
    result = [serialize_consumable(consumable) for consumable in consumables]
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.CONSUMABLES)
    redis_cache.set(cache_key, result, ttl=ttl)
    
    return [ConsumableResponse.from_orm(consumable) for consumable in consumables]

# 其他路由保持原样（不需要缓存的操作）
@router.post("/{consumable_id}/receive", response_model=dict)
def receive_consumable(
    consumable_id: int,
    receive_data: ConsumableReceive,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """接收耗材（清除相关缓存）"""
    consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 更新库存
    consumable.quantity = (consumable.quantity or 0) + receive_data.quantity
    if receive_data.supplier:
        consumable.supplier = receive_data.supplier
    consumable.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 清除相关缓存
    invalidate_related_caches([CacheType.CONSUMABLES])
    
    return {
        "message": "耗材接收成功",
        "new_quantity": consumable.quantity
    }

@router.post("/{consumable_id}/use", response_model=dict)
def use_consumable(
    consumable_id: int,
    quantity: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """使用耗材（清除相关缓存）"""
    consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    if (consumable.quantity or 0) < quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    
    # 更新库存
    consumable.quantity = (consumable.quantity or 0) - quantity
    consumable.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 清除相关缓存
    invalidate_related_caches([CacheType.CONSUMABLES])
    
    return {
        "message": "耗材使用记录成功",
        "remaining_quantity": consumable.quantity
    }

@router.post("/request", response_model=dict)
@require_permission(Permissions.CONSUMABLE_REQUEST)
def request_consumable(
    request: ConsumableRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """申请耗材"""
    # 检查耗材是否存在
    consumable = db.query(Consumable).filter(Consumable.id == request.consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 检查库存
    if (consumable.quantity or 0) < request.quantity:
        raise HTTPException(status_code=400, detail="库存不足，无法申请")
    
    # 这里应该添加到审批队列，暂时简化处理
    # TODO: 实现审批流程
    
    return {
        "message": "耗材申请已提交，等待审批",
        "request_id": f"CONS_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    }

# 缓存管理端点
@router.post("/cache/clear", response_model=dict)
def clear_consumable_cache(
    current_user: dict = Depends(require_admin)
):
    """清除耗材缓存"""
    invalidate_related_caches([CacheType.CONSUMABLES])
    return {"message": "耗材缓存已清除"}

@router.post("/cache/warmup", response_model=dict)
def warmup_consumable_cache(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """预热耗材缓存"""
    # 预热分类缓存
    get_consumable_categories(db=db, current_user=current_user)
    
    # 预热低库存缓存
    get_low_stock_consumables(db=db, current_user=current_user)
    
    # 预热第一页数据
    get_consumables(db=db, current_user=current_user)
    
    return {"message": "耗材缓存预热完成"}