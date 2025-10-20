#!/usr/bin/env python3
import requests
import json

def test_complete_auth_flow():
    base_url = "http://localhost:8000"
    
    print("=== 完整认证流程测试 ===\n")
    
    # 1. 测试登录
    print("1. 测试登录...")
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"   登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access_token')
            print(f"   登录成功! Token: {access_token[:50]}...")
            
            # 2. 测试获取用户信息
            print("\n2. 测试获取用户信息...")
            me_url = f"{base_url}/api/auth/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            me_response = requests.get(me_url, headers=headers)
            print(f"   用户信息状态码: {me_response.status_code}")
            
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"   用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
                
                # 3. 检查用户角色
                print("\n3. 检查用户角色...")
                user_role = user_info.get('role')
                print(f"   用户角色: {user_role}")
                print(f"   角色类型: {type(user_role)}")
                
                # 4. 模拟前端条件检查
                print("\n4. 模拟前端条件检查...")
                user = user_info  # 模拟前端的user对象
                should_show_user_management = user and user.get('role') == 'admin'
                print(f"   user存在: {user is not None}")
                print(f"   user.role === 'admin': {user.get('role') == 'admin'}")
                print(f"   应该显示用户管理链接: {should_show_user_management}")
                
                if should_show_user_management:
                    print("   ✅ 前端应该显示用户管理链接")
                else:
                    print("   ❌ 前端不应该显示用户管理链接")
                    
            else:
                print(f"   获取用户信息失败: {me_response.text}")
                
        else:
            print(f"   登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"   测试异常: {e}")

if __name__ == "__main__":
    test_complete_auth_flow()