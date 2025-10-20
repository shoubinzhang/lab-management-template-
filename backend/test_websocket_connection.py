import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = 'ws://localhost:8000/api/ws/notifications'
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket successfully")
            
            # Send authentication message with valid token
            auth_msg = {
                'type': 'auth',
                'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NzY0ODQ5MH0.p92L6atMc2WeovTJujOVU6bE_WPaPR3cB6NvJ1tKhoc'
            }
            await websocket.send(json.dumps(auth_msg))
            print("✓ Auth message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✓ Response received: {response}")
            except asyncio.TimeoutError:
                print("⚠ No response received within 5 seconds")
                
    except websockets.exceptions.ConnectionRefused:
        print("✗ Connection refused - WebSocket server may not be running")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())