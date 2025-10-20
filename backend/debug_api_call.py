import requests
import json

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_create_reagent():
    """测试创建试剂"""
    token = login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建包含manufacturer和unit字段的试剂数据
    reagent_data = {
        "name": "测试试剂-调试",
        "category": "有机试剂",
        "manufacturer": "测试制造商",
        "lot_number": "LOT123",
        "quantity": 100.0,
        "unit": "ml",
        "location": "A1-01",
        "safety_notes": "注意安全"
    }
    
    print("发送的试剂数据:")
    print(json.dumps(reagent_data, indent=2, ensure_ascii=False))
    
    response = requests.post("http://localhost:8000/api/reagents", json=reagent_data, headers=headers)
    
    print(f"\n响应状态码: {response.status_code}")
    print("响应数据:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        reagent = response.json()
        print(f"\n试剂ID: {reagent.get('id', 'N/A')}")
        print(f"制造商: {reagent.get('manufacturer', 'N/A')}")
        print(f"单位: {reagent.get('unit', 'N/A')}")
    else:
        print(f"创建失败: {response.text}")

if __name__ == "__main__":
    test_create_reagent()