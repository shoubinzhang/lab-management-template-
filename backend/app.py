from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
import qrcode
import io
import base64
import uuid
import time

from database import SessionLocal, engine, get_db, check_db_health, init_database
from models import Base, User, Device, Reagent, Consumable, ExperimentRecord, Knowledge, Feedback, DeviceMaintenance, DeviceReservation, Notification, WebSocketConnection
from routers import records, reagents, consumables, users, approvals
from cached_reagents import router as cached_reagents_router
from cached_consumables import router as cached_consumables_router
from cached_devices import router as cached_devices_router

from auth import get_current_user
from notification_routes import router as notification_router
from query_optimization import OptimizedQueries, monitor_query_performance
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# 创建数据库表
Base.metadata.create_all(bind=engine)

# FastAPI应用实例
app = FastAPI(
    title="Lab Management API",
    description="""实验室管理系统API
    
    ## 功能特性
    
    * **用户管理** - 用户注册、登录、权限管理
    * **试剂管理** - 试剂信息的增删改查
    * **耗材管理** - 实验耗材的库存管理
    * **实验记录** - 实验过程和结果记录
    * **设备管理** - 实验设备的状态监控
    
    ## 认证方式
    
    使用JWT Bearer Token进行身份认证。
    
    ## 错误处理
    
    API使用标准HTTP状态码，错误响应包含详细的错误信息。
    """,
    version="1.0.0",
    contact={
        "name": "Lab Management Team",
        "email": "admin@lab-management.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        },
        {
            "url": "https://api.lab-management.com",
            "description": "生产环境"
        }
    ]
)

# 配置静态文件服务 - 创建专门的static目录用于存放静态文件
import os
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 通用HTML页面重定向 - 让用户可以直接通过文件名访问静态HTML页面
@app.get("/{filename}.html")
async def redirect_html_files(filename: str):
    # 使用绝对路径检查文件存在性，解决Windows系统路径问题
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "static", f"{filename}.html")
    
    if os.path.exists(file_path):
        return RedirectResponse(url=f"/static/{filename}.html")
    else:
        raise HTTPException(status_code=404, detail="页面不存在")

# 移动端登录页面路由
@app.get("/mobile_login")
async def mobile_login_page():
    return RedirectResponse(url="/static/mobile_login.html")

# 移动端登录页面直接访问
@app.get("/mobile_login.html")
async def mobile_login_html_page():
    return RedirectResponse(url="/static/mobile_login.html")

# 移动端登录页面别名
@app.get("/mobile")
async def mobile_redirect():
    return RedirectResponse(url="/static/mobile_login.html")

# 移动端登录测试页面
@app.get("/mobile_login_test")
async def mobile_login_test_page():
    return RedirectResponse(url="/static/mobile_login_test.html")

# 移动端登录最终版本页面
@app.get("/mobile_login_final")
async def mobile_login_final_page():
    return RedirectResponse(url="/static/mobile_login_final.html")

# 移动端访问助手页面
@app.get("/mobile_helper")
async def mobile_helper_page():
    return RedirectResponse(url="/static/mobile_access_friendly.html")

# 处理 @vite/client 请求，返回空的 JavaScript 文件以避免 404 错误
@app.get("/@vite/client")
async def vite_client():
    return Response("// Vite client mock", media_type="application/javascript")

# 健康检查端点
@app.get("/api/health", tags=["系统"], summary="健康检查")
async def health_check():
    """
    系统健康检查端点
    用于监控服务是否正常运行
    """
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.now().isoformat()}

# API端点路径兼容层 - 添加旧路径到新路径的重定向
@app.get("/api/users/me", include_in_schema=False)
async def users_me_redirect(current_user: User = Depends(get_current_user)):
    try:
        return RedirectResponse(url="/api/auth/me")
    except NameError:
        # 备用方案：重新导入RedirectResponse
        from fastapi.responses import RedirectResponse as RR
        return RR(url="/api/auth/me")

# 请求验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，返回详细的错误信息"""
    # 处理 body 可能是 bytes 的情况
    body = exc.body
    if isinstance(body, bytes):
        try:
            body = body.decode('utf-8')
        except UnicodeDecodeError:
            body = str(body)
    
    # 处理 errors 中可能的 bytes 对象
    def clean_errors(errors):
        cleaned = []
        for error in errors:
            cleaned_error = {}
            for key, value in error.items():
                if isinstance(value, bytes):
                    try:
                        cleaned_error[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        cleaned_error[key] = str(value)
                else:
                    cleaned_error[key] = value
            cleaned.append(cleaned_error)
        return cleaned
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求验证失败",
            "errors": clean_errors(exc.errors()),
            "body": body
        }
    )

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，解决手机访问问题
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT配置 - 从config模块导入避免重复定义
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 二维码登录配置
QR_CODE_EXPIRE_MINUTES = 5  # 二维码5分钟过期
qr_login_sessions = {}  # 内存存储二维码登录会话 {login_id: {status, user_id, created_at, access_token}}

