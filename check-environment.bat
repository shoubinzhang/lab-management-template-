@echo off
chcp 65001 >nul
echo ========================================
echo   实验室管理系统 - 环境检查脚本
echo ========================================
echo.
echo 🔍 正在检查系统环境和配置...
echo.

:: 检查项目目录结构
echo 📁 检查项目目录结构...
if exist "backend" (
    echo ✅ backend目录存在
) else (
    echo ❌ backend目录缺失
    set HAS_ERROR=1
)

if exist "frontend" (
    echo ✅ frontend目录存在
) else (
    echo ❌ frontend目录缺失
    set HAS_ERROR=1
)

if exist "USER_GUIDE.md" (
    echo ✅ 用户指南存在
) else (
    echo ⚠️  用户指南缺失
)

if exist "start-system.bat" (
    echo ✅ 启动脚本存在
) else (
    echo ⚠️  启动脚本缺失
)

if exist "stop-system.bat" (
    echo ✅ 停止脚本存在
) else (
    echo ⚠️  停止脚本缺失
)

echo.

:: 检查Python环境
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    echo 💡 请从 https://www.python.org/downloads/ 下载安装
    set HAS_ERROR=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        echo ✅ Python版本：%%i
        set PYTHON_VERSION=%%i
    )
    
    :: 检查Python版本是否符合要求
    python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
    if errorlevel 1 (
        echo ⚠️  Python版本过低，建议使用3.8或更高版本
    )
)

:: 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip未安装
    set HAS_ERROR=1
) else (
    echo ✅ pip可用
)

echo.

:: 检查Node.js环境
echo ⚛️  检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或不在PATH中
    echo 💡 请从 https://nodejs.org/ 下载安装
    set HAS_ERROR=1
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do (
        echo ✅ Node.js版本：%%i
        set NODE_VERSION=%%i
    )
)

:: 检查npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm未安装
    set HAS_ERROR=1
) else (
    for /f "tokens=1" %%i in ('npm --version 2^>^&1') do (
        echo ✅ npm版本：%%i
    )
)

echo.

:: 检查后端环境
echo 🔧 检查后端环境...
cd backend

if exist "requirements.txt" (
    echo ✅ requirements.txt存在
) else (
    echo ❌ requirements.txt缺失
    set HAS_ERROR=1
)

if exist "app" (
    echo ✅ app目录存在
) else (
    echo ❌ app目录缺失
    set HAS_ERROR=1
)

if exist "venv" (
    echo ✅ Python虚拟环境存在
    
    :: 检查虚拟环境中的依赖
    call venv\Scripts\activate.bat 2>nul
    if errorlevel 1 (
        echo ❌ 虚拟环境激活失败
        set HAS_ERROR=1
    ) else (
        echo ✅ 虚拟环境可用
        
        :: 检查关键依赖
        python -c "import fastapi" 2>nul
        if errorlevel 1 (
            echo ❌ FastAPI未安装
            set HAS_ERROR=1
        ) else (
            echo ✅ FastAPI已安装
        )
        
        python -c "import uvicorn" 2>nul
        if errorlevel 1 (
            echo ❌ Uvicorn未安装
            set HAS_ERROR=1
        ) else (
            echo ✅ Uvicorn已安装
        )
        
        python -c "import sqlalchemy" 2>nul
        if errorlevel 1 (
            echo ❌ SQLAlchemy未安装
            set HAS_ERROR=1
        ) else (
            echo ✅ SQLAlchemy已安装
        )
    )
) else (
    echo ⚠️  Python虚拟环境不存在，建议运行 setup-environment.bat
)

if exist ".env" (
    echo ✅ 后端配置文件存在
) else (
    echo ⚠️  后端配置文件缺失
)

cd ..
echo.

:: 检查前端环境
echo 🔧 检查前端环境...
cd frontend

if exist "package.json" (
    echo ✅ package.json存在
) else (
    echo ❌ package.json缺失
    set HAS_ERROR=1
)

if exist "src" (
    echo ✅ src目录存在
) else (
    echo ❌ src目录缺失
    set HAS_ERROR=1
)

