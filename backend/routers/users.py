from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Role, Permission
from backend.auth import get_current_user
from backend.permissions import check_permission, check_role, Permissions, Roles, get_permission_checker
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter(prefix="/api/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic模型
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    role: str = None
    password: str = None

class RoleUpdate(BaseModel):
    role: str

class PasswordUpdate(BaseModel):
    new_password: str

class UserRoleAssignment(BaseModel):
    user_id: int
    role_ids: List[int]

class RoleAssignment(BaseModel):
    role_ids: List[int]

class RoleCreate(BaseModel):
    name: str
    description: str
    permission_ids: List[int] = []

class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    permissions: List[dict] = []
    
    class Config:
        from_attributes = True

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str
    resource: str
    action: str
    
    class Config:
        from_attributes = True

class UserDetailResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str = None
    roles: List[dict] = []
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

# 权限检查函数
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员权限不足"
        )
    return current_user

# 获取所有用户（仅管理员）
@router.get("/")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    users = db.query(User).all()
    
    # 计算统计信息
    total_users = len(users)
    admin_count = len([u for u in users if u.role == "admin"])
    user_count = len([u for u in users if u.role == "user"])
    
    # 转换用户数据
    users_data = []
    for user in users:
        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "roles": [],
            "permissions": []
        })
    
    return {
        "users": users_data,
        "stats": {
            "total_users": total_users,
            "admin_count": admin_count,
            "user_count": user_count
        }
    }

# 获取所有角色
@router.get("/roles", response_model=List[RoleResponse])
def get_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_MANAGE))
):
    """获取所有角色列表"""
    roles = db.query(Role).all()
    result = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "permissions": [
                {
                    "id": perm.id,
                    "name": perm.name,
                    "description": perm.description,
                    "resource": perm.resource,
                    "action": perm.action
                } for perm in role.permissions
            ]
        }
        result.append(role_dict)
    return result

# 获取所有权限
@router.get("/permissions", response_model=List[PermissionResponse])
def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_MANAGE))
):
    """获取所有权限列表"""
    permissions = db.query(Permission).all()
    return permissions

# 获取单个用户信息（仅管理员）
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

# 创建新用户（仅管理员）
@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 更新用户信息（仅管理员）
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    if user_data.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        user.username = user_data.username
    
    if user_data.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        user.email = user_data.email
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.password is not None:
        user.hashed_password = pwd_context.hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    return user

# 更新用户角色（仅管理员）
@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员修改自己的角色
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    return user

# 删除用户（仅管理员）
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    db.delete(user)
    db.commit()
    return {"message": "用户删除成功"}

# 获取用户统计信息（仅管理员）
@router.get("/stats/overview")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    total_users = db.query(User).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    user_count = db.query(User).filter(User.role == "user").count()
    
    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "user_count": user_count
    }

# ==================== 权限管理API ====================

# 创建角色
@router.post("/roles", response_model=RoleResponse)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_MANAGE))
):
    """创建新角色"""
    # 检查角色名是否已存在
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名已存在"
        )
    
    # 创建角色
    role = Role(
        name=role_data.name,
        description=role_data.description
    )
    
    # 添加权限
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
        role.permissions = permissions
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permissions": [
            {
                "id": perm.id,
                "name": perm.name,
                "description": perm.description,
                "resource": perm.resource,
                "action": perm.action
            } for perm in role.permissions
        ]
    }

# 更新角色权限
@router.put("/roles/{role_id}/permissions")
def update_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_MANAGE))
):
    """更新角色权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 获取权限
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    role.permissions = permissions
    
    db.commit()
    return {"message": "角色权限更新成功"}

# 为用户分配角色
@router.put("/{user_id}/roles")
def assign_user_roles(
    user_id: int,
    role_assignment: RoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_MANAGE))
):
    """为用户分配角色"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员修改自己的角色
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    # 获取角色
    roles = db.query(Role).filter(Role.id.in_(role_assignment.role_ids)).all()
    user.roles = roles
    
    db.commit()
    return {"message": "用户角色分配成功"}

# 获取用户详细信息（包含角色和权限）
@router.get("/{user_id}/details", response_model=UserDetailResponse)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permissions.USER_READ))
):
    """获取用户详细信息，包含角色和权限"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取用户权限
    checker = get_permission_checker(db)
    user_permissions = checker.get_user_permissions(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_active": role.is_active
            } for role in user.roles if role.is_active
        ],
        "permissions": user_permissions
    }

# 获取当前用户的权限
@router.get("/me/permissions")
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的权限列表"""
    checker = get_permission_checker(db)
    user_permissions = checker.get_user_permissions(current_user)
    user_roles = checker.get_user_roles(current_user)
    
    return {
        "permissions": user_permissions,
        "roles": user_roles
    }

# 修改用户密码（仅管理员）
@router.put("/{user_id}/password")
def update_user_password(
    user_id: int,
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    import re
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证密码长度
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少为8位"
        )
    
    # 验证密码包含字母、数字和特殊字符
    has_letter = bool(re.search(r'[a-zA-Z]', password_data.new_password))
    has_number = bool(re.search(r'[0-9]', password_data.new_password))
    has_symbol = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\|,.<>?/~`]', password_data.new_password))
    
    if not (has_letter and has_number and has_symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含字母、数字和特殊字符"
        )
    
    # 更新密码
    user.hashed_password = pwd_context.hash(password_data.new_password)
    db.commit()
    db.refresh(user)
    
    return {"message": "密码修改成功"}