"""Redis配置文件"""
import os
from typing import Optional

class RedisConfig:
    """Redis配置类"""
    
    def __init__(self):
        # Redis连接配置
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD')
        
        # 连接池配置
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 20))
        self.socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', 5.0))
        self.socket_connect_timeout = float(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 5.0))
        
        # 重试配置
        self.retry_on_timeout = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        self.health_check_interval = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', 30))
        
        # 缓存配置
        self.default_ttl = int(os.getenv('REDIS_DEFAULT_TTL', 3600))  # 1小时
        self.key_prefix = os.getenv('REDIS_KEY_PREFIX', 'lab_mgmt:')
        
        # 开发环境配置
        self.debug = os.getenv('REDIS_DEBUG', 'false').lower() == 'true'
        
    def get_connection_url(self) -> str:
        """获取Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"redis://{self.host}:{self.port}/{self.db}"
    
    def get_connection_params(self) -> dict:
        """获取Redis连接参数"""
        params = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'health_check_interval': self.health_check_interval,
            'max_connections': self.max_connections,
            'decode_responses': True  # 自动解码响应为字符串
        }
        
        if self.password:
            params['password'] = self.password
            
        return params

# 全局配置实例
redis_config = RedisConfig()

# 环境特定配置
if os.getenv('ENVIRONMENT') == 'production':
    # 生产环境配置
    redis_config.default_ttl = 7200  # 2小时
    redis_config.max_connections = 50
elif os.getenv('ENVIRONMENT') == 'development':
    # 开发环境配置
    redis_config.debug = True
    redis_config.default_ttl = 1800  # 30分钟
elif os.getenv('ENVIRONMENT') == 'test':
    # 测试环境配置
    redis_config.db = 1  # 使用不同的数据库
    redis_config.default_ttl = 300  # 5分钟