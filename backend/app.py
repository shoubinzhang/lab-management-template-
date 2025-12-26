import sys
import os

print("开始加载 app.py 文件...")
print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

# =========================
# 基础依赖
# =========================
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
import qrcode
import io
import base64
import uuid
import time

print("基础模块导入完成")

# =========================
# backend 内部模块（统一使用 backend.xxx）
# =========================
print("正在导入数据库模块...")
from backend.database import (
    SessionLocal,
    engine,
    get_db,
    check_db_health,
    init_database,
)

print("正在导入模型模块...")
from backend.models import (
    Base,
    User,
    Device,
    Reagent,
    Consumable,
    ExperimentRecord,
    Knowledge,
    Feedback,
    DeviceMaintenance,
    DeviceReservation,
    Notification,
    WebSocketConnection,
)

print("正在导入路由模块...")
from backend.routers import records, reagents, consumables, users, approvals
from backend.routers.mcp_routes import router as mcp_router

from backend.cached_reagents import router as cached_reagents_router
from backend.cached_consumables import router as cached_consumables_router
from backend.cached_devices import router as cached_devices_router

print("正在导入认证与工具模块...")
from backend.auth import get_current_user
from backend.notification_routes import router as notification_router
from backend.query_optimization import OptimizedQueries, monitor_query_performance
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt

print("所有 backend 模块导入成功")

# =========================
# 数据库初始化
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# FastAPI 应用实例
# =========================
app = FastAPI(
    title="Lab Management API",
    description="实验室管理系统 API",
    version="1.0.0",
)

# =========================
# 静态文件
# =========================
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# =========================
# 中间件
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 全局异常处理
# =========================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# =========================
# 根路由
# =========================
@app.get("/")
async def root():
    return RedirectResponse(url="/mobile_portal")

@app.get("/health")
def health():
    return {
        "status": "healthy" if check_db_health() else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

# =========================
# JWT / 密码工具
# =========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =========================
# Pydantic 模型（节选）
# =========================
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    username: str
    password: str

# =========================
# 认证 API（示例）
# =========================
@app.post("/api/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(
        {"sub": db_user.username},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}

# =========================
# 挂载子路由
# =========================
app.include_router(records.router)
app.include_router(reagents.router)
app.include_router(consumables.router)
app.include_router(users.router)
app.include_router(approvals.router)

app.include_router(cached_reagents_router, prefix="/api")
app.include_router(cached_consumables_router, prefix="/api")
app.include_router(cached_devices_router, prefix="/api")

app.include_router(notification_router, prefix="/api")
app.include_router(mcp_router)

# =========================
# 启动事件
# =========================
@app.on_event("startup")
async def on_startup():
    init_database()
    print("数据库初始化完成")
if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )