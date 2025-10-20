#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_devices_endpoint():
    """直接测试设备API端点"""
    base_url = "http://127.0.0.1:8001"
    
    print("开始测试设备API端点...")
    
    # 1. 先登录获取token
    print("\n1. 登录获取token")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.text}")
            return
        
        token_data = login_response.json()
        token = token_data.get('access_token')
        print(f"获取到token: {token[:50]}...")
        
    except Exception as e:
        print(f"登录请求失败: {e}")
        return
    
    # 2. 测试设备API
    print("\n2. 测试设备API")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"发送GET请求到: {base_url}/api/devices")
        print(f"请求头: {headers}")
        
        devices_response = requests.get(
            f"{base_url}/api/devices",
            headers=headers,
            timeout=10
        )
        
        print(f"\n响应状态码: {devices_response.status_code}")
        print(f"响应头: {dict(devices_response.headers)}")
        
        if devices_response.status_code == 200:
            data = devices_response.json()
            print(f"\n成功获取设备数据:")
            print(f"数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"数据键: {list(data.keys())}")
                if 'items' in data:
                    print(f"设备数量: {len(data['items'])}")
                elif 'total' in data:
                    print(f"总数: {data['total']}")
            elif isinstance(data, list):
                print(f"设备数量: {len(data)}")
            
            print(f"\n完整响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"\n请求失败:")
            print(f"状态码: {devices_response.status_code}")
            print(f"响应文本: {devices_response.text}")
            print(f"响应内容: {devices_response.content}")
            
    except Exception as e:
        print(f"设备API请求失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    test_devices_endpoint()