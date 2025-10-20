from database import get_db
from models import Device, DeviceMaintenance, DeviceReservation, ExperimentRecord
from sqlalchemy.orm import Session

def safe_delete_devices(device_ids: list, db: Session):
    """
    安全删除设备，先删除所有关联数据
    """
    print(f"准备删除设备: {device_ids}")
    
    # 1. 删除设备维护记录
    maintenance_records = db.query(DeviceMaintenance).filter(
        DeviceMaintenance.device_id.in_(device_ids)
    ).all()
    
    if maintenance_records:
        print(f"删除 {len(maintenance_records)} 条维护记录")
        for record in maintenance_records:
            print(f"  - 设备ID: {record.device_id}, 维护类型: {record.maintenance_type}, 日期: {record.maintenance_date}")
            db.delete(record)
    
    # 2. 删除设备预约记录
    reservation_records = db.query(DeviceReservation).filter(
        DeviceReservation.device_id.in_(device_ids)
    ).all()
    
    if reservation_records:
        print(f"删除 {len(reservation_records)} 条预约记录")
        for record in reservation_records:
            print(f"  - 设备ID: {record.device_id}, 状态: {record.status}")
            db.delete(record)
    
    # 3. 删除实验记录
    experiment_records = db.query(ExperimentRecord).filter(
        ExperimentRecord.device_id.in_(device_ids)
    ).all()
    
    if experiment_records:
        print(f"删除 {len(experiment_records)} 条实验记录")
        for record in experiment_records:
            print(f"  - 设备ID: {record.device_id}, 描述: {record.description}")
            db.delete(record)
    
    # 4. 提交关联数据删除
    db.commit()
    print("关联数据删除完成")
    
    # 5. 删除设备本身
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    deleted_devices = []
    
    for device in devices:
        print(f"删除设备: ID={device.id}, 名称={device.name}, 型号={device.model}")
        deleted_devices.append({
            'id': device.id,
            'name': device.name,
            'model': device.model
        })
        db.delete(device)
    
    # 6. 提交设备删除
    db.commit()
    print(f"成功删除 {len(deleted_devices)} 个设备")
    
    return {
        'deleted_count': len(deleted_devices),
        'deleted_devices': deleted_devices,
        'maintenance_records_deleted': len(maintenance_records),
        'reservation_records_deleted': len(reservation_records),
        'experiment_records_deleted': len(experiment_records)
    }

def test_fix_deletion():
    """
    测试修复删除功能
    """
    db = next(get_db())
    device_ids = [57, 56, 58]
    
    try:
        result = safe_delete_devices(device_ids, db)
        print("\n删除结果:")
        print(f"删除设备数量: {result['deleted_count']}")
        print(f"删除维护记录数量: {result['maintenance_records_deleted']}")
        print(f"删除预约记录数量: {result['reservation_records_deleted']}")
        print(f"删除实验记录数量: {result['experiment_records_deleted']}")
        print("\n删除的设备:")
        for device in result['deleted_devices']:
            print(f"  - ID: {device['id']}, 名称: {device['name']}, 型号: {device['model']}")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"删除失败: {e}")
        return False
    finally:
        db.close()

if __name__ == '__main__':
    test_fix_deletion()