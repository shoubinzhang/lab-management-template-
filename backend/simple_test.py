#!/usr/bin/env python3
"""
简单的测试脚本，直接测试编辑用户功能
"""
import http.client
import json

def test_edit_user():
    """测试编辑用户功能"""
    base_url = "localhost:8000"
    
    # 首先登录获取令牌
    print("1. 登录获取令牌...")
    conn = http.client.HTTPConnection(base_url)
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        conn.request("POST", "/api/auth/login", json.dumps(login_data), headers)
        response = conn.getresponse()
        
        if response.status == 200:
            token_data = json.loads(response.read().decode())
            token = token_data.get("access_token")
            print(f"✅ 登录成功，令牌: {token[:20]}...")
            
            # 设置认证头
            auth_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 获取用户列表
            print("\n2. 获取用户列表...")
            conn.request("GET", "/api/users", headers=auth_headers)
            response = conn.getresponse()
            
            if response.status == 200:
                users = json.loads(response.read().decode())
                print(f"✅ 获取到 {len(users)} 个用户")
                
                # 显示所有用户
                for user in users:
                    print(f"   ID: {user.get('id')}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
                
                # 找到第一个非admin用户
                editable_user = None
                for user in users:
                    if user.get('username') != 'admin':
                        editable_user = user
                        break
                
                if editable_user:
                    user_id = editable_user.get('id')
                    username = editable_user.get('username')
                    print(f"\n3. 尝试编辑用户ID: {user_id}, 用户名: {username}")
                    
                    # 编辑用户信息（保持原用户名，只修改邮箱）
                    edit_data = {
                        "username": username,  # 保持原用户名
                        "email": f"{username}_updated@example.com",
                        "role": editable_user.get('role')
                    }
                    
                    conn.request("PUT", f"/api/users/{user_id}", json.dumps(edit_data), auth_headers)
                    response = conn.getresponse()
                    
                    print(f"编辑用户状态码: {response.status}")
                    
                    if response.status == 200:
                        updated_user = json.loads(response.read().decode())
                        print(f"✅ 编辑用户成功！")
                        print(f"   新邮箱: {updated_user.get('email')}")
                    else:
                        error_data = response.read().decode()
                        print(f"❌ 编辑用户失败: {error_data}")
                else:
                    print("❌ 没有找到可编辑的非admin用户")
            else:
                print(f"❌ 获取用户列表失败: {response.status}")
                print(f"   错误信息: {response.read().decode()}")
        else:
            print(f"❌ 登录失败: {response.status}")
            print(f"   错误信息: {response.read().decode()}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_edit_user()