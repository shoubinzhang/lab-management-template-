from database import get_db
from models import Device, DeviceMaintenance, DeviceReservation, ExperimentRecord, User
from sqlalchemy.orm import Session
from datetime import datetime, date
import requests
import json

def create_test_data():
    """
    创建测试数据
    """
    db = next(get_db())
    
    try:
        # 创建测试设备
        test_devices = [
            Device(
                name="测试设备A",
                description="用于测试删除功能的设备A",
                status="available",
                location="实验室A",
                model="TEST-A001",
                serial_number="SN-A001",
                purchase_date=date(2024, 1, 1),
                warranty_expiry=date(2025, 1, 1),
                maintenance_interval=90,
                responsible_person="测试人员"
            ),
            Device(
                name="测试设备B",
                description="用于测试删除功能的设备B",
                status="available",
                location="实验室B",
                model="TEST-B001",
                serial_number="SN-B001",
                purchase_date=date(2024, 2, 1),
                warranty_expiry=date(2025, 2, 1),
                maintenance_interval=90,
                responsible_person="测试人员"
            )
        ]
        
        for device in test_devices:
            db.add(device)
        
        db.commit()
        
        # 获取创建的设备ID
        device_a = db.query(Device).filter(Device.name == "测试设备A").first()
        device_b = db.query(Device).filter(Device.name == "测试设备B").first()
        
        print(f"创建测试设备: A (ID: {device_a.id}), B (ID: {device_b.id})")
        
        # 为设备A创建维护记录
        maintenance_record = DeviceMaintenance(
            device_id=device_a.id,
            maintenance_type="定期维护",
            maintenance_date=date.today(),
            description="测试维护记录",
            cost=100.0,
            performed_by="测试维护员"
        )
        db.add(maintenance_record)
        
        # 为设备B创建预约记录（需要先有用户）
        user = db.query(User).first()
        if user:
            reservation_record = DeviceReservation(
                device_id=device_b.id,
                user_id=user.id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                purpose="测试预约",
                status="confirmed"
            )
            db.add(reservation_record)
        
        db.commit()
        
        print("测试数据创建完成")
        print(f"设备A维护记录: 1条")
        print(f"设备B预约记录: {1 if user else 0}条")
        
        return [device_a.id, device_b.id]
        
    except Exception as e:
        db.rollback()
        print(f"创建测试数据失败: {e}")
        return []
    finally:
        db.close()

def test_api_deletion(device_ids):
    """
    测试API批量删除功能
    """
    if not device_ids:
        print("没有设备ID可供测试")
        return
    
    # 首先需要登录获取token
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录
        login_response = requests.post(login_url, data=login_data)
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code}")
            print(login_response.text)
            return
        
        token = login_response.json().get("access_token")
        if not token:
            print("未获取到访问令牌")
            return
        
        print("登录成功，获取到访问令牌")
        
        # 测试批量删除API
        delete_url = "http://127.0.0.1:8000/devices/bulk-delete"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print(f"测试批量删除设备: {device_ids}")
        
        delete_response = requests.post(
            delete_url,
            headers=headers,
            json=device_ids
        )
        
        print(f"删除响应状态码: {delete_response.status_code}")
        print(f"删除响应内容: {delete_response.text}")
        
        if delete_response.status_code == 200:
            result = delete_response.json()
            print("\n删除成功!")
            print(f"删除设备数量: {result.get('deleted_count', 0)}")
            print(f"删除维护记录数量: {result.get('maintenance_records_deleted', 0)}")
            print(f"删除预约记录数量: {result.get('reservation_records_deleted', 0)}")
            print(f"删除实验记录数量: {result.get('experiment_records_deleted', 0)}")
        else:
            print(f"删除失败: {delete_response.text}")
            
    except Exception as e:
        print(f"API测试失败: {e}")

def main():
    print("=== 测试修复后的批量删除功能 ===")
    
    # 1. 创建测试数据
    print("\n1. 创建测试数据...")
    device_ids = create_test_data()
    
    if not device_ids:
        print("测试数据创建失败，退出测试")
        return
    
    # 2. 测试API删除
    print("\n2. 测试API批量删除...")
    test_api_deletion(device_ids)
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()