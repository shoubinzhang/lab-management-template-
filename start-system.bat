@echo off
chcp 65001 >nul
echo ========================================
echo    实验室管理系统 - 一键启动脚本
echo ========================================
echo.

:: 检查是否在正确的目录
if not exist "backend" (
    echo ❌ 错误：未找到backend目录，请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ❌ 错误：未找到frontend目录，请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

:: 检查Python是否安装
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

:: 检查Node.js是否安装
echo 🔍 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)
echo ✅ Node.js环境检查通过

:: 检查npm是否安装
echo 🔍 检查npm环境...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到npm，请确保Node.js正确安装
    pause
    exit /b 1
)
echo ✅ npm环境检查通过
echo.

:: 检查后端依赖
echo 🔍 检查后端依赖...
if not exist "backend\requirements.txt" (
    echo ❌ 错误：未找到requirements.txt文件
    pause
    exit /b 1
)

:: 检查前端依赖
echo 🔍 检查前端依赖...
if not exist "frontend\package.json" (
    echo ❌ 错误：未找到package.json文件
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ⚠️  警告：未找到node_modules目录，将自动安装前端依赖
    echo 📦 安装前端依赖...
    cd frontend
    npm install
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo ✅ 前端依赖安装完成
)
echo.

:: 获取本机IP地址
echo 🌐 获取网络信息...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%j in ("%%i") do (
        set LOCAL_IP=%%j
        goto :ip_found
    )
)
:ip_found

if "%LOCAL_IP%"=="" (
    set LOCAL_IP=localhost
    echo ⚠️  无法获取IP地址，使用localhost
) else (
    echo ✅ 本机IP地址：%LOCAL_IP%
)
echo.

:: 检查端口是否被占用
echo 🔍 检查端口占用情况...
netstat -an | findstr :8000 >nul
if not errorlevel 1 (
    echo ⚠️  警告：端口8000已被占用，后端可能无法启动
)

netstat -an | findstr :3000 >nul
if not errorlevel 1 (
    echo ⚠️  警告：端口3000已被占用，前端可能无法启动
)
echo.

:: 启动后端服务
echo 🚀 启动后端服务...
echo 📍 后端服务地址：http://%LOCAL_IP%:8000
start "实验室管理系统-后端" cmd /k "cd /d "%~dp0backend" && echo 🐍 启动Python后端服务... && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul

:: 检查后端是否启动成功
echo 🔍 检查后端服务状态...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端服务可能未完全启动，继续启动前端...
) else (
    echo ✅ 后端服务启动成功
)
echo.

:: 启动前端服务
echo 🚀 启动前端服务...
echo 📍 前端服务地址：http://%LOCAL_IP%:3000
start "实验室管理系统-前端" cmd /k "cd /d "%~dp0frontend" && echo ⚛️  启动React前端服务... && npm start"

:: 等待前端启动
echo ⏳ 等待前端服务启动...
timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo           🎉 启动完成！
echo ========================================
echo.
echo 📱 访问地址：
echo   🌐 主系统：http://%LOCAL_IP%:3000
echo   📱 二维码页面：http://%LOCAL_IP%:3000/qr-access.html
echo   🔧 API文档：http://%LOCAL_IP%:8000/docs
echo.
echo 💡 使用提示：
echo   • 首次登录请使用 admin/admin123
echo   • 手机访问请扫描二维码页面的二维码
echo   • 支持PWA安装，可添加到手机主屏幕
echo   • 关闭此窗口不会停止服务
echo.
echo 🛑 停止服务：
echo   • 关闭对应的命令行窗口
echo   • 或运行 stop-system.bat
echo.
echo ❓ 遇到问题？
echo   • 查看 USER_GUIDE.md 使用指南
echo   • 检查防火墙设置
echo   • 确保端口8000和3000未被占用
echo.

:: 询问是否自动打开浏览器
set /p OPEN_BROWSER="是否自动打开浏览器？(Y/n): "
if /i "%OPEN_BROWSER%"=="" set OPEN_BROWSER=Y
if /i "%OPEN_BROWSER%"=="Y" (
    echo 🌐 正在打开浏览器...
    timeout /t 3 /nobreak >nul
    start http://%LOCAL_IP%:3000
)

echo.
echo 📋 系统已在后台运行，可以最小化此窗口
echo 🔄 要重新显示此信息，请重新运行脚本
echo.
pause