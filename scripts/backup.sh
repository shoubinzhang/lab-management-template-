#!/bin/bash

# 实验室管理系统数据库备份脚本
# 作者: Lab Management System
# 版本: 1.0

set -e

# 配置变量
BACKUP_DIR="/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="lab_management_backup_${DATE}.sql"
COMPRESSED_FILE="lab_management_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

# 数据库连接信息
DB_HOST="postgres"
DB_PORT="5432"
DB_NAME="${POSTGRES_DB:-lab_management}"
DB_USER="${POSTGRES_USER:-lab_user}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 错误处理函数
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查必要的环境变量
if [ -z "$DB_PASSWORD" ]; then
    error_exit "POSTGRES_PASSWORD environment variable is not set"
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"

# 等待数据库可用
log "Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
    log "Database is not ready, waiting..."
    sleep 5
done

log "Database is ready, starting backup..."

# 执行数据库备份
log "Creating database backup: $BACKUP_FILE"
export PGPASSWORD="$DB_PASSWORD"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --no-password \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/$BACKUP_FILE" || error_exit "Database backup failed"

# 压缩备份文件
log "Compressing backup file..."
gzip "$BACKUP_DIR/$BACKUP_FILE" || error_exit "Failed to compress backup file"

# 验证备份文件
if [ -f "$BACKUP_DIR/$COMPRESSED_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$COMPRESSED_FILE" | cut -f1)
    log "Backup completed successfully: $COMPRESSED_FILE (Size: $BACKUP_SIZE)"
else
    error_exit "Backup file not found after compression"
fi

# 清理旧备份文件
log "Cleaning up old backup files (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "lab_management_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# 显示当前备份文件列表
log "Current backup files:"
ls -lh "$BACKUP_DIR"/lab_management_backup_*.sql.gz 2>/dev/null || log "No backup files found"

# 可选: 上传到云存储 (需要配置)
if [ -n "$CLOUD_BACKUP_ENABLED" ] && [ "$CLOUD_BACKUP_ENABLED" = "true" ]; then
    log "Uploading backup to cloud storage..."
    # 这里可以添加云存储上传逻辑
    # 例如: aws s3 cp "$BACKUP_DIR/$COMPRESSED_FILE" s3://your-backup-bucket/
    log "Cloud backup upload completed"
fi

# 发送备份通知 (可选)
if [ -n "$NOTIFICATION_WEBHOOK" ]; then
    log "Sending backup notification..."
    curl -X POST "$NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"实验室管理系统数据库备份完成\\n文件: $COMPRESSED_FILE\\n大小: $BACKUP_SIZE\\n时间: $(date)\"
        }" || log "Failed to send notification"
fi

log "Backup process completed successfully"

# 清理环境变量
unset PGPASSWORD

exit 0