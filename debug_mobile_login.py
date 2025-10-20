#!/usr/bin/env python3
"""
移动端登录问题诊断脚本
使用Python标准库，避免依赖问题
"""

import urllib.request
import urllib.parse
import json
import socket
import sys
import os

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个外部地址来获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def test_health_check(base_url):
    """测试健康检查端点"""
    try:
        url = f"{base_url}/health"
        print(f"正在测试健康检查: {url}")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mobile-Diagnostic-Tool/1.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            status_code = response.getcode()
            
            print(f"状态码: {status_code}")
            print(f"响应: {data}")
            
            if status_code == 200:
                try:
                    json_data = json.loads(data)
                    print(f"服务状态: {json_data.get('status', 'unknown')}")
                    return True
                except json.JSONDecodeError:
                    print("响应不是有效的JSON格式")
                    return False
            else:
                print(f"健康检查失败，状态码: {status_code}")
                return False
                
    except urllib.error.URLError as e:
        print(f"连接失败: {e}")
        return False
    except Exception as e:
        print(f"测试健康检查时发生错误: {e}")
        return False

def test_login(base_url, username="admin", password="admin123"):
    """测试登录功能"""
    try:
        login_url = f"{base_url}/api/auth/login"
        print(f"\n正在测试登录: {login_url}")
        
        # 准备登录数据
        login_data = {
            "username": username,
            "password": password
        }
        
        # 将数据编码为JSON
        json_data = json.dumps(login_data).encode('utf-8')
        
        # 创建请求
        req = urllib.request.Request(login_url, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1')
        req.add_header('Accept', 'application/json')
        
        # 发送请求
        with urllib.request.urlopen(req, data=json_data, timeout=15) as response:
            response_data = response.read().decode('utf-8')
            status_code = response.getcode()
            
            print(f"登录状态码: {status_code}")
            print(f"登录响应: {response_data[:200]}...")
            
            if status_code == 200:
                try:
                    login_response = json.loads(response_data)
                    token = login_response.get('access_token')
                    if token:
                        print(f"✅ 登录成功！获取到Token: {token[:30]}...")
                        return token
                    else:
                        print("❌ 登录响应中没有找到access_token")
                        return None
                except json.JSONDecodeError:
                    print("登录响应不是有效的JSON格式")
                    return None
            else:
                print(f"❌ 登录失败，状态码: {status_code}")
                return None
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print(f"❌ 登录HTTP错误: {e.code} - {error_body}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ 登录连接失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 登录测试时发生错误: {e}")
        return None

def test_user_info(base_url, token):
    """测试获取用户信息"""
    try:
        user_url = f"{base_url}/api/auth/me"
        print(f"\n正在测试获取用户信息: {user_url}")
        
        req = urllib.request.Request(user_url, method='GET')
        req.add_header('Authorization', f'Bearer {token}')
        req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            status_code = response.getcode()
            
            print(f"用户信息状态码: {status_code}")
            print(f"用户信息响应: {response_data[:200]}...")
            
            if status_code == 200:
                try:
                    user_data = json.loads(response_data)
                    print(f"✅ 获取用户信息成功！用户名: {user_data.get('username', 'unknown')}")
                    return True
                except json.JSONDecodeError:
                    print("用户信息响应不是有效的JSON格式")
                    return False
            else:
                print(f"❌ 获取用户信息失败，状态码: {status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 获取用户信息时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("🔍 移动端登录问题诊断脚本")
    print("=" * 50)
    
    # 获取本机IP
    local_ip = get_local_ip()
    print(f"本机IP地址: {local_ip}")
    
    # 测试不同的基础URL
    base_urls = [
        f"http://{local_ip}:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    for base_url in base_urls:
        print(f"\n{'='*50}")
        print(f"正在测试: {base_url}")
        print(f"{'='*50}")
        
        # 测试健康检查
        health_ok = test_health_check(base_url)
        
        if health_ok:
            # 测试登录
            token = test_login(base_url)
            
            if token:
                # 测试获取用户信息
                user_info_ok = test_user_info(base_url, token)
                
                if user_info_ok:
                    print(f"\n✅ {base_url} - 所有测试通过！移动端可以正常使用此地址")
                    print(f"\n📱 手机访问地址: {base_url}")
                    print(f"🔗 测试页面: {base_url.replace(':8000', ':3000')}/mobile_login_final_test.html")
                else:
                    print(f"\n❌ {base_url} - 获取用户信息失败")
            else:
                print(f"\n❌ {base_url} - 登录失败")
        else:
            print(f"\n❌ {base_url} - 健康检查失败，服务可能未运行或端口错误")
    
    print(f"\n{'='*50}")
    print("诊断完成！")
    print("\n💡 如果所有测试都失败，请检查:")
    print("1. 后端服务是否正在运行 (python app.py)")
    print("2. 防火墙是否允许8000端口访问")
    print("3. 手机和电脑是否在同一WiFi网络下")
    print("4. 是否使用了正确的IP地址")

if __name__ == "__main__":
    main()