#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视文件重命名工具 - PyQt5 GUI版本 v1.3 智能分析版
主程序入口
"""

import sys
import os
import logging
import traceback
from datetime import datetime

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyQt5导入
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication

# 导入自定义模块
from core.version import APP_NAME, VERSION
from ui.main_window import RenameUI

def setup_logging():
    """设置日志系统"""
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 主日志文件
    main_log_file = f'logs/media_rename_{datetime.now().strftime("%Y%m%d")}.log'
    main_handler = logging.FileHandler(main_log_file, encoding='utf-8')
    main_handler.setLevel(logging.INFO)
    main_formatter = logging.Formatter(log_format, date_format)
    main_handler.setFormatter(main_formatter)
    
    # 错误日志文件
    error_log_file = f'logs/errors_{datetime.now().strftime("%Y%m%d")}.log'
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(log_format, date_format)
    error_handler.setFormatter(error_formatter)
    
    # 性能日志文件
    performance_log_file = f'logs/performance_{datetime.now().strftime("%Y%m%d")}.log'
    performance_handler = logging.FileHandler(performance_log_file, encoding='utf-8')
    performance_handler.setLevel(logging.DEBUG)
    performance_formatter = logging.Formatter(log_format, date_format)
    performance_handler.setFormatter(performance_formatter)
    
    # 安全日志文件
    security_log_file = f'logs/security_{datetime.now().strftime("%Y%m%d")}.log'
    security_handler = logging.FileHandler(security_log_file, encoding='utf-8')
    security_handler.setLevel(logging.WARNING)
    security_formatter = logging.Formatter(log_format, date_format)
    security_handler.setFormatter(security_formatter)
    
    # GUI日志文件
    gui_log_file = f'logs/gui_{datetime.now().strftime("%Y%m%d")}.log'
    gui_handler = logging.FileHandler(gui_log_file, encoding='utf-8')
    gui_handler.setLevel(logging.INFO)
    gui_formatter = logging.Formatter(log_format, date_format)
    gui_handler.setFormatter(gui_formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(performance_handler)
    root_logger.addHandler(security_handler)
    root_logger.addHandler(gui_handler)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger('PyQt5').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info("日志系统初始化完成")

def setup_application():
    """设置应用程序"""
    # 设置高DPI支持 - 兼容不同PyQt5版本
    try:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} v{VERSION} 智能分析版")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("MediaRenameTool")
    app.setOrganizationDomain("mediarenametool.com")
    # app.setWindowIcon(QIcon("icon.ico"))
    app.setStyle('Fusion')
    return app

def check_dependencies():
    """检查依赖模块"""
    required_modules = [
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
        'core.tv_rename_cache_optimized',
        'ui.check_problems'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            logging.info(f"✅ 模块 {module} 导入成功")
        except ImportError as e:
            missing_modules.append(f"{module}: {str(e)}")
            logging.error(f"❌ 模块 {module} 导入失败: {e}")
    
    if missing_modules:
        error_msg = "缺少必要的依赖模块:\n" + "\n".join(missing_modules)
        logging.error(error_msg)
        return False, error_msg
    
    return True, "所有依赖模块检查通过"

def main():
    """主函数"""
    try:
        # 设置日志系统
        setup_logging()
        logging.info("🚀 启动影视文件重命名工具 v1.3 智能分析版")
        
        # 检查依赖
        deps_ok, deps_msg = check_dependencies()
        if not deps_ok:
            raise ImportError(deps_msg)
        
        # 设置应用程序
        app = setup_application()
        
        # 创建主窗口
        logging.info("创建主窗口...")
        main_window = RenameUI()
        main_window.show()
        
        # 后台升级检测（静默，不影响启动）
        try:
            from core.update_checker import UpdateChecker
            from PyQt5.QtCore import QObject, pyqtSignal

            class _UpdateBridge(QObject):
                """跨线程信号桥：后台线程 → 主线程（QueuedConnection 自动调度）"""
                found = pyqtSignal(object)

            bridge = _UpdateBridge()
            bridge.found.connect(main_window.show_update_banner)

            def _on_update_result(info):
                # 仅当有新版本时通知主线程显示横幅
                if info is not None and info.has_update:
                    bridge.found.emit(info)

            checker = UpdateChecker(version=VERSION)
            checker.check_async(on_result=_on_update_result)
            logging.info("🔍 后台升级检测已启动（当前版本 %s）", VERSION)
        except Exception:
            logging.debug("升级检测初始化失败（忽略）", exc_info=True)
        
        # 记录启动信息
        logging.info("✅ 主窗口已显示，程序启动成功")
        logging.info("🎯 功能特性:")
        logging.info("   • 智能文件识别和分析")
        logging.info("   • 批量重命名操作")
        logging.info("   • 拖拽文件支持")
        logging.info("   • 撤销/重做功能")
        logging.info("   • 实时进度显示")
        logging.info("   • 多线程处理")
        logging.info("   • 操作历史记录")
        logging.info("   • 文件保护机制")
        logging.info("   • 问题诊断功能")
        logging.info("🎮 快捷键:")
        logging.info("   • Ctrl+A: 智能分析")
        logging.info("   • Ctrl+P: 批量预览")
        logging.info("   • Ctrl+Z: 撤销操作")
        logging.info("   • Ctrl+Y: 重做操作")
        logging.info("   • Ctrl+F: 搜索文件")
        logging.info("🔧 诊断工具:")
        logging.info("   • python ui/check_problems.py - 检查系统问题")
        logging.info("   • python tests/test_gui.py - 完整性测试")
        
        # 运行应用程序
        exit_code = app.exec_()
        
        # 记录退出信息
        logging.info(f"应用程序退出，退出码: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        # 记录错误信息
        error_msg = f"程序启动失败: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        
        # 显示错误对话框
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if not QApplication.instance():
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "启动错误", f"程序启动时发生错误:\n{str(e)}\n\n{traceback.format_exc()}")
        except:
            print(f"错误: {error_msg}")
            print(traceback.format_exc())
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 