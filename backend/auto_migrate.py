#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动数据迁移脚本
帮助用户从localStorage迁移设备数据到数据库
"""

from database import SessionLocal, init_database
from models import Device
from datetime import datetime, date
import logging
import json
import requests
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_backend_status():
    """检查后端服务状态"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend_status():
    """检查前端服务状态"""
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        return response.status_code == 200
    except:
        return False

def get_admin_token():
    """获取管理员token"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post('http://localhost:8000/api/auth/login', json=login_data)
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception as e:
        logger.error(f"获取管理员token失败: {e}")
    return None

def trigger_migration():
    """触发前端数据迁移"""
    token = get_admin_token()
    if not token:
        logger.error("无法获取管理员token")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        # 检查是否有需要迁移的数据
        response = requests.get('http://localhost:8000/api/devices', headers=headers)
        if response.status_code == 200:
            devices = response.json()
            logger.info(f"当前数据库中有 {len(devices)} 个设备")
            
            # 如果设备数量很少，可能需要迁移
            if len(devices) <= 1:
                logger.info("检测到设备数量较少，建议进行数据迁移")
                return True
            else:
                logger.info("数据库中已有足够的设备数据")
                return False
    except Exception as e:
        logger.error(f"检查设备数据失败: {e}")
    
    return False

def show_migration_instructions():
    """显示迁移指导"""
    print("\n" + "="*60)
    print("           设备数据迁移指导")
    print("="*60)
    print()
    print("当前状态:")
    print(f"  ✓ 后端服务: {'运行中' if check_backend_status() else '未运行'}")
    print(f"  ✓ 前端服务: {'运行中' if check_frontend_status() else '未运行'}")
    print(f"  ✓ 数据库: 已清理示例数据，保留原始设备")
    print()
    print("迁移步骤:")
    print("1. 打开浏览器访问: http://localhost:3000")
    print("2. 使用管理员账户登录:")
    print("   用户名: admin")
    print("   密码: admin123")
    print("3. 系统会自动检测localStorage中的数据")
    print("4. 如果有数据，会显示迁移对话框")
    print("5. 点击'开始迁移'按钮")
    print("6. 等待迁移完成")
    print()
    print("手动检查localStorage数据:")
    print("1. 在浏览器中按F12打开开发者工具")
    print("2. 切换到Console标签")
    print("3. 输入: localStorage.getItem('devices')")
    print("4. 输入: localStorage.getItem('devices_backup')")
    print()
    print("如果没有自动迁移对话框:")
    print("1. 在Console中输入: window.location.reload()")
    print("2. 或者手动导出localStorage数据为JSON文件")
    print("3. 使用设备管理页面的导入功能")
    print()
    print("="*60)
    print("迁移完成后，您的所有原始设备数据将恢复到数据库中")
    print("="*60)

def main():
    """主函数"""
    logger.info("开始自动数据迁移流程...")
    
    try:
        # 初始化数据库
        init_database()
        
        # 检查服务状态
        if not check_backend_status():
            logger.error("后端服务未运行，请先启动后端服务")
            return 1
        
        if not check_frontend_status():
            logger.error("前端服务未运行，请先启动前端服务")
            return 1
        
        # 检查是否需要迁移
        needs_migration = trigger_migration()
        
        # 显示迁移指导
        show_migration_instructions()
        
        if needs_migration:
            print("\n建议立即进行数据迁移以恢复您的原始设备数据。")
        else:
            print("\n如果您确定需要恢复更多数据，请按照上述步骤进行迁移。")
        
        # 等待用户操作
        print("\n按任意键继续...")
        input()
        
    except Exception as e:
        logger.error(f"迁移流程失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())