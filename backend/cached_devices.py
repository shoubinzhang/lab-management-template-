from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

from database import get_db
from models import Device, DeviceMaintenance, DeviceReservation, User, ExperimentRecord
from auth import get_current_user, require_admin
from permissions import require_permission, Permissions, PermissionChecker, get_permission_checker
from pydantic import BaseModel
from redis_cache import RedisCache, cache_result, invalidate_cache_pattern
from redis_config import redis_config
from cache_config import CacheConfig, CacheType, invalidate_related_cache
from query_optimization import OptimizedQueries, monitor_query_performance

# 创建路由器
router = APIRouter(prefix="/devices", tags=["devices"])
# 初始化Redis缓存
redis_cache = RedisCache(redis_config)

# Pydantic模型
class DeviceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "available"
    location: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    maintenance_interval: Optional[int] = 90
    responsible_person: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    maintenance_interval: Optional[int] = None
    responsible_person: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    location: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    purchase_date: Optional[date]
    warranty_expiry: Optional[date]
    last_maintenance: Optional[date]
    next_maintenance: Optional[date]
    maintenance_interval: Optional[int]
    responsible_person: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaginatedDeviceResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

class MaintenanceCreate(BaseModel):
    device_id: int
    maintenance_type: str
    description: str
    performed_by: str
    maintenance_date: date
    cost: Optional[float] = 0.0
    notes: Optional[str] = None

class MaintenanceResponse(BaseModel):
    id: int
    maintenance_type: str
    description: str
    performed_by: str
    maintenance_date: date
    cost: Optional[float]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 设备预约相关模型
class ReservationCreate(BaseModel):
    device_id: int
    start_time: datetime
    end_time: datetime
    purpose: str
    notes: Optional[str] = None

class ReservationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ReservationResponse(BaseModel):
    id: int
    device_id: Optional[int] = None  # 允许device_id为None，处理数据不一致情况
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 设备借用相关模型
class DeviceBorrowCreate(BaseModel):
    notes: Optional[str] = None

class DeviceBorrowResponse(BaseModel):
    id: int
    device_id: int
    user_id: int
    borrow_time: datetime
    return_time: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 缓存辅助函数
def serialize_device(device):
    """序列化设备对象为字典"""
    return {
        "id": device.id,
        "name": device.name,
        "description": device.description,
        "status": device.status,
        "location": device.location,
        "model": device.model,
        "serial_number": device.serial_number,
        "purchase_date": device.purchase_date.isoformat() if device.purchase_date else None,
        "warranty_expiry": device.warranty_expiry.isoformat() if device.warranty_expiry else None,
        "last_maintenance": device.last_maintenance.isoformat() if device.last_maintenance else None,
        "next_maintenance": device.next_maintenance.isoformat() if device.next_maintenance else None,
        "maintenance_interval": device.maintenance_interval,
        "responsible_person": device.responsible_person,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None
    }

def deserialize_device(data):
    """反序列化字典为设备响应对象"""
    if data.get("purchase_date"):
        data["purchase_date"] = date.fromisoformat(data["purchase_date"])
    if data.get("warranty_expiry"):
        data["warranty_expiry"] = date.fromisoformat(data["warranty_expiry"])
    if data.get("last_maintenance"):
        data["last_maintenance"] = date.fromisoformat(data["last_maintenance"])
    if data.get("next_maintenance"):
        data["next_maintenance"] = date.fromisoformat(data["next_maintenance"])
    if data.get("created_at"):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    if data.get("updated_at"):
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
    return DeviceResponse(**data)

