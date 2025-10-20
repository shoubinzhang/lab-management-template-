#!/bin/bash

# Docker部署脚本
# 用于简化实验室管理系统的容器化部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查Docker和Docker Compose
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建环境变量文件
setup_env() {
    log_info "设置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.docker" ]; then
            cp .env.docker .env
            log_warning "已从.env.docker复制环境变量文件，请根据实际情况修改.env文件"
        else
            log_error "未找到环境变量模板文件.env.docker"
            exit 1
        fi
    else
        log_info "环境变量文件.env已存在"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml build
            ;;
        "prod")
            docker-compose build
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml up -d
            ;;
        "prod")
            docker-compose up -d
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
    
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml down
            ;;
        "prod")
            docker-compose down
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
    
    log_success "服务已停止"
}

# 查看服务状态
status_services() {
    log_info "查看服务状态..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml ps
            ;;
        "prod")
            docker-compose ps
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml logs -f $2
            ;;
        "prod")
            docker-compose logs -f $2
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
}

# 数据库迁移
run_migration() {
    log_info "运行数据库迁移..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml exec backend-dev python -m flask db upgrade
            ;;
        "prod")
            docker-compose exec backend python -m flask db upgrade
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
    
    log_success "数据库迁移完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    case $1 in
        "dev")
            docker-compose -f docker-compose.dev.yml exec backend-dev python health_check.py --comprehensive
            ;;
        "prod")
            docker-compose exec backend python health_check.py --comprehensive
            ;;
        *)
            log_error "无效的环境类型: $1"
            exit 1
            ;;
    esac
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止所有容器
    docker-compose down
    docker-compose -f docker-compose.dev.yml down
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷
    docker volume prune -f
    
    log_success "资源清理完成"
}

# 显示帮助信息
show_help() {
    echo "实验室管理系统 Docker 部署脚本"
    echo ""
    echo "用法: $0 <命令> [环境] [选项]"
    echo ""
    echo "命令:"
    echo "  build <env>     构建Docker镜像"
    echo "  start <env>     启动服务"
    echo "  stop <env>      停止服务"
    echo "  restart <env>   重启服务"
    echo "  status <env>    查看服务状态"
    echo "  logs <env> [service]  查看日志"
    echo "  migrate <env>   运行数据库迁移"
    echo "  health <env>    健康检查"
    echo "  cleanup         清理Docker资源"
    echo "  help            显示帮助信息"
    echo ""
    echo "环境:"
    echo "  dev             开发环境"
    echo "  prod            生产环境"
    echo ""
    echo "示例:"
    echo "  $0 build dev    构建开发环境镜像"
    echo "  $0 start prod   启动生产环境"
    echo "  $0 logs dev backend-dev  查看开发环境后端日志"
}

# 主函数
main() {
    case $1 in
        "build")
            check_docker
            setup_env
            build_images $2
            ;;
        "start")
            check_docker
            setup_env
            start_services $2
            ;;
        "stop")
            stop_services $2
            ;;
        "restart")
            stop_services $2
            start_services $2
            ;;
        "status")
            status_services $2
            ;;
        "logs")
            view_logs $2 $3
            ;;
        "migrate")
            run_migration $2
            ;;
        "health")
            health_check $2
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "无效的命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 检查参数
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# 执行主函数
main "$@"