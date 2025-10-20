#!/usr/bin/env python3
"""
移动端登录测试脚本
用于验证移动端登录功能是否正常工作
"""

import requests
import json
import time
import sys
import os
import argparse
from urllib.parse import urljoin

# 添加项目根目录到Python路径，以便导入backend.config
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入配置，如果导入失败则使用默认配置
try:
    from backend.config import CORS_ORIGINS
    from backend.app import app as fastapi_app
    CONFIG_AVAILABLE = True
except ImportError:
    print("警告: 无法导入backend.config, 将使用默认配置")
    CONFIG_AVAILABLE = False
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# 获取主机IP（从环境变量或当前主机获取）
def get_host_ip():
    """获取主机IP地址"""
    # 优先从环境变量获取
    if os.getenv("LAB_HOST_IP"):
        return os.getenv("LAB_HOST_IP")
    
    # 尝试从CORS_ORIGINS中提取IP
    if CONFIG_AVAILABLE:
        for origin in CORS_ORIGINS:
            if origin.startswith("http://") and not origin.startswith("http://localhost") and not origin.startswith("http://127.0.0.1"):
                host = origin.split("://")[1].split(":")[0]
                return host
    
    # 默认返回localhost
    return "localhost"

def test_mobile_login(api_base_url=None, frontend_base_url=None):
    """测试移动端登录"""
    
    # 获取或使用提供的API基础URL
    if api_base_url:
        base_url = api_base_url
    else:
        host_ip = get_host_ip()
        base_url = f"http://{host_ip}:8000"
    
    login_url = f"{base_url}/api/auth/login"
    
    print("=" * 50)
    print("移动端登录功能测试")
    print("=" * 50)
    
    # 测试数据
    test_credentials = [
        {"username": "admin", "password": "admin123"},
        {"username": "test_user", "password": "test123"},
    ]
    
    for i, creds in enumerate(test_credentials):
        print(f"\n测试用例 {i+1}: {creds['username']}")
        print("-" * 30)
        
        try:
            # 发送登录请求
            response = requests.post(
                login_url,
                json=creds,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
                },
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"登录成功!")
                    print(f"访问令牌: {data.get('access_token', '无')[:20]}...")
                    print(f"用户: {data.get('user', {}).get('username', '未知')}")
                    print(f"角色: {data.get('user', {}).get('role', '未知')}")
                    
                    # 测试令牌是否有效
                    if data.get('access_token'):
                        test_token_validation(base_url, data['access_token'])
                        
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"响应内容: {response.text}")
            else:
                print(f"登录失败!")
                print(f"响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
        
        time.sleep(1)  # 避免请求过快

def test_token_validation(base_url, token):
    """测试令牌有效性"""
    print("\n测试令牌有效性...")
    
    try:
        response = requests.get(
            f"{base_url}/api/auth/me",
            headers={
                'Authorization': f'Bearer {token}',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"令牌有效! 用户: {user_data.get('username')}")
        else:
            print(f"令牌无效! 状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"令牌验证请求错误: {e}")

def test_cors_configuration(api_base_url=None, frontend_base_url=None):
    """测试CORS配置"""
    print("\n" + "=" * 50)
    print("CORS配置测试")
    print("=" * 50)
    
    # 获取或使用提供的API基础URL
    if api_base_url:
        base_url = api_base_url
    else:
        host_ip = get_host_ip()
        base_url = f"http://{host_ip}:8000"
    
    login_url = f"{base_url}/api/auth/login"
    
    # 模拟跨域请求
    try:
        response = requests.options(
            login_url,
            headers={
                'Origin': 'http://172.30.81.103:3001',  # 前端服务器
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type',
            },
            timeout=10
        )
        
        print(f"CORS预检请求状态码: {response.status_code}")
        print(f"CORS响应头:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control-'):
                print(f"  {header}: {value}")
                
    except requests.exceptions.RequestException as e:
        print(f"CORS测试请求错误: {e}")

def test_mobile_pages(api_base_url=None, frontend_base_url=None):
    """测试移动端页面"""
    print("\n" + "=" * 50)
    print("移动端页面测试")
    print("=" * 50)
    
    # 获取或使用提供的前端基础URL
    if frontend_base_url:
        base_url = frontend_base_url
    else:
        host_ip = get_host_ip()
        base_url = f"http://{host_ip}:3000"
    
    pages = [
        "/mobile_login.html",
        "/mobile_login_fix.html", 
        "/mobile_login_test.html",
        "/mobile_diagnostic.html"
    ]
    
    for page in pages:
        url = base_url + page
        print(f"\n测试页面: {url}")
        
        try:
            response = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
                },
                timeout=10
            )
            
            print(f"  状态码: {response.status_code}")
            print(f"  内容长度: {len(response.text)} 字符")
            
            if response.status_code == 200:
                # 检查是否包含关键元素
                if 'login-form' in response.text or 'username' in response.text:
                    print("  ✓ 包含登录表单")
                else:
                    print("  ✗ 不包含登录表单")
                    
        except requests.exceptions.RequestException as e:
            print(f"  请求错误: {e}")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="移动端登录功能测试工具")
    parser.add_argument("--api-url", help="指定API基础URL，默认自动检测")
    parser.add_argument("--frontend-url", help="指定前端基础URL，默认自动检测")
    args = parser.parse_args()
    
    # 显示配置信息
    print("开始移动端登录功能测试...")
    print("=" * 50)
    print(f"配置信息:")
    print(f"- CONFIG_AVAILABLE: {CONFIG_AVAILABLE}")
    print(f"- API URL: {args.api_url or '自动检测'}")
    print(f"- 前端URL: {args.frontend_url or '自动检测'}")
    print(f"- 主机IP: {get_host_ip()}")
    print("=" * 50)
    
    try:
        # 执行测试，传入命令行参数
        test_mobile_login(args.api_url, args.frontend_url)
        test_cors_configuration(args.api_url, args.frontend_url)
        test_mobile_pages(args.api_url, args.frontend_url)
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)