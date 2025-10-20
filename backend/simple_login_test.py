#!/usr/bin/env python3
import requests
import json

def test_login():
    url = "http://localhost:8000/api/auth/login"
    
    # 测试数据
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"测试登录端点: {url}")
    print(f"登录数据: {login_data}")
    
    try:
        response = requests.post(url, json=login_data)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("登录成功!")
            data = response.json()
            print(f"响应数据: {data}")
            return data.get('access_token')
        else:
            print(f"登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None

if __name__ == "__main__":
    test_login()