# 缓存路由处理函数
@router.get("", response_model=PaginatedDeviceResponse)
@monitor_query_performance
def get_devices(
    page: int = 1,
    per_page: int = 50,
    status: Optional[str] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_checker: PermissionChecker = Depends(get_permission_checker)
):
    """获取设备列表（带缓存）"""
    # 检查权限
    if not permission_checker.user_has_permission(current_user, Permissions.DEVICE_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要设备读取权限"
        )
    
    # 验证分页参数
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 1000:
        per_page = 50
    
    # 生成缓存键
    cache_key = CacheConfig.get_cache_key(
        CacheType.DEVICES, 
        f"list:page={page}:per_page={per_page}:status={status}:location={location}:search={search}:sort_by={sort_by}:sort_order={sort_order}"
    )
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return PaginatedDeviceResponse(**cached_data)
    
    # 从数据库查询
    query = db.query(Device)
    
    # 状态筛选
    if status:
        query = query.filter(Device.status == status)
    
    # 位置筛选
    if location:
        query = query.filter(Device.location == location)
    
    # 搜索功能
    if search:
        query = query.filter(
            Device.name.contains(search) |
            Device.model.contains(search) |
            Device.serial_number.contains(search) |
            Device.description.contains(search)
        )
    
    # 排序
    if sort_by == "name":
        query = query.order_by(Device.name.asc() if sort_order == "asc" else Device.name.desc())
    elif sort_by == "status":
        query = query.order_by(Device.status.asc() if sort_order == "asc" else Device.status.desc())
    elif sort_by == "location":
        query = query.order_by(Device.location.asc() if sort_order == "asc" else Device.location.desc())
    elif sort_by == "created_at":
        query = query.order_by(Device.created_at.asc() if sort_order == "asc" else Device.created_at.desc())
    
    # 分页
    total = query.count()
    devices = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # 构建设备详细信息
    items = []
    for device in devices:
        device_data = serialize_device(device)
        
        # 添加维护状态
        if device.next_maintenance:
            days_until = (device.next_maintenance - datetime.now().date()).days
            device_data["maintenance_status"] = {
                "days_until_maintenance": days_until,
                "needs_maintenance": days_until <= 7
            }
        
        # 添加预约信息
        current_reservation = db.query(DeviceReservation).filter(
            DeviceReservation.device_id == device.id,
            DeviceReservation.start_time <= datetime.now(),
            DeviceReservation.end_time >= datetime.now(),
            DeviceReservation.status == "confirmed"
        ).first()
        
        if current_reservation:
            device_data["current_reservation"] = {
                "user_id": current_reservation.user_id,
                "start_time": current_reservation.start_time.isoformat(),
                "end_time": current_reservation.end_time.isoformat(),
                "purpose": current_reservation.purpose
            }
        
        items.append(device_data)
    
    # 构建响应
    pages = (total + per_page - 1) // per_page
    result = {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.DEVICES)
    redis_cache.set(cache_key, result, ttl=ttl)
    
    return PaginatedDeviceResponse(**result)

@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个设备（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.DEVICES, f"detail:id={device_id}")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return deserialize_device(cached_data)
    
    # 从数据库查询
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 序列化并缓存
    data = serialize_device(device)
    ttl = CacheConfig.get_ttl(CacheType.DEVICES)
    redis_cache.set(cache_key, data, ttl=ttl)
    
    return DeviceResponse.from_orm(device)

@router.post("", response_model=dict)
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建设备（清除相关缓存）"""
    # 数据清理和验证
    device_data = device.dict()
    
    # 清理序列号字段
    if device_data.get('serial_number') in [None, '', '/', '-']:
        device_data['serial_number'] = None
    
    # 检查序列号唯一性（仅当序列号不为空时）
    if device_data.get('serial_number'):
        existing = db.query(Device).filter(Device.serial_number == device_data['serial_number']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"序列号 '{device_data['serial_number']}' 已存在，设备名称: {existing.name}")
    
    try:
        db_device = Device(**device_data)
        
        # 计算下次维护日期
        if device.purchase_date and device.maintenance_interval:
            db_device.next_maintenance = device.purchase_date + timedelta(days=device.maintenance_interval)
        
        db.add(db_device)
        db.commit()
    except Exception as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e):
            if "serial_number" in str(e):
                raise HTTPException(status_code=400, detail=f"序列号 '{device.serial_number}' 已存在")
            else:
                raise HTTPException(status_code=400, detail="数据重复，请检查设备信息")
        else:
            raise HTTPException(status_code=500, detail=f"创建设备失败: {str(e)}")
    
    # 获取创建的设备ID
    device_id = db_device.id
    
    # 清除相关缓存
    patterns = CacheConfig.get_invalidation_patterns(CacheType.DEVICES)
    for pattern in patterns:
        invalidate_cache_pattern(pattern)
    
    return {"message": "设备创建成功", "id": device_id}

@router.put("/{device_id}", response_model=dict)
def update_device(
    device_id: int,
    device: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新设备（清除相关缓存）"""
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 检查序列号唯一性
    if device.serial_number and device.serial_number != db_device.serial_number:
        existing = db.query(Device).filter(Device.serial_number == device.serial_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="序列号已存在")
    
    # 更新字段
    for field, value in device.dict(exclude_unset=True).items():
        setattr(db_device, field, value)
    
    db_device.updated_at = datetime.utcnow()
    db.commit()
    
    # 清除相关缓存
    patterns = CacheConfig.get_invalidation_patterns(CacheType.DEVICES)
    for pattern in patterns:
        invalidate_cache_pattern(pattern)
    
    return {"message": "设备更新成功"}

