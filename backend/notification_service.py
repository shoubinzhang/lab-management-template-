import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from models import Notification, WebSocketConnection, User
from database import get_db
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """通知管理器 - 处理WebSocket连接和通知分发"""
    
    def __init__(self):
        # 活跃的WebSocket连接 {user_id: {connection_id: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # 连接ID到用户ID的映射
        self.connection_user_map: Dict[str, int] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, db: Session) -> str:
        """建立WebSocket连接"""
        # WebSocket已经在路由中accept了，这里不需要再次accept
        
        connection_id = str(uuid.uuid4())
        
        # 添加到活跃连接
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][connection_id] = websocket
        self.connection_user_map[connection_id] = user_id
        
        # 保存到数据库
        db_connection = WebSocketConnection(
            user_id=user_id,
            connection_id=connection_id,
            is_active=True,
            last_ping=datetime.utcnow()
        )
        db.add(db_connection)
        db.commit()
        
        logger.info(f"用户 {user_id} 建立WebSocket连接: {connection_id}")
        
        # 发送未读通知
        await self._send_unread_notifications(user_id, connection_id, db)
        
        return connection_id
    
    async def disconnect(self, connection_id: str, db: Session):
        """断开WebSocket连接"""
        if connection_id in self.connection_user_map:
            user_id = self.connection_user_map[connection_id]
            
            # 从活跃连接中移除
            if user_id in self.active_connections and connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.connection_user_map[connection_id]
            
            # 更新数据库
            db_connection = db.query(WebSocketConnection).filter(
                WebSocketConnection.connection_id == connection_id
            ).first()
            if db_connection:
                db_connection.is_active = False
                db.commit()
            
            logger.info(f"用户 {user_id} 断开WebSocket连接: {connection_id}")
    
    async def send_notification_to_user(self, user_id: int, notification_data: dict, db: Session):
        """向特定用户发送通知"""
        if user_id in self.active_connections:
            # 向该用户的所有活跃连接发送通知
            disconnected_connections = []
            
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(notification_data, ensure_ascii=False))
                    
                    # 更新心跳时间
                    db_connection = db.query(WebSocketConnection).filter(
                        WebSocketConnection.connection_id == connection_id
                    ).first()
                    if db_connection:
                        db_connection.last_ping = datetime.utcnow()
                        db.commit()
                        
                except Exception as e:
                    logger.error(f"发送通知失败，连接 {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnected_connections:
                await self.disconnect(connection_id, db)
    
    async def broadcast_notification(self, notification_data: dict, user_ids: Optional[List[int]] = None, db: Session = None):
        """广播通知"""
        if user_ids is None:
            # 向所有在线用户广播
            target_users = list(self.active_connections.keys())
        else:
            target_users = user_ids
        
        for user_id in target_users:
            await self.send_notification_to_user(user_id, notification_data, db)
    
    async def _send_unread_notifications(self, user_id: int, connection_id: str, db: Session):
        """发送未读通知"""
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).limit(50).all()
        
        if unread_notifications:
            websocket = self.active_connections[user_id][connection_id]
            for notification in unread_notifications:
                notification_data = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "priority": notification.priority,
                    "data": json.loads(notification.data) if notification.data else None,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read
                }
                
                try:
                    await websocket.send_text(json.dumps(notification_data, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送未读通知失败: {e}")
                    break
    
    async def handle_message(self, websocket: WebSocket, connection_id: str, message: str, db: Session):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # 心跳消息
                await websocket.send_text(json.dumps({"type": "pong"}))
                
                # 更新心跳时间
                db_connection = db.query(WebSocketConnection).filter(
                    WebSocketConnection.connection_id == connection_id
                ).first()
                if db_connection:
                    db_connection.last_ping = datetime.utcnow()
                    db.commit()
                    
            elif message_type == "mark_read":
                # 标记通知为已读
                notification_id = data.get("notification_id")
                if notification_id:
                    notification = db.query(Notification).filter(
                        Notification.id == notification_id
                    ).first()
                    if notification:
                        notification.is_read = True
                        db.commit()
                        
                        await websocket.send_text(json.dumps({
                            "type": "notification_marked_read",
                            "notification_id": notification_id
                        }))
                        
        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    def get_online_users(self) -> List[int]:
        """获取在线用户列表"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections

# 全局通知管理器实例
notification_manager = NotificationManager()

class NotificationService:
    """通知服务 - 处理通知的创建和发送"""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        priority: str = "normal",
        data: Optional[dict] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            data=json.dumps(data, ensure_ascii=False) if data else None,
            expires_at=expires_at
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    @staticmethod
    async def send_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        priority: str = "normal",
        data: Optional[dict] = None,
        expires_at: Optional[datetime] = None
    ):
        """创建并发送通知"""
        # 创建通知记录
        notification = NotificationService.create_notification(
            db, user_id, title, message, notification_type, priority, data, expires_at
        )
        
        # 实时发送通知
        notification_data = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "priority": notification.priority,
            "data": json.loads(notification.data) if notification.data else None,
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read
        }
        
        await notification_manager.send_notification_to_user(user_id, notification_data, db)
    
    @staticmethod
    async def send_system_notification(
        db: Session,
        title: str,
        message: str,
        notification_type: str = "system_alert",
        priority: str = "normal",
        data: Optional[dict] = None,
        user_ids: Optional[List[int]] = None
    ):
        """发送系统通知"""
        if user_ids is None:
            # 获取所有活跃用户
            users = db.query(User).filter(User.is_active == True).all()
            user_ids = [user.id for user in users]
        
        # 为每个用户创建通知记录
        for user_id in user_ids:
            notification = NotificationService.create_notification(
                db, user_id, title, message, notification_type, priority, data
            )
        
        # 广播通知
        notification_data = {
            "title": title,
            "message": message,
            "type": notification_type,
            "priority": priority,
            "data": data,
            "created_at": datetime.utcnow().isoformat(),
            "is_read": False
        }
        
        await notification_manager.broadcast_notification(notification_data, user_ids, db)
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """获取用户通知"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def mark_all_notifications_read(db: Session, user_id: int) -> int:
        """标记所有通知为已读"""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        
        db.commit()
        return count
    
    @staticmethod
    def delete_expired_notifications(db: Session) -> int:
        """删除过期通知"""
        count = db.query(Notification).filter(
            Notification.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        return count
    
    @staticmethod
    def cleanup_inactive_connections(db: Session, timeout_minutes: int = 30) -> int:
        """清理非活跃连接"""
        timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        count = db.query(WebSocketConnection).filter(
            WebSocketConnection.last_ping < timeout_time,
            WebSocketConnection.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        return count

# 通知类型常量
class NotificationType:
    REAGENT_LOW_STOCK = "reagent_low_stock"
    REAGENT_EXPIRING = "reagent_expiring"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    EXPERIMENT_COMPLETED = "experiment_completed"
    SYSTEM_ALERT = "system_alert"
    APPROVAL_REQUEST = "approval_request"
    RESERVATION_APPROVED = "reservation_approved"
    RESERVATION_REJECTED = "reservation_rejected"
    MAINTENANCE_DUE = "maintenance_due"
    DEVICE_AVAILABLE = "device_available"

# 通知优先级常量
class NotificationPriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"