#!/usr/bin/env python3
"""
测试新添加的制造商和单位字段功能
"""

import requests
import json
import sys

# API 基础 URL
BASE_URL = "http://localhost:8000"

def login():
    """登录获取 token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return None

def test_add_reagent_with_new_fields(token):
    """测试添加试剂时包含制造商和单位字段"""
    headers = {"Authorization": f"Bearer {token}"}
    
    reagent_data = {
        "name": "测试试剂-新字段",
        "manufacturer": "Sigma-Aldrich",  # 新字段
        "lot_number": "BATCH-001",
        "quantity": 100.0,
        "unit": "mL",  # 新字段
        "location": "冰箱A",
        "expiry_date": "2025-12-31T00:00:00",
        "category": "有机试剂",
        "safety_notes": "测试安全说明",
        "price": 299.99
    }
    
    response = requests.post(f"{BASE_URL}/api/reagents", json=reagent_data, headers=headers)
    
    if response.status_code == 200:
        reagent = response.json()
        print("✅ 添加试剂成功")
        print(f"   制造商: {reagent.get('manufacturer', 'N/A')}")
        print(f"   单位: {reagent.get('unit', 'N/A')}")
        
        # 验证字段是否正确保存
        if reagent.get('manufacturer') == reagent_data['manufacturer']:
            print("✓ 制造商字段保存正确")
        else:
            print("✗ 制造商字段保存失败")
            
        if reagent.get('unit') == reagent_data['unit']:
            print("✓ 单位字段保存正确")
        else:
            print("✗ 单位字段保存失败")
            
        return reagent.get('id')
    else:
        print(f"❌ 添加试剂失败: {response.status_code}")
        print(f"   响应: {response.text}")
        return None

def test_edit_reagent_with_new_fields(token, reagent_id):
    """测试编辑试剂时更新制造商和单位字段"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 编辑试剂
    edit_data = {
        "manufacturer": "更新后的制造商",
        "unit": "g"
    }
    
    edit_response = requests.put(
        f"{BASE_URL}/api/reagents/{reagent_id}",
        json=edit_data,
        headers=headers
    )
    
    if edit_response.status_code == 200:
        print("✓ 编辑试剂成功")
        updated_reagent = edit_response.json()
        
        print(f"  更新后制造商: {updated_reagent.get('manufacturer', 'N/A')}")
        print(f"  更新后单位: {updated_reagent.get('unit', 'N/A')}")
        
        # 验证编辑是否成功
        if updated_reagent.get('manufacturer') == edit_data['manufacturer']:
            print("✓ 制造商字段编辑正确")
        else:
            print("✗ 制造商字段编辑失败")
            
        if updated_reagent.get('unit') == edit_data['unit']:
            print("✓ 单位字段编辑正确")
        else:
            print("✗ 单位字段编辑失败")
            
        return True
    else:
        print(f"❌ 编辑试剂失败: {edit_response.status_code}")
        print(f"   响应: {edit_response.text}")
        return False

def cleanup_test_reagent(token, reagent_id):
    """清理测试数据"""
    if reagent_id:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
        if response.status_code == 200:
            print("✅ 清理测试数据成功")
        else:
            print(f"⚠️ 清理测试数据失败: {response.status_code}")

def main():
    print("🧪 开始测试制造商和单位字段功能...")
    print("=" * 50)
    
    # 登录
    token = login()
    if not token:
        sys.exit(1)
    
    # 测试添加试剂
    print("\n📝 测试添加试剂（包含新字段）...")
    reagent_id = test_add_reagent_with_new_fields(token)
    
    if reagent_id:
        # 测试编辑试剂
        print("\n✏️ 测试编辑试剂（更新新字段）...")
        edit_success = test_edit_reagent_with_new_fields(token, reagent_id)
        
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        cleanup_test_reagent(token, reagent_id)
        
        if edit_success:
            print("\n🎉 所有测试通过！制造商和单位字段功能正常。")
        else:
            print("\n❌ 编辑测试失败")
            sys.exit(1)
    else:
        print("\n❌ 添加测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()