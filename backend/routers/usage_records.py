from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import csv
import io

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response

from backend.database import get_db
from backend.models import UsageRecord, User, Reagent, Consumable
from backend.auth import get_current_user

router = APIRouter()

# Pydantic模型
class UsageRecordResponse(BaseModel):
    id: int
    request_id: int
    item_type: str
    item_id: int
    item_name: str
    quantity_used: float
    unit: str
    user_id: int
    user_name: str
    approved_by_id: int
    approved_by_name: str
    purpose: str
    notes: Optional[str]
    used_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class UsageRecordCreate(BaseModel):
    request_id: int
    item_type: str
    item_id: int
    item_name: str
    quantity_used: float
    unit: str
    user_id: int
    approved_by_id: int
    purpose: str
    notes: Optional[str] = None

# 获取使用记录列表
@router.get("/", response_model=List[UsageRecordResponse])
async def get_usage_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_type: Optional[str] = Query(None, description="过滤物品类型: reagent 或 consumable"),
    user_id: Optional[int] = Query(None, description="过滤使用者ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取使用记录列表，支持多种过滤条件"""
    
    query = db.query(UsageRecord)
    
    # 应用过滤条件
    if item_type:
        query = query.filter(UsageRecord.item_type == item_type)
    
    if user_id:
        query = query.filter(UsageRecord.user_id == user_id)
    
    if start_date:
        query = query.filter(UsageRecord.used_at >= start_date)
    
    if end_date:
        query = query.filter(UsageRecord.used_at <= end_date)
    
    # 按使用时间倒序排列
    records = query.order_by(desc(UsageRecord.used_at)).offset(skip).limit(limit).all()
    
    # 构建响应数据
    result = []
    for record in records:
        user = db.query(User).filter(User.id == record.user_id).first()
        approved_by = db.query(User).filter(User.id == record.approved_by_id).first()
        
        result.append(UsageRecordResponse(
            id=record.id,
            request_id=record.request_id,
            item_type=record.item_type,
            item_id=record.item_id,
            item_name=record.item_name,
            quantity_used=record.quantity_used,
            unit=record.unit,
            user_id=record.user_id,
            user_name=user.username if user else "未知用户",
            approved_by_id=record.approved_by_id,
            approved_by_name=approved_by.username if approved_by else "未知管理员",
            purpose=record.purpose,
            notes=record.notes,
            used_at=record.used_at,
            created_at=record.created_at
        ))
    
    return result

# 获取我的使用记录
@router.get("/my-records", response_model=List[UsageRecordResponse])
async def get_my_usage_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_type: Optional[str] = Query(None, description="过滤物品类型: reagent 或 consumable"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的使用记录"""
    
    query = db.query(UsageRecord).filter(UsageRecord.user_id == current_user.id)
    
    if item_type:
        query = query.filter(UsageRecord.item_type == item_type)
    
    records = query.order_by(desc(UsageRecord.used_at)).offset(skip).limit(limit).all()
    
    result = []
    for record in records:
        approved_by = db.query(User).filter(User.id == record.approved_by_id).first()
        
        result.append(UsageRecordResponse(
            id=record.id,
            request_id=record.request_id,
            item_type=record.item_type,
            item_id=record.item_id,
            item_name=record.item_name,
            quantity_used=record.quantity_used,
            unit=record.unit,
            user_id=record.user_id,
            user_name=current_user.username,
            approved_by_id=record.approved_by_id,
            approved_by_name=approved_by.username if approved_by else "未知管理员",
            purpose=record.purpose,
            notes=record.notes,
            used_at=record.used_at,
            created_at=record.created_at
        ))
    
    return result

# 获取使用记录详情
@router.get("/{record_id}", response_model=UsageRecordResponse)
async def get_usage_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取使用记录详情"""
    
    record = db.query(UsageRecord).filter(UsageRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="使用记录不存在")
    
    user = db.query(User).filter(User.id == record.user_id).first()
    approved_by = db.query(User).filter(User.id == record.approved_by_id).first()
    
    return UsageRecordResponse(
        id=record.id,
        request_id=record.request_id,
        item_type=record.item_type,
        item_id=record.item_id,
        item_name=record.item_name,
        quantity_used=record.quantity_used,
        unit=record.unit,
        user_id=record.user_id,
        user_name=user.username if user else "未知用户",
        approved_by_id=record.approved_by_id,
        approved_by_name=approved_by.username if approved_by else "未知管理员",
        purpose=record.purpose,
        notes=record.notes,
        used_at=record.used_at,
        created_at=record.created_at
    )

# 获取使用统计
@router.get("/stats/summary")
async def get_usage_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取使用统计信息"""
    
    query = db.query(UsageRecord)
    
    if start_date:
        query = query.filter(UsageRecord.used_at >= start_date)
    
    if end_date:
        query = query.filter(UsageRecord.used_at <= end_date)
    
    records = query.all()
    
    # 统计数据
    total_records = len(records)
    reagent_records = len([r for r in records if r.item_type == 'reagent'])
    consumable_records = len([r for r in records if r.item_type == 'consumable'])
    
    # 按用户统计
    user_stats = {}
    for record in records:
        user_id = record.user_id
        if user_id not in user_stats:
            user = db.query(User).filter(User.id == user_id).first()
            user_stats[user_id] = {
                'user_name': user.username if user else '未知用户',
                'total_usage': 0,
                'reagent_usage': 0,
                'consumable_usage': 0
            }
        
        user_stats[user_id]['total_usage'] += 1
        if record.item_type == 'reagent':
            user_stats[user_id]['reagent_usage'] += 1
        else:
            user_stats[user_id]['consumable_usage'] += 1
    
    return {
        'total_records': total_records,
        'reagent_records': reagent_records,
        'consumable_records': consumable_records,
        'user_stats': list(user_stats.values())
    }

# 导出使用记录为CSV
@router.get("/export-csv")
async def export_usage_records_csv(
    item_type: Optional[str] = Query(None, description="过滤物品类型: reagent 或 consumable"),
    user_id: Optional[int] = Query(None, description="过滤使用者ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出使用记录为CSV格式"""
    
    query = db.query(UsageRecord)
    
    # 应用过滤条件
    if item_type:
        query = query.filter(UsageRecord.item_type == item_type)
    
    if user_id:
        query = query.filter(UsageRecord.user_id == user_id)
    
    if start_date:
        query = query.filter(UsageRecord.used_at >= start_date)
    
    if end_date:
        query = query.filter(UsageRecord.used_at <= end_date)
    
    # 按使用时间倒序排列
    records = query.order_by(desc(UsageRecord.used_at)).all()
    
    # 创建CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        '记录ID', '申请ID', '物品类型', '物品ID', '物品名称', 
        '使用数量', '单位', '使用者ID', '使用者名称', '批准人ID', 
        '批准人名称', '使用目的', '备注', '使用时间', '创建时间'
    ])
    
    # 写入数据行
    for record in records:
        user = db.query(User).filter(User.id == record.user_id).first()
        approved_by = db.query(User).filter(User.id == record.approved_by_id).first()
        
        writer.writerow([
            record.id,
            record.request_id,
            record.item_type,
            record.item_id,
            record.item_name,
            record.quantity_used,
            record.unit,
            record.user_id,
            user.username if user else "未知用户",
            record.approved_by_id,
            approved_by.username if approved_by else "未知管理员",
            record.purpose,
            record.notes or "",
            record.used_at.isoformat() if record.used_at else "",
            record.created_at.isoformat() if record.created_at else ""
        ])
    
    # 创建响应
    output.seek(0)
    response = Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=usage_records.csv"
        }
    )
    
    return response