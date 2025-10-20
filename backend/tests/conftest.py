import pytest
import asyncio
import tempfile
import os
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from fakeredis import FakeRedis

from app import app
from models.database import Base, get_db
from config import Config
from utils.auth import create_access_token
from models.user import User
from models.reagent import Reagent
from models.consumable import Consumable
from models.inventory import Inventory


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_redis():
    """创建测试Redis连接"""
    fake_redis = FakeRedis(decode_responses=True)
    with patch('redis.Redis', return_value=fake_redis):
        yield fake_redis
    fake_redis.flushall()


@pytest.fixture
def client(test_session, test_redis):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_upload_dir():
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_folder = Config.UPLOAD_FOLDER
        Config.UPLOAD_FOLDER = temp_dir
        yield temp_dir
        Config.UPLOAD_FOLDER = original_upload_folder


@pytest.fixture
def test_user(test_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True
    )
    user.set_password("testpassword123")
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def admin_user(test_session):
    """创建管理员用户"""
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    admin.set_password("adminpassword123")
    test_session.add(admin)
    test_session.commit()
    test_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """创建管理员认证头"""
    token = create_access_token(data={"sub": admin_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_reagent(test_session, test_user):
    """创建测试试剂"""
    reagent = Reagent(
        name="Test Reagent",
        cas_number="123-45-6",
        molecular_formula="C6H12O6",
        molecular_weight=180.16,
        purity=99.5,
        supplier="Test Supplier",
        catalog_number="TR001",
        storage_condition="室温",
        safety_info="无特殊要求",
        created_by=test_user.id
    )
    test_session.add(reagent)
    test_session.commit()
    test_session.refresh(reagent)
    return reagent


@pytest.fixture
def test_consumable(test_session, test_user):
    """创建测试耗材"""
    consumable = Consumable(
        name="Test Consumable",
        category="实验器具",
        specification="100ml",
        supplier="Test Supplier",
        catalog_number="TC001",
        unit_price=10.50,
        created_by=test_user.id
    )
    test_session.add(consumable)
    test_session.commit()
    test_session.refresh(consumable)
    return consumable


@pytest.fixture
def test_inventory(test_session, test_reagent, test_user):
    """创建测试库存"""
    inventory = Inventory(
        item_type="reagent",
        item_id=test_reagent.id,
        quantity=100.0,
        unit="g",
        location="A1-01",
        expiry_date="2025-12-31",
        batch_number="BATCH001",
        created_by=test_user.id
    )
    test_session.add(inventory)
    test_session.commit()
    test_session.refresh(inventory)
    return inventory


@pytest.fixture
def mock_email():
    """模拟邮件发送"""
    with patch('utils.email.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send


@pytest.fixture
def mock_file_upload():
    """模拟文件上传"""
    with patch('utils.file_handler.save_file') as mock_save:
        mock_save.return_value = "test_file.pdf"
        yield mock_save


@pytest.fixture
def mock_sentry():
    """模拟Sentry监控"""
    with patch('sentry_sdk.capture_exception') as mock_capture:
        yield mock_capture


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """创建用户测试数据"""
        default_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "testpassword123",
            "role": "user"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_reagent_data(**kwargs):
        """创建试剂测试数据"""
        default_data = {
            "name": "Test Reagent",
            "cas_number": "123-45-6",
            "molecular_formula": "C6H12O6",
            "molecular_weight": 180.16,
            "purity": 99.5,
            "supplier": "Test Supplier",
            "catalog_number": "TR001",
            "storage_condition": "室温",
            "safety_info": "无特殊要求"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_consumable_data(**kwargs):
        """创建耗材测试数据"""
        default_data = {
            "name": "Test Consumable",
            "category": "实验器具",
            "specification": "100ml",
            "supplier": "Test Supplier",
            "catalog_number": "TC001",
            "unit_price": 10.50
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_inventory_data(**kwargs):
        """创建库存测试数据"""
        default_data = {
            "item_type": "reagent",
            "quantity": 100.0,
            "unit": "g",
            "location": "A1-01",
            "expiry_date": "2025-12-31",
            "batch_number": "BATCH001"
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory


# 性能测试装饰器
def performance_test(max_duration=1.0):
    """性能测试装饰器"""
    def decorator(func):
        @pytest.mark.performance
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            duration = time.time() - start_time
            assert duration < max_duration, f"测试执行时间 {duration:.2f}s 超过限制 {max_duration}s"
            return result
        return wrapper
    return decorator


# 数据库事务回滚装饰器
def with_rollback(func):
    """确保测试后回滚数据库事务"""
    def wrapper(test_session, *args, **kwargs):
        try:
            return func(test_session, *args, **kwargs)
        finally:
            test_session.rollback()
    return wrapper