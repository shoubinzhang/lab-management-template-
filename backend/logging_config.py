import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
import json

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class JSONFormatter(logging.Formatter):
    """JSON格式化器，用于结构化日志"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 格式化时间
        record.asctime = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        
        # 构建日志消息
        log_message = f"{color}[{record.asctime}] {record.levelname:8} {record.name}:{record.lineno} - {record.getMessage()}{reset}"
        
        # 添加异常信息
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message

def get_logging_config():
    """获取日志配置"""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    environment = os.getenv('FLASK_ENV', 'development')
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
            'colored': {
                '()': ColoredFormatter,
            },
            'standard': {
                'format': '[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored' if environment == 'development' else 'standard',
                'stream': sys.stdout
            },
            'file_info': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': LOG_DIR / 'app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': LOG_DIR / 'error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'file_access': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': LOG_DIR / 'access.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': ['console', 'file_info', 'file_error'],
                'propagate': False
            },
            'access': {
                'level': 'INFO',
                'handlers': ['file_access'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['console', 'file_info'],
                'propagate': False
            },
            'gunicorn.error': {
                'level': 'INFO',
                'handlers': ['console', 'file_error'],
                'propagate': False
            },
            'gunicorn.access': {
                'level': 'INFO',
                'handlers': ['file_access'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    return config

def setup_logging():
    """设置日志配置"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # 获取应用日志器
    logger = logging.getLogger('app')
    logger.info("日志系统初始化完成")
    
    return logger

def get_logger(name='app'):
    """获取日志器"""
    return logging.getLogger(name)

# 请求日志中间件
class RequestLoggingMiddleware:
    """请求日志中间件"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('access')
    
    def __call__(self, environ, start_response):
        import time
        import uuid
        from werkzeug.wrappers import Request
        
        request = Request(environ)
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 添加请求ID到环境变量
        environ['REQUEST_ID'] = request_id
        
        def new_start_response(status, response_headers, exc_info=None):
            # 记录访问日志
            response_time = (time.time() - start_time) * 1000  # 毫秒
            status_code = int(status.split()[0])
            
            log_data = {
                'request_id': request_id,
                'method': request.method,
                'url': request.url,
                'endpoint': request.path,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'status_code': status_code,
                'response_time': round(response_time, 2),
                'content_length': request.content_length or 0
            }
            
            # 记录日志
            extra = {
                'request_id': request_id,
                'ip_address': request.remote_addr,
                'endpoint': request.path,
                'method': request.method,
                'status_code': status_code,
                'response_time': round(response_time, 2)
            }
            
            if status_code >= 400:
                self.logger.warning(f"HTTP {status_code} - {request.method} {request.path}", extra=extra)
            else:
                self.logger.info(f"HTTP {status_code} - {request.method} {request.path}", extra=extra)
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)

# 性能监控装饰器
def log_performance(func):
    """性能监控装饰器"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger('app')
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                f"函数 {func.__name__} 执行完成",
                extra={'function': func.__name__, 'execution_time': round(execution_time, 2)}
            )
            
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            logger.error(
                f"函数 {func.__name__} 执行失败: {str(e)}",
                extra={'function': func.__name__, 'execution_time': round(execution_time, 2)},
                exc_info=True
            )
            raise
    
    return wrapper