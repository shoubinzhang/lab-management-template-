import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import logging
from functools import wraps
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 获取日志器
logger = logging.getLogger('app')

class PerformanceMonitor:
    """性能监控类"""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'error_count': 0,
            'total_response_time': 0,
            'slow_requests': 0,
            'database_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.slow_request_threshold = 1000  # 1秒
    
    def record_request(self, response_time: float, status_code: int):
        """记录请求指标"""
        self.metrics['request_count'] += 1
        self.metrics['total_response_time'] += response_time
        
        if status_code >= 400:
            self.metrics['error_count'] += 1
        
        if response_time > self.slow_request_threshold:
            self.metrics['slow_requests'] += 1
    
    def record_database_query(self):
        """记录数据库查询"""
        self.metrics['database_queries'] += 1
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.metrics['cache_misses'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        avg_response_time = (
            self.metrics['total_response_time'] / self.metrics['request_count']
            if self.metrics['request_count'] > 0 else 0
        )
        
        error_rate = (
            self.metrics['error_count'] / self.metrics['request_count'] * 100
            if self.metrics['request_count'] > 0 else 0
        )
        
        cache_hit_rate = (
            self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100
            if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0
        )
        
        return {
            **self.metrics,
            'avg_response_time': round(avg_response_time, 2),
            'error_rate': round(error_rate, 2),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'system_metrics': self.get_system_metrics()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'disk_usage': disk.percent,
                'disk_free': disk.free,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def reset_metrics(self):
        """重置指标"""
        for key in self.metrics:
            self.metrics[key] = 0

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

def setup_sentry(app):
    """设置Sentry监控"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    environment = os.getenv('FLASK_ENV', 'development')
    
    if not sentry_dsn:
        logger.warning("未配置SENTRY_DSN，跳过Sentry初始化")
        return
    
    # 配置日志集成
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # 捕获info及以上级别的日志
        event_level=logging.ERROR  # 将error及以上级别的日志作为事件发送
    )
    
    # 初始化Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        integrations=[
            FlaskIntegration(transaction_style='endpoint'),
            SqlalchemyIntegration(),
            logging_integration,
            RedisIntegration()
        ],
        traces_sample_rate=0.1 if environment == 'production' else 1.0,
        profiles_sample_rate=0.1 if environment == 'production' else 1.0,
        send_default_pii=False,  # 不发送个人身份信息
        attach_stacktrace=True,
        before_send=filter_sensitive_data,
        before_send_transaction=filter_transaction_data
    )
    
    logger.info(f"Sentry监控已初始化，环境: {environment}")

def filter_sensitive_data(event, hint):
    """过滤敏感数据"""
    # 移除敏感的请求头
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            if header in event['request']['headers']:
                event['request']['headers'][header] = '[Filtered]'
    
    # 移除敏感的表单数据
    if 'request' in event and 'data' in event['request']:
        sensitive_fields = ['password', 'token', 'secret', 'key']
        data = event['request']['data']
        if isinstance(data, dict):
            for field in sensitive_fields:
                if field in data:
                    data[field] = '[Filtered]'
    
    return event

def filter_transaction_data(event, hint):
    """过滤事务数据"""
    # 忽略健康检查和静态文件请求
    if 'request' in event and 'url' in event['request']:
        url = event['request']['url']
        if any(path in url for path in ['/health', '/static', '/favicon.ico']):
            return None
    
    return event

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # 记录异常到Sentry
            sentry_sdk.capture_exception(e)
            raise
        finally:
            # 记录性能指标
            execution_time = (time.time() - start_time) * 1000
            
            # 如果执行时间过长，记录到Sentry
            if execution_time > 5000:  # 5秒
                sentry_sdk.add_breadcrumb(
                    message=f"慢函数执行: {func.__name__}",
                    data={
                        'function': func.__name__,
                        'execution_time': execution_time
                    },
                    level='warning'
                )
    
    return wrapper

def track_user_action(action: str, user_id: Optional[str] = None, **kwargs):
    """追踪用户行为"""
    with sentry_sdk.configure_scope() as scope:
        if user_id:
            scope.set_user({"id": user_id})
        
        scope.set_tag("action", action)
        
        sentry_sdk.add_breadcrumb(
            message=f"用户行为: {action}",
            data=kwargs,
            level='info'
        )

def capture_business_exception(message: str, level: str = 'error', **extra_data):
    """捕获业务异常"""
    with sentry_sdk.configure_scope() as scope:
        for key, value in extra_data.items():
            scope.set_extra(key, value)
        
        if level == 'error':
            sentry_sdk.capture_message(message, level='error')
        elif level == 'warning':
            sentry_sdk.capture_message(message, level='warning')
        else:
            sentry_sdk.capture_message(message, level='info')

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func):
        """注册健康检查"""
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'metrics': performance_monitor.get_metrics()
        }
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                check_result = check_func()
                execution_time = (time.time() - start_time) * 1000
                
                results['checks'][name] = {
                    'status': 'pass' if check_result else 'fail',
                    'execution_time': round(execution_time, 2)
                }
                
                if not check_result:
                    results['status'] = 'unhealthy'
                    
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['status'] = 'unhealthy'
                
                # 记录健康检查失败
                logger.error(f"健康检查失败: {name} - {e}")
                sentry_sdk.capture_exception(e)
        
        return results

# 全局健康检查器实例
health_checker = HealthChecker()

def setup_monitoring(app):
    """设置监控系统"""
    # 初始化Sentry
    setup_sentry(app)
    
    # 注册健康检查
    def database_check():
        """数据库健康检查"""
        try:
            from database import db
            db.session.execute('SELECT 1')
            return True
        except Exception:
            return False
    
    def redis_check():
        """Redis健康检查"""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            return True
        except Exception:
            return False
    
    health_checker.register_check('database', database_check)
    health_checker.register_check('redis', redis_check)
    
    logger.info("监控系统初始化完成")

# 错误处理器
def handle_error(error):
    """统一错误处理"""
    error_id = sentry_sdk.last_event_id()
    
    logger.error(
        f"应用错误: {error}",
        extra={
            'error_id': error_id,
            'error_type': type(error).__name__
        },
        exc_info=True
    )
    
    return {
        'error': '服务器内部错误',
        'error_id': error_id
    }, 500

# 性能分析装饰器
def profile_performance(threshold_ms: int = 1000):
    """性能分析装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000
                
                if execution_time > threshold_ms:
                    logger.warning(
                        f"慢函数检测: {func.__name__}",
                        extra={
                            'function': func.__name__,
                            'execution_time': round(execution_time, 2),
                            'threshold': threshold_ms
                        }
                    )
                    
                    # 发送到Sentry
                    sentry_sdk.set_tag("slow_function", func.__name__)
                    sentry_sdk.capture_message(
                        f"慢函数: {func.__name__} 执行时间: {execution_time:.2f}ms",
                        level='warning'
                    )
        
        return wrapper
    return decorator