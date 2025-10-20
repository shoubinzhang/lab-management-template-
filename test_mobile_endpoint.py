import requests
import time

# 测试后端8000端口的/mobile_login端点
def test_backend_mobile_login():
    print("=== 测试后端移动端登录端点 ===")
    url = "http://localhost:8000/mobile_login"
    try:
        response = requests.get(url, timeout=5)
        print(f"后端8000端口响应状态码: {response.status_code}")
        print(f"响应内容前100个字符: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"后端8000端口访问失败: {str(e)}")
        return False

# 测试前端3000端口的/mobile_login端点
def test_frontend_mobile_login():
    print("=== 测试前端移动端登录端点 ===")
    url = "http://localhost:3000/mobile_login"
    try:
        response = requests.get(url, timeout=5)
        print(f"前端3000端口响应状态码: {response.status_code}")
        print(f"响应内容前100个字符: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"前端3000端口访问失败: {str(e)}")
        return False

# 查看登录页面状态
def check_login_page():
    print("=== 检查登录页面 ===")
    url = "http://localhost:3000/login"
    try:
        response = requests.get(url, timeout=5)
        print(f"登录页面响应状态码: {response.status_code}")
        # 检查页面内容中是否包含二维码相关元素
        has_qr_element = "手机扫码访问" in response.text
        has_mobile_login = "/mobile_login" in response.text
        print(f"页面包含'手机扫码访问'元素: {has_qr_element}")
        print(f"页面包含'/mobile_login'路径: {has_mobile_login}")
        return response.text
    except Exception as e:
        print(f"登录页面访问失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("开始测试移动端登录功能...")
    
    # 测试后端端点
    backend_ok = test_backend_mobile_login()
    print()
    
    # 测试前端端点
    frontend_ok = test_frontend_mobile_login()
    print()
    
    # 检查登录页面
    login_page_content = check_login_page()
    print()
    
    # 分析结果
    print("=== 测试结果分析 ===")
    if backend_ok and not frontend_ok:
        print("✓ 建议: 二维码应该指向后端8000端口")
    elif frontend_ok and not backend_ok:
        print("✗ 问题: 后端8000端口无法访问，但前端3000端口可访问")
    elif frontend_ok and backend_ok:
        print("! 注意: 前后端都响应了/mobile_login请求，需要确保二维码指向后端8000端口")
    else:
        print("✗ 错误: 前后端都无法访问/mobile_login请求")
    
    print("\n请确保前端生成的二维码URL使用8000端口，指向后端服务！")