#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""实验室管理系统 - 移动端功能综合测试脚本"""

import requests
import json
import time
import sys
import os

# 配置信息
BACKEND_HOST = "172.30.81.103"
BACKEND_PORT = 8000
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# 测试账户信息
TEST_ACCOUNTS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "should_succeed": True
    },
    "test_user": {
        "username": "test_user",
        "password": "wrong_password",
        "should_succeed": False
    }
}

# 测试页面列表
TEST_PAGES = [
    "/static/mobile_login_final.html",
    "/mobile_login",
    "/mobile",
    "/mobile_guide"
]

# 颜色常量，用于终端输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

# 检查命令行参数是否支持颜色
def supports_color():
    """检查当前终端是否支持颜色输出"""
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

# 确保在不支持颜色的终端中禁用颜色
if not supports_color():
    class Colors:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
        ENDC = ''

class ComprehensiveTester:
    """综合测试类"""
    
    def __init__(self):
        self.success_count = 0
        self.fail_count = 0
        self.results = []
        
    def print_header(self):
        """打印测试头部信息"""
        print(f"\n{Colors.BLUE}===== 实验室管理系统 - 移动端功能综合测试 ====={Colors.ENDC}\n")
        print(f"测试日期: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端服务: {BASE_URL}\n")
    
    def print_result(self, test_name, success, message=None):
        """打印测试结果"""
        status = f"{Colors.GREEN}✓ 成功{Colors.ENDC}" if success else f"{Colors.RED}✗ 失败{Colors.ENDC}"
        result_text = f"[{status}] {test_name}"
        if message:
            result_text += f" - {message}"
        print(result_text)
        
        # 更新计数
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # 记录结果
        self.results.append({
            "name": test_name,
            "success": success,
            "message": message
        })
    
    def test_backend_health(self):
        """测试后端服务健康状态"""
        test_name = "后端服务健康检查"
        try:
            url = f"{BASE_URL}/health"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["ok", "healthy"]:
                    self.print_result(test_name, True, f"后端服务正常运行 - 状态: {data}")
                else:
                    self.print_result(test_name, False, f"状态异常: {data}")
            else:
                self.print_result(test_name, False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.print_result(test_name, False, f"连接失败: {str(e)}")
    
    def test_login_functionality(self):
        """测试登录功能"""
        print(f"\n{Colors.YELLOW}测试登录功能:{Colors.ENDC}")
        
        for account_name, account_info in TEST_ACCOUNTS.items():
            test_name = f"登录测试 - {account_name}"
            try:
                url = f"{BASE_URL}/api/auth/login"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                payload = {
                    "username": account_info["username"],
                    "password": account_info["password"]
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
                
                if account_info["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        # 检查响应结构
                        if "access_token" in data and "token_type" in data and "user" in data:
                            self.print_result(test_name, True, "登录成功，获取到令牌")
                            # 验证token
                            self._validate_token(data["access_token"])
                        else:
                            self.print_result(test_name, False, "登录成功但响应结构不正确")
                    else:
                        self.print_result(test_name, False, f"预期成功但失败: 状态码 {response.status_code}")
                else:
                    if response.status_code == 401:
                        self.print_result(test_name, True, "预期失败，正确返回401")
                    else:
                        self.print_result(test_name, False, f"预期失败但状态码异常: {response.status_code}")
            except Exception as e:
                self.print_result(test_name, False, f"请求异常: {str(e)}")
    
    def _validate_token(self, token):
        """验证JWT令牌的有效性"""
        test_name = "令牌验证测试"
        try:
            url = f"{BASE_URL}/api/auth/me"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                self.print_result(test_name, True, "令牌有效，用户信息获取成功")
            else:
                self.print_result(test_name, False, f"令牌无效: 状态码 {response.status_code}")
        except Exception as e:
            self.print_result(test_name, False, f"验证异常: {str(e)}")
    
    def test_static_pages(self):
        """测试静态页面访问"""
        print(f"\n{Colors.YELLOW}测试静态页面访问:{Colors.ENDC}")
        
        for page_path in TEST_PAGES:
            test_name = f"页面访问测试 - {page_path}"
            try:
                url = f"{BASE_URL}{page_path}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" in content_type:
                        self.print_result(test_name, True, f"页面可正常访问 - 内容类型: {content_type}")
                    else:
                        self.print_result(test_name, False, f"页面返回但内容类型异常: {content_type}")
                else:
                    self.print_result(test_name, False, f"页面访问失败: 状态码 {response.status_code}")
            except Exception as e:
                self.print_result(test_name, False, f"页面访问异常: {str(e)}")
    
    def print_summary(self):
        """打印测试摘要"""
        total_tests = self.success_count + self.fail_count
        print(f"\n{Colors.BLUE}===== 测试摘要 ====={Colors.ENDC}")
        print(f"总测试数: {total_tests}")
        print(f"成功数: {Colors.GREEN}{self.success_count}{Colors.ENDC}")
        print(f"失败数: {Colors.RED}{self.fail_count}{Colors.ENDC}")
        
        if self.fail_count == 0:
            print(f"\n{Colors.GREEN}测试通过！所有功能正常工作！{Colors.ENDC}")
            print(f"\n移动端登录页面访问地址：")
            for page_path in TEST_PAGES:
                print(f"  {BASE_URL}{page_path}")
        else:
            print(f"\n{Colors.RED}测试失败！请查看上面的详细信息进行排查。{Colors.ENDC}")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header()
        # 测试后端健康状态
        self.test_backend_health()
        # 测试登录功能
        self.test_login_functionality()
        # 测试静态页面访问
        self.test_static_pages()
        # 打印测试摘要
        self.print_summary()

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_all_tests()