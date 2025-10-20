#!/usr/bin/env python3
"""
调试试剂查询脚本
"""

from database import SessionLocal, init_database
from models import Reagent
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_reagent_query():
    """调试试剂查询"""
    db = SessionLocal()
    
    try:
        # 直接查询所有试剂
        all_reagents = db.query(Reagent).all()
        print(f"数据库中总试剂数: {len(all_reagents)}")
        
        # 使用count()方法
        total_count = db.query(Reagent).count()
        print(f"使用count()方法: {total_count}")
        
        # 测试分页查询
        page = 1
        per_page = 50
        offset = (page - 1) * per_page
        
        query = db.query(Reagent)
        total = query.count()
        reagents = query.offset(offset).limit(per_page).all()
        
        print(f"分页查询 - 总数: {total}, 当前页数据: {len(reagents)}")
        
        # 显示前几个试剂的信息
        if reagents:
            print("\n前3个试剂:")
            for i, reagent in enumerate(reagents[:3]):
                print(f"  {i+1}. ID: {reagent.id}, 名称: {reagent.name}")
        
        # 测试具体的查询条件
        query_with_order = db.query(Reagent).order_by(Reagent.name.asc())
        total_with_order = query_with_order.count()
        reagents_with_order = query_with_order.offset(offset).limit(per_page).all()
        
        print(f"\n带排序的查询 - 总数: {total_with_order}, 当前页数据: {len(reagents_with_order)}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_reagent_query()