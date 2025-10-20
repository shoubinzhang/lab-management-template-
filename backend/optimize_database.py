#!/usr/bin/env python3
"""
数据库优化脚本
为关键字段添加索引，优化查询性能
"""

import sqlite3
import os
from datetime import datetime

def create_indexes(db_path):
    """
    为数据库表创建索引以优化查询性能
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"开始优化数据库: {db_path}")
        print(f"优化时间: {datetime.now()}")
        
        # 设备表索引
        indexes = [
            # 设备表索引
            "CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)",
            "CREATE INDEX IF NOT EXISTS idx_devices_location ON devices(location)",
            "CREATE INDEX IF NOT EXISTS idx_devices_serial_number ON devices(serial_number)",
            "CREATE INDEX IF NOT EXISTS idx_devices_next_maintenance ON devices(next_maintenance)",
            "CREATE INDEX IF NOT EXISTS idx_devices_created_at ON devices(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_devices_responsible_person ON devices(responsible_person)",
            
            # 试剂表索引
            "CREATE INDEX IF NOT EXISTS idx_reagents_category ON reagents(category)",
            "CREATE INDEX IF NOT EXISTS idx_reagents_manufacturer ON reagents(manufacturer)",
            "CREATE INDEX IF NOT EXISTS idx_reagents_lot_number ON reagents(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_reagents_expiry_date ON reagents(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_reagents_location ON reagents(location)",
            "CREATE INDEX IF NOT EXISTS idx_reagents_created_at ON reagents(created_at)",
            
            # 耗材表索引
            "CREATE INDEX IF NOT EXISTS idx_consumables_name ON consumables(name)",
            "CREATE INDEX IF NOT EXISTS idx_consumables_quantity ON consumables(quantity)",
            
            # 用户表索引（已有username和email的唯一索引）
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # 实验记录表索引
            "CREATE INDEX IF NOT EXISTS idx_experiment_records_user_id ON experiment_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_experiment_records_device_id ON experiment_records(device_id)",
            "CREATE INDEX IF NOT EXISTS idx_experiment_records_start_time ON experiment_records(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_experiment_records_end_time ON experiment_records(end_time)",
            
            # 设备维护记录表索引
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_device_id ON device_maintenance(device_id)",
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_type ON device_maintenance(maintenance_type)",
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_date ON device_maintenance(maintenance_date)",
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_status ON device_maintenance(status)",
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_performed_by ON device_maintenance(performed_by)",
            
            # 设备预约表索引
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_device_id ON device_reservations(device_id)",
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_user_id ON device_reservations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_start_time ON device_reservations(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_end_time ON device_reservations(end_time)",
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_status ON device_reservations(status)",
            
            # 通知表索引
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires_at ON notifications(expires_at)",
            
            # 知识库表索引
            "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)",
            
            # 反馈表索引
            "CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status)",
            
            # WebSocket连接表索引
            "CREATE INDEX IF NOT EXISTS idx_websocket_connections_user_id ON websocket_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_websocket_connections_is_active ON websocket_connections(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_websocket_connections_last_ping ON websocket_connections(last_ping)",
            
            # 角色权限相关索引
            "CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource)",
            "CREATE INDEX IF NOT EXISTS idx_permissions_action ON permissions(action)",
            "CREATE INDEX IF NOT EXISTS idx_roles_is_active ON roles(is_active)",
        ]
        
        # 复合索引（多字段组合查询优化）
        composite_indexes = [
            # 设备状态和位置组合查询
            "CREATE INDEX IF NOT EXISTS idx_devices_status_location ON devices(status, location)",
            # 试剂过期日期和类别组合查询
            "CREATE INDEX IF NOT EXISTS idx_reagents_expiry_category ON reagents(expiry_date, category)",
            # 设备预约时间范围查询
            "CREATE INDEX IF NOT EXISTS idx_device_reservations_time_range ON device_reservations(start_time, end_time)",
            # 通知未读状态和用户组合查询
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read)",
            # 设备维护日期和状态组合查询
            "CREATE INDEX IF NOT EXISTS idx_device_maintenance_date_status ON device_maintenance(maintenance_date, status)",
        ]
        
        # 执行单字段索引
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✓ 创建索引: {index_sql.split('idx_')[1].split(' ON')[0]}")
            except sqlite3.Error as e:
                print(f"✗ 索引创建失败: {e}")
        
        # 执行复合索引
        for index_sql in composite_indexes:
            try:
                cursor.execute(index_sql)
                print(f"✓ 创建复合索引: {index_sql.split('idx_')[1].split(' ON')[0]}")
            except sqlite3.Error as e:
                print(f"✗ 复合索引创建失败: {e}")
        
        # 提交更改
        conn.commit()
        print("\n数据库索引优化完成！")
        
        # 分析数据库统计信息
        cursor.execute("ANALYZE")
        conn.commit()
        print("数据库统计信息更新完成！")
        
    except Exception as e:
        print(f"数据库优化过程中发生错误: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_database_info(db_path):
    """
    显示数据库信息和索引列表
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\n=== 数据库表信息 ===")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: {count} 条记录")
        
        # 获取所有索引
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        
        print("\n=== 数据库索引信息 ===")
        for index in indexes:
            index_name, table_name = index
            print(f"{table_name}.{index_name}")
            
    except Exception as e:
        print(f"获取数据库信息时发生错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 数据库文件路径
    db_path = "lab_management.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        exit(1)
    
    print("实验室管理系统 - 数据库优化工具")
    print("=" * 50)
    
    # 显示优化前的数据库信息
    print("优化前的数据库状态:")
    show_database_info(db_path)
    
    # 执行数据库优化
    create_indexes(db_path)
    
    # 显示优化后的数据库信息
    print("\n优化后的数据库状态:")
    show_database_info(db_path)
    
    print("\n数据库优化完成！查询性能已得到提升。")