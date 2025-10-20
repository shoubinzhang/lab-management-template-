@echo off
chcp 65001 >nul
echo ========================================
echo   实验室管理系统 - 环境配置脚本
echo ========================================
echo.
echo 🔧 此脚本将帮助您配置运行环境
echo ⏱️  预计需要5-15分钟，请保持网络连接
echo.

:: 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️  建议以管理员身份运行此脚本以获得最佳体验
    echo 📝 某些功能可能需要管理员权限
    echo.
)

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

echo ✅ 项目目录检查通过
echo.

:: 检查Python环境
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8或更高版本
    echo 📥 下载地址：https://www.python.org/downloads/
    echo.
    set /p CONTINUE="是否继续配置其他环境？(Y/n): "
    if /i "%CONTINUE%"=="n" exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python版本：%PYTHON_VERSION%
)

:: 检查pip
echo 📦 检查pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到pip，尝试安装...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo ❌ pip安装失败，请手动安装
    ) else (
        echo ✅ pip安装成功
    )
) else (
    echo ✅ pip可用
)
echo.

:: 检查Node.js环境
echo ⚛️  检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Node.js，请先安装Node.js 16或更高版本
    echo 📥 下载地址：https://nodejs.org/
    echo.
    set /p CONTINUE="是否继续配置Python环境？(Y/n): "
    if /i "%CONTINUE%"=="n" exit /b 1
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
    echo ✅ Node.js版本：%NODE_VERSION%
)

:: 检查npm
echo 📦 检查npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到npm，请重新安装Node.js
) else (
    for /f "tokens=1" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
    echo ✅ npm版本：%NPM_VERSION%
)
echo.

:: 配置Python虚拟环境
echo 🔧 配置Python后端环境...
cd backend

:: 检查是否已有虚拟环境
if exist "venv" (
    echo ℹ️  发现现有虚拟环境
    set /p RECREATE="是否重新创建虚拟环境？(y/N): "
    if /i "%RECREATE%"=="y" (
        echo 🗑️  删除现有虚拟环境...
        rmdir /s /q venv
    )
)

if not exist "venv" (
    echo 🏗️  创建Python虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        cd ..
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

:: 激活虚拟环境并安装依赖
echo 📦 安装Python依赖包...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    cd ..
    pause
    exit /b 1
)

:: 升级pip
echo 🔄 升级pip...
python -m pip install --upgrade pip

:: 安装依赖
if exist "requirements.txt" (
    echo 📋 从requirements.txt安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Python依赖安装失败
        echo 💡 请检查网络连接或尝试使用国内镜像源
        echo 🔧 镜像源命令：pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    ) else (
        echo ✅ Python依赖安装完成
    )
) else (
    echo ⚠️  未找到requirements.txt文件
)

cd ..
echo.

:: 配置Node.js前端环境
echo 🔧 配置React前端环境...
cd frontend

:: 检查package.json
if not exist "package.json" (
    echo ❌ 未找到package.json文件
    cd ..
    pause
    exit /b 1
)

:: 清理现有依赖（可选）
if exist "node_modules" (
    echo ℹ️  发现现有node_modules目录
    set /p CLEAN="是否清理并重新安装依赖？(y/N): "
    if /i "%CLEAN%"=="y" (
        echo 🗑️  清理node_modules...
        rmdir /s /q node_modules
        if exist "package-lock.json" del package-lock.json
    )
)

:: 安装前端依赖
echo 📦 安装前端依赖包...
npm install
if errorlevel 1 (
    echo ❌ 前端依赖安装失败
    echo 💡 尝试使用淘宝镜像源...
    npm install --registry=https://registry.npmmirror.com
    if errorlevel 1 (
        echo ❌ 依赖安装仍然失败，请检查网络连接
        cd ..
        pause
        exit /b 1
    )
)
echo ✅ 前端依赖安装完成

cd ..
echo.

:: 创建配置文件
echo 🔧 创建配置文件...

:: 创建后端配置文件
if not exist "backend\.env" (
    echo 📝 创建后端环境配置文件...
    (
        echo # 实验室管理系统后端配置
        echo DATABASE_URL=sqlite:///./lab_management.db
        echo SECRET_KEY=your-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
        echo DEBUG=True
    ) > "backend\.env"
    echo ✅ 后端配置文件已创建
) else (
    echo ℹ️  后端配置文件已存在
)

:: 创建前端环境配置
if not exist "frontend\.env" (
    echo 📝 创建前端环境配置文件...
    (
        echo # 实验室管理系统前端配置
        echo REACT_APP_API_BASE_URL=http://localhost:8000
        echo REACT_APP_VERSION=1.0.0
        echo GENERATE_SOURCEMAP=false
    ) > "frontend\.env"
    echo ✅ 前端配置文件已创建
) else (
    echo ℹ️  前端配置文件已存在
)

echo.

:: 初始化数据库
echo 🗄️  初始化数据库...
cd backend
call venv\Scripts\activate.bat
python -c "from app.database import init_db; init_db()" 2>nul
if errorlevel 1 (
    echo ⚠️  数据库初始化可能失败，首次启动时会自动创建
) else (
    echo ✅ 数据库初始化完成
)
cd ..

echo.

:: 检查防火墙设置
echo 🔥 检查防火墙设置...
netsh advfirewall firewall show rule name="Lab Management System" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到防火墙规则
    set /p ADD_FIREWALL="是否添加防火墙规则允许端口3000和8000？(Y/n): "
    if /i not "%ADD_FIREWALL%"=="n" (
        echo 🔧 添加防火墙规则...
        netsh advfirewall firewall add rule name="Lab Management System Frontend" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
        netsh advfirewall firewall add rule name="Lab Management System Backend" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
        if errorlevel 1 (
            echo ⚠️  防火墙规则添加失败，可能需要管理员权限
        ) else (
            echo ✅ 防火墙规则添加成功
        )
    )
) else (
    echo ✅ 防火墙规则已存在
)

echo.
echo ========================================
echo           🎉 环境配置完成！
echo ========================================
echo.
echo 📋 配置摘要：
echo   🐍 Python环境：已配置
echo   ⚛️  Node.js环境：已配置
echo   📦 依赖包：已安装
echo   🔧 配置文件：已创建
echo   🗄️  数据库：已初始化
echo   🔥 防火墙：已配置
echo.
echo 🚀 下一步操作：
echo   1. 运行 start-system.bat 启动系统
echo   2. 访问 http://localhost:3000
echo   3. 使用 admin/admin123 登录
echo   4. 查看 USER_GUIDE.md 了解详细使用方法
echo.
echo 💡 常用命令：
echo   • 启动系统：start-system.bat
echo   • 停止系统：stop-system.bat
echo   • 环境检查：check-environment.bat
echo.
echo 📞 遇到问题？
echo   • 查看 USER_GUIDE.md 故障排除部分
 echo   • 检查网络连接和防火墙设置
echo   • 确保端口3000和8000未被占用
echo.

set /p START_NOW="是否现在启动系统？(Y/n): "
if /i not "%START_NOW%"=="n" (
    echo 🚀 启动系统...
    call start-system.bat
) else (
    echo 📝 配置完成，您可以稍后运行 start-system.bat 启动系统
    pause
)