#!/usr/bin/env python3
"""
数据库直接查询测试脚本
绕过缓存直接查询数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from models import Reagent
from sqlalchemy.orm import Session

def test_database_direct():
    print("=== 数据库直接查询测试 ===\n")
    
    try:
        # 获取数据库会话
        db_gen = get_db()
        db: Session = next(db_gen)
        
        # 1. 查询所有试剂
        print("1. 查询数据库中的所有试剂...")
        reagents = db.query(Reagent).all()
        print(f"数据库中试剂总数: {len(reagents)}")
        
        if reagents:
            print("试剂列表:")
            for reagent in reagents[-5:]:  # 显示最后5个
                print(f"  - ID: {reagent.id}, 名称: {reagent.name}, 类别: {reagent.category}, 库存: {reagent.quantity}")
        else:
            print("数据库中没有试剂数据")
            
        # 2. 查询试剂总数
        total_count = db.query(Reagent).count()
        print(f"\n2. 试剂总数（count查询）: {total_count}")
        
        # 3. 查询最新的试剂
        latest_reagents = db.query(Reagent).order_by(Reagent.id.desc()).limit(3).all()
        print(f"\n3. 最新的3个试剂:")
        for reagent in latest_reagents:
            print(f"  - ID: {reagent.id}, 名称: {reagent.name}, 创建时间: {reagent.created_at}")
            
        # 4. 按名称搜索测试试剂
        test_reagents = db.query(Reagent).filter(Reagent.name.like('%测试试剂%')).all()
        print(f"\n4. 测试试剂数量: {len(test_reagents)}")
        for reagent in test_reagents:
            print(f"  - ID: {reagent.id}, 名称: {reagent.name}")
            
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_database_direct()