import sqlite3
import json

conn = sqlite3.connect('lab_management.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute('PRAGMA table_info(devices)')
columns = cursor.fetchall()
print('设备表结构:')
for col in columns:
    print(col)

# 检查设备数据
cursor.execute('SELECT * FROM devices')
devices = cursor.fetchall()
print('\n设备数据:')
for device in devices:
    print(device)

conn.close()