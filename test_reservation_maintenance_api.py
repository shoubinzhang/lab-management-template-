import requests
import json
import time

# 服务器URL
base_url = "http://localhost:8000"

# 登录凭证（根据实际情况修改）
login_credentials = {
    "username": "admin",  # 默认管理员用户名
    "password": "admin123"  # 默认管理员密码
}

def login():
    """登录获取JWT令牌"""
    print("正在尝试登录...")
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_credentials)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"登录成功，获取到令牌: {token}")
            return token
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            # 如果默认凭证失败，尝试使用其他常见凭证
            print("尝试使用其他常见凭证...")
            other_credentials = {
                "username": "user",
                "password": "user123"
            }
            response = requests.post(f"{base_url}/api/auth/login", json=other_credentials)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print(f"登录成功，获取到令牌: {token}")
                return token
            else:
                print(f"登录失败: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"登录过程发生错误: {str(e)}")
        return None

def get_devices(token):
    """获取设备列表"""
    print("\n正在获取设备列表...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{base_url}/api/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            print(f"设备API返回: {type(devices)}")
            print(f"设备API内容: {devices}")  # 打印完整的返回内容以便调试
            
            # 返回原始响应，让调用者决定如何处理
            return devices
        else:
            print(f"获取设备列表失败: {response.status_code} - {response.text}")
            # 显示完整的响应内容以进行调试
            print(f"完整响应: {response.text}")
            return None
    except Exception as e:
        print(f"获取设备列表过程发生错误: {str(e)}")
        return None

def create_reservation(token, device_id):
    """创建设备预约"""
    print(f"\n正在为设备 {device_id} 创建预约...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 构建预约时间（当前时间加1小时开始，持续2小时）
    current_time = int(time.time())
    start_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(current_time + 3600))  # 1小时后开始
    end_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(current_time + 7200))    # 2小时后结束
    
    reservation_data = {
        "device_id": device_id,
        "start_time": start_time,
        "end_time": end_time,
        "purpose": "测试设备预约功能",
        "notes": "这是一个API测试预约"
    }
    
    try:
        response = requests.post(f"{base_url}/api/devices/{device_id}/reservations", 
                               headers=headers, 
                               json=reservation_data)
        if response.status_code == 200:
            reservation = response.json()
            print(f"预约创建成功: {reservation}")
            return reservation
        else:
            print(f"预约创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"创建预约过程发生错误: {str(e)}")
        return None

def get_my_reservations(token):
    """获取当前用户的预约列表"""
    print("\n正在获取当前用户的预约列表...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{base_url}/api/devices/reservations/my", headers=headers)
        if response.status_code == 200:
            reservations = response.json()
            print(f"获取到 {len(reservations)} 条预约记录")
            if reservations:
                print("预约记录:")
                for i, reservation in enumerate(reservations):
                    device_name = reservation.get('device', {}).get('name', '未知设备')
                    start_time = reservation.get('start_time', '未知时间')
                    status = reservation.get('status', '未知状态')
                    print(f"{i+1}. {device_name} - {start_time} ({status})")
            return reservations
        else:
            print(f"获取预约列表失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取预约列表过程发生错误: {str(e)}")
        return None

def create_maintenance_record(token, device_id):
    """创建设备维护记录"""
    print(f"\n正在为设备 {device_id} 创建维护记录...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 获取今天的日期
    today = time.strftime('%Y-%m-%d', time.localtime())
    
    maintenance_data = {
        "device_id": device_id,
        "maintenance_type": "routine",
        "description": "定期维护测试",
        "performed_by": "系统管理员",
        "maintenance_date": today,
        "cost": 100.50,
        "notes": "这是一个API测试维护记录"
    }
    
    try:
        response = requests.post(f"{base_url}/api/devices/{device_id}/maintenance", 
                               headers=headers, 
                               json=maintenance_data)
        if response.status_code == 200:
            maintenance = response.json()
            print(f"维护记录创建成功: {maintenance}")
            return maintenance
        else:
            print(f"维护记录创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"创建维护记录过程发生错误: {str(e)}")
        return None

def get_maintenance_history(token, device_id=None):
    """获取设备维护历史"""
    print("\n正在获取设备维护历史...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        if device_id:
            url = f"{base_url}/api/devices/{device_id}/maintenance"
        else:
            url = f"{base_url}/api/devices/maintenance-needed/list"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            maintenance_records = response.json()
            print(f"获取到 {len(maintenance_records)} 条维护记录")
            if maintenance_records:
                print("维护记录:")
                for i, record in enumerate(maintenance_records[:5]):  # 只显示前5个
                    device_name = record.get('device', {}).get('name', '未知设备') or record.get('name', '未知设备')
                    date = record.get('maintenance_date', '未知日期') or record.get('next_maintenance', '未知日期')
                    type = record.get('maintenance_type', '未知类型')
                    print(f"{i+1}. {device_name} - {date} ({type})")
            return maintenance_records
        else:
            print(f"获取维护历史失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取维护历史过程发生错误: {str(e)}")
        return None

def main():
    # 登录获取令牌
    token = login()
    if not token:
        print("无法获取令牌，测试终止。")
        return
    
    # 获取设备列表
    devices_response = get_devices(token)
    if not devices_response:
        print("无法获取设备列表，测试终止。")
        return
    
    # 尝试从响应中提取设备ID（针对不同的响应格式）
    test_device_id = None
    
    # 1. 如果响应是字典，尝试直接获取ID（可能是单个设备）
    if isinstance(devices_response, dict):
        if 'id' in devices_response:
            test_device_id = devices_response['id']
            device_name = devices_response.get('name', '未知设备')
            print(f"\n选择单个设备 '{device_name}' (ID: {test_device_id}) 进行测试")
        else:
            # 2. 尝试从字典的特定键中提取设备列表
            possible_device_keys = ['devices', 'data', 'result', 'items']
            found = False
            for key in possible_device_keys:
                if key in devices_response and isinstance(devices_response[key], list) and devices_response[key]:
                    devices = devices_response[key]
                    test_device_id = devices[0].get('id')
                    device_name = devices[0].get('name', '未知设备')
                    print(f"\n从 '{key}' 键中提取到 {len(devices)} 台设备")
                    print(f"选择第一个设备 '{device_name}' (ID: {test_device_id}) 进行测试")
                    found = True
                    break
            
            if not found:
                print("\n警告: 无法从响应中提取有效的设备列表或设备ID")
                print("尝试使用直接的API调用跳过设备列表获取步骤")
                # 3. 如果上述方法都失败，尝试使用硬编码的设备ID（仅用于测试）
                # 假设系统中有ID为1的设备
                test_device_id = 1
                print(f"\n使用默认设备ID: {test_device_id} 进行测试")
    
    # 4. 如果响应是列表，选择第一个设备
    elif isinstance(devices_response, list) and devices_response:
        test_device_id = devices_response[0].get('id')
        device_name = devices_response[0].get('name', '未知设备')
        print(f"\n选择第一个设备 '{device_name}' (ID: {test_device_id}) 进行测试")
    
    if not test_device_id:
        print("无法获取有效的设备ID，测试终止。")
        return
    
    # 创建设备预约（尝试API调用）
    reservation = create_reservation(token, test_device_id)
    
    # 获取当前用户的预约列表
    my_reservations = get_my_reservations(token)
    
    # 创建设备维护记录（尝试API调用）
    maintenance = create_maintenance_record(token, test_device_id)
    
    # 获取设备维护历史
    maintenance_history = get_maintenance_history(token)
    
    # 测试完成
    print("\n测试完成！")
    print("\nAPI测试总结:")
    print(f"- 登录: {'成功' if token else '失败'}")
    print(f"- 获取设备列表: {'成功' if devices_response else '失败'}")
    print(f"- 创建设备预约: {'成功' if reservation else '失败'}")
    print(f"- 获取预约列表: {'成功' if my_reservations else '失败'}")
    print(f"- 创建设备维护记录: {'成功' if maintenance else '失败'}")
    print(f"- 获取维护历史: {'成功' if maintenance_history else '失败'}")

if __name__ == "__main__":
    main()