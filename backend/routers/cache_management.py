# backend/routers/cache_management.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from backend.database import get_db
from backend.auth import require_admin
from backend.models import User
from backend.redis_cache import redis_cache
from backend.redis_config import redis_config
from backend.cache_config import CacheType, CacheConfig, invalidate_related_cache
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/cache", tags=["cache-management"])

# Pydantic模型
class CacheStats(BaseModel):
    """缓存统计信息"""
    connected: bool
    used_memory: str
    connected_clients: int
    total_commands_processed: int
    keyspace_hits: int
    keyspace_misses: int
    hit_rate: float
    uptime_in_seconds: int
    error: Optional[str] = None

class CacheKeyInfo(BaseModel):
    """缓存键信息"""
    key: str
    ttl: int
    size: Optional[int] = None
    type: str

class CacheOperationResult(BaseModel):
    """缓存操作结果"""
    success: bool
    message: str
    affected_keys: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class WarmupRequest(BaseModel):
    """缓存预热请求"""
    cache_types: Optional[List[str]] = None  # 指定要预热的缓存类型
    force: bool = False  # 是否强制重新预热已存在的缓存

class CacheKeyPattern(BaseModel):
    """缓存键模式"""
    pattern: str
    description: Optional[str] = None

# 路由处理函数
@router.get("/stats", response_model=CacheStats)
def get_cache_stats(
    current_user: User = Depends(require_admin)
):
    """获取Redis缓存统计信息"""
    try:
        stats = redis_cache.get_stats()
        return CacheStats(**stats)
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

@router.get("/keys", response_model=List[CacheKeyInfo])
def get_cache_keys(
    pattern: str = "*",
    limit: int = 100,
    current_user: User = Depends(require_admin)
):
    """获取缓存键列表"""
    if not redis_cache.is_connected:
        raise HTTPException(status_code=503, detail="Redis未连接")
    
    try:
        # 获取匹配的键
        keys = redis_cache.redis_client.keys(pattern)
        
        # 限制返回数量
        if len(keys) > limit:
            keys = keys[:limit]
        
        key_infos = []
        for key in keys:
            try:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                ttl = redis_cache.ttl(key_str)
                key_type = redis_cache.redis_client.type(key).decode('utf-8')
                
                # 尝试获取键的大小（仅对字符串类型）
                size = None
                if key_type == 'string':
                    try:
                        size = redis_cache.redis_client.strlen(key)
                    except:
                        pass
                
                key_infos.append(CacheKeyInfo(
                    key=key_str,
                    ttl=ttl,
                    size=size,
                    type=key_type
                ))
            except Exception as e:
                logger.warning(f"获取键 {key} 信息失败: {e}")
                continue
        
        return key_infos
        
    except Exception as e:
        logger.error(f"获取缓存键列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存键列表失败: {str(e)}")

