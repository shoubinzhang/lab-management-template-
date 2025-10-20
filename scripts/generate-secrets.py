#!/usr/bin/env python3
"""
生产环境安全密钥生成脚本
用于生成JWT密钥和其他安全配置
"""

import secrets
import string
import os
import sys
from pathlib import Path

def generate_secret_key(length=32):
    """生成安全的随机密钥"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=64):
    """生成JWT专用密钥"""
    return secrets.token_urlsafe(length)

def generate_database_password(length=16):
    """生成数据库密码"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def update_env_file(env_file_path, updates):
    """更新环境变量文件"""
    if not os.path.exists(env_file_path):
        print(f"错误: 环境文件 {env_file_path} 不存在")
        return False
    
    # 读取现有内容
    with open(env_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新配置
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key = line.split('=')[0]
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line + '\n')
        else:
            updated_lines.append(line + '\n')
    
    # 添加未更新的新配置
    for key, value in updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}\n")
    
    # 写回文件
    with open(env_file_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    return True

def main():
    """主函数"""
    print("🔐 Lab Management System - 安全密钥生成器")
    print("=" * 50)
    
    # 生成密钥
    secret_key = generate_secret_key(64)
    jwt_secret = generate_jwt_secret(64)
    db_password = generate_database_password(20)
    
    print("✅ 已生成安全密钥:")
    print(f"   SECRET_KEY: {secret_key[:20]}...")
    print(f"   JWT_SECRET_KEY: {jwt_secret[:20]}...")
    print(f"   数据库密码: {db_password}")
    print()
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_dir = project_root / "backend"
    
    # 更新后端环境文件
    env_production_path = backend_dir / ".env.production"
    
    if env_production_path.exists():
        updates = {
            'SECRET_KEY': secret_key,
            'JWT_SECRET_KEY': jwt_secret,
            'DATABASE_URL': f'postgresql://lab_user:{db_password}@localhost:5432/lab_management_prod'
        }
        
        if update_env_file(str(env_production_path), updates):
            print(f"✅ 已更新 {env_production_path}")
        else:
            print(f"❌ 更新 {env_production_path} 失败")
    else:
        print(f"⚠️  环境文件 {env_production_path} 不存在")
    
    # 生成数据库创建脚本
    db_script_path = project_root / "scripts" / "setup-database.sql"
    db_script_content = f"""
-- Lab Management System 数据库设置脚本
-- 在PostgreSQL中运行此脚本来创建数据库和用户

-- 创建数据库用户
CREATE USER lab_user WITH PASSWORD '{db_password}';

-- 创建数据库
CREATE DATABASE lab_management_prod OWNER lab_user;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE lab_management_prod TO lab_user;

-- 连接到新数据库并设置权限
\c lab_management_prod;
GRANT ALL ON SCHEMA public TO lab_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lab_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lab_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lab_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lab_user;

SELECT 'Database setup completed successfully!' as status;
"""
    
    with open(db_script_path, 'w', encoding='utf-8') as f:
        f.write(db_script_content)
    
    print(f"✅ 已生成数据库设置脚本: {db_script_path}")
    
    # 安全提醒
    print()
    print("🔒 安全提醒:")
    print("   1. 请妥善保管生成的密钥，不要泄露给他人")
    print("   2. 定期更换密钥以提高安全性")
    print("   3. 确保 .env.production 文件不被提交到版本控制")
    print("   4. 在生产服务器上运行 setup-database.sql 来创建数据库")
    print("   5. 配置防火墙只允许必要的端口访问")
    print()
    print("📋 下一步操作:")
    print("   1. 在PostgreSQL中运行: psql -U postgres -f scripts/setup-database.sql")
    print("   2. 安装生产依赖: pip install -r requirements.txt")
    print("   3. 运行数据库迁移: alembic upgrade head")
    print("   4. 配置Nginx和SSL证书")
    print("   5. 启动Gunicorn服务")

if __name__ == "__main__":
    main()