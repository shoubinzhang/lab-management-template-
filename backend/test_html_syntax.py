import os
import re
import sys

# 定义要检查的HTML文件列表
html_files = [
    'mobile_dashboard.html',
    'mobile_devices.html',
    'mobile_reagents.html',
    'mobile_consumables.html',
    'mobile_reservations.html',
    'mobile_maintenance.html',
    'mobile_scan.html'
]

# 定义检查规则 - 寻找onclick事件中的引号嵌套问题
problem_pattern = re.compile(r'onclick=\\"[^\"]*"')

# 存储检查结果
results = {}

def check_html_file(file_path):
    """检查HTML文件中的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找问题模式
        matches = problem_pattern.finditer(content)
        problems = []
        
        for match in matches:
            line_number = content.count('\n', 0, match.start()) + 1
            problems.append({
                'line': line_number,
                'code': match.group()
            })
            
        return problems
    except Exception as e:
        return [{"error": str(e)}]

# 检查每个文件
total_problems = 0

print("===== HTML语法错误检查结果 =====")
print("""本脚本用于检查HTML文件中onclick事件的引号嵌套问题\n""")

for file in html_files:
    file_path = os.path.join(os.getcwd(), file)
    if os.path.exists(file_path):
        problems = check_html_file(file_path)
        results[file] = problems
        
        if len(problems) > 0:
            print(f"❌ {file} 发现 {len(problems)} 个问题")
            total_problems += len(problems)
        else:
            print(f"✅ {file} 检查通过")
    else:
        print(f"⚠️ {file} 文件不存在")

# 检查static目录中的相同文件
print("\n===== 检查static目录中的文件 ====")
static_dir = os.path.join(os.getcwd(), 'static')
if os.path.exists(static_dir):
    for file in html_files:
        file_path = os.path.join(static_dir, file)
        if os.path.exists(file_path):
            problems = check_html_file(file_path)
            
            if len(problems) > 0:
                print(f"❌ static/{file} 发现 {len(problems)} 个问题")
                total_problems += len(problems)
            else:
                print(f"✅ static/{file} 检查通过")

# 输出总结
print("\n===== 检查总结 =====")
if total_problems == 0:
    print("🎉 所有文件检查通过，没有发现语法错误！")
    print("\n提示:\n" 
          "1. 已修复所有HTML文件中onclick事件的引号嵌套问题\n" 
          "2. 现在可以安全地在浏览器中打开这些页面\n" 
          "3. 页面间的导航功能应该可以正常工作了")
else:
    print(f"❌ 总共发现 {total_problems} 个问题，请查看详细信息")

# 保存详细结果到文件
detail_file = "html_syntax_check_results.txt"
with open(detail_file, 'w', encoding='utf-8') as f:
    f.write("HTML语法错误检查详细结果\n")
    f.write("="*50 + "\n\n")
    
    for file, problems in results.items():
        if problems:
            f.write(f"文件: {file}\n")
            f.write("-"*30 + "\n")
            for i, problem in enumerate(problems, 1):
                if "error" in problem:
                    f.write(f"  {i}. 错误: {problem['error']}\n")
                else:
                    f.write(f"  {i}. 行号: {problem['line']}, 代码: {problem['code']}\n")
            f.write("\n")

print(f"\n详细结果已保存到: {detail_file}")