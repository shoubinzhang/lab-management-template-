from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from enum import Enum

from database import get_db
from models import User, Request
from auth import get_current_user
from permissions import require_permission, Permissions
from pydantic import BaseModel

# 创建路由器
router = APIRouter(prefix="/api/approvals", tags=["approvals"])

# 申请状态枚举
class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# 申请类型枚举
class RequestType(str, Enum):
    REAGENT = "reagent"
    CONSUMABLE = "consumable"

# Pydantic模型
class ApprovalRequest(BaseModel):
    request_id: int
    request_type: RequestType
    item_id: int
    item_name: str
    quantity: float
    unit: str
    purpose: str
    notes: Optional[str] = None
    requester_id: int
    requester_name: str
    created_at: datetime
    status: RequestStatus

class ApprovalAction(BaseModel):
    action: str  # "approve" or "reject"
    notes: Optional[str] = None

class ApprovalResponse(BaseModel):
    message: str
    request_id: int
    status: RequestStatus
    approved_by: str
    approved_at: datetime

# 使用数据库存储申请数据

@router.get("/", response_model=List[ApprovalRequest])
@require_permission(Permissions.REQUEST_APPROVE)
def get_pending_requests(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取待审批的申请列表"""
    # 从数据库查询所有待审批的申请
    pending_requests = db.query(Request).filter(Request.status == RequestStatus.PENDING).all()
    
    # 转换为响应模型格式
    result = []
    for req in pending_requests:
        result.append(ApprovalRequest(
            request_id=req.id,
            request_type=RequestType(req.request_type),
            item_id=req.item_id,
            item_name=req.item_name,
            quantity=req.quantity,
            unit=req.unit,
            purpose=req.purpose,
            notes=req.notes,
            requester_id=req.requester_id,
            requester_name=req.requester.username,
            created_at=req.created_at,
            status=RequestStatus(req.status)
        ))
    
    return result

@router.get("/{request_id}", response_model=ApprovalRequest)
@require_permission(Permissions.REQUEST_APPROVE)
def get_request_detail(request_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取特定申请的详细信息"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    return ApprovalRequest(
        request_id=request.id,
        request_type=RequestType(request.request_type),
        item_id=request.item_id,
        item_name=request.item_name,
        quantity=request.quantity,
        unit=request.unit,
        purpose=request.purpose,
        notes=request.notes,
        requester_id=request.requester_id,
        requester_name=request.requester.username,
        created_at=request.created_at,
        status=RequestStatus(request.status)
    )

@router.post("/{request_id}/approve", response_model=ApprovalResponse)
@require_permission(Permissions.REQUEST_APPROVE)
def approve_request(request_id: int, action: ApprovalAction, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """审批申请（批准或拒绝）"""
    # 查找申请
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    # 检查申请状态
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="申请已经被处理")
    
    # 更新申请状态
    if action.action == "approve":
        # 批准前进行库存检查和扣减
        try:
            # 导入模型
            from models import Reagent, Consumable, UsageRecord
            
            # 根据申请类型检查库存
            if request.request_type == RequestType.REAGENT:
                item = db.query(Reagent).filter(Reagent.id == request.item_id).first()
                if not item:
                    raise HTTPException(status_code=404, detail="试剂不存在")
                
                # 检查库存是否充足
                if item.quantity < request.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"库存不足。当前库存：{item.quantity} {item.unit}，申请数量：{request.quantity} {request.unit}"
                    )
                
                # 扣减库存
                item.quantity -= request.quantity
                item.updated_at = datetime.utcnow()
                
            elif request.request_type == RequestType.CONSUMABLE:
                item = db.query(Consumable).filter(Consumable.id == request.item_id).first()
                if not item:
                    raise HTTPException(status_code=404, detail="耗材不存在")
                
                # 检查库存是否充足
                if item.quantity < request.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"库存不足。当前库存：{item.quantity} {item.unit}，申请数量：{request.quantity} {request.unit}"
                    )
                
                # 扣减库存
                item.quantity -= request.quantity
                item.updated_at = datetime.utcnow()
            
            else:
                raise HTTPException(status_code=400, detail="不支持的申请类型")
            
            # 创建使用记录
            usage_record = UsageRecord(
                request_id=request.id,
                item_type=request.request_type.lower(),
                item_id=request.item_id,
                item_name=request.item_name,
                quantity_used=request.quantity,
                unit=request.unit,
                user_id=request.requester_id,
                approved_by_id=current_user["id"],
                purpose=request.purpose,
                notes=action.notes,
                used_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(usage_record)
            
            new_status = RequestStatus.APPROVED
            message = f"申请已批准，库存已扣减。剩余库存：{item.quantity} {item.unit}"
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 处理其他异常
            db.rollback()
            raise HTTPException(status_code=500, detail=f"处理批准时发生错误：{str(e)}")
            
    elif action.action == "reject":
        new_status = RequestStatus.REJECTED
        message = "申请已拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    # 更新申请记录
    request.status = new_status
    request.approved_by_id = current_user["id"]
    request.approved_at = datetime.utcnow()
    request.approval_notes = action.notes
    request.updated_at = datetime.utcnow()
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存数据时发生错误：{str(e)}")
    
    return ApprovalResponse(
        message=message,
        request_id=request_id,
        status=new_status,
        approved_by=current_user["username"],
        approved_at=datetime.utcnow()
    )

@router.get("/history/", response_model=List[ApprovalRequest])
@require_permission(Permissions.REQUEST_APPROVE)
def get_approval_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取审批历史记录"""
    # 从数据库查询所有已处理的申请
    processed_requests = db.query(Request).filter(Request.status != RequestStatus.PENDING).all()
    
    # 转换为响应模型格式
    result = []
    for req in processed_requests:
        result.append(ApprovalRequest(
            request_id=req.id,
            request_type=RequestType(req.request_type),
            item_id=req.item_id,
            item_name=req.item_name,
            quantity=req.quantity,
            unit=req.unit,
            purpose=req.purpose,
            notes=req.notes,
            requester_id=req.requester_id,
            requester_name=req.requester.username,
            created_at=req.created_at,
            status=RequestStatus(req.status)
        ))
    
    return result

# 获取当前用户的申请记录
@router.get("/my-requests", response_model=List[ApprovalRequest])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户的所有申请记录"""
    requests = db.query(Request).filter(
        Request.requester_id == current_user["id"]
    ).order_by(Request.created_at.desc()).all()
    
    result = []
    for req in requests:
        result.append(ApprovalRequest(
            request_id=req.id,
            request_type=RequestType(req.request_type),
            item_id=req.item_id,
            item_name=req.item_name,
            quantity=req.quantity,
            unit=req.unit,
            purpose=req.purpose,
            notes=req.notes,
            requester_id=req.requester_id,
            requester_name=current_user["username"],
            created_at=req.created_at,
            status=RequestStatus(req.status)
        ))
    
    return result

# 内部函数：添加新申请到数据库（由其他模块调用）
def add_request(request_type: RequestType, item_id: int, item_name: str, quantity: float, unit: str, purpose: str, requester_id: int, requester_name: str, notes: str = None):
    """添加新的申请到审批队列"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        new_request = Request(
            request_type=request_type.value,
            item_id=item_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            purpose=purpose,
            notes=notes,
            requester_id=requester_id,
            status=RequestStatus.PENDING.value,
            created_at=datetime.utcnow()
        )
        
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return new_request.id
    finally:
        db.close()