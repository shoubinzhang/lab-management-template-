from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import Reagent, User
from backend.auth import get_current_user, require_admin
from backend.permissions import check_permission, Permissions
from pydantic import BaseModel

# 创建路由器
router = APIRouter(prefix="/api/reagents", tags=["reagents"])

# Pydantic模型
class ReagentCreate(BaseModel):
    name: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    product_number: Optional[str] = None  # 产品编号
    batch_number: Optional[str] = None   # 批号（原lot_number）
    expiry_date: Optional[datetime] = None
    quantity: Optional[float] = 0.0
    unit: Optional[str] = "ml"
    min_threshold: Optional[float] = 10.0  # 最小库存阈值
    location: Optional[str] = None
    storage_temperature: Optional[str] = None  # 储存温度
    storage_location: Optional[str] = None     # 储存位置
    cas_number: Optional[str] = None           # CAS号
    molecular_formula: Optional[str] = None    # 分子式
    molecular_weight: Optional[float] = None   # 分子量
    purity: Optional[float] = None             # 纯度
    supplier: Optional[str] = None             # 供应商
    specification: Optional[str] = None       # 规格
    safety_notes: Optional[str] = None        # 安全信息
    price: Optional[float] = None              # 价格

class ReagentUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    product_number: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    min_threshold: Optional[float] = None  # 最小库存阈值
    location: Optional[str] = None
    storage_temperature: Optional[str] = None
    storage_location: Optional[str] = None
    cas_number: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    purity: Optional[float] = None
    supplier: Optional[str] = None
    specification: Optional[str] = None
    safety_notes: Optional[str] = None
    price: Optional[float] = None

class ReagentResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    manufacturer: Optional[str]
    product_number: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[datetime]
    quantity: Optional[float]
    unit: Optional[str]
    min_threshold: Optional[float]  # 最小库存阈值
    location: Optional[str]
    storage_temperature: Optional[str]
    storage_location: Optional[str]
    cas_number: Optional[str]
    molecular_formula: Optional[str]
    molecular_weight: Optional[float]
    purity: Optional[float]
    supplier: Optional[str]
    specification: Optional[str]
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

# 认证依赖已从主app导入

# 分页响应模型
class PaginatedReagentResponse(BaseModel):
    items: List[ReagentResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# 路由处理函数
@router.get("/", response_model=PaginatedReagentResponse)
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
    """获取试剂列表（分页）"""
    # 验证分页参数
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50
    
    query = db.query(Reagent)
    
    # 按类别筛选
    if category:
        query = query.filter(Reagent.category == category)
    
    # 搜索功能
    if search:
        query = query.filter(
            Reagent.name.contains(search) |
            Reagent.manufacturer.contains(search) |
            Reagent.product_number.contains(search) |
            Reagent.batch_number.contains(search) |
            Reagent.cas_number.contains(search) |
            Reagent.molecular_formula.contains(search) |
            Reagent.supplier.contains(search) |
            Reagent.specification.contains(search)
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
    
    return PaginatedReagentResponse(
        items=reagents,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/{reagent_id}", response_model=ReagentResponse)
def get_reagent(
    reagent_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取特定试剂"""
    reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    return reagent

@router.post("/", response_model=ReagentResponse)
def create_reagent(
    reagent: ReagentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建新试剂"""
    db_reagent = Reagent(
        **reagent.dict(),
        created_at=datetime.utcnow()
    )
    db.add(db_reagent)
    db.commit()
    db.refresh(db_reagent)
    return db_reagent

@router.put("/{reagent_id}", response_model=ReagentResponse)
def update_reagent(
    reagent_id: int,
    reagent: ReagentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新试剂信息"""
    db_reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not db_reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    for key, value in reagent.dict(exclude_unset=True).items():
        setattr(db_reagent, key, value)
    
    db_reagent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_reagent)
    return db_reagent

@router.delete("/{reagent_id}", response_model=dict)
def delete_reagent(
    reagent_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """删除试剂"""
    db_reagent = db.query(Reagent).filter(Reagent.id == reagent_id).first()
    if not db_reagent:
        raise HTTPException(status_code=404, detail="试剂不存在")
    
    db.delete(db_reagent)
    db.commit()
    return {"message": "试剂删除成功"}

@router.get("/categories/list", response_model=List[str])
def get_reagent_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有试剂类别"""
    categories = db.query(Reagent.category).distinct().filter(Reagent.category.isnot(None)).all()
    return [category[0] for category in categories if category[0]]

@router.get("/expiring/list", response_model=List[ReagentResponse])
def get_expiring_reagents(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取即将过期的试剂"""
    from datetime import timedelta
    
    expiry_threshold = datetime.utcnow() + timedelta(days=days)
    reagents = db.query(Reagent).filter(
        Reagent.expiry_date.isnot(None),
        Reagent.expiry_date <= expiry_threshold
    ).all()
    
    return reagents

@router.get("/low-stock/list", response_model=List[ReagentResponse])
def get_low_stock_reagents(
    threshold: float = 10.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取库存不足的试剂"""
    reagents = db.query(Reagent).filter(
        Reagent.quantity <= threshold
    ).all()
    
    return reagents

@router.post("/request", response_model=dict)
def request_reagent(
    request: ReagentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.REAGENT_REQUEST))
):
    """申请领用试剂"""
    from backend.routers.approvals import add_request, RequestType
    
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