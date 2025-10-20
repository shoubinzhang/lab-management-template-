#!/bin/bash

# SSL证书自动续期脚本
# 用于Let's Encrypt证书的自动续期

set -e

# 配置变量
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
NGINX_CONTAINER="lab-management-nginx-prod"
SSL_DIR="/etc/letsencrypt/live/$DOMAIN"
PROJECT_SSL_DIR="./nginx/ssl"
LOG_FILE="/var/log/ssl-renew.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "ERROR: $1"
    exit 1
}

log "Starting SSL certificate renewal process..."

# 检查是否安装了certbot
if ! command -v certbot &> /dev/null; then
    log "Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

# 检查证书是否需要续期
log "Checking certificate expiration..."
if certbot certificates | grep -q "$DOMAIN"; then
    DAYS_LEFT=$(certbot certificates | grep -A 10 "$DOMAIN" | grep "VALID" | grep -o '[0-9]\+ days' | cut -d' ' -f1)
    log "Certificate expires in $DAYS_LEFT days"
    
    if [ "$DAYS_LEFT" -gt 30 ]; then
        log "Certificate is still valid for more than 30 days. No renewal needed."
        exit 0
    fi
else
    log "No existing certificate found for $DOMAIN"
fi

# 停止Nginx容器以释放端口80
log "Stopping Nginx container..."
docker stop "$NGINX_CONTAINER" || log "Warning: Failed to stop Nginx container"

# 续期或获取新证书
log "Renewing/obtaining SSL certificate..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN,www.$DOMAIN,m.$DOMAIN" \
    --keep-until-expiring \
    --expand || error_exit "Failed to renew/obtain SSL certificate"

# 复制新证书到项目目录
log "Copying certificates to project directory..."
mkdir -p "$PROJECT_SSL_DIR"
cp "$SSL_DIR/fullchain.pem" "$PROJECT_SSL_DIR/" || error_exit "Failed to copy fullchain.pem"
cp "$SSL_DIR/privkey.pem" "$PROJECT_SSL_DIR/" || error_exit "Failed to copy privkey.pem"

# 设置正确的权限
chown -R $USER:$USER "$PROJECT_SSL_DIR"
chmod 644 "$PROJECT_SSL_DIR/fullchain.pem"
chmod 600 "$PROJECT_SSL_DIR/privkey.pem"

# 验证证书
log "Validating certificate..."
openssl x509 -in "$PROJECT_SSL_DIR/fullchain.pem" -text -noout | grep -q "$DOMAIN" || error_exit "Certificate validation failed"

# 重新启动Nginx容器
log "Starting Nginx container..."
docker start "$NGINX_CONTAINER" || error_exit "Failed to start Nginx container"

# 等待容器启动
sleep 10

# 验证HTTPS连接
log "Testing HTTPS connection..."
curl -f -s "https://$DOMAIN/health" > /dev/null || error_exit "HTTPS connection test failed"

# 发送通知 (可选)
if [ -n "$NOTIFICATION_WEBHOOK" ]; then
    log "Sending renewal notification..."
    curl -X POST "$NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"SSL证书续期成功\\n域名: $DOMAIN\\n时间: $(date)\\n有效期: $(openssl x509 -in $PROJECT_SSL_DIR/fullchain.pem -noout -enddate | cut -d= -f2)\"
        }" || log "Failed to send notification"
fi

log "SSL certificate renewal completed successfully"

# 清理旧的日志文件
find /var/log -name "ssl-renew.log.*" -mtime +30 -delete 2>/dev/null || true

exit 0