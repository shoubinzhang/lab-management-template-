#!/usr/bin/env python3
"""
检查当前用户权限和角色信息
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def check_current_user():
    """检查当前用户的权限和角色"""
    print("=== 当前用户权限检查 ===")
    
    # 1. 登录获取token
    print("\n1. 登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"登录状态: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            user_info = token_data.get("user", {})
            print(f"登录成功!")
            print(f"用户ID: {user_info.get('id')}")
            print(f"用户名: {user_info.get('username')}")
            print(f"邮箱: {user_info.get('email')}")
            print(f"角色: {user_info.get('role')}")
            print(f"激活状态: {user_info.get('is_active')}")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 获取当前用户的权限
            print("\n2. 获取当前用户权限...")
            response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=headers)
            print(f"权限API状态: {response.status_code}")
            
            if response.status_code == 200:
                permissions_data = response.json()
                print(f"用户权限: {permissions_data.get('permissions', [])}")
                print(f"用户角色: {permissions_data.get('roles', [])}")
            else:
                print(f"获取权限失败: {response.text}")
            
            # 3. 获取用户详细信息
            print("\n3. 获取用户详细信息...")
            user_id = user_info.get('id')
            if user_id:
                response = requests.get(f"{BASE_URL}/api/users/{user_id}/details", headers=headers)
                print(f"用户详情API状态: {response.status_code}")
                
                if response.status_code == 200:
                    details = response.json()
                    print(f"详细角色信息: {details.get('roles', [])}")
                    print(f"详细权限信息: {details.get('permissions', [])}")
                else:
                    print(f"获取用户详情失败: {response.text}")
            
            # 4. 测试管理员权限
            print("\n4. 测试管理员权限...")
            response = requests.get(f"{BASE_URL}/api/users/", headers=headers)
            print(f"用户列表API状态: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                if isinstance(users_data, dict):
                    users = users_data.get('users', [])
                    stats = users_data.get('stats', {})
                    print(f"用户总数: {len(users)}")
                    print(f"统计信息: {stats}")
                else:
                    print(f"用户列表: {len(users_data)} 个用户")
            else:
                print(f"获取用户列表失败: {response.text}")
                
        else:
            print(f"登录失败: {response.text}")
            
    except Exception as e:
        print(f"检查过程中出错: {e}")

if __name__ == "__main__":
    check_current_user()