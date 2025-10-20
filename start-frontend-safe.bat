@echo off
chcp 65001 >nul
title 实验室管理系统 - 安全启动前端

echo.
echo ========================================
echo    实验室管理系统 - 安全启动前端
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 🔍 检查环境...
if not exist "package.json" (
    echo ❌ 错误：未找到package.json文件
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

echo 📦 检查Node.js和npm...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到npm，请检查Node.js安装
    pause
    exit /b 1
)

echo.
echo 🛠️  开始修复和清理...
echo.

REM 停止可能运行的前端服务器
echo 🛑 停止现有的前端服务器...
taskkill /f /im node.exe >nul 2>&1
timeout /t 2 >nul

REM 清理npm缓存
echo 📦 清理npm缓存...
cmd /c "npm cache clean --force" 2>nul

REM 删除node_modules/.cache
echo 🗂️  清理webpack缓存...
if exist "node_modules\.cache" (
    rmdir /s /q "node_modules\.cache" 2>nul
)

REM 删除build目录
echo 🏗️  清理build目录...
if exist "build" (
    rmdir /s /q "build" 2>nul
)

REM 清理临时文件
echo 🧹 清理临时文件...
if exist ".tmp" rmdir /s /q ".tmp" 2>nul
if exist "tmp" rmdir /s /q "tmp" 2>nul
if exist ".cache" rmdir /s /q ".cache" 2>nul

echo.
echo ✅ 清理完成！
echo.

echo 🚀 启动前端服务器...
echo.
echo 💡 提示：
echo    - 前端将在 http://localhost:3000 启动
echo    - 如果遇到问题，请检查后端是否正在运行
echo    - 按 Ctrl+C 可以停止服务器
echo.

REM 检查依赖是否存在
if not exist "node_modules" (
    echo 📦 首次运行，安装依赖...
    cmd /c "npm install"
    if errorlevel 1 (
        echo ❌ 依赖安装失败！
        echo 请检查网络连接和npm配置
        pause
        exit /b 1
    )
)

REM 使用安全启动命令
echo 🚀 使用安全模式启动...
cmd /c "npm run start:safe"

if errorlevel 1 (
    echo.
    echo ❌ 安全启动失败！尝试备用方案...
    echo.
    
    REM 备用方案1：重新安装依赖
    echo 📦 重新安装依赖...
    if exist "node_modules" rmdir /s /q "node_modules"
    cmd /c "npm install"
    
    if errorlevel 1 (
        echo ❌ 依赖安装失败！
        echo 请检查网络连接和npm配置
        pause
        exit /b 1
    )
    
    echo 🚀 重新启动...
    cmd /c "npm start"
    
    if errorlevel 1 (
        echo ❌ 所有启动方案都失败了！
        echo 请检查：
        echo   1. Node.js版本是否兼容
        echo   2. 网络连接是否正常
        echo   3. 防火墙设置
        echo   4. 端口3000是否被占用
        pause
        exit /b 1
    )
)

pause