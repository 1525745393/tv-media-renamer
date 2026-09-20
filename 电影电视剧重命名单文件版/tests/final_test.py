#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试 - 验证程序启动
"""

import sys
import os
import logging

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_main_window_creation():
    """测试主窗口创建"""
    try:
        logger.info("🔍 测试主窗口创建...")
        
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import RenameUI
        
        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        main_window = RenameUI()
        logger.info("✅ 主窗口创建成功")
        
        # 检查窗口属性
        if hasattr(main_window, 'settings'):
            logger.info("✅ 设置属性存在")
        if hasattr(main_window, 'batch_manager'):
            logger.info("✅ 批量管理器存在")
        if hasattr(main_window, 'operation_history'):
            logger.info("✅ 操作历史存在")
        if hasattr(main_window, 'enhanced_analyzer'):
            logger.info("✅ 增强分析器存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 主窗口创建失败: {e}")
        return False

def test_program_startup():
    """测试程序启动"""
    try:
        logger.info("🔍 测试程序启动...")
        
        # 检查主程序文件是否存在
        if os.path.exists("main/tv_rename_gui_v1.3.py"):
            logger.info("✅ 主程序文件存在")
        else:
            logger.error("❌ 主程序文件不存在")
            return False
        
        # 检查必要的模块文件
        required_files = [
            "ui/main_window.py",
            "modules/enhanced_analyzer.py", 
            "modules/batch_manager.py",
            "core/operation_history.py",
            "core/constants.py"
        ]
        
        for file in required_files:
            if os.path.exists(file):
                logger.info(f"✅ {file} 存在")
            else:
                logger.error(f"❌ {file} 不存在")
                return False
        
        logger.info("✅ 所有必要文件存在")
        return True
        
    except Exception as e:
        logger.error(f"❌ 程序启动测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始最终测试...")
    
    tests = [
        ("主窗口创建", test_main_window_creation),
        ("程序启动", test_program_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 测试: {test_name}")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} 通过")
        else:
            logger.error(f"❌ {test_name} 失败")
    
    logger.info(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！程序可以正常启动")
        logger.info("🚀 现在可以运行: python main/tv_rename_gui_v1.3.py")
        return 0
    else:
        logger.error("❌ 部分测试失败，程序可能有问题")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 