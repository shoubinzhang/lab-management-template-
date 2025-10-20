#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的手机登录测试脚本
使用实际IP地址测试登录功能
"""

import requests
import json
import sys

def test_mobile_login_with_ip():
    """使用实际IP地址测试手机登录功能"""
    # 使用实际IP地址
    base_url = "http://172.30.81.103:8000"
    login_url = f"{base_url}/api/auth/login"
    
    # 测试用户凭据
    test_credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("=== 修复后的手机登录测试 ===")
    print(f"登录URL: {login_url}")
    print(f"测试凭据: {test_credentials}")
    print(f"模拟手机访问...")
    
    try:
        # 模拟手机浏览器的请求头
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        
        response = requests.post(
            login_url,
            json=test_credentials,
            headers=headers,
            timeout=10
        )
        
        print(f"\n📱 手机登录测试结果:")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ 登录成功!")
                print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
                
                # 测试token是否有效
                if 'access_token' in data:
                    token = data['access_token']
                    test_mobile_protected_endpoint(base_url, token, headers)
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"❌ 登录失败!")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器")
        print("请检查:")
        print("1. 后端服务器是否运行在 172.30.81.103:8000")
        print("2. 防火墙是否允许端口8000")
        print("3. 网络连接是否正常")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_mobile_protected_endpoint(base_url, token, mobile_headers):
    """测试手机访问受保护的端点"""
    print("\n🔐 测试受保护端点...")
    
    headers = {
        **mobile_headers,
        "Authorization": f"Bearer {token}"
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
            print(f"✅ 用户信息获取成功: {data.get('username', 'N/A')}")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试受保护端点时出错: {e}")

def test_frontend_access():
    """测试前端页面访问"""
    print("\n🌐 测试前端页面访问...")
    frontend_url = "http://172.30.81.103:3000"
    
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ 前端页面访问成功: {frontend_url}")
            print(f"页面大小: {len(response.content)} bytes")
        else:
            print(f"❌ 前端页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端页面访问错误: {e}")

if __name__ == "__main__":
    test_mobile_login_with_ip()
    test_frontend_access()
    
    print("\n📋 手机访问指南:")
    print("1. 确保手机和电脑连接同一WiFi")
    print("2. 在手机浏览器中访问: http://172.30.81.103:3000")
    print("3. 使用 admin/admin123 登录")
    print("4. 如果无法访问，检查防火墙设置")