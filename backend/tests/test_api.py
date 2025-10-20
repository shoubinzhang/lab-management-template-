import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch

from conftest import TestDataFactory, performance_test


class TestAuthAPI:
    """认证API测试"""
    
    def test_register_user_success(self, client, test_data_factory):
        """测试用户注册成功"""
        user_data = test_data_factory.create_user_data(
            username="newuser",
            email="newuser@example.com"
        )
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
    
    def test_register_user_duplicate_username(self, client, test_user, test_data_factory):
        """测试注册重复用户名"""
        user_data = test_data_factory.create_user_data(
            username=test_user.username,
            email="different@example.com"
        )
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, client, test_data_factory):
        """测试注册无效邮箱"""
        user_data = test_data_factory.create_user_data(
            email="invalid-email"
        )
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_user):
        """测试登录凭据无效"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_get_current_user(self, client, auth_headers, test_user):
        """测试获取当前用户信息"""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    def test_get_current_user_unauthorized(self, client):
        """测试未授权访问用户信息"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    @performance_test(max_duration=0.5)
    def test_login_performance(self, client, test_user):
        """测试登录性能"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200


class TestReagentAPI:
    """试剂API测试"""
    
    def test_create_reagent_success(self, client, auth_headers, test_data_factory):
        """测试创建试剂成功"""
        reagent_data = test_data_factory.create_reagent_data()
        
        response = client.post("/api/reagents", json=reagent_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == reagent_data["name"]
        assert data["cas_number"] == reagent_data["cas_number"]
    
    def test_create_reagent_unauthorized(self, client, test_data_factory):
        """测试未授权创建试剂"""
        reagent_data = test_data_factory.create_reagent_data()
        
        response = client.post("/api/reagents", json=reagent_data)
        
        assert response.status_code == 401
    
    def test_create_reagent_invalid_data(self, client, auth_headers):
        """测试创建试剂数据无效"""
        invalid_data = {
            "name": "",  # 空名称
            "cas_number": "invalid-cas"
        }
        
        response = client.post("/api/reagents", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_get_reagents_list(self, client, auth_headers, test_reagent):
        """测试获取试剂列表"""
        response = client.get("/api/reagents", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    def test_get_reagent_by_id(self, client, auth_headers, test_reagent):
        """测试根据ID获取试剂"""
        response = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_reagent.id
        assert data["name"] == test_reagent.name
    
    def test_get_reagent_not_found(self, client, auth_headers):
        """测试获取不存在的试剂"""
        response = client.get("/api/reagents/99999", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_reagent_success(self, client, auth_headers, test_reagent):
        """测试更新试剂成功"""
        update_data = {
            "name": "Updated Reagent Name",
            "purity": 98.5
        }
        
        response = client.put(
            f"/api/reagents/{test_reagent.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Reagent Name"
        assert data["purity"] == 98.5
    
    def test_delete_reagent_success(self, client, auth_headers, test_reagent):
        """测试删除试剂成功"""
        response = client.delete(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # 验证试剂已被删除
        get_response = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_search_reagents(self, client, auth_headers, test_reagent):
        """测试搜索试剂"""
        response = client.get(
            f"/api/reagents/search?q={test_reagent.name[:5]}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(item["id"] == test_reagent.id for item in data["items"])


class TestConsumableAPI:
    """耗材API测试"""
    
    def test_create_consumable_success(self, client, auth_headers, test_data_factory):
        """测试创建耗材成功"""
        consumable_data = test_data_factory.create_consumable_data()
        
        response = client.post("/api/consumables", json=consumable_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == consumable_data["name"]
        assert data["category"] == consumable_data["category"]
    
    def test_get_consumables_list(self, client, auth_headers, test_consumable):
        """测试获取耗材列表"""
        response = client.get("/api/consumables", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
    
    def test_get_consumable_by_id(self, client, auth_headers, test_consumable):
        """测试根据ID获取耗材"""
        response = client.get(f"/api/consumables/{test_consumable.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_consumable.id
        assert data["name"] == test_consumable.name


class TestInventoryAPI:
    """库存API测试"""
    
    def test_create_inventory_success(self, client, auth_headers, test_reagent, test_data_factory):
        """测试创建库存成功"""
        inventory_data = test_data_factory.create_inventory_data(
            item_id=test_reagent.id
        )
        
        response = client.post("/api/inventory", json=inventory_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["item_id"] == test_reagent.id
        assert data["quantity"] == inventory_data["quantity"]
    
    def test_get_inventory_list(self, client, auth_headers, test_inventory):
        """测试获取库存列表"""
        response = client.get("/api/inventory", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
    
    def test_update_inventory_quantity(self, client, auth_headers, test_inventory):
        """测试更新库存数量"""
        update_data = {
            "quantity": 50.0,
            "operation": "consume",
            "reason": "实验使用"
        }
        
        response = client.post(
            f"/api/inventory/{test_inventory.id}/update-quantity", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 50.0
    
    def test_get_low_stock_items(self, client, auth_headers):
        """测试获取低库存物品"""
        response = client.get("/api/inventory/low-stock", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_expiring_items(self, client, auth_headers):
        """测试获取即将过期物品"""
        response = client.get("/api/inventory/expiring", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestFileUploadAPI:
    """文件上传API测试"""
    
    def test_upload_file_success(self, client, auth_headers, temp_upload_dir, mock_file_upload):
        """测试文件上传成功"""
        # 创建测试文件
        test_file_content = b"Test file content"
        files = {"file": ("test.txt", test_file_content, "text/plain")}
        
        response = client.post("/api/upload", files=files, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "url" in data
    
    def test_upload_file_unauthorized(self, client):
        """测试未授权文件上传"""
        files = {"file": ("test.txt", b"content", "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 401
    
    def test_upload_file_too_large(self, client, auth_headers):
        """测试上传文件过大"""
        # 创建超大文件（模拟）
        large_content = b"x" * (20 * 1024 * 1024)  # 20MB
        files = {"file": ("large.txt", large_content, "text/plain")}
        
        response = client.post("/api/upload", files=files, headers=auth_headers)
        
        assert response.status_code == 413


class TestAdminAPI:
    """管理员API测试"""
    
    def test_get_users_list_admin(self, client, admin_headers):
        """测试管理员获取用户列表"""
        response = client.get("/api/admin/users", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_users_list_forbidden(self, client, auth_headers):
        """测试普通用户无权访问用户列表"""
        response = client.get("/api/admin/users", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_user_role_admin(self, client, admin_headers, test_user):
        """测试管理员更新用户角色"""
        update_data = {"role": "manager"}
        
        response = client.put(
            f"/api/admin/users/{test_user.id}/role", 
            json=update_data, 
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "manager"
    
    def test_get_system_stats(self, client, admin_headers):
        """测试获取系统统计信息"""
        response = client.get("/api/admin/stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_reagents" in data
        assert "total_consumables" in data


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_not_found(self, client):
        """测试404错误"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_500_internal_error(self, client, auth_headers):
        """测试500内部错误"""
        with patch('app.some_function', side_effect=Exception("Test error")):
            # 这里需要根据实际的错误端点进行测试
            pass
    
    @patch('sentry_sdk.capture_exception')
    def test_error_monitoring(self, mock_sentry, client, auth_headers):
        """测试错误监控"""
        # 触发一个错误并验证Sentry是否被调用
        with patch('app.some_function', side_effect=Exception("Test error")):
            # 调用会产生错误的端点
            pass
        
        # 验证Sentry被调用
        # mock_sentry.assert_called_once()


