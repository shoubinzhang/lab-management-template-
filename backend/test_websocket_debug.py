#!/usr/bin/env python3
"""
WebSocket 连接调试脚本
用于测试 WebSocket 连接和认证流程
"""

import asyncio
import websockets
import json
import requests
import sys

async def test_websocket_connection():
    """测试 WebSocket 连接"""
    
    # 首先获取认证 token
    print("1. 获取认证 token...")
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code != 200:
            print(f"登录失败: {response.status_code} - {response.text}")
            return
        
        token_data = response.json()
        token = token_data.get("access_token")
        if not token:
            print("未获取到 token")
            return
        
        print(f"✓ 获取到 token: {token[:20]}...")
        
    except Exception as e:
        print(f"登录请求失败: {e}")
        return
    
    # 测试 WebSocket 连接
    print("\n2. 测试 WebSocket 连接...")
    uri = "ws://localhost:8000/api/ws/notifications"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket 连接建立成功")
            
            # 发送认证消息
            print("3. 发送认证消息...")
            auth_message = {
                "type": "auth",
                "token": token
            }
            
            await websocket.send(json.dumps(auth_message))
            print("✓ 认证消息已发送")
            
            # 等待响应
            print("4. 等待服务器响应...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"✓ 收到响应: {response_data}")
                
                if response_data.get("type") == "connected":
                    print("✓ WebSocket 认证成功！")
                    
                    # 保持连接一段时间
                    print("5. 保持连接 10 秒...")
                    await asyncio.sleep(10)
                    
                elif response_data.get("type") == "error":
                    print(f"✗ 认证失败: {response_data.get('message')}")
                
            except asyncio.TimeoutError:
                print("✗ 等待响应超时")
            except json.JSONDecodeError as e:
                print(f"✗ 解析响应失败: {e}")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"✗ WebSocket 连接被关闭: {e}")
    except Exception as e:
        print(f"✗ WebSocket 连接失败: {e}")

if __name__ == "__main__":
    print("WebSocket 连接调试测试")
    print("=" * 40)
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)