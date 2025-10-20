#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络连接测试脚本
"""

import requests
import os
import socket

def check_network():
    """检查网络连接"""
    print("=== 网络连接测试 ===")
    
    # 检查环境变量
    print(f"环境变量 NO_PROXY: {os.environ.get('NO_PROXY', 'not set')}")
    print(f"环境变量 HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'not set')}")
    print(f"环境变量 HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'not set')}")
    
    # 获取本机IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"本机IP: {local_ip}")
    except:
        print("无法获取本机IP")
    
    # 测试外部连接
    print("\n测试外部连接...")
    try:
        response = requests.get('http://httpbin.org/ip', timeout=5)
        print(f"✅ 外部连接成功: {response.status_code}")
        print(f"公网IP: {response.json()}")
    except Exception as e:
        print(f"❌ 外部连接失败: {e}")
    
    # 测试本地后端
    print("\n测试本地后端...")
    base_url = "http://172.30.81.103:8000"
    
    try:
        health_url = f"{base_url}/health"
        print(f"测试健康检查: {health_url}")
        health_response = requests.get(health_url, timeout=5)
        print(f"健康检查状态: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print("✅ 后端服务正常运行")
            return True
        else:
            print(f"⚠️  后端服务异常: {health_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到后端服务器")
        print("可能原因:")
        print("1. 后端服务器未运行")
        print("2. IP地址不正确")
        print("3. 防火墙阻止连接")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_login():
    """测试登录功能"""
    print("\n=== 登录测试 ===")
    base_url = "http://172.30.81.103:8000"
    login_url = f"{base_url}/api/auth/login"
    
    test_credentials = {"username": "admin", "password": "admin123"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    
    try:
        response = requests.post(login_url, json=test_credentials, headers=headers, timeout=10)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 登录成功!")
            token = data.get("access_token", "")
            if token:
                print(f"Token: {token[:30]}...")
                return token
            else:
                print("❌ 未获取到token")
                return None
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return None

if __name__ == "__main__":
    # 清除代理环境变量
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if key in os.environ:
            del os.environ[key]
    os.environ['NO_PROXY'] = '*'
    
    print("清除代理设置...")
    print(f"NO_PROXY: {os.environ.get('NO_PROXY', 'not set')}")
    
    # 测试网络连接
    backend_ok = check_network()
    
    if backend_ok:
        # 测试登录
        token = test_login()
        
        if token:
            print("\n✅ 移动端登录测试通过!")
            print("手机端访问地址: http://172.30.81.103:3000")
            print("使用账号: admin/admin123")
        else:
            print("\n❌ 移动端登录测试失败!")
    else:
        print("\n❌ 后端服务连接失败，无法进行登录测试!")
        
    print("\n=== 测试完成 ===")