#!/bin/bash

# 后端Docker容器启动脚本
# 用于生产环境的后端容器初始化

set -e

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Lab Management Backend Container..."

# 等待数据库可用
log "Waiting for database to be ready..."
while ! nc -z postgres 5432; do
    log "Database is not ready, waiting..."
    sleep 2
done
log "Database is ready!"

# 等待Redis可用
log "Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
    log "Redis is not ready, waiting..."
    sleep 2
done
log "Redis is ready!"

# 运行数据库迁移
log "Running database migrations..."
python -m alembic upgrade head || {
    log "ERROR: Database migration failed!"
    exit 1
}

# 创建初始数据 (如果需要)
if [ "$CREATE_INITIAL_DATA" = "true" ]; then
    log "Creating initial data..."
    python scripts/create_initial_data.py || {
        log "WARNING: Failed to create initial data"
    }
fi

# 创建管理员用户 (如果需要)
if [ "$CREATE_ADMIN_USER" = "true" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    log "Creating admin user..."
    python scripts/create_admin.py || {
        log "WARNING: Failed to create admin user"
    }
fi

# 检查必要的环境变量
required_vars=("DATABASE_URL" "JWT_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

# 显示环境信息
log "Container Environment:"
log "- Python version: $(python --version)"
log "- Environment: ${ENVIRONMENT:-production}"
log "- Debug mode: ${DEBUG:-false}"
log "- Workers: ${WORKERS:-4}"
log "- Database: Connected"
log "- Redis: Connected"
log "- Timezone: $(date +%Z)"

# 测试数据库连接
log "Testing database connection..."
python -c "from app.database import engine; engine.connect().close()" || {
    log "ERROR: Database connection test failed!"
    exit 1
}

# 测试Redis连接
log "Testing Redis connection..."
python -c "from app.cache import redis_client; redis_client.ping()" || {
    log "WARNING: Redis connection test failed"
}

# 创建必要的目录
mkdir -p /app/logs /app/uploads /app/temp

# 设置文件权限
chmod 755 /app/uploads /app/logs /app/temp

# 清理临时文件
find /app/temp -type f -mtime +1 -delete 2>/dev/null || true

# 启动前的健康检查
log "Performing pre-startup health checks..."

# 检查磁盘空间
DISK_USAGE=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log "WARNING: Disk usage is high: ${DISK_USAGE}%"
fi

# 检查内存使用
MEM_AVAILABLE=$(free -m | grep Available | awk '{print $7}' 2>/dev/null || echo "0")
if [ "$MEM_AVAILABLE" -lt 100 ]; then
    log "WARNING: Available memory is low: ${MEM_AVAILABLE}MB"
fi

log "Backend container initialization completed successfully"
log "Starting application server..."

# 如果是开发模式，使用uvicorn
if [ "$ENVIRONMENT" = "development" ]; then
    log "Starting in development mode with uvicorn..."
    exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
fi

# 生产模式，执行传入的命令
exec "$@"