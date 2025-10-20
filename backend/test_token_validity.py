#!/usr/bin/env python3
"""
测试令牌有效性的脚本
"""
import requests
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_token_validity():
    """测试当前令牌的有效性"""
    base_url = "http://localhost:8000"
    
    # 首先尝试登录获取新令牌
    print("1. 尝试登录获取新令牌...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data, verify=False)
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            new_token = token_data.get("access_token")
            print(f"✅ 登录成功，获取到新令牌: {new_token[:20]}...")
            
            # 使用新令牌测试用户管理API
            headers = {
                "Authorization": f"Bearer {new_token}",
                "Content-Type": "application/json"
            }
            
            print("\n2. 使用新令牌测试用户管理API...")
            
            # 测试获取用户列表
            users_response = requests.get(f"{base_url}/api/users", headers=headers)
            print(f"   获取用户列表 - 状态码: {users_response.status_code}")
            
            # 测试获取用户统计信息
            stats_response = requests.get(f"{base_url}/api/users/stats/overview", headers=headers)
            print(f"   获取用户统计 - 状态码: {stats_response.status_code}")
            
            # 首先获取用户列表，找到可编辑的用户
            users_response = requests.get(f"{base_url}/api/users", headers=headers)
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"   获取到 {len(users)} 个用户")
                
                # 调试：打印用户数据结构
                if users:
                    print(f"   第一个用户的数据类型: {type(users[0])}")
                    print(f"   第一个用户数据: {users[0]}")
                
                # 尝试编辑第一个非admin用户
                editable_user = None
                for user in users:
                    if isinstance(user, dict) and user.get('username') != 'admin':
                        editable_user = user
                        break
                
                if editable_user:
                    user_id = editable_user.get('id')
                    print(f"   尝试编辑用户ID: {user_id}, 用户名: {editable_user.get('username')}")
                    
                    # 测试编辑用户
                    edit_data = {
                        "username": editable_user.get('username'),  # 保持原用户名
                        "email": f"{editable_user.get('username')}_updated@example.com",
                        "role": editable_user.get('role')
                    }
                    edit_response = requests.put(f"{base_url}/api/users/{user_id}", json=edit_data, headers=headers)
                    print(f"   编辑用户信息 - 状态码: {edit_response.status_code}")
                    
                    if edit_response.status_code != 200:
                        print(f"   编辑用户失败 - 响应内容: {edit_response.text}")
                    else:
                        print("✅ 编辑用户成功！")
                else:
                    print("   没有找到可编辑的非admin用户")
            else:
                print(f"   获取用户列表失败: {users_response.status_code}")
                
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"   响应内容: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    test_token_validity()