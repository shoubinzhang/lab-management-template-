import requests
import json

# API配置
API_BASE_URL = "http://127.0.0.1:8000"

def test_reagents_api():
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录
        print("正在登录...")
        login_response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
        print(f"登录响应状态: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            print(f"登录成功，获取到token: {token[:20]}...")
            
            # 2. 使用token获取试剂数据
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print("\n正在获取试剂数据...")
            reagents_response = requests.get(
                f"{API_BASE_URL}/api/reagents/?page=1&size=50&search=&category=&status=",
                headers=headers
            )
            print(f"试剂API响应状态: {reagents_response.status_code}")
            
            if reagents_response.status_code == 200:
                reagents_data = reagents_response.json()
                print(f"\n试剂数据结构:")
                print(f"- 总数: {reagents_data.get('total', 'N/A')}")
                print(f"- 页数: {reagents_data.get('pages', 'N/A')}")
                print(f"- 当前页: {reagents_data.get('page', 'N/A')}")
                print(f"- 每页大小: {reagents_data.get('size', 'N/A')}")
                
                items = reagents_data.get('items', [])
                print(f"- 试剂条目数: {len(items)}")
                
                if items:
                    print("\n前3条试剂数据:")
                    for i, item in enumerate(items[:3]):
                        print(f"  {i+1}. {item.get('name', 'N/A')} - {item.get('category', 'N/A')} - {item.get('quantity', 'N/A')} {item.get('unit', 'N/A')}")
                else:
                    print("\n⚠️  试剂列表为空！")
                    
                # 打印完整响应以便调试
                print("\n完整API响应:")
                print(json.dumps(reagents_data, indent=2, ensure_ascii=False))
            else:
                print(f"获取试剂数据失败: {reagents_response.text}")
        else:
            print(f"登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_reagents_api()