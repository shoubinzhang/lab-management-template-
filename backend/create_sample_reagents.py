#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例试剂数据脚本
用于填充数据库中的试剂信息
"""

from database import SessionLocal, init_database
from models import Reagent
from datetime import datetime, date
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_reagents():
    """创建示例试剂数据"""
    db = SessionLocal()
    
    try:
        # 检查现有试剂数量
        existing_count = db.query(Reagent).count()
        logger.info(f"现有试剂数量: {existing_count}")
        
        # 如果已有试剂数据，先询问是否继续
        if existing_count > 0:
            logger.info("检测到现有试剂数据，将添加新的示例试剂")
        
        # 示例试剂数据
        sample_reagents = [
            {
                "name": "氯化钠",
                "quantity": 500.0,
                "unit": "g",
                "expiry_date": datetime(2025, 12, 31)
            },
            {
                "name": "硫酸",
                "quantity": 1000.0,
                "unit": "mL",
                "expiry_date": datetime(2026, 6, 30)
            },
            {
                "name": "氢氧化钠",
                "quantity": 250.0,
                "unit": "g",
                "expiry_date": datetime(2025, 8, 15)
            },
            {
                "name": "盐酸",
                "quantity": 500.0,
                "unit": "mL",
                "expiry_date": datetime(2026, 3, 20)
            },
            {
                "name": "乙醇",
                "quantity": 2000.0,
                "unit": "mL",
                "expiry_date": datetime(2025, 10, 10)
            },
            {
                "name": "丙酮",
                "quantity": 1500.0,
                "unit": "mL",
                "expiry_date": datetime(2025, 9, 25)
            },
            {
                "name": "硝酸银",
                "quantity": 100.0,
                "unit": "g",
                "expiry_date": datetime(2026, 1, 15)
            },
            {
                "name": "碳酸钙",
                "quantity": 300.0,
                "unit": "g",
                "expiry_date": datetime(2027, 5, 30)
            },
            {
                "name": "硫酸铜",
                "quantity": 200.0,
                "unit": "g",
                "expiry_date": datetime(2025, 11, 20)
            },
            {
                "name": "氯化钾",
                "quantity": 400.0,
                "unit": "g",
                "expiry_date": datetime(2026, 4, 10)
            }
        ]
        
        # 创建试剂记录
        created_count = 0
        for reagent_data in sample_reagents:
            # 检查是否已存在同名试剂
            existing_reagent = db.query(Reagent).filter(
                Reagent.name == reagent_data["name"]
            ).first()
            
            if existing_reagent:
                logger.info(f"试剂 '{reagent_data['name']}' 已存在，跳过创建")
                continue
            
            # 创建新试剂
            reagent = Reagent(**reagent_data)
            db.add(reagent)
            created_count += 1
            logger.info(f"创建试剂: {reagent_data['name']}")
        
        # 提交更改
        db.commit()
        logger.info(f"成功创建 {created_count} 个示例试剂")
        
        # 显示最终统计
        total_count = db.query(Reagent).count()
        logger.info(f"数据库中总试剂数量: {total_count}")
        
    except Exception as e:
        logger.error(f"创建示例试剂失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("开始创建示例试剂数据...")
    
    try:
        # 初始化数据库
        init_database()
        
        # 创建示例试剂
        create_sample_reagents()
        
        logger.info("示例试剂数据创建完成！")
        
    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())