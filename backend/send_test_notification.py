import requests
import json

def send_test_notification():
    try:
        # 1. 获取认证token
        print("获取认证token...")
        login_response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'username': 'admin', 'password': 'admin123'}
        )
        
        if login_response.status_code != 200:
            print(f"✗ 登录失败: {login_response.status_code}")
            return
        
        token = login_response.json()['access_token']
        print(f"✓ 获取token成功")
        
        # 2. 发送测试通知
        print("\n发送测试通知...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        notification_data = {
            'title': '测试通知',
            'message': '这是一个测试通知，用于验证实时通知系统是否正常工作',
            'type': 'info',
            'user_id': 1  # 发送给admin用户
        }
        
        # 尝试通过API创建通知
        response = requests.post(
            'http://localhost:8000/api/notifications',
            json=notification_data,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ 测试通知发送成功: {response.json()}")
            print("\n请检查前端应用是否收到实时通知！")
        else:
            print(f"✗ 发送通知失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"✗ 发送通知时出错: {e}")

if __name__ == "__main__":
    send_test_notification()