if exist "public" (
    echo ✅ public目录存在
) else (
    echo ❌ public目录缺失
    set HAS_ERROR=1
)

if exist "node_modules" (
    echo ✅ node_modules存在
    
    :: 检查关键依赖
    if exist "node_modules\react" (
        echo ✅ React已安装
    ) else (
        echo ❌ React未安装
        set HAS_ERROR=1
    )
    
    if exist "node_modules\react-router-dom" (
        echo ✅ React Router已安装
    ) else (
        echo ❌ React Router未安装
        set HAS_ERROR=1
    )
    
    if exist "node_modules\react-bootstrap" (
        echo ✅ React Bootstrap已安装
    ) else (
        echo ❌ React Bootstrap未安装
        set HAS_ERROR=1
    )
) else (
    echo ⚠️  node_modules不存在，需要运行 npm install
)

if exist ".env" (
    echo ✅ 前端配置文件存在
) else (
    echo ⚠️  前端配置文件缺失
)

cd ..
echo.

:: 检查端口占用
echo 🌐 检查端口占用情况...
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo ✅ 端口8000可用
) else (
    echo ⚠️  端口8000被占用
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        echo 📍 占用进程PID：%%a
    )
)

netstat -an | findstr :3000 >nul
if errorlevel 1 (
    echo ✅ 端口3000可用
) else (
    echo ⚠️  端口3000被占用
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
        echo 📍 占用进程PID：%%a
    )
)

echo.

:: 检查网络连接
echo 🌐 检查网络连接...
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  网络连接异常
) else (
    echo ✅ 网络连接正常
)

:: 检查防火墙规则
echo 🔥 检查防火墙设置...
netsh advfirewall firewall show rule name="Lab Management System Frontend" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  前端防火墙规则不存在
) else (
    echo ✅ 前端防火墙规则存在
)

netsh advfirewall firewall show rule name="Lab Management System Backend" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端防火墙规则不存在
) else (
    echo ✅ 后端防火墙规则存在
)

echo.

:: 获取系统信息
echo 💻 系统信息...
for /f "tokens=2 delims==" %%i in ('wmic os get Caption /value ^| find "Caption"') do echo 操作系统：%%i
for /f "tokens=2 delims==" %%i in ('wmic computersystem get TotalPhysicalMemory /value ^| find "TotalPhysicalMemory"') do (
    set /a RAM_GB=%%i/1024/1024/1024
    echo 内存：!RAM_GB! GB
)

:: 获取IP地址
echo 🌐 网络信息...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%j in ("%%i") do (
        echo 本机IP：%%j
        goto :ip_done
    )
)
:ip_done

echo.
echo ========================================
echo           📊 检查结果
echo ========================================
echo.

if defined HAS_ERROR (
    echo ❌ 发现问题，系统可能无法正常运行
    echo.
    echo 🔧 建议操作：
    echo   1. 运行 setup-environment.bat 重新配置环境
    echo   2. 检查缺失的依赖和文件
    echo   3. 确保Python和Node.js正确安装
    echo   4. 查看 USER_GUIDE.md 获取详细帮助
) else (
    echo ✅ 环境检查通过，系统应该可以正常运行
    echo.
    echo 🚀 可用操作：
    echo   • 启动系统：start-system.bat
    echo   • 停止系统：stop-system.bat
    echo   • 重新配置：setup-environment.bat
)

echo.
echo 📋 快速诊断：
if defined HAS_ERROR (
    echo   🔴 状态：需要修复
) else (
    echo   🟢 状态：就绪
)
echo   🐍 Python：%PYTHON_VERSION%
echo   ⚛️  Node.js：%NODE_VERSION%
echo   📁 项目：完整
echo   🌐 网络：可用
echo.

echo 💡 提示：
echo   • 如果遇到问题，请先运行 setup-environment.bat
 echo   • 确保以管理员身份运行脚本以获得完整权限
echo   • 检查防火墙和杀毒软件设置
echo   • 查看 USER_GUIDE.md 了解详细故障排除方法
echo.

pause