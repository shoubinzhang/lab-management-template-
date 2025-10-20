"""
测试完整的领用申请流程
包括：申请创建 -> 管理员批准 -> 库存扣减 -> 使用记录生成
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
USER_USERNAME = "testuser"
USER_PASSWORD = "testpass"

def login(username, password):
    """登录并获取token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.text}")
        return None

def get_headers(token):
    """获取请求头"""
    return {"Authorization": f"Bearer {token}"}

def test_reagent_request_flow():
    """测试试剂申请流程"""
    print("🧪 开始测试试剂申请流程...")
    
    # 1. 管理员登录
    admin_token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not admin_token:
        print("❌ 管理员登录失败")
        return False
    
    admin_headers = get_headers(admin_token)
    print("✅ 管理员登录成功")
    
    # 2. 获取试剂列表，选择一个试剂
    response = requests.get(f"{BASE_URL}/api/reagents/", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取试剂列表失败: {response.text}")
        return False
    
    reagents = response.json()
    if not reagents:
        print("❌ 没有可用的试剂")
        return False
    
    test_reagent = reagents[0]
    print(f"✅ 选择测试试剂: {test_reagent['name']} (库存: {test_reagent['quantity']} {test_reagent['unit']})")
    
    # 记录原始库存
    original_quantity = test_reagent['quantity']
    request_quantity = min(1.0, original_quantity / 2)  # 申请一半库存或1单位
    
    # 3. 创建试剂申请
    request_data = {
        "request_type": "reagent",
        "item_id": test_reagent['id'],
        "item_name": test_reagent['name'],
        "quantity": request_quantity,
        "unit": test_reagent['unit'],
        "purpose": "测试实验用途",
        "notes": "自动化测试申请"
    }
    
    response = requests.post(f"{BASE_URL}/api/reagents/request", 
                           json=request_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 创建试剂申请失败: {response.text}")
        return False
    
    request_result = response.json()
    request_id = request_result["request_id"]
    print(f"✅ 试剂申请创建成功，申请ID: {request_id}")
    
    # 4. 获取待审批列表
    response = requests.get(f"{BASE_URL}/api/approvals/pending", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取待审批列表失败: {response.text}")
        return False
    
    pending_requests = response.json()
    target_request = None
    for req in pending_requests:
        if req["request_id"] == request_id:
            target_request = req
            break
    
    if not target_request:
        print(f"❌ 在待审批列表中找不到申请 {request_id}")
        return False
    
    print(f"✅ 在待审批列表中找到申请: {target_request['item_name']}")
    
    # 5. 批准申请
    approval_data = {
        "action": "approve",
        "notes": "测试批准"
    }
    
    response = requests.post(f"{BASE_URL}/api/approvals/{request_id}/approve",
                           json=approval_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 批准申请失败: {response.text}")
        return False
    
    approval_result = response.json()
    print(f"✅ 申请批准成功: {approval_result['message']}")
    
    # 6. 验证库存是否扣减
    response = requests.get(f"{BASE_URL}/api/reagents/{test_reagent['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取试剂详情失败: {response.text}")
        return False
    
    updated_reagent = response.json()
    new_quantity = updated_reagent['quantity']
    expected_quantity = original_quantity - request_quantity
    
    if abs(new_quantity - expected_quantity) < 0.001:  # 浮点数比较
        print(f"✅ 库存扣减正确: {original_quantity} -> {new_quantity}")
    else:
        print(f"❌ 库存扣减错误: 期望 {expected_quantity}，实际 {new_quantity}")
        return False
    
    # 7. 验证使用记录是否生成
    response = requests.get(f"{BASE_URL}/api/usage-records/", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取使用记录失败: {response.text}")
        return False
    
    usage_records = response.json()
    target_record = None
    for record in usage_records:
        if record["request_id"] == request_id:
            target_record = record
            break
    
    if not target_record:
        print(f"❌ 未找到对应的使用记录")
        return False
    
    print(f"✅ 使用记录生成成功: {target_record['item_name']} - {target_record['quantity_used']} {target_record['unit']}")
    
    return True

def test_consumable_request_flow():
    """测试耗材申请流程"""
    print("\n🧰 开始测试耗材申请流程...")
    
    # 1. 管理员登录
    admin_token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not admin_token:
        print("❌ 管理员登录失败")
        return False
    
    admin_headers = get_headers(admin_token)
    
    # 2. 获取耗材列表
    response = requests.get(f"{BASE_URL}/api/consumables/", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取耗材列表失败: {response.text}")
        return False
    
    consumables = response.json()
    if not consumables:
        print("❌ 没有可用的耗材")
        return False
    
    test_consumable = consumables[0]
    print(f"✅ 选择测试耗材: {test_consumable['name']} (库存: {test_consumable['quantity']} {test_consumable['unit']})")
    
    # 记录原始库存
    original_quantity = test_consumable['quantity']
    request_quantity = min(1.0, original_quantity / 2)
    
    # 3. 创建耗材申请
    request_data = {
        "request_type": "consumable",
        "item_id": test_consumable['id'],
        "item_name": test_consumable['name'],
        "quantity": request_quantity,
        "unit": test_consumable['unit'],
        "purpose": "测试实验用途",
        "notes": "自动化测试申请"
    }
    
    response = requests.post(f"{BASE_URL}/api/consumables/request",
                           json=request_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 创建耗材申请失败: {response.text}")
        return False
    
    request_result = response.json()
    request_id = request_result["request_id"]
    print(f"✅ 耗材申请创建成功，申请ID: {request_id}")
    
    # 4. 批准申请
    approval_data = {
        "action": "approve",
        "notes": "测试批准"
    }
    
    response = requests.post(f"{BASE_URL}/api/approvals/{request_id}/approve",
                           json=approval_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 批准申请失败: {response.text}")
        return False
    
    approval_result = response.json()
    print(f"✅ 申请批准成功: {approval_result['message']}")
    
    # 5. 验证库存扣减
    response = requests.get(f"{BASE_URL}/api/consumables/{test_consumable['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取耗材详情失败: {response.text}")
        return False
    
    updated_consumable = response.json()
    new_quantity = updated_consumable['quantity']
    expected_quantity = original_quantity - request_quantity
    
    if abs(new_quantity - expected_quantity) < 0.001:
        print(f"✅ 库存扣减正确: {original_quantity} -> {new_quantity}")
    else:
        print(f"❌ 库存扣减错误: 期望 {expected_quantity}，实际 {new_quantity}")
        return False
    
    return True

def test_insufficient_stock():
    """测试库存不足的情况"""
    print("\n⚠️ 开始测试库存不足情况...")
    
    admin_token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not admin_token:
        print("❌ 管理员登录失败")
        return False
    
    admin_headers = get_headers(admin_token)
    
    # 获取试剂列表
    response = requests.get(f"{BASE_URL}/api/reagents/", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 获取试剂列表失败")
        return False
    
    reagents = response.json()
    if not reagents:
        print("❌ 没有可用的试剂")
        return False
    
    test_reagent = reagents[0]
    
    # 申请超过库存的数量
    excessive_quantity = test_reagent['quantity'] + 100
    
    request_data = {
        "request_type": "reagent",
        "item_id": test_reagent['id'],
        "item_name": test_reagent['name'],
        "quantity": excessive_quantity,
        "unit": test_reagent['unit'],
        "purpose": "测试库存不足",
        "notes": "测试超量申请"
    }
    
    response = requests.post(f"{BASE_URL}/api/reagents/request",
                           json=request_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ 创建申请失败: {response.text}")
        return False
    
    request_result = response.json()
    request_id = request_result["request_id"]
    
    # 尝试批准申请（应该失败）
    approval_data = {
        "action": "approve",
        "notes": "测试批准"
    }
    
    response = requests.post(f"{BASE_URL}/api/approvals/{request_id}/approve",
                           json=approval_data, headers=admin_headers)
    
    if response.status_code == 400:
        error_detail = response.json().get("detail", "")
        if "库存不足" in error_detail:
            print(f"✅ 库存不足检查正常: {error_detail}")
            return True
        else:
            print(f"❌ 错误信息不正确: {error_detail}")
            return False
    else:
        print(f"❌ 应该返回400错误，但返回了: {response.status_code}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试完整的领用申请流程\n")
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    success_count = 0
    total_tests = 3
    
    # 测试试剂申请流程
    if test_reagent_request_flow():
        success_count += 1
    
    # 测试耗材申请流程
    if test_consumable_request_flow():
        success_count += 1
    
    # 测试库存不足情况
    if test_insufficient_stock():
        success_count += 1
    
    print(f"\n📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！领用申请流程工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查系统配置。")
        return False

if __name__ == "__main__":
    main()