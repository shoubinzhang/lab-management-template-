#!/usr/bin/env python3
"""
简化的系统验证测试
专注于核心功能验证
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_login_and_basic_apis():
    """测试登录和基础API"""
    print("🚀 开始简化系统验证测试")
    print("=" * 40)
    
    # 1. 测试登录
    print("🔐 测试登录...")
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 登录成功 - 用户: {data.get('user', {}).get('username')}")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 测试试剂列表
    print("\n🧪 测试试剂列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/reagents/", headers=headers, timeout=10)
        if response.status_code == 200:
            reagents = response.json()
            print(f"✅ 获取试剂列表成功 - 共 {len(reagents)} 个试剂")
            if reagents:
                print(f"   示例试剂: {reagents[0].get('name')}")
        else:
            print(f"❌ 获取试剂列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 试剂API异常: {e}")
    
    # 3. 测试耗材列表
    print("\n📦 测试耗材列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/consumables/", headers=headers, timeout=10)
        if response.status_code == 200:
            consumables = response.json()
            print(f"✅ 获取耗材列表成功 - 共 {len(consumables)} 个耗材")
            if consumables:
                print(f"   示例耗材: {consumables[0].get('name')}")
        else:
            print(f"❌ 获取耗材列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 耗材API异常: {e}")
    
    # 4. 测试使用记录
    print("\n📊 测试使用记录...")
    try:
        response = requests.get(f"{BASE_URL}/api/usage-records/", headers=headers, timeout=10)
        if response.status_code == 200:
            records = response.json()
            print(f"✅ 获取使用记录成功 - 共 {len(records)} 条记录")
        else:
            print(f"❌ 获取使用记录失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 使用记录API异常: {e}")
    
    # 5. 测试申请列表
    print("\n📝 测试申请列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/requests/", headers=headers, timeout=10)
        if response.status_code == 200:
            requests_list = response.json()
            print(f"✅ 获取申请列表成功 - 共 {len(requests_list)} 个申请")
        else:
            print(f"❌ 获取申请列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 申请API异常: {e}")
    
    print("\n" + "=" * 40)
    print("✅ 基础功能验证完成")

if __name__ == "__main__":
    test_login_and_basic_apis()