# Pydantic模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo

class QRCodeResponse(BaseModel):
    login_id: str
    qr_code: str  # base64编码的二维码图片
    expires_at: datetime

class QRStatusResponse(BaseModel):
    status: str  # waiting, scanned, confirmed, expired
    access_token: Optional[str] = None
    user: Optional[UserInfo] = None

class DeviceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "available"
    location: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[str] = None  # YYYY-MM-DD格式
    warranty_expiry: Optional[str] = None  # YYYY-MM-DD格式
    maintenance_interval: Optional[int] = 90
    responsible_person: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None
    maintenance_interval: Optional[int] = None
    responsible_person: Optional[str] = None

class MaintenanceCreate(BaseModel):
    device_id: int
    maintenance_type: str  # routine, repair, calibration
    description: str
    performed_by: str
    maintenance_date: str  # YYYY-MM-DD格式
    cost: Optional[float] = 0.0
    status: Optional[str] = "completed"
    notes: Optional[str] = None

class DeviceBatchImport(BaseModel):
    devices: List[dict]  # 设备数据列表

class ReservationCreate(BaseModel):
    device_id: int
    start_time: str  # YYYY-MM-DD HH:MM:SS格式
    end_time: str  # YYYY-MM-DD HH:MM:SS格式
    purpose: str
    notes: Optional[str] = None

class ReservationUpdate(BaseModel):
    status: Optional[str] = None  # pending, approved, rejected, completed, cancelled
    notes: Optional[str] = None

# 工具函数
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# get_current_user 函数已移至 auth.py 模块

# 认证路由
@app.post("/api/auth/register", response_model=dict, tags=["认证"], summary="用户注册")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - **username**: 用户名 (唯一)
    - **email**: 邮箱地址 (唯一)
    - **password**: 密码
    - **role**: 用户角色 (可选，默认为 'user')
    
    创建新用户账户，密码会自动加密存储。
    """
    # 检查用户是否已存在
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "用户注册成功", "user_id": db_user.id}

@app.post("/api/auth/login", response_model=Token, tags=["认证"], summary="用户登录")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT访问令牌和用户信息，用于后续API调用的身份验证。
    """
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    # 创建用户信息对象
    user_info = UserInfo(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        is_active=db_user.is_active
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user_info
    }

# 二维码登录相关API
@app.post("/api/auth/qr-generate", response_model=QRCodeResponse, tags=["认证"], summary="生成二维码登录")
def generate_qr_login():
    """
    生成二维码登录
    
    返回登录ID和二维码图片（base64编码），用于手机扫码登录。
    """
    login_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=QR_CODE_EXPIRE_MINUTES)
    
    # 生成二维码内容（包含登录ID和过期时间）
    qr_content = f"lab-login:{login_id}:{int(expires_at.timestamp())}"
    
    # 生成二维码图片
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 转换为base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    # 存储登录会话
    qr_login_sessions[login_id] = {
        "status": "waiting",
        "user_id": None,
        "created_at": datetime.now(),
        "access_token": None
    }
    
    return QRCodeResponse(
        login_id=login_id,
        qr_code=f"data:image/png;base64,{img_str}",
        expires_at=expires_at
    )

@app.get("/api/auth/qr-status/{login_id}", response_model=QRStatusResponse, tags=["认证"], summary="检查二维码登录状态")
def check_qr_status(login_id: str, db: Session = Depends(get_db)):
    """
    检查二维码登录状态
    
    - **login_id**: 登录ID
    
    返回登录状态：waiting（等待扫码）、scanned（已扫码）、confirmed（已确认）、expired（已过期）
    """
    if login_id not in qr_login_sessions:
        raise HTTPException(status_code=404, detail="登录会话不存在")
    
    session = qr_login_sessions[login_id]
    
    # 检查是否过期
    if datetime.now() - session["created_at"] > timedelta(minutes=QR_CODE_EXPIRE_MINUTES):
        session["status"] = "expired"
        return QRStatusResponse(status="expired")
    
    if session["status"] == "confirmed" and session["access_token"]:
        # 获取用户信息
        user_id = session["user_id"]
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            user_info = UserInfo(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                role=db_user.role,
                is_active=db_user.is_active
            )
            return QRStatusResponse(
                status="confirmed",
                access_token=session["access_token"],
                user=user_info
            )
    
    return QRStatusResponse(status=session["status"])

