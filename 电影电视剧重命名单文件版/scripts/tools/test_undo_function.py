#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试撤销功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from ui.main_window import RenameUI

def test_undo_function():
    """测试撤销功能"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = RenameUI()
    main_window.show()
    
    print("✅ 撤销功能测试:")
    print("1. 检查撤销按钮是否存在:", main_window.control_panel.btn_undo is not None)
    print("2. 检查重做按钮是否存在:", main_window.control_panel.btn_redo is not None)
    print("3. 检查撤销按钮初始状态:", main_window.control_panel.btn_undo.isEnabled())
    print("4. 检查重做按钮初始状态:", main_window.control_panel.btn_redo.isEnabled())
    print("5. 检查撤销按钮提示:", main_window.control_panel.btn_undo.toolTip())
    print("6. 检查重做按钮提示:", main_window.control_panel.btn_redo.toolTip())
    
    # 测试撤销操作
    print("\n🔄 测试撤销操作:")
    try:
        main_window.undo_operation()
        print("✅ 撤销操作执行成功")
    except Exception as e:
        print(f"❌ 撤销操作失败: {e}")
    
    # 测试重做操作
    print("\n🔄 测试重做操作:")
    try:
        main_window.redo_operation()
        print("✅ 重做操作执行成功")
    except Exception as e:
        print(f"❌ 重做操作失败: {e}")
    
    print("\n🎯 测试完成！")
    print("请检查UI界面中是否显示了撤销和重做按钮")
    
    return app.exec_()

if __name__ == "__main__":
    test_undo_function() 