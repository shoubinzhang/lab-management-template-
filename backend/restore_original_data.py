#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复原始设备数据脚本
从localStorage备份或其他数据源恢复原始设备数据
"""

from database import SessionLocal, init_database
from models import Device
from datetime import datetime, date
import logging
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_backup_sources():
    """检查可能的数据备份源"""
    logger.info("检查可能的数据备份源...")
    
    # 检查是否有数据库备份文件
    backup_files = []
    
    # 检查当前目录和上级目录的备份文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if 'backup' in file.lower() and (file.endswith('.db') or file.endswith('.sql') or file.endswith('.json')):
                backup_files.append(os.path.join(root, file))
    
    if backup_files:
        logger.info(f"发现备份文件: {backup_files}")
    else:
        logger.info("未发现数据库备份文件")
    
    return backup_files

def restore_from_database_backup(backup_file):
    """从数据库备份文件恢复数据"""
    logger.info(f"尝试从备份文件恢复数据: {backup_file}")
    
    if backup_file.endswith('.json'):
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"JSON备份文件包含 {len(data)} 条记录")
                    return data
        except Exception as e:
            logger.error(f"读取JSON备份文件失败: {e}")
    
    return None

def clear_sample_devices():
    """清除示例设备数据（保留原始数据）"""
    db = SessionLocal()
    
    try:
        # 查询所有设备
        all_devices = db.query(Device).all()
        logger.info(f"当前数据库中有 {len(all_devices)} 个设备")
        
        # 识别并删除示例设备（基于特定的名称模式）
        sample_device_names = [
            "高效液相色谱仪",
            "气相色谱质谱联用仪", 
            "原子吸收分光光度计",
            "紫外可见分光光度计",
            "红外光谱仪",
            "核磁共振波谱仪",
            "X射线衍射仪",
            "扫描电子显微镜"
        ]
        
        deleted_count = 0
        for device in all_devices:
            if device.name in sample_device_names:
                logger.info(f"删除示例设备: {device.name}")
                db.delete(device)
                deleted_count += 1
        
        db.commit()
        logger.info(f"已删除 {deleted_count} 个示例设备")
        
        # 显示剩余设备
        remaining_devices = db.query(Device).all()
        logger.info(f"剩余设备数量: {len(remaining_devices)}")
        
        if remaining_devices:
            logger.info("剩余设备列表:")
            for device in remaining_devices:
                logger.info(f"  - ID: {device.id}, 名称: {device.name}, 型号: {device.model}")
        
    except Exception as e:
        logger.error(f"清除示例设备失败: {e}")
        db.rollback()
    finally:
        db.close()

def show_current_devices():
    """显示当前数据库中的所有设备"""
    db = SessionLocal()
    
    try:
        devices = db.query(Device).all()
        logger.info(f"\n当前数据库中的设备 (共 {len(devices)} 个):")
        logger.info("-" * 80)
        
        for device in devices:
            logger.info(f"ID: {device.id:2d} | 名称: {device.name:20s} | 型号: {device.model or 'N/A':15s} | 状态: {device.status or 'N/A'}")
            if device.description:
                logger.info(f"     描述: {device.description}")
            if device.serial_number:
                logger.info(f"     序列号: {device.serial_number}")
            logger.info("-" * 80)
            
    except Exception as e:
        logger.error(f"查询设备数据失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("开始恢复原始设备数据...")
    
    try:
        # 初始化数据库
        init_database()
        
        # 显示当前设备状态
        show_current_devices()
        
        # 检查备份源
        backup_files = check_backup_sources()
        
        # 询问用户操作
        print("\n请选择操作:")
        print("1. 清除示例设备数据（保留原始数据）")
        print("2. 显示当前设备列表")
        print("3. 检查localStorage备份提示")
        print("0. 退出")
        
        choice = input("请输入选择 (0-3): ").strip()
        
        if choice == '1':
            confirm = input("确认要清除示例设备数据吗？(y/N): ").strip().lower()
            if confirm == 'y':
                clear_sample_devices()
            else:
                logger.info("操作已取消")
        elif choice == '2':
            show_current_devices()
        elif choice == '3':
            print("\n=== localStorage备份恢复提示 ===")
            print("如果您的原始数据存储在浏览器的localStorage中，请按以下步骤操作:")
            print("1. 打开前端页面 (http://localhost:3000)")
            print("2. 按F12打开开发者工具")
            print("3. 切换到Console标签")
            print("4. 输入以下命令查看localStorage数据:")
            print("   localStorage.getItem('devices_backup')")
            print("   localStorage.getItem('devices')")
            print("5. 如果有数据，可以通过前端的数据迁移功能恢复")
            print("6. 或者将数据复制保存为JSON文件，然后使用批量导入功能")
        elif choice == '0':
            logger.info("退出程序")
        else:
            logger.info("无效选择")
        
    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())