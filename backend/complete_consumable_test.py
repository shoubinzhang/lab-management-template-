import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 完整测试脚本，直接使用管理员用户测试登录和获取耗材列表
def main():
    print("🚀 开始完整耗材API测试")
    print("==================================================")
    
    # 测试登录 - 使用管理员用户
    print("=== 测试登录功能 ===")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            print(f"✅ 登录成功，获取到令牌: {token[:20]}...")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求异常: {str(e)}")
        return
    
    # 3. 测试获取耗材列表
    print("\n=== 测试获取耗材列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 尝试不同的API路径
    api_paths = [
        "/api/consumables",
        "/consumables",
        "/cached_consumables"
    ]
    
    for path in api_paths:
        try:
            print(f"\n尝试API路径: {path}")
            response = requests.get(
                f"{BASE_URL}{path}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # 检查是否是分页格式
                    if isinstance(response_data, dict) and 'items' in response_data:
                        consumables = response_data['items']
                        total_count = response_data.get('total', 0)
                        print(f"✅ 获取成功，共找到 {total_count} 个耗材（当前页 {len(consumables)} 个）")
                    else:
                        consumables = response_data
                        print(f"✅ 获取成功，共找到 {len(consumables)} 个耗材")
                    
                    if consumables and isinstance(consumables, list) and len(consumables) > 0:
                        # 打印第一个耗材的详细信息
                        first_consumable = consumables[0]
                        print(f"   第一个耗材: {first_consumable.get('name', 'N/A')}")
                        print(f"   库存/数量: {first_consumable.get('quantity', first_consumable.get('stock', 'N/A'))}")
                        print(f"   ID: {first_consumable.get('id', 'N/A')}")
                        
                        # 测试提交申请
                        print("\n=== 测试提交耗材申请 ===")
                        consumable_id = first_consumable.get('id')
                        if consumable_id:
                            test_submit_request(headers, consumable_id)
                        
                        # 测试成功
                        return consumable_id
                    else:
                        print("⚠️ 耗材列表为空或格式不正确")
                        print(f"   响应数据: {response_data}")
                except json.JSONDecodeError:
                    print(f"⚠️ 响应不是有效的JSON格式: {response.text}")
                except Exception as e:
                    print(f"⚠️ 处理响应时发生错误: {str(e)}")
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
    
    return None

# 测试提交耗材申请
def test_submit_request(headers, consumable_id):
    try:
        request_data = {
            "quantity": 1,
            "purpose": "测试申请",
            "notes": "这是一个测试申请",
            "unit": "个"  # 添加必需的unit字段
        }
        
        # 尝试不同的申请API路径
        request_api_paths = [
            f"/api/consumables/{consumable_id}/request",
            f"/consumables/{consumable_id}/request",
            "/api/consumables/request"
        ]
        
        for path in request_api_paths:
            print(f"\n尝试申请API路径: {path}")
            
            # 根据路径调整请求数据
            if path == "/api/consumables/request":
                # 需要在body中包含consumable_id
                full_request_data = request_data.copy()
                full_request_data["consumable_id"] = consumable_id
            else:
                full_request_data = request_data
            
            try:
                response = requests.post(
                    f"{BASE_URL}{path}",
                    headers=headers,
                    json=full_request_data,
                    timeout=10
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    print(f"✅ 申请提交成功: {result}")
                    return True
                else:
                    print(f"❌ 申请提交失败: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ 申请请求异常: {str(e)}")
    except Exception as e:
        print(f"❌ 提交申请过程中发生错误: {str(e)}")
    
    return False

if __name__ == "__main__":
    main()