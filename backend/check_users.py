import sqlite3
import json

conn = sqlite3.connect('lab_management.db')
cursor = conn.cursor()

# 检查用户表结构
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()
print('用户表结构:')
for col in columns:
    print(col)

# 检查用户数据
cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users')
users = cursor.fetchall()
print('\n用户数据:')
for user in users:
    print(user)

# 检查是否有默认管理员用户
cursor.execute('SELECT * FROM users WHERE username = "admin"')
admin_user = cursor.fetchone()
print('\n管理员用户:')
print(admin_user)

conn.close()