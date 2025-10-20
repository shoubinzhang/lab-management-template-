from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
import psutil
import os
from typing import Dict, Any
from flask import request, g
import threading
from datetime import datetime

# 定义Prometheus指标

# 计数器指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table']
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

USER_ACTIONS = Counter(
    'user_actions_total',
    'Total user actions',
    ['action', 'user_type']
)

# 直方图指标（用于测量延迟）
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

CACHE_OPERATION_DURATION = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25]
)

# 仪表指标（用于测量当前值）
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

MEMORY_USAGE_PERCENT = Gauge(
    'memory_usage_percent',
    'Memory usage percentage'
)

DISK_USAGE = Gauge(
    'disk_usage_bytes',
    'Disk usage in bytes',
    ['device']
)

DISK_USAGE_PERCENT = Gauge(
    'disk_usage_percent',
    'Disk usage percentage',
    ['device']
)

ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections',
    'Number of database connections',
    ['state']
)

CACHE_SIZE = Gauge(
    'cache_size_bytes',
    'Cache size in bytes'
)

QUEUE_SIZE = Gauge(
    'queue_size',
    'Queue size',
    ['queue_name']
)

# 信息指标
APP_INFO = Info(
    'app_info',
    'Application information'
)

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.active_requests = 0
        self.lock = threading.Lock()
        
        # 设置应用信息
        APP_INFO.info({
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('FLASK_ENV', 'development'),
            'python_version': os.sys.version.split()[0]
        })
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if status_code >= 400:
            ERROR_COUNT.labels(
                method=method,
                endpoint=endpoint,
                error_type='client_error' if status_code < 500 else 'server_error'
            ).inc()
    
    def record_database_operation(self, operation: str, table: str, duration: float):
        """记录数据库操作指标"""
        DATABASE_OPERATIONS.labels(
            operation=operation,
            table=table
        ).inc()
        
        DATABASE_QUERY_DURATION.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str, duration: float):
        """记录缓存操作指标"""
        CACHE_OPERATIONS.labels(
            operation=operation,
            result=result
        ).inc()
        
        CACHE_OPERATION_DURATION.labels(
            operation=operation
        ).observe(duration)
    
    def record_user_action(self, action: str, user_type: str):
        """记录用户行为指标"""
        USER_ACTIONS.labels(
            action=action,
            user_type=user_type
        ).inc()
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            MEMORY_USAGE_PERCENT.set(memory.percent)
            
            # 磁盘使用情况
            for partition in psutil.disk_partitions():
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    device = partition.device.replace(':', '').replace('\\', '_')
                    DISK_USAGE.labels(device=device).set(disk_usage.used)
                    DISK_USAGE_PERCENT.labels(device=device).set(
                        (disk_usage.used / disk_usage.total) * 100
                    )
                except (PermissionError, OSError):
                    continue
            
        except Exception as e:
            print(f"更新系统指标失败: {e}")
    
    def increment_active_requests(self):
        """增加活跃请求数"""
        with self.lock:
            self.active_requests += 1
            ACTIVE_CONNECTIONS.set(self.active_requests)
    
    def decrement_active_requests(self):
        """减少活跃请求数"""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
            ACTIVE_CONNECTIONS.set(self.active_requests)
    
    def set_active_users(self, count: int):
        """设置活跃用户数"""
        ACTIVE_USERS.set(count)
    
    def set_database_connections(self, active: int, idle: int):
        """设置数据库连接数"""
        DATABASE_CONNECTIONS.labels(state='active').set(active)
        DATABASE_CONNECTIONS.labels(state='idle').set(idle)
    
    def set_cache_size(self, size: int):
        """设置缓存大小"""
        CACHE_SIZE.set(size)
    
    def set_queue_size(self, queue_name: str, size: int):
        """设置队列大小"""
        QUEUE_SIZE.labels(queue_name=queue_name).set(size)

