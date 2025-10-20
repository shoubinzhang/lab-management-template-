# backend/routers/cached_reagents.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import hashlib

from database import get_db
from models import Reagent, User
from auth import get_current_user, require_admin
from permissions import check_permission, Permissions
from pydantic import BaseModel
from redis_cache import redis_cache, cache_result, invalidate_cache_pattern
from redis_config import redis_config
from cache_config import CacheType, CacheConfig, invalidate_related_cache, cache_key_for_item

# 创建路由器
router = APIRouter(prefix="/reagents", tags=["reagents"])
# Pydantic模型
class ReagentCreate(BaseModel):
    name: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = "ml"
    min_threshold: Optional[float] = 10.0  # 最小库存阈值
    location: Optional[str] = None
    safety_notes: Optional[str] = None
    price: Optional[float] = None

class ReagentUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    min_threshold: Optional[float] = None  # 最小库存阈值
    location: Optional[str] = None
    safety_notes: Optional[str] = None
    price: Optional[float] = None

class ReagentResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    manufacturer: Optional[str]
    lot_number: Optional[str]
    expiry_date: Optional[datetime]
    quantity: Optional[float]
    unit: Optional[str]
    min_threshold: Optional[float]  # 最小库存阈值
    location: Optional[str]
    safety_notes: Optional[str]
    price: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ReagentRequest(BaseModel):
    reagent_id: int
    quantity: float
    unit: str
    purpose: str
    notes: Optional[str] = None

# 分页响应模型
class PaginatedReagentResponse(BaseModel):
    items: List[ReagentResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# 缓存辅助函数
def _generate_cache_key(endpoint: str, **params) -> str:
    """生成缓存键"""
    # 移除None值并排序参数以确保一致性
    clean_params = {k: v for k, v in params.items() if v is not None}
    param_str = json.dumps(clean_params, sort_keys=True, default=str)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
    return f"reagents:{endpoint}:{param_hash}"

def _serialize_reagents(reagents: List[Reagent]) -> List[dict]:
    """序列化试剂列表"""
    return [{
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "manufacturer": r.manufacturer,
        "lot_number": r.lot_number,
        "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
        "quantity": r.quantity,
        "unit": r.unit,
        "min_threshold": r.min_threshold,
        "location": r.location,
        "safety_notes": r.safety_notes,
        "price": r.price,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat() if r.updated_at else None
    } for r in reagents]

def _deserialize_reagents(data: List[dict]) -> List[ReagentResponse]:
    """反序列化试剂列表"""
    result = []
    for item in data:
        # 处理日期字段
        if item.get('expiry_date'):
            item['expiry_date'] = datetime.fromisoformat(item['expiry_date'])
        if item.get('created_at'):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        if item.get('updated_at'):
            item['updated_at'] = datetime.fromisoformat(item['updated_at'])
        
        result.append(ReagentResponse(**item))
    return result

# 路由处理函数
@router.get("", response_model=PaginatedReagentResponse)
def get_reagents(
    page: int = 1,
    per_page: int = 50,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_READ))
):
    """获取试剂列表（分页，带缓存）"""
    # 验证分页参数
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50
    
    # 生成缓存键
    cache_key = _generate_cache_key(
        "list",
        page=page,
        per_page=per_page,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 尝试从缓存获取
    try:
        cached_result = redis_cache.get(cache_key)
        if cached_result:
            return PaginatedReagentResponse(**cached_result)
    except Exception as e:
        # 缓存获取失败时记录警告但继续执行
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"缓存获取失败: {e}")
    
    # 从数据库查询
    query = db.query(Reagent)
    
    # 按类别筛选
    if category:
        query = query.filter(Reagent.category == category)
    
    # 搜索功能
    if search:
        query = query.filter(
            Reagent.name.contains(search) |
            Reagent.manufacturer.contains(search) |
            Reagent.lot_number.contains(search)
        )
    
    # 排序
    if sort_by and hasattr(Reagent, sort_by):
        order_column = getattr(Reagent, sort_by)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    else:
        query = query.order_by(Reagent.name.asc())
    
    # 获取总数
    total = query.count()
    
    # 计算偏移量
    offset = (page - 1) * per_page
    
    # 获取分页数据
    reagents = query.offset(offset).limit(per_page).all()
    
    # 计算分页信息
    pages = (total + per_page - 1) // per_page
    has_next = page < pages
    has_prev = page > 1
    
    # 序列化数据
    serialized_items = _serialize_reagents(reagents)
    
    result = {
        "items": serialized_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev
    }
    
    # 缓存结果
    try:
        ttl = CacheConfig.get_ttl(CacheType.REAGENTS)
        redis_cache.set(cache_key, result, ttl)
    except Exception as e:
        # 缓存设置失败时记录警告但继续执行
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"缓存设置失败: {e}")
    
    # 反序列化返回
    result["items"] = _deserialize_reagents(serialized_items)
    return PaginatedReagentResponse(**result)

