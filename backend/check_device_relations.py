from database import get_db
from models import DeviceMaintenance, DeviceReservation, ExperimentRecord

def check_device_relations():
    db = next(get_db())
    device_ids = [57, 56, 58]
    
    print('检查设备关联数据:')
    print(f'目标设备ID: {device_ids}')
    print('=' * 50)
    
    # 检查设备维护记录
    print('设备维护记录:')
    maintenance = db.query(DeviceMaintenance).filter(
        DeviceMaintenance.device_id.in_(device_ids)
    ).all()
    print(f'找到 {len(maintenance)} 条维护记录')
    for m in maintenance:
        print(f'  设备ID: {m.device_id}, 维护类型: {m.maintenance_type}, 日期: {m.maintenance_date}')
    
    print('\n设备预约记录:')
    reservations = db.query(DeviceReservation).filter(
        DeviceReservation.device_id.in_(device_ids)
    ).all()
    print(f'找到 {len(reservations)} 条预约记录')
    for r in reservations:
        print(f'  设备ID: {r.device_id}, 状态: {r.status}, 开始时间: {r.start_time}')
    
    print('\n实验记录:')
    experiments = db.query(ExperimentRecord).filter(
        ExperimentRecord.device_id.in_(device_ids)
    ).all()
    print(f'找到 {len(experiments)} 条实验记录')
    for e in experiments:
        print(f'  设备ID: {e.device_id}, 描述: {e.description}')
    
    db.close()
    
    # 返回是否有关联数据
    has_relations = len(maintenance) > 0 or len(reservations) > 0 or len(experiments) > 0
    return has_relations, len(maintenance), len(reservations), len(experiments)

if __name__ == '__main__':
    check_device_relations()