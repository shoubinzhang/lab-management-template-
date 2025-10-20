#!/usr/bin/env python3
"""
测试移动端登录功能的完整流程
"""

import urllib.request
import urllib.parse
import json
import sys

def test_api_endpoints():
    """测试API端点"""
    base_urls = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://172.30.81.103:8000'
    ]
    
    for base_url in base_urls:
        print(f"\n{'='*50}")
        print(f"测试地址: {base_url}")
        print(f"{'='*50}")
        
        try:
            # 测试健康检查
            print("1. 测试健康检查端点...")
            req = urllib.request.Request(f'{base_url}/health', method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"   ✅ 健康检查成功: {data}")
            
            # 测试登录
            print("2. 测试登录端点...")
            login_data = json.dumps({
                'username': 'admin',
                'password': 'admin123'
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f'{base_url}/api/auth/login',
                data=login_data,
                method='POST',
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"   ✅ 登录成功")
                print(f"   📝 Token: {data.get('access_token', '无')[:50]}...")
                print(f"   👤 用户: {data.get('user', {}).get('username', '未知')}")
                
                # 测试使用token访问受保护端点
                if 'access_token' in data:
                    print("3. 测试使用Token访问受保护端点...")
                    token = data['access_token']
                    req = urllib.request.Request(
                        f'{base_url}/api/users/me',
                        headers={
                            'Authorization': f'Bearer {token}'
                        }
                    )
                    
                    with urllib.request.urlopen(req, timeout=5) as response:
                        user_data = json.loads(response.read().decode('utf-8'))
                        print(f"   ✅ Token验证成功: {user_data.get('username', '未知')}")
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP错误 {e.code}: {e.reason}")
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                print(f"   📄 错误详情: {error_data}")
            except:
                pass
        except urllib.error.URLError as e:
            print(f"   ❌ 连接错误: {e.reason}")
        except Exception as e:
            print(f"   ❌ 未知错误: {str(e)}")

if __name__ == '__main__':
    print("🧪 开始测试移动端登录API...")
    print("时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    test_api_endpoints()
    
    print("\n✅ 测试完成！")
    print("\n建议:")
    print("1. 如果localhost测试通过但IP地址失败，请检查防火墙设置")
    print("2. 如果所有地址都失败，请确认后端服务是否运行")
    print("3. 如果登录失败，请检查用户名密码是否正确")
    print("4. 浏览器端测试请访问: http://localhost:3000/mobile_login_final.html")