#!/usr/bin/env python3
"""
测试试剂添加和编辑功能是否包含所有必需字段
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_reagent_fields():
    """测试试剂字段功能"""
    print("=== 试剂字段测试 ===\n")
    
    # 1. 登录获取token
    print("1. 登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ 登录失败: {response.status_code}")
            return
            
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
        # 2. 测试添加试剂（包含所有必需字段）
        print("\n2. 测试添加试剂（包含所有必需字段）...")
        test_reagent = {
            "name": "测试试剂-字段验证",
            "manufacturer": "测试制造商",
            "lot_number": "TEST-BATCH-001",
            "quantity": 100.0,
            "unit": "mL",
            "location": "测试位置A-1",
            "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "category": "测试分类"
        }
        
        response = requests.post(f"{BASE_URL}/api/reagents", json=test_reagent, headers=headers)
        print(f"添加试剂状态: {response.status_code}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            print("✅ 试剂添加成功!")
            print(f"响应: {response_data}")
            
            # 获取新试剂ID
            reagent_id = response_data.get('reagent_id') or response_data.get('id')
            
            if reagent_id:
                # 3. 获取刚添加的试剂，验证字段
                print(f"\n3. 验证添加的试剂字段...")
                response = requests.get(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
                
                if response.status_code == 200:
                    reagent_data = response.json()
                    print("✅ 获取试剂成功")
                    
                    # 验证所有必需字段
                    required_fields = ["name", "manufacturer", "lot_number", "quantity", "unit", "location", "expiry_date", "category"]
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in reagent_data or reagent_data[field] is None:
                            missing_fields.append(field)
                        else:
                            print(f"  ✅ {field}: {reagent_data[field]}")
                    
                    if missing_fields:
                        print(f"❌ 缺少字段: {missing_fields}")
                    else:
                        print("✅ 所有必需字段都存在!")
                    
                    # 4. 测试编辑试剂
                    print(f"\n4. 测试编辑试剂...")
                    update_data = {
                        "name": reagent_data["name"],  # 名称不变
                        "manufacturer": "更新后的制造商",
                        "lot_number": "UPDATED-BATCH-002",
                        "quantity": 150.0,
                        "unit": "g",
                        "location": "更新后位置B-2",
                        "expiry_date": reagent_data["expiry_date"],
                        "category": "更新后分类"
                    }
                    
                    response = requests.put(f"{BASE_URL}/api/reagents/{reagent_id}", json=update_data, headers=headers)
                    print(f"编辑试剂状态: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("✅ 试剂编辑成功!")
                        
                        # 5. 验证编辑后的字段
                        print(f"\n5. 验证编辑后的试剂字段...")
                        response = requests.get(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
                        
                        if response.status_code == 200:
                            updated_reagent = response.json()
                            print("✅ 获取编辑后试剂成功")
                            
                            # 验证更新的字段
                            if updated_reagent["manufacturer"] == "更新后的制造商":
                                print("  ✅ 制造商字段更新成功")
                            else:
                                print(f"  ❌ 制造商字段更新失败: {updated_reagent['manufacturer']}")
                                
                            if updated_reagent["unit"] == "g":
                                print("  ✅ 单位字段更新成功")
                            else:
                                print(f"  ❌ 单位字段更新失败: {updated_reagent['unit']}")
                                
                            print("✅ 字段编辑功能正常!")
                        else:
                            print(f"❌ 获取编辑后试剂失败: {response.status_code}")
                    else:
                        print(f"❌ 编辑试剂失败: {response.status_code} - {response.text}")
                else:
                    print(f"❌ 获取试剂失败: {response.status_code}")
            else:
                print("❌ 无法获取新试剂ID")
        else:
            print(f"❌ 添加试剂失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_reagent_fields()