from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lab_management.db")

# 数据库引擎配置
engine_kwargs = {
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",  # SQL日志
    "pool_pre_ping": True,  # 连接前检查
    "pool_recycle": 3600,   # 连接回收时间（秒）
}

# SQLite特殊配置
if "sqlite" in DATABASE_URL:
    engine_kwargs.update({
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20,  # 连接超时
        },
        "poolclass": StaticPool,
    })
else:
    # PostgreSQL/MySQL配置
    engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    })

# 创建数据库引擎
engine = create_engine(DATABASE_URL, **engine_kwargs)

# SQLite外键约束启用
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 避免会话关闭后对象失效
)

# 创建基类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # 不要捕获HTTPException，让它正常传播
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# 数据库健康检查
def check_db_health():
    """检查数据库连接健康状态"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# 初始化数据库
def init_database():
    """初始化数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 创建默认管理员账户
        create_default_admin()
        
        # 初始化权限系统
        init_permissions_system()
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def create_default_admin():
    """创建默认管理员账户"""
    try:
        from models import User
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        db = SessionLocal()
        
        # 检查是否已存在管理员账户
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            # 创建默认管理员
            hashed_password = pwd_context.hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@lab.com",
                hashed_password=hashed_password,
                role="admin"
            )
            
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: username=admin, password=admin123")
        else:
            logger.info("Admin user already exists")
            
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to create default admin: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def init_permissions_system():
    """初始化权限系统"""
    try:
        from init_permissions import initialize_permissions_and_roles
        initialize_permissions_and_roles()
        logger.info("Permissions system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize permissions system: {e}")
