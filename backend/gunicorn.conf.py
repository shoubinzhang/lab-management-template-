# Gunicorn配置文件
# Lab Management System 生产环境配置

import multiprocessing
import os
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# 服务器绑定
bind = "0.0.0.0:8000"
backlog = 2048

# Worker进程配置
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 性能优化
preload_app = True
reuse_port = True

# 进程管理
pidfile = str(project_root / "gunicorn.pid")
user = os.getenv("GUNICORN_USER")
group = os.getenv("GUNICORN_GROUP")
tmp_upload_dir = None

# 日志配置
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
logfile = str(log_dir / "gunicorn.log")
accesslog = str(log_dir / "access.log")
errorlog = str(log_dir / "error.log")

# 访问日志格式
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)

# 进程命名
proc_name = 'lab-management'

# SSL配置 (如果需要)
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')
ssl_version = 2  # TLSv1.2+
ciphers = 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'

# 安全配置
limit_request_line = 4096
# 其他配置
enable_stdio_inheritance = True
capture_output = True
chdir = str(project_root)

# 环境变量
raw_env = [
    f'PYTHONPATH={project_root}',
    f'ENVIRONMENT=production'
]

# 钩子函数
def on_starting(server):
    """服务器启动时调用"""
    server.log.info("Lab Management System 正在启动...")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Bind: {bind}")
    server.log.info(f"PID文件: {pidfile}")

def on_reload(server):
    """重新加载时调用"""
    server.log.info("Lab Management System 正在重新加载...")

def when_ready(server):
    """服务器准备就绪时调用"""
    server.log.info("Lab Management System 已启动并准备接受连接")
    
    # 创建健康检查文件
    ready_file = project_root / '.ready'
    ready_file.touch()
    
    # 执行健康检查
    import time
    time.sleep(2)
    
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            server.log.info("健康检查通过，服务器已就绪")
        else:
            server.log.warning(f"健康检查失败: HTTP {response.status_code}")
    except Exception as e:
        server.log.warning(f"健康检查异常: {e}")

def on_exit(server):
    """服务器退出时调用"""
    server.log.info("Lab Management System 正在关闭...")
    
    # 清理健康检查文件
    ready_file = project_root / '.ready'
    if ready_file.exists():
        ready_file.unlink()

def worker_int(worker):
    """Worker进程收到SIGINT信号时调用"""
    worker.log.info(f"Worker {worker.pid} 收到中断信号")

def pre_fork(server, worker):
    """Worker进程fork之前调用"""
    server.log.info(f"Worker {worker.age} 正在启动")

def post_fork(server, worker):
    """Worker进程fork之后调用"""
    server.log.info(f"Worker {worker.pid} 已启动")

def post_worker_init(worker):
    """Worker进程初始化完成后调用"""
    # 设置数据库连接池
    try:
        from database import init_connection_pool
        init_connection_pool()
        worker.log.info("数据库连接池初始化完成")
    except Exception as e:
        worker.log.error(f"数据库连接池初始化失败: {e}")
    
    # 初始化缓存
    try:
        from cache import init_cache
        init_cache()
        worker.log.info("缓存系统初始化完成")
    except Exception as e:
        worker.log.error(f"缓存系统初始化失败: {e}")
    
    # 设置日志
    import logging
    logging.getLogger('uvicorn.access').disabled = True
    
    worker.log.info(f"Worker {worker.pid} 初始化完成")

def worker_abort(worker):
    """Worker进程异常终止时调用"""
    import traceback
    worker.log.error(f"Worker {worker.pid} 异常终止")
    worker.log.error(f"异常信息: {traceback.format_exc()}")

def pre_exec(server):
    """执行新的二进制文件之前调用"""
    server.log.info("正在执行新的二进制文件...")

# 环境特定配置
if os.getenv('ENVIRONMENT') == 'development':
    reload = True
    reload_extra_files = [
        str(project_root / 'app.py'),
        str(project_root / 'database.py'),
        str(project_root / '.env.development')
    ]
    loglevel = 'debug'
    workers = 1

# 生产环境优化
if os.getenv('ENVIRONMENT') == 'production':
    # 禁用调试模式
    debug = False
    
    # 安全设置
    forwarded_allow_ips = '*'
    proxy_allow_ips = '*'
    
    # 性能监控
    statsd_host = os.getenv('STATSD_HOST')
    if statsd_host:
        statsd_prefix = 'lab-management'

# 性能调优
performance_mode = os.getenv('PERFORMANCE_MODE', 'balanced')
if performance_mode == 'high':
    # 高性能模式
    workers = multiprocessing.cpu_count() * 4
    worker_connections = 2000
    max_requests = 2000
    max_requests_jitter = 200
    keepalive = 5
elif performance_mode == 'memory':
    # 内存优化模式
    workers = max(2, multiprocessing.cpu_count())
    worker_connections = 500
    max_requests = 500
    max_requests_jitter = 50
    keepalive = 1

# 调试模式
if os.getenv('DEBUG', 'false').lower() == 'true':
    loglevel = 'debug'
    reload = True
    workers = 1
    timeout = 0  # 禁用超时

# 性能调优
worker_tmp_dir = '/dev/shm'  # 使用内存文件系统提高性能

# 钩子函数
def on_starting(server):
    """服务器启动时调用"""
    server.log.info("Lab Management API服务器正在启动...")

def on_reload(server):
    """服务器重载时调用"""
    server.log.info("Lab Management API服务器正在重载...")

def when_ready(server):
    """服务器准备就绪时调用"""
    server.log.info("Lab Management API服务器已准备就绪")

def worker_int(worker):
    """工作进程接收到SIGINT信号时调用"""
    worker.log.info("工作进程 %s 正在关闭...", worker.pid)

def pre_fork(server, worker):
    """工作进程fork之前调用"""
    server.log.info("工作进程 %s 正在启动", worker.pid)

def post_fork(server, worker):
    """工作进程fork之后调用"""
    server.log.info("工作进程 %s 已启动", worker.pid)

def post_worker_init(worker):
    """工作进程初始化完成后调用"""
    worker.log.info("工作进程 %s 初始化完成", worker.pid)

def worker_abort(worker):
    """工作进程异常终止时调用"""
    worker.log.info("工作进程 %s 异常终止", worker.pid)

def pre_exec(server):
    """服务器重新执行前调用"""
    server.log.info("Lab Management API服务器正在重新执行")

def pre_request(worker, req):
    """处理请求前调用"""
    worker.log.debug("%s %s", req.method, req.path)

def post_request(worker, req, environ, resp):
    """处理请求后调用"""
    worker.log.debug("%s %s - %s", req.method, req.path, resp.status_code)