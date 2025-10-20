import sqlite3

conn = sqlite3.connect('lab_management.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM devices')
device_count = cursor.fetchone()[0]
print(f'数据库中设备总数: {device_count}')

cursor.execute('SELECT id, name, serial_number FROM devices LIMIT 5')
devices = cursor.fetchall()
print('前5个设备:')
for device in devices:
    print(f'  ID: {device[0]}, Name: {device[1]}, Serial: {device[2]}')

conn.close()