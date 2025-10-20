#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除示例设备数据脚本
只删除我创建的示例设备，保留原始数据
"""

from database import SessionLocal, init_database
from models import Device
from datetime import datetime, date
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "扫描电子显微镜",
            "电子天平",
            "离心机",
            "PCR仪"
        ]
        
        deleted_count = 0
        for device in all_devices:
            if device.name in sample_device_names:
                logger.info(f"删除示例设备: ID={device.id}, 名称={device.name}, 型号={device.model}")
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
                logger.info(f"  - ID: {device.id}, 名称: {device.name}, 型号: {device.model}, 状态: {device.status}")
                if device.description:
                    logger.info(f"    描述: {device.description}")
        else:
            logger.info("数据库中没有剩余设备")
        
    except Exception as e:
        logger.error(f"清除示例设备失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("开始清除示例设备数据...")
    
    try:
        # 初始化数据库
        init_database()
        
        # 清除示例设备
        clear_sample_devices()
        
        logger.info("示例设备清除完成！")
        
    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())