#!/usr/bin/env python3
"""
数据库迁移初始化脚本
用于初始化Alembic迁移环境并创建初始迁移
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {cmd}")
        logger.error(f"错误输出: {e.stderr}")
        raise

def init_alembic_migration():
    """初始化Alembic迁移环境"""
    logger.info("初始化数据库迁移环境...")
    
    # 获取项目路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_dir = project_root / "backend"
    
    # 切换到后端目录
    os.chdir(backend_dir)
    
    # 检查是否已经初始化
    alembic_dir = backend_dir / "alembic"
    if alembic_dir.exists() and (alembic_dir / "versions").exists():
        logger.info("Alembic已经初始化，跳过初始化步骤")
    else:
        logger.info("初始化Alembic...")
        # 如果alembic目录不完整，重新初始化
        if alembic_dir.exists():
            import shutil
            shutil.rmtree(alembic_dir)
        
        run_command("alembic init alembic", cwd=backend_dir)
        logger.info("Alembic初始化完成")
        
        # 复制我们的配置文件
        logger.info("更新Alembic配置...")
        # env.py和script.py.mako已经通过之前的脚本创建
    
    # 创建versions目录
    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir(exist_ok=True)
    
    # 检查是否存在迁移文件
    existing_migrations = list(versions_dir.glob("*.py"))
    
    if not existing_migrations:
        logger.info("创建初始迁移...")
        
        # 创建初始迁移
        try:
            output = run_command(
                'alembic revision --autogenerate -m "Initial migration"',
                cwd=backend_dir
            )
            logger.info("初始迁移创建成功")
            logger.info(output)
        except Exception as e:
            logger.warning(f"自动生成迁移失败: {e}")
            logger.info("尝试创建空的初始迁移...")
            
            # 如果自动生成失败，创建空的迁移
            output = run_command(
                'alembic revision -m "Initial migration"',
                cwd=backend_dir
            )
            logger.info("空的初始迁移创建成功")
            logger.info(output)
    else:
        logger.info(f"发现{len(existing_migrations)}个现有迁移文件")
    
    # 显示当前迁移状态
    try:
        logger.info("检查迁移状态...")
        output = run_command("alembic current", cwd=backend_dir)
        logger.info(f"当前迁移状态: {output.strip() if output.strip() else '未应用任何迁移'}")
        
        # 显示迁移历史
        output = run_command("alembic history", cwd=backend_dir)
        if output.strip():
            logger.info("迁移历史:")
            for line in output.strip().split('\n'):
                logger.info(f"  {line}")
        else:
            logger.info("暂无迁移历史")
            
    except Exception as e:
        logger.warning(f"无法获取迁移状态: {e}")

def create_migration_script():
    """创建迁移管理脚本"""
    script_content = '''
#!/usr/bin/env python3
"""
数据库迁移管理脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd):
    """执行Alembic命令"""
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='数据库迁移管理')
    parser.add_argument('action', choices=[
        'current', 'history', 'upgrade', 'downgrade', 
        'revision', 'show', 'stamp'
    ], help='迁移操作')
    parser.add_argument('--message', '-m', help='迁移消息')
    parser.add_argument('--revision', '-r', help='目标版本')
    parser.add_argument('--autogenerate', action='store_true', help='自动生成迁移')
    
    args = parser.parse_args()
    
    if args.action == 'current':
        run_command('alembic current')
    elif args.action == 'history':
        run_command('alembic history --verbose')
    elif args.action == 'upgrade':
        revision = args.revision or 'head'
        run_command(f'alembic upgrade {revision}')
    elif args.action == 'downgrade':
        revision = args.revision or '-1'
        run_command(f'alembic downgrade {revision}')
    elif args.action == 'revision':
        message = args.message or 'New migration'
        if args.autogenerate:
            run_command(f'alembic revision --autogenerate -m "{message}"')
        else:
            run_command(f'alembic revision -m "{message}"')
    elif args.action == 'show':
        revision = args.revision or 'head'
        run_command(f'alembic show {revision}')
    elif args.action == 'stamp':
        revision = args.revision or 'head'
        run_command(f'alembic stamp {revision}')

if __name__ == '__main__':
    main()
'''
    
    script_path = Path(__file__).parent / "migrate.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_path, 0o755)
    logger.info(f"迁移管理脚本已创建: {script_path}")

def main():
    """主函数"""
    logger.info("🔄 Lab Management System - 数据库迁移初始化")
    logger.info("=" * 50)
    
    try:
        # 初始化Alembic迁移
        init_alembic_migration()
        
        # 创建迁移管理脚本
        create_migration_script()
        
        logger.info("\n✅ 数据库迁移初始化完成！")
        logger.info("\n📋 下一步操作:")
        logger.info("   1. 检查生成的迁移文件")
        logger.info("   2. 运行迁移: python scripts/migrate.py upgrade")
        logger.info("   3. 创建新迁移: python scripts/migrate.py revision --autogenerate -m '描述'")
        logger.info("   4. 查看迁移状态: python scripts/migrate.py current")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
    
    script_path = Path(__file__).parent / "migrate.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限 (在Windows上可能不起作用)
    try:
        os.chmod(script_path, 0o755)
    except:
        pass
    
    logger.info(f"迁移管理脚本已创建: {script_path}")

def main():
    """主函数"""
    logger.info("🔄 Lab Management System - 数据库迁移初始化")
    logger.info("=" * 50)
    
    try:
        # 初始化Alembic迁移
        init_alembic_migration()
        
        # 创建迁移管理脚本
        create_migration_script()
        
        logger.info("\n✅ 数据库迁移初始化完成！")
        logger.info("\n📋 下一步操作:")
        logger.info("   1. 检查生成的迁移文件")
        logger.info("   2. 运行迁移: python scripts/migrate.py upgrade")
        logger.info("   3. 创建新迁移: python scripts/migrate.py revision --autogenerate -m '描述'")
        logger.info("   4. 查看迁移状态: python scripts/migrate.py current")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()