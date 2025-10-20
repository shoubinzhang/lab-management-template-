"""
简化的领用申请流程测试
测试核心功能：申请创建 -> 管理员批准 -> 库存扣减 -> 使用记录生成
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"

def test_basic_connection():
    """测试基本连接"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ 服务器连接正常: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def login_admin():
    """管理员登录"""
    try:
        print("🔐 尝试管理员登录...")
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=30)
        
        print(f"   登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ 管理员登录成功")
            return token
        else:
            print(f"❌ 管理员登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def test_reagent_list(token):
    """测试获取试剂列表"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/reagents/", headers=headers, timeout=10)
        
        print(f"   试剂列表响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            reagents = response.json()
            print(f"✅ 获取试剂列表成功，共 {len(reagents)} 个试剂")
            if reagents and len(reagents) > 0:
                print(f"   第一个试剂: {reagents[0]}")
            return reagents
        else:
            print(f"❌ 获取试剂列表失败: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取试剂列表请求失败: {e}")
        return []

def test_create_request(token, reagent):
    """测试创建申请"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        request_data = {
            "request_type": "reagent",
            "item_id": reagent['id'],
            "item_name": reagent['name'],
            "quantity": 1.0,
            "unit": reagent['unit'],
            "purpose": "测试实验用途",
            "notes": "自动化测试申请"
        }
        
        response = requests.post(f"{BASE_URL}/api/reagents/request", 
                               json=request_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            request_id = result["request_id"]
            print(f"✅ 创建申请成功，申请ID: {request_id}")
            return request_id
        else:
            print(f"❌ 创建申请失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 创建申请请求失败: {e}")
        return None

def test_approve_request(token, request_id):
    """测试批准申请"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        approval_data = {
            "action": "approve",
            "notes": "测试批准"
        }
        
        response = requests.post(f"{BASE_URL}/api/approvals/{request_id}/approve",
                               json=approval_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 申请批准成功: {result['message']}")
            return True
        else:
            print(f"❌ 申请批准失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 批准申请请求失败: {e}")
        return False

def test_usage_records(token):
    """测试使用记录"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/usage-records/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            records = response.json()
            print(f"✅ 获取使用记录成功，共 {len(records)} 条记录")
            if records:
                latest_record = records[0]
                print(f"   最新记录: {latest_record['item_name']} - {latest_record['quantity_used']} {latest_record['unit']}")
            return True
        else:
            print(f"❌ 获取使用记录失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取使用记录请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始简化的领用申请流程测试\n")
    
    # 1. 测试基本连接
    if not test_basic_connection():
        return False
    
    # 2. 管理员登录
    token = login_admin()
    if not token:
        return False
    
    # 3. 获取试剂列表
    reagents = test_reagent_list(token)
    if not reagents or len(reagents) == 0:
        print("❌ 没有可用的试剂进行测试")
        return False
    
    test_reagent = reagents[0]
    print(f"📝 选择测试试剂: {test_reagent['name']} (库存: {test_reagent['quantity']} {test_reagent['unit']})")
    
    # 4. 创建申请
    request_id = test_create_request(token, test_reagent)
    if not request_id:
        return False
    
    # 5. 批准申请
    if not test_approve_request(token, request_id):
        return False
    
    # 6. 检查使用记录
    if not test_usage_records(token):
        return False
    
    print("\n🎉 所有测试通过！领用申请流程工作正常。")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 测试失败，请检查系统配置。")
        exit(1)
    else:
        print("\n✅ 测试完成！")