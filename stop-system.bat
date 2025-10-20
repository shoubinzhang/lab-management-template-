@echo off
chcp 65001 >nul
echo ========================================
echo    实验室管理系统 - 停止服务脚本
echo ========================================
echo.

echo 🛑 正在停止实验室管理系统服务...
echo.

:: 停止占用端口8000的进程（后端）
echo 🔍 查找后端服务进程（端口8000）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set BACKEND_PID=%%a
    goto :backend_found
)
set BACKEND_PID=
:backend_found

if "%BACKEND_PID%"=="" (
    echo ℹ️  未找到运行在端口8000的后端服务
) else (
    echo 🛑 停止后端服务（PID: %BACKEND_PID%）...
    taskkill /PID %BACKEND_PID% /F >nul 2>&1
    if errorlevel 1 (
        echo ❌ 停止后端服务失败
    ) else (
        echo ✅ 后端服务已停止
    )
)

:: 停止占用端口3000的进程（前端）
echo 🔍 查找前端服务进程（端口3000）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    set FRONTEND_PID=%%a
    goto :frontend_found
)
set FRONTEND_PID=
:frontend_found

if "%FRONTEND_PID%"=="" (
    echo ℹ️  未找到运行在端口3000的前端服务
) else (
    echo 🛑 停止前端服务（PID: %FRONTEND_PID%）...
    taskkill /PID %FRONTEND_PID% /F >nul 2>&1
    if errorlevel 1 (
        echo ❌ 停止前端服务失败
    ) else (
        echo ✅ 前端服务已停止
    )
)

:: 停止相关的Python和Node.js进程
echo 🔍 清理相关进程...

:: 查找并停止uvicorn进程
tasklist | findstr uvicorn >nul 2>&1
if not errorlevel 1 (
    echo 🛑 停止uvicorn进程...
    taskkill /IM python.exe /F >nul 2>&1
    echo ✅ Python进程已清理
)

:: 查找并停止node进程（谨慎操作，只停止相关的）
for /f "tokens=2" %%a in ('tasklist ^| findstr node.exe') do (
    for /f "tokens=5" %%b in ('netstat -ano ^| findstr :3000 ^| findstr %%a') do (
        taskkill /PID %%a /F >nul 2>&1
        echo ✅ Node.js进程已清理
        goto :node_cleaned
    )
)
:node_cleaned

echo.
echo 🔍 验证服务状态...

:: 验证端口是否已释放
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo ✅ 端口8000已释放
) else (
    echo ⚠️  端口8000仍被占用
)

netstat -an | findstr :3000 >nul
if errorlevel 1 (
    echo ✅ 端口3000已释放
) else (
    echo ⚠️  端口3000仍被占用
)

echo.
echo ========================================
echo           🎉 停止完成！
echo ========================================
echo.
echo 📊 服务状态：
echo   🔴 后端服务：已停止
echo   🔴 前端服务：已停止
echo.
echo 💡 提示：
echo   • 要重新启动服务，请运行 start-system.bat
echo   • 如果端口仍被占用，请重启计算机
echo   • 数据已自动保存，无需担心数据丢失
echo.
echo 🔄 其他操作：
echo   • 重启服务：运行 start-system.bat
echo   • 查看日志：检查对应的命令行窗口
echo   • 环境检查：运行 check-environment.bat
echo.

pause