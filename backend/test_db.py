#!/usr/bin/env python3
"""测试数据库连接和表结构"""

from database import engine
from sqlalchemy import text

def test_database():
    try:
        # 连接数据库
        conn = engine.connect()
        print("✅ 数据库连接成功")
        
        # 查询所有表
        result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
        tables = [row[0] for row in result]
        
        print("\n📊 数据库表列表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查核心表是否存在
        core_tables = ['users', 'devices', 'reagents', 'consumables', 'experiment_records']
        missing_tables = [table for table in core_tables if table not in tables]
        
        if missing_tables:
            print(f"\n⚠️  缺少核心表: {missing_tables}")
        else:
            print("\n✅ 所有核心表都存在")
        
        # 测试用户表数据
        if 'users' in tables:
            user_count = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
            print(f"\n👥 用户表记录数: {user_count}")
        
        conn.close()
        print("\n✅ 数据库测试完成")
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")

if __name__ == "__main__":
    test_database()