#!/bin/bash

# Lab Management System 生产环境部署脚本
# 用于自动化部署到生产服务器

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="lab-management"
APP_DIR="/opt/${APP_NAME}"
BACKEND_DIR="${APP_DIR}/backend"
FRONTEND_DIR="${APP_DIR}/frontend"
VENV_DIR="${APP_DIR}/venv"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
LOG_DIR="/var/log/${APP_NAME}"
UPLOAD_DIR="/var/uploads"
BACKUP_DIR="/var/backups/${APP_NAME}"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查系统依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local deps=("python3" "python3-pip" "python3-venv" "postgresql" "redis-server" "nginx" "git" "curl")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少以下依赖: ${missing_deps[*]}"
        log_info "请运行: apt update && apt install -y ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "系统依赖检查完成"
}

# 创建应用用户
create_app_user() {
    log_info "创建应用用户..."
    
    if ! id "www-data" &>/dev/null; then
        useradd -r -s /bin/false www-data
        log_success "已创建用户 www-data"
    else
        log_info "用户 www-data 已存在"
    fi
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    local dirs=("$APP_DIR" "$LOG_DIR" "$UPLOAD_DIR" "$BACKUP_DIR")
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        chown www-data:www-data "$dir"
        chmod 755 "$dir"
    done
    
    log_success "目录结构创建完成"
}

# 部署后端
deploy_backend() {
    log_info "部署后端应用..."
    
    # 复制后端代码
    cp -r ./backend/* "$BACKEND_DIR/"
    chown -R www-data:www-data "$BACKEND_DIR"
    
    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        chown -R www-data:www-data "$VENV_DIR"
    fi
    
    # 激活虚拟环境并安装依赖
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$BACKEND_DIR/requirements.txt"
    
    # 设置环境变量文件权限
    if [ -f "$BACKEND_DIR/.env.production" ]; then
        chmod 600 "$BACKEND_DIR/.env.production"
        chown www-data:www-data "$BACKEND_DIR/.env.production"
    fi
    
    log_success "后端部署完成"
}

# 部署前端
deploy_frontend() {
    log_info "部署前端应用..."
    
    # 检查Node.js和npm
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        log_info "安装Node.js和npm..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
    
    # 复制前端代码
    cp -r ./frontend/* "$FRONTEND_DIR/"
    
    # 安装依赖并构建
    cd "$FRONTEND_DIR"
    npm ci --production
    npm run build
    
    # 设置权限
    chown -R www-data:www-data "$FRONTEND_DIR"
    
    log_success "前端部署完成"
}

# 配置数据库
setup_database() {
    log_info "配置数据库..."
    
    # 检查PostgreSQL是否运行
    if ! systemctl is-active --quiet postgresql; then
        systemctl start postgresql
        systemctl enable postgresql
    fi
    
    # 运行数据库设置脚本
    if [ -f "./scripts/setup-database.sql" ]; then
        sudo -u postgres psql -f "./scripts/setup-database.sql"
        log_success "数据库设置完成"
    else
        log_warning "数据库设置脚本不存在，请手动配置数据库"
    fi
    
    # 运行数据库迁移
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 如果有Alembic配置，运行迁移
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        log_success "数据库迁移完成"
    fi
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    # 复制Nginx配置
    cp ./nginx.conf "$NGINX_CONF"
    
    # 创建符号链接
    ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/${APP_NAME}"
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试Nginx配置
    if nginx -t; then
        systemctl reload nginx
        systemctl enable nginx
        log_success "Nginx配置完成"
    else
        log_error "Nginx配置测试失败"
        exit 1
    fi
}

# 配置系统服务
setup_service() {
    log_info "配置系统服务..."
    
    # 复制服务文件
    cp "./scripts/${APP_NAME}.service" "$SERVICE_FILE"
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用并启动服务
    systemctl enable "${APP_NAME}.service"
    systemctl start "${APP_NAME}.service"
    
    # 检查服务状态
    if systemctl is-active --quiet "${APP_NAME}.service"; then
        log_success "系统服务配置完成"
    else
        log_error "服务启动失败"
        systemctl status "${APP_NAME}.service"
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw reload
        log_success "防火墙配置完成"
    else
        log_warning "UFW未安装，请手动配置防火墙"
    fi
}

# 设置日志轮转
setup_logrotate() {
    log_info "配置日志轮转..."
    
    cat > "/etc/logrotate.d/${APP_NAME}" << EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload ${APP_NAME}.service
    endscript
}
EOF
    
    log_success "日志轮转配置完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 10
    
    # 检查后端API
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "后端API健康检查通过"
    else
        log_error "后端API健康检查失败"
        return 1
    fi
    
    # 检查Nginx
    if curl -f http://localhost &>/dev/null; then
        log_success "前端服务健康检查通过"
    else
        log_error "前端服务健康检查失败"
        return 1
    fi
    
    log_success "所有服务健康检查通过"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo
    echo "=== 部署信息 ==="
    echo "应用目录: $APP_DIR"
    echo "日志目录: $LOG_DIR"
    echo "上传目录: $UPLOAD_DIR"
    echo "备份目录: $BACKUP_DIR"
    echo
    echo "=== 服务管理 ==="
    echo "启动服务: systemctl start ${APP_NAME}"
    echo "停止服务: systemctl stop ${APP_NAME}"
    echo "重启服务: systemctl restart ${APP_NAME}"
    echo "查看状态: systemctl status ${APP_NAME}"
    echo "查看日志: journalctl -u ${APP_NAME} -f"
    echo
    echo "=== 下一步 ==="
    echo "1. 配置SSL证书"
    echo "2. 设置域名DNS解析"
    echo "3. 配置监控和告警"
    echo "4. 设置定期备份"
    echo
}

# 主函数
main() {
    log_info "开始部署 Lab Management System..."
    
    check_root
    check_dependencies
    create_app_user
    create_directories
    deploy_backend
    deploy_frontend
    setup_database
    setup_nginx
    setup_service
    setup_firewall
    setup_logrotate
    
    if health_check; then
        show_deployment_info
    else
        log_error "部署验证失败，请检查日志"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi