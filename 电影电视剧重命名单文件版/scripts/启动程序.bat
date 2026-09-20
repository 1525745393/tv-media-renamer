@echo off
chcp 65001 >nul
title 影视文件重命名工具 v1.3

echo.
echo ========================================
echo    影视文件重命名工具 v1.3 智能分析版
echo ========================================
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请确保已安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

echo.
echo 🔍 检查依赖模块...
python test_gui.py >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 依赖模块检查失败
    echo 请运行: python test_gui.py 查看详细信息
    pause
    exit /b 1
)

echo ✅ 依赖模块检查通过

echo.
echo 🚀 选择启动方式:
echo 1. 启动主程序
echo 2. 运行诊断工具
echo 3. 运行问题检查
echo 4. 运行完整性测试
echo.
set /p choice="请选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动程序...
    echo 正在加载界面，请稍候...
    python tv_rename_gui_v1.3.py
) else if "%choice%"=="2" (
    echo.
    echo 🔧 启动诊断工具...
    python diagnostic_tools.py
) else if "%choice%"=="3" (
    echo.
    echo 🔍 运行问题检查...
    python check_problems.py
) else if "%choice%"=="4" (
    echo.
    echo 🔍 运行完整性测试...
    python test_gui.py
) else (
    echo ❌ 无效选择，启动主程序...
    python tv_rename_gui_v1.3.py
)

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    echo 请检查错误信息或查看日志文件
    pause
    exit /b 1
)

echo.
echo ✅ 程序正常退出
pause 