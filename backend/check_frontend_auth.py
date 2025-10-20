#!/usr/bin/env python3
"""
检查前端认证状态的脚本
"""
import requests
import json

def check_frontend_auth():
    """检查前端认证状态"""
    base_url = "http://localhost:8000"
    
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("1. 尝试登录...")
    login_response = requests.post(f"{base_url}/api/auth/login", data=login_data)
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        print(login_response.text)
        return
    
    token_data = login_response.json()
    token = token_data.get("access_token")
    print(f"登录成功，获取到token: {token[:20]}...")
    
    # 2. 使用token获取用户信息
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n2. 获取当前用户信息...")
    me_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
    
    if me_response.status_code != 200:
        print(f"获取用户信息失败: {me_response.status_code}")
        print(me_response.text)
        return
    
    user_info = me_response.json()
    print("用户信息:")
    print(json.dumps(user_info, indent=2, ensure_ascii=False))
    
    # 3. 检查角色字段
    role = user_info.get("role")
    print(f"\n3. 角色检查:")
    print(f"   角色值: {repr(role)}")
    print(f"   角色类型: {type(role)}")
    print(f"   是否为admin: {role == 'admin'}")
    print(f"   是否为字符串: {isinstance(role, str)}")
    
    # 4. 模拟前端的条件检查
    print(f"\n4. 前端条件检查:")
    user_exists = user_info is not None
    role_is_admin = user_info.get("role") == "admin"
    should_show_user_management = user_exists and role_is_admin
    
    print(f"   user存在: {user_exists}")
    print(f"   user.role === 'admin': {role_is_admin}")
    print(f"   应该显示用户管理链接: {should_show_user_management}")

if __name__ == "__main__":
    try:
        check_frontend_auth()
    except Exception as e:
        print(f"检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()