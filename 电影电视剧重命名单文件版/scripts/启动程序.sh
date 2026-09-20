#!/bin/bash

# 设置编码
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

echo ""
echo "========================================"
echo "   影视文件重命名工具 v1.3 智能分析版"
echo "========================================"
echo ""

echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3环境"
    echo "请确保已安装Python 3.7或更高版本"
    exit 1
fi

echo "✅ Python环境检查通过"

echo ""
echo "🔍 检查依赖模块..."
if ! python3 test_gui.py > /dev/null 2>&1; then
    echo "❌ 错误: 依赖模块检查失败"
    echo "请运行: python3 test_gui.py 查看详细信息"
    exit 1
fi

echo "✅ 依赖模块检查通过"

echo ""
echo "🚀 选择启动方式:"
echo "1. 启动主程序"
echo "2. 运行诊断工具"
echo "3. 运行问题检查"
echo "4. 运行完整性测试"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动程序..."
        echo "正在加载界面，请稍候..."
        python3 tv_rename_gui_v1.3.py
        ;;
    2)
        echo ""
        echo "🔧 启动诊断工具..."
        python3 diagnostic_tools.py
        ;;
    3)
        echo ""
        echo "🔍 运行问题检查..."
        python3 check_problems.py
        ;;
    4)
        echo ""
        echo "🔍 运行完整性测试..."
        python3 test_gui.py
        ;;
    *)
        echo "❌ 无效选择，启动主程序..."
        python3 tv_rename_gui_v1.3.py
        ;;
esac

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 程序运行出错"
    echo "请检查错误信息或查看日志文件"
    exit 1
fi

echo ""
echo "✅ 程序正常退出" 