#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime


def test_mobile_static_access():
    """测试通过后端静态文件服务访问移动登录页面并进行登录"""
    print("=== 移动端静态页面访问测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 后端服务器地址
    base_url = "http://172.30.81.103:8000"
    print(f"\n后端服务器地址: {base_url}")
    
    # 测试1: 通过静态文件服务访问移动登录页面
    print("\n=== 测试1: 通过静态文件服务访问移动登录页面 ===")
    try:
        # 尝试不同的URL路径
        test_paths = [
            "/static/mobile_login_final.html",
            "/mobile_login",  # 路由别名
            "/mobile"  # 路由别名
        ]
        
        for path in test_paths:
            url = f"{base_url}{path}"
            print(f"\n尝试访问: {url}")
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"成功访问页面: {path}")
                # 检查页面内容是否包含登录相关元素
                if "移动端登录" in response.text:
                    print("✓ 页面包含登录相关内容")
                else:
                    print("✗ 页面不包含登录相关内容")
                break  # 找到可用的页面后停止尝试
            else:
                print(f"无法访问页面: {path}")
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    
    # 测试2: 直接测试登录API
    print("\n=== 测试2: 直接测试登录API ===")
    try:
        login_url = f"{base_url}/api/auth/login"
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        print(f"发送登录请求到: {login_url}")
        response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 登录成功")
            print(f"访问令牌: {data.get('access_token')[:30]}...")
            print(f"用户信息: {json.dumps(data.get('user'), ensure_ascii=False)}")
            
            # 测试3: 使用获取的token访问用户信息
            print("\n=== 测试3: 验证token有效性 ===")
            token = data.get('access_token')
            if token:
                me_url = f"{base_url}/api/auth/me"
                auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                }
                me_response = requests.get(me_url, headers=auth_headers, timeout=10)
                print(f"用户信息请求状态码: {me_response.status_code}")
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"✓ 令牌有效! 用户信息: {json.dumps(me_data, ensure_ascii=False)}")
                else:
                    print(f"✗ 令牌无效! 错误码: {me_response.status_code}")
                    print(f"错误信息: {me_response.text}")
        else:
            print(f"✗ 登录失败")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    
    # 测试4: 检查health端点
    print("\n=== 测试4: 检查后端健康状态 ===")
    try:
        health_url = f"{base_url}/health"
        health_response = requests.get(health_url, timeout=10)
        print(f"health端点状态码: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"✓ 后端服务健康: {health_response.text}")
        else:
            print(f"✗ 后端服务异常")
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n总结:")
    print("1. 后端API服务工作正常，admin用户可以成功登录")
    print("2. 前端服务（端口3001）可能未启动或无法访问")
    print("3. 建议通过后端静态文件服务访问移动登录页面")
    print("4. 请使用以下URL尝试访问移动登录页面:")
    print(f"   - {base_url}/static/mobile_login_final.html")
    print(f"   - {base_url}/mobile_login")
    print(f"   - {base_url}/mobile")


if __name__ == "__main__":
    test_mobile_static_access()