#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块 - 影视文件重命名工具 v1.3
"""

import os
import logging
import psutil
import time
import gc
from typing import Dict, Any, List, Optional

# PyQt5导入
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, QSplitter, QStatusBar, QProgressBar, QMessageBox, QFileDialog, QDialog, QProgressDialog
from PyQt5.QtCore import Qt, QTimer, QUrl, QSettings
from PyQt5.QtGui import QKeySequence, QDesktopServices

# 导入自定义模块
from core.constants import DEFAULT_SETTINGS
from core.tv_rename_cache_optimized import MediaRenamer
from core.operation_history import EnhancedOperationHistory
from modules.file_protector import FileProtector
from modules.enhanced_analyzer import EnhancedAnalyzer
from modules.batch_manager import EnhancedBatchManager
from modules.file_classifier import FileClassifier
from modules.workers import ScanWorker, RenameWorker
from ui.control_panel import ControlPanel
from ui.file_table import FileTableWidget
from ui.settings_dialog import SettingsDialog
from ui.help_dialog import HelpDialog
from ui.batch_preview_dialog import BatchPreviewDialog
from ui.smart_analysis_dialog import SmartAnalysisDialog

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.memory_threshold = 80  # 内存使用阈值（%）
        self.warning_threshold = 70  # 警告阈值（%）
        self.check_interval = 5000  # 检查间隔（毫秒）
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_memory_usage)
        
    def start_monitoring(self):
        """开始监控"""
        self.timer.start(self.check_interval)
        logger.info("🔍 内存监控已启动")
        
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
        logger.info("🔍 内存监控已停止")
        
    def check_memory_usage(self):
        """检查内存使用情况"""
        try:
            memory_info = self.get_memory_info()
            
            # 更新状态栏显示
            if self.parent and hasattr(self.parent, 'statusBar'):
                status_text = f"内存: {memory_info['process_mb']:.1f}MB | 系统: {memory_info['system_percent']:.1f}%"
                self.parent.statusBar().showMessage(status_text)
            
            # 检查是否需要优化内存
            if memory_info['system_percent'] > self.memory_threshold:
                self.optimize_memory()
                logger.warning(f"⚠️ 内存使用率过高: {memory_info['system_percent']:.1f}%")
                
            elif memory_info['system_percent'] > self.warning_threshold:
                logger.info(f"📊 内存使用率较高: {memory_info['system_percent']:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ 内存监控错误: {e}")
    
    def get_memory_info(self) -> Dict[str, float]:
        """获取内存信息"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            return {
                'system_percent': memory.percent,
                'process_mb': process.memory_info().rss / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'total_mb': memory.total / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"❌ 获取内存信息失败: {e}")
            return {
                'system_percent': 0,
                'process_mb': 0,
                'available_mb': 0,
                'total_mb': 0
            }
    
    def optimize_memory(self):
        """优化内存使用"""
        try:
            logger.info("🧹 开始内存优化...")
            
            # 清理缓存
            self.clear_caches()
            
            # 强制垃圾回收
            gc.collect()
            
            # 检查优化效果
            memory_info = self.get_memory_info()
            logger.info(f"✅ 内存优化完成，当前使用率: {memory_info['system_percent']:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ 内存优化失败: {e}")
    
    def clear_caches(self):
        """清理各种缓存"""
        try:
            # 清理Python缓存
            import sys
            for module in list(sys.modules.keys()):
                module_obj = sys.modules[module]
                if hasattr(module_obj, '__cache__') and isinstance(module_obj.__cache__, dict):
                    module_obj.__cache__.clear()
            
            # 清理其他可能的缓存
            if hasattr(self.parent, 'cache') and self.parent.cache is not None:
                self.parent.cache.clear_expired()
                
        except Exception as e:
            logger.error(f"❌ 清理缓存失败: {e}")
    
    def get_memory_report(self) -> str:
        """获取内存使用报告"""
        try:
            memory_info = self.get_memory_info()
            return f"""
内存使用报告:
- 进程内存: {memory_info['process_mb']:.1f} MB
- 系统内存使用率: {memory_info['system_percent']:.1f}%
- 可用内存: {memory_info['available_mb']:.1f} MB
- 总内存: {memory_info['total_mb']:.1f} MB
- 状态: {'正常' if memory_info['system_percent'] < self.warning_threshold else '警告' if memory_info['system_percent'] < self.memory_threshold else '危险'}
"""
        except Exception as e:
            return f"获取内存报告失败: {e}"


