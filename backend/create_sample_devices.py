#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例设备数据脚本
用于重新填充数据库中的设备信息
"""

from database import SessionLocal, init_database
from models import Device
from datetime import datetime, date
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_devices():
    """创建示例设备数据"""
    db = SessionLocal()
    
    try:
        # 检查现有设备数量
        existing_count = db.query(Device).count()
        logger.info(f"现有设备数量: {existing_count}")
        
        # 如果已有设备数据，先询问是否继续
        if existing_count > 0:
            logger.info("检测到现有设备数据，将添加新的示例设备")
        
        # 示例设备数据
        sample_devices = [
            {
                "name": "高效液相色谱仪",
                "description": "用于分离和分析化合物的高精度仪器",
                "status": "available",
                "location": "分析化学实验室",
                "model": "LC-2030C",
                "serial_number": "LC2030001",
                "responsible_person": "张三",
                "purchase_date": date(2023, 1, 15),
                "warranty_expiry": date(2026, 1, 15),
                "maintenance_interval": 90
            },
            {
                "name": "气相色谱质谱联用仪",
                "description": "用于有机化合物定性定量分析",
                "status": "in_use",
                "location": "有机化学实验室",
                "model": "GCMS-QP2020",
                "serial_number": "GCMS2020001",
                "responsible_person": "李四",
                "purchase_date": date(2022, 6, 10),
                "warranty_expiry": date(2025, 6, 10),
                "maintenance_interval": 120
            },
            {
                "name": "紫外可见分光光度计",
                "description": "用于紫外和可见光区域的光谱分析",
                "status": "available",
                "location": "物理化学实验室",
                "model": "UV-2600",
                "serial_number": "UV2600001",
                "responsible_person": "王五",
                "purchase_date": date(2023, 3, 20),
                "warranty_expiry": date(2026, 3, 20),
                "maintenance_interval": 60
            },
            {
                "name": "原子吸收分光光度计",
                "description": "用于金属元素的定量分析",
                "status": "maintenance",
                "location": "无机化学实验室",
                "model": "AA-7000",
                "serial_number": "AA7000001",
                "responsible_person": "赵六",
                "purchase_date": date(2021, 9, 5),
                "warranty_expiry": date(2024, 9, 5),
                "maintenance_interval": 90
            },
            {
                "name": "核磁共振波谱仪",
                "description": "用于分子结构分析的高端仪器",
                "status": "available",
                "location": "结构化学实验室",
                "model": "NMR-400",
                "serial_number": "NMR400001",
                "responsible_person": "孙七",
                "purchase_date": date(2020, 12, 1),
                "warranty_expiry": date(2025, 12, 1),
                "maintenance_interval": 180
            },
            {
                "name": "电子天平",
                "description": "高精度电子分析天平",
                "status": "available",
                "location": "天平室",
                "model": "XS205",
                "serial_number": "XS205001",
                "responsible_person": "周八",
                "purchase_date": date(2023, 5, 15),
                "warranty_expiry": date(2026, 5, 15),
                "maintenance_interval": 30
            },
            {
                "name": "离心机",
                "description": "高速冷冻离心机",
                "status": "available",
                "location": "生物化学实验室",
                "model": "CF-16RX",
                "serial_number": "CF16RX001",
                "responsible_person": "吴九",
                "purchase_date": date(2022, 11, 8),
                "warranty_expiry": date(2025, 11, 8),
                "maintenance_interval": 90
            },
            {
                "name": "PCR仪",
                "description": "聚合酶链式反应仪",
                "status": "in_use",
                "location": "分子生物学实验室",
                "model": "T100",
                "serial_number": "T100001",
                "responsible_person": "郑十",
                "purchase_date": date(2023, 2, 28),
                "warranty_expiry": date(2026, 2, 28),
                "maintenance_interval": 120
            }
        ]
        
        # 创建设备记录
        for device_data in sample_devices:
            device = Device(**device_data)
            db.add(device)
            logger.info(f"创建设备: {device_data['name']}")
        
        db.commit()
        logger.info(f"成功创建 {len(sample_devices)} 个示例设备")
        
        # 验证创建结果
        device_count = db.query(Device).count()
        logger.info(f"数据库中现有设备数量: {device_count}")
        
    except Exception as e:
        logger.error(f"创建示例设备失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("开始创建示例设备数据...")
    
    try:
        # 初始化数据库
        init_database()
        
        # 创建示例设备
        create_sample_devices()
        
        logger.info("示例设备数据创建完成！")
        
    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())