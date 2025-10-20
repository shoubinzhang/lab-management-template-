import requests
import os
import time

# 测试HTML页面重定向功能
def test_html_redirects():
    # 获取static目录下所有HTML文件
    static_dir = r"c:\lab-management-app\backend\static"
    html_files = [f for f in os.listdir(static_dir) if f.endswith('.html')]
    
    print(f"开始测试HTML页面重定向功能，共测试{len(html_files)}个页面")
    print("=" * 70)
    
    success_count = 0
    failure_count = 0
    
    # 测试每个HTML文件的重定向
    for html_file in html_files:
        # 去除.html扩展名
        filename = html_file[:-5]
        # 构造直接访问的URL和通过/static访问的URL
        direct_url = f"http://localhost:8000/{filename}.html"
        static_url = f"http://localhost:8000/static/{html_file}"
        
        try:
            # 测试直接访问URL
            start_time = time.time()
            direct_response = requests.get(direct_url, timeout=5, allow_redirects=True)
            response_time = time.time() - start_time
            
            # 验证响应状态码和最终URL
            if direct_response.status_code == 200 and direct_response.url.endswith(static_url):
                print(f"✓ 成功: {direct_url} → {static_url}")
                print(f"   状态码: {direct_response.status_code}, 响应时间: {response_time:.3f}秒")
                success_count += 1
            else:
                print(f"✗ 失败: {direct_url}")
                print(f"   状态码: {direct_response.status_code}, 最终URL: {direct_response.url}")
                failure_count += 1
        except Exception as e:
            print(f"✗ 失败: {direct_url}")
            print(f"   异常: {str(e)}")
            failure_count += 1
        
        print("-" * 70)
    
    # 打印总结
    print("测试总结:")
    print(f"  成功访问: {success_count}个页面")
    print(f"  访问失败: {failure_count}个页面")
    print(f"  成功率: {(success_count / len(html_files) * 100):.1f}%")
    print(f"\n提示：")
    print(f"  1. 现在可以直接通过 http://localhost:8000/文件名.html 访问静态页面")
    print(f"  2. 系统会自动重定向到 /static/ 目录下的对应文件")

if __name__ == "__main__":
    test_html_redirects()