#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的手机登录测试脚本
"""

import requests
import json

def test_mobile_login():
    """测试手机登录功能"""
    base_url = "http://172.30.81.103:8000"
    login_url = f"{base_url}/api/auth/login"
    
    print("=== 手机登录测试 ===")
    print(f"登录URL: {login_url}")
    
    try:
        # 测试健康检查
        health_url = f"{base_url}/health"
        print(f"测试健康检查: {health_url}")
        health_response = requests.get(health_url, timeout=5)
        print(f"健康检查状态: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print(f"⚠️  后端服务异常: {health_response.status_code}")
        
        # 测试登录
        test_credentials = {"username": "admin", "password": "admin123"}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
        }
        
        print("测试登录...")
        response = requests.post(login_url, json=test_credentials, headers=headers, timeout=10)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 登录成功!")
            token = data.get("access_token", "")
            if token:
                print(f"Token: {token[:30]}...")
                
                # 测试用户信息端点
                user_url = f"{base_url}/api/auth/me"
                user_headers = {**headers, "Authorization": f"Bearer {token}"}
                user_response = requests.get(user_url, headers=user_headers)
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    print(f"✅ 用户信息获取成功: {user_data.get('username', 'N/A')}")
                else:
                    print(f"❌ 获取用户信息失败: {user_response.status_code}")
            else:
                print("❌ 未获取到token")
        else:
            print(f"❌ 登录失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器")
        print("请检查:")
        print("1. 后端服务器是否运行在 172.30.81.103:8000")
        print("2. 防火墙是否允许端口8000")
        print("3. 网络连接是否正常")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    test_mobile_login()