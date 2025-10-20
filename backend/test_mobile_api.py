import requests
import json

# 测试登录并获取token
def test_login():
    url = "http://localhost:8000/api/auth/login"
    credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=credentials)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"登录失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

# 测试用户信息API
def test_user_info(token):
    if not token:
        print("没有有效的token，无法测试用户信息API")
        return
        
    url = "http://localhost:8000/api/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n用户信息API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"用户信息API响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"用户信息API失败，响应: {response.text}")
    except Exception as e:
        print(f"用户信息API请求异常: {e}")

# 测试仪表板统计API
def test_dashboard_stats(token):
    if not token:
        print("没有有效的token，无法测试仪表板统计API")
        return
        
    url = "http://localhost:8000/api/dashboard/quick-stats"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n仪表板统计API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"仪表板统计API响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"仪表板统计API失败，响应: {response.text}")
    except Exception as e:
        print(f"仪表板统计API请求异常: {e}")

# 测试设备列表API
def test_devices_api(token):
    if not token:
        print("没有有效的token，无法测试设备列表API")
        return
        
    url = "http://localhost:8000/api/devices"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n设备列表API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"设备列表API响应类型: {type(data)}")
            if isinstance(data, dict) and "items" in data:
                print(f"设备总数: {len(data['items'])}")
            else:
                print(f"设备数量: {len(data)}")
        else:
            print(f"设备列表API失败，响应: {response.text}")
    except Exception as e:
        print(f"设备列表API请求异常: {e}")

# 主测试函数
def main():
    print("开始测试移动应用API...")
    
    # 1. 获取登录token
    token = test_login()
    if token:
        print(f"登录成功，获取到token")
        
        # 2. 测试各个API端点
        test_user_info(token)
        test_dashboard_stats(token)
        test_devices_api(token)
    else:
        print("登录失败，无法继续测试")

if __name__ == "__main__":
    main()