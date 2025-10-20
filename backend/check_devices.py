from database import get_db
from models import Device
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///lab_management.db')
Session = sessionmaker(bind=engine)
session = Session()

try:
    devices = session.query(Device).all()
    print(f'数据库中共有 {len(devices)} 个设备')
    
    if devices:
        print('\n设备列表:')
        for device in devices:
            print(f'设备ID: {device.id}, 名称: {device.name}, 型号: {device.model}, 状态: {device.status}')
    else:
        print('数据库中没有设备数据')
        
except Exception as e:
    print(f'查询设备数据时出错: {e}')
    
finally:
    session.close()