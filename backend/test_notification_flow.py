import asyncio
import websockets
import json
import requests
import time

async def test_notification_flow():
    # 1. 获取有效token
    print("1. 获取认证token...")
    login_response = requests.post(
        'http://localhost:8000/api/auth/login',
        json={'username': 'admin', 'password': 'admin123'}
    )
    
    if login_response.status_code != 200:
        print(f"✗ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    print(f"✓ 获取token成功: {token[:50]}...")
    
    # 2. 建立WebSocket连接
    print("\n2. 建立WebSocket连接...")
    try:
        uri = 'ws://localhost:8000/api/ws/notifications'
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 3. 发送认证消息
            print("\n3. 发送认证消息...")
            auth_msg = {'type': 'auth', 'token': token}
            await websocket.send(json.dumps(auth_msg))
            
            # 等待认证响应
            auth_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            auth_data = json.loads(auth_response)
            print(f"✓ 认证响应: {auth_data}")
            
            if auth_data.get('type') != 'connected':
                print("✗ 认证失败")
                return
            
            # 4. 监听通知消息
            print("\n4. 监听通知消息（等待10秒）...")
            
            # 创建一个任务来监听消息
            async def listen_for_messages():
                try:
                    while True:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                        data = json.loads(message)
                        print(f"📨 收到通知: {data}")
                except asyncio.TimeoutError:
                    pass
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket连接已关闭")
            
            # 监听10秒钟
            await asyncio.wait_for(listen_for_messages(), timeout=10)
            
            print("\n✓ 通知流程测试完成")
            
    except Exception as e:
        print(f"✗ WebSocket测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_notification_flow())