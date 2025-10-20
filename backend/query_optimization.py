#!/usr/bin/env python3
"""
查询优化模块
提供优化的数据库查询方法，减少N+1查询问题
"""

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from models import Device, Reagent, Consumable, User, DeviceMaintenance, DeviceReservation, Notification
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class OptimizedQueries:
    """
    优化的数据库查询类
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # 设备相关优化查询
    def get_devices_with_maintenance(self, 
                                   status: Optional[str] = None,
                                   location: Optional[str] = None,
                                   limit: int = 100,
                                   offset: int = 0) -> List[Device]:
        """
        获取设备列表，预加载维护记录（避免N+1查询）
        """
        query = self.db.query(Device).options(
            selectinload(Device.maintenance_records),
            selectinload(Device.reservations)
        )
        
        if status:
            query = query.filter(Device.status == status)
        if location:
            query = query.filter(Device.location == location)
            
        return query.offset(offset).limit(limit).all()
    
    def get_devices_needing_maintenance(self, days_ahead: int = 7) -> List[Device]:
        """
        获取需要维护的设备（未来N天内）
        """
        target_date = datetime.now().date() + timedelta(days=days_ahead)
        
        return self.db.query(Device).filter(
            and_(
                Device.next_maintenance <= target_date,
                Device.status != 'maintenance'
            )
        ).order_by(Device.next_maintenance).all()
    
    def get_device_usage_stats(self, device_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取设备使用统计信息
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 预约统计
        reservations = self.db.query(DeviceReservation).filter(
            and_(
                DeviceReservation.device_id == device_id,
                DeviceReservation.created_at >= start_date
            )
        ).all()
        
        # 维护统计
        maintenance_count = self.db.query(func.count(DeviceMaintenance.id)).filter(
            and_(
                DeviceMaintenance.device_id == device_id,
                DeviceMaintenance.maintenance_date >= start_date.date()
            )
        ).scalar()
        
        return {
            'total_reservations': len(reservations),
            'completed_reservations': len([r for r in reservations if r.status == 'completed']),
            'maintenance_count': maintenance_count,
            'utilization_rate': len([r for r in reservations if r.status == 'completed']) / max(days, 1)
        }
    
    # 试剂相关优化查询
    def get_expiring_reagents(self, days_ahead: int = 30) -> List[Reagent]:
        """
        获取即将过期的试剂
        """
        target_date = datetime.now() + timedelta(days=days_ahead)
        
        return self.db.query(Reagent).filter(
            and_(
                Reagent.expiry_date <= target_date,
                Reagent.quantity > 0
            )
        ).order_by(Reagent.expiry_date).all()
    
    def get_low_stock_reagents(self, threshold: float = 10.0) -> List[Reagent]:
        """
        获取库存不足的试剂
        """
        return self.db.query(Reagent).filter(
            Reagent.quantity <= threshold
        ).order_by(Reagent.quantity).all()
    
    def get_reagents_by_category_optimized(self, 
                                         category: Optional[str] = None,
                                         manufacturer: Optional[str] = None,
                                         limit: int = 100,
                                         offset: int = 0) -> List[Reagent]:
        """
        按类别获取试剂（优化查询）
        """
        query = self.db.query(Reagent)
        
        if category:
            query = query.filter(Reagent.category == category)
        if manufacturer:
            query = query.filter(Reagent.manufacturer == manufacturer)
            
        return query.order_by(Reagent.name).offset(offset).limit(limit).all()
    
    # 用户相关优化查询
    def get_users_with_roles(self, 
                           is_active: Optional[bool] = None,
                           role: Optional[str] = None) -> List[User]:
        """
        获取用户列表，预加载角色信息
        """
        query = self.db.query(User).options(
            selectinload(User.roles)
        )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if role:
            query = query.filter(User.role == role)
            
        return query.order_by(User.username).all()
    
    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取用户活动摘要
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 设备预约统计
        reservations = self.db.query(DeviceReservation).filter(
            and_(
                DeviceReservation.user_id == user_id,
                DeviceReservation.created_at >= start_date
            )
        ).all()
        
        # 通知统计
        notifications = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            )
        ).all()
        
        return {
            'total_reservations': len(reservations),
            'pending_reservations': len([r for r in reservations if r.status == 'pending']),
            'completed_reservations': len([r for r in reservations if r.status == 'completed']),
            'total_notifications': len(notifications),
            'unread_notifications': len([n for n in notifications if not n.is_read])
        }
    
    # 通知相关优化查询
    def get_user_notifications_optimized(self, 
                                       user_id: int,
                                       is_read: Optional[bool] = None,
                                       notification_type: Optional[str] = None,
                                       limit: int = 50) -> List[Notification]:
        """
        获取用户通知（优化查询）
        """
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        if notification_type:
            query = query.filter(Notification.type == notification_type)
            
        return query.order_by(desc(Notification.created_at)).limit(limit).all()
    
    def get_system_notifications_summary(self) -> Dict[str, Any]:
        """
        获取系统通知摘要
        """
        # 使用聚合查询减少数据库访问
        total_notifications = self.db.query(func.count(Notification.id)).scalar()
        unread_notifications = self.db.query(func.count(Notification.id)).filter(
            Notification.is_read == False
        ).scalar()
        
        # 按类型统计
        type_stats = self.db.query(
            Notification.type,
            func.count(Notification.id).label('count')
        ).group_by(Notification.type).all()
        
        # 按优先级统计
        priority_stats = self.db.query(
            Notification.priority,
            func.count(Notification.id).label('count')
        ).group_by(Notification.priority).all()
        
        return {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'type_distribution': {stat.type: stat.count for stat in type_stats},
            'priority_distribution': {stat.priority: stat.count for stat in priority_stats}
        }
    
    # 预约相关优化查询
    def get_device_reservations_optimized(self, 
                                        device_id: Optional[int] = None,
                                        user_id: Optional[int] = None,
                                        status: Optional[str] = None,
                                        start_date: Optional[datetime] = None,
                                        end_date: Optional[datetime] = None,
                                        limit: int = 100) -> List[DeviceReservation]:
        """
        获取设备预约（优化查询，预加载关联数据）
        """
        query = self.db.query(DeviceReservation).options(
            joinedload(DeviceReservation.device),
            joinedload(DeviceReservation.user)
        )
        
        if device_id:
            query = query.filter(DeviceReservation.device_id == device_id)
        if user_id:
            query = query.filter(DeviceReservation.user_id == user_id)
        if status:
            query = query.filter(DeviceReservation.status == status)
        if start_date:
            query = query.filter(DeviceReservation.start_time >= start_date)
        if end_date:
            query = query.filter(DeviceReservation.end_time <= end_date)
            
        return query.order_by(desc(DeviceReservation.start_time)).limit(limit).all()
    
    def get_reservation_conflicts(self, 
                                device_id: int,
                                start_time: datetime,
                                end_time: datetime,
                                exclude_reservation_id: Optional[int] = None) -> List[DeviceReservation]:
        """
        检查预约时间冲突
        """
        query = self.db.query(DeviceReservation).filter(
            and_(
                DeviceReservation.device_id == device_id,
                DeviceReservation.status.in_(['pending', 'approved']),
                or_(
                    and_(
                        DeviceReservation.start_time <= start_time,
                        DeviceReservation.end_time > start_time
                    ),
                    and_(
                        DeviceReservation.start_time < end_time,
                        DeviceReservation.end_time >= end_time
                    ),
                    and_(
                        DeviceReservation.start_time >= start_time,
                        DeviceReservation.end_time <= end_time
                    )
                )
            )
        )
        
        if exclude_reservation_id:
            query = query.filter(DeviceReservation.id != exclude_reservation_id)
            
        return query.all()
    
    # 批量操作优化
    def bulk_update_notification_read_status(self, user_id: int, notification_ids: List[int]) -> int:
        """
        批量更新通知已读状态
        """
        updated_count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids)
            )
        ).update({'is_read': True}, synchronize_session=False)
        
        self.db.commit()
        return updated_count
    
    def cleanup_expired_notifications(self, days_old: int = 30) -> int:
        """
        清理过期通知
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = self.db.query(Notification).filter(
            or_(
                Notification.expires_at < datetime.now(),
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date
                )
            )
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return deleted_count

# 查询性能监控装饰器
import time
import functools
import logging

logger = logging.getLogger(__name__)

def monitor_query_performance(func):
    """
    监控查询性能的装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # 查询时间超过1秒时记录警告
                logger.warning(f"慢查询检测: {func.__name__} 执行时间: {execution_time:.2f}秒")
            else:
                logger.info(f"查询性能: {func.__name__} 执行时间: {execution_time:.3f}秒")
                
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"查询错误: {func.__name__} 执行时间: {execution_time:.3f}秒, 错误: {str(e)}")
            raise
    return wrapper

# 使用示例
def get_optimized_queries(db: Session) -> OptimizedQueries:
    """
    获取优化查询实例
    """
    return OptimizedQueries(db)