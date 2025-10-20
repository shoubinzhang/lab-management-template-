#!/usr/bin/env python3
"""
检查数据库中的试剂数据
"""
import sqlite3
import os

def check_reagent_data():
    """检查数据库中的试剂数据"""
    db_path = "lab_management.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查试剂表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reagents'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ 试剂表不存在")
            return
        
        # 检查试剂数量
        cursor.execute("SELECT COUNT(*) FROM reagents")
        count = cursor.fetchone()[0]
        print(f"✓ 试剂表存在，共有 {count} 条记录")
        
        if count > 0:
            # 显示前几条记录
            cursor.execute("SELECT id, name, category, manufacturer, quantity, unit FROM reagents LIMIT 5")
            reagents = cursor.fetchall()
            
            print("\n前5条试剂记录:")
            for reagent in reagents:
                print(f"  ID: {reagent[0]}, 名称: {reagent[1]}, 类别: {reagent[2]}, 制造商: {reagent[3]}, 数量: {reagent[4]} {reagent[5]}")
        else:
            print("⚠️ 试剂表为空")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    check_reagent_data()