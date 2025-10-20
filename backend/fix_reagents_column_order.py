#!/usr/bin/env python3
"""
修复试剂表列顺序的脚本
"""
import sqlite3
import sys
import os
from datetime import datetime

def fix_reagents_column_order():
    """修复试剂表列顺序"""
    db_path = "lab_management.db"
    backup_path = f"lab_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 创建备份
        print(f"创建数据库备份: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始修复试剂表列顺序...")
        
        # 1. 创建新的试剂表，列顺序与模型定义一致
        create_new_table_sql = """
        CREATE TABLE reagents_new (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            category VARCHAR,
            manufacturer VARCHAR,
            lot_number VARCHAR,
            expiry_date DATETIME,
            quantity FLOAT,
            unit VARCHAR,
            min_threshold REAL DEFAULT 10.0,
            location VARCHAR,
            safety_notes VARCHAR,
            price FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_new_table_sql)
        print("✅ 创建新表成功")
        
        # 2. 复制数据到新表，确保列顺序正确
        copy_data_sql = """
        INSERT INTO reagents_new (
            id, name, category, manufacturer, lot_number, expiry_date, 
            quantity, unit, min_threshold, location, safety_notes, 
            price, created_at, updated_at
        )
        SELECT 
            id, name, category, manufacturer, lot_number, expiry_date, 
            quantity, unit, min_threshold, location, safety_notes, 
            price, created_at, updated_at
        FROM reagents;
        """
        
        cursor.execute(copy_data_sql)
        print("✅ 数据复制成功")
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE reagents;")
        print("✅ 删除旧表成功")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE reagents_new RENAME TO reagents;")
        print("✅ 重命名新表成功")
        
        # 5. 重新创建索引
        indexes = [
            "CREATE INDEX ix_reagents_id ON reagents (id);",
            "CREATE INDEX ix_reagents_name ON reagents (name);",
            "CREATE INDEX idx_reagents_category ON reagents (category);",
            "CREATE INDEX idx_reagents_manufacturer ON reagents (manufacturer);",
            "CREATE INDEX idx_reagents_lot_number ON reagents (lot_number);",
            "CREATE INDEX idx_reagents_expiry_date ON reagents (expiry_date);",
            "CREATE INDEX idx_reagents_location ON reagents (location);",
            "CREATE INDEX idx_reagents_created_at ON reagents (created_at);",
            "CREATE INDEX idx_reagents_expiry_category ON reagents (expiry_date, category);"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                print(f"创建索引时出现警告: {e}")
        
        print("✅ 重新创建索引成功")
        
        # 6. 验证修复结果
        cursor.execute("PRAGMA table_info(reagents);")
        columns = cursor.fetchall()
        
        expected_order = [
            'id', 'name', 'category', 'manufacturer', 'lot_number', 
            'expiry_date', 'quantity', 'unit', 'min_threshold', 
            'location', 'safety_notes', 'price', 'created_at', 'updated_at'
        ]
        
        actual_order = [col[1] for col in columns]
        
        print("\n验证结果:")
        print(f"期望顺序: {expected_order}")
        print(f"实际顺序: {actual_order}")
        
        if actual_order == expected_order:
            print("✅ 列顺序修复成功!")
            
            # 检查数据完整性
            cursor.execute("SELECT COUNT(*) FROM reagents;")
            count = cursor.fetchone()[0]
            print(f"✅ 数据完整性检查: {count} 行数据")
            
            conn.commit()
            conn.close()
            return True
        else:
            print("❌ 列顺序仍然不匹配")
            conn.rollback()
            conn.close()
            return False
        
    except Exception as e:
        print(f"修复过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 恢复备份
        if os.path.exists(backup_path):
            print(f"恢复备份: {backup_path}")
            shutil.copy2(backup_path, db_path)
        
        return False

if __name__ == "__main__":
    success = fix_reagents_column_order()
    if success:
        print("\n🎉 试剂表列顺序修复完成!")
    else:
        print("\n❌ 修复失败，请检查错误信息")
        sys.exit(1)