#!/bin/bash

# Lab Management System 部署脚本
# 用于自动化部署到生产环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="lab-management"
APP_USER="labuser"
APP_GROUP="labuser"
APP_DIR="/opt/lab-management-app"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/lab-management"
RUN_DIR="/var/run/lab-management"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

# 函数定义
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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法确定操作系统版本"
        exit 1
    fi
    
    source /etc/os-release
    log_info "操作系统: $PRETTY_NAME"
    
    # 检查必要的命令
    local commands=("git" "python3" "pip3" "nginx" "systemctl")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "命令 '$cmd' 未找到，请先安装"
            exit 1
        fi
    done
    
    log_success "系统环境检查完成"
}

install_dependencies() {
    log_info "安装系统依赖..."
    
    # 更新包列表
    apt-get update
    
    # 安装必要的包
    apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        nginx \
        postgresql \
        postgresql-contrib \
        redis-server \
        supervisor \
        certbot \
        python3-certbot-nginx
    
    log_success "系统依赖安装完成"
}

create_user() {
    log_info "创建应用用户..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home "$APP_DIR" --create-home "$APP_USER"
        log_success "用户 $APP_USER 创建成功"
    else
        log_info "用户 $APP_USER 已存在"
    fi
}

setup_directories() {
    log_info "设置目录结构..."
    
    # 创建必要的目录
    mkdir -p "$APP_DIR" "$LOG_DIR" "$RUN_DIR"
    
    # 设置权限
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR" "$LOG_DIR" "$RUN_DIR"
    chmod 755 "$APP_DIR" "$LOG_DIR" "$RUN_DIR"
    
    log_success "目录结构设置完成"
}

clone_repository() {
    log_info "克隆代码仓库..."
    
    if [[ -d "$APP_DIR/.git" ]]; then
        log_info "代码仓库已存在，更新代码..."
        cd "$APP_DIR"
        sudo -u "$APP_USER" git pull origin main
    else
        log_info "克隆新的代码仓库..."
        # 这里需要替换为实际的仓库地址
        # sudo -u "$APP_USER" git clone https://github.com/your-repo/lab-management-app.git "$APP_DIR"
        log_warning "请手动将代码复制到 $APP_DIR"
    fi
    
    log_success "代码仓库设置完成"
}

setup_python_environment() {
    log_info "设置Python虚拟环境..."
    
    cd "$APP_DIR/backend"
    
    # 创建虚拟环境
    if [[ ! -d "$VENV_DIR" ]]; then
        sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
        log_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境并安装依赖
    sudo -u "$APP_USER" bash -c "
        source '$VENV_DIR/bin/activate' && \
        pip install --upgrade pip && \
        pip install -r requirements.txt
    "
    
    log_success "Python环境设置完成"
}

setup_database() {
    log_info "设置数据库..."
    
    # 启动PostgreSQL服务
    systemctl start postgresql
    systemctl enable postgresql
    
    # 创建数据库和用户
    sudo -u postgres psql -c "CREATE DATABASE lab_management;" 2>/dev/null || log_info "数据库已存在"
    sudo -u postgres psql -c "CREATE USER labuser WITH PASSWORD 'your_password';" 2>/dev/null || log_info "用户已存在"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lab_management TO labuser;"
    
    # 运行数据库迁移
    cd "$APP_DIR/backend"
    sudo -u "$APP_USER" bash -c "
        source '$VENV_DIR/bin/activate' && \
        python database.py
    "
    
    log_success "数据库设置完成"
}

setup_environment() {
    log_info "设置环境变量..."
    
    # 复制环境配置文件
    if [[ ! -f "$APP_DIR/backend/.env.production" ]]; then
        cp "$APP_DIR/backend/.env.production.example" "$APP_DIR/backend/.env.production" 2>/dev/null || {
            log_warning "请手动创建 .env.production 文件"
        }
    fi
    
    # 设置文件权限
    chown "$APP_USER:$APP_GROUP" "$APP_DIR/backend/.env.production"
    chmod 600 "$APP_DIR/backend/.env.production"
    
    log_success "环境变量设置完成"
}

