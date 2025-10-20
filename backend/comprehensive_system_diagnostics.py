import requests
import os
import time
import sqlite3
import json
from datetime import datetime

# 服务器配置
base_url = "http://localhost:8000"
static_base_url = f"{base_url}/static"

# 定义测试项目
tests = {
    'static_files': {
        'name': '静态文件服务',
        'description': '检查移动页面是否可以通过/static/路径正常访问',
        'pages': [
            'mobile_index.html',
            'mobile_devices.html',
            'mobile_user.html',
            'mobile_test_fixed.html'
        ]
    },
    'api_endpoints': {
        'name': 'API端点',
        'description': '检查关键API是否可访问',
        'endpoints': [
            {'url': '/api/devices', 'method': 'GET', 'auth_required': True},
            {'url': '/api/users/me', 'method': 'GET', 'auth_required': True},
            {'url': '/api/health', 'method': 'GET', 'auth_required': False}
        ]
    },
    'database_connection': {
        'name': '数据库连接',
        'description': '检查SQLite数据库是否可连接',
        'files': [
            'lab.db',
            'lab_management.db',
            'test.db'
        ]
    },
    'authentication': {
        'name': '认证功能',
        'description': '检查登录和认证流程',
        'login_endpoint': '/api/auth/login',
        'test_credentials': {
            'username': 'admin',
            'password': 'admin123'
        }
    },
    'network_configuration': {
        'name': '网络配置',
        'description': '检查网络相关配置'
    }
}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 打印带颜色的消息
def print_colored(text, color):
    print(f"{color}{text}{bcolors.ENDC}")

# 测试静态文件服务
def test_static_files():
    results = {'success': True, 'details': []}
    
    for page in tests['static_files']['pages']:
        url = f"{static_base_url}/{page}"
        try:
            response = requests.get(url, timeout=5)
            success = response.status_code == 200 and len(response.content) > 0
            results['details'].append({
                'page': page,
                'url': url,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'success': success
            })
            if not success:
                results['success'] = False
        except Exception as e:
            results['details'].append({
                'page': page,
                'url': url,
                'error': str(e),
                'success': False
            })
            results['success'] = False
    
    return results

# 测试API端点
def test_api_endpoints(token=None):
    results = {'success': True, 'details': []}
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    for endpoint in tests['api_endpoints']['endpoints']:
        url = f"{base_url}{endpoint['url']}"
        try:
            if endpoint['auth_required'] and not token:
                results['details'].append({
                    'endpoint': endpoint['url'],
                    'url': url,
                    'skipped': True,
                    'reason': '需要认证令牌'
                })
                continue
            
            current_headers = headers.copy() if endpoint['auth_required'] else {}
            response = requests.request(endpoint['method'], url, headers=current_headers, timeout=5)
            success = 200 <= response.status_code < 300
            results['details'].append({
                'endpoint': endpoint['url'],
                'url': url,
                'method': endpoint['method'],
                'status_code': response.status_code,
                'success': success
            })
            if not success:
                results['success'] = False
        except Exception as e:
            results['details'].append({
                'endpoint': endpoint['url'],
                'url': url,
                'error': str(e),
                'success': False
            })
            results['success'] = False
    
    return results

# 测试数据库连接
def test_database_connection():
    results = {'success': True, 'details': []}
    
    for db_file in tests['database_connection']['files']:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_file)
        if not os.path.exists(db_path):
            results['details'].append({
                'db_file': db_file,
                'error': '数据库文件不存在',
                'success': False
            })
            results['success'] = False
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            results['details'].append({
                'db_file': db_file,
                'table_count': len(tables),
                'success': True
            })
        except Exception as e:
            results['details'].append({
                'db_file': db_file,
                'error': str(e),
                'success': False
            })
            results['success'] = False
    
    return results

# 测试认证功能
def test_authentication():
    results = {'success': False, 'details': {}, 'token': None}
    login_url = f"{base_url}{tests['authentication']['login_endpoint']}"
    credentials = tests['authentication']['test_credentials']
    
    try:
        response = requests.post(login_url, json=credentials, timeout=10)
        results['details']['status_code'] = response.status_code
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data:
                    results['success'] = True
                    results['token'] = data['access_token']
                    results['details']['token_received'] = True
                else:
                    results['details']['error'] = '响应中没有access_token字段'
            except json.JSONDecodeError:
                results['details']['error'] = '无法解析登录响应为JSON'
        else:
            results['details']['error'] = f'登录失败，状态码: {response.status_code}'
    except Exception as e:
        results['details']['error'] = str(e)
    
    return results

# 测试网络配置
def test_network_configuration():
    results = {'success': True, 'details': []}
    
    # 检查服务器是否可访问
    try:
        response = requests.get(base_url, timeout=5)
        server_accessible = response.status_code != 404
        results['details'].append({
            'test': '服务器可访问性',
            'success': server_accessible,
            'status_code': response.status_code
        })
        if not server_accessible:
            results['success'] = False
    except Exception as e:
        results['details'].append({
            'test': '服务器可访问性',
            'success': False,
            'error': str(e)
        })
        results['success'] = False

    # 检查CORS配置
    try:
        headers = {'Origin': 'http://localhost:3000'}
        response = requests.get(f"{base_url}/api/health", headers=headers, timeout=5)
        cors_headers = response.headers.get('Access-Control-Allow-Origin')
        results['details'].append({
            'test': 'CORS配置',
            'success': cors_headers is not None,
            'access_control_allow_origin': cors_headers
        })
        if cors_headers is None:
            results['success'] = False
    except Exception as e:
        results['details'].append({
            'test': 'CORS配置',
            'success': False,
            'error': str(e)
        })
        results['success'] = False

    return results