@app.post("/api/auth/qr-confirm/{login_id}", tags=["认证"], summary="确认二维码登录")
def confirm_qr_login(login_id: str, user: UserLogin, db: Session = Depends(get_db)):
    """
    确认二维码登录（手机端调用）
    
    - **login_id**: 登录ID
    - **username**: 用户名
    - **password**: 密码
    
    验证用户凭据并确认登录。
    """
    if login_id not in qr_login_sessions:
        raise HTTPException(status_code=404, detail="登录会话不存在")
    
    session = qr_login_sessions[login_id]
    
    # 检查是否过期
    if datetime.now() - session["created_at"] > timedelta(minutes=QR_CODE_EXPIRE_MINUTES):
        raise HTTPException(status_code=400, detail="登录会话已过期")
    
    # 验证用户凭据
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    # 更新会话状态
    session["status"] = "confirmed"
    session["user_id"] = db_user.id
    session["access_token"] = access_token
    
    return {"message": "登录确认成功"}

@app.get("/api/auth/me", tags=["认证"], summary="获取当前用户信息")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的详细信息
    
    需要在请求头中包含有效的JWT令牌。
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }

# 设备管理路由
# 分页响应模型
class PaginatedDeviceResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# 设备路由已移至 cached_devices.py
# @app.get("/api/devices", response_model=PaginatedDeviceResponse, tags=["设备管理"], summary="获取设备列表")
# @monitor_query_performance
# 设备路由已移至 cached_devices.py
# def get_devices(
#     page: int = 1,
#     per_page: int = 50,
#     status: Optional[str] = None,
#     location: Optional[str] = None,
#     search: Optional[str] = None,
#     sort_by: Optional[str] = "name",
#     sort_order: Optional[str] = "asc",
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取设备列表（分页）
#     
#     - **page**: 页码 (默认1)
#     - **per_page**: 每页数量 (默认50，最大100)
#     - **status**: 设备状态筛选
#     - **location**: 位置筛选
#     - **search**: 搜索关键词
#     - **sort_by**: 排序字段
#     - **sort_order**: 排序方向 (asc/desc)
#     
#     返回设备的详细信息，包括维护状态和预约信息。
#     """
#     # 验证分页参数
#     if page < 1:
#         page = 1
#     if per_page < 1 or per_page > 100:
#         per_page = 50
#     
#     query = db.query(Device)
#     
#     # 状态筛选
#     if status:
#         query = query.filter(Device.status == status)
#     
#     # 位置筛选
#     if location:
#         query = query.filter(Device.location == location)
#     
#     # 搜索功能
#     if search:
#         query = query.filter(
#             Device.name.contains(search) |
#             Device.model.contains(search) |
#             Device.serial_number.contains(search) |
#             Device.responsible_person.contains(search)
#         )
#     
#     # 排序
#     if sort_by and hasattr(Device, sort_by):
#         order_column = getattr(Device, sort_by)
#         if sort_order == "desc":
#             query = query.order_by(order_column.desc())
#         else:
#             query = query.order_by(order_column.asc())
#     else:
#         query = query.order_by(Device.name.asc())
#     
#     # 获取总数
#     total = query.count()
#     
#     # 计算偏移量
#     offset = (page - 1) * per_page
#     
#     # 获取分页数据
#     devices = query.offset(offset).limit(per_page).all()
#     
#     result = []
#     for device in devices:
#         device_data = {
#             "id": device.id,
#             "name": device.name,
#             "description": device.description,
#             "status": device.status,
#             "location": device.location,
#             "model": device.model,
#             "serial_number": device.serial_number,
#             "purchase_date": device.purchase_date.isoformat() if device.purchase_date else None,
#             "warranty_expiry": device.warranty_expiry.isoformat() if device.warranty_expiry else None,
#             "last_maintenance": device.last_maintenance.isoformat() if device.last_maintenance else None,
#             "next_maintenance": device.next_maintenance.isoformat() if device.next_maintenance else None,
#             "maintenance_interval": device.maintenance_interval,
#             "responsible_person": device.responsible_person,
#             "created_at": device.created_at.isoformat() if device.created_at else None,
#             "updated_at": device.updated_at.isoformat() if device.updated_at else None
#         }
#         result.append(device_data)
#     
#     # 计算分页信息
#     pages = (total + per_page - 1) // per_page
#     has_next = page < pages
#     has_prev = page > 1
#     
#     return PaginatedDeviceResponse(
#         items=result,
#         total=total,
#         page=page,
#         per_page=per_page,
#         pages=pages,
#         has_next=has_next,
#         has_prev=has_prev
#     )

