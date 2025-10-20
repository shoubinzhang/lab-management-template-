#!/usr/bin/env python3
"""
简单的WebSocket连接测试
"""
import asyncio
import websockets
import json
import requests
import sys

async def test_websocket():
    """测试WebSocket连接"""
    print("🔍 开始WebSocket连接测试...")
    
    # 首先测试后端API连接
    try:
        print("📡 测试后端API连接...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端API连接正常")
        else:
            print(f"❌ 后端API连接失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端API连接失败: {e}")
        return False
    
    # 测试WebSocket连接
    websocket_url = "ws://localhost:8000/api/ws/notifications"
    print(f"🔌 尝试连接WebSocket: {websocket_url}")
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket连接建立成功")
            
            # 发送认证消息（使用测试token）
            auth_message = {
                "type": "auth",
                "token": "test_token_123"  # 测试用token
            }
            
            print("📤 发送认证消息...")
            await websocket.send(json.dumps(auth_message))
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"📨 收到响应: {response_data}")
                
                if response_data.get("type") == "error":
                    print(f"⚠️ 认证失败（预期的）: {response_data.get('message')}")
                    print("✅ WebSocket服务器正常响应错误消息")
                    return True
                elif response_data.get("type") == "connected":
                    print("✅ 认证成功，WebSocket连接完全正常")
                    return True
                else:
                    print(f"❓ 收到未知响应类型: {response_data}")
                    return True
                    
            except asyncio.TimeoutError:
                print("⏰ 等待响应超时")
                return False
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ WebSocket连接被拒绝 - 服务器可能未启动")
        return False
    except websockets.exceptions.InvalidURI:
        print("❌ WebSocket URL无效")
        return False
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 50)
    print("WebSocket 连接诊断工具")
    print("=" * 50)
    
    success = await test_websocket()
    
    print("=" * 50)
    if success:
        print("✅ WebSocket测试完成 - 连接正常")
        sys.exit(0)
    else:
        print("❌ WebSocket测试失败 - 存在连接问题")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())