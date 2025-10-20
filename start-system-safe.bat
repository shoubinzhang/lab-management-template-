@echo off
chcp 65001 >nul
title 实验室管理系统 - 安全启动

echo.
echo ========================================
echo      实验室管理系统 - 安全启动
echo ========================================
echo.

cd /d "%~dp0"

echo 🔍 检查环境...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

echo 🛑 停止现有服务...
REM 停止可能运行的服务器
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 3 >nul

echo.
echo 🛠️  开始后端修复和启动...
echo.

REM 启动后端
cd backend

REM 检查后端目录和文件
if not exist "app.py" (
    echo ❌ 错误：未找到app.py文件
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ 错误：未找到requirements.txt文件
    pause
    exit /b 1
)

echo 📦 检查后端依赖...
if not exist "venv" (
    echo 🔧 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
)

echo 🔌 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

echo 📦 安装/更新后端依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)

echo 🚀 启动后端服务器...
start "后端服务器" cmd /k "python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ 等待后端启动...
timeout /t 5 >nul

cd ..

echo.
echo 🛠️  开始前端修复和启动...
echo.

cd frontend

echo 🧹 清理前端缓存...
cmd /c "npm cache clean --force" >nul 2>&1

REM 清理缓存目录
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist ".tmp" rmdir /s /q ".tmp" >nul 2>&1

echo 📦 检查前端依赖...
if not exist "node_modules" (
    echo 🔧 安装前端依赖...
    cmd /c "npm install"
)

echo 🚀 启动前端服务器...
start "前端服务器" cmd /k "npm run start:safe"

cd ..

echo.
echo ✅ 系统启动完成！
echo.
echo 📋 服务信息：
echo    🔗 前端地址: http://localhost:3000
echo    🔗 后端地址: http://localhost:8000
echo    📊 API文档: http://localhost:8000/docs
echo.
echo 💡 提示：
echo    - 两个服务器窗口将保持打开状态
echo    - 关闭窗口即可停止对应服务
echo    - 如遇问题，请检查防火墙和端口占用
echo.

echo 🌐 等待服务完全启动后自动打开浏览器...
timeout /t 10 >nul

REM 打开浏览器
start http://localhost:3000

echo.
echo 🎉 系统已启动！按任意键退出此窗口...
pause >nul