#!/usr/bin/env python3
"""
测试修复后的试剂API
"""
import requests
import json

def test_reagents_api():
    """测试试剂API是否正常工作"""
    base_url = "http://localhost:8000"
    
    try:
        # 1. 先登录获取token
        print("1. 登录获取token...")
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
        # 2. 测试试剂列表API
        print("\n2. 测试试剂列表API...")
        reagents_response = requests.get(
            f"{base_url}/api/reagents?page=1&per_page=5",
            headers=headers
        )
        
        print(f"状态码: {reagents_response.status_code}")
        
        if reagents_response.status_code == 200:
            data = reagents_response.json()
            print(f"✅ 试剂列表API正常工作")
            print(f"总数: {data['total']}")
            print(f"当前页: {data['page']}")
            print(f"每页数量: {data['per_page']}")
            
            if data['items']:
                print(f"第一个试剂: {data['items'][0]['name']}")
                print(f"试剂字段: {list(data['items'][0].keys())}")
            
            return True
        else:
            print(f"❌ 试剂列表API失败: {reagents_response.status_code}")
            print(f"错误信息: {reagents_response.text}")
            return False
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 测试修复后的试剂API ===")
    success = test_reagents_api()
    
    if success:
        print("\n🎉 试剂API测试成功!")
    else:
        print("\n❌ 试剂API测试失败")