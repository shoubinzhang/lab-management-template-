import sqlite3
from datetime import datetime, timedelta
import os

# 数据库文件路径
db_path = "lab_management.db"

def recreate_reagents_table():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 删除现有的试剂表
        cursor.execute("DROP TABLE IF EXISTS reagents")
        
        # 创建新的试剂表结构
        cursor.execute("""
        CREATE TABLE reagents (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            category VARCHAR,
            manufacturer VARCHAR,
            lot_number VARCHAR,
            expiry_date DATETIME,
            quantity FLOAT,
            unit VARCHAR,
            location VARCHAR,
            safety_notes VARCHAR,
            price FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 插入示例数据
        sample_reagents = [
            ("氯化钠", "无机盐", "国药集团", "NaCl2024001", datetime.now() + timedelta(days=365), 500.0, "g", "试剂柜A-1", "无特殊安全要求", 25.50),
            ("硫酸", "无机酸", "西陇科学", "H2SO4-2024-002", datetime.now() + timedelta(days=730), 1000.0, "mL", "酸性试剂柜B-2", "强酸，需佩戴防护用品", 45.80),
            ("氢氧化钠", "无机碱", "阿拉丁", "NaOH-AL-003", datetime.now() + timedelta(days=1095), 250.0, "g", "碱性试剂柜C-1", "强碱，避免接触皮肤", 32.00),
            ("乙醇", "有机溶剂", "国药集团", "EtOH-2024-004", datetime.now() + timedelta(days=1460), 2500.0, "mL", "有机溶剂柜D-3", "易燃，远离火源", 68.90),
            ("丙酮", "有机溶剂", "西陇科学", "ACE-XL-005", datetime.now() + timedelta(days=912), 1000.0, "mL", "有机溶剂柜D-1", "易燃易挥发，通风使用", 55.20),
            ("氯仿", "有机溶剂", "阿拉丁", "CHCl3-AL-006", datetime.now() + timedelta(days=548), 500.0, "mL", "有机溶剂柜D-2", "有毒，避免吸入", 89.50),
            ("硝酸银", "无机盐", "国药集团", "AgNO3-2024-007", datetime.now() + timedelta(days=1825), 100.0, "g", "贵金属试剂柜E-1", "避光保存，氧化性强", 156.80),
            ("氨水", "无机碱", "西陇科学", "NH3H2O-XL-008", datetime.now() + timedelta(days=365), 500.0, "mL", "碱性试剂柜C-2", "刺激性气味，通风使用", 28.60),
            ("甲醛", "有机化合物", "阿拉丁", "HCHO-AL-009", datetime.now() + timedelta(days=730), 250.0, "mL", "有机试剂柜F-1", "致癌物质，严格防护", 42.30),
            ("磷酸", "无机酸", "国药集团", "H3PO4-2024-010", datetime.now() + timedelta(days=1095), 1000.0, "mL", "酸性试剂柜B-1", "中强酸，避免接触", 38.70)
        ]
        
        for reagent in sample_reagents:
            cursor.execute("""
            INSERT INTO reagents (name, category, manufacturer, lot_number, expiry_date, quantity, unit, location, safety_notes, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, reagent)
        
        conn.commit()
        print(f"成功重新创建试剂表并添加了 {len(sample_reagents)} 条示例数据")
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM reagents")
        count = cursor.fetchone()[0]
        print(f"试剂表中共有 {count} 条记录")
        
        # 显示前3条记录
        cursor.execute("SELECT id, name, category, manufacturer, quantity, unit FROM reagents LIMIT 3")
        records = cursor.fetchall()
        print("\n前3条记录:")
        for record in records:
            print(f"ID: {record[0]}, 名称: {record[1]}, 类别: {record[2]}, 制造商: {record[3]}, 数量: {record[4]} {record[5]}")
            
    except Exception as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_reagents_table()