@router.delete("/{device_id}", response_model=dict)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除设备（安全删除，先删除关联数据）"""
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    try:
        # 1. 删除设备维护记录
        maintenance_records = db.query(DeviceMaintenance).filter(
            DeviceMaintenance.device_id == device_id
        ).all()
        maintenance_count = len(maintenance_records)
        for record in maintenance_records:
            db.delete(record)
        
        # 2. 删除设备预约记录
        reservation_records = db.query(DeviceReservation).filter(
            DeviceReservation.device_id == device_id
        ).all()
        reservation_count = len(reservation_records)
        for record in reservation_records:
            db.delete(record)
        
        # 3. 删除实验记录
        experiment_records = db.query(ExperimentRecord).filter(
            ExperimentRecord.device_id == device_id
        ).all()
        experiment_count = len(experiment_records)
        for record in experiment_records:
            db.delete(record)
        
        # 4. 删除设备本身
        db.delete(db_device)
        db.commit()
        
        # 清除相关缓存
        patterns = CacheConfig.get_invalidation_patterns(CacheType.DEVICES)
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
        
        return {
            "message": "设备删除成功",
            "maintenance_records_deleted": maintenance_count,
            "reservation_records_deleted": reservation_count,
            "experiment_records_deleted": experiment_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/bulk-delete", response_model=dict)
def bulk_delete_devices(
    device_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """批量删除设备（安全删除，先删除关联数据）"""
    if not device_ids:
        raise HTTPException(status_code=400, detail="设备ID列表不能为空")
    
    # 查找所有要删除的设备
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    found_ids = [device.id for device in devices]
    missing_ids = [device_id for device_id in device_ids if device_id not in found_ids]
    
    if missing_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"以下设备不存在: {missing_ids}"
        )
    
    # 安全删除设备（先删除关联数据）
    try:
        # 1. 删除设备维护记录
        maintenance_records = db.query(DeviceMaintenance).filter(
            DeviceMaintenance.device_id.in_(device_ids)
        ).all()
        maintenance_count = len(maintenance_records)
        for record in maintenance_records:
            db.delete(record)
        
        # 2. 删除设备预约记录
        reservation_records = db.query(DeviceReservation).filter(
            DeviceReservation.device_id.in_(device_ids)
        ).all()
        reservation_count = len(reservation_records)
        for record in reservation_records:
            db.delete(record)
        
        # 3. 删除实验记录
        experiment_records = db.query(ExperimentRecord).filter(
            ExperimentRecord.device_id.in_(device_ids)
        ).all()
        experiment_count = len(experiment_records)
        for record in experiment_records:
            db.delete(record)
        
        # 4. 删除设备本身
        for device in devices:
            db.delete(device)
        
        db.commit()
        
        # 清除相关缓存
        patterns = CacheConfig.get_invalidation_patterns(CacheType.DEVICES)
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
        
        return {
            "message": f"成功删除 {len(device_ids)} 个设备",
            "deleted_count": len(device_ids),
            "deleted_ids": device_ids,
            "maintenance_records_deleted": maintenance_count,
            "reservation_records_deleted": reservation_count,
            "experiment_records_deleted": experiment_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")

@router.get("/maintenance-needed/list", response_model=List[dict])
@monitor_query_performance
def get_devices_needing_maintenance(
    days_ahead: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取需要维护的设备列表（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.DEVICES, f"maintenance_needed:days_ahead={days_ahead}")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 使用优化查询
    optimized_queries = OptimizedQueries(db)
    devices = optimized_queries.get_devices_needing_maintenance(days_ahead)
    
    result = []
    for device in devices:
        device_data = {
            "id": device.id,
            "name": device.name,
            "status": device.status,
            "location": device.location,
            "next_maintenance": device.next_maintenance.isoformat() if device.next_maintenance else None,
            "responsible_person": device.responsible_person,
            "days_until_maintenance": (device.next_maintenance - datetime.now().date()).days if device.next_maintenance else None
        }
        result.append(device_data)
    
    # 缓存结果（较短的TTL，因为这是时间敏感的数据）
    redis_cache.set(cache_key, result, ttl=300)  # 5分钟缓存
    
    return result

@router.get("/{device_id}/maintenance", response_model=List[MaintenanceResponse])
def get_device_maintenance(
    device_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取设备维护记录（带缓存）"""
    cache_key = CacheConfig.get_cache_key(CacheType.DEVICES, f"maintenance:{device_id}")
    
    # 尝试从缓存获取
    cached_data = redis_cache.get(cache_key)
    if cached_data:
        return [MaintenanceResponse(**item) for item in cached_data]
    
    # 从数据库查询
    records = db.query(DeviceMaintenance).filter(DeviceMaintenance.device_id == device_id).all()
    result = [MaintenanceResponse.from_orm(record) for record in records]
    
    # 缓存结果
    ttl = CacheConfig.get_ttl(CacheType.DEVICES)
    redis_cache.set(cache_key, [record.dict() for record in result], ttl=ttl)
    
    return result

