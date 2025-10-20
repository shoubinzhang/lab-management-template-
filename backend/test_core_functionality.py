"""
核心功能验证测试
验证领用申请流程的关键组件是否正常工作
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_server_health():
    """测试服务器健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"✅ 服务器健康检查通过: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 服务器健康检查失败: {e}")
        return False

def test_login():
    """测试登录功能"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            token = result["access_token"]
            print("✅ 登录功能正常")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None

def test_database_connection(token):
    """测试数据库连接"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 数据库连接正常，当前用户: {user_info['username']}")
            return True
        else:
            print(f"❌ 数据库连接测试失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 数据库连接测试异常: {e}")
        return False

def test_usage_records_api(token):
    """测试使用记录API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/usage-records/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            records = response.json()
            print(f"✅ 使用记录API正常，当前记录数: {len(records)}")
            return True
        else:
            print(f"❌ 使用记录API测试失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 使用记录API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始核心功能验证测试\n")
    
    # 1. 服务器健康检查
    if not test_server_health():
        return False
    
    # 等待服务器完全启动
    print("⏳ 等待服务器完全启动...")
    time.sleep(3)
    
    # 2. 登录测试
    token = test_login()
    if not token:
        return False
    
    # 3. 数据库连接测试
    if not test_database_connection(token):
        return False
    
    # 4. 使用记录API测试
    if not test_usage_records_api(token):
        return False
    
    print("\n🎉 所有核心功能验证通过！")
    print("📋 系统状态:")
    print("   - 后端服务器: ✅ 正常运行")
    print("   - 用户认证: ✅ 正常工作")
    print("   - 数据库连接: ✅ 正常连接")
    print("   - 使用记录API: ✅ 正常响应")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 核心功能验证完成，系统准备就绪！")
    else:
        print("\n❌ 核心功能验证失败，请检查系统配置。")
        exit(1)