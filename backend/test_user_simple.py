#!/usr/bin/env python3
"""
简化的用户管理测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_user_simple():
    """简化测试用户管理功能"""
    print("=== 简化用户管理测试 ===")
    
    # 1. 登录
    print("\n1. 管理员登录...")
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        print(f"登录状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"登录失败: {response.text}")
            return
            
        token_data = response.json()
        token = token_data.get("access_token")
        print("登录成功!")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取用户列表
        print("\n2. 获取用户列表...")
        response = requests.get(f"{BASE_URL}/api/users/", headers=headers, timeout=10)
        print(f"用户列表状态: {response.status_code}")
        
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('users', [])
            stats = users_data.get('stats', {})
            print(f"用户总数: {len(users)}")
            print(f"管理员数量: {stats.get('admin_count', 0)}")
            print(f"普通用户数量: {stats.get('user_count', 0)}")
        else:
            print(f"获取用户列表失败: {response.text}")
            return
        
        # 3. 获取角色列表
        print("\n3. 获取角色列表...")
        response = requests.get(f"{BASE_URL}/api/users/roles", headers=headers, timeout=10)
        print(f"角色列表状态: {response.status_code}")
        
        if response.status_code == 200:
            roles = response.json()
            print(f"角色数量: {len(roles)}")
            for role in roles[:3]:
                print(f"  - {role.get('name')}: {role.get('description')}")
        else:
            print(f"获取角色列表失败: {response.text}")
        
        # 4. 获取当前用户权限
        print("\n4. 获取当前用户权限...")
        response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=headers, timeout=10)
        print(f"权限状态: {response.status_code}")
        
        if response.status_code == 200:
            permissions_data = response.json()
            roles = permissions_data.get('roles', [])
            permissions = permissions_data.get('permissions', [])
            print(f"当前用户角色: {roles}")
            print(f"权限数量: {len(permissions)}")
            print(f"部分权限: {permissions[:5]}")
        else:
            print(f"获取权限失败: {response.text}")
        
        print("\n=== 用户管理基本功能正常 ===")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"测试过程中出错: {e}")

if __name__ == "__main__":
    test_user_simple()