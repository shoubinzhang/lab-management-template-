from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models import User

# JWT配置
import os
from config import SECRET_KEY, ALGORITHM  # 从config模块导入配置，避免循环导入



security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """获取当前认证用户"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# 管理员权限验证
def require_admin(current_user: User = Depends(get_current_user)):
    # 检查用户是否是管理员 - 兼容字符串角色和roles关系
    if hasattr(current_user, 'role') and current_user.role == "admin":
        return current_user
    # 检查roles关系
    if hasattr(current_user, 'roles') and current_user.roles:
        for role in current_user.roles:
            if hasattr(role, 'name') and role.name == "admin":
                return current_user
    raise HTTPException(
        status_code=403,
        detail="需要管理员权限",
    )