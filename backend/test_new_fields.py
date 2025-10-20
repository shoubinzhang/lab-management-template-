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

def test_manufacturer_and_unit_fields():
    """测试制造商和单位字段"""
    token = login()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试添加试剂
    print("=== 测试添加试剂 ===")
    reagent_data = {
        "name": "测试试剂-新字段",
        "category": "有机试剂",
        "manufacturer": "测试制造商公司",
        "lot_number": "LOT456",
        "quantity": 50.0,
        "unit": "g",
        "location": "B2-03",
        "safety_notes": "小心操作"
    }
    
    response = requests.post("http://localhost:8000/api/reagents", json=reagent_data, headers=headers)
    
    if response.status_code == 200:
        reagent = response.json()
        print(f"✓ 试剂创建成功")
        print(f"  ID: {reagent['id']}")
        print(f"  制造商: {reagent.get('manufacturer', 'N/A')}")
        print(f"  单位: {reagent.get('unit', 'N/A')}")
        
        # 验证字段值
        if reagent.get('manufacturer') == "测试制造商公司":
            print("✓ 制造商字段正确保存")
        else:
            print(f"✗ 制造商字段错误: 期望 '测试制造商公司', 实际 '{reagent.get('manufacturer')}'")
            return False
            
        if reagent.get('unit') == "g":
            print("✓ 单位字段正确保存")
        else:
            print(f"✗ 单位字段错误: 期望 'g', 实际 '{reagent.get('unit')}'")
            return False
        
        reagent_id = reagent['id']
        
        # 测试获取试剂
        print("\n=== 测试获取试剂 ===")
        response = requests.get(f"http://localhost:8000/api/reagents/{reagent_id}", headers=headers)
        
        if response.status_code == 200:
            reagent = response.json()
            print(f"✓ 试剂获取成功")
            print(f"  制造商: {reagent.get('manufacturer', 'N/A')}")
            print(f"  单位: {reagent.get('unit', 'N/A')}")
            
            if reagent.get('manufacturer') == "测试制造商公司" and reagent.get('unit') == "g":
                print("✓ 制造商和单位字段在获取时正确显示")
            else:
                print("✗ 制造商或单位字段在获取时不正确")
                return False
        else:
            print(f"✗ 获取试剂失败: {response.status_code}")
            return False
        
        # 测试更新试剂
        print("\n=== 测试更新试剂 ===")
        update_data = {
            "manufacturer": "更新后的制造商",
            "unit": "ml"
        }
        
        response = requests.put(f"http://localhost:8000/api/reagents/{reagent_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            print("✓ 试剂更新成功")
            
            # 再次获取验证更新
            response = requests.get(f"http://localhost:8000/api/reagents/{reagent_id}", headers=headers)
            if response.status_code == 200:
                reagent = response.json()
                print(f"  更新后制造商: {reagent.get('manufacturer', 'N/A')}")
                print(f"  更新后单位: {reagent.get('unit', 'N/A')}")
                
                if reagent.get('manufacturer') == "更新后的制造商" and reagent.get('unit') == "ml":
                    print("✓ 制造商和单位字段更新成功")
                else:
                    print("✗ 制造商或单位字段更新失败")
                    return False
            else:
                print(f"✗ 更新后获取试剂失败: {response.status_code}")
                return False
        else:
            print(f"✗ 更新试剂失败: {response.status_code}")
            return False
        
        print("\n=== 所有测试通过! ===")
        return True
        
    else:
        print(f"✗ 创建试剂失败: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_manufacturer_and_unit_fields()
    if success:
        print("\n🎉 制造商和单位字段功能测试成功!")
    else:
        print("\n❌ 制造商和单位字段功能测试失败!")
        exit(1)