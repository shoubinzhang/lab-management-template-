#!/usr/bin/env python3
"""
使用urllib测试令牌有效性的简单脚本
"""
import urllib.request
import urllib.parse
import json

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
        # 登录请求
        login_url = f"{base_url}/api/auth/login"
        data = json.dumps(login_data).encode('utf-8')
        req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                token_data = json.loads(response.read().decode('utf-8'))
                new_token = token_data.get("access_token")
                print(f"✅ 登录成功，获取到新令牌: {new_token[:20]}...")
                
                # 使用新令牌测试用户管理API
                headers = {
                    "Authorization": f"Bearer {new_token}",
                    "Content-Type": "application/json"
                }
                
                print("\n2. 使用新令牌测试用户管理API...")
                
                # 测试获取用户列表
                users_url = f"{base_url}/api/users"
                req = urllib.request.Request(users_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    print(f"   获取用户列表 - 状态码: {response.getcode()}")
                    if response.getcode() == 200:
                        users = json.loads(response.read().decode('utf-8'))
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
                            
                            edit_url = f"{base_url}/api/users/{user_id}"
                            data = json.dumps(edit_data).encode('utf-8')
                            req = urllib.request.Request(edit_url, data=data, headers=headers, method='PUT')
                            
                            try:
                                with urllib.request.urlopen(req) as edit_response:
                                    print(f"   编辑用户信息 - 状态码: {edit_response.getcode()}")
                                    if edit_response.getcode() == 200:
                                        print("✅ 编辑用户成功！")
                                    else:
                                        print(f"   编辑用户失败 - 响应内容: {edit_response.read().decode('utf-8')}")
                            except urllib.error.HTTPError as e:
                                print(f"   编辑用户失败 - 状态码: {e.code}")
                                print(f"   错误信息: {e.read().decode('utf-8')}")
                        else:
                            print("   没有找到可编辑的非admin用户")
                    
                # 测试获取用户统计信息
                stats_url = f"{base_url}/api/users/stats/overview"
                req = urllib.request.Request(stats_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    print(f"   获取用户统计 - 状态码: {response.getcode()}")
                    
            else:
                print(f"❌ 登录失败: {response.getcode()}")
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP错误: {e.code}")
        print(f"   错误信息: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    test_token_validity()