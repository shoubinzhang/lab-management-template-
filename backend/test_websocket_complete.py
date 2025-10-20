import asyncio
import websockets
import json
import requests

async def test_websocket_complete():
    """完整的WebSocket连接测试，包含认证流程"""
    
    # 1. 获取认证token
    print("1. 获取认证token...")
    try:
        login_response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'username': 'admin', 'password': 'admin123'}
        )
        
        if login_response.status_code != 200:
            print(f"✗ 登录失败: {login_response.status_code} - {login_response.text}")
            return False
        
        token = login_response.json()['access_token']
        print(f"✓ 获取token成功")
        
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")
        return False
    
    # 2. 建立WebSocket连接并认证
    print("\n2. 建立WebSocket连接...")
    try:
        uri = 'ws://localhost:8000/api/ws/notifications'
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 3. 发送认证消息
            print("\n3. 发送认证消息...")
            auth_msg = {
                'type': 'auth', 
                'token': token
            }
            await websocket.send(json.dumps(auth_msg))
            print("✓ 认证消息已发送")
            
            # 4. 等待认证响应
            print("\n4. 等待认证响应...")
            try:
                auth_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                auth_data = json.loads(auth_response)
                print(f"✓ 认证响应: {auth_data}")
                
                if auth_data.get('type') == 'connected':
                    print("✓ 认证成功，连接已建立")
                    connection_id = auth_data.get('connection_id')
                    print(f"✓ 连接ID: {connection_id}")
                    
                    # 5. 发送心跳测试
                    print("\n5. 发送心跳测试...")
                    ping_msg = {'type': 'ping'}
                    await websocket.send(json.dumps(ping_msg))
                    
                    # 等待pong响应
                    pong_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    pong_data = json.loads(pong_response)
                    print(f"✓ 心跳响应: {pong_data}")
                    
                    # 6. 监听通知消息
                    print("\n6. 监听通知消息（5秒）...")
                    try:
                        while True:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5)
                            data = json.loads(message)
                            print(f"📨 收到消息: {data}")
                    except asyncio.TimeoutError:
                        print("⏰ 5秒内未收到新消息")
                    
                    print("\n✅ WebSocket测试完全成功！")
                    return True
                    
                elif auth_data.get('type') == 'error':
                    print(f"✗ 认证失败: {auth_data.get('message')}")
                    return False
                else:
                    print(f"✗ 未知认证响应: {auth_data}")
                    return False
                    
            except asyncio.TimeoutError:
                print("✗ 认证响应超时")
                return False
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"✗ WebSocket连接被关闭: {e}")
        return False
    except Exception as e:
        print(f"✗ WebSocket连接失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_complete())
    if result:
        print("\n🎉 所有测试通过！WebSocket连接和通知系统工作正常。")
    else:
        print("\n❌ 测试失败，WebSocket连接存在问题。")