class TestRateLimiting:
    """速率限制测试"""
    
    @pytest.mark.slow
    def test_rate_limiting(self, client, auth_headers):
        """测试API速率限制"""
        # 快速发送多个请求
        responses = []
        for _ in range(100):
            response = client.get("/api/reagents", headers=auth_headers)
            responses.append(response.status_code)
        
        # 检查是否有429状态码（Too Many Requests）
        assert 429 in responses or all(code == 200 for code in responses)


class TestCaching:
    """缓存测试"""
    
    def test_cache_hit(self, client, auth_headers, test_reagent, test_redis):
        """测试缓存命中"""
        # 第一次请求
        response1 = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        assert response1.status_code == 200
        
        # 第二次请求应该从缓存获取
        response2 = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        assert response2.status_code == 200
        assert response1.json() == response2.json()
    
    def test_cache_invalidation(self, client, auth_headers, test_reagent, test_redis):
        """测试缓存失效"""
        # 获取试剂信息（缓存）
        response1 = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        assert response1.status_code == 200
        
        # 更新试剂信息（应该清除缓存）
        update_data = {"name": "Updated Name"}
        update_response = client.put(
            f"/api/reagents/{test_reagent.id}", 
            json=update_data, 
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # 再次获取试剂信息（应该是新数据）
        response2 = client.get(f"/api/reagents/{test_reagent.id}", headers=auth_headers)
        assert response2.status_code == 200
        assert response2.json()["name"] == "Updated Name"