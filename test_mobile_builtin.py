#!/usr/bin/env python3
"""
使用内置库直接测试移动端登录API的脚本
绕过浏览器的CORS限制，不需要安装额外库
"""

import json
import urllib.request
import urllib.parse
import urllib.error
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
    print("移动端登录API直接测试（内置库版本）")
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
                health_response = urllib.request.urlopen(health_url, timeout=5)
                health_data = json.loads(health_response.read().decode('utf-8'))
                print(f"   状态码: {health_response.getcode()}")
                print(f"   响应数据: {json.dumps(health_data, ensure_ascii=False)}")
            except urllib.error.HTTPError as e:
                print(f"   HTTP错误: {e.code} - {e.reason}")
            except Exception as e:
                print(f"   错误: {e}")
            
            # 2. 测试登录端点（POST请求）
            print("\n2. 测试登录端点（POST）...")
            login_url = f"{base_url}/api/auth/login"
            login_data = json.dumps(test_credentials).encode('utf-8')
            
            print(f"   请求数据: {json.dumps(test_credentials, ensure_ascii=False)}")
            
            try:
                # 创建POST请求
                login_request = urllib.request.Request(
                    login_url,
                    data=login_data,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    method='POST'
                )
                
                login_response = urllib.request.urlopen(login_request, timeout=5)
                login_result = json.loads(login_response.read().decode('utf-8'))
                
                print(f"   状态码: {login_response.getcode()}")
                print(f"   登录成功！")
                print(f"   Token: {login_result.get('access_token', '无token')[:50]}...")
                print(f"   用户: {json.dumps(login_result.get('user', {}), ensure_ascii=False)}")
                
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"   HTTP错误: {e.code} - {e.reason}")
                print(f"   错误详情: {error_body}")
                
                # 尝试解析错误信息
                try:
                    error_data = json.loads(error_body)
                    if 'detail' in error_data:
                        print(f"   错误详情: {error_data['detail']}")
                    if 'errors' in error_data:
                        for error in error_data['errors']:
                            print(f"   验证错误: {error.get('msg', '')}")
                except:
                    print(f"   原始错误: {error_body}")
                    
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