# 全局指标收集器实例
metrics_collector = MetricsCollector()

def metrics_middleware(app):
    """Prometheus指标中间件"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        metrics_collector.increment_active_requests()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # 获取端点信息
            endpoint = request.endpoint or 'unknown'
            method = request.method
            status_code = response.status_code
            
            # 记录请求指标
            metrics_collector.record_request(method, endpoint, status_code, duration)
        
        metrics_collector.decrement_active_requests()
        return response
    
    return app

def monitor_database_operation(operation: str, table: str):
    """数据库操作监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_database_operation(operation, table, duration)
        return wrapper
    return decorator

def monitor_cache_operation(operation: str):
    """缓存操作监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            try:
                result = func(*args, **kwargs)
                cache_result = 'hit' if result is not None else 'miss'
                return result
            except Exception as e:
                cache_result = 'error'
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_cache_operation(operation, cache_result, duration)
        return wrapper
    return decorator

def track_user_action(action: str):
    """用户行为追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从请求中获取用户类型（需要根据实际认证系统调整）
            user_type = 'anonymous'
            if hasattr(request, 'user') and request.user:
                user_type = getattr(request.user, 'role', 'authenticated')
            
            metrics_collector.record_user_action(action, user_type)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_metrics():
    """获取Prometheus格式的指标"""
    # 更新系统指标
    metrics_collector.update_system_metrics()
    
    return generate_latest()

def setup_metrics_endpoint(app):
    """设置指标端点"""
    
    @app.route('/metrics')
    def metrics():
        """Prometheus指标端点"""
        from flask import Response
        return Response(get_metrics(), mimetype=CONTENT_TYPE_LATEST)
    
    # 应用中间件
    metrics_middleware(app)
    
    return app

# 定期更新指标的后台任务
def start_metrics_updater():
    """启动指标更新器"""
    import threading
    import time
    
    def update_metrics():
        while True:
            try:
                metrics_collector.update_system_metrics()
                time.sleep(30)  # 每30秒更新一次
            except Exception as e:
                print(f"更新指标失败: {e}")
                time.sleep(60)  # 出错时等待更长时间
    
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
    
    return thread

# 自定义指标示例
class BusinessMetrics:
    """业务指标"""
    
    def __init__(self):
        self.reagent_operations = Counter(
            'reagent_operations_total',
            'Total reagent operations',
            ['operation', 'reagent_type']
        )
        
        self.consumable_operations = Counter(
            'consumable_operations_total',
            'Total consumable operations',
            ['operation', 'consumable_type']
        )
        
        self.user_logins = Counter(
            'user_logins_total',
            'Total user logins',
            ['user_role']
        )
        
        self.inventory_levels = Gauge(
            'inventory_levels',
            'Current inventory levels',
            ['item_type', 'item_name']
        )
        
        self.low_stock_alerts = Counter(
            'low_stock_alerts_total',
            'Total low stock alerts',
            ['item_type']
        )
    
    def record_reagent_operation(self, operation: str, reagent_type: str):
        """记录试剂操作"""
        self.reagent_operations.labels(
            operation=operation,
            reagent_type=reagent_type
        ).inc()
    
    def record_consumable_operation(self, operation: str, consumable_type: str):
        """记录耗材操作"""
        self.consumable_operations.labels(
            operation=operation,
            consumable_type=consumable_type
        ).inc()
    
    def record_user_login(self, user_role: str):
        """记录用户登录"""
        self.user_logins.labels(user_role=user_role).inc()
    
    def update_inventory_level(self, item_type: str, item_name: str, level: int):
        """更新库存水平"""
        self.inventory_levels.labels(
            item_type=item_type,
            item_name=item_name
        ).set(level)
    
    def record_low_stock_alert(self, item_type: str):
        """记录低库存警报"""
        self.low_stock_alerts.labels(item_type=item_type).inc()

# 全局业务指标实例
business_metrics = BusinessMetrics()