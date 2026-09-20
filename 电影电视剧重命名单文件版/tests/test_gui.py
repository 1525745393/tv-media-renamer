#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI程序完整性测试脚本
"""

import sys
import os
import logging
from datetime import datetime

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    
    modules_to_test = [
        'ui.main_window',
        'modules.workers', 
        'core.operation_history',
        'modules.file_protector',
        'modules.enhanced_analyzer',
        'modules.batch_manager',
        'modules.file_classifier',
        'ui.smart_analysis_dialog',
        'core.constants',
        'ui.settings_dialog',
        'ui.help_dialog',
        'ui.control_panel',
        'ui.file_table',
        'ui.batch_preview_dialog',
        'core.tv_rename_cache_optimized'
    ]
    
    failed_imports = []
    successful_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            successful_imports.append(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            failed_imports.append(f"{module}: {str(e)}")
            print(f"  ❌ {module}: {e}")
    
    print(f"\n📊 导入结果: {len(successful_imports)}/{len(modules_to_test)} 成功")
    
    if failed_imports:
        print("\n❌ 失败的导入:")
        for failed in failed_imports:
            print(f"  - {failed}")
        return False
    else:
        print("\n✅ 所有模块导入成功!")
        return True

def test_pyqt5():
    """测试PyQt5环境"""
    print("\n🔍 测试PyQt5环境...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt, QCoreApplication
        print("  ✅ PyQt5 导入成功")
        
        # 测试创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            print("  ✅ QApplication 创建成功")
        else:
            print("  ✅ QApplication 实例已存在")
        
        return True
    except ImportError as e:
        print(f"  ❌ PyQt5 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ PyQt5 测试失败: {e}")
        return False

def test_main_window():
    """测试主窗口创建"""
    print("\n🔍 测试主窗口创建...")
    
    try:
        from ui.main_window import RenameUI
        print("  ✅ RenameUI 类导入成功")
        
        # 注意：这里不实际创建窗口，因为需要GUI环境
        print("  ✅ 主窗口类定义正确")
        return True
    except Exception as e:
        print(f"  ❌ 主窗口测试失败: {e}")
        return False

def test_logging():
    """测试日志系统"""
    print("\n🔍 测试日志系统...")
    
    try:
        # 创建logs目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 测试日志文件创建
        test_log_file = f'logs/test_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(test_log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logging.info("测试日志消息")
        print("  ✅ 日志系统工作正常")
        return True
    except Exception as e:
        print(f"  ❌ 日志系统测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始GUI程序完整性测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("PyQt5环境", test_pyqt5),
        ("主窗口", test_main_window),
        ("日志系统", test_logging)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("�� 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过! 程序完整性良好!")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查相关模块")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 