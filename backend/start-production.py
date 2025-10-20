#!/usr/bin/env python3
"""
Lab Management System 生产服务器启动脚本
用于管理Gunicorn服务器的启动、停止和监控
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
PID_FILE = PROJECT_ROOT / 'gunicorn.pid'
LOG_DIR = PROJECT_ROOT / 'logs'
ACCESS_LOG = LOG_DIR / 'access.log'
ERROR_LOG = LOG_DIR / 'error.log'
GUNICORN_LOG = LOG_DIR / 'gunicorn.log'
CONFIG_FILE = PROJECT_ROOT / 'gunicorn.conf.py'

# 添加项目根目录到Python路径
sys.path.insert(0, str(PROJECT_ROOT))

def check_environment():
    """检查环境变量和配置"""
    env_file = PROJECT_ROOT / '.env.production'
    if not env_file.exists():
        print("❌ 生产环境配置文件 .env.production 不存在")
        print("请先运行: python scripts/generate-secrets.py")
        return False
    
    # 检查必要的环境变量
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请检查 .env.production 文件")
        return False
    
    print("✅ 环境配置检查通过")
    return True

def check_dependencies():
    """检查依赖包"""
    try:
        import gunicorn
        import uvicorn
        print("✅ 生产服务器依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_database():
    """检查数据库连接"""
    print("🔄 检查数据库连接...")
    try:
        from database import check_db_health, init_database
        
        # 检查数据库健康状态
        if not check_db_health():
            print("❌ 数据库连接失败")
            return False
        
        # 初始化数据库（如果需要）
        init_database()
        print("✅ 数据库检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库设置失败: {e}")
        return False

def is_running():
    """检查服务器是否正在运行"""
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ProcessLookupError, ValueError):
        # PID文件存在但进程不存在，清理PID文件
        if PID_FILE.exists():
            PID_FILE.unlink()
        return False

def start_server(workers=4, port=8000, daemon=False, config_file=None):
    """启动Gunicorn服务器"""
    if is_running():
        print("⚠️  服务器已在运行")
        return False
    
    # 创建日志目录
    LOG_DIR.mkdir(exist_ok=True)
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(PROJECT_ROOT)
    
    # 使用配置文件或命令行参数
    if config_file and Path(config_file).exists():
        cmd = [
            'gunicorn',
            '--config', str(config_file),
            'app:app'
        ]
    else:
        # Gunicorn命令
        cmd = [
            'gunicorn',
            '--name', 'lab-management',
            '--bind', f'0.0.0.0:{port}',
            '--workers', str(workers),
            '--worker-class', 'uvicorn.workers.UvicornWorker',
            '--worker-connections', '1000',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--timeout', '30',
            '--keep-alive', '2',
            '--preload',
            '--enable-stdio-inheritance',
            '--log-level', 'info',
            '--log-file', str(GUNICORN_LOG),
            '--access-logfile', str(ACCESS_LOG),
            '--error-logfile', str(ERROR_LOG),
            '--pid', str(PID_FILE),
            '--capture-output',
            'app:app'
        ]
    
    if daemon:
        cmd.append('--daemon')
    
    print(f"🚀 启动生产服务器...")
    print(f"   地址: http://0.0.0.0:{port}")
    print(f"   工作进程: {workers}")
    
    try:
        if daemon:
            subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, check=True)
            time.sleep(3)  # 等待启动
            
            if is_running():
                print("✅ 服务器启动成功")
                show_server_info()
                return True
            else:
                print("❌ 服务器启动失败")
                show_logs(lines=20)
                return False
        else:
            # 前台运行
            print("🔄 运行在前台模式，按 Ctrl+C 停止")
            process = subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env)
            
            def signal_handler(signum, frame):
                print("\n🛑 正在停止服务器...")
                process.terminate()
                process.wait()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            process.wait()
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务器启动失败: {e}")
        show_logs(lines=10)
        return False
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        return False

def stop_server():
    """停止服务器"""
    if not is_running():
        print("❌ 服务器未运行")
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🛑 正在停止服务器 (PID: {pid})...")
        
        # 发送SIGTERM信号
        os.kill(pid, signal.SIGTERM)
        
        # 等待进程结束
        for i in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except ProcessLookupError:
                break
        else:
            # 如果进程仍然存在，强制终止
            print("⚠️  进程未响应SIGTERM，发送SIGKILL...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        
        print(f"✅ 服务器已停止")
        
        # 删除PID文件
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        return True
        
    except (FileNotFoundError, ProcessLookupError):
        print("❌ 服务器进程未找到")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return False
    except Exception as e:
        print(f"❌ 停止服务器失败: {e}")
        return False

def show_status():
    """显示服务器状态"""
    if not is_running():
        print("🔴 服务器未运行")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🟢 服务器正在运行 (PID: {pid})")
        
        # 显示更多信息
        try:
            import psutil
            process = psutil.Process(pid)
            print(f"   内存使用: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            print(f"   CPU使用: {process.cpu_percent():.1f}%")
            print(f"   启动时间: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   线程数: {process.num_threads()}")
            
            # 显示子进程（worker进程）
            children = process.children()
            if children:
                print(f"   Worker进程: {len(children)}")
                for i, child in enumerate(children[:3]):  # 只显示前3个
                    print(f"     Worker {i+1}: PID {child.pid}, 内存 {child.memory_info().rss / 1024 / 1024:.1f} MB")
        except ImportError:
            print("   (安装psutil包可显示更多信息)")
            
    except Exception as e:
        print(f"❌ 检查状态失败: {e}")

def show_server_info():
    """显示服务器信息"""
    if not is_running():
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        import psutil
        process = psutil.Process(pid)
        
        print(f"📊 服务器信息:")
        print(f"   PID: {pid}")
        print(f"   内存使用: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"   CPU使用: {process.cpu_percent():.1f}%")
        print(f"   启动时间: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   线程数: {process.num_threads()}")
        
        # 显示子进程（worker进程）
        children = process.children()
        if children:
            print(f"   Worker进程: {len(children)}")
            for i, child in enumerate(children[:3]):  # 只显示前3个
                print(f"     Worker {i+1}: PID {child.pid}, 内存 {child.memory_info().rss / 1024 / 1024:.1f} MB")
    
    except Exception as e:
        print(f"⚠️  获取服务器信息失败: {e}")

def show_logs(lines=50, log_type='error'):
    """显示日志"""
    log_files = {
        'error': ERROR_LOG,
        'access': ACCESS_LOG,
        'gunicorn': GUNICORN_LOG
    }
    
    log_file = log_files.get(log_type, ERROR_LOG)
    
    if not log_file.exists():
        print(f"📝 日志文件不存在: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        print(f"📝 最近 {len(recent_lines)} 行日志 ({log_type}):")
        print("-" * 60)
        for line in recent_lines:
            print(line.rstrip())
        print("-" * 60)
    
    except Exception as e:
        print(f"❌ 读取日志失败: {e}")

def reload_server():
    """重新加载服务器配置"""
    if not is_running():
        print("❌ 服务器未运行")
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGHUP)
        print("✅ 服务器配置已重新加载")
        return True
    
    except Exception as e:
        print(f"❌ 重新加载失败: {e}")
        return False

def create_gunicorn_config():
    """创建Gunicorn配置文件"""
    config_content = '''# Gunicorn配置文件
# Lab Management System

import multiprocessing
import os
from pathlib import Path

# 基础配置
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# 性能配置
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True

# 日志配置
project_root = Path(__file__).parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

loglevel = "info"
logfile = str(log_dir / "gunicorn.log")
accesslog = str(log_dir / "access.log")
errorlog = str(log_dir / "error.log")
access_log_format = '%%(h)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s" %%(D)s'

# 进程管理
pidfile = str(project_root / "gunicorn.pid")
user = os.getenv("GUNICORN_USER")
group = os.getenv("GUNICORN_GROUP")

# 安全配置
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# 其他配置
enable_stdio_inheritance = True
capture_output = True
'''
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ Gunicorn配置文件已创建: {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Lab Management System 生产服务器管理')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'check', 'logs', 'reload', 'config'],
                       help='要执行的操作')
    parser.add_argument('--workers', type=int, default=4, help='Worker进程数量')
    parser.add_argument('--port', type=int, default=8000, help='监听端口')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--config', help='Gunicorn配置文件路径')
    parser.add_argument('--log-type', choices=['error', 'access', 'gunicorn'], default='error',
                       help='日志类型')
    parser.add_argument('--lines', type=int, default=50, help='显示的日志行数')
    parser.add_argument('--skip-checks', action='store_true', help='跳过环境检查')
    
    args = parser.parse_args()
    
    print(f"Lab Management System 生产服务器管理 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if args.action == 'check':
        success = True
        success &= check_environment()
        success &= check_dependencies()
        success &= check_database()
        
        if success:
            print("\n✅ 所有检查通过，可以启动服务器")
        else:
            print("\n❌ 检查失败，请修复问题后重试")
            sys.exit(1)
    
    elif args.action == 'config':
        create_gunicorn_config()
    
    elif args.action == 'start':
        if not args.skip_checks:
            if not check_environment():
                sys.exit(1)
        
        config_file = args.config or (CONFIG_FILE if CONFIG_FILE.exists() else None)
        
        if start_server(args.workers, args.port, args.daemon, config_file):
            if args.daemon:
                print(f"\n🎉 服务器已启动")
                print(f"📊 状态检查: python {__file__} status")
                print(f"📝 查看日志: python {__file__} logs")
                print(f"🔄 重新加载: python {__file__} reload")
                print(f"🛑 停止服务: python {__file__} stop")
        else:
            sys.exit(1)
    
    elif args.action == 'stop':
        if stop_server():
            print("✅ 服务器已停止")
        else:
            print("❌ 停止服务器失败")
            sys.exit(1)
    
    elif args.action == 'restart':
        print("🔄 重启服务器...")
        stop_server()
        time.sleep(2)
        
        if not args.skip_checks:
            if not check_environment():
                sys.exit(1)
        
        config_file = args.config or (CONFIG_FILE if CONFIG_FILE.exists() else None)
        
        if start_server(args.workers, args.port, args.daemon, config_file):
            print("✅ 服务器重启成功")
        else:
            sys.exit(1)
    
    elif args.action == 'reload':
        reload_server()
    
    elif args.action == 'logs':
        show_logs(args.lines, args.log_type)
    
    elif args.action == 'status':
        show_status()

if __name__ == '__main__':
    main()