class RenameUI(QWidget):
    """主界面类"""
    
    def __init__(self) -> None:
        super().__init__()
        self.settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.scan_worker: Optional[ScanWorker] = None
        self.rename_worker: Optional[RenameWorker] = None
        self.results: List[Dict[str, Any]] = []
        self.renamer: Optional[MediaRenamer] = None
        self._update_banner_widgets: List[QWidget] = []
        
        # 启用拖拽支持
        self.setAcceptDrops(True)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.setStyleSheet(self.setup_styles())
        
        # 初始化内存监控器
        self.memory_monitor = MemoryMonitor(self)
        
        # 启动内存监控定时器
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)  # 每5秒更新一次
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        
        # 启动内存监控
        self.memory_monitor.start_monitoring()
        
        # 操作历史记录
        self.operation_history = EnhancedOperationHistory(
            history_file="operation_history.json",
            max_history=self.settings.get("max_history", 100)
        )
        
        # 文件保护
        self.file_protector = FileProtector(self.settings)
        
        # 增强文件分析器
        self.enhanced_analyzer = EnhancedAnalyzer(self.settings)
        
        # 批量操作管理器
        self.batch_manager = EnhancedBatchManager()
        
        # 文件分类器
        self.file_classifier = FileClassifier(self.settings)
        
        # 初始化撤销重做按钮状态
        self.update_undo_redo_buttons()
        
    def setup_ui(self) -> None:
        """设置主界面"""
        self.setWindowTitle("影视文件重命名工具 - PyQt5 v1.3")
        self.resize(1400, 800)
        self.setMinimumSize(1000, 600)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加标题栏
        title_layout = QHBoxLayout()
        title_icon = QLabel("🎬")
        title_icon.setStyleSheet("font-size: 32px; margin-right: 10px;")
        title_text = QLabel("影视文件重命名工具")
        title_text.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 0;")
        subtitle_text = QLabel("智能识别 · 安全重命名 · 批量处理")
        subtitle_text.setStyleSheet("font-size: 14px; color: #7f8c8d; margin: 0;")
        
        title_left = QVBoxLayout()
        title_left.addWidget(title_text)
        title_left.addWidget(subtitle_text)
        
        title_layout.addWidget(title_icon)
        title_layout.addLayout(title_left)
        title_layout.addStretch()
        
        # 添加版本信息
        version_label = QLabel("v1.3")
        version_label.setStyleSheet("font-size: 12px; color: #95a5a6; padding: 5px 10px; background-color: #ecf0f1; border-radius: 10px;")
        title_layout.addWidget(version_label)

        # NAS 服务（远程模式）入口
        self.remote_btn = QPushButton("🌐 NAS 服务")
        self.remote_btn.setToolTip("连接 NAS 上的重命名服务（远程模式）")
        self.remote_btn.setStyleSheet(
            "QPushButton { font-size: 13px; color: white; background-color: #2c3e50;"
            " border-radius: 10px; padding: 5px 14px; }"
            "QPushButton:hover { background-color: #34495e; }")
        title_layout.addWidget(self.remote_btn)
        
        main_layout.addLayout(title_layout)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("QSplitter::handle { background-color: #bdc3c7; border-radius: 1px; } QSplitter::handle:hover { background-color: #95a5a6; }")
        
        # 左侧控制面板
        self.control_panel = ControlPanel()
        splitter.addWidget(self.control_panel)
        
        # 右侧文件表格区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # 搜索和筛选区域
        search_group = QGroupBox("🔍 搜索和筛选")
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.search_label = QLabel("搜索:")
        self.search_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("输入文件名、标题或类型进行搜索...")
        self.search_box.textChanged.connect(self.filter_files)
        self.search_box.setStyleSheet("QLineEdit { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; background-color: white; } QLineEdit:focus { border-color: #3498db; outline: none; }")
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["全部类型", "电影", "电视剧", "特辑"])
        self.filter_type_combo.currentTextChanged.connect(self.filter_files)
        self.filter_type_combo.setStyleSheet("QComboBox { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; background-color: white; min-width: 100px; } QComboBox:focus { border-color: #3498db; } QComboBox::drop-down { border: none; width: 20px; } QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #7f8c8d; }")
        
        self.clear_filter_btn = QPushButton("🗑️ 清除筛选")
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        self.clear_filter_btn.setStyleSheet("QPushButton { background-color: #e74c3c; border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        
        self.batch_preview_btn = QPushButton("👁️ 批量预览")
        self.batch_preview_btn.clicked.connect(self.show_batch_preview)
        self.batch_preview_btn.setToolTip("查看所有文件的重命名预览(Ctrl+P)")
        self.batch_preview_btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9b59b6, stop:1 #8e44ad); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e44ad, stop:1 #7d3c98); }")
        
        self.smart_analysis_btn = QPushButton("🧠 智能分析")
        self.smart_analysis_btn.clicked.connect(self.show_smart_analysis)
        self.smart_analysis_btn.setToolTip("智能分析文件内容、分类和批量操作(Ctrl+A)")
        self.smart_analysis_btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e67e22, stop:1 #d35400); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d35400, stop:1 #ba4a00); }")
        
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_box, 1)
        search_layout.addWidget(QLabel("类型:"))
        search_layout.addWidget(self.filter_type_combo)
        search_layout.addWidget(self.clear_filter_btn)
        search_layout.addWidget(self.batch_preview_btn)
        search_layout.addWidget(self.smart_analysis_btn)
        search_group.setLayout(search_layout)
        
        # 文件表格
        self.file_table = FileTableWidget()
        
        right_layout.addWidget(search_group)
        right_layout.addWidget(self.file_table)
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)
        
        # 添加状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #ecf0f1; border-top: 1px solid #bdc3c7; color: #2c3e50; font-size: 12px; }")
        
        # 状态标签
        self.status_label = QLabel("🚀 就绪")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.status_bar.addWidget(self.status_label)
        
        # 进度指示器
        self.progress_indicator = QProgressBar()
        self.progress_indicator.setVisible(False)
        self.progress_indicator.setMaximumWidth(200)
        self.progress_indicator.setStyleSheet("QProgressBar { border: 1px solid #bdc3c7; border-radius: 4px; text-align: center; background-color: #ecf0f1; color: #2c3e50; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); border-radius: 3px; }")
        self.status_bar.addPermanentWidget(self.progress_indicator)
        
        # 内存使用指示器
        self.memory_label = QLabel("💾 内存: 0 MB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        # 将状态栏添加到主布局
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # 初始化状态
        self.update_status("🚀 就绪")
        
    def setup_connections(self) -> None:
        """设置信号连接"""
        # 控制面板连接
        self.control_panel.btn_select.clicked.connect(self.select_folder)
        self.control_panel.btn_scan.clicked.connect(self.scan_folder)
        self.control_panel.btn_rename.clicked.connect(self.do_rename)
        self.control_panel.btn_theme.clicked.connect(self.toggle_theme)
        self.control_panel.btn_settings.clicked.connect(self.open_settings)
        self.control_panel.btn_help.clicked.connect(self.open_help)
        self.control_panel.btn_cancel.clicked.connect(self.cancel_operation)
        self.control_panel.btn_undo.clicked.connect(self.undo_operation)
        self.control_panel.btn_redo.clicked.connect(self.redo_operation)
        
        # 模式切换
        self.control_panel.radio_rename.toggled.connect(self.on_mode_changed)

        # NAS 服务（远程模式）
        self.remote_btn.clicked.connect(self.open_remote_mode)

        # 添加快捷键支持
        self.setup_shortcuts()

    def open_remote_mode(self) -> None:
        """打开 NAS 服务远程模式对话框。"""
        from ui.remote_mode import RemoteModeDialog
        RemoteModeDialog(self).exec_()
        
    def setup_styles(self) -> str:
        """设置样式"""
        # 返回样式字符串
        styles = (
            "QWidget {"
            "    background-color: #f8f9fa;"
            "    color: #2c3e50;"
            "    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;"
            "}"
            ""
            "QMainWindow {"
            "    background-color: #f8f9fa;"
            "}"
            ""
            "QGroupBox {"
            "    font-weight: bold;"
            "    border: 2px solid #dee2e6;"
            "    border-radius: 8px;"
            "    margin-top: 1ex;"
            "    padding-top: 15px;"
            "    background-color: white;"
            "}"
            ""
            "QGroupBox::title {"
            "    subcontrol-origin: margin;"
            "    left: 15px;"
            "    padding: 0 8px 0 8px;"
            "    color: #495057;"
            "    font-size: 14px;"
            "}"
            ""
            "QPushButton {"
            "    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);"
            "    border: none;"
            "    color: white;"
            "    padding: 10px 20px;"
            "    text-align: center;"
            "    font-size: 14px;"
            "    font-weight: bold;"
            "    border-radius: 6px;"
            "    min-height: 20px;"
            "}"
            ""
            "QPushButton:hover {"
            "    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);"
            "    border: 2px solid #004085;"
            "}"
            ""
            "QPushButton:pressed {"
            "    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004085, stop:1 #002752);"
            "    border: 2px solid #002752;"
            "}"
            ""
            "QPushButton:disabled {"
            "    background-color: #6c757d;"
            "    color: #adb5bd;"
            "}"
            ""
            "QLineEdit {"
            "    border: 2px solid #ced4da;"
            "    border-radius: 6px;"
            "    padding: 8px 12px;"
            "    font-size: 14px;"
            "    background-color: white;"
            "}"
            ""
            "QLineEdit:focus {"
            "    border-color: #007bff;"
            "    outline: none;"
            "}"
            ""
            "QComboBox {"
            "    border: 2px solid #ced4da;"
            "    border-radius: 6px;"
            "    padding: 8px 12px;"
            "    font-size: 14px;"
            "    background-color: white;"
            "    min-height: 20px;"
            "}"
            ""
            "QComboBox:focus {"
            "    border-color: #007bff;"
            "}"
            ""
            "QComboBox::drop-down {"
            "    border: none;"
            "    width: 20px;"
            "}"
            ""
            "QComboBox::down-arrow {"
            "    image: none;"
            "    border-left: 5px solid transparent;"
            "    border-right: 5px solid transparent;"
            "    border-top: 5px solid #6c757d;"
            "}"
            ""
            "QTableWidget {"
            "    gridline-color: #dee2e6;"
            "    selection-background-color: #e3f2fd;"
            "    alternate-background-color: #f8f9fa;"
            "    background-color: white;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 6px;"
            "}"
            ""
            "QHeaderView::section {"
            "    background-color: #f8f9fa;"
            "    padding: 10px;"
            "    border: none;"
            "    border-bottom: 2px solid #dee2e6;"
            "    font-weight: bold;"
            "    color: #495057;"
            "}"
            ""
            "QHeaderView::section:hover {"
            "    background-color: #e9ecef;"
            "}"
            ""
            "QStatusBar {"
            "    background-color: #f8f9fa;"
            "    border-top: 1px solid #dee2e6;"
            "    color: #495057;"
            "}"
            ""
            "QProgressBar {"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 4px;"
            "    text-align: center;"
            "    background-color: #e9ecef;"
            "}"
            ""
            "QProgressBar::chunk {"
            "    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);"
            "    border-radius: 3px;"
            "}"
            ""
            "QRadioButton {"
            "    font-size: 14px;"
            "    color: #495057;"
            "}"
            ""
            "QRadioButton::indicator {"
            "    width: 18px;"
            "    height: 18px;"
            "}"
            ""
            "QRadioButton::indicator:unchecked {"
            "    border: 2px solid #ced4da;"
            "    border-radius: 9px;"
            "    background-color: white;"
            "}"
            ""
            "QRadioButton::indicator:checked {"
            "    border: 2px solid #007bff;"
            "    border-radius: 9px;"
            "    background-color: #007bff;"
            "}"
            ""
            "QLabel {"
            "    color: #495057;"
            "    font-size: 14px;"
            "}"
            ""
            "QSplitter::handle {"
            "    background-color: #dee2e6;"
            "    border-radius: 1px;"
            "}"
            ""
            "QSplitter::handle:hover {"
            "    background-color: #adb5bd;"
            "}"
        )
        return styles
        
    def setup_shortcuts(self) -> None:
        """设置快捷键（增强版）"""
        from PyQt5.QtWidgets import QShortcut
        
        # 文件操作快捷键
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.select_folder)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.scan_folder)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.do_rename)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.show_batch_preview)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.open_settings)
        QShortcut(QKeySequence("F1"), self).activated.connect(self.open_help)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.cancel_operation)
        
        # 筛选和搜索快捷键
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.focus_search_box)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.clear_filters)
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.show_smart_analysis)
        
        # 主题切换快捷键
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.toggle_theme)
        
        # 撤销和重做快捷键
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(lambda: self.undo_operation())
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(lambda: self.redo_operation())
        
        # 新增快捷键
        QShortcut(QKeySequence("F2"), self).activated.connect(self.rename_selected)  # 重命名选中文件
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.delete_selected)  # 删除选中文件
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.select_all_files)  # 全选文件
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.deselect_all_files)  # 取消全选
        QShortcut(QKeySequence("F3"), self).activated.connect(self.show_performance_report)  # 性能报告
        QShortcut(QKeySequence("F4"), self).activated.connect(self.show_memory_report)  # 内存报告
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.show_shortcuts_help)  # 快捷键帮助
        
        # 表格操作快捷键
        QShortcut(QKeySequence("Up"), self).activated.connect(self.select_previous_file)
        QShortcut(QKeySequence("Down"), self).activated.connect(self.select_next_file)
        QShortcut(QKeySequence("Home"), self).activated.connect(self.select_first_file)
        QShortcut(QKeySequence("End"), self).activated.connect(self.select_last_file)
        
        logger.info("✅ 快捷键系统已初始化")
    
    def show_shortcuts_help(self) -> None:
        """显示快捷键帮助"""
        help_text = """
🎮 快捷键帮助

📁 文件操作:
• Ctrl+O: 选择文件夹
• F5: 扫描文件夹
• Ctrl+R: 执行重命名
• Ctrl+P: 批量预览
• Ctrl+S: 打开设置
• F1: 帮助
• Ctrl+Q: 退出程序
• Escape: 取消操作

🔍 搜索和筛选:
• Ctrl+F: 聚焦搜索框
• Ctrl+L: 清除筛选
• Ctrl+A: 智能分析

🎨 界面操作:
• Ctrl+T: 切换主题
• Ctrl+Z: 撤销操作
• Ctrl+Y: 重做操作

📋 文件管理:
• F2: 重命名选中文件
• Delete: 删除选中文件
• Ctrl+A: 全选文件
• Ctrl+D: 取消全选

📊 系统信息:
• F3: 性能报告
• F4: 内存报告
• Ctrl+H: 快捷键帮助

📋 表格操作:
• ↑/↓: 选择上一个/下一个文件
• Home/End: 选择第一个/最后一个文件

💡 提示: 这些快捷键可以大大提高操作效率！
        """
        
        QMessageBox.information(self, "🎮 快捷键帮助", help_text)
    
    def rename_selected(self) -> None:
        """重命名选中的文件"""
        current_row = self.file_table.currentRow()
        if current_row >= 0 and current_row < len(self.results):
            result = self.results[current_row]
            self.show_rename_dialog(result)
        else:
            QMessageBox.information(self, "提示", "请先选择一个文件")
    
    def delete_selected(self) -> None:
        """删除选中的文件"""
        current_row = self.file_table.currentRow()
        if current_row >= 0 and current_row < len(self.results):
            result = self.results[current_row]
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除文件 '{result.get('original_name', '')}' 吗？\n此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 标记为删除
                result['status'] = '删除'
                self.file_table.update_data(self.results)
                self.update_status(f"✅ 已标记删除: {result.get('original_name', '')}")
        else:
            QMessageBox.information(self, "提示", "请先选择一个文件")
    
    def select_all_files(self) -> None:
        """全选文件"""
        self.file_table.selectAll()
        self.update_status(f"✅ 已全选 {len(self.results)} 个文件")
    
    def deselect_all_files(self) -> None:
        """取消全选"""
        self.file_table.clearSelection()
        self.update_status("✅ 已取消全选")
    
    def show_memory_report(self) -> None:
        """显示内存报告"""
        if hasattr(self, 'memory_monitor'):
            report = self.memory_monitor.get_memory_report()
            QMessageBox.information(self, "💾 内存报告", report)
        else:
            QMessageBox.information(self, "内存报告", "内存监控未启用")
    
    def select_previous_file(self) -> None:
        """选择上一个文件"""
        current_row = self.file_table.currentRow()
        if current_row > 0:
            self.file_table.selectRow(current_row - 1)
    
    def select_next_file(self) -> None:
        """选择下一个文件"""
        current_row = self.file_table.currentRow()
        if current_row < self.file_table.rowCount() - 1:
            self.file_table.selectRow(current_row + 1)
    
    def select_first_file(self) -> None:
        """选择第一个文件"""
        if self.file_table.rowCount() > 0:
            self.file_table.selectRow(0)
    
    def select_last_file(self) -> None:
        """选择最后一个文件"""
        row_count = self.file_table.rowCount()
        if row_count > 0:
            self.file_table.selectRow(row_count - 1)
    
    def show_rename_dialog(self, result: Dict[str, Any]) -> None:
        """显示重命名对话框"""
        from PyQt5.QtWidgets import QInputDialog
        
        original_name = result.get('original_name', '')
        new_name = result.get('new_name', '')
        
        new_name, ok = QInputDialog.getText(
            self, 
            "重命名文件", 
            f"重命名文件: {original_name}\n\n新文件名:",
            text=new_name
        )
        
        if ok and new_name:
            result['new_name'] = new_name
            self.file_table.update_data(self.results)
            self.update_status(f"✅ 已更新重命名: {original_name} → {new_name}")
    
    def select_folder(self) -> None:
        """选择文件夹"""
        # 获取当前文件夹路径，如果没有则使用默认值
        current_folder = self.settings.get("folder_path", "")
        
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择影视文件夹", 
            current_folder
        )
        if folder:
            self.settings["folder_path"] = folder
            self.control_panel.folder_path.setText(folder)
            
    def on_mode_changed(self, checked: bool) -> None:
        """模式改变处理"""
        if checked:
            self.control_panel.btn_rename.setEnabled(len(self.results) > 0)
            
    def scan_folder(self) -> None:
        """扫描文件夹"""
        folder = self.settings.get("folder_path", "")
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "错误", "请先选择有效的影视文件夹")
            return None
            
        # 禁用按钮
        self.control_panel.btn_scan.setEnabled(False)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(True)
        
        # 更新状态
        self.update_status("正在扫描文件夹...")
        self.update_progress(0)
        
        # 创建并启动扫描线程
        self.scan_worker = ScanWorker(folder, self.settings)
        self.scan_worker.progress_updated.connect(self.update_progress)
        self.scan_worker.scan_completed.connect(self.on_scan_completed)
        self.scan_worker.error_occurred.connect(self.on_scan_error)
        self.scan_worker.eta_updated.connect(self.update_eta)
        self.scan_worker.current_file_changed.connect(self.update_current_file)
        self.scan_worker.start()
        
        return None
        
    def on_scan_completed(self, results: List[Dict[str, Any]]) -> None:
        """扫描完成处理"""
        self.results = results
        
        # 更新表格
        self.file_table.set_all_results(results)
        self.file_table.update_data(results)
        
        # 恢复按钮状态
        self.control_panel.btn_scan.setEnabled(True)
        self.control_panel.btn_rename.setEnabled(self.control_panel.radio_rename.isChecked())
        self.control_panel.btn_cancel.setEnabled(False)
        
        # 更新状态
        self.update_status(f"✅ 扫描完成，共找到 {len(results)} 个文件")
        self.update_progress(100)
        self.update_memory_usage()
        
        # 统计文件类型
        type_counts = {}
        for result in results:
            file_type = result.get('type', '未知')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # 显示详细结果统计
        stats_text = "📊 扫描统计：\n"
        for file_type, count in type_counts.items():
            stats_text += f"• {file_type}: {count} 个文件\n"
        
        QMessageBox.information(
            self, 
            "🎉 扫描完成", 
            f"共扫描到 {len(results)} 个文件\n\n{stats_text}"
        )
        
    def on_scan_error(self, error_msg: str) -> None:
        """扫描错误处理"""
        self.control_panel.btn_scan.setEnabled(True)
        self.update_status(f"扫描错误: {error_msg}")
        self.update_progress(0)
        QMessageBox.critical(self, "扫描错误", f"扫描过程中发生错误：\n{error_msg}")
        
    def do_rename(self) -> None:
        """执行重命名"""
        if not self.results:
            QMessageBox.warning(self, "错误", "请先扫描并分析文件夹")
            return None
            
        # 大批量操作二次确认
        if len(self.results) > 100:
            reply = QMessageBox.question(
                self,
                "批量重命名确认",
                f"即将重命名 {len(self.results)} 个文件，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return None
                
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认重命名",
            f"确定要对 {len(self.results)} 个文件执行重命名操作吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return None
            
        # 禁用按钮
        self.control_panel.btn_scan.setEnabled(False)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(True)
        
        # 更新状态
        self.update_status("正在执行重命名操作...")
        self.update_progress(0)
        
        # 创建重命名器
        self.settings["preview_only"] = False
        self.renamer = MediaRenamer(self.settings)
        folder_path = self.settings.get("folder_path", "")
        if folder_path:
            self.renamer.build_directory_cache(folder_path)
        
        # 创建并启动重命名线程
        self.rename_worker = RenameWorker(self.renamer, self.results)
        self.rename_worker.rename_completed.connect(self.on_rename_completed)
        self.rename_worker.eta_updated.connect(self.update_eta)
        self.rename_worker.current_file_changed.connect(self.update_current_file)
        self.rename_worker.start()
        
        return None
        
    def on_rename_completed(self, success: bool, message: str) -> None:
        """重命名完成处理"""
        # 恢复按钮状态
        self.control_panel.btn_scan.setEnabled(True)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(False)
        
        # 更新状态
        if success:
            self.update_status("✅ 重命名操作完成")
            self.update_progress(100)
        else:
            self.update_status(f"❌ 重命名失败: {message}")
            self.update_progress(0)
        self.update_memory_usage()
        
        # 显示结果
        if success:
            QMessageBox.information(
                self, 
                "🎉 操作完成", 
                f"{message}\n\n所有文件已成功重命名！"
            )
            # 重新扫描以更新显示
            self.scan_folder()
        else:
            QMessageBox.critical(
                self, 
                "❌ 操作失败", 
                f"重命名过程中发生错误：\n\n{message}\n\n请检查文件权限和磁盘空间。"
            )
        
        # 更新撤销重做按钮状态
        self.update_undo_redo_buttons()
        
    def cancel_operation(self) -> None:
        """取消操作"""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait()
            self.control_panel.btn_scan.setEnabled(True)
            self.update_status("扫描操作已取消")
            
        if self.rename_worker and self.rename_worker.isRunning():
            self.rename_worker.cancel()
            self.rename_worker.wait()
            self.control_panel.btn_rename.setEnabled(True)
            self.update_status("重命名操作已取消")
            
        self.control_panel.btn_cancel.setEnabled(False)
        self.update_progress(0)
        
        return None
        
    def toggle_theme(self) -> None:
        """切换主题"""
        current_theme = getattr(self, '_current_theme', 'light')
        
        if current_theme == 'light':
            # 切换到深色主题
            self.setStyleSheet(self.get_dark_theme())
            self._current_theme = 'dark'
            self.control_panel.btn_theme.setText("☀️ 浅色")
        else:
            # 切换到浅色主题
            self.setStyleSheet(self.get_light_theme())
            self._current_theme = 'light'
            self.control_panel.btn_theme.setText("🌙 深色")
            
    def get_light_theme(self) -> str:
        """获取浅色主题样式"""
        return self.setup_styles()
        
    def get_dark_theme(self) -> str:
        """获取深色主题样式"""
        return """
            QWidget {
                background-color: #2d3748;
                color: #e2e8f0;
            }
            QMainWindow {
                background-color: #2d3748;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #4a5568;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #e2e8f0;
                font-size: 14px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3182ce, stop:1 #2c5aa0);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c5aa0, stop:1 #1a365d);
            }
            QLineEdit {
                border: 2px solid #4a5568;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #4a5568;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border-color: #3182ce;
            }
            QComboBox {
                border: 2px solid #4a5568;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #4a5568;
                color: #e2e8f0;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3182ce;
            }
            QTableWidget {
                gridline-color: #4a5568;
                selection-background-color: #2c5aa0;
                alternate-background-color: #2d3748;
                background-color: #4a5568;
                border: 1px solid #4a5568;
                border-radius: 6px;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #2d3748;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #4a5568;
                font-weight: bold;
                color: #e2e8f0;
            }
            QStatusBar {
                background-color: #2d3748;
                border-top: 1px solid #4a5568;
                color: #e2e8f0;
            }
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 4px;
                text-align: center;
                background-color: #4a5568;
                color: #e2e8f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3182ce, stop:1 #2c5aa0);
                border-radius: 3px;
            }
        """
        
    def open_settings(self) -> None:
        """打开设置对话框"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # 更新设置
            self.settings = dialog.get_settings()
            logging.info("设置已更新")
        
    def open_help(self) -> None:
        """打开帮助对话框"""
        dialog = HelpDialog(self)
        dialog.exec_()
        
    def filter_files(self) -> None:
        """筛选文件"""
        search_text = self.search_box.text()
        file_type = self.filter_type_combo.currentText()
        self.file_table.filter_files(search_text, file_type)
        
    def focus_search_box(self) -> None:
        """聚焦搜索框"""
        self.search_box.setFocus()
        self.search_box.selectAll()
        
    def clear_filters(self) -> None:
        """清除筛选"""
        self.search_box.clear()
        self.filter_type_combo.setCurrentText("全部类型")
        
    def show_batch_preview(self) -> None:
        """显示批量预览"""
        if not self.results:
            QMessageBox.information(self, "提示", "请先扫描文件")
            return None
            
        dialog = BatchPreviewDialog(self.results, self)
        dialog.exec_()
        
        return None
    
    def show_smart_analysis(self) -> None:
        """显示智能分析对话框"""
        if not self.results:
            QMessageBox.information(self, "提示", "请先扫描文件")
            return None
        
        # 获取文件路径列表
        file_paths = [result.get('file_path', '') for result in self.results if result.get('file_path')]
        
        if not file_paths:
            QMessageBox.warning(self, "警告", "没有有效的文件路径")
            return None
        
        try:
            dialog = SmartAnalysisDialog(file_paths, self.settings, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"打开智能分析对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开智能分析对话框失败: {str(e)}")
        
        return None
        
    def update_status(self, message: str) -> None:
        """更新状态"""
        self.status_label.setText(message)
        
    def update_progress(self, value: int) -> None:
        """更新进度"""
        self.progress_indicator.setValue(value)
        self.progress_indicator.setVisible(value > 0)
        
    def update_eta(self, eta: str) -> None:
        """更新预计时间"""
        self.status_label.setText(f"{self.status_label.text()} - {eta}")
        
    def update_current_file(self, filename: str) -> None:
        """更新当前处理文件"""
        self.status_label.setText(f"正在处理: {filename}")
        
    def update_memory_usage(self) -> None:
        """更新内存使用显示"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.memory_label.setText(f"💾 内存: {memory_mb:.1f} MB")
            
            # 检查内存使用是否超过限制
            memory_limit = self.settings.get("memory_limit", 1073741824)  # 1GB
            if memory_info.rss > memory_limit:
                self.memory_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            else:
                self.memory_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        except Exception as e:
            logger.error(f"更新内存使用显示失败: {e}")
    
    # 拖拽支持
    def dragEnterEvent(self, event) -> None:
        """拖拽进入事件（增强版）"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # 添加拖拽提示样式
            self.setStyleSheet(self.setup_styles() + """
                QWidget { 
                    border: 3px dashed #3498db; 
                    background-color: rgba(52, 152, 219, 0.1);
                }
            """)
            # 显示拖拽提示
            self.update_status("📁 拖拽文件或文件夹到此处")
    
    def dragLeaveEvent(self, event) -> None:
        """拖拽离开事件"""
        self.setStyleSheet(self.setup_styles())
        self.update_status("🚀 就绪")
    
    def dropEvent(self, event) -> None:
        """拖拽放下事件（增强版）"""
        self.setStyleSheet(self.setup_styles())
        
        try:
            files = []
            folders = []
            
            # 分类处理拖拽的项目
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    folders.append(file_path)
            
            # 处理文件夹
            if folders:
                if len(folders) == 1:
                    # 单个文件夹，直接扫描
                    self.settings["folder_path"] = folders[0]
                    self.update_status(f"📁 扫描文件夹: {os.path.basename(folders[0])}")
                    self.scan_folder()
                else:
                    # 多个文件夹，询问用户
                    folder_list = "\n".join([f"• {os.path.basename(folder)}" for folder in folders])
                    reply = QMessageBox.question(
                        self, 
                        "多文件夹处理", 
                        f"检测到多个文件夹:\n{folder_list}\n\n是否要扫描所有文件夹？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        # 批量扫描文件夹
                        self.batch_scan_folders(folders)
                    else:
                        # 只扫描第一个文件夹
                        self.settings["folder_path"] = folders[0]
                        self.update_status(f"📁 扫描文件夹: {os.path.basename(folders[0])}")
                        self.scan_folder()
                return
            
            # 处理文件
            if files:
                self.update_status(f"📄 处理 {len(files)} 个文件...")
                self.add_files_to_table(files)
            
        except Exception as e:
            logger.error(f"拖拽处理失败: {e}")
            QMessageBox.warning(self, "错误", f"拖拽处理失败: {str(e)}")
            self.update_status("❌ 拖拽处理失败")
    
    def batch_scan_folders(self, folders: List[str]) -> None:
        """批量扫描多个文件夹"""
        try:
            self.update_status(f"📁 批量扫描 {len(folders)} 个文件夹...")
            
            all_results = []
            total_files = 0
            
            for i, folder in enumerate(folders):
                self.update_status(f"📁 扫描文件夹 {i+1}/{len(folders)}: {os.path.basename(folder)}")
                
                # 创建扫描工作线程
                scan_worker = ScanWorker(folder, self.settings)
                scan_worker.scan_completed.connect(lambda results, folder_name=os.path.basename(folder): 
                    self.on_batch_scan_completed(results, folder_name))
                scan_worker.error_occurred.connect(self.on_scan_error)
                
                # 执行扫描
                scan_worker.run()
                
                # 等待扫描完成
                scan_worker.wait()
                
                # 获取扫描结果（通过信号获取）
                if hasattr(scan_worker, '_results'):
                    all_results.extend(scan_worker._results)
                    total_files += len(scan_worker._results)
            
            # 更新表格显示所有结果
            self.results = all_results
            self.file_table.update_data(self.results)
            self.update_status(f"✅ 批量扫描完成，共找到 {total_files} 个文件")
            
        except Exception as e:
            logger.error(f"批量扫描失败: {e}")
            QMessageBox.warning(self, "错误", f"批量扫描失败: {str(e)}")
            self.update_status("❌ 批量扫描失败")
    
    def on_batch_scan_completed(self, results: List[Dict[str, Any]], folder_name: str) -> None:
        """批量扫描完成回调"""
        try:
            # 将结果添加到总结果中
            self.results.extend(results)
            
            # 更新表格
            self.file_table.update_data(self.results)
            
            logger.info(f"✅ 文件夹 {folder_name} 扫描完成，找到 {len(results)} 个文件")
            
        except Exception as e:
            logger.error(f"处理批量扫描结果失败: {e}")
    
    def add_files_to_table(self, file_paths: List[str]) -> None:
        """将文件添加到表格中（增强版）"""
        try:
            self.performance_monitor.start_timer("add_files")
            
            # 过滤媒体文件
            allowed_extensions = self.settings.get("video_extensions", [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"])
            media_files = []
            
            for file_path in file_paths:
                _, ext = os.path.splitext(file_path)
                if ext.lower() in allowed_extensions:
                    media_files.append(file_path)
            
            if not media_files:
                QMessageBox.information(self, "提示", f"在 {len(file_paths)} 个文件中没有找到支持的媒体文件\n\n支持的格式: {', '.join(allowed_extensions)}")
                return None
            
            # 显示处理进度
            progress_dialog = QProgressDialog("正在分析文件...", "取消", 0, len(media_files), self)
            progress_dialog.setWindowTitle("文件分析")
            progress_dialog.setWindowModality(Qt.ApplicationModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.show()
            
            # 分析文件并添加到表格
            renamer = MediaRenamer(self.settings)
            processed_count = 0
            
            for i, file_path in enumerate(media_files):
                if progress_dialog.wasCanceled():
                    break
                
                try:
                    filename = os.path.basename(file_path)
                    folder_path = os.path.dirname(file_path)
                    result = renamer.smart_analyze_file(filename, folder_path)
                    
                    if result:
                        result['original_name'] = filename
                        result['file_path'] = file_path
                        result['status'] = '待处理'
                        
                        # 生成新文件名
                        new_name = self.generate_new_filename(result, filename)
                        result['new_name'] = new_name
                        
                        self.results.append(result)
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"分析文件失败 {file_path}: {e}")
                    error_result = {
                        'original_name': os.path.basename(file_path),
                        'file_path': file_path,
                        'type': '未知',
                        'status': '分析失败',
                        'error': str(e)
                    }
                    self.results.append(error_result)
                
                # 更新进度
                progress_dialog.setValue(i + 1)
                progress_dialog.setLabelText(f"正在分析: {os.path.basename(file_path)}")
            
            progress_dialog.close()
            
            # 更新表格
            self.file_table.update_data(self.results)
            self.update_status(f"✅ 已添加 {processed_count} 个媒体文件")
            
            # 显示统计信息
            if processed_count > 0:
                QMessageBox.information(
                    self, 
                    "文件添加完成", 
                    f"成功添加 {processed_count} 个媒体文件\n\n"
                    f"总文件数: {len(self.results)}\n"
                    f"支持格式: {', '.join(allowed_extensions)}"
                )
            
            self.performance_monitor.end_timer("add_files")
            
        except Exception as e:
            logger.error(f"添加文件失败: {e}")
            QMessageBox.warning(self, "错误", f"添加文件失败: {str(e)}")
            self.update_status("❌ 添加文件失败")
            return None
    
    def generate_new_filename(self, result: Dict[str, Any], original_filename: str) -> str:
        """根据分析结果生成新文件名"""
        try:
            # 获取文件扩展名
            _, ext = os.path.splitext(original_filename)
            
            # 获取分析结果
            title = result.get('title', '')
            year = result.get('year', '')
            season = result.get('season')
            episode = result.get('episode')
            file_type = result.get('type', '')
            
            # 清理标题中的特殊字符
            if title:
                import re
                clean_title = re.sub(r'[\\/*?:"<>|$$$$\.\!_]', ' ', title).strip()
                clean_title = re.sub(r'[Ss]\d{2}[ ._]?E\d{2}', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title)
                clean_title = re.sub(r'\[\s*\]', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                title = clean_title
            
            # 根据文件类型生成新文件名
            if file_type == 'movie' and title:
                if year:
                    return f"{title} ({year}){ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'tv' and title:
                if season == 0:  # 特辑
                    if episode:
                        episode_str = str(episode).zfill(2)
                        return f"{title}.S00.E{episode_str}{ext}"
                    else:
                        return f"{title}.S00{ext}"
                elif season and episode:
                    season_str = str(season).zfill(2)
                    episode_str = str(episode).zfill(2)
                    return f"{title}.S{season_str}E{episode_str}{ext}"
                elif episode:
                    episode_str = str(episode).zfill(2)
                    return f"{title}.E{episode_str}{ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'special' and title:
                if episode:
                    episode_str = str(episode).zfill(2)
                    return f"{title}.S00.E{episode_str}{ext}"
                else:
                    return f"{title}.S00{ext}"
            else:
                return original_filename
                
        except Exception as e:
            logger.error(f"生成新文件名失败: {e}")
            return original_filename
    
    def undo_operation(self) -> None:
        """撤销操作"""
        if not self.operation_history.can_undo():
            QMessageBox.information(self, "提示", "没有可撤销的操作")
            return None
        
        try:
            operation = self.operation_history.undo_last_operation()
            if operation:
                self.update_status(f"已撤销: {operation.operation_type} - {os.path.basename(operation.original_path)}")
                # 重新扫描以更新显示
                if self.settings["folder_path"]:
                    self.scan_folder()
            else:
                QMessageBox.warning(self, "错误", "撤销操作失败")
        except Exception as e:
            logger.error(f"撤销操作失败: {e}")
            QMessageBox.critical(self, "错误", f"撤销操作失败: {str(e)}")
        
        # 更新撤销重做按钮状态
        self.update_undo_redo_buttons()
        return None
    
    def redo_operation(self) -> None:
        """重做操作"""
        if not self.operation_history.can_redo():
            QMessageBox.information(self, "提示", "没有可重做的操作")
            return None
        
        try:
            operation = self.operation_history.redo_last_operation()
            if operation:
                self.update_status(f"已重做: {operation.operation_type} - {os.path.basename(operation.original_path)}")
                # 重新扫描以更新显示
                if self.settings["folder_path"]:
                    self.scan_folder()
            else:
                QMessageBox.warning(self, "错误", "重做操作失败")
        except Exception as e:
            logger.error(f"重做操作失败: {e}")
            QMessageBox.critical(self, "错误", f"重做操作失败: {str(e)}")
        
        # 更新撤销重做按钮状态
        self.update_undo_redo_buttons()
        return None
    
    def update_undo_redo_buttons(self) -> None:
        """更新撤销重做按钮状态"""
        try:
            # 更新撤销按钮状态
            can_undo = self.operation_history.can_undo()
            self.control_panel.btn_undo.setEnabled(can_undo)
            
            # 更新重做按钮状态
            can_redo = self.operation_history.can_redo()
            self.control_panel.btn_redo.setEnabled(can_redo)
            
            # 更新按钮提示信息
            if can_undo:
                undo_info = self.operation_history.get_undo_info()
                if undo_info:
                    self.control_panel.btn_undo.setToolTip(f"撤销: {undo_info.get('description', '上一步操作')} (Ctrl+Z)")
                else:
                    self.control_panel.btn_undo.setToolTip("撤销上一步操作 (Ctrl+Z)")
            else:
                self.control_panel.btn_undo.setToolTip("没有可撤销的操作")
            
            if can_redo:
                self.control_panel.btn_redo.setToolTip("重做上一步操作 (Ctrl+Y)")
            else:
                self.control_panel.btn_redo.setToolTip("没有可重做的操作")
                
        except Exception as e:
            logger.error(f"更新撤销重做按钮状态失败: {e}")
    
    def show_performance_report(self) -> None:
        """显示性能报告"""
        try:
            report = self.performance_monitor.get_performance_report()
            
            if not report:
                QMessageBox.information(self, "性能报告", "暂无性能数据")
                return None
            
            report_text = "📊 性能报告\n\n"
            for operation, metrics in report.items():
                report_text += f"🔹 {operation}:\n"
                report_text += f"   执行次数: {metrics['count']}\n"
                report_text += f"   平均耗时: {metrics['avg_time']:.3f}秒\n"
                report_text += f"   最短耗时: {metrics['min_time']:.3f}秒\n"
                report_text += f"   最长耗时: {metrics['max_time']:.3f}秒\n"
                report_text += f"   总耗时: {metrics['total_time']:.3f}秒\n\n"
            
            # 显示历史记录摘要
            history_summary = self.operation_history.get_history_summary()
            report_text += "📋 操作历史:\n"
            report_text += f"   总操作数: {history_summary['total_operations']}\n"
            report_text += f"   成功操作: {history_summary['successful_operations']}\n"
            report_text += f"   失败操作: {history_summary['failed_operations']}\n"
            report_text += f"   可撤销: {'是' if history_summary['can_undo'] else '否'}\n"
            report_text += f"   可重做: {'是' if history_summary['can_redo'] else '否'}\n"
            
            QMessageBox.information(self, "性能报告", report_text)
            
        except Exception as e:
            logger.error(f"显示性能报告失败: {e}")
            QMessageBox.warning(self, "错误", f"显示性能报告失败: {str(e)}")
            return None

    # ==== 升级提示（主线程调用，信号桥保证） ====

    def show_update_banner(self, info: Any) -> None:
        """在状态栏显示升级提示横幅（可点击查看 / 不再提醒）。

        由主入口的后台升级检测线程通过 Qt 信号桥调用，运行于主线程。
        """
        if info is None or not getattr(info, "has_update", False):
            return
        latest = getattr(info, "latest_version", "")
        if not latest:
            return
        # 用户已选择"不再提醒"该版本则跳过
        settings = QSettings("TVMediaRenamer", "updates")
        if settings.value("dismissed_version", "") == latest:
            return

        # 清除旧横幅（避免重复叠加）
        for w in list(self._update_banner_widgets):
            self._close_update_banner(w)

        banner = QWidget()
        banner.setStyleSheet("background: #fff8e1; border: 1px solid #f0c36d; border-radius: 4px;")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(8)

        label = QLabel(f"✨ 发现新版本 {latest}")
        label.setStyleSheet("color: #7a5c00; font-weight: bold;")

        view_btn = QPushButton("查看详情")
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setStyleSheet("color: #1565c0; background: transparent; border: none; text-decoration: underline;")
        url = getattr(info, "release_url", "")
        view_btn.clicked.connect(lambda: self._open_update_url(url))

        dismiss_btn = QPushButton("不再提醒")
        dismiss_btn.setCursor(Qt.PointingHandCursor)
        dismiss_btn.setStyleSheet("color: #666; background: transparent; border: none;")
        dismiss_btn.clicked.connect(lambda: self._dismiss_update(latest, banner))

        layout.addWidget(label)
        layout.addWidget(view_btn)
        layout.addWidget(dismiss_btn)
        self.status_bar.addWidget(banner)
        self._update_banner_widgets.append(banner)
        self._update_banner_widgets = [b for b in self._update_banner_widgets if b is not None]

    def _open_update_url(self, url: str) -> None:
        """打开 Release 页面。"""
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _dismiss_update(self, version: str, banner: QWidget) -> None:
        """记录"不再提醒"并移除横幅。"""
        QSettings("TVMediaRenamer", "updates").setValue("dismissed_version", version)
        self._close_update_banner(banner)

    def _close_update_banner(self, banner: QWidget) -> None:
        """从状态栏移除横幅。"""
        try:
            self.status_bar.removeWidget(banner)
        except RuntimeError:
            pass
        banner.deleteLater()
        if banner in self._update_banner_widgets:
            self._update_banner_widgets.remove(banner)


class PerformanceMonitor:
    """性能监控类"""
    
    def __init__(self):
        self.metrics = {}
        self.timers = {}
    
    def start_timer(self, operation: str) -> None:
        """开始计时"""
        self.timers[operation] = time.time()
    
    def end_timer(self, operation: str) -> None:
        """结束计时并记录"""
        if operation in self.timers:
            elapsed = time.time() - self.timers[operation]
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
            
            # 只保留最近100次记录
            if len(self.metrics[operation]) > 100:
                self.metrics[operation] = self.metrics[operation][-100:]
            
            del self.timers[operation]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {}
        for operation, times in self.metrics.items():
            if times:
                report[operation] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        return report
    
    def get_operation_time(self, operation: str) -> float:
        """获取操作耗时"""
        if operation in self.metrics and self.metrics[operation]:
            return sum(self.metrics[operation]) / len(self.metrics[operation])
        return 0.0