# 生成详细报告
def generate_report(all_results):
    report = {
        'timestamp': datetime.now().isoformat(),
        'base_url': base_url,
        'results': all_results
    }
    
    # 保存报告到文件
    report_file = f"system_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report, report_file

# 主函数
def main():
    print_colored("\n========== 实验室管理系统综合诊断工具 ==========", bcolors.HEADER)
    print_colored(f"诊断开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", bcolors.OKBLUE)
    print_colored(f"测试服务器: {base_url}", bcolors.OKBLUE)
    print_colored("=============================================\n", bcolors.HEADER)
    
    all_results = {}
    token = None
    
    # 1. 测试静态文件服务
    print_colored(f"\n1. {tests['static_files']['name']}", bcolors.BOLD)
    print(f"描述: {tests['static_files']['description']}")
    static_results = test_static_files()
    all_results['static_files'] = static_results
    
    for detail in static_results['details']:
        status = "✅ 成功" if detail['success'] else "❌ 失败"
        if detail['success']:
            print_colored(f"  - {detail['page']}: {status} (状态码: {detail['status_code']}, 内容长度: {detail['content_length']})", bcolors.OKGREEN)
        else:
            error_msg = detail.get('error', f"状态码: {detail.get('status_code')}")
            print_colored(f"  - {detail['page']}: {status} - {error_msg}", bcolors.FAIL)
    
    # 2. 测试网络配置
    print_colored(f"\n2. {tests['network_configuration']['name']}", bcolors.BOLD)
    print(f"描述: {tests['network_configuration']['description']}")
    network_results = test_network_configuration()
    all_results['network_configuration'] = network_results
    
    for detail in network_results['details']:
        status = "✅ 成功" if detail['success'] else "❌ 失败"
        if detail['success']:
            print_colored(f"  - {detail['test']}: {status}", bcolors.OKGREEN)
        else:
            error_msg = detail.get('error', '未知错误')
            print_colored(f"  - {detail['test']}: {status} - {error_msg}", bcolors.FAIL)
    
    # 3. 测试数据库连接
    print_colored(f"\n3. {tests['database_connection']['name']}", bcolors.BOLD)
    print(f"描述: {tests['database_connection']['description']}")
    db_results = test_database_connection()
    all_results['database_connection'] = db_results
    
    for detail in db_results['details']:
        status = "✅ 成功" if detail['success'] else "❌ 失败"
        if detail['success']:
            print_colored(f"  - {detail['db_file']}: {status} (表数量: {detail['table_count']})", bcolors.OKGREEN)
        else:
            print_colored(f"  - {detail['db_file']}: {status} - {detail['error']}", bcolors.FAIL)
    
    # 4. 测试认证功能
    print_colored(f"\n4. {tests['authentication']['name']}", bcolors.BOLD)
    print(f"描述: {tests['authentication']['description']}")
    auth_results = test_authentication()
    all_results['authentication'] = auth_results
    token = auth_results.get('token')
    
    status = "✅ 成功" if auth_results['success'] else "❌ 失败"
    if auth_results['success']:
        print_colored(f"  - 登录测试: {status} (已获取令牌)", bcolors.OKGREEN)
    else:
        print_colored(f"  - 登录测试: {status} - {auth_results['details'].get('error', '未知错误')}", bcolors.FAIL)
    
    # 5. 测试API端点
    print_colored(f"\n5. {tests['api_endpoints']['name']}", bcolors.BOLD)
    print(f"描述: {tests['api_endpoints']['description']}")
    api_results = test_api_endpoints(token)
    all_results['api_endpoints'] = api_results
    
    for detail in api_results['details']:
        if 'skipped' in detail:
            print_colored(f"  - {detail['endpoint']}: ⚠️ 跳过 ({detail['reason']})", bcolors.WARNING)
        else:
            status = "✅ 成功" if detail['success'] else "❌ 失败"
            if detail['success']:
                print_colored(f"  - {detail['method']} {detail['endpoint']}: {status} (状态码: {detail['status_code']})", bcolors.OKGREEN)
            else:
                error_msg = detail.get('error', f"状态码: {detail.get('status_code')}")
                print_colored(f"  - {detail['method']} {detail['endpoint']}: {status} - {error_msg}", bcolors.FAIL)
    
    # 生成报告
    report, report_file = generate_report(all_results)
    
    # 总结
    print_colored("\n=============================================", bcolors.HEADER)
    print_colored("系统诊断总结", bcolors.BOLD)
    
    overall_success = all(results['success'] for results in all_results.values())
    
    if overall_success:
        print_colored("✅ 所有测试项均通过！系统运行正常。", bcolors.OKGREEN)
    else:
        print_colored("❌ 发现问题！请查看详细报告。", bcolors.FAIL)
        
        # 列出失败的测试项
        print("\n失败的测试项：")
        for test_name, results in all_results.items():
            if not results['success']:
                test_display_name = tests.get(test_name, {}).get('name', test_name)
                print_colored(f"  - {test_display_name}", bcolors.FAIL)
    
    print_colored(f"\n诊断报告已保存至: {report_file}", bcolors.OKCYAN)
    print_colored("=============================================\n", bcolors.HEADER)

if __name__ == "__main__":
    main()