from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Role, Permission
from auth import get_current_user
from functools import wraps

class PermissionChecker:
    """权限检查器类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def user_has_permission(self, user: User, permission_name: str) -> bool:
        """检查用户是否具有指定权限"""
        # 检查用户的所有角色是否包含该权限
        for role in user.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def user_has_role(self, user: User, role_name: str) -> bool:
        """检查用户是否具有指定角色"""
        for role in user.roles:
            if role.name == role_name and role.is_active:
                return True
        return False
    
    def get_user_permissions(self, user: User) -> List[str]:
        """获取用户的所有权限"""
        permissions = set()
        for role in user.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                permissions.add(permission.name)
        return list(permissions)
    
    def get_user_roles(self, user: User) -> List[str]:
        """获取用户的所有角色"""
        return [role.name for role in user.roles if role.is_active]

def require_permission(permission_name: str):
    """权限装饰器 - 要求特定权限"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从依赖注入中获取当前用户和数据库会话
            current_user = None
            db = None
            
            # 查找函数参数中的current_user和db
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif hasattr(value, 'query'):  # 检查是否为数据库会话
                    db = value
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败：缺少必要参数"
                )
            
            checker = PermissionChecker(db)
            if not checker.user_has_permission(current_user, permission_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足：需要 {permission_name} 权限"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name: str):
    """角色装饰器 - 要求特定角色"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从依赖注入中获取当前用户和数据库会话
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif hasattr(value, 'query'):
                    db = value
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败：缺少必要参数"
                )
            
            checker = PermissionChecker(db)
            if not checker.user_has_role(current_user, role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足：需要 {role_name} 角色"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 权限依赖函数
def check_permission(permission_name: str):
    """权限检查依赖函数"""
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        checker = PermissionChecker(db)
        if not checker.user_has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {permission_name} 权限"
            )
        return current_user
    return permission_dependency

def check_role(role_name: str):
    """角色检查依赖函数"""
    def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        checker = PermissionChecker(db)
        if not checker.user_has_role(current_user, role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {role_name} 角色"
            )
        return current_user
    return role_dependency

# 常用权限检查函数
def require_admin(current_user: User = Depends(get_current_user)):
    """要求管理员权限（兼容现有代码）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员权限不足"
        )
    return current_user

def get_permission_checker(db: Session = Depends(get_db)) -> PermissionChecker:
    """获取权限检查器实例"""
    return PermissionChecker(db)

# 预定义的权限常量
class Permissions:
    """权限常量类"""
    # 用户管理权限
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_MANAGE = "user.manage"
    
    # 设备管理权限
    DEVICE_CREATE = "device.create"
    DEVICE_READ = "device.read"
    DEVICE_UPDATE = "device.update"
    DEVICE_DELETE = "device.delete"
    DEVICE_MANAGE = "device.manage"
    
    # 试剂管理权限
    REAGENT_CREATE = "reagent.create"
    REAGENT_READ = "reagent.read"
    REAGENT_UPDATE = "reagent.update"
    REAGENT_DELETE = "reagent.delete"
    REAGENT_MANAGE = "reagent.manage"
    
    # 耗材管理权限
    CONSUMABLE_CREATE = "consumable.create"
    CONSUMABLE_READ = "consumable.read"
    CONSUMABLE_UPDATE = "consumable.update"
    CONSUMABLE_DELETE = "consumable.delete"
    CONSUMABLE_MANAGE = "consumable.manage"
    
    # 实验记录权限
    RECORD_CREATE = "record.create"
    RECORD_READ = "record.read"
    RECORD_UPDATE = "record.update"
    RECORD_DELETE = "record.delete"
    RECORD_MANAGE = "record.manage"
    
    # 申请相关权限
    REAGENT_REQUEST = "reagent.request"        # 申请领用试剂
    CONSUMABLE_REQUEST = "consumable.request"  # 申请领用耗材
    REQUEST_APPROVE = "request.approve"        # 审批申请
    
    # 数据调阅权限
    DATA_ACCESS = "data.access"               # 调阅实验数据
    
    # 系统管理权限
    SYSTEM_ADMIN = "system.admin"
    SYSTEM_CONFIG = "system.config"

# 预定义的角色常量
class Roles:
    """角色常量定义"""
    ADMIN = "admin"                    # 系统管理员
    MANAGER = "manager"                # 实验室管理员
    RESEARCHER = "researcher"           # 研究员
    USER = "user"                     # 普通用户
    GUEST = "guest"                   # 访客
    
    # 新增的分级权限角色
    LAB_TECHNICIAN = "lab_technician"   # 实验技术员
    WAREHOUSE_MANAGER = "warehouse_manager"  # 仓库管理员
    DOC_MANAGER = "doc_manager"         # 文档管理员