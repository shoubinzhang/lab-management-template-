import os
import shutil

# 定义源目录和目标目录
source_dir = r'c:\lab-management-app\backend'
target_dir = r'c:\lab-management-app\backend\static'

# 确保目标目录存在
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 列出所有需要复制的HTML文件
html_files = [
    'mobile_access_guide.html',
    'mobile_consumables.html',
    'mobile_dashboard.html',
    'mobile_devices.html',
    'mobile_index.html',
    'mobile_login_final.html',
    'mobile_login_test.html',
    'mobile_maintenance.html',
    'mobile_reagents.html',
    'mobile_reservations.html',
    'mobile_scan.html',
    'mobile_test_debug.html',
    'mobile_test_fixed.html',
    'mobile_test_nav.html',
    'mobile_user.html',
    'simple_test.html'
]

# 复制文件
print(f"开始复制HTML文件到 {target_dir}")
success_count = 0
failed_count = 0
failed_files = []

for html_file in html_files:
    source_path = os.path.join(source_dir, html_file)
    target_path = os.path.join(target_dir, html_file)
    try:
        # 使用shutil.copy2保留文件元数据
        shutil.copy2(source_path, target_path)
        print(f"✓ 成功复制: {html_file}")
        success_count += 1
    except Exception as e:
        print(f"✗ 复制失败: {html_file} - 错误: {str(e)}")
        failed_count += 1
        failed_files.append(html_file)

# 打印总结
print(f"\n复制总结:")
print(f"成功复制: {success_count} 个文件")
print(f"复制失败: {failed_count} 个文件")
if failed_files:
    print(f"失败的文件: {', '.join(failed_files)}")

print("\n复制操作完成！")