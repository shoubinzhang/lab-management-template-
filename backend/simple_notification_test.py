import asyncio
import websockets
import json

async def test_simple_notification():
    try:
        # 使用之前获取的有效token
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NzY0ODQ5MH0.p92L6atMc2WeovTJujOVU6bE_WPaPR3cB6NvJ1tKhoc'
        
        print("连接到WebSocket...")
        uri = 'ws://localhost:8000/api/ws/notifications'
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 发送认证消息
            auth_msg = {'type': 'auth', 'token': token}
            await websocket.send(json.dumps(auth_msg))
            print("✓ 认证消息已发送")
            
            # 等待认证响应
            auth_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            auth_data = json.loads(auth_response)
            print(f"✓ 认证响应: {auth_data}")
            
            if auth_data.get('type') == 'connected':
                print("✓ 认证成功，连接已建立")
                
                # 监听通知消息5秒钟
                print("\n监听通知消息（5秒）...")
                try:
                    while True:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        print(f"📨 收到通知: {data}")
                except asyncio.TimeoutError:
                    print("⏰ 5秒内未收到新通知")
                
                print("\n✅ 通知系统测试完成 - WebSocket连接和认证正常工作")
            else:
                print(f"✗ 认证失败: {auth_data}")
                
    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_notification())