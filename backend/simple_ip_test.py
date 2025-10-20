#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的IP地址登录测试
"""

import requests
import json

def simple_test():
    """简单测试"""
    url = "http://172.30.81.103:8000/api/auth/login"
    data = {"username": "admin", "password": "admin123"}
    
    print(f"测试URL: {url}")
    print(f"测试数据: {data}")
    
    try:
        response = requests.post(url, json=data, timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"Token: {result.get('access_token', 'N/A')[:30]}...")
        else:
            print(f"❌ 登录失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    simple_test()