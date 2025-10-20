import sqlite3
import json

conn = sqlite3.connect('lab_management.db')
cursor = conn.cursor()

# 检查试剂表结构
cursor.execute('PRAGMA table_info(reagents)')
columns = cursor.fetchall()
print('试剂表结构:')
for col in columns:
    print(col)

# 检查试剂数据
cursor.execute('SELECT * FROM reagents')
reagents = cursor.fetchall()
print(f'\n试剂数据总数: {len(reagents)}')
if reagents:
    print('\n试剂数据:')
    for reagent in reagents[:10]:  # 只显示前10条
        print(reagent)
    if len(reagents) > 10:
        print(f'... 还有 {len(reagents) - 10} 条数据')
else:
    print('\n试剂表中没有数据')

conn.close()