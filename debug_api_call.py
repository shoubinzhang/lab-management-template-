#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code}")
        print(f"响应: {response.text}")
        return None

def test_create_reagent():
    """测试创建试剂"""
    token = login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    reagent_data = {
        "name": "调试测试试剂",
        "manufacturer": "测试制造商",
        "unit": "mL",
        "category": "测试类别",
        "quantity": 100.0
    }
    
    print("发送的数据:")
    print(json.dumps(reagent_data, indent=2, ensure_ascii=False))
    
    response = requests.post(f"{BASE_URL}/api/reagents", json=reagent_data, headers=headers)
    
    print(f"\n响应状态码: {response.status_code}")
    print("响应数据:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        reagent_id = response.json()["id"]
        
        # 删除测试数据
        delete_response = requests.delete(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
        print(f"\n删除响应: {delete_response.status_code}")

if __name__ == "__main__":
    test_create_reagent()