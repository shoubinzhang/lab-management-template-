#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的手机登录测试脚本 (使用标准库)
"""

import urllib.request
import json

def test_mobile_login():
    """测试手机登录功能"""
    base_url = "http://172.30.81.103:8000"
    login_url = f"{base_url}/api/auth/login"
    
    print("=== 手机登录测试 ===")
    print(f"登录URL: {login_url}")
    
    # 测试登录
    test_credentials = {"username": "admin", "password": "admin123"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    
    print("测试登录...")
    
    try:
        data = json.dumps(test_credentials).encode("utf-8")
        req = urllib.request.Request(login_url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"登录状态码: {response.status}")
            
            if response.status == 200:
                result = json.loads(response.read().decode("utf-8"))
                print("✅ 登录成功!")
                token = result.get("access_token", "")
                if token:
                    print(f"Token: {token[:30]}...")
                    
                    # 测试用户信息端点
                    user_url = f"{base_url}/api/auth/me"
                    user_headers = {
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
                    }
                    
                    user_req = urllib.request.Request(user_url, headers=user_headers)
                    with urllib.request.urlopen(user_req) as user_response:
                        if user_response.status == 200:
                            user_data = json.loads(user_response.read().decode("utf-8"))
                            print(f"✅ 用户信息获取成功: {user_data.get('username', 'N/A')}")
                        else:
                            print(f"❌ 获取用户信息失败: {user_response.status}")
                    
                    return True
                else:
                    print("❌ 未获取到token")
                    return False
            else:
                print(f"❌ 登录失败，状态码: {response.status}")
                print(f"错误响应: {response.read().decode('utf-8')}")
                return False
                
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        print("可能原因:")
        print("1. 用户名或密码错误")
        print("2. 后端服务异常")
        print("3. 网络连接问题")
        return False

def test_health():
    """测试后端健康状态"""
    print("\n=== 后端健康检查 ===")
    base_url = "http://172.30.81.103:8000"
    
    try:
        health_url = f"{base_url}/health"
        print(f"测试健康检查: {health_url}")
        
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"健康检查状态: {response.status}")
            if response.status == 200:
                print("✅ 后端服务正常运行")
                return True
            else:
                print(f"⚠️  后端服务异常: {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        print("可能原因:")
        print("1. 后端服务器未运行")
        print("2. IP地址不正确")
        print("3. 防火墙阻止连接")
        return False

if __name__ == "__main__":
    # 首先测试健康状态
    if test_health():
        # 然后测试登录
        if test_mobile_login():
            print("\n✅ 移动端登录测试通过!")
            print("手机端访问地址: http://172.30.81.103:3000")
            print("使用账号: admin/admin123")
        else:
            print("\n❌ 移动端登录测试失败!")
    else:
        print("\n❌ 后端服务连接失败，无法进行登录测试!")
        
    print("\n=== 测试完成 ===")