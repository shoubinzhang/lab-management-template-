from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import Consumable, User
from backend.auth import get_current_user, require_admin
from backend.permissions import require_permission, Permissions
from pydantic import BaseModel

# 创建路由器
router = APIRouter(prefix="/api/consumables", tags=["consumables"])

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

# 认证依赖已从主app导入

# 分页响应模型
class PaginatedConsumableResponse(BaseModel):
    items: List[ConsumableResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# 路由处理函数
@router.get("/", response_model=PaginatedConsumableResponse)
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
    """获取耗材列表（分页）"""
    # 验证分页参数
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50
    
    query = db.query(Consumable)
    
    # 按类别筛选
    if category:
        query = query.filter(Consumable.category == category)
    
    # 搜索功能
    if search:
        query = query.filter(
            Consumable.name.contains(search) |
            Consumable.manufacturer.contains(search) |
            Consumable.model.contains(search)
        )
    
    # 库存不足筛选
    if low_stock:
        query = query.filter(Consumable.quantity <= Consumable.min_stock)
    
    # 排序
    if sort_by and hasattr(Consumable, sort_by):
        order_column = getattr(Consumable, sort_by)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    else:
        query = query.order_by(Consumable.name.asc())
    
    # 获取总数
    total = query.count()
    
    # 计算偏移量
    offset = (page - 1) * per_page
    
    # 获取分页数据
    consumables = query.offset(offset).limit(per_page).all()
    
    # 计算分页信息
    pages = (total + per_page - 1) // per_page
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedConsumableResponse(
        items=consumables,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/{consumable_id}", response_model=ConsumableResponse)
def get_consumable(
    consumable_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取特定耗材"""
    consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    return consumable

@router.post("/", response_model=dict)
def create_consumable(
    consumable: ConsumableCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """创建新耗材"""
    db_consumable = Consumable(
        **consumable.dict(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_consumable)
    db.commit()
    db.refresh(db_consumable)
    return {"message": "耗材创建成功", "consumable_id": db_consumable.id}

@router.put("/{consumable_id}", response_model=dict)
def update_consumable(
    consumable_id: int,
    consumable: ConsumableUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """更新耗材信息"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    for key, value in consumable.dict(exclude_unset=True).items():
        setattr(db_consumable, key, value)
    
    db_consumable.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "耗材更新成功"}

@router.delete("/{consumable_id}", response_model=dict)
def delete_consumable(
    consumable_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """删除耗材"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    db.delete(db_consumable)
    db.commit()
    return {"message": "耗材删除成功"}

@router.post("/{consumable_id}/receive", response_model=dict)
def receive_consumable(
    consumable_id: int,
    receive_data: ConsumableReceive,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """耗材入库"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 更新库存
    db_consumable.quantity = (db_consumable.quantity or 0) + quantity
    db_consumable.updated_at = datetime.now(timezone.utc)
    
    # 更新供应商信息（如果提供）
    if receive_data.supplier:
        db_consumable.supplier = receive_data.supplier
    
    db.commit()
    
    return {
        "message": "耗材入库成功",
        "new_quantity": db_consumable.quantity,
        "received_quantity": receive_data.quantity
    }

@router.post("/{consumable_id}/use", response_model=dict)
def use_consumable(
    consumable_id: int,
    quantity: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """耗材使用/出库"""
    db_consumable = db.query(Consumable).filter(Consumable.id == consumable_id).first()
    if not db_consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    if (db_consumable.quantity or 0) < quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    
    # 更新库存
    db_consumable.quantity = (db_consumable.quantity or 0) - quantity
    db_consumable.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "message": "耗材使用记录成功",
        "remaining_quantity": db_consumable.quantity,
        "used_quantity": quantity
    }

@router.get("/categories/list", response_model=List[str])
def get_consumable_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有耗材类别"""
    categories = db.query(Consumable.category).distinct().filter(Consumable.category.isnot(None)).all()
    return [category[0] for category in categories if category[0]]

@router.get("/low-stock/list", response_model=List[ConsumableResponse])
def get_low_stock_consumables(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取库存不足的耗材"""
    consumables = db.query(Consumable).filter(
        Consumable.quantity <= Consumable.min_stock
    ).all()
    
    return consumables

@router.post("/request", response_model=dict)
@require_permission(Permissions.CONSUMABLE_REQUEST)
def request_consumable(
    request: ConsumableRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """申请耗材"""
    from backend.routers.approvals import add_request, RequestType
    
    # 检查耗材是否存在
    consumable = db.query(Consumable).filter(Consumable.id == request.consumable_id).first()
    if not consumable:
        raise HTTPException(status_code=404, detail="耗材不存在")
    
    # 检查库存是否充足
    if consumable.quantity < request.quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    
    # 添加申请到审批队列
    request_id = add_request(
        request_type=RequestType.CONSUMABLE,
        item_id=request.consumable_id,
        item_name=consumable.name,
        quantity=request.quantity,
        unit=request.unit,
        purpose=request.purpose,
        requester_id=current_user["id"],
        requester_name=current_user["username"],
        notes=request.notes
    )
    
    return {
        "message": "耗材申请已提交，等待审批",
        "request_id": request_id,
        "consumable_name": consumable.name,
        "requested_quantity": request.quantity,
        "unit": request.unit,
        "purpose": request.purpose
    }

# 批量删除耗材
class ConsumableBatchDelete(BaseModel):
    consumable_ids: List[int]

@router.post("/batch-delete", response_model=dict)
def batch_delete_consumables(
    delete_request: ConsumableBatchDelete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """批量删除耗材（仅管理员）"""
    if not delete_request.consumable_ids:
        raise HTTPException(status_code=400, detail="耗材ID列表不能为空")
    
    # 查找所有要删除的耗材
    consumables = db.query(Consumable).filter(Consumable.id.in_(delete_request.consumable_ids)).all()
    found_ids = [consumable.id for consumable in consumables]
    missing_ids = [consumable_id for consumable_id in delete_request.consumable_ids if consumable_id not in found_ids]
    
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"以下耗材不存在: {missing_ids}"
        )
    
    try:
        # 删除耗材
        for consumable in consumables:
            db.delete(consumable)
        
        db.commit()
        
        return {
            "message": "批量删除耗材成功",
            "deleted_count": len(consumables),
            "deleted_ids": found_ids
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除耗材失败: {str(e)}")

# 批量更新耗材
class ConsumableBatchUpdate(BaseModel):
    consumable_ids: List[int]
    updates: ConsumableUpdate

@router.post("/batch-update", response_model=dict)
def batch_update_consumables(
    update_request: ConsumableBatchUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """批量更新耗材信息（仅管理员）"""
    if not update_request.consumable_ids:
        raise HTTPException(status_code=400, detail="耗材ID列表不能为空")
    
    if not any(update_request.updates.dict().values()):
        raise HTTPException(status_code=400, detail="更新内容不能为空")
    
    # 查找所有要更新的耗材
    consumables = db.query(Consumable).filter(Consumable.id.in_(update_request.consumable_ids)).all()
    found_ids = [consumable.id for consumable in consumables]
    missing_ids = [consumable_id for consumable_id in update_request.consumable_ids if consumable_id not in found_ids]
    
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"以下耗材不存在: {missing_ids}"
        )
    
    try:
        # 更新耗材信息
        update_data = update_request.updates.dict(exclude_unset=True)
        
        for consumable in consumables:
            for key, value in update_data.items():
                if value is not None:
                    setattr(consumable, key, value)
            consumable.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "message": "批量更新耗材成功",
            "updated_count": len(consumables),
            "updated_ids": found_ids,
            "updated_fields": list(update_data.keys())
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新耗材失败: {str(e)}")