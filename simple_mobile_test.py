#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端登录简化测试脚本
"""
import json
import urllib.request
import urllib.error
from urllib.parse import urlencode

def test_simple_login():
    """测试简单的移动端登录"""
    print("🧪 移动端登录简化测试")
    print("=" * 50)
    
    # 测试不同的API地址
    base_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000", 
        "http://172.30.81.103:8000"
    ]
    
    test_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    for base_url in base_urls:
        print(f"\n📍 测试: {base_url}")
        
        try:
            # 测试健康检查
            health_url = f"{base_url}/health"
            print(f"🏥 健康检查: {health_url}")
            
            with urllib.request.urlopen(health_url, timeout=5) as response:
                health_data = json.loads(response.read().decode())
                print(f"✅ 健康检查通过: {health_data}")
            
            # 测试登录
            login_url = f"{base_url}/api/auth/login"
            print(f"🔐 登录测试: {login_url}")
            
            data = json.dumps(test_data).encode('utf-8')
            req = urllib.request.Request(
                login_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mobile-Test-Client/1.0'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                login_result = json.loads(response.read().decode())
                print(f"✅ 登录成功: {login_result}")
                
                # 保存token
                if 'access_token' in login_result:
                    token = login_result['access_token']
                    print(f"🔑 Token: {token[:20]}...")
                    
                    # 测试用户信息获取
                    me_url = f"{base_url}/api/auth/me"
                    me_req = urllib.request.Request(
                        me_url,
                        headers={
                            'Authorization': f'Bearer {token}',
                            'User-Agent': 'Mobile-Test-Client/1.0'
                        }
                    )
                    
                    with urllib.request.urlopen(me_req, timeout=10) as me_response:
                        user_info = json.loads(me_response.read().decode())
                        print(f"👤 用户信息: {user_info}")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"❌ HTTP错误 {e.code}: {error_body}")
        except urllib.error.URLError as e:
            print(f"❌ 连接错误: {e.reason}")
        except Exception as e:
            print(f"❌ 其他错误: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 50)
    print("📱 移动端访问测试完成")
    print("💡 提示: 使用手机访问以下地址测试移动端登录:")
    print("   http://172.30.81.103:8000/mobile_login.html")
    print("   http://172.30.81.103:8000/mobile_login_fix.html")

if __name__ == "__main__":
    test_simple_login()