# 新增优化的API端点
# 设备路由已移至 cached_devices.py
# @app.get("/api/devices/maintenance-needed", response_model=List[dict], tags=["设备管理"], summary="获取需要维护的设备")
# @monitor_query_performance
# def get_devices_needing_maintenance(
#     days_ahead: int = 7,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取需要维护的设备列表
#     
#     - **days_ahead**: 提前多少天检查 (默认7天)
#     """
#     optimized_queries = OptimizedQueries(db)
#     devices = optimized_queries.get_devices_needing_maintenance(days_ahead)
#     
#     result = []
#     for device in devices:
#         device_data = {
#             "id": device.id,
#             "name": device.name,
#             "status": device.status,
#             "location": device.location,
#             "next_maintenance": device.next_maintenance.isoformat() if device.next_maintenance else None,
#             "responsible_person": device.responsible_person,
#             "days_until_maintenance": (device.next_maintenance - datetime.now().date()).days if device.next_maintenance else None
#         }
#         result.append(device_data)
#     return result

# 试剂路由已移至 cached_reagents.py
# @app.get("/api/reagents/expiring", response_model=List[dict], tags=["试剂管理"], summary="获取即将过期的试剂")
# @monitor_query_performance
# def get_expiring_reagents(
#     days_ahead: int = 30,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取即将过期的试剂列表
#     
#     - **days_ahead**: 提前多少天检查 (默认30天)
#     """
#     optimized_queries = OptimizedQueries(db)
#     reagents = optimized_queries.get_expiring_reagents(days_ahead)
#     
#     result = []
#     for reagent in reagents:
#         reagent_data = {
#             "id": reagent.id,
#             "name": reagent.name,
#             "category": reagent.category,
#             "manufacturer": reagent.manufacturer,
#             "lot_number": reagent.lot_number,
#             "expiry_date": reagent.expiry_date.isoformat() if reagent.expiry_date else None,
#             "quantity": reagent.quantity,
#             "unit": reagent.unit,
#             "location": reagent.location,
#             "days_until_expiry": (reagent.expiry_date - datetime.now()).days if reagent.expiry_date else None
#         }
#         result.append(reagent_data)
#     return result

# 试剂路由已移至 cached_reagents.py
# 试剂路由已移至 cached_reagents.py
# @app.get("/api/reagents/low-stock", response_model=List[dict], tags=["试剂管理"], summary="获取库存不足的试剂")
# @monitor_query_performance
# def get_low_stock_reagents(
#     threshold: float = 10.0,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取库存不足的试剂列表
#     
#     - **threshold**: 库存阈值 (默认10.0)
#     """
#     optimized_queries = OptimizedQueries(db)
#     reagents = optimized_queries.get_low_stock_reagents(threshold)
#     
#     result = []
#     for reagent in reagents:
#         reagent_data = {
#             "id": reagent.id,
#             "name": reagent.name,
#             "category": reagent.category,
#             "quantity": reagent.quantity,
#             "unit": reagent.unit,
#             "location": reagent.location,
#             "price": reagent.price
#         }
#         result.append(reagent_data)
#     return result

# 设备路由已移至 cached_devices.py
# @app.post("/api/devices", response_model=dict, tags=["设备管理"], summary="创建新设备")
# def create_device(device: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     创建新的实验设备记录
#     
#     - **name**: 设备名称
#     - **description**: 设备描述
#     - **status**: 设备状态 (available, in_use, maintenance, broken)
#     - **location**: 设备位置
#     - **model**: 设备型号
#     - **serial_number**: 序列号
#     - **purchase_date**: 购买日期
#     - **warranty_expiry**: 保修到期日期
#     - **maintenance_interval**: 维护间隔（天）
#     - **responsible_person**: 负责人
#     """
#     from datetime import datetime
#     
#     device_data = device.dict()
#     
#     # 处理日期字段
#     if device_data.get('purchase_date'):
#         device_data['purchase_date'] = datetime.strptime(device_data['purchase_date'], '%Y-%m-%d').date()
#     if device_data.get('warranty_expiry'):
#         device_data['warranty_expiry'] = datetime.strptime(device_data['warranty_expiry'], '%Y-%m-%d').date()
#     
#     # 计算下次维护日期
#     if device_data.get('purchase_date') and device_data.get('maintenance_interval'):
#         from datetime import timedelta
#         purchase_date = device_data['purchase_date']
#         interval = device_data['maintenance_interval']
#         device_data['next_maintenance'] = purchase_date + timedelta(days=interval)
#     
#     db_device = Device(**device_data)
#     db.add(db_device)
#     db.commit()
#     db.refresh(db_device)
#     return {"message": "设备创建成功", "device_id": db_device.id}

