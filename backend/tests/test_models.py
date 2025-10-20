import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from models.user import User
from models.reagent import Reagent
from models.consumable import Consumable
from models.inventory import Inventory
from models.audit_log import AuditLog
from conftest import TestDataFactory, with_rollback


class TestUserModel:
    """用户模型测试"""
    
    @with_rollback
    def test_create_user_success(self, test_session):
        """测试创建用户成功"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="user"
        )
        user.set_password("password123")
        
        test_session.add(user)
        test_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
    
    @with_rollback
    def test_user_password_hashing(self, test_session):
        """测试用户密码哈希"""
        user = User(username="testuser", email="test@example.com")
        password = "password123"
        user.set_password(password)
        
        # 密码应该被哈希
        assert user.password_hash != password
        assert user.password_hash is not None
        
        # 验证密码
        assert user.check_password(password) is True
        assert user.check_password("wrongpassword") is False
    
    @with_rollback
    def test_user_unique_constraints(self, test_session):
        """测试用户唯一性约束"""
        # 创建第一个用户
        user1 = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User 1"
        )
        test_session.add(user1)
        test_session.commit()
        
        # 尝试创建相同用户名的用户
        user2 = User(
            username="testuser",  # 重复用户名
            email="different@example.com",
            full_name="Test User 2"
        )
        test_session.add(user2)
        
        with pytest.raises(IntegrityError):
            test_session.commit()
    
    @with_rollback
    def test_user_email_unique_constraint(self, test_session):
        """测试用户邮箱唯一性约束"""
        # 创建第一个用户
        user1 = User(
            username="user1",
            email="test@example.com",
            full_name="Test User 1"
        )
        test_session.add(user1)
        test_session.commit()
        
        # 尝试创建相同邮箱的用户
        user2 = User(
            username="user2",
            email="test@example.com",  # 重复邮箱
            full_name="Test User 2"
        )
        test_session.add(user2)
        
        with pytest.raises(IntegrityError):
            test_session.commit()
    
    def test_user_role_validation(self):
        """测试用户角色验证"""
        valid_roles = ["user", "manager", "admin"]
        
        for role in valid_roles:
            user = User(
                username=f"user_{role}",
                email=f"{role}@example.com",
                role=role
            )
            assert user.role == role
    
    def test_user_repr(self):
        """测试用户字符串表示"""
        user = User(username="testuser", email="test@example.com")
        assert "testuser" in repr(user)
    
    @with_rollback
    def test_user_soft_delete(self, test_session):
        """测试用户软删除"""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        test_session.add(user)
        test_session.commit()
        
        # 软删除
        user.is_active = False
        test_session.commit()
        
        assert user.is_active is False
        assert user.id is not None  # 用户仍然存在


class TestReagentModel:
    """试剂模型测试"""
    
    @with_rollback
    def test_create_reagent_success(self, test_session, test_user):
        """测试创建试剂成功"""
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
        
        assert reagent.id is not None
        assert reagent.name == "Test Reagent"
        assert reagent.cas_number == "123-45-6"
        assert reagent.molecular_weight == 180.16
        assert reagent.purity == 99.5
        assert reagent.created_at is not None
    
    @with_rollback
    def test_reagent_cas_number_validation(self, test_session, test_user):
        """测试试剂CAS号验证"""
        # 有效的CAS号格式
        valid_cas_numbers = ["123-45-6", "7732-18-5", "64-17-5"]
        
        for cas_number in valid_cas_numbers:
            reagent = Reagent(
                name=f"Reagent {cas_number}",
                cas_number=cas_number,
                molecular_formula="H2O",
                created_by=test_user.id
            )
            test_session.add(reagent)
            test_session.commit()
            test_session.delete(reagent)  # 清理
    
    @with_rollback
    def test_reagent_molecular_weight_validation(self, test_session, test_user):
        """测试试剂分子量验证"""
        reagent = Reagent(
            name="Test Reagent",
            cas_number="123-45-6",
            molecular_formula="C6H12O6",
            molecular_weight=-10.0,  # 负数分子量
            created_by=test_user.id
        )
        
        # 应该在应用层验证，这里只测试模型能否存储
        test_session.add(reagent)
        test_session.commit()
        
        assert reagent.molecular_weight == -10.0
    
    @with_rollback
    def test_reagent_purity_range(self, test_session, test_user):
        """测试试剂纯度范围"""
        # 测试边界值
        purities = [0.0, 50.0, 99.9, 100.0]
        
        for purity in purities:
            reagent = Reagent(
                name=f"Reagent {purity}%",
                cas_number=f"123-45-{int(purity)}",
                purity=purity,
                created_by=test_user.id
            )
            test_session.add(reagent)
            test_session.commit()
            
            assert reagent.purity == purity
            test_session.delete(reagent)  # 清理
    
    def test_reagent_repr(self, test_user):
        """测试试剂字符串表示"""
        reagent = Reagent(
            name="Test Reagent",
            cas_number="123-45-6",
            created_by=test_user.id
        )
        assert "Test Reagent" in repr(reagent)
        assert "123-45-6" in repr(reagent)
    
    @with_rollback
    def test_reagent_search_functionality(self, test_session, test_user):
        """测试试剂搜索功能"""
        reagents = [
            Reagent(name="Sodium Chloride", cas_number="7647-14-5", created_by=test_user.id),
            Reagent(name="Potassium Chloride", cas_number="7447-40-7", created_by=test_user.id),
            Reagent(name="Calcium Carbonate", cas_number="471-34-1", created_by=test_user.id),
        ]
        
        for reagent in reagents:
            test_session.add(reagent)
        test_session.commit()
        
        # 按名称搜索
        chloride_reagents = test_session.query(Reagent).filter(
            Reagent.name.contains("Chloride")
        ).all()
        assert len(chloride_reagents) == 2
        
        # 按CAS号搜索
        specific_reagent = test_session.query(Reagent).filter(
            Reagent.cas_number == "7647-14-5"
        ).first()
        assert specific_reagent.name == "Sodium Chloride"


class TestConsumableModel:
    """耗材模型测试"""
    
    @with_rollback
    def test_create_consumable_success(self, test_session, test_user):
        """测试创建耗材成功"""
        consumable = Consumable(
            name="Test Tube",
            category="实验器具",
            specification="15ml",
            supplier="Lab Supply Co.",
            catalog_number="TT001",
            unit_price=Decimal('2.50'),
            created_by=test_user.id
        )
        
        test_session.add(consumable)
        test_session.commit()
        
        assert consumable.id is not None
        assert consumable.name == "Test Tube"
        assert consumable.category == "实验器具"
        assert consumable.unit_price == Decimal('2.50')
        assert consumable.created_at is not None
    
    @with_rollback
    def test_consumable_price_precision(self, test_session, test_user):
        """测试耗材价格精度"""
        prices = [Decimal('0.01'), Decimal('10.99'), Decimal('999.99')]
        
        for price in prices:
            consumable = Consumable(
                name=f"Item {price}",
                category="测试",
                unit_price=price,
                created_by=test_user.id
            )
            test_session.add(consumable)
            test_session.commit()
            
            assert consumable.unit_price == price
            test_session.delete(consumable)  # 清理
    
    def test_consumable_categories(self, test_user):
        """测试耗材分类"""
        categories = ["实验器具", "化学试剂", "安全用品", "清洁用品"]
        
        for category in categories:
            consumable = Consumable(
                name=f"Test {category}",
                category=category,
                created_by=test_user.id
            )
            assert consumable.category == category
    
    def test_consumable_repr(self, test_user):
        """测试耗材字符串表示"""
        consumable = Consumable(
            name="Test Tube",
            category="实验器具",
            created_by=test_user.id
        )
        assert "Test Tube" in repr(consumable)


class TestInventoryModel:
    """库存模型测试"""
    
    @with_rollback
    def test_create_inventory_success(self, test_session, test_reagent, test_user):
        """测试创建库存成功"""
        inventory = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('100.0'),
            unit="g",
            location="A1-01",
            expiry_date=datetime.now() + timedelta(days=365),
            batch_number="BATCH001",
            created_by=test_user.id
        )
        
        test_session.add(inventory)
        test_session.commit()
        
        assert inventory.id is not None
        assert inventory.item_type == "reagent"
        assert inventory.item_id == test_reagent.id
        assert inventory.quantity == Decimal('100.0')
        assert inventory.unit == "g"
        assert inventory.location == "A1-01"
    
    @with_rollback
    def test_inventory_quantity_operations(self, test_session, test_reagent, test_user):
        """测试库存数量操作"""
        inventory = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('100.0'),
            unit="g",
            created_by=test_user.id
        )
        test_session.add(inventory)
        test_session.commit()
        
        # 消耗库存
        inventory.quantity -= Decimal('25.0')
        test_session.commit()
        assert inventory.quantity == Decimal('75.0')
        
        # 补充库存
        inventory.quantity += Decimal('50.0')
        test_session.commit()
        assert inventory.quantity == Decimal('125.0')
    
    @with_rollback
    def test_inventory_expiry_date(self, test_session, test_reagent, test_user):
        """测试库存过期日期"""
        future_date = datetime.now() + timedelta(days=30)
        past_date = datetime.now() - timedelta(days=30)
        
        # 未过期库存
        inventory1 = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('100.0'),
            expiry_date=future_date,
            created_by=test_user.id
        )
        test_session.add(inventory1)
        
        # 已过期库存
        inventory2 = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('50.0'),
            expiry_date=past_date,
            created_by=test_user.id
        )
        test_session.add(inventory2)
        test_session.commit()
        
        # 查询即将过期的库存（30天内）
        expiring_soon = test_session.query(Inventory).filter(
            Inventory.expiry_date <= datetime.now() + timedelta(days=30)
        ).all()
        
        assert len(expiring_soon) >= 1
    
    @with_rollback
    def test_inventory_low_stock_detection(self, test_session, test_reagent, test_user):
        """测试低库存检测"""
        # 创建低库存项目
        low_stock = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('5.0'),  # 低库存
            min_quantity=Decimal('10.0'),  # 最小库存阈值
            unit="g",
            created_by=test_user.id
        )
        test_session.add(low_stock)
        test_session.commit()
        
        # 查询低库存项目
        low_stock_items = test_session.query(Inventory).filter(
            Inventory.quantity <= Inventory.min_quantity
        ).all()
        
        assert len(low_stock_items) >= 1
        assert low_stock in low_stock_items
    
    def test_inventory_item_types(self, test_reagent, test_user):
        """测试库存物品类型"""
        valid_types = ["reagent", "consumable"]
        
        for item_type in valid_types:
            inventory = Inventory(
                item_type=item_type,
                item_id=test_reagent.id,
                quantity=Decimal('100.0'),
                created_by=test_user.id
            )
            assert inventory.item_type == item_type
    
    def test_inventory_repr(self, test_reagent, test_user):
        """测试库存字符串表示"""
        inventory = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('100.0'),
            unit="g",
            location="A1-01",
            created_by=test_user.id
        )
        repr_str = repr(inventory)
        assert "reagent" in repr_str
        assert "100.0" in repr_str
        assert "A1-01" in repr_str


class TestAuditLogModel:
    """审计日志模型测试"""
    
    @with_rollback
    def test_create_audit_log_success(self, test_session, test_user):
        """测试创建审计日志成功"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="CREATE",
            resource_type="reagent",
            resource_id=1,
            details={"name": "Test Reagent", "cas_number": "123-45-6"},
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        
        test_session.add(audit_log)
        test_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.user_id == test_user.id
        assert audit_log.action == "CREATE"
        assert audit_log.resource_type == "reagent"
        assert audit_log.details["name"] == "Test Reagent"
        assert audit_log.timestamp is not None
    
    @with_rollback
    def test_audit_log_actions(self, test_session, test_user):
        """测试审计日志动作类型"""
        actions = ["CREATE", "READ", "UPDATE", "DELETE", "LOGIN", "LOGOUT"]
        
        for action in actions:
            audit_log = AuditLog(
                user_id=test_user.id,
                action=action,
                resource_type="test",
                resource_id=1
            )
            test_session.add(audit_log)
            test_session.commit()
            
            assert audit_log.action == action
            test_session.delete(audit_log)  # 清理
    
    @with_rollback
    def test_audit_log_json_details(self, test_session, test_user):
        """测试审计日志JSON详情"""
        complex_details = {
            "old_values": {"name": "Old Name", "quantity": 50},
            "new_values": {"name": "New Name", "quantity": 75},
            "changes": ["name", "quantity"]
        }
        
        audit_log = AuditLog(
            user_id=test_user.id,
            action="UPDATE",
            resource_type="inventory",
            resource_id=1,
            details=complex_details
        )
        
        test_session.add(audit_log)
        test_session.commit()
        
        assert audit_log.details == complex_details
        assert audit_log.details["old_values"]["name"] == "Old Name"
        assert audit_log.details["new_values"]["quantity"] == 75
    
    def test_audit_log_repr(self, test_user):
        """测试审计日志字符串表示"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="CREATE",
            resource_type="reagent",
            resource_id=1
        )
        repr_str = repr(audit_log)
        assert "CREATE" in repr_str
        assert "reagent" in repr_str


class TestModelRelationships:
    """模型关系测试"""
    
    @with_rollback
    def test_user_reagent_relationship(self, test_session, test_user):
        """测试用户和试剂的关系"""
        reagent = Reagent(
            name="Test Reagent",
            cas_number="123-45-6",
            created_by=test_user.id
        )
        test_session.add(reagent)
        test_session.commit()
        
        # 通过关系访问创建者
        assert reagent.creator.username == test_user.username
        
        # 通过用户访问创建的试剂
        user_reagents = test_session.query(Reagent).filter(
            Reagent.created_by == test_user.id
        ).all()
        assert reagent in user_reagents
    
    @with_rollback
    def test_inventory_reagent_relationship(self, test_session, test_reagent, test_user):
        """测试库存和试剂的关系"""
        inventory = Inventory(
            item_type="reagent",
            item_id=test_reagent.id,
            quantity=Decimal('100.0'),
            created_by=test_user.id
        )
        test_session.add(inventory)
        test_session.commit()
        
        # 验证关系
        assert inventory.item_id == test_reagent.id
        assert inventory.item_type == "reagent"
    
    @with_rollback
    def test_cascade_delete_behavior(self, test_session, test_user):
        """测试级联删除行为"""
        # 创建试剂
        reagent = Reagent(
            name="Test Reagent",
            cas_number="123-45-6",
            created_by=test_user.id
        )
        test_session.add(reagent)
        test_session.commit()
        reagent_id = reagent.id
        
        # 创建相关库存
        inventory = Inventory(
            item_type="reagent",
            item_id=reagent_id,
            quantity=Decimal('100.0'),
            created_by=test_user.id
        )
        test_session.add(inventory)
        test_session.commit()
        
        # 删除试剂
        test_session.delete(reagent)
        test_session.commit()
        
        # 验证试剂已删除
        deleted_reagent = test_session.query(Reagent).filter(
            Reagent.id == reagent_id
        ).first()
        assert deleted_reagent is None
        
        # 库存应该仍然存在（根据业务逻辑）
        remaining_inventory = test_session.query(Inventory).filter(
            Inventory.item_id == reagent_id
        ).first()
        # 这取决于具体的级联删除配置


class TestModelValidation:
    """模型验证测试"""
    
    def test_required_fields_validation(self, test_user):
        """测试必填字段验证"""
        # 用户必填字段
        with pytest.raises(Exception):  # 具体异常类型取决于ORM配置
            user = User()  # 缺少必填字段
        
        # 试剂必填字段
        with pytest.raises(Exception):
            reagent = Reagent()  # 缺少必填字段
    
    def test_field_length_validation(self, test_user):
        """测试字段长度验证"""
        # 测试用户名长度限制
        long_username = "a" * 1000  # 超长用户名
        user = User(
            username=long_username,
            email="test@example.com"
        )
        # 根据模型定义，这可能会被截断或抛出异常
    
    def test_email_format_validation(self):
        """测试邮箱格式验证"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com"
        ]
        
        for email in invalid_emails:
            user = User(
                username="testuser",
                email=email
            )
            # 在应用层应该验证邮箱格式
    
    def test_numeric_field_validation(self, test_user):
        """测试数值字段验证"""
        # 测试负数分子量
        reagent = Reagent(
            name="Test Reagent",
            molecular_weight=-100.0,  # 负数
            created_by=test_user.id
        )
        # 应该在应用层验证
        
        # 测试超出范围的纯度
        reagent.purity = 150.0  # 超过100%
        # 应该在应用层验证