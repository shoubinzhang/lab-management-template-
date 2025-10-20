#!/usr/bin/env python3
"""
调试试剂API端点
"""

import requests
import json

def test_reagent_api():
    """测试试剂API端点"""
    base_url = "http://localhost:8000"
    
    # 1. 登录获取token
    print("1. 登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("✅ 登录成功")
            
            # 2. 测试试剂列表API
            print("\n2. 测试试剂列表API...")
            headers = {"Authorization": f"Bearer {token}"}
            
            reagents_response = requests.get(f"{base_url}/api/reagents", headers=headers)
            print(f"试剂列表状态码: {reagents_response.status_code}")
            
            if reagents_response.status_code == 200:
                data = reagents_response.json()
                print(f"✅ API返回成功")
                print(f"总数: {data.get('total', 'N/A')}")
                print(f"当前页数据数量: {len(data.get('items', []))}")
                print(f"页数: {data.get('page', 'N/A')}")
                print(f"每页数量: {data.get('per_page', 'N/A')}")
                
                # 显示前几个试剂
                items = data.get('items', [])
                if items:
                    print("\n前3个试剂:")
                    for i, item in enumerate(items[:3]):
                        print(f"  {i+1}. ID: {item.get('id')}, 名称: {item.get('name')}")
                else:
                    print("❌ 没有试剂数据")
            else:
                print(f"❌ API调用失败: {reagents_response.text}")
        else:
            print(f"❌ 登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_reagent_api()