# 设备路由已移至 cached_devices.py
# @app.put("/api/devices/{device_id}", response_model=dict, tags=["设备管理"], summary="更新设备信息")
# def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     更新指定设备的信息
#     
#     - **device_id**: 设备ID
#     - 可更新字段: name, description, status, location, model, serial_number, purchase_date, warranty_expiry, maintenance_interval, responsible_person
#     """
#     from datetime import datetime
#     
#     db_device = db.query(Device).filter(Device.id == device_id).first()
#     if not db_device:
#         raise HTTPException(status_code=404, detail="设备不存在")
#     
#     update_data = device.dict(exclude_unset=True)
#     
#     # 处理日期字段
#     if 'purchase_date' in update_data and update_data['purchase_date']:
#         update_data['purchase_date'] = datetime.strptime(update_data['purchase_date'], '%Y-%m-%d').date()
#     if 'warranty_expiry' in update_data and update_data['warranty_expiry']:
#         update_data['warranty_expiry'] = datetime.strptime(update_data['warranty_expiry'], '%Y-%m-%d').date()
#     
#     # 如果更新了维护间隔，重新计算下次维护日期
#     if 'maintenance_interval' in update_data and db_device.last_maintenance:
#         from datetime import timedelta
#         interval = update_data['maintenance_interval']
#         update_data['next_maintenance'] = db_device.last_maintenance + timedelta(days=interval)
#     
#     for key, value in update_data.items():
#         setattr(db_device, key, value)
#     
#     db.commit()
#     return {"message": "设备更新成功"}

# 设备路由已移至 cached_devices.py
# @app.delete("/api/devices/{device_id}", response_model=dict, tags=["设备管理"], summary="删除设备")
# def delete_device(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     删除指定的设备记录
#     
#     - **device_id**: 要删除的设备ID
#     
#     注意：此操作不可逆，请谨慎使用。
#     """
#     db_device = db.query(Device).filter(Device.id == device_id).first()
#     if not db_device:
#         raise HTTPException(status_code=404, detail="设备不存在")
#     
#     db.delete(db_device)
#     db.commit()
#     return {"message": "设备删除成功"}

# 设备路由已移至 cached_devices.py
# @app.post("/api/devices/batch-import", response_model=dict, tags=["设备管理"], summary="批量导入设备数据")
# def batch_import_devices(import_data: DeviceBatchImport, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     批量导入设备数据，用于从localStorage迁移数据到数据库
#     
#     - **devices**: 设备数据列表，每个设备包含name, model, location等字段
#     
#     返回导入结果统计信息。
#     """
#     from datetime import datetime
#     
#     imported_count = 0
#     failed_count = 0
#     errors = []
#     used_serial_numbers = set()  # 跟踪当前事务中使用的序列号
#     
#     for device_data in import_data.devices:
#         try:
#             # 检查必要字段
#             if not device_data.get('name'):
#                 errors.append(f"设备缺少名称字段: {device_data}")
#                 failed_count += 1
#                 continue
#             
#             # 获取序列号
#             serial_number = device_data.get('serial_number') or device_data.get('设备编号') or device_data.get('资产编号')
#             device_name = device_data.get('name') or device_data.get('设备名称') or device_data.get('名称') or 'Device'
#             
#             # 如果序列号为空或者是默认值'/'，生成唯一序列号
#             if not serial_number or serial_number == '/' or serial_number.strip() == '':
#                 import time
#                 import random
#                 # 使用更精确的时间戳（包含微秒）和随机数确保唯一性
#                 timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')  # 包含微秒
#                 random_suffix = random.randint(100, 999)
#                 serial_number = f"{device_name[:8]}_{timestamp}_{random_suffix}"
#             
#             # 检查序列号是否已存在（包括数据库和当前事务中的序列号）
#             attempt = 0
#             original_serial = serial_number
#             while attempt < 10:  # 最多尝试10次
#                 existing_device = db.query(Device).filter(Device.serial_number == serial_number).first()
#                 # 检查数据库中是否存在或当前事务中是否已使用
#                 if not existing_device and serial_number not in used_serial_numbers:
#                     break
#                 # 如果重复，生成新的序列号
#                 import random
#                 import time
#                 time.sleep(0.001)  # 短暂延迟确保时间戳不同
#                 timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
#                 random_suffix = random.randint(1000, 9999)
#                 # 对于重复的序列号，在原序列号基础上添加时间戳和随机后缀
#                 if original_serial and original_serial != '/' and original_serial.strip():
#                     serial_number = f"{original_serial}_{timestamp[-6:]}_{random_suffix}"
#                 else:
#                     serial_number = f"{device_name[:8]}_{timestamp}_{random_suffix}"
#                 attempt += 1
#             
#             if attempt >= 10:
#                 errors.append(f"无法生成唯一序列号，已尝试10次: {original_serial}")
#                 failed_count += 1
#                 continue
#             
#             # 将序列号添加到已使用集合中
#             used_serial_numbers.add(serial_number)
#             
#             # 数据映射和清理
#             clean_data = {
#                 'name': device_data.get('name') or device_data.get('设备名称') or device_data.get('名称'),
#                 'description': device_data.get('description') or device_data.get('描述'),
#                 'status': device_data.get('status') or device_data.get('状态') or 'available',
#                 'location': device_data.get('location') or device_data.get('位置') or device_data.get('部门'),
#                 'model': device_data.get('model') or device_data.get('型号'),
#                 'serial_number': serial_number,
#                 'responsible_person': device_data.get('responsible_person') or device_data.get('负责人'),
#                 'maintenance_interval': device_data.get('maintenance_interval') or 90
#             }
#             
#             # 处理日期字段
#             purchase_date = device_data.get('purchase_date') or device_data.get('购买日期')
#             if purchase_date and isinstance(purchase_date, str):
#                 try:
#                     clean_data['purchase_date'] = datetime.strptime(purchase_date, '%Y-%m-%d').date()
#                 except ValueError:
#                     # 尝试其他日期格式
#                     try:
#                         clean_data['purchase_date'] = datetime.strptime(purchase_date, '%Y/%m/%d').date()
#                     except ValueError:
#                         pass
#             
#             # 创建设备记录
#             db_device = Device(**{k: v for k, v in clean_data.items() if v is not None})
#             db.add(db_device)
#             imported_count += 1
#             
#         except Exception as e:
#             errors.append(f"导入设备失败: {device_data.get('name', 'Unknown')} - {str(e)}")
#             failed_count += 1
#     
#     try:
#         db.commit()
#         return {
#             "message": "批量导入完成",
#             "imported_count": imported_count,
#             "failed_count": failed_count,
#             "total_count": len(import_data.devices),
#             "errors": errors[:10]  # 只返回前10个错误
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")

# 设备维护记录管理
# 设备路由已移至 cached_devices.py
# @app.get("/api/devices/{device_id}/maintenance", response_model=List[dict], tags=["设备管理"], summary="获取设备维护记录")
# def get_device_maintenance(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     获取指定设备的维护记录
#     """
#     records = db.query(DeviceMaintenance).filter(DeviceMaintenance.device_id == device_id).all()
#     return [{
#         "id": record.id,
#         "maintenance_type": record.maintenance_type,
#         "description": record.description,
#         "performed_by": record.performed_by,
#         "maintenance_date": record.maintenance_date.isoformat() if record.maintenance_date else None,
#         "cost": record.cost,
#         "status": record.status,
#         "notes": record.notes,
#         "created_at": record.created_at.isoformat() if record.created_at else None
#     } for record in records]

