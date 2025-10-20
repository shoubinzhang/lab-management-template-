import os
import re

# 定义项目根目录
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# 移动页面文件列表
MOBILE_FILES = [
    'mobile_index.html',
    'mobile_devices.html',
    'mobile_reagents.html', 
    'mobile_consumables.html',
    'mobile_scan.html',
    'mobile_user.html',
    'mobile_login_final.html',
    'mobile_test_nav.html',
    'mobile_test_fixed.html'
]

# 定义需要修复的导航模式
NAV_PATTERNS = [
    # 匹配href属性
    (r'href="([^"]+)"', lambda m: f'href="{fix_path(m.group(1))}"'),
    # 匹配src属性
    (r'src="([^"]+)"', lambda m: f'src="{fix_path(m.group(1))}"'),
    # 匹配window.location
    (r'window\.location\s*=\s*["\']([^"\']+)["\']', lambda m: f'window.location = "{fix_path(m.group(1))}"'),
    # 匹配window.location.href
    (r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', lambda m: f'window.location.href = "{fix_path(m.group(1))}"'),
    # 匹配navigateTo函数调用
    (r'navigateTo\(\s*["\']([^"\']+)["\']\s*\)', lambda m: f'navigateTo("{fix_path(m.group(1))}")'),
]

# 需要忽略的路径前缀
IGNORE_PREFIXES = [
    'http://', 'https://', 'data:', 'mailto:', 'tel:', '/static/', '#',
    'javascript:', 'blob:', 'about:', 'chrome:', 'file:', 'ftp:'
]

# 修复路径函数
def fix_path(path):
    # 检查是否应该忽略此路径
    for prefix in IGNORE_PREFIXES:
        if path.startswith(prefix):
            return path
    
    # 检查是否已经有/static/前缀
    if not path.startswith('/static/'):
        # 如果路径以/开头，移除它
        if path.startswith('/'):
            path = path[1:]
        # 添加/static/前缀
        return f'/static/{path}'
    
    return path

# 修复单个文件
def fix_file(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False, 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        # 应用所有修复模式
        for pattern, replace_func in NAV_PATTERNS:
            # 查找所有匹配项
            matches = list(re.finditer(pattern, content))
            if matches:
                # 从后往前替换，避免位置偏移
                for match in reversed(matches):
                    old_str = match.group(0)
                    new_str = replace_func(match)
                    if old_str != new_str:
                        content = content[:match.start()] + new_str + content[match.end():]
                        changes += 1
        
        # 如果有变化，保存文件
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已修复 {changes} 处导航路径: {file_path}")
        else:
            print(f"无需修复: {file_path}")
        
        return True, changes
    except Exception as e:
        print(f"修复文件时出错 {file_path}: {str(e)}")
        return False, 0

# 主函数
def main():
    print("=== 导航路径修复工具 ===")
    print(f"开始扫描并修复 {BACKEND_DIR} 目录下的移动页面文件...\n")
    
    total_files = 0
    fixed_files = 0
    total_changes = 0
    
    for file_name in MOBILE_FILES:
        file_path = os.path.join(BACKEND_DIR, file_name)
        total_files += 1
        success, changes = fix_file(file_path)
        if success:
            fixed_files += 1
            total_changes += changes
    
    # 扫描目录中可能遗漏的移动页面文件
    print("\n扫描目录中其他可能的移动页面文件...")
    for file_name in os.listdir(BACKEND_DIR):
        if file_name.startswith('mobile_') and file_name.endswith('.html') and file_name not in MOBILE_FILES:
            file_path = os.path.join(BACKEND_DIR, file_name)
            total_files += 1
            success, changes = fix_file(file_path)
            if success:
                fixed_files += 1
                total_changes += changes
    
    print(f"\n=== 修复结果摘要 ===")
    print(f"扫描文件总数: {total_files}")
    print(f"成功处理文件数: {fixed_files}")
    print(f"修复导航路径总数: {total_changes}")
    print("\n所有导航路径已修复完成！请使用 http://localhost:8000/static/[文件名] 格式访问页面。")

if __name__ == "__main__":
    main()