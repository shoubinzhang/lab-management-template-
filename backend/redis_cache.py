# backend/redis_cache.py

import redis
import json
import pickle
import logging
from typing import Any, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import os
from decouple import config
from redis_config import redis_config

# 配置日志
logger = logging.getLogger(__name__)

class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, config_obj=None):
        self.redis_client = None
        self.is_connected = False
        self.config = config_obj or redis_config
        self.default_ttl = self.config.default_ttl
        self.key_prefix = self.config.key_prefix
        self._connect()
    
    def _connect(self):
        """连接到Redis服务器"""
        try:
            # 使用配置对象获取连接参数
            connection_params = self.config.get_connection_params()
            
            self.redis_client = redis.Redis(**connection_params)
            
            # 测试连接
            self.redis_client.ping()
            self.is_connected = True
            logger.info(f"Successfully connected to Redis at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            self.redis_client = None
    
    def _serialize(self, data: Any) -> bytes:
        """序列化数据"""
        try:
            # 尝试JSON序列化（更快，更小）
            return json.dumps(data, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # 如果JSON失败，使用pickle
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """反序列化数据"""
        try:
            # 尝试JSON反序列化
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 如果JSON失败，使用pickle
            return pickle.loads(data)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        
        Returns:
            bool: 是否设置成功
        """
        if not self.is_connected:
            return False
        
        try:
            serialized_data = self._serialize(value)
            
            if ttl:
                return self.redis_client.setex(key, ttl, serialized_data)
            else:
                return self.redis_client.set(key, serialized_data)
                
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或None
        """
        if not self.is_connected:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            
            return self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否删除成功
        """
        if not self.is_connected:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键
        
        Args:
            pattern: 键的模式（支持通配符*）
        
        Returns:
            int: 删除的键数量
        """
        if not self.is_connected:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to delete keys with pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 键是否存在
        """
        if not self.is_connected:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取键的剩余生存时间
        
        Args:
            key: 缓存键
        
        Returns:
            int: 剩余秒数，-1表示永不过期，-2表示键不存在
        """
        if not self.is_connected:
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -2
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
        
        Returns:
            bool: 是否设置成功
        """
        if not self.is_connected:
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Failed to set expiry for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器
        
        Args:
            key: 缓存键
            amount: 递增量
        
        Returns:
            int: 递增后的值
        """
        if not self.is_connected:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return None
    
    def get_stats(self) -> dict:
        """获取Redis统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self.is_connected:
            return {
                'connected': False,
                'error': 'Not connected to Redis'
            }
        
        try:
            info = self.redis_client.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human', 'Unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """计算缓存命中率"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    def flush_all(self) -> bool:
        """清空所有缓存
        
        Returns:
            bool: 是否清空成功
        """
        if not self.is_connected:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to flush Redis cache: {e}")
            return False
    
    def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            try:
                self.redis_client.close()
                self.is_connected = False
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

# 全局Redis缓存实例
redis_cache = RedisCache()

def cache_result(key_prefix: str, ttl: int = 300):
    """缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒），默认5分钟
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            cached_result = redis_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            redis_cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """使缓存模式失效
    
    Args:
        pattern: 缓存键模式
    """
    deleted_count = redis_cache.delete_pattern(pattern)
    logger.info(f"Invalidated {deleted_count} cache entries with pattern: {pattern}")
    return deleted_count