#!/usr/bin/env python3
"""
前端试剂显示测试脚本
测试添加试剂后前端是否能正常显示
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_frontend_reagent_display():
    print("=== 前端试剂显示测试 ===\n")
    
    try:
        # 1. 登录获取token
        print("1. 登录获取token...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"响应: {response.text}")
            return
            
        token_data = response.json()
        token = token_data.get('access_token')
        print(f"✅ 登录成功，获取到token")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取当前试剂列表（模拟前端API调用）
        print("\n2. 获取当前试剂列表...")
        response = requests.get(f"{BASE_URL}/api/reagents", headers=headers)
        
        if response.status_code == 200:
            reagents_data = response.json()
            print(f"✅ 试剂列表获取成功")
            
            # 处理分页数据
            if isinstance(reagents_data, dict) and 'items' in reagents_data:
                reagents_before = reagents_data['items']
                total_count = reagents_data.get('total', len(reagents_before))
                print(f"当前试剂总数: {total_count}")
            elif isinstance(reagents_data, dict) and 'data' in reagents_data:
                reagents_before = reagents_data['data']
                total_count = reagents_data.get('total', len(reagents_before))
                print(f"当前试剂总数: {total_count}")
            else:
                reagents_before = reagents_data
                total_count = len(reagents_before) if isinstance(reagents_before, list) else 0
                print(f"当前试剂总数: {total_count}")
                
            # 显示最近的几个试剂
            if isinstance(reagents_before, list) and len(reagents_before) > 0:
                print("最近的试剂:")
                for reagent in reagents_before[-3:]:
                    print(f"  - {reagent.get('name')} (ID: {reagent.get('id')}, 库存: {reagent.get('quantity')}, 位置: {reagent.get('location')})")
            else:
                print("没有找到试剂数据")
        else:
            print(f"❌ 获取试剂列表失败: {response.status_code}")
            return
            
        # 3. 添加新试剂
        print("\n3. 添加新试剂...")
        test_reagent = {
            "name": f"测试试剂_{int(time.time())}",
            "category": "测试分类",
            "manufacturer": "测试厂商",
            "lot_number": f"LOT{int(time.time())}",
            "expiry_date": "2025-12-31T00:00:00",
            "quantity": 100.0,
            "unit": "mL",
            "min_threshold": 10.0,
            "location": "测试位置",
            "safety_notes": "测试安全说明",
            "price": 99.99
        }
        
        response = requests.post(f"{BASE_URL}/api/reagents", json=test_reagent, headers=headers)
        print(f"添加试剂状态: {response.status_code}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            print(f"✅ 试剂添加成功! 响应: {response_data}")
            
            # 获取新试剂ID
            if 'reagent_id' in response_data:
                reagent_id = response_data['reagent_id']
            elif 'id' in response_data:
                reagent_id = response_data['id']
            else:
                reagent_id = None
                print("⚠️ 无法获取新试剂的ID")
                
            # 4. 等待一下，然后重新获取试剂列表
            print("\n4. 等待2秒后重新获取试剂列表...")
            time.sleep(2)
            
            response = requests.get(f"{BASE_URL}/api/reagents", headers=headers)
            if response.status_code == 200:
                reagents_data_after = response.json()
                
                # 处理分页数据
                if isinstance(reagents_data_after, dict) and 'items' in reagents_data_after:
                    reagents_after = reagents_data_after['items']
                    total_count_after = reagents_data_after.get('total', len(reagents_after))
                    print(f"✅ 添加后试剂总数: {total_count_after}")
                elif isinstance(reagents_data_after, dict) and 'data' in reagents_data_after:
                    reagents_after = reagents_data_after['data']
                    total_count_after = reagents_data_after.get('total', len(reagents_after))
                    print(f"✅ 添加后试剂总数: {total_count_after}")
                else:
                    reagents_after = reagents_data_after
                    total_count_after = len(reagents_after) if isinstance(reagents_after, list) else 0
                    print(f"✅ 添加后试剂总数: {total_count_after}")
                
                # 检查数量是否增加
                if total_count_after > total_count:
                    print(f"✅ 试剂数量已增加: {total_count} -> {total_count_after}")
                else:
                    print(f"❌ 试剂数量未增加: {total_count} -> {total_count_after}")
                
                # 检查新添加的试剂是否在列表中
                if reagent_id and isinstance(reagents_after, list):
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
                        print(f"  - {reagent.get('name')} (ID: {reagent.get('id')}, 库存: {reagent.get('quantity')}, 位置: {reagent.get('location')})")
                else:
                    print("没有找到试剂数据")
            else:
                print(f"❌ 重新获取试剂列表失败: {response.status_code}")
                
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
                
                if response.status_code in [200, 204]:
                    print("✅ 测试数据清理成功")
                else:
                    print(f"⚠️ 测试数据清理失败: {response.text}")
        else:
            print(f"❌ 试剂添加失败: {response.text}")
            
        # 7. 检查缓存相关信息
        print(f"\n7. 检查缓存相关信息...")
        response = requests.delete(f"{BASE_URL}/api/cache/clear", headers=headers)
        print(f"缓存清理状态: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_frontend_reagent_display()