#!/usr/bin/env python3
"""
最终系统验证测试
验证完整的领用申请流程和所有API功能
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_system_health():
    """测试系统健康状态"""
    print("🔍 测试系统健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 404:
            print("✅ 服务器响应正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def test_user_login():
    """测试用户登录"""
    print("\n🔐 测试用户登录...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            print(f"✅ 登录成功 - 用户: {user_info.get('username')}, 角色: {user_info.get('role')}")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def test_reagents_api(token):
    """测试试剂API"""
    print("\n🧪 测试试剂API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/reagents/", headers=headers, timeout=30)
        if response.status_code == 200:
            reagents = response.json()
            print(f"✅ 获取试剂列表成功 - 共 {len(reagents)} 个试剂")
            if reagents:
                first_reagent = reagents[0]
                print(f"   第一个试剂: {first_reagent.get('name')} (库存: {first_reagent.get('quantity')} {first_reagent.get('unit')})")
            return reagents
        else:
            print(f"❌ 获取试剂列表失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 试剂API请求失败: {e}")
        return []

def test_consumables_api(token):
    """测试耗材API"""
    print("\n📦 测试耗材API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/consumables/", headers=headers, timeout=30)
        if response.status_code == 200:
            consumables = response.json()
            print(f"✅ 获取耗材列表成功 - 共 {len(consumables)} 个耗材")
            if consumables:
                first_consumable = consumables[0]
                print(f"   第一个耗材: {first_consumable.get('name')} (库存: {first_consumable.get('quantity')} {first_consumable.get('unit')})")
            return consumables
        else:
            print(f"❌ 获取耗材列表失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 耗材API请求失败: {e}")
        return []

def test_usage_records_api(token):
    """测试使用记录API"""
    print("\n📊 测试使用记录API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 测试获取所有使用记录
        response = requests.get(f"{BASE_URL}/api/usage-records/", headers=headers, timeout=30)
        if response.status_code == 200:
            records = response.json()
            print(f"✅ 获取使用记录列表成功 - 共 {len(records)} 条记录")
        else:
            print(f"❌ 获取使用记录列表失败: {response.status_code}")
            return False
        
        # 测试获取我的使用记录
        response = requests.get(f"{BASE_URL}/api/usage-records/my", headers=headers, timeout=30)
        if response.status_code == 200:
            my_records = response.json()
            print(f"✅ 获取我的使用记录成功 - 共 {len(my_records)} 条记录")
        else:
            print(f"❌ 获取我的使用记录失败: {response.status_code}")
            return False
        
        # 测试获取使用统计
        response = requests.get(f"{BASE_URL}/api/usage-records/stats", headers=headers, timeout=30)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 获取使用统计成功 - 总记录数: {stats.get('total_records', 0)}")
            print(f"   按类型统计: {stats.get('by_item_type', {})}")
        else:
            print(f"❌ 获取使用统计失败: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 使用记录API请求失败: {e}")
        return False

def test_requests_api(token, reagents):
    """测试申请API"""
    print("\n📝 测试申请API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    if not reagents:
        print("❌ 没有可用的试剂进行测试")
        return False
    
    try:
        # 获取现有申请列表
        response = requests.get(f"{BASE_URL}/api/requests/", headers=headers, timeout=30)
        if response.status_code == 200:
            requests_list = response.json()
            print(f"✅ 获取申请列表成功 - 共 {len(requests_list)} 个申请")
        else:
            print(f"❌ 获取申请列表失败: {response.status_code}")
            return False
        
        # 创建新申请
        first_reagent = reagents[0]
        request_data = {
            "request_type": "reagent",
            "item_id": first_reagent["id"],
            "item_name": first_reagent["name"],
            "quantity": 10.0,
            "unit": first_reagent["unit"],
            "purpose": "系统测试用途",
            "urgency": "normal"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/requests/",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            new_request = response.json()
            request_id = new_request["id"]
            print(f"✅ 创建申请成功 - 申请ID: {request_id}")
            print(f"   申请内容: {new_request['item_name']} {new_request['quantity']} {new_request['unit']}")
            return request_id
        else:
            print(f"❌ 创建申请失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 申请API请求失败: {e}")
        return False

def test_approval_flow(token, request_id):
    """测试批准流程"""
    print(f"\n✅ 测试批准流程 - 申请ID: {request_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 批准申请
        approval_data = {
            "notes": "系统测试批准"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/requests/{request_id}/approve",
            json=approval_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 申请批准成功")
            print(f"   使用记录ID: {result.get('usage_record_id')}")
            print(f"   剩余库存: {result.get('remaining_stock')}")
            return True
        else:
            print(f"❌ 申请批准失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 批准流程请求失败: {e}")
        return False

def test_user_info(token):
    """测试用户信息API"""
    print("\n👤 测试用户信息API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=30)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 获取用户信息成功")
            print(f"   用户名: {user_info.get('username')}")
            print(f"   邮箱: {user_info.get('email')}")
            print(f"   角色: {user_info.get('role')}")
            return True
        else:
            print(f"❌ 获取用户信息失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 用户信息API请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始最终系统验证测试")
    print("=" * 50)
    
    test_results = []
    
    # 1. 系统健康检查
    health_ok = test_system_health()
    test_results.append(("系统健康检查", health_ok))
    
    if not health_ok:
        print("\n❌ 系统健康检查失败，停止测试")
        return
    
    # 2. 用户登录
    token = test_user_login()
    test_results.append(("用户登录", token is not None))
    
    if not token:
        print("\n❌ 用户登录失败，停止测试")
        return
    
    # 3. 用户信息API
    user_info_ok = test_user_info(token)
    test_results.append(("用户信息API", user_info_ok))
    
    # 4. 试剂API
    reagents = test_reagents_api(token)
    test_results.append(("试剂API", len(reagents) > 0))
    
    # 5. 耗材API
    consumables = test_consumables_api(token)
    test_results.append(("耗材API", len(consumables) > 0))
    
    # 6. 使用记录API
    usage_records_ok = test_usage_records_api(token)
    test_results.append(("使用记录API", usage_records_ok))
    
    # 7. 申请API
    request_id = test_requests_api(token, reagents)
    test_results.append(("申请API", request_id is not False))
    
    # 8. 批准流程（如果申请创建成功）
    if request_id:
        approval_ok = test_approval_flow(token, request_id)
        test_results.append(("批准流程", approval_ok))
    
    # 输出测试结果总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统功能完整且正常运行。")
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败，请检查相关功能。")
    
    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()