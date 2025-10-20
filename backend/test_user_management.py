#!/usr/bin/env python3
"""
用户管理功能测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_user_management():
    """测试用户管理功能"""
    print("=== 用户管理功能测试 ===")
    
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
            print(f"登录成功! 用户: {user_info.get('username')}, 角色: {user_info.get('role')}")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 获取用户列表
            print("\n2. 获取用户列表...")
            response = requests.get(f"{BASE_URL}/api/users", headers=headers)
            print(f"用户列表API状态: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                print(f"用户数量: {len(users)}")
                if isinstance(users, list):
                    for user in users[:3]:  # 显示前3个用户
                        print(f"  - {user.get('username')} ({user.get('role')}) - {user.get('email', 'N/A')}")
                else:
                    print(f"用户数据格式: {type(users)}")
                    print(f"用户数据: {users}")
            else:
                print(f"获取用户列表失败: {response.text}")
            
            # 3. 获取角色列表
            print("\n3. 获取角色列表...")
            response = requests.get(f"{BASE_URL}/api/users/roles", headers=headers)
            print(f"角色列表API状态: {response.status_code}")
            
            if response.status_code == 200:
                roles = response.json()
                print(f"可用角色: {roles}")
            else:
                print(f"获取角色列表失败: {response.text}")
            
            # 4. 测试创建用户（可选）
            print("\n4. 测试用户管理权限...")
            test_user_data = {
                "username": "test_user_temp",
                "email": "test@example.com",
                "password": "test123",
                "role": "user"
            }
            
            response = requests.post(f"{BASE_URL}/api/users", json=test_user_data, headers=headers)
            print(f"创建用户测试状态: {response.status_code}")
            
            if response.status_code == 201:
                print("用户创建权限正常")
                # 删除测试用户
                created_user = response.json()
                user_id = created_user.get("id")
                if user_id:
                    delete_response = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers)
                    print(f"清理测试用户状态: {delete_response.status_code}")
            else:
                print(f"用户创建测试: {response.text}")
            
        else:
            print(f"登录失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_user_management()