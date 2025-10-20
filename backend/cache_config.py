# backend/cache_config.py

from typing import Dict, Any
from enum import Enum

class CacheType(Enum):
    """缓存类型枚举"""
    REAGENTS = "reagents"
    CONSUMABLES = "consumables"
    DEVICES = "devices"
    USERS = "users"
    APPROVALS = "approvals"
    MAINTENANCE = "maintenance"
    RESERVATIONS = "reservations"
    EXPERIMENTS = "experiment_records"
    STATISTICS = "statistics"

class CacheConfig:
    """缓存配置类"""
    
    # 缓存键前缀
    KEY_PREFIXES = {
        CacheType.REAGENTS: "reagents",
        CacheType.CONSUMABLES: "consumables", 
        CacheType.DEVICES: "devices",
        CacheType.USERS: "users",
        CacheType.APPROVALS: "approvals",
        CacheType.MAINTENANCE: "maintenance",
        CacheType.RESERVATIONS: "reservations",
        CacheType.EXPERIMENTS: "experiment_records",
        CacheType.STATISTICS: "stats"
    }
    
    # 缓存过期时间（秒）
    TTL_CONFIG = {
        CacheType.REAGENTS: 300,        # 5分钟 - 试剂数据变化较频繁
        CacheType.CONSUMABLES: 300,     # 5分钟 - 耗材数据变化较频繁
        CacheType.DEVICES: 600,         # 10分钟 - 设备信息相对稳定
        CacheType.USERS: 1800,          # 30分钟 - 用户信息变化较少
        CacheType.APPROVALS: 60,        # 1分钟 - 审批状态需要实时性
        CacheType.MAINTENANCE: 900,     # 15分钟 - 维护记录相对稳定
        CacheType.RESERVATIONS: 180,    # 3分钟 - 预约信息需要较高实时性
        CacheType.EXPERIMENTS: 600,     # 10分钟 - 实验记录相对稳定
        CacheType.STATISTICS: 3600      # 1小时 - 统计数据可以缓存较长时间
    }
    
    # 热点数据配置（需要预热的数据）
    WARMUP_CONFIG = {
        CacheType.REAGENTS: {
            "enabled": True,
            "endpoints": ["/api/reagents", "/api/reagents/categories"],
            "priority": 1
        },
        CacheType.CONSUMABLES: {
            "enabled": True,
            "endpoints": ["/api/consumables", "/api/consumables/categories"],
            "priority": 1
        },
        CacheType.DEVICES: {
            "enabled": True,
            "endpoints": ["/api/devices", "/api/devices/status"],
            "priority": 2
        },
        CacheType.USERS: {
            "enabled": False,  # 用户数据不预热，按需缓存
            "endpoints": [],
            "priority": 3
        },
        CacheType.STATISTICS: {
            "enabled": True,
            "endpoints": ["/api/statistics/dashboard"],
            "priority": 3
        }
    }
    
    # 缓存失效策略
    INVALIDATION_PATTERNS = {
        CacheType.REAGENTS: [
            "reagents:*",
            "stats:reagents:*"
        ],
        CacheType.CONSUMABLES: [
            "consumables:*",
            "stats:consumables:*"
        ],
        CacheType.DEVICES: [
            "devices:*",
            "maintenance:*",
            "reservations:*",
            "stats:devices:*"
        ],
        CacheType.USERS: [
            "users:*"
        ],
        CacheType.APPROVALS: [
            "approvals:*",
            "stats:approvals:*"
        ],
        CacheType.MAINTENANCE: [
            "maintenance:*",
            "devices:*",  # 维护记录变化可能影响设备状态
            "stats:maintenance:*"
        ],
        CacheType.RESERVATIONS: [
            "reservations:*",
            "devices:*",  # 预约变化可能影响设备可用性
            "stats:reservations:*"
        ],
        CacheType.EXPERIMENTS: [
            "experiment_records:*",
            "stats:experiment_records:*"
        ]
    }
    
    @classmethod
    def get_cache_key(cls, cache_type: CacheType, identifier: str = "") -> str:
        """生成缓存键
        
        Args:
            cache_type: 缓存类型
            identifier: 标识符（如ID、查询参数等）
        
        Returns:
            str: 完整的缓存键
        """
        prefix = cls.KEY_PREFIXES.get(cache_type, "unknown")
        if identifier:
            return f"{prefix}:{identifier}"
        return f"{prefix}:all"
    
    @classmethod
    def get_ttl(cls, cache_type: CacheType) -> int:
        """获取缓存过期时间
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            int: 过期时间（秒）
        """
        return cls.TTL_CONFIG.get(cache_type, 300)  # 默认5分钟
    
    @classmethod
    def get_invalidation_patterns(cls, cache_type: CacheType) -> list:
        """获取缓存失效模式
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            list: 需要失效的缓存键模式列表
        """
        return cls.INVALIDATION_PATTERNS.get(cache_type, [])
    
    @classmethod
    def should_warmup(cls, cache_type: CacheType) -> bool:
        """检查是否需要预热
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            bool: 是否需要预热
        """
        config = cls.WARMUP_CONFIG.get(cache_type, {})
        return config.get("enabled", False)
    
    @classmethod
    def get_warmup_endpoints(cls, cache_type: CacheType) -> list:
        """获取预热端点
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            list: 需要预热的API端点列表
        """
        config = cls.WARMUP_CONFIG.get(cache_type, {})
        return config.get("endpoints", [])
    
    @classmethod
    def get_warmup_priority(cls, cache_type: CacheType) -> int:
        """获取预热优先级
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            int: 预热优先级（数字越小优先级越高）
        """
        config = cls.WARMUP_CONFIG.get(cache_type, {})
        return config.get("priority", 999)