# 移动端维护记录接口 - 与前端调用匹配的端点
@app.post("/api/devices/{device_id}/maintenance", response_model=dict, tags=["设备管理"], summary="移动端创建维护记录")
def mobile_create_maintenance(device_id: int, maintenance_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    移动端创建维护记录 - 与前端调用匹配的端点
    
    - **device_id**: 设备ID
    - 请求体包含maintenance_date, maintenance_type, maintainer, cost, notes等字段
    """
    from datetime import datetime, timedelta
    
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 处理日期格式
    maintenance_date = datetime.strptime(maintenance_data['maintenance_date'], '%Y-%m-%d').date()
    
    # 创建维护记录
    db_maintenance = DeviceMaintenance(
        device_id=device_id,
        maintenance_type=maintenance_data['maintenance_type'],
        description=maintenance_data.get('notes', ''),
        performed_by=maintenance_data.get('maintainer', current_user.username),
        maintenance_date=maintenance_date,
        cost=maintenance_data.get('cost'),
        status='completed',
        notes=maintenance_data.get('notes', '')
    )
    db.add(db_maintenance)
    
    # 更新设备的维护信息
    device.last_maintenance = maintenance_date
    device.next_maintenance = maintenance_date + timedelta(days=device.maintenance_interval or 90)
    
    db.commit()
    db.refresh(db_maintenance)
    return {"message": "维护记录创建成功", "maintenance_id": db_maintenance.id}

# 设备路由已移至 cached_devices.py
# @app.post("/api/maintenance", response_model=dict, tags=["设备管理"], summary="创建维护记录")
# def create_maintenance(maintenance: MaintenanceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     创建新的设备维护记录
#     """
#     from datetime import datetime, timedelta
#     
#     # 检查设备是否存在
#     device = db.query(Device).filter(Device.id == maintenance.device_id).first()
#     if not device:
#         raise HTTPException(status_code=404, detail="设备不存在")
#     
#     maintenance_data = maintenance.dict()
#     maintenance_data['maintenance_date'] = datetime.strptime(maintenance_data['maintenance_date'], '%Y-%m-%d').date()
#     
#     db_maintenance = DeviceMaintenance(**maintenance_data)
#     db.add(db_maintenance)
#     
#     # 更新设备的维护信息
#     device.last_maintenance = maintenance_data['maintenance_date']
#     device.next_maintenance = maintenance_data['maintenance_date'] + timedelta(days=device.maintenance_interval or 90)
#     
#     db.commit()
#     db.refresh(db_maintenance)
#     return {"message": "维护记录创建成功", "maintenance_id": db_maintenance.id}

# 设备预约管理
# 设备路由已移至 cached_devices.py
# @app.get("/api/devices/{device_id}/reservations", response_model=List[dict], tags=["设备管理"], summary="获取设备预约")
# def get_device_reservations(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     获取指定设备的预约记录
#     """
#     reservations = db.query(DeviceReservation).filter(DeviceReservation.device_id == device_id).all()
#     return [{
#         "id": reservation.id,
#         "user_id": reservation.user_id,
#         "start_time": reservation.start_time.isoformat() if reservation.start_time else None,
#         "end_time": reservation.end_time.isoformat() if reservation.end_time else None,
#         "purpose": reservation.purpose,
#         "status": reservation.status,
#         "notes": reservation.notes,
#         "created_at": reservation.created_at.isoformat() if reservation.created_at else None
#     } for reservation in reservations]

# 移动端预约接口 - 与前端调用匹配的端点
@app.post("/api/devices/{device_id}/reservations", response_model=dict, tags=["设备管理"], summary="移动端创建设备预约")
def mobile_create_reservation(device_id: int, reservation_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    移动端创建设备预约 - 与前端调用匹配的端点
    
    - **device_id**: 设备ID
    - 请求体包含start_time, end_time, purpose, notes等字段
    """
    from datetime import datetime
    
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 处理时间格式
    start_time = datetime.fromisoformat(reservation_data['start_time'])
    end_time = datetime.fromisoformat(reservation_data['end_time'])
    
    # 检查时间冲突
    existing_reservations = db.query(DeviceReservation).filter(
        DeviceReservation.device_id == device_id,
        DeviceReservation.status.in_(['pending', 'approved']),
        DeviceReservation.start_time < end_time,
        DeviceReservation.end_time > start_time
    ).first()
    
    if existing_reservations:
        raise HTTPException(status_code=400, detail="该时间段设备已被预约")
    
    # 创建预约记录
    db_reservation = DeviceReservation(
        device_id=device_id,
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        purpose=reservation_data.get('purpose', ''),
        notes=reservation_data.get('notes', ''),
        status='pending'
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return {"message": "预约创建成功", "reservation_id": db_reservation.id}

# 设备路由已移至 cached_devices.py
# @app.post("/api/reservations", response_model=dict, tags=["设备管理"], summary="创建设备预约")
# def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     创建新的设备预约
#     """
#     from datetime import datetime
#     
#     # 检查设备是否存在
#     device = db.query(Device).filter(Device.id == reservation.device_id).first()
#     if not device:
#         raise HTTPException(status_code=404, detail="设备不存在")
#     
#     reservation_data = reservation.dict()
#     reservation_data['start_time'] = datetime.strptime(reservation_data['start_time'], '%Y-%m-%dT%H:%M:%S')
#     reservation_data['end_time'] = datetime.strptime(reservation_data['end_time'], '%Y-%m-%dT%H:%M:%S')
#     reservation_data['user_id'] = current_user.id
#     
#     # 检查时间冲突
#     existing_reservations = db.query(DeviceReservation).filter(
#         DeviceReservation.device_id == reservation.device_id,
#         DeviceReservation.status.in_(['pending', 'approved']),
#         DeviceReservation.start_time < reservation_data['end_time'],
#         DeviceReservation.end_time > reservation_data['start_time']
#     ).first()
#     
#     if existing_reservations:
#         raise HTTPException(status_code=400, detail="该时间段设备已被预约")
#     
#     db_reservation = DeviceReservation(**reservation_data)
#     db.add(db_reservation)
#     db.commit()
#     db.refresh(db_reservation)
#     return {"message": "预约创建成功", "reservation_id": db_reservation.id}

@app.put("/api/reservations/{reservation_id}", response_model=dict, tags=["设备管理"], summary="更新预约状态")
def update_reservation(reservation_id: int, reservation: ReservationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    更新预约状态（管理员权限）
    """
    db_reservation = db.query(DeviceReservation).filter(DeviceReservation.id == reservation_id).first()
    if not db_reservation:
        raise HTTPException(status_code=404, detail="预约不存在")
    
    for key, value in reservation.dict(exclude_unset=True).items():
        setattr(db_reservation, key, value)
    
    db.commit()
    return {"message": "预约更新成功"}

# 包含路由器
app.include_router(records.router)
app.include_router(cached_reagents_router, prefix="/api")  # 使用缓存版本的试剂路由
app.include_router(cached_consumables_router, prefix="/api")  # 使用缓存版本的耗材路由
app.include_router(cached_devices_router, prefix="/api")  # 使用缓存版本的设备路由
app.include_router(users.router)
app.include_router(approvals.router)
app.include_router(notification_router, prefix="/api", tags=["通知系统"])

# 导入使用记录路由
from routers import usage_records
app.include_router(usage_records.router, prefix="/api/usage-records", tags=["使用记录"])


# 快速统计数据API
@app.get("/api/dashboard/quick-stats", tags=["仪表板"], summary="获取快速统计数据")
def get_quick_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取仪表板快速统计数据
    
    返回设备、试剂、耗材、实验等的快速统计信息。
    """
    try:
        from datetime import date
        
        # 获取设备统计
        total_devices = db.query(Device).count()
        active_devices = db.query(Device).filter(Device.status == "available").count()
        
        # 获取试剂统计
        total_reagents = db.query(Reagent).count()
        low_stock_reagents = db.query(Reagent).filter(Reagent.quantity <= 10).count()
        
        # 获取耗材统计
        total_consumables = db.query(Consumable).count()
        low_stock_consumables = db.query(Consumable).filter(Consumable.quantity <= Consumable.min_stock).count()
        
        # 获取实验记录统计
        total_experiments = db.query(ExperimentRecord).count()
        # 由于ExperimentRecord没有status字段，我们使用总实验数作为进行中的实验数
        active_experiments = total_experiments
        
        # 获取待处理任务数（低库存项目 + 需要维护的设备）
        maintenance_devices = db.query(Device).filter(Device.status.in_(["维护中", "maintenance"])).count()
        pending_tasks = low_stock_reagents + low_stock_consumables + maintenance_devices
        
        # 获取今日预约数
        today = date.today()
        from datetime import datetime
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        today_reservations = db.query(DeviceReservation).filter(
            DeviceReservation.start_time <= today_end,
            DeviceReservation.end_time >= today_start
        ).count()
        
        return {
            "totalExperiments": active_experiments,
            "activeEquipment": active_devices,
            "pendingTasks": pending_tasks,
            "todaySchedule": today_reservations
        }
    except Exception as e:
        print(f"获取快速统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")

# 健康检查
@app.get("/health", tags=["系统"], summary="健康检查")
def health_check():
    """
    系统健康检查接口
    
    用于监控系统状态，返回服务器运行状态和基本信息。
    """
    db_status = check_db_health()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.utcnow()
    }

# 访问日志中间件
@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    """记录HTTP访问日志"""
    import time
    import uuid
    import logging
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 记录请求开始
    logger = logging.getLogger('access')
    if not logger.handlers:
        # 如果access logger没有配置，使用基本的文件处理器
        import os
        from pathlib import Path
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(log_dir / "access.log", encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    try:
        response = await call_next(request)
        
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 毫秒
        status_code = response.status_code
        
        # 记录访问日志
        log_message = f"HTTP {status_code} - {request.method} {request.url.path} - IP: {client_ip} - ResponseTime: {round(response_time, 2)}ms"
        
        if status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        return response
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        logger.error(
            f"HTTP ERROR - {request.method} {request.url.path}: {str(e)} - IP: {client_ip} - ResponseTime: {round(response_time, 2)}ms",
            exc_info=True
        )
        raise

# 数据库初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_database()
    
    # 设置访问日志
    from logging_config import setup_logging
    setup_logging()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