@router.get("/{reagent_id}", response_model=ReagentResponse)
def get_reagent(
    reagent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_READ))
):
    """获取特定试剂（带缓存）"""
    # 生成缓存键
    cache_key = cache_key_for_item(CacheType.REAGENTS, reagent_id)
    
    # 尝试从缓存获取
    cached_result = redis_cache.get(cache_key)
    if cached_result:
        # 处理日期字段
        if cached_result.get('expiry_date'):
            cached_result['expiry_date'] = datetime.fromisoformat(cached_result['expiry_date'])
        if cached_result.get('created_at'):
            cached_result['created_at'] = datetime.fromisoformat(cached_result['created_at'])
        if cached_result.get('updated_at'):
            cached_result['updated_at'] = datetime.fromisoformat(cached_result['updated_at'])
        return ReagentResponse(**cached_result)
    
    # 从数据库查询
    reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    # 序列化并缓存
    serialized_reagent = _serialize_reagents([reagent])[0]
    ttl = CacheConfig.get_ttl(CacheType.REAGENTS)
    redis_cache.set(cache_key, serialized_reagent, ttl)
    
    return reagent

@router.post("", response_model=ReagentResponse)
def create_reagent(
    reagent: ReagentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建新试剂（清除相关缓存）"""
    db_reagent = Reagent(
        **reagent.dict(),
        created_at=datetime.utcnow()
    )
    db.add(db_reagent)
    db.commit()
    db.refresh(db_reagent)
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.REAGENTS)
    
    return db_reagent

@router.put("/{reagent_id}", response_model=dict)
def update_reagent(
    reagent_id: int,
    reagent: ReagentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新试剂信息（清除相关缓存）"""
    db_reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not db_reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    for key, value in reagent.dict(exclude_unset=True).items():
        setattr(db_reagent, key, value)
    
    db_reagent.updated_at = datetime.utcnow()
    db.commit()
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.REAGENTS)
    
    return {"message": "试剂更新成功"}

@router.delete("/{reagent_id}", response_model=dict)
def delete_reagent(
    reagent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除试剂（清除相关缓存）"""
    db_reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not db_reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    db.delete(db_reagent)
    db.commit()
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.REAGENTS)
    
    return {"message": "试剂删除成功"}

@router.get("/categories/list", response_model=List[str])
def get_reagent_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_READ))
):
    """获取所有试剂类别（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.REAGENTS, "categories")
    
    # 尝试从缓存获取
    cached_result = redis_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # 从数据库查询
    categories = db.query(Reagent.category).distinct().filter(Reagent.category.isnot(None)).all()
    result = [category[0] for category in categories if category[0]]
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.REAGENTS)
    redis_cache.set(cache_key, result, ttl)
    
    return result