setup_systemd_service() {
    log_info "设置systemd服务..."
    
    # 复制服务文件
    cp "$APP_DIR/backend/lab-management.service" "$SYSTEMD_DIR/"
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用并启动服务
    systemctl enable lab-management
    systemctl start lab-management
    
    # 检查服务状态
    if systemctl is-active --quiet lab-management; then
        log_success "Lab Management服务启动成功"
    else
        log_error "Lab Management服务启动失败"
        systemctl status lab-management
        exit 1
    fi
}

setup_nginx() {
    log_info "设置Nginx..."
    
    # 复制Nginx配置
    cp "$APP_DIR/backend/nginx.conf" "$NGINX_AVAILABLE/lab-management"
    
    # 创建软链接
    ln -sf "$NGINX_AVAILABLE/lab-management" "$NGINX_ENABLED/"
    
    # 删除默认站点
    rm -f "$NGINX_ENABLED/default"
    
    # 测试Nginx配置
    if nginx -t; then
        log_success "Nginx配置测试通过"
        systemctl reload nginx
        log_success "Nginx重新加载完成"
    else
        log_error "Nginx配置测试失败"
        exit 1
    fi
}

build_frontend() {
    log_info "构建前端应用..."
    
    cd "$APP_DIR/frontend"
    
    # 安装Node.js依赖
    sudo -u "$APP_USER" npm install
    
    # 构建生产版本
    sudo -u "$APP_USER" npm run build
    
    # 设置静态文件权限
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/frontend/build"
    
    log_success "前端构建完成"
}

setup_ssl() {
    log_info "设置SSL证书..."
    
    read -p "请输入域名 (例如: lab.example.com): " DOMAIN
    read -p "请输入邮箱地址: " EMAIL
    
    if [[ -n "$DOMAIN" && -n "$EMAIL" ]]; then
        certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
        log_success "SSL证书设置完成"
    else
        log_warning "跳过SSL证书设置"
    fi
}

run_health_check() {
    log_info "运行健康检查..."
    
    cd "$APP_DIR/backend"
    
    # 等待服务启动
    sleep 5
    
    # 运行健康检查
    sudo -u "$APP_USER" bash -c "
        source '$VENV_DIR/bin/activate' && \
        python health_check.py
    "
    
    if [[ $? -eq 0 ]]; then
        log_success "健康检查通过"
    else
        log_warning "健康检查发现问题，请检查日志"
    fi
}

show_status() {
    log_info "显示服务状态..."
    
    echo "=== 服务状态 ==="
    systemctl status lab-management --no-pager -l
    echo
    
    echo "=== Nginx状态 ==="
    systemctl status nginx --no-pager -l
    echo
    
    echo "=== 端口监听 ==="
    netstat -tlnp | grep -E ':(80|443|8000)'
    echo
    
    echo "=== 日志位置 ==="
    echo "应用日志: $LOG_DIR/"
    echo "Nginx日志: /var/log/nginx/"
    echo "系统日志: journalctl -u lab-management"
}

# 主函数
main() {
    log_info "开始部署 Lab Management System..."
    
    check_root
    check_system
    
    # 询问用户要执行的步骤
    echo "请选择要执行的步骤:"
    echo "1) 完整部署 (推荐)"
    echo "2) 仅更新代码"
    echo "3) 仅重启服务"
    echo "4) 仅健康检查"
    echo "5) 显示状态"
    
    read -p "请输入选择 (1-5): " CHOICE
    
    case $CHOICE in
        1)
            install_dependencies
            create_user
            setup_directories
            clone_repository
            setup_python_environment
            setup_database
            setup_environment
            build_frontend
            setup_systemd_service
            setup_nginx
            setup_ssl
            run_health_check
            show_status
            ;;
        2)
            clone_repository
            setup_python_environment
            build_frontend
            systemctl restart lab-management
            run_health_check
            ;;
        3)
            systemctl restart lab-management
            systemctl reload nginx
            run_health_check
            ;;
        4)
            run_health_check
            ;;
        5)
            show_status
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
    
    log_success "部署完成！"
    log_info "访问地址: https://your-domain.com"
    log_info "管理命令:"
    log_info "  启动服务: systemctl start lab-management"
    log_info "  停止服务: systemctl stop lab-management"
    log_info "  重启服务: systemctl restart lab-management"
    log_info "  查看日志: journalctl -u lab-management -f"
    log_info "  健康检查: cd $APP_DIR/backend && python health_check.py"
}

# 执行主函数
main "$@"