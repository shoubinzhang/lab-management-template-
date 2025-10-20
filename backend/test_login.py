import requests
import json

# 测试登录API
print('测试登录API...')
try:
    response = requests.post('http://localhost:8000/api/auth/login', 
                           json={'username': 'admin', 'password': 'admin123'})
    print(f'登录响应状态码: {response.status_code}')
    if response.ok:
        data = response.json()
        print(f'登录成功, token: {data.get("access_token", "无")[:20]}...')
        
        # 测试跳转到移动端主页
        print('\n测试移动端主页访问...')
        dashboard_response = requests.get('http://localhost:8000/mobile_dashboard.html')
        print(f'移动端主页状态码: {dashboard_response.status_code}')
        if dashboard_response.status_code == 200:
            print('移动端主页可正常访问')
        else:
            print(f'移动端主页访问失败: {dashboard_response.text[:100]}')
    else:
        print(f'登录失败: {response.text}')
except Exception as e:
    print(f'错误: {e}')