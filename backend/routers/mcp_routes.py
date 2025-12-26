"""MCP工具API路由
提供RESTful接口访问MCP工具功能
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from backend.mcp_tools import (
    create_entities, create_relations, add_observations,
    delete_entities, delete_observations, delete_relations,
    read_graph, search_nodes, open_nodes
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["MCP工具"])

# 请求/响应模型
class EntityRequest(BaseModel):
    name: str
    entityType: str
    observations: List[str]

class RelationRequest(BaseModel):
    from_entity: str
    to_entity: str
    relationType: str

class ObservationRequest(BaseModel):
    entityName: str
    contents: List[str]

class SearchRequest(BaseModel):
    query: str

@router.post("/entities")
async def create_entities_endpoint(entities: List[EntityRequest]):
    """创建实体"""
    try:
        entities_data = [
            {
                "name": e.name,
                "entityType": e.entityType,
                "observations": e.observations
            }
            for e in entities
        ]
        result = create_entities(entities_data)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"创建实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/relations")
async def create_relations_endpoint(relations: List[RelationRequest]):
    """创建关系"""
    try:
        relations_data = [
            {
                "from": r.from_entity,
                "to": r.to_entity,
                "relationType": r.relationType
            }
            for r in relations
        ]
        result = create_relations(relations_data)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"创建关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/observations")
async def add_observations_endpoint(observations: List[ObservationRequest]):
    """添加观察内容"""
    try:
        observations_data = [
            {
                "entityName": obs.entityName,
                "contents": obs.contents
            }
            for obs in observations
        ]
        result = add_observations(observations_data)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"添加观察失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entities")
async def delete_entities_endpoint(entity_names: List[str]):
    """删除实体"""
    try:
        result = delete_entities(entity_names)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"删除实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/observations")
async def delete_observations_endpoint(deletions: List[Dict[str, Any]]):
    """删除观察内容"""
    try:
        result = delete_observations(deletions)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"删除观察失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/relations")
async def delete_relations_endpoint(relations: List[RelationRequest]):
    """删除关系"""
    try:
        relations_data = [
            {
                "from": r.from_entity,
                "to": r.to_entity,
                "relationType": r.relationType
            }
            for r in relations
        ]
        result = delete_relations(relations_data)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"删除关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
async def read_graph_endpoint():
    """读取完整知识图谱"""
    try:
        result = read_graph()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"读取图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_nodes_endpoint(search: SearchRequest):
    """搜索节点"""
    try:
        result = search_nodes(search.query)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nodes")
async def open_nodes_endpoint(names: List[str]):
    """获取特定节点详情"""
    try:
        result = open_nodes(names)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))