@router.get("/key/{key_name}")
def get_cache_value(
    key_name: str,
    current_user: User = Depends(require_admin)
):
    """获取指定缓存键的值"""
    try:
        value = redis_cache.get(key_name)
        if value is None:
            raise HTTPException(status_code=404, detail="缓存键不存在")
        
        return {
            "key": key_name,
            "value": value,
            "ttl": redis_cache.ttl(key_name),
            "exists": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存值失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存值失败: {str(e)}")

@router.delete("/key/{key_name}", response_model=CacheOperationResult)
def delete_cache_key(
    key_name: str,
    current_user: User = Depends(require_admin)
):
    """删除指定缓存键"""
    try:
        success = redis_cache.delete(key_name)
        
        return CacheOperationResult(
            success=success,
            message=f"缓存键 '{key_name}' {'删除成功' if success else '不存在或删除失败'}",
            affected_keys=1 if success else 0
        )
        
    except Exception as e:
        logger.error(f"删除缓存键失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除缓存键失败: {str(e)}")

@router.delete("/pattern", response_model=CacheOperationResult)
def delete_cache_pattern(
    request: CacheKeyPattern,
    current_user: User = Depends(require_admin)
):
    """删除匹配模式的缓存键"""
    try:
        deleted_count = redis_cache.delete_pattern(request.pattern)
        
        return CacheOperationResult(
            success=True,
            message=f"删除了 {deleted_count} 个匹配模式 '{request.pattern}' 的缓存键",
            affected_keys=deleted_count,
            details={"pattern": request.pattern}
        )
        
    except Exception as e:
        logger.error(f"删除缓存模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除缓存模式失败: {str(e)}")

@router.delete("/type/{cache_type}", response_model=CacheOperationResult)
def clear_cache_by_type(
    cache_type: str,
    current_user: User = Depends(require_admin)
):
    """清除指定类型的所有缓存"""
    try:
        # 验证缓存类型
        try:
            cache_type_enum = CacheType(cache_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的缓存类型: {cache_type}")
        
        deleted_count = invalidate_related_cache(cache_type_enum)
        
        return CacheOperationResult(
            success=True,
            message=f"清除了 {deleted_count} 个 '{cache_type}' 类型的缓存项",
            affected_keys=deleted_count,
            details={"cache_type": cache_type}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除缓存类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除缓存类型失败: {str(e)}")

@router.delete("/all", response_model=CacheOperationResult)
def clear_all_cache(
    current_user: User = Depends(require_admin)
):
    """清除所有缓存"""
    try:
        success = redis_cache.flush_all()
        
        return CacheOperationResult(
            success=success,
            message="所有缓存已清除" if success else "清除缓存失败"
        )
        
    except Exception as e:
        logger.error(f"清除所有缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除所有缓存失败: {str(e)}")

@router.post("/warmup", response_model=CacheOperationResult)
def warmup_cache(
    request: WarmupRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """预热缓存"""
    try:
        warmed_count = 0
        details = {}
        
        # 确定要预热的缓存类型
        cache_types_to_warmup = []
        if request.cache_types:
            for cache_type_str in request.cache_types:
                try:
                    cache_types_to_warmup.append(CacheType(cache_type_str))
                except ValueError:
                    logger.warning(f"无效的缓存类型: {cache_type_str}")
        else:
            # 默认预热所有支持的类型
            cache_types_to_warmup = [
                CacheType.REAGENTS,
                CacheType.CONSUMABLES,
                CacheType.DEVICES
            ]
        
        # 按优先级排序
        cache_types_to_warmup.sort(key=lambda ct: CacheConfig.get_warmup_priority(ct))
        
        for cache_type in cache_types_to_warmup:
            if not CacheConfig.should_warmup(cache_type):
                continue
            
            type_warmed = 0
            endpoints = CacheConfig.get_warmup_endpoints(cache_type)
            
            for endpoint in endpoints:
                try:
                    # 这里可以根据不同的端点执行不同的预热逻辑
                    if cache_type == CacheType.REAGENTS:
                        type_warmed += _warmup_reagents(db, current_user, request.force)
                    elif cache_type == CacheType.CONSUMABLES:
                        type_warmed += _warmup_consumables(db, current_user, request.force)
                    elif cache_type == CacheType.DEVICES:
                        type_warmed += _warmup_devices(db, current_user, request.force)
                    
                except Exception as e:
                    logger.error(f"预热 {cache_type.value} 失败: {e}")
                    continue
            
            details[cache_type.value] = type_warmed
            warmed_count += type_warmed
        
        return CacheOperationResult(
            success=True,
            message=f"缓存预热完成，预热了 {warmed_count} 个缓存项",
            affected_keys=warmed_count,
            details=details
        )
        
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(status_code=500, detail=f"缓存预热失败: {str(e)}")

@router.get("/config", response_model=Dict[str, Any])
def get_cache_config(
    current_user: User = Depends(require_admin)
):
    """获取缓存配置信息"""
    try:
        config_info = {
            "cache_types": {
                cache_type.value: {
                    "ttl": CacheConfig.get_ttl(cache_type),
                    "key_prefix": CacheConfig.KEY_PREFIXES.get(cache_type),
                    "warmup_enabled": CacheConfig.should_warmup(cache_type),
                    "warmup_priority": CacheConfig.get_warmup_priority(cache_type),
                    "warmup_endpoints": CacheConfig.get_warmup_endpoints(cache_type),
                    "invalidation_patterns": CacheConfig.get_invalidation_patterns(cache_type)
                }
                for cache_type in CacheType
            },
            "redis_connection": {
                "connected": redis_cache.is_connected,
                "host": "localhost",  # 可以从配置中获取
                "port": 6379,
                "db": 0
            }
        }
        
        return config_info
        
    except Exception as e:
        logger.error(f"获取缓存配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存配置失败: {str(e)}")

@router.post("/test", response_model=CacheOperationResult)
def test_cache_connection(
    current_user: User = Depends(require_admin)
):
    """测试缓存连接"""
    try:
        # 测试写入
        test_key = "cache_test:connection"
        test_value = {"timestamp": datetime.utcnow().isoformat(), "test": True}
        
        write_success = redis_cache.set(test_key, test_value, 60)
        if not write_success:
            return CacheOperationResult(
                success=False,
                message="缓存写入测试失败"
            )
        
        # 测试读取
        read_value = redis_cache.get(test_key)
        if read_value != test_value:
            return CacheOperationResult(
                success=False,
                message="缓存读取测试失败"
            )
        
        # 测试删除
        delete_success = redis_cache.delete(test_key)
        if not delete_success:
            return CacheOperationResult(
                success=False,
                message="缓存删除测试失败"
            )
        
        return CacheOperationResult(
            success=True,
            message="缓存连接测试成功",
            details={
                "write_test": "passed",
                "read_test": "passed",
                "delete_test": "passed"
            }
        )
        
    except Exception as e:
        logger.error(f"缓存连接测试失败: {e}")
        return CacheOperationResult(
            success=False,
            message=f"缓存连接测试失败: {str(e)}"
        )

# 辅助函数
def _warmup_reagents(db: Session, current_user: dict, force: bool = False) -> int:
    """预热试剂缓存"""
    from backend.routers.cached_reagents import get_reagents, get_reagent_categories
    
    warmed = 0
    
    # 预热首页数据
    cache_key = "reagents:list:" + "7d865e959b2466918c9863afca942d0f"  # 默认参数的hash
    if force or not redis_cache.exists(cache_key):
        get_reagents(db=db, current_user=current_user)
        warmed += 1
    
    # 预热类别数据
    categories_key = CacheConfig.get_cache_key(CacheType.REAGENTS, "categories")
    if force or not redis_cache.exists(categories_key):
        get_reagent_categories(db=db, current_user=current_user)
        warmed += 1
    
    return warmed

def _warmup_consumables(db: Session, current_user: dict, force: bool = False) -> int:
    """预热耗材缓存"""
    # 这里可以添加耗材的预热逻辑
    return 0

def _warmup_devices(db: Session, current_user: dict, force: bool = False) -> int:
    """预热设备缓存"""
    # 这里可以添加设备的预热逻辑
    return 0