@router.get("/expiring/list", response_model=List[ReagentResponse])
def get_expiring_reagents(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_READ))
):
    """获取即将过期的试剂（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.REAGENTS, f"expiring:{days}")
    
    # 尝试从缓存获取
    cached_result = redis_cache.get(cache_key)
    if cached_result:
        return _deserialize_reagents(cached_result)
    
    # 从数据库查询
    from datetime import timedelta
    
    expiry_threshold = datetime.utcnow() + timedelta(days=days)
    reagents = db.query(Reagent).filter(
        Reagent.expiry_date.isnot(None),
        Reagent.expiry_date <= expiry_threshold
    ).all()
    
    # 序列化并缓存
    serialized_reagents = _serialize_reagents(reagents)
    ttl = CacheConfig.get_ttl(CacheType.REAGENTS) // 2  # 过期数据缓存时间较短
    redis_cache.set(cache_key, serialized_reagents, ttl)
    
    return reagents

@router.get("/low-stock/list", response_model=List[ReagentResponse])
def get_low_stock_reagents(
    threshold: float = 10.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_READ))
):
    """获取库存不足的试剂（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.REAGENTS, f"low_stock:{threshold}")
    
    # 尝试从缓存获取
    cached_result = redis_cache.get(cache_key)
    if cached_result:
        return _deserialize_reagents(cached_result)
    
    # 从数据库查询
    reagents = db.query(Reagent).filter(
        Reagent.quantity <= threshold
    ).all()
    
    # 序列化并缓存
    serialized_reagents = _serialize_reagents(reagents)
    ttl = CacheConfig.get_ttl(CacheType.REAGENTS) // 2  # 库存数据缓存时间较短
    redis_cache.set(cache_key, serialized_reagents, ttl)
    
    return reagents

@router.post("/request", response_model=dict)
def request_reagent(
    request: ReagentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_REQUEST))
):
    """申请领用试剂"""
    from routers.approvals import add_request, RequestType
    
    # 检查试剂是否存在
    reagent = db.query(Reagent).filter(Reagent.id == request.reagent_id).first()
    if not reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    # 检查库存是否充足
    if reagent.quantity < request.quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    
    # 添加申请到审批队列
    request_id = add_request(
        request_type=RequestType.REAGENT,
        item_id=request.reagent_id,
        item_name=reagent.name,
        quantity=request.quantity,
        unit=request.unit,
        purpose=request.purpose,
        requester_id=current_user["id"],
        requester_name=current_user["username"],
        notes=request.notes
    )
    
    return {
        "message": "试剂申请已提交，等待审批",
        "request_id": request_id,
        "reagent_name": reagent.name,
        "requested_quantity": request.quantity,
        "unit": request.unit,
        "purpose": request.purpose
    }

# 缓存管理端点
@router.post("/cache/clear", response_model=dict)
def clear_reagent_cache(
    current_user: User = Depends(require_admin)
):
    """清除试剂相关缓存（仅管理员）"""
    deleted_count = invalidate_related_cache(CacheType.REAGENTS)
    return {
        "message": f"已清除 {deleted_count} 个试剂相关缓存项",
        "deleted_count": deleted_count
    }

@router.post("/cache/warmup", response_model=dict)
def warmup_reagent_cache(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """预热试剂缓存（仅管理员）"""
    try:
        # 预热常用查询
        warmup_queries = [
            {"page": 1, "per_page": 50},  # 首页数据
            {"page": 1, "per_page": 50, "sort_by": "created_at", "sort_order": "desc"},  # 最新数据
        ]
        
        warmed_count = 0
        for query_params in warmup_queries:
            cache_key = _generate_cache_key("list", **query_params)
            if not redis_cache.exists(cache_key):
                # 执行查询并缓存
                get_reagents(db=db, current_user=current_user, **query_params)
                warmed_count += 1
        
        # 预热类别数据
        categories_key = CacheConfig.get_cache_key(CacheType.REAGENTS, "categories")
        if not redis_cache.exists(categories_key):
            get_reagent_categories(db=db, current_user=current_user)
            warmed_count += 1
        
        return {
            "message": f"试剂缓存预热完成，预热了 {warmed_count} 个缓存项",
            "warmed_count": warmed_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"缓存预热失败: {str(e)}")