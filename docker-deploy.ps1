# Docker部署脚本 (PowerShell版本)
# 用于简化实验室管理系统的容器化部署

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Service = ""
)

# 颜色定义
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Blue"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# 检查Docker和Docker Compose
function Test-DockerEnvironment {
    Write-Info "检查Docker环境..."
    
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            Write-Error "Docker未安装，请先安装Docker Desktop"
            exit 1
        }
        
        $composeVersion = docker-compose --version 2>$null
        if (-not $composeVersion) {
            Write-Error "Docker Compose未安装，请先安装Docker Compose"
            exit 1
        }
        
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker服务未运行，请启动Docker Desktop"
            exit 1
        }
        
        Write-Success "Docker环境检查通过"
    }
    catch {
        Write-Error "Docker环境检查失败: $($_.Exception.Message)"
        exit 1
    }
}

# 创建环境变量文件
function Initialize-Environment {
    Write-Info "设置环境变量..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" ".env"
            Write-Warning "已从.env.docker复制环境变量文件，请根据实际情况修改.env文件"
        }
        else {
            Write-Error "未找到环境变量模板文件.env.docker"
            exit 1
        }
    }
    else {
        Write-Info "环境变量文件.env已存在"
    }
}

# 构建镜像
function Build-Images {
    param([string]$Env)
    
    Write-Info "构建Docker镜像..."
    
    try {
        switch ($Env) {
            "dev" {
                docker-compose -f docker-compose.dev.yml build
            }
            "prod" {
                docker-compose build
            }
            default {
                Write-Error "无效的环境类型: $Env"
                exit 1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "镜像构建完成"
        }
        else {
            Write-Error "镜像构建失败"
            exit 1
        }
    }
    catch {
        Write-Error "构建过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

# 启动服务
function Start-Services {
    param([string]$Env)
    
    Write-Info "启动服务..."
    
    try {
        switch ($Env) {
            "dev" {
                docker-compose -f docker-compose.dev.yml up -d
            }
            "prod" {
                docker-compose up -d
            }
            default {
                Write-Error "无效的环境类型: $Env"
                exit 1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "服务启动完成"
            Show-ServiceUrls $Env
        }
        else {
            Write-Error "服务启动失败"
            exit 1
        }
    }
    catch {
        Write-Error "启动过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

# 停止服务
function Stop-Services {
    param([string]$Env)
    
    Write-Info "停止服务..."
    
    try {
        switch ($Env) {
            "dev" {
                docker-compose -f docker-compose.dev.yml down
            }
            "prod" {
                docker-compose down
            }
            default {
                Write-Error "无效的环境类型: $Env"
                exit 1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "服务已停止"
        }
        else {
            Write-Error "停止服务失败"
        }
    }
    catch {
        Write-Error "停止过程中发生错误: $($_.Exception.Message)"
    }
}

# 查看服务状态
function Get-ServiceStatus {
    param([string]$Env)
    
    Write-Info "查看服务状态..."
    
    switch ($Env) {
        "dev" {
            docker-compose -f docker-compose.dev.yml ps
        }
        "prod" {
            docker-compose ps
        }
        default {
            Write-Error "无效的环境类型: $Env"
            exit 1
        }
    }
}

# 查看日志
function Get-ServiceLogs {
    param([string]$Env, [string]$ServiceName = "")
    
    Write-Info "查看服务日志..."
    
    switch ($Env) {
        "dev" {
            if ($ServiceName) {
                docker-compose -f docker-compose.dev.yml logs -f $ServiceName
            }
            else {
                docker-compose -f docker-compose.dev.yml logs -f
            }
        }
        "prod" {
            if ($ServiceName) {
                docker-compose logs -f $ServiceName
            }
            else {
                docker-compose logs -f
            }
        }
        default {
            Write-Error "无效的环境类型: $Env"
            exit 1
        }
    }
}

# 数据库迁移
function Invoke-DatabaseMigration {
    param([string]$Env)
    
    Write-Info "运行数据库迁移..."
    
    try {
        switch ($Env) {
            "dev" {
                docker-compose -f docker-compose.dev.yml exec backend-dev python -m flask db upgrade
            }
            "prod" {
                docker-compose exec backend python -m flask db upgrade
            }
            default {
                Write-Error "无效的环境类型: $Env"
                exit 1
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "数据库迁移完成"
        }
        else {
            Write-Error "数据库迁移失败"
        }
    }
    catch {
        Write-Error "迁移过程中发生错误: $($_.Exception.Message)"
    }
}

# 健康检查
function Test-ServiceHealth {
    param([string]$Env)
    
    Write-Info "执行健康检查..."
    
    try {
        switch ($Env) {
            "dev" {
                docker-compose -f docker-compose.dev.yml exec backend-dev python health_check.py --comprehensive
            }
            "prod" {
                docker-compose exec backend python health_check.py --comprehensive
            }
            default {
                Write-Error "无效的环境类型: $Env"
                exit 1
            }
        }
    }
    catch {
        Write-Error "健康检查过程中发生错误: $($_.Exception.Message)"
    }
}

# 清理资源
function Clear-DockerResources {
    Write-Info "清理Docker资源..."
    
    try {
        # 停止所有容器
        docker-compose down 2>$null
        docker-compose -f docker-compose.dev.yml down 2>$null
        
        # 删除未使用的镜像
        docker image prune -f
        
        # 删除未使用的卷
        docker volume prune -f
        
        Write-Success "资源清理完成"
    }
    catch {
        Write-Error "清理过程中发生错误: $($_.Exception.Message)"
    }
}

# 显示服务URL
function Show-ServiceUrls {
    param([string]$Env)
    
    Write-Info "服务访问地址:"
    
    switch ($Env) {
        "dev" {
            Write-ColorOutput "前端应用: http://localhost:3000" "Cyan"
            Write-ColorOutput "后端API: http://localhost:8001" "Cyan"
            Write-ColorOutput "数据库: localhost:5433" "Cyan"
            Write-ColorOutput "Redis: localhost:6380" "Cyan"
        }
        "prod" {
            Write-ColorOutput "前端应用: http://localhost:80" "Cyan"
            Write-ColorOutput "后端API: http://localhost:8000" "Cyan"
            Write-ColorOutput "数据库: localhost:5432" "Cyan"
            Write-ColorOutput "Redis: localhost:6379" "Cyan"
        }
    }
}

# 显示帮助信息
function Show-Help {
    Write-ColorOutput "实验室管理系统 Docker 部署脚本 (PowerShell版本)" "Yellow"
    Write-Host ""
    Write-Host "用法: .\docker-deploy.ps1 -Command <命令> [-Environment <环境>] [-Service <服务>]"
    Write-Host ""
    Write-Host "命令:"
    Write-Host "  build       构建Docker镜像"
    Write-Host "  start       启动服务"
    Write-Host "  stop        停止服务"
    Write-Host "  restart     重启服务"
    Write-Host "  status      查看服务状态"
    Write-Host "  logs        查看日志"
    Write-Host "  migrate     运行数据库迁移"
    Write-Host "  health      健康检查"
    Write-Host "  cleanup     清理Docker资源"
    Write-Host "  help        显示帮助信息"
    Write-Host ""
    Write-Host "环境:"
    Write-Host "  dev         开发环境 (默认)"
    Write-Host "  prod        生产环境"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\docker-deploy.ps1 -Command build -Environment dev"
    Write-Host "  .\docker-deploy.ps1 -Command start -Environment prod"
    Write-Host "  .\docker-deploy.ps1 -Command logs -Environment dev -Service backend-dev"
}

# 主函数
switch ($Command.ToLower()) {
    "build" {
        Test-DockerEnvironment
        Initialize-Environment
        Build-Images $Environment
    }
    "start" {
        Test-DockerEnvironment
        Initialize-Environment
        Start-Services $Environment
    }
    "stop" {
        Stop-Services $Environment
    }
    "restart" {
        Stop-Services $Environment
        Start-Sleep -Seconds 2
        Start-Services $Environment
    }
    "status" {
        Get-ServiceStatus $Environment
    }
    "logs" {
        Get-ServiceLogs $Environment $Service
    }
    "migrate" {
        Invoke-DatabaseMigration $Environment
    }
    "health" {
        Test-ServiceHealth $Environment
    }
    "cleanup" {
        Clear-DockerResources
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "无效的命令: $Command"
        Show-Help
        exit 1
    }
}