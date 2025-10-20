#!/usr/bin/env python3
"""
数据库备份脚本
支持PostgreSQL和SQLite数据库的自动备份
"""

import os
import sys
import subprocess
import datetime
import shutil
import gzip
import logging
from pathlib import Path
from decouple import config
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/lab-management/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self):
        self.database_url = config('DATABASE_URL', default='sqlite:///./lab_management.db')
        self.backup_dir = config('BACKUP_LOCATION', default='/var/backups/lab-management')
        self.retention_days = config('BACKUP_RETENTION_DAYS', default=30, cast=int)
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 确保备份目录存在
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def parse_database_url(self):
        """解析数据库URL"""
        if self.database_url.startswith('postgresql://'):
            return 'postgresql'
        elif self.database_url.startswith('mysql://'):
            return 'mysql'
        elif self.database_url.startswith('sqlite://'):
            return 'sqlite'
        else:
            raise ValueError(f"不支持的数据库类型: {self.database_url}")
    
    def backup_postgresql(self):
        """备份PostgreSQL数据库"""
        logger.info("开始备份PostgreSQL数据库...")
        
        # 解析数据库连接信息
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(self.database_url)
        
        db_name = parsed.path[1:]  # 去掉开头的'/'
        db_user = parsed.username
        db_password = parsed.password
        db_host = parsed.hostname or 'localhost'
        db_port = parsed.port or 5432
        
        # 备份文件名
        backup_filename = f"postgresql_backup_{self.timestamp}.sql"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # 设置环境变量
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password
        
        # 执行pg_dump命令
        cmd = [
            'pg_dump',
            '-h', str(db_host),
            '-p', str(db_port),
            '-U', db_user,
            '-d', db_name,
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            '-f', backup_path
        ]
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            logger.info(f"PostgreSQL备份成功: {backup_path}")
            
            # 压缩备份文件
            compressed_path = self.compress_backup(backup_path)
            os.remove(backup_path)  # 删除未压缩的文件
            
            return compressed_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL备份失败: {e.stderr}")
            raise
    
    def backup_sqlite(self):
        """备份SQLite数据库"""
        logger.info("开始备份SQLite数据库...")
        
        # 获取SQLite文件路径
        if self.database_url.startswith('sqlite:///'):
            db_path = self.database_url[10:]  # 去掉'sqlite:///'
        else:
            raise ValueError(f"无效的SQLite URL: {self.database_url}")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite数据库文件不存在: {db_path}")
        
        # 备份文件名
        backup_filename = f"sqlite_backup_{self.timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # 复制数据库文件
            shutil.copy2(db_path, backup_path)
            logger.info(f"SQLite备份成功: {backup_path}")
            
            # 压缩备份文件
            compressed_path = self.compress_backup(backup_path)
            os.remove(backup_path)  # 删除未压缩的文件
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"SQLite备份失败: {e}")
            raise
    
    def backup_mysql(self):
        """备份MySQL数据库"""
        logger.info("开始备份MySQL数据库...")
        
        # 解析数据库连接信息
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(self.database_url)
        
        db_name = parsed.path[1:]  # 去掉开头的'/'
        db_user = parsed.username
        db_password = parsed.password
        db_host = parsed.hostname or 'localhost'
        db_port = parsed.port or 3306
        
        # 备份文件名
        backup_filename = f"mysql_backup_{self.timestamp}.sql"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # 执行mysqldump命令
        cmd = [
            'mysqldump',
            '-h', str(db_host),
            '-P', str(db_port),
            '-u', db_user,
            f'-p{db_password}' if db_password else '',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            '--result-file', backup_path,
            db_name
        ]
        
        # 过滤空字符串
        cmd = [arg for arg in cmd if arg]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"MySQL备份成功: {backup_path}")
            
            # 压缩备份文件
            compressed_path = self.compress_backup(backup_path)
            os.remove(backup_path)  # 删除未压缩的文件
            
            return compressed_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"MySQL备份失败: {e.stderr}")
            raise
    
    def compress_backup(self, backup_path):
        """压缩备份文件"""
        compressed_path = backup_path + '.gz'
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"备份文件已压缩: {compressed_path}")
        return compressed_path
    
    def cleanup_old_backups(self):
        """清理过期的备份文件"""
        logger.info(f"清理{self.retention_days}天前的备份文件...")
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        deleted_count = 0
        
        for backup_file in Path(self.backup_dir).glob('*_backup_*.gz'):
            file_stat = backup_file.stat()
            file_date = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            
            if file_date < cutoff_date:
                backup_file.unlink()
                logger.info(f"已删除过期备份: {backup_file}")
                deleted_count += 1
        
        logger.info(f"清理完成，删除了{deleted_count}个过期备份文件")
    
    def get_backup_info(self):
        """获取备份信息"""
        backups = []
        
        for backup_file in sorted(Path(self.backup_dir).glob('*_backup_*.gz')):
            file_stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': file_stat.st_size,
                'created': datetime.datetime.fromtimestamp(file_stat.st_ctime),
                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime)
            })
        
        return backups
    
    def run_backup(self):
        """执行备份"""
        try:
            db_type = self.parse_database_url()
            
            if db_type == 'postgresql':
                backup_path = self.backup_postgresql()
            elif db_type == 'sqlite':
                backup_path = self.backup_sqlite()
            elif db_type == 'mysql':
                backup_path = self.backup_mysql()
            else:
                raise ValueError(f"不支持的数据库类型: {db_type}")
            
            # 清理过期备份
            self.cleanup_old_backups()
            
            logger.info(f"备份完成: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"备份失败: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Lab Management System 数据库备份工具')
    parser.add_argument('--info', action='store_true', help='显示备份信息')
    parser.add_argument('--cleanup', action='store_true', help='只执行清理操作')
    
    args = parser.parse_args()
    
    backup = DatabaseBackup()
    
    if args.info:
        # 显示备份信息
        backups = backup.get_backup_info()
        print(f"\n备份目录: {backup.backup_dir}")
        print(f"保留天数: {backup.retention_days}")
        print(f"\n现有备份 ({len(backups)} 个):")
        print("-" * 80)
        
        for b in backups:
            size_mb = b['size'] / (1024 * 1024)
            print(f"{b['filename']:<40} {size_mb:>8.2f} MB {b['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        
    elif args.cleanup:
        # 只执行清理
        backup.cleanup_old_backups()
        
    else:
        # 执行备份
        backup.run_backup()

if __name__ == '__main__':
    main()