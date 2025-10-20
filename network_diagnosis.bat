@echo off
echo ========================================
echo       网络连接诊断工具
echo ========================================
echo.
echo 1. 检查端口监听状态...
netstat -an | findstr :8000
echo.
echo 2. 检查防火墙规则...
netsh advfirewall firewall show rule name="Python Web Server Port 8000"
echo.
echo 3. 测试本地访问...
curl -I http://localhost:8000/mobile_login_final
echo.
echo 4. 测试外部IP访问...
curl -I http://172.30.81.97:8000/mobile_login_final
echo.
echo 5. 获取网络信息...
ipconfig | findstr "IPv4"
echo.
echo ========================================
echo 诊断完成！请检查以上输出。
echo ========================================
pause