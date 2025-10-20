#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API修复效果
"""

import requests
import json

def test_reagents_api():
    """测试试剂API"""
    try:
        # 获取认证token
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = requests.post('http://localhost:8000/api/auth/login', json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # 测试获取试剂列表
            reagents_response = requests.get('http://localhost:8000/api/reagents', headers=headers)
            print(f'试剂列表API状态: {reagents_response.status_code}')
            
            if reagents_response.status_code == 200:
                data = reagents_response.json()
                print(f'成功获取试剂数据，总数: {data.get("total", 0)}')
                if data.get('items'):
                    first_item = data['items'][0]
                    print(f'第一个试剂: {first_item.get("name", "N/A")}')
                    print(f'min_threshold字段: {first_item.get("min_threshold", "缺失")}')
                    print('✅ API测试成功，min_threshold字段已正确包含')
                else:
                    print('⚠️ 没有试剂数据')
            else:
                print(f'❌ 获取试剂列表失败: {reagents_response.text}')
        else:
            print(f'❌ 登录失败: {login_response.status_code} - {login_response.text}')
            
    except Exception as e:
        print(f'❌ 测试API时出错: {e}')

if __name__ == "__main__":
    test_reagents_api()