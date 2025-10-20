import requests
import json

def test_reagents_api():
    try:
        # 先登录获取token
        login_data = {'username': 'admin', 'password': 'admin123'}
        login_response = requests.post('http://localhost:8000/api/auth/login', json=login_data)
        print(f'登录状态码: {login_response.status_code}')

        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # 请求试剂数据
            reagents_response = requests.get('http://localhost:8000/api/reagents/', headers=headers)
            print(f'试剂API状态码: {reagents_response.status_code}')
            print(f'响应头Content-Type: {reagents_response.headers.get("Content-Type")}')
            
            if reagents_response.status_code == 200:
                data = reagents_response.json()
                print(f'试剂数据类型: {type(data)}')
                print(f'试剂数量: {len(data) if isinstance(data, list) else "不是列表"}')
                if isinstance(data, list) and len(data) > 0:
                    print(f'第一个试剂名称: {data[0].get("name", "未知")}')
                    print(f'第一个试剂ID: {data[0].get("id", "未知")}')
                else:
                    print('试剂数据为空或格式错误')
                    print(f'实际数据: {data}')
            else:
                print(f'试剂API错误: {reagents_response.text}')
        else:
            print(f'登录失败: {login_response.text}')
    except Exception as e:
        print(f'测试过程中出现错误: {e}')

if __name__ == "__main__":
    test_reagents_api()