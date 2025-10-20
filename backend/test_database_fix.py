#!/usr/bin/env python3
"""
测试数据库修复是否成功
"""
import sqlite3
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Reagent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_structure():
    """测试数据库结构是否正确"""
    print("=== 测试数据库结构修复 ===")
    
    # 1. 测试SQLite直接查询
    print("\n1. 测试SQLite直接查询...")
    try:
        conn = sqlite3.connect("lab_management.db")
        cursor = conn.cursor()
        
        # 查询试剂表结构
        cursor.execute("PRAGMA table_info(reagents)")
        columns = cursor.fetchall()
        
        print("试剂表列结构:")
        for i, col in enumerate(columns):
            print(f"  {i}: {col[1]} - {col[2]}")
        
        # 查询前3行数据
        cursor.execute("SELECT * FROM reagents LIMIT 3")
        rows = cursor.fetchall()
        
        print(f"\n前3行数据 (每行{len(rows[0]) if rows else 0}列):")
        for i, row in enumerate(rows):
            print(f"  行 {i+1}: 长度={len(row)}")
        
        conn.close()
        print("✅ SQLite直接查询成功")
        
    except Exception as e:
        print(f"❌ SQLite直接查询失败: {e}")
        return False
    
    # 2. 测试SQLAlchemy ORM查询
    print("\n2. 测试SQLAlchemy ORM查询...")
    try:
        db = SessionLocal()
        
        # 查询试剂数量
        count = db.query(Reagent).count()
        print(f"试剂总数: {count}")
        
        # 查询前3个试剂
        reagents = db.query(Reagent).limit(3).all()
        
        print("前3个试剂:")
        for i, reagent in enumerate(reagents):
            print(f"  {i+1}. {reagent.name} - {reagent.category}")
            print(f"      最小阈值: {reagent.min_threshold}")
            print(f"      位置: {reagent.location}")
        
        db.close()
        print("✅ SQLAlchemy ORM查询成功")
        
    except Exception as e:
        print(f"❌ SQLAlchemy ORM查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_specific_queries():
    """测试特定的查询操作"""
    print("\n=== 测试特定查询操作 ===")
    
    try:
        db = SessionLocal()
        
        # 测试分页查询
        print("\n1. 测试分页查询...")
        reagents = db.query(Reagent).offset(0).limit(5).all()
        print(f"分页查询结果: {len(reagents)} 个试剂")
        
        # 测试筛选查询
        print("\n2. 测试筛选查询...")
        filtered = db.query(Reagent).filter(Reagent.category.like('%无机%')).all()
        print(f"无机类试剂: {len(filtered)} 个")
        
        # 测试排序查询
        print("\n3. 测试排序查询...")
        sorted_reagents = db.query(Reagent).order_by(Reagent.name).limit(3).all()
        print("按名称排序的前3个试剂:")
        for reagent in sorted_reagents:
            print(f"  - {reagent.name}")
        
        db.close()
        print("✅ 所有查询操作成功")
        return True
        
    except Exception as e:
        print(f"❌ 查询操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试数据库修复结果...")
    
    structure_ok = test_database_structure()
    queries_ok = test_specific_queries()
    
    if structure_ok and queries_ok:
        print("\n🎉 数据库修复测试全部通过!")
        print("IndexError问题已解决，数据库结构正常。")
    else:
        print("\n❌ 数据库修复测试失败")
        print("仍存在问题，需要进一步检查。")