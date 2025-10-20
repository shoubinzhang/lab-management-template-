#!/usr/bin/env python3
"""
检查数据库表结构的脚本
"""
import sqlite3
import sys
import os

def check_table_structure():
    """检查数据库表结构"""
    db_path = "lab_management.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== 数据库表结构检查 ===\n")
        
        for table in tables:
            table_name = table[0]
            print(f"表名: {table_name}")
            print("-" * 50)
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("列信息:")
            for col in columns:
                cid, name, type_, notnull, default_value, pk = col
                print(f"  {name}: {type_} (主键: {bool(pk)}, 非空: {bool(notnull)}, 默认值: {default_value})")
            
            # 获取外键信息
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print("外键:")
                for fk in foreign_keys:
                    id_, seq, table, from_, to, on_update, on_delete, match = fk
                    print(f"  {from_} -> {table}.{to}")
            
            # 获取索引信息
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            
            if indexes:
                print("索引:")
                for idx in indexes:
                    seq, name, unique, origin, partial = idx
                    print(f"  {name} (唯一: {bool(unique)})")
            
            print("\n")
        
        conn.close()
        
    except Exception as e:
        print(f"检查数据库结构时出错: {e}")

if __name__ == "__main__":
    check_table_structure()