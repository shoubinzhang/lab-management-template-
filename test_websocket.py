import asyncio
import websockets
import json
import urllib.request
import urllib.parse

async def test_websocket():
    # 首先登录获取token
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    data = urllib.parse.urlencode(login_data).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=data)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                response_data = json.loads(response.read().decode('utf-8'))
                token = response_data.get('access_token')
                print(f"登录成功，获取到token: {token[:20]}...")
            else:
                print(f"登录失败: {response.status}")
                return
    except Exception as e:
        print(f"登录请求失败: {e}")
        return
    
    # 测试正确的WebSocket URL
    ws_url = "ws://127.0.0.1:8000/api/ws/notifications"
    print(f"连接WebSocket: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("WebSocket连接成功")
            
            # 发送认证消息
            auth_message = {
                "type": "auth",
                "token": token
            }
            await websocket.send(json.dumps(auth_message))
            print("已发送认证消息")
            
            # 等待响应
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"收到响应: {response_data}")
            
            if response_data.get('type') == 'connected':
                print("WebSocket认证成功！")
            else:
                print(f"认证失败: {response_data}")
                
    except Exception as e:
        print(f"WebSocket连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())