@router.post("/{device_id}/maintenance", response_model=dict)
def create_maintenance_record(
    device_id: int,
    maintenance: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建维护记录（清除相关缓存）"""
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 创建维护记录
    db_maintenance = DeviceMaintenance(**maintenance.dict())
    db.add(db_maintenance)
    
    # 更新设备的维护信息
    device.last_maintenance = maintenance.maintenance_date
    if device.maintenance_interval:
        device.next_maintenance = maintenance.maintenance_date + timedelta(days=device.maintenance_interval)
    device.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_maintenance)
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.DEVICES)
    
    return {"message": "维护记录创建成功", "id": db_maintenance.id}

# 设备借用API
# Pydantic模型
class DeviceBorrowCreate(BaseModel):
    notes: Optional[str] = None

class DeviceBorrowResponse(BaseModel):
    id: int
    device_id: int
    user_id: int
    borrow_time: datetime
    return_time: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/{device_id}/borrow", response_model=dict)
def borrow_device(
    device_id: int,
    borrow_data: DeviceBorrowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """借用设备"""
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 检查设备状态是否可用
    if device.status != "available" and device.status != "有效":
        raise HTTPException(status_code=400, detail="设备当前不可借用")
    
    # 检查用户是否已有借用该设备的未归还记录
    existing_borrow = db.query(DeviceBorrow).filter(
        DeviceBorrow.device_id == device_id,
        DeviceBorrow.user_id == current_user.id,
        DeviceBorrow.status == "borrowed"
    ).first()
    
    if existing_borrow:
        raise HTTPException(status_code=400, detail="您已借用该设备，请先归还")
    
    try:
        # 创建借用记录
        borrow_record = DeviceBorrow(
            device_id=device_id,
            user_id=current_user.id,
            notes=borrow_data.notes
        )
        db.add(borrow_record)
        
        # 更新设备状态
        device.status = "in_use" if device.status == "available" else "使用中"
        db.commit()
        
        # 清除相关缓存
        invalidate_related_cache(CacheType.DEVICES)
        
        return {
            "message": "设备借用成功",
            "borrow_id": borrow_record.id,
            "device_name": device.name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"借用设备失败: {str(e)}")

@router.post("/{device_id}/return", response_model=dict)
def return_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """归还设备"""
    # 查找用户借用该设备的未归还记录
    borrow_record = db.query(DeviceBorrow).filter(
        DeviceBorrow.device_id == device_id,
        DeviceBorrow.user_id == current_user.id,
        DeviceBorrow.status == "borrowed"
    ).first()
    
    if not borrow_record:
        raise HTTPException(status_code=404, detail="未找到您的借用记录")
    
    try:
        # 更新借用记录
        borrow_record.status = "returned"
        borrow_record.return_time = datetime.utcnow()
        
        # 更新设备状态
        device = db.query(Device).filter(Device.id == device_id).first()
        device.status = "available" if device.status == "in_use" else "有效"
        
        db.commit()
        
        # 清除相关缓存
        invalidate_related_cache(CacheType.DEVICES)
        
        return {
            "message": "设备归还成功",
            "device_name": device.name,
            "borrow_duration": (borrow_record.return_time - borrow_record.borrow_time).total_seconds() / 3600  # 借用时长（小时）
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"归还设备失败: {str(e)}")

@router.get("/{device_id}/borrows", response_model=List[DeviceBorrowResponse])
def get_device_borrows(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备的借用记录"""
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 获取借用记录
    borrows = db.query(DeviceBorrow).filter(
        DeviceBorrow.device_id == device_id
    ).order_by(DeviceBorrow.borrow_time.desc()).all()
    
    return borrows

# 设备预约相关API
@router.post("/{device_id}/reservations", response_model=dict)
def create_device_reservation(
    device_id: int,
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建设备预约"""
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 检查设备状态是否可用
    if device.status not in ["available", "有效"]:
        raise HTTPException(status_code=400, detail="设备当前不可预约")
    
    # 检查预约时间是否合法
    if reservation.start_time >= reservation.end_time:
        raise HTTPException(status_code=400, detail="开始时间必须早于结束时间")
    
    # 检查是否与现有预约冲突
    conflicting_reservation = db.query(DeviceReservation).filter(
        DeviceReservation.device_id == device_id,
        DeviceReservation.status.in_(["pending", "approved"]),
        (
            (DeviceReservation.start_time < reservation.end_time) &
            (DeviceReservation.end_time > reservation.start_time)
        )
    ).first()
    
    if conflicting_reservation:
        raise HTTPException(status_code=400, detail="该时间段设备已被预约")
    
    # 创建预约记录
    db_reservation = DeviceReservation(
        device_id=device_id,
        user_id=current_user.id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        purpose=reservation.purpose,
        notes=reservation.notes
    )
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.DEVICES)
    
    return {
        "message": "设备预约创建成功",
        "reservation_id": db_reservation.id,
        "status": "pending"
    }

@router.get("/{device_id}/reservations", response_model=List[ReservationResponse])
def get_device_reservations(
    device_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取设备的预约记录"""
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 构建查询
    query = db.query(DeviceReservation).filter(
        DeviceReservation.device_id == device_id
    )
    
    # 状态筛选
    if status:
        query = query.filter(DeviceReservation.status == status)
    
    # 获取预约记录
    reservations = query.order_by(DeviceReservation.start_time.desc()).all()
    
    return reservations

@router.get("/reservations/my", response_model=List[ReservationResponse])
def get_my_reservations(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的设备预约记录"""
    # 构建查询
    query = db.query(DeviceReservation).filter(
        DeviceReservation.user_id == current_user.id
    )
    
    # 状态筛选
    if status:
        query = query.filter(DeviceReservation.status == status)
    
    # 获取预约记录
    reservations = query.order_by(DeviceReservation.start_time.desc()).all()
    
    return reservations

@router.put("/reservations/{reservation_id}", response_model=dict)
def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新预约状态或备注"""
    # 查找预约记录
    reservation = db.query(DeviceReservation).filter(
        DeviceReservation.id == reservation_id
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    
    # 检查权限：只有管理员或预约创建者可以更新
    if current_user.id != reservation.user_id and not current_user.role == "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 更新字段
    update_data = reservation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)
    
    reservation.updated_at = datetime.utcnow()
    db.commit()
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.DEVICES)
    
    return {
        "message": "预约更新成功",
        "reservation_id": reservation_id,
        "status": reservation.status
    }

@router.delete("/reservations/{reservation_id}", response_model=dict)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消设备预约"""
    # 查找预约记录
    reservation = db.query(DeviceReservation).filter(
        DeviceReservation.id == reservation_id
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    
    # 检查权限：只有管理员或预约创建者可以取消
    if current_user.id != reservation.user_id and not current_user.role == "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 更新预约状态为已取消
    reservation.status = "cancelled"
    reservation.updated_at = datetime.utcnow()
    db.commit()
    
    # 清除相关缓存
    invalidate_related_cache(CacheType.DEVICES)
    
    return {
        "message": "预约已取消",
        "reservation_id": reservation_id
    }

@router.get("/borrows/my", response_model=List[DeviceBorrowResponse])
def get_my_borrows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的设备借用记录"""
    # 获取用户的借用记录
    borrows = db.query(DeviceBorrow).filter(
        DeviceBorrow.user_id == current_user.id
    ).order_by(DeviceBorrow.borrow_time.desc()).all()
    
    return borrows

# 缓存管理端点
@router.post("/cache/clear", response_model=dict)
def clear_device_cache(
    current_user: User = Depends(require_admin)
):
    """清除设备缓存"""
    invalidate_related_cache(CacheType.DEVICES)
    return {"message": "设备缓存已清除"}

@router.post("/cache/warmup", response_model=dict)
def warmup_device_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """预热设备缓存"""
    # 预热需要维护的设备
    get_devices_needing_maintenance(db=db, current_user=current_user)
    
    # 预热第一页设备数据
    get_devices(db=db, current_user=current_user)
    
    return {"message": "设备缓存预热完成"}

class DeviceBatchImport(BaseModel):
    devices: List[DeviceCreate]

@router.post("/batch-import", response_model=dict)
def batch_import_devices(
    import_data: DeviceBatchImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """批量导入设备"""
    imported_count = 0
    failed_count = 0
    errors = []
    used_serial_numbers = set()  # 跟踪当前事务中使用的序列号
    
    try:
        for i, device_data in enumerate(import_data.devices):
            try:
                # 数据清理和验证
                device_dict = device_data.dict()
                
                # 清理序列号字段
                if device_dict.get('serial_number') in [None, '', '/', '-']:
                    device_dict['serial_number'] = None
                
                # 检查必要字段
                if not device_dict.get('name'):
                    errors.append(f"第{i+1}行: 设备名称不能为空")
                    failed_count += 1
                    continue
                
                # 检查序列号唯一性（包括数据库和当前批次）
                serial_number = device_dict.get('serial_number')
                if serial_number:
                    # 检查数据库中是否已存在
                    existing = db.query(Device).filter(Device.serial_number == serial_number).first()
                    if existing:
                        errors.append(f"第{i+1}行: 序列号 '{serial_number}' 已存在，设备名称: {existing.name}")
                        failed_count += 1
                        continue
                    
                    # 检查当前批次中是否重复
                    if serial_number in used_serial_numbers:
                        errors.append(f"第{i+1}行: 序列号 '{serial_number}' 在导入数据中重复")
                        failed_count += 1
                        continue
                    
                    used_serial_numbers.add(serial_number)
                
                # 创建设备
                db_device = Device(**device_dict)
                
                # 计算下次维护日期
                if device_dict.get('purchase_date') and device_dict.get('maintenance_interval'):
                    db_device.next_maintenance = device_dict['purchase_date'] + timedelta(days=device_dict['maintenance_interval'])
                
                db.add(db_device)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"第{i+1}行: {str(e)}")
                failed_count += 1
        
        # 提交事务
        db.commit()
        
        # 清除相关缓存
        patterns = CacheConfig.get_invalidation_patterns(CacheType.DEVICES)
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
        
        return {
            "message": "批量导入完成",
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors[:10],  # 只返回前10个错误
            "total_errors": len(errors)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")