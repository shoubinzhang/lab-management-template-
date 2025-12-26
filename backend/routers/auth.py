from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from backend.database import get_db
from backend.models import User
from backend.auth import verify_password, create_access_token
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    # 用户不存在
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 用户被禁用
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 密码字段检查（关键）
    if not user.hashed_password:
        raise HTTPException(status_code=401, detail="用户未设置密码")

    # 验证密码
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成 JWT
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }
