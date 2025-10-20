#!/usr/bin/env python3
"""
专门检查试剂表结构的脚本
"""
import sqlite3
import sys
import os

def check_reagents_table():
    """检查试剂表结构"""
    db_path = "lab_management.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 试剂表 (reagents) 详细结构检查 ===\n")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reagents';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("错误: reagents 表不存在!")
            return
        
        # 获取表结构
        cursor.execute("PRAGMA table_info(reagents);")
        columns = cursor.fetchall()
        
        print("列信息:")
        for col in columns:
            cid, name, type_, notnull, default_value, pk = col
            print(f"  {cid}: {name} - {type_} (主键: {bool(pk)}, 非空: {bool(notnull)}, 默认值: {default_value})")
        
        print(f"\n总列数: {len(columns)}")
        
        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM reagents;")
        count = cursor.fetchone()[0]
        print(f"数据行数: {count}")
        
        if count > 0:
            # 获取前几行数据
            cursor.execute("SELECT * FROM reagents LIMIT 3;")
            rows = cursor.fetchall()
            
            print("\n前3行数据:")
            for i, row in enumerate(rows):
                print(f"  行 {i+1}: {row}")
                print(f"    数据长度: {len(row)}")
        
        # 检查是否有缺失的列
        expected_columns = [
            'id', 'name', 'category', 'manufacturer', 'lot_number', 
            'expiry_date', 'quantity', 'unit', 'min_threshold', 
            'location', 'safety_notes', 'price', 'created_at', 'updated_at'
        ]
        
        actual_columns = [col[1] for col in columns]
        
        print(f"\n期望的列: {expected_columns}")
        print(f"实际的列: {actual_columns}")
        
        missing_columns = set(expected_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(expected_columns)
        
        if missing_columns:
            print(f"\n缺失的列: {missing_columns}")
        
        if extra_columns:
            print(f"\n额外的列: {extra_columns}")
        
        if not missing_columns and not extra_columns:
            print("\n✅ 列结构匹配!")
        
        conn.close()
        
    except Exception as e:
        print(f"检查试剂表结构时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_reagents_table()