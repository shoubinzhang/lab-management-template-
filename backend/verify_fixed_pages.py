import requests
import time

# 服务器地址
base_url = "http://localhost:8000/static"

# 要验证的页面列表
pages_to_verify = [
    'mobile_index.html',
    'mobile_devices.html',
    'mobile_reagents.html',
    'mobile_consumables.html',
    'mobile_scan.html',
    'mobile_user.html',
    'mobile_login_final.html',
    'mobile_test_nav.html',
    'mobile_test_fixed.html',
    'mobile_access_guide.html',
    'mobile_dashboard.html',
    'mobile_login_test.html',
    'mobile_maintenance.html',
    'mobile_reservations.html',
    'mobile_test_debug.html'
]

# 测试函数
def test_page(url, timeout=5):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        # 检查状态码和内容长度
        success = response.status_code == 200 and len(response.content) > 0
        
        return {
            'url': url,
            'success': success,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'response_time': round(end_time - start_time, 2),
            'error': None
        }
    except requests.exceptions.RequestException as e:
        return {
            'url': url,
            'success': False,
            'status_code': None,
            'content_length': 0,
            'response_time': None,
            'error': str(e)
        }

# 主函数
def main():
    print("=== 移动端页面验证工具 ===")
    print(f"开始验证 {len(pages_to_verify)} 个页面通过 {base_url} 访问...\n")
    
    results = []
    success_count = 0
    failure_count = 0
    
    # 测试每个页面
    for i, page in enumerate(pages_to_verify, 1):
        url = f"{base_url}/{page}"
        print(f"[{i}/{len(pages_to_verify)}] 测试: {url}")
        
        result = test_page(url)
        results.append(result)
        
        if result['success']:
            success_count += 1
            print(f"✅ 成功 - 状态码: {result['status_code']}, 内容长度: {result['content_length']}, 响应时间: {result['response_time']}s")
        else:
            failure_count += 1
            print(f"❌ 失败 - 状态码: {result['status_code']}, 错误: {result['error']}")
    
    # 打印总结
    print("\n=== 验证结果总结 ===")
    print(f"总页面数: {len(pages_to_verify)}")
    print(f"成功访问: {success_count}")
    print(f"访问失败: {failure_count}")
    
    # 打印失败详情
    if failure_count > 0:
        print("\n=== 失败详情 ===")
        for result in results:
            if not result['success']:
                print(f"{result['url']} - 状态码: {result['status_code']}, 错误: {result['error']}")
    
    # 提供访问建议
    print("\n=== 访问建议 ===")
    if success_count == len(pages_to_verify):
        print("🎉 恭喜！所有移动端页面现在都可以通过/static/路径正常访问。")
        print("\n请使用以下格式访问您的移动页面：")
        print("http://localhost:8000/static/[页面文件名]")
        print("\n例如：")
        print("  - 首页: http://localhost:8000/static/mobile_index.html")
        print("  - 设备管理: http://localhost:8000/static/mobile_devices.html")
        print("  - 个人中心: http://localhost:8000/static/mobile_user.html")
        print("\n修复后的测试页面: http://localhost:8000/static/mobile_test_fixed.html")
    else:
        print("⚠️ 仍有页面无法正常访问，请检查服务器配置或页面文件是否存在。")
        print("建议检查：")
        print("1. 确保uvicorn服务器正在运行")
        print("2. 检查页面文件是否存在于backend目录下")
        print("3. 确认app.py中的静态文件配置正确")

if __name__ == "__main__":
    main()