# 缓存管理器辅助函数
def invalidate_related_cache(cache_type: CacheType):
    """使相关缓存失效
    
    Args:
        cache_type: 缓存类型
    """
    try:
        from redis_cache import redis_cache
        
        patterns = CacheConfig.get_invalidation_patterns(cache_type)
        total_deleted = 0
        
        for pattern in patterns:
            deleted = redis_cache.delete_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    except Exception as e:
        # Redis不可用时优雅降级，记录警告但不抛出异常
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"缓存失效失败，Redis可能不可用: {e}")
        return 0

def cache_key_for_list(cache_type: CacheType, **filters) -> str:
    """为列表查询生成缓存键
    
    Args:
        cache_type: 缓存类型
        **filters: 查询过滤器
    
    Returns:
        str: 缓存键
    """
    if filters:
        # 将过滤器排序以确保一致的缓存键
        filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
        return CacheConfig.get_cache_key(cache_type, f"list:{filter_str}")
    else:
        return CacheConfig.get_cache_key(cache_type, "list")

def cache_key_for_item(cache_type: CacheType, item_id: Any) -> str:
    """为单个项目生成缓存键
    
    Args:
        cache_type: 缓存类型
        item_id: 项目ID
    
    Returns:
        str: 缓存键
    """
    return CacheConfig.get_cache_key(cache_type, f"item:{item_id}")

def cache_key_for_stats(cache_type: CacheType, stat_type: str = "general") -> str:
    """为统计数据生成缓存键
    
    Args:
        cache_type: 缓存类型
        stat_type: 统计类型
    
    Returns:
        str: 缓存键
    """
    return f"stats:{CacheConfig.KEY_PREFIXES[cache_type]}:{stat_type}"

def invalidate_related_caches(cache_types: list[CacheType]):
    """使多个相关缓存失效
    
    Args:
        cache_types: 缓存类型列表
    
    Returns:
        int: 总共删除的缓存数量
    """
    total_deleted = 0
    for cache_type in cache_types:
        try:
            deleted = invalidate_related_cache(cache_type)
            total_deleted += deleted
        except Exception as e:
            # 继续处理其他缓存类型，即使某个失败
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"缓存类型 {cache_type} 失效失败: {e}")
    return total_deleted