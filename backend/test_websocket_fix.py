#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试WebSocket连接修复效果
"""

import asyncio
import websockets
import json
import requests

async def test_websocket_connection():
    """测试WebSocket连接"""
    try:
        # 1. 获取认证token
        print("1. 获取认证token...")
        login_response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'username': 'admin', 'password': 'admin123'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return
        
        token = login_response.json()['access_token']
        print(f"✅ 获取token成功")
        
        # 2. 建立WebSocket连接
        print("\n2. 建立WebSocket连接...")
        uri = 'ws://localhost:8000/api/ws/notifications'
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 3. 发送认证消息
            print("\n3. 发送认证消息...")
            auth_msg = {'type': 'auth', 'token': token}
            await websocket.send(json.dumps(auth_msg))
            
            # 等待认证响应
            auth_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            auth_data = json.loads(auth_response)
            print(f"✅ 认证响应: {auth_data.get('type', 'unknown')}")
            
            if auth_data.get('type') == 'connected':
                print("✅ WebSocket认证成功，连接建立")
                print("✅ 所有测试通过，WebSocket问题已修复")
            else:
                print(f"❌ 认证失败: {auth_data}")
                
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())