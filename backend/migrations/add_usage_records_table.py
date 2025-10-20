"""
数据库迁移脚本：添加使用记录表
创建时间：2024年
描述：为试剂和耗材领用系统添加使用记录表，用于记录批准后的使用情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import logging

# 数据库配置
DATABASE_URL = "sqlite:///./lab_management.db"

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """执行数据库升级"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 创建使用记录表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                item_type VARCHAR NOT NULL,
                item_id INTEGER NOT NULL,
                item_name VARCHAR NOT NULL,
                quantity_used FLOAT NOT NULL,
                unit VARCHAR NOT NULL,
                user_id INTEGER NOT NULL,
                approved_by_id INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                notes TEXT,
                used_at DATETIME,
                created_at DATETIME,
                FOREIGN KEY(request_id) REFERENCES requests (id),
                FOREIGN KEY(user_id) REFERENCES users (id),
                FOREIGN KEY(approved_by_id) REFERENCES users (id)
            );
            """
            
            connection.execute(text(create_table_sql))
            connection.commit()
            
            logger.info("✅ 使用记录表创建成功")
            
            # 创建索引以提高查询性能
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_usage_records_request_id ON usage_records(request_id);",
                "CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_usage_records_item_type ON usage_records(item_type);",
                "CREATE INDEX IF NOT EXISTS idx_usage_records_used_at ON usage_records(used_at);",
                "CREATE INDEX IF NOT EXISTS idx_usage_records_item_type_id ON usage_records(item_type, item_id);"
            ]
            
            for index_sql in indexes:
                connection.execute(text(index_sql))
            
            connection.commit()
            logger.info("✅ 使用记录表索引创建成功")
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        raise

def downgrade():
    """执行数据库降级（回滚）"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 删除索引
            drop_indexes = [
                "DROP INDEX IF EXISTS idx_usage_records_request_id;",
                "DROP INDEX IF EXISTS idx_usage_records_user_id;",
                "DROP INDEX IF EXISTS idx_usage_records_item_type;",
                "DROP INDEX IF EXISTS idx_usage_records_used_at;",
                "DROP INDEX IF EXISTS idx_usage_records_item_type_id;"
            ]
            
            for drop_sql in drop_indexes:
                connection.execute(text(drop_sql))
            
            # 删除表
            connection.execute(text("DROP TABLE IF EXISTS usage_records;"))
            connection.commit()
            
            logger.info("✅ 使用记录表删除成功")
            
    except Exception as e:
        logger.error(f"❌ 数据库回滚失败: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("执行数据库回滚...")
        downgrade()
        print("回滚完成")
    else:
        print("执行数据库迁移...")
        upgrade()
        print("迁移完成")