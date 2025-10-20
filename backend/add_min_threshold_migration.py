#!/usr/bin/env python3
"""
数据库迁移脚本：为试剂表添加 min_threshold 字段
"""

import sqlite3
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_min_threshold_column():
    """为试剂表添加 min_threshold 字段"""
    db_path = Path(__file__).parent / "lab_management.db"
    
    if not db_path.exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(reagents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'min_threshold' in columns:
            logger.info("min_threshold 字段已存在，跳过迁移")
            return True
        
        # 添加 min_threshold 字段
        logger.info("正在添加 min_threshold 字段...")
        cursor.execute("""
            ALTER TABLE reagents 
            ADD COLUMN min_threshold REAL DEFAULT 10.0
        """)
        
        # 为现有记录设置默认值
        cursor.execute("""
            UPDATE reagents 
            SET min_threshold = 10.0 
            WHERE min_threshold IS NULL
        """)
        
        conn.commit()
        logger.info("成功添加 min_threshold 字段")
        
        # 验证字段添加成功
        cursor.execute("PRAGMA table_info(reagents)")
        columns = cursor.fetchall()
        logger.info("当前试剂表结构:")
        for column in columns:
            logger.info(f"  {column}")
        
        return True
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_min_threshold_column()
    if success:
        logger.info("数据库迁移完成")
    else:
        logger.error("数据库迁移失败")
        exit(1)