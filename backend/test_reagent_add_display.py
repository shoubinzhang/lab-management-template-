#!/usr/bin/env python3
"""
试剂添加和显示功能测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_reagent_functionality():
    """测试试剂添加和显示功能"""
    print("=== 试剂添加和显示功能测试 ===")
    
    # 1. 登录获取token
    print("\n1. 登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"登录状态: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"登录成功! Token获取成功")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 获取当前试剂列表
            print("\n2. 获取当前试剂列表...")
            response = requests.get(f"{BASE_URL}/api/reagents", headers=headers)
            print(f"试剂列表API状态: {response.status_code}")
            
            if response.status_code == 200:
                reagents_data = response.json()
                
                # 处理分页数据
                if isinstance(reagents_data, dict) and 'data' in reagents_data:
                    reagents_before = reagents_data['data']
                    total_count = reagents_data.get('total', len(reagents_before))
                    print(f"添加前试剂数量: {total_count}")
                else:
                    reagents_before = reagents_data
                    print(f"添加前试剂数量: {len(reagents_before) if isinstance(reagents_before, list) else 'Unknown'}")
                
                # 显示最近的几个试剂
                print("最近的试剂:")
                if isinstance(reagents_before, list) and len(reagents_before) > 0:
                    for reagent in reagents_before[-3:]:
                        print(f"  - {reagent.get('name')} (库存: {reagent.get('quantity', reagent.get('current_stock'))}, 位置: {reagent.get('location')})")
                else:
                    print(f"试剂数据格式: {type(reagents_before)}")
                    print(f"试剂数据: {reagents_before}")
            else:
                print(f"获取试剂列表失败: {response.text}")
                return
            
            # 3. 测试添加新试剂
            print("\n3. 测试添加新试剂...")
            test_reagent = {
                "name": f"测试试剂_{int(time.time())}",
                "cas_number": f"TEST-{int(time.time())}",
                "molecular_formula": "C6H12O6",
                "molecular_weight": 180.16,
                "purity": 99.5,
                "concentration": "1M",
                "current_stock": 100.0,
                "min_threshold": 10.0,
                "max_threshold": 500.0,
                "unit": "mL",
                "location": "A1-01",
                "supplier": "测试供应商",
                "lot_number": f"LOT{int(time.time())}",
                "expiry_date": "2025-12-31",
                "storage_conditions": "室温保存",
                "safety_notes": "无特殊注意事项"
            }
            
            response = requests.post(f"{BASE_URL}/api/reagents", json=test_reagent, headers=headers)
            print(f"添加试剂状态: {response.status_code}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                print(f"✅ 试剂添加成功! 响应: {response_data}")
                
                # 处理不同的响应格式
                if 'reagent_id' in response_data:
                    reagent_id = response_data['reagent_id']
                elif 'id' in response_data:
                    reagent_id = response_data['id']
                else:
                    reagent_id = None
                    print("⚠️ 无法获取新试剂的ID")
                
                # 4. 立即重新获取试剂列表
                print("\n4. 重新获取试剂列表验证...")
                response = requests.get(f"{BASE_URL}/api/reagents", headers=headers)
                print(f"重新获取试剂列表状态: {response.status_code}")
                
                if response.status_code == 200:
                    reagents_data_after = response.json()
                    
                    # 处理分页数据
                    if isinstance(reagents_data_after, dict) and 'data' in reagents_data_after:
                        reagents_after = reagents_data_after['data']
                        total_count_after = reagents_data_after.get('total', len(reagents_after))
                        print(f"添加后试剂数量: {total_count_after}")
                    else:
                        reagents_after = reagents_data_after
                        print(f"添加后试剂数量: {len(reagents_after) if isinstance(reagents_after, list) else 'Unknown'}")
                    
                    # 检查新添加的试剂是否在列表中
                    if reagent_id:
                        found_new_reagent = False
                        for reagent in reagents_after:
                            if reagent.get('id') == reagent_id:
                                found_new_reagent = True
                                print(f"✅ 新添加的试剂已在列表中找到: {reagent.get('name')}")
                                break
                        
                        if not found_new_reagent:
                            print(f"❌ 新添加的试剂(ID: {reagent_id})未在列表中找到")
                    
                    # 显示最新的几个试剂
                    print("最新的试剂:")
                    if isinstance(reagents_after, list) and len(reagents_after) > 0:
                        for reagent in reagents_after[-3:]:
                            print(f"  - {reagent.get('name')} (库存: {reagent.get('quantity', reagent.get('current_stock'))}, 位置: {reagent.get('location')})")
                    else:
                        print(f"试剂数据格式: {type(reagents_after)}")
                        print(f"试剂数据: {reagents_after}")
                
                # 5. 测试单个试剂获取
                if reagent_id:
                    print(f"\n5. 测试获取单个试剂 (ID: {reagent_id})...")
                    response = requests.get(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
                print(f"单个试剂获取状态: {response.status_code}")
                
                if response.status_code == 200:
                    single_reagent = response.json()
                    print(f"✅ 单个试剂获取成功: {single_reagent.get('name')}")
                else:
                    print(f"❌ 单个试剂获取失败: {response.text}")
                
                # 6. 清理测试数据
                if reagent_id:
                    print(f"\n6. 清理测试数据...")
                    response = requests.delete(f"{BASE_URL}/api/reagents/{reagent_id}", headers=headers)
                    print(f"删除测试试剂状态: {response.status_code}")
                
            else:
                print(f"❌ 试剂添加失败: {response.text}")
            
            # 7. 检查缓存状态
            print("\n7. 检查缓存相关信息...")
            try:
                # 检查是否有缓存清理端点
                response = requests.post(f"{BASE_URL}/api/cache/clear", headers=headers)
                print(f"缓存清理状态: {response.status_code}")
            except:
                print("缓存清理端点不可用")
                
        else:
            print(f"登录失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_reagent_functionality()