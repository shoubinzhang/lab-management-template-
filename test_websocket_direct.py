#!/usr/bin/env python3
"""
直接测试WebSocket连接，不依赖前端
"""
import asyncio
import websockets
import json
import sys
import os

async def test_websocket_direct():
    """直接测试WebSocket连接"""
    print("🔍 直接测试WebSocket连接...")
    
    websocket_url = "ws://localhost:8000/api/ws/notifications"
    print(f"🔌 连接到: {websocket_url}")
    
    try:
        # 设置连接超时
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket连接建立成功")
            
            # 发送认证消息
            auth_message = {
                "type": "auth",
                "token": "invalid_test_token"  # 故意使用无效token来测试错误处理
            }
            
            print("📤 发送认证消息...")
            await websocket.send(json.dumps(auth_message))
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                print(f"📨 收到响应: {response_data}")
                
                if response_data.get("type") == "error":
                    print(f"✅ 服务器正确返回错误: {response_data.get('message')}")
                    print("✅ WebSocket服务器工作正常")
                    return True
                elif response_data.get("type") == "connected":
                    print("✅ 意外的认证成功")
                    return True
                else:
                    print(f"❓ 收到未知响应: {response_data}")
                    return True
                    
            except asyncio.TimeoutError:
                print("⏰ 等待响应超时")
                return False
                
    except ConnectionRefusedError as e:
        print(f"❌ WebSocket连接被拒绝: {e}")
        return False
    except ValueError as e:
        print(f"❌ WebSocket URL无效: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("WebSocket 直接连接测试")
    print("=" * 60)
    
    success = await test_websocket_direct()
    
    print("=" * 60)
    if success:
        print("✅ WebSocket连接测试成功")
        print("🔧 WebSocket服务器正常工作，问题可能在前端配置")
        sys.exit(0)
    else:
        print("❌ WebSocket连接测试失败")
        print("🔧 需要检查后端WebSocket服务器配置")
        sys.exit(1)

if __name__ == "__main__":
    # 清除可能的代理设置
    for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        if proxy_var in os.environ:
            del os.environ[proxy_var]
    
    asyncio.run(main())