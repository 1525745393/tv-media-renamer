#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI界面完整性测试
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ui_components():
    """测试UI组件是否完整"""
    print("🔍 开始UI界面完整性测试...")
    
    try:
        # 测试主窗口
        print("1. 测试主窗口模块...")
        from ui.main_window import RenameUI
        print("   ✅ 主窗口模块导入成功")
        
        # 测试设置对话框
        print("2. 测试设置对话框...")
        from ui.settings_dialog import SettingsDialog
        print("   ✅ 设置对话框模块导入成功")
        
        # 测试帮助对话框
        print("3. 测试帮助对话框...")
        from ui.help_dialog import HelpDialog
        print("   ✅ 帮助对话框模块导入成功")
        
        # 测试控制面板
        print("4. 测试控制面板...")
        from ui.control_panel import ControlPanel
        print("   ✅ 控制面板模块导入成功")
        
        # 测试文件表格
        print("5. 测试文件表格...")
        from ui.file_table import FileTableWidget
        print("   ✅ 文件表格模块导入成功")
        
        # 测试批量预览对话框
        print("6. 测试批量预览对话框...")
        from ui.batch_preview_dialog import BatchPreviewDialog
        print("   ✅ 批量预览对话框模块导入成功")
        
        # 测试智能分析对话框
        print("7. 测试智能分析对话框...")
        from ui.smart_analysis_dialog import SmartAnalysisDialog
        print("   ✅ 智能分析对话框模块导入成功")
        
        # 测试问题检查模块
        print("8. 测试问题检查模块...")
        from ui.check_problems import check_imports, check_syntax, check_dependencies
        print("   ✅ 问题检查模块导入成功")
        
        # 测试核心引擎
        print("9. 测试核心引擎...")
        from core.tv_rename_cache_optimized import MediaRenamer, PatternRecognizer
        print("   ✅ 核心引擎模块导入成功")
        
        # 测试性能监控
        print("10. 测试性能监控...")
        from core.performance.performance_monitor import PerformanceMonitor
        print("   ✅ 性能监控模块导入成功")
        
        # 测试安全管理
        print("11. 测试安全管理...")
        from core.security.security_manager import SecurityManager
        print("   ✅ 安全管理模块导入成功")
        
        # 测试工作线程
        print("12. 测试工作线程...")
        from modules.workers import ScanWorker, RenameWorker
        print("   ✅ 工作线程模块导入成功")
        
        print("\n🎉 所有UI组件测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_ui_functionality():
    """测试UI功能是否正常"""
    print("\n🔧 开始UI功能测试...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import RenameUI
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("1. 创建主窗口...")
        main_window = RenameUI()
        print("   ✅ 主窗口创建成功")
        
        # 测试窗口属性
        print("2. 测试窗口属性...")
        assert hasattr(main_window, 'settings'), "主窗口缺少settings属性"
        assert hasattr(main_window, 'scan_worker'), "主窗口缺少scan_worker属性"
        assert hasattr(main_window, 'rename_worker'), "主窗口缺少rename_worker属性"
        assert hasattr(main_window, 'results'), "主窗口缺少results属性"
        assert hasattr(main_window, 'renamer'), "主窗口缺少renamer属性"
        print("   ✅ 窗口属性检查通过")
        
        # 测试方法存在性
        print("3. 测试方法存在性...")
        assert hasattr(main_window, 'setup_ui'), "主窗口缺少setup_ui方法"
        assert hasattr(main_window, 'setup_connections'), "主窗口缺少setup_connections方法"
        assert hasattr(main_window, 'setup_shortcuts'), "主窗口缺少setup_shortcuts方法"
        assert hasattr(main_window, 'select_folder'), "主窗口缺少select_folder方法"
        assert hasattr(main_window, 'scan_folder'), "主窗口缺少scan_folder方法"
        assert hasattr(main_window, 'do_rename'), "主窗口缺少do_rename方法"
        print("   ✅ 方法存在性检查通过")
        
        # 测试设置对话框
        print("4. 测试设置对话框...")
        from ui.settings_dialog import SettingsDialog
        settings_dialog = SettingsDialog({})
        print("   ✅ 设置对话框创建成功")
        
        # 测试帮助对话框
        print("5. 测试帮助对话框...")
        from ui.help_dialog import HelpDialog
        help_dialog = HelpDialog()
        print("   ✅ 帮助对话框创建成功")
        
        print("\n🎉 所有UI功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ UI功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始UI界面完整性测试")
    print("=" * 50)
    
    # 测试组件导入
    components_ok = test_ui_components()
    
    if components_ok:
        # 测试功能
        functionality_ok = test_ui_functionality()
        
        if functionality_ok:
            print("\n🎉 UI界面完整性测试全部通过！")
            print("✅ 界面组件完整")
            print("✅ 功能模块正常")
            print("✅ 可以正常使用")
            return True
        else:
            print("\n❌ UI功能测试失败")
            return False
    else:
        print("\n❌ UI组件测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 