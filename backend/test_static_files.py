import requests
import os

# 测试当前目录下的HTML文件列表
def list_mobile_html_files():
    """列出backend目录下所有移动端HTML文件"""
    mobile_files = []
    try:
        for file in os.listdir('.'):
            if file.endswith('.html') and (file.startswith('mobile_') or file == 'mobile_access_guide.html'):
                mobile_files.append(file)
        print(f"找到的移动端HTML文件: {mobile_files}")
    except Exception as e:
        print(f"列出文件时出错: {e}")
    return mobile_files

# 测试静态文件访问
def test_static_access():
    """测试通过/static/路径访问文件"""
    base_url = "http://localhost:8000"
    mobile_files = list_mobile_html_files()
    
    print("\n测试静态文件访问:")
    print("="*50)
    
    # 测试1: 直接访问HTML文件（通过app.py中的路由）
    print("\n测试1: 直接访问HTML文件（通过app.py中的路由）:")
    for file in mobile_files:
        if file == 'mobile_login_final.html':
            # 这个文件有对应的路由
            url = f"{base_url}/mobile_login"
            try:
                response = requests.get(url, timeout=5)
                print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
            except Exception as e:
                print(f"访问 {url} 失败: {e}")
        elif file == 'mobile_login_test.html':
            # 这个文件有对应的路由
            url = f"{base_url}/mobile_login_test"
            try:
                response = requests.get(url, timeout=5)
                print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
            except Exception as e:
                print(f"访问 {url} 失败: {e}")
        elif file == 'mobile_access_guide.html':
            # 这个文件有对应的路由
            url = f"{base_url}/mobile_guide"
            try:
                response = requests.get(url, timeout=5)
                print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
            except Exception as e:
                print(f"访问 {url} 失败: {e}")
        elif file.endswith('.html'):
            # 其他HTML文件
            url = f"{base_url}/{file}"
            try:
                response = requests.get(url, timeout=5)
                print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
            except Exception as e:
                print(f"访问 {url} 失败: {e}")
    
    # 测试2: 通过/static/路径访问
    print("\n测试2: 通过/static/路径访问:")
    for file in mobile_files:
        url = f"{base_url}/static/{file}"
        try:
            response = requests.get(url, timeout=5)
            print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
        except Exception as e:
            print(f"访问 {url} 失败: {e}")
    
    # 测试3: 特别测试mobile_test_nav.html
    print("\n测试3: 特别测试mobile_test_nav.html:")
    url = f"{base_url}/static/mobile_test_nav.html"
    try:
        response = requests.get(url, timeout=5)
        print(f"访问 {url} - 状态码: {response.status_code}, 内容长度: {len(response.text)} 字节")
    except Exception as e:
        print(f"访问 {url} 失败: {e}")

if __name__ == "__main__":
    print("开始测试静态文件访问...")
    test_static_access()
    print("\n测试完成!")