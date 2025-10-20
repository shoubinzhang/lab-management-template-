#!/usr/bin/env python3
"""
完整的用户管理功能测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_user_management_complete():
    """完整测试用户管理功能"""
    print("=== 完整用户管理功能测试 ===")
    
    # 1. 登录获取token
    print("\n1. 管理员登录...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"登录状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"登录失败: {response.text}")
            return
            
        token_data = response.json()
        token = token_data.get("access_token")
        user_info = token_data.get("user", {})
        print(f"登录成功! 用户: {user_info.get('username')}, 角色: {user_info.get('role')}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取用户列表和统计
        print("\n2. 获取用户列表...")
        response = requests.get(f"{BASE_URL}/api/users/", headers=headers)
        print(f"用户列表API状态: {response.status_code}")
        
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('users', [])
            stats = users_data.get('stats', {})
            print(f"用户总数: {len(users)}")
            print(f"统计信息: {stats}")
            
            for user in users:
                print(f"  - {user.get('username')} ({user.get('role')}) - {user.get('email', 'N/A')}")
        else:
            print(f"获取用户列表失败: {response.text}")
            return
        
        # 3. 测试创建用户
        print("\n3. 测试创建用户...")
        test_user_data = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "test123456",
            "role": "user"
        }
        
        response = requests.post(f"{BASE_URL}/api/users/", json=test_user_data, headers=headers)
        print(f"创建用户状态: {response.status_code}")
        
        created_user = None
        if response.status_code == 201:
            created_user = response.json()
            print(f"用户创建成功: {created_user.get('username')} (ID: {created_user.get('id')})")
        else:
            print(f"用户创建失败: {response.text}")
            return
        
        # 4. 测试获取单个用户
        print("\n4. 测试获取单个用户...")
        user_id = created_user.get('id')
        response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        print(f"获取用户状态: {response.status_code}")
        
        if response.status_code == 200:
            user_detail = response.json()
            print(f"用户详情: {user_detail.get('username')} - {user_detail.get('email')}")
        else:
            print(f"获取用户失败: {response.text}")
        
        # 5. 测试更新用户
        print("\n5. 测试更新用户...")
        update_data = {
            "username": created_user.get('username'),
            "email": f"updated_{int(time.time())}@example.com",
            "role": "user"
        }
        
        response = requests.put(f"{BASE_URL}/api/users/{user_id}", json=update_data, headers=headers)
        print(f"更新用户状态: {response.status_code}")
        
        if response.status_code == 200:
            updated_user = response.json()
            print(f"用户更新成功: {updated_user.get('email')}")
        else:
            print(f"用户更新失败: {response.text}")
        
        # 6. 测试修改用户角色
        print("\n6. 测试修改用户角色...")
        role_data = {"role": "manager"}
        
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}/role", json=role_data, headers=headers)
        print(f"修改角色状态: {response.status_code}")
        
        if response.status_code == 200:
            role_updated_user = response.json()
            print(f"角色修改成功: {role_updated_user.get('role')}")
        else:
            print(f"角色修改失败: {response.text}")
        
        # 7. 测试修改密码
        print("\n7. 测试修改密码...")
        password_data = {"new_password": "newpassword123"}
        
        response = requests.patch(f"{BASE_URL}/api/users/{user_id}/password", json=password_data, headers=headers)
        print(f"修改密码状态: {response.status_code}")
        
        if response.status_code == 200:
            print("密码修改成功")
        else:
            print(f"密码修改失败: {response.text}")
        
        # 8. 获取角色列表
        print("\n8. 获取角色列表...")
        response = requests.get(f"{BASE_URL}/api/users/roles", headers=headers)
        print(f"角色列表状态: {response.status_code}")
        
        if response.status_code == 200:
            roles = response.json()
            print(f"可用角色数量: {len(roles)}")
            for role in roles[:3]:  # 显示前3个角色
                print(f"  - {role.get('name')}: {role.get('description')}")
        else:
            print(f"获取角色列表失败: {response.text}")
        
        # 9. 获取权限列表
        print("\n9. 获取权限列表...")
        response = requests.get(f"{BASE_URL}/api/users/permissions", headers=headers)
        print(f"权限列表状态: {response.status_code}")
        
        if response.status_code == 200:
            permissions = response.json()
            print(f"可用权限数量: {len(permissions)}")
            for perm in permissions[:5]:  # 显示前5个权限
                print(f"  - {perm.get('name')}: {perm.get('description')}")
        else:
            print(f"获取权限列表失败: {response.text}")
        
        # 10. 获取用户详细信息（包含角色和权限）
        print("\n10. 获取用户详细信息...")
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/details", headers=headers)
        print(f"用户详情状态: {response.status_code}")
        
        if response.status_code == 200:
            details = response.json()
            print(f"用户角色: {details.get('roles', [])}")
            print(f"用户权限数量: {len(details.get('permissions', []))}")
        else:
            print(f"获取用户详情失败: {response.text}")
        
        # 11. 获取当前用户权限
        print("\n11. 获取当前用户权限...")
        response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=headers)
        print(f"当前用户权限状态: {response.status_code}")
        
        if response.status_code == 200:
            my_permissions = response.json()
            print(f"当前用户角色: {my_permissions.get('roles', [])}")
            print(f"当前用户权限数量: {len(my_permissions.get('permissions', []))}")
        else:
            print(f"获取当前用户权限失败: {response.text}")
        
        # 12. 清理测试数据 - 删除测试用户
        print("\n12. 清理测试数据...")
        response = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        print(f"删除用户状态: {response.status_code}")
        
        if response.status_code == 200:
            print("测试用户删除成功")
        else:
            print(f"删除用户失败: {response.text}")
        
        print("\n=== 用户管理功能测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")

if __name__ == "__main__":
    test_user_management_complete()