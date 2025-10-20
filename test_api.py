#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8001"

def test_health():
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"健康检查状态码: {response.status_code}")
        print(f"健康检查响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_login():
    """测试登录端点"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"登录状态码: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print(f"登录成功，获取到token: {token_data.get('access_token', '')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def test_devices_api(token):
    """测试设备API端点"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        print(f"发送请求到: {BASE_URL}/api/devices")
        print(f"请求头: {headers}")
        
        response = requests.get(
            f"{BASE_URL}/api/devices",
            headers=headers,
            timeout=10
        )
        print(f"设备API状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            devices_data = response.json()
            print(f"设备API成功，返回 {devices_data.get('total', 0)} 个设备")
            return True
        else:
            print(f"设备API失败: {response.text}")
            print(f"响应内容: {response.content}")
            return False
    except Exception as e:
        print(f"设备API请求失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def main():
    print("开始API测试...")
    print("=" * 50)
    
    # 测试健康检查
    print("1. 测试健康检查")
    if not test_health():
        print("健康检查失败，退出测试")
        return
    
    print("\n2. 测试登录")
    token = test_login()
    if not token:
        print("登录失败，退出测试")
        return
    
    print("\n3. 测试设备API")
    if test_devices_api(token):
        print("设备API测试成功！")
    else:
        print("设备API测试失败！")
    
    print("\n" + "=" * 50)
    print("API测试完成")

if __name__ == "__main__":
    main()