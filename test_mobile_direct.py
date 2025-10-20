#!/usr/bin/env python3
"""
直接测试移动端登录API的脚本
绕过浏览器的CORS限制
"""

import requests
import json
import sys
import time

def test_api_endpoints():
    """测试各种API端点"""
    
    # API地址 - 可以根据需要修改
    base_urls = [
        "http://172.30.81.103:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # 测试凭据
    test_credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("=" * 60)
    print("移动端登录API直接测试")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试凭据: {test_credentials['username']} / {test_credentials['password']}")
    print()
    
    for base_url in base_urls:
        print(f"测试地址: {base_url}")
        print("-" * 40)
        
        try:
            # 1. 测试健康检查端点
            print("1. 测试健康检查端点...")
            health_url = f"{base_url}/health"
            try:
                health_response = requests.get(health_url, timeout=5)
                print(f"   状态码: {health_response.status_code}")
                if health_response.ok:
                    health_data = health_response.json()
                    print(f"   响应数据: {json.dumps(health_data, ensure_ascii=False)}")
                else:
                    print(f"   响应文本: {health_response.text}")
            except Exception as e:
                print(f"   错误: {e}")
            
            # 2. 测试API文档端点
            print("\n2. 测试API文档端点...")
            docs_url = f"{base_url}/docs"
            try:
                docs_response = requests.get(docs_url, timeout=5)
                print(f"   状态码: {docs_response.status_code}")
                print(f"   内容长度: {len(docs_response.text)} 字符")
            except Exception as e:
                print(f"   错误: {e}")
            
            # 3. 测试登录端点（GET请求检查是否存在）
            print("\n3. 测试登录端点（GET）...")
            login_url = f"{base_url}/api/auth/login"
            try:
                # GET请求通常会被拒绝，但可以检查端点是否存在
                login_get_response = requests.get(login_url, timeout=5)
                print(f"   状态码: {login_get_response.status_code}")
                print(f"   响应文本: {login_get_response.text[:100]}...")
            except Exception as e:
                print(f"   错误: {e}")
            
            # 4. 测试登录端点（POST请求）
            print("\n4. 测试登录端点（POST）...")
            print(f"   请求数据: {json.dumps(test_credentials, ensure_ascii=False)}")
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                login_post_response = requests.post(
                    login_url, 
                    json=test_credentials, 
                    headers=headers, 
                    timeout=5
                )
                
                print(f"   状态码: {login_post_response.status_code}")
                print(f"   响应头: {dict(login_post_response.headers)}")
                
                if login_post_response.ok:
                    login_data = login_post_response.json()
                    print(f"   登录成功！")
                    print(f"   Token: {login_data.get('access_token', '无token')[:50]}...")
                    print(f"   用户: {json.dumps(login_data.get('user', {}), ensure_ascii=False)}")
                else:
                    print(f"   登录失败！")
                    try:
                        error_data = login_post_response.json()
                        print(f"   错误详情: {json.dumps(error_data, ensure_ascii=False)}")
                    except:
                        print(f"   响应文本: {login_post_response.text}")
                        
            except Exception as e:
                print(f"   错误: {e}")
            
            # 5. 测试使用获得的token访问受保护端点
            print("\n5. 测试Token验证...")
            try:
                if login_post_response.ok:
                    login_data = login_post_response.json()
                    token = login_data.get('access_token')
                    if token:
                        # 测试用户端点
                        user_url = f"{base_url}/api/users/me"
                        headers = {
                            'Authorization': f'Bearer {token}'
                        }
                        
                        user_response = requests.get(user_url, headers=headers, timeout=5)
                        print(f"   用户端点状态码: {user_response.status_code}")
                        
                        if user_response.ok:
                            user_data = user_response.json()
                            print(f"   用户信息: {json.dumps(user_data, ensure_ascii=False)}")
                        else:
                            print(f"   用户端点失败: {user_response.text}")
                    else:
                        print("   无token可用，跳过测试")
                else:
                    print("   登录失败，跳过token测试")
            except Exception as e:
                print(f"   错误: {e}")
            
            print("\n" + "=" * 40)
            
        except Exception as e:
            print(f"测试失败: {e}")
            print("=" * 40)
    
    print("\n测试完成！")
    print("\n建议:")
    print("1. 如果健康检查失败，请检查后端服务是否运行")
    print("2. 如果登录失败，请检查用户名密码是否正确")
    print("3. 如果所有测试都失败，请检查网络连接和防火墙设置")
    print("4. 如果只有浏览器测试失败，请检查CORS配置")

if __name__ == "__main__":
    test_api_endpoints()