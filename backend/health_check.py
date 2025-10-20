#!/usr/bin/env python3
"""
健康检查脚本
用于监控Lab Management System的服务器健康状态
"""

import os
import sys
import time
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_api_health(base_url='http://localhost:8000', timeout=10):
    """检查API健康状态"""
    health_url = f"{base_url}/health"
    
    try:
        response = requests.get(health_url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'response_time': response.elapsed.total_seconds(),
                'data': data
            }
        else:
            return {
                'status': 'unhealthy',
                'error': f'HTTP {response.status_code}',
                'response_time': response.elapsed.total_seconds()
            }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unreachable',
            'error': 'Connection refused'
        }
    except requests.exceptions.Timeout:
        return {
            'status': 'timeout',
            'error': f'Request timeout after {timeout}s'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_database_health():
    """检查数据库健康状态"""
    try:
        from database import check_db_health
        start_time = time.time()
        is_healthy = check_db_health()
        response_time = time.time() - start_time
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'response_time': response_time
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_disk_space(threshold=90):
    """检查磁盘空间"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(project_root)
        
        usage_percent = (used / total) * 100
        
        return {
            'status': 'healthy' if usage_percent < threshold else 'warning',
            'usage_percent': round(usage_percent, 2),
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_memory_usage():
    """检查内存使用情况"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        return {
            'status': 'healthy' if memory.percent < 90 else 'warning',
            'usage_percent': memory.percent,
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2)
        }
    except ImportError:
        return {
            'status': 'unknown',
            'error': 'psutil not installed'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_process_status():
    """检查Gunicorn进程状态"""
    pid_file = project_root / 'gunicorn.pid'
    
    if not pid_file.exists():
        return {
            'status': 'not_running',
            'error': 'PID file not found'
        }
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        os.kill(pid, 0)
        
        try:
            import psutil
            process = psutil.Process(pid)
            
            return {
                'status': 'running',
                'pid': pid,
                'memory_mb': round(process.memory_info().rss / (1024**2), 2),
                'cpu_percent': process.cpu_percent(),
                'create_time': process.create_time(),
                'num_threads': process.num_threads()
            }
        except ImportError:
            return {
                'status': 'running',
                'pid': pid
            }
            
    except (FileNotFoundError, ProcessLookupError):
        return {
            'status': 'not_running',
            'error': 'Process not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_log_errors(log_file=None, lines=100):
    """检查日志中的错误"""
    if log_file is None:
        log_file = project_root / 'logs' / 'error.log'
    
    if not log_file.exists():
        return {
            'status': 'no_log',
            'error': 'Log file not found'
        }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # 获取最后N行
        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        # 统计错误级别
        error_count = sum(1 for line in recent_lines if 'ERROR' in line.upper())
        warning_count = sum(1 for line in recent_lines if 'WARNING' in line.upper())
        
        return {
            'status': 'healthy' if error_count == 0 else 'warning',
            'error_count': error_count,
            'warning_count': warning_count,
            'total_lines': len(recent_lines)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def run_comprehensive_check(base_url='http://localhost:8000'):
    """运行全面的健康检查"""
    print(f"🔍 开始健康检查... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    checks = {
        'api': check_api_health(base_url),
        'database': check_database_health(),
        'process': check_process_status(),
        'disk': check_disk_space(),
        'memory': check_memory_usage(),
        'logs': check_log_errors()
    }
    
    # 显示结果
    overall_status = 'healthy'
    
    for check_name, result in checks.items():
        status = result.get('status', 'unknown')
        
        if status == 'healthy':
            icon = "✅"
        elif status in ['warning', 'timeout']:
            icon = "⚠️"
            if overall_status == 'healthy':
                overall_status = 'warning'
        else:
            icon = "❌"
            overall_status = 'unhealthy'
        
        print(f"{icon} {check_name.upper()}: {status}")
        
        # 显示详细信息
        if 'error' in result:
            print(f"   错误: {result['error']}")
        
        if 'response_time' in result:
            print(f"   响应时间: {result['response_time']:.3f}s")
        
        if check_name == 'disk' and 'usage_percent' in result:
            print(f"   磁盘使用: {result['usage_percent']}% ({result['free_gb']}GB 可用)")
        
        if check_name == 'memory' and 'usage_percent' in result:
            print(f"   内存使用: {result['usage_percent']}% ({result['available_gb']}GB 可用)")
        
        if check_name == 'process' and 'pid' in result:
            print(f"   进程ID: {result['pid']}")
            if 'memory_mb' in result:
                print(f"   内存: {result['memory_mb']}MB")
        
        if check_name == 'logs' and 'error_count' in result:
            print(f"   错误数: {result['error_count']}, 警告数: {result['warning_count']}")
        
        print()
    
    print("=" * 60)
    print(f"🎯 总体状态: {overall_status.upper()}")
    
    return overall_status, checks

def monitor_mode(base_url='http://localhost:8000', interval=60):
    """监控模式 - 持续检查健康状态"""
    print(f"🔄 开始监控模式 (间隔: {interval}秒)")
    print("按 Ctrl+C 停止监控")
    print()
    
    try:
        while True:
            status, _ = run_comprehensive_check(base_url)
            
            if status != 'healthy':
                print(f"⚠️  检测到问题，状态: {status}")
            
            print(f"⏰ 下次检查: {interval}秒后")
            print("\n" + "="*60 + "\n")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")

def main():
    parser = argparse.ArgumentParser(description='Lab Management System 健康检查')
    parser.add_argument('--url', default='http://localhost:8000', help='API基础URL')
    parser.add_argument('--monitor', action='store_true', help='监控模式')
    parser.add_argument('--interval', type=int, default=60, help='监控间隔(秒)')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--check', choices=['api', 'database', 'process', 'disk', 'memory', 'logs'],
                       help='单独检查特定组件')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_mode(args.url, args.interval)
        return
    
    if args.check:
        # 单独检查
        check_functions = {
            'api': lambda: check_api_health(args.url),
            'database': check_database_health,
            'process': check_process_status,
            'disk': check_disk_space,
            'memory': check_memory_usage,
            'logs': check_log_errors
        }
        
        result = check_functions[args.check]()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"{args.check.upper()}: {result['status']}")
            if 'error' in result:
                print(f"错误: {result['error']}")
    else:
        # 全面检查
        status, checks = run_comprehensive_check(args.url)
        
        if args.json:
            output = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': status,
                'checks': checks
            }
            print(json.dumps(output, indent=2))
        
        # 设置退出码
        if status == 'unhealthy':
            sys.exit(1)
        elif status == 'warning':
            sys.exit(2)

if __name__ == '__main__':
    main()