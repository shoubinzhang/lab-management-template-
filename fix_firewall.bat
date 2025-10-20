@echo off
echo ========================================
echo   实验室管理系统防火墙配置工具
echo ========================================
echo.
echo 正在检查防火墙状态...
echo.

REM 检查8000端口是否被监听
netstat -an | findstr ":8000"
if %errorlevel% equ 0 (
    echo ✅ 8000端口正在监听
) else (
    echo ❌ 8000端口未监听，请检查服务器是否启动
    pause
    exit /b 1
)

echo.
echo 检查防火墙规则...
netsh advfirewall firewall show rule name="Python Web Server Port 8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 防火墙规则已存在
    goto :TEST_CONNECTION
)

echo.
echo ❌ 防火墙规则不存在，需要管理员权限添加...
echo 请右键点击此批处理文件，选择"以管理员身份运行"
echo 或者手动执行以下命令：
echo netsh advfirewall firewall add rule name="Python Web Server Port 8000" dir=in action=allow protocol=TCP localport=8000
echo.
pause
exit /b 1

:TEST_CONNECTION
echo.
echo 测试本地连接...
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/health
if %errorlevel% equ 0 (
    echo ✅ 本地连接正常
) else (
    echo ❌ 本地连接失败
)

echo.
echo 测试外部IP连接...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr "IPv4"') do set IP=%%i
set IP=%IP: =%
echo 检测到IP地址: %IP%
curl -s -o nul -w "%%{http_code}" http://%IP%:8000/api/health
if %errorlevel% equ 0 (
    echo ✅ 外部IP连接正常
    echo.
    echo 📱 移动端访问地址：http://%IP%:8000/mobile_login_final
) else (
    echo ❌ 外部IP连接失败
    echo.
    echo 🔧 请检查防火墙设置
)

echo.
echo ========================================
echo   配置完成！
echo ========================================
echo.
pause