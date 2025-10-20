from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import jwt
from database import get_db
from models import User, Notification
from notification_service import (
    notification_manager, 
    NotificationService, 
    NotificationType, 
    NotificationPriority
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])
security = HTTPBearer()

# JWT配置（应该从环境变量获取）
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # 从环境变量获取
ALGORITHM = "HS256"

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """从令牌获取当前用户"""
    payload = verify_token(token)
    if payload is None:
        return None
    
    username = payload.get("sub")
    if username is None:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket通知端点"""
    connection_id = None
    user = None
    db = next(get_db())
    
    try:
        await websocket.accept()
        
        # 等待认证消息
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        
        if auth_data.get("type") != "auth":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "需要认证"
            }))
            await websocket.close()
            return
        
        token = auth_data.get("token")
        if not token:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "缺少认证令牌"
            }))
            await websocket.close()
            return
        
        # 验证用户
        user = get_current_user_from_token(token, db)
        if not user:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "无效的认证令牌"
            }))
            await websocket.close()
            return
        
        # 建立连接
        connection_id = await notification_manager.connect(websocket, user.id, db)
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connected",
            "connection_id": connection_id,
            "message": "连接成功"
        }))
        
        # 处理消息循环
        while True:
            message = await websocket.receive_text()
            await notification_manager.handle_message(websocket, connection_id, message, db)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        if connection_id:
            await notification_manager.disconnect(connection_id, db)
        db.close()

def get_current_user_dependency(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """获取当前用户的依赖函数"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少认证令牌")
    
    user = get_current_user_from_token(token.credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    return user

@router.get("/notifications")
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="过滤已读/未读通知"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取用户通知列表"""
    notifications = NotificationService.get_user_notifications(
        db, current_user.id, is_read, limit, offset
    )
    
    result = []
    for notification in notifications:
        result.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "priority": notification.priority,
            "is_read": notification.is_read,
            "data": json.loads(notification.data) if notification.data else None,
            "created_at": notification.created_at.isoformat(),
            "expires_at": notification.expires_at.isoformat() if notification.expires_at else None
        })
    
    return {
        "notifications": result,
        "total": len(result),
        "has_more": len(result) == limit
    }

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """标记通知为已读"""
    success = NotificationService.mark_notification_read(db, notification_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return {"message": "通知已标记为已读"}

@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """标记所有通知为已读"""
    count = NotificationService.mark_all_notifications_read(db, current_user.id)
    
    return {
        "message": f"已标记 {count} 条通知为已读",
        "count": count
    }

@router.get("/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取未读通知数量"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}

@router.post("/notifications/send")
async def send_notification(
    title: str,
    message: str,
    user_id: int,
    notification_type: str = NotificationType.SYSTEM_ALERT,
    priority: str = NotificationPriority.NORMAL,
    data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """发送通知（管理员功能）"""
    # 检查权限（这里简化处理，实际应该检查用户角色）
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证目标用户存在
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    
    await NotificationService.send_notification(
        db, user_id, title, message, notification_type, priority, data
    )
    
    return {"message": "通知发送成功"}

@router.post("/notifications/broadcast")
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = NotificationType.SYSTEM_ALERT,
    priority: str = NotificationPriority.NORMAL,
    data: Optional[dict] = None,
    user_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """广播通知（管理员功能）"""
    # 检查权限
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    
    await NotificationService.send_system_notification(
        db, title, message, notification_type, priority, data, user_ids
    )
    
    return {"message": "通知广播成功"}

@router.get("/notifications/online-users")
async def get_online_users(
    current_user: User = Depends(get_current_user_dependency)
):
    """获取在线用户列表（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    
    online_user_ids = notification_manager.get_online_users()
    
    return {
        "online_users": online_user_ids,
        "count": len(online_user_ids)
    }

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """删除通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "通知已删除"}

@router.post("/notifications/cleanup")
async def cleanup_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """清理过期通知（管理员功能）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 清理过期通知
    expired_count = NotificationService.delete_expired_notifications(db)
    
    # 清理非活跃连接
    inactive_count = NotificationService.cleanup_inactive_connections(db)
    
    return {
        "message": "清理完成",
        "expired_notifications": expired_count,
        "inactive_connections": inactive_count
    }

# 通知触发器函数
class NotificationTriggers:
    """通知触发器 - 在特定事件发生时自动发送通知"""
    
    @staticmethod
    async def trigger_reagent_low_stock(db: Session, reagent_name: str, current_stock: float, min_stock: float):
        """试剂库存不足通知"""
        # 获取需要通知的用户（管理员和相关研究人员）
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        for user in admin_users:
            await NotificationService.send_notification(
                db=db,
                user_id=user.id,
                title="试剂库存不足警告",
                message=f"试剂 {reagent_name} 库存不足，当前库存：{current_stock}，最低库存：{min_stock}",
                notification_type=NotificationType.REAGENT_LOW_STOCK,
                priority=NotificationPriority.HIGH,
                data={
                    "reagent_name": reagent_name,
                    "current_stock": current_stock,
                    "min_stock": min_stock
                }
            )
    
    @staticmethod
    async def trigger_reagent_expiring(db: Session, reagent_name: str, expiry_date: str, days_until_expiry: int):
        """试剂即将过期通知"""
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        for user in admin_users:
            await NotificationService.send_notification(
                db=db,
                user_id=user.id,
                title="试剂即将过期提醒",
                message=f"试剂 {reagent_name} 将在 {days_until_expiry} 天后过期（{expiry_date}）",
                notification_type=NotificationType.REAGENT_EXPIRING,
                priority=NotificationPriority.NORMAL if days_until_expiry > 7 else NotificationPriority.HIGH,
                data={
                    "reagent_name": reagent_name,
                    "expiry_date": expiry_date,
                    "days_until_expiry": days_until_expiry
                }
            )
    
    @staticmethod
    async def trigger_equipment_maintenance(db: Session, device_name: str, maintenance_date: str, user_id: int):
        """设备维护提醒"""
        await NotificationService.send_notification(
            db=db,
            user_id=user_id,
            title="设备维护提醒",
            message=f"设备 {device_name} 需要进行维护，预定维护日期：{maintenance_date}",
            notification_type=NotificationType.EQUIPMENT_MAINTENANCE,
            priority=NotificationPriority.NORMAL,
            data={
                "device_name": device_name,
                "maintenance_date": maintenance_date
            }
        )
    
    @staticmethod
    async def trigger_reservation_approved(db: Session, user_id: int, device_name: str, start_time: str, end_time: str):
        """设备预约批准通知"""
        await NotificationService.send_notification(
            db=db,
            user_id=user_id,
            title="设备预约已批准",
            message=f"您的设备预约已获批准：{device_name}，使用时间：{start_time} 至 {end_time}",
            notification_type=NotificationType.RESERVATION_APPROVED,
            priority=NotificationPriority.NORMAL,
            data={
                "device_name": device_name,
                "start_time": start_time,
                "end_time": end_time
            }
        )
    
    @staticmethod
    async def trigger_reservation_rejected(db: Session, user_id: int, device_name: str, reason: str):
        """设备预约拒绝通知"""
        await NotificationService.send_notification(
            db=db,
            user_id=user_id,
            title="设备预约被拒绝",
            message=f"您的设备预约被拒绝：{device_name}，原因：{reason}",
            notification_type=NotificationType.RESERVATION_REJECTED,
            priority=NotificationPriority.NORMAL,
            data={
                "device_name": device_name,
                "reason": reason
            }
        )

# 导出路由和触发器
__all__ = ["router", "NotificationTriggers"]