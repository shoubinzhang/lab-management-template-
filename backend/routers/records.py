from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import ExperimentRecord, User
from backend.auth import get_current_user, require_admin
from backend.permissions import require_permission, Permissions
from pydantic import BaseModel

# 创建路由器
router = APIRouter(prefix="/api/records", tags=["records"])

# Pydantic模型
class RecordCreate(BaseModel):
    title: str
    description: Optional[str] = None
    experiment_type: Optional[str] = None
    result: Optional[str] = None
    notes: Optional[str] = None

class RecordUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    experiment_type: Optional[str] = None
    result: Optional[str] = None
    notes: Optional[str] = None

class RecordResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    experiment_type: Optional[str]
    result: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int

    class Config:
        from_attributes = True

# 认证依赖已从主app导入

# 路由处理函数
@router.get("/", response_model=List[RecordResponse])
@require_permission(Permissions.RECORD_READ)
def get_records(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取所有实验记录"""
    records = db.query(ExperimentRecord).all()
    return records

@router.get("/{record_id}", response_model=RecordResponse)
@require_permission(Permissions.RECORD_READ)
def get_record(record_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取特定实验记录"""
    record = db.query(ExperimentRecord).filter(ExperimentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record

@router.post("/", response_model=dict)
@require_permission(Permissions.RECORD_CREATE)
def create_record(record: RecordCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """创建新的实验记录"""
    db_record = ExperimentRecord(
        **record.dict(),
        user_id=current_user["id"],
        created_at=datetime.utcnow()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return {"message": "记录创建成功", "record_id": db_record.id}

@router.put("/{record_id}", response_model=dict)
@require_permission(Permissions.RECORD_UPDATE)
def update_record(record_id: int, record: RecordUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """更新实验记录"""
    db_record = db.query(ExperimentRecord).filter(ExperimentRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限（只有创建者或管理员可以修改）
    if db_record.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此记录")
    
    for key, value in record.dict(exclude_unset=True).items():
        setattr(db_record, key, value)
    
    db_record.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "记录更新成功"}

@router.delete("/{record_id}", response_model=dict)
@require_permission(Permissions.RECORD_DELETE)
def delete_record(record_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """删除实验记录"""
    db_record = db.query(ExperimentRecord).filter(ExperimentRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限（只有创建者或管理员可以删除）
    if db_record.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="无权限删除此记录")
    
    db.delete(db_record)
    db.commit()
    return {"message": "记录删除成功"}

@router.get("/user/{user_id}", response_model=List[RecordResponse])
@require_permission(Permissions.DATA_ACCESS)
def get_user_records(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取特定用户的实验记录"""
    records = db.query(ExperimentRecord).filter(ExperimentRecord.user_id == user_id).all()
    return records
