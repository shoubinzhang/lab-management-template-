import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 简单测试脚本，绕过Redis缓存测试耗材API
def main():
    print("🚀 开始简单耗材API测试")
    print("==================================================")
    
    # 1. 测试登录
    print("=== 测试登录功能 ===")
    login_data = {
        "username": "test_user",
        "password": "test_password"
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
    
    # 2. 测试直接获取耗材列表（不使用缓存API）
    print("\n=== 测试直接获取耗材列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 尝试直接的耗材API，而不是缓存版本
        response = requests.get(
            f"{BASE_URL}/api/consumables",  # 尝试直接API路径
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            consumables = response.json()
            print(f"✅ 获取成功，共找到 {len(consumables)} 个耗材")
            if consumables:
                print(f"   第一个耗材: {consumables[0].get('name', 'N/A')}")
                return consumables[0].get('id')
            else:
                print("⚠️ 耗材列表为空")
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
    
    return None

if __name__ == "__main__":
    main()