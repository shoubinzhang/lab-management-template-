#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机登录测试脚本
用于测试和诊断手机登录问题
"""

import requests
import json
import sys

def test_mobile_login():
    """测试手机登录功能"""
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/auth/login"
    
    # 测试用户凭据
    test_credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("开始测试手机登录...")
    print(f"登录URL: {login_url}")
    print(f"测试凭据: {test_credentials}")
    
    try:
        # 发送登录请求
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Accept": "application/json"
        }
        
        response = requests.post(
            login_url,
            json=test_credentials,
            headers=headers,
            timeout=10
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"登录成功!")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # 测试token是否有效
                if 'access_token' in data:
                    token = data['access_token']
                    test_protected_endpoint(base_url, token)
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"登录失败!")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("连接错误: 无法连接到服务器")
    except requests.exceptions.Timeout:
        print("请求超时")
    except Exception as e:
        print(f"未知错误: {e}")

def test_protected_endpoint(base_url, token):
    """测试受保护的端点"""
    print("\n测试受保护端点...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试用户信息端点
    try:
        response = requests.get(
            f"{base_url}/api/auth/me",
            headers=headers,
            timeout=10
        )
        
        print(f"用户信息端点状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"用户信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"获取用户信息失败: {response.text}")
            
    except Exception as e:
        print(f"测试受保护端点时出错: {e}")

if __name__ == "__main__":
    test_mobile_login()