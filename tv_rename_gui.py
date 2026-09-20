#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视文件重命名工�?- PyQt5 GUI版本
使用PyQt/PySide最佳实践结�?"""

import sys
import os
import json
from typing import List, Tuple, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QRadioButton, QButtonGroup, QProgressBar, QGroupBox, QSplitter,
    QDialog, QLineEdit, QCheckBox, QSpinBox, QComboBox, QTextEdit,
    QTabWidget, QFormLayout, QScrollArea, QFrame, QStatusBar, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QFont, QColor, QPalette, QKeySequence, QGuiApplication
from PyQt5.QtWidgets import QShortcut
from tv_rename_cache_optimized import PatternRecognizer, MediaRenamer, DEFAULT_SETTINGS, ConfigManager
from constants import MOVIE_TYPE, TV_TYPE, SPECIAL_TYPE, DEFAULT_MOVIE_TEMPLATE, DEFAULT_TV_TEMPLATE, DEFAULT_SPECIAL_TEMPLATE
import logging
from datetime import datetime, timedelta
import re

# 兼容性常量定�?ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ITEM_IS_ENABLED = Qt.ItemFlag.ItemIsEnabled

# 日志初始化
log_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, 'frozen', False) else __file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"media_rename_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 统一异常处理与日志
def log_and_show_error(msg, parent=None):
    logging.error(msg)
    if parent:
        QMessageBox.critical(parent, "错误", msg)

# 常用按钮样式复用
BUTTON_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3498db, stop:1 #2980b9);
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2980b9, stop:1 #1f5f8b);
}
"""


class HelpDialog(QDialog):
    """帮助对话框"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        self.search_text = ""
        self.tab_widget = None
        self.search_box = None
    def setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("设置 - 影视文件重命名工具")
        self.resize(800, 600)

        # 主布局
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = self.create_basic_settings_tab()
        tab_widget.addTab(basic_tab, "基本设置")
        
        # 命名规则标签页
        naming_tab = self.create_naming_settings_tab()
        tab_widget.addTab(naming_tab, "命名规则")
        
        # 高级设置标签页
        advanced_tab = self.create_advanced_settings_tab()
        tab_widget.addTab(advanced_tab, "高级设置")
        
        # 安全设置标签页
        security_tab = self.create_security_settings_tab()
        tab_widget.addTab(security_tab, "安全设置")
        
        layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("保存设置")
        self.btn_save.setToolTip("保存当前设置到配置文件")
        self.btn_save.setStyleSheet(BUTTON_STYLE)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setToolTip("取消设置修改，不保存更改")
        self.btn_cancel.setStyleSheet(BUTTON_STYLE)
        self.btn_reset = QPushButton("重置为默认")
        self.btn_reset.setToolTip("将所有设置恢复为默认值")
        self.btn_reset.setStyleSheet(BUTTON_STYLE)
        self.btn_export = QPushButton("导出设置")
        self.btn_export.setToolTip("将设置导出为JSON文件，便于备份和迁移")
        self.btn_export.setStyleSheet(BUTTON_STYLE)
        self.btn_import = QPushButton("导入设置")
        self.btn_import.setToolTip("从JSON文件导入设置")
        self.btn_import.setStyleSheet(BUTTON_STYLE)
        self.btn_help = QPushButton("帮助")
        self.btn_help.setToolTip("查看详细的设置说明和使用指南")
        self.btn_help.setStyleSheet(BUTTON_STYLE)
        button_layout.addWidget(self.btn_reset)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_help)
        button_layout.addWidget(self.btn_export)
        button_layout.addWidget(self.btn_import)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_save)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 连接信号
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_reset.clicked.connect(self.reset_to_default)
        self.btn_export.clicked.connect(self.export_settings)
        self.btn_import.clicked.connect(self.import_settings)
        self.btn_help.clicked.connect(self.show_settings_help)

    def create_basic_settings_tab(self) -> QWidget:
        """创建基本设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        # 默认文件夹路径
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setToolTip("设置程序启动时默认打开的影视文件夹路径\n建议设置为您的影视库根目录")
        self.btn_browse_folder = QPushButton("浏览")
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(self.btn_browse_folder)
        scroll_layout.addRow("默认文件夹路径", folder_layout)
        # 预览模式
        self.preview_only_check = QCheckBox("默认启用预览模式")
        self.preview_only_check.setToolTip("默认启用预览模式，确保安全操作\n预览模式下不会实际修改文件")
        scroll_layout.addRow("预览模式:", self.preview_only_check)
        # 跳过已存在文件
        self.skip_existing_check = QCheckBox("跳过已存在的文件")
        self.skip_existing_check.setToolTip("避免覆盖已重命名的文件\n提高处理效率，避免重复操作")
        scroll_layout.addRow("跳过已存在:", self.skip_existing_check)
        # 启用历史记录
        self.enable_history_check = QCheckBox("启用重命名历史记录")
        self.enable_history_check.setToolTip("记录所有重命名操作的历史\n便于追踪和恢复操作")
        scroll_layout.addRow("历史记录:", self.enable_history_check)
        # 预览页面大小
        self.preview_page_size_spin = QSpinBox()
        self.preview_page_size_spin.setRange(5, 100)
        self.preview_page_size_spin.setValue(10)
        self.preview_page_size_spin.setToolTip("控制预览表格显示的文件数量\n建议设置10-20之间")
        scroll_layout.addRow("预览页面大小:", self.preview_page_size_spin)
        # 视频文件扩展名
        self.video_extensions_edit = QTextEdit()
        self.video_extensions_edit.setMaximumHeight(80)
        self.video_extensions_edit.setToolTip("支持处理的视频文件格式\n每行一个扩展名，不包含点号\n例如：mp4, mkv, avi, mov")
        scroll_layout.addRow("视频文件扩展名:", self.video_extensions_edit)
        # 元数据文件扩展名
        self.metadata_extensions_edit = QTextEdit()
        self.metadata_extensions_edit.setMaximumHeight(80)
        self.metadata_extensions_edit.setToolTip("字幕、海报等辅助文件格式\n每行一个扩展名，不包含点号\n例如：srt, ass, jpg, png")
        scroll_layout.addRow("元数据文件扩展名:", self.metadata_extensions_edit)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        # 连接信号
        self.btn_browse_folder.clicked.connect(self.browse_folder)
        widget.setLayout(layout)
        return widget

    def create_naming_settings_tab(self) -> QWidget:
        """创建命名规则标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        # 电影命名模板
        self.movie_template_edit = QLineEdit()
        self.movie_template_edit.setToolTip("电影文件的命名模板\n支持变量：{title}, {year}, {ext}\n示例：{title} ({year}){ext}")
        scroll_layout.addRow("电影命名模板:", self.movie_template_edit)
        # 电视剧命名模板
        self.tv_template_edit = QLineEdit()
        self.tv_template_edit.setToolTip("电视剧文件的命名模板\n支持变量：{title}, {season}, {episode}, {ext}\n示例：{title}.S{season:02d}.E{episode:02d}{ext}")
        scroll_layout.addRow("电视剧命名模板:", self.tv_template_edit)
        # 特辑命名模板
        self.special_template_edit = QLineEdit()
        self.special_template_edit.setToolTip("特辑文件的命名模板\n支持变量：{title}, {episode}, {ext}\n示例：{title}.S00.E{episode:02d}{ext}")
        scroll_layout.addRow("特辑命名模板:", self.special_template_edit)
        # 电视剧文件夹关键词
        self.tv_keywords_edit = QTextEdit()
        self.tv_keywords_edit.setMaximumHeight(60)
        self.tv_keywords_edit.setToolTip("用于识别电视剧文件夹的关键词\n每行一个关键词，支持中文和英文\n例如：电视剧、剧集、TV、Series")
        scroll_layout.addRow("电视剧文件夹关键词:", self.tv_keywords_edit)
        # 电影文件夹关键词
        self.movie_keywords_edit = QTextEdit()
        self.movie_keywords_edit.setMaximumHeight(60)
        self.movie_keywords_edit.setToolTip("用于识别电影文件夹的关键词\n每行一个关键词，支持中文和英文\n例如：电影、Movie、Film")
        scroll_layout.addRow("电影文件夹关键词:", self.movie_keywords_edit)
        # 特辑关键词
        self.special_keywords_edit = QTextEdit()
        self.special_keywords_edit.setMaximumHeight(60)
        self.special_keywords_edit.setToolTip("用于识别特辑文件的关键词\n每行一个关键词，支持中文和英文\n例如：特辑、特别篇、Special")
        scroll_layout.addRow("特辑关键词:", self.special_keywords_edit)
        # 强制规则
        self.force_tv_check = QCheckBox("强制使用电视剧规则")
        self.force_tv_check.setToolTip("忽略文件夹名称，强制按电视剧处理\n谨慎使用，可能影响识别准确性")
        scroll_layout.addRow("强制电视剧规则:", self.force_tv_check)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        widget.setLayout(layout)
        widget.setLayout(layout)
        return widget

    def create_advanced_settings_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        # 并行处理
        self.parallel_processing_check = QCheckBox("启用并行处理")
        self.parallel_processing_check.setToolTip("启用多线程并行处理，提高处理速度\n建议在多核CPU上启用，单核CPU建议关闭")
        scroll_layout.addRow("并行处理:", self.parallel_processing_check)
        # 最大工作线程数
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        self.max_workers_spin.setToolTip("并行处理时使用的工作线程数量\n建议设置为CPU核心数的1-2倍")
        scroll_layout.addRow("最大工作线程数:", self.max_workers_spin)
        # 缓存设置
        self.enable_cache_check = QCheckBox("启用智能缓存")
        self.enable_cache_check.setToolTip("缓存文件信息，提高重复扫描速度\n减少磁盘I/O操作")
        scroll_layout.addRow("智能缓存:", self.enable_cache_check)
        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(60, 86400)
        self.cache_ttl_spin.setValue(300)
        self.cache_ttl_spin.setSuffix(" 秒")
        self.cache_ttl_spin.setToolTip("缓存数据的有效时间（秒）\n过期后自动重新扫描")
        scroll_layout.addRow("缓存有效期:", self.cache_ttl_spin)
        self.cache_max_size_spin = QSpinBox()
        self.cache_max_size_spin.setRange(10, 1000)
        self.cache_max_size_spin.setValue(100)
        self.cache_max_size_spin.setSuffix(" MB")
        self.cache_max_size_spin.setToolTip("缓存文件占用的最大磁盘空间\n超过限制时自动清理旧缓存")
        scroll_layout.addRow("缓存最大大小:", self.cache_max_size_spin)
        # 性能监控
        self.performance_monitoring_check = QCheckBox("启用性能监控")
        self.performance_monitoring_check.setToolTip("监控处理过程中的性能指标\n显示内存使用情况和处理速度")
        scroll_layout.addRow("性能监控:", self.performance_monitoring_check)
        # 操作超时
        self.operation_timeout_spin = QSpinBox()
        self.operation_timeout_spin.setRange(10, 300)
        self.operation_timeout_spin.setValue(30)
        self.operation_timeout_spin.setSuffix(" 秒")
        self.operation_timeout_spin.setToolTip("单个文件处理的最大时间限制\n超时后自动跳过该文件")
        scroll_layout.addRow("操作超时时间:", self.operation_timeout_spin)
        # 最大重试次数
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(1, 10)
        self.max_retries_spin.setValue(3)
        self.max_retries_spin.setToolTip("处理失败时的重试次数\n提高处理成功率，建议设置为3-5次")
        scroll_layout.addRow("最大重试次数:", self.max_retries_spin)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget
        
    def create_security_settings_tab(self) -> QWidget:
        """创建安全设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout()
        # 沙盒模式
        self.sandbox_mode_check = QCheckBox("启用沙盒模式")
        self.sandbox_mode_check.setToolTip("在安全环境中测试重命名操作\n不会修改原始文件")
        scroll_layout.addRow("沙盒模式:", self.sandbox_mode_check)
        # 沙盒目录
        self.sandbox_dir_edit = QLineEdit()
        self.sandbox_dir_edit.setToolTip("沙盒模式下的测试目录\n建议设置为临时目录")
        self.btn_browse_sandbox = QPushButton("浏览")
        sandbox_layout = QHBoxLayout()
        sandbox_layout.addWidget(self.sandbox_dir_edit)
        sandbox_layout.addWidget(self.btn_browse_sandbox)
        scroll_layout.addRow("沙盒目录:", sandbox_layout)
        # 操作确认
        self.require_confirmation_check = QCheckBox("需要用户确认重要操作")
        self.require_confirmation_check.setToolTip("重要操作前需要用户确认\n防止误操作")
        scroll_layout.addRow("操作确认:", self.require_confirmation_check)
        # 安全级别
        self.security_level_combo = QComboBox()
        self.security_level_combo.addItems(["low", "medium", "high"])
        self.security_level_combo.setToolTip("low：低安全级别，操作限制较少\nmedium：中等安全级别，平衡安全性和便利性\nhigh：高安全级别，严格的操作限制")
        scroll_layout.addRow("安全级别:", self.security_level_combo)
        # 最大文件大小
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(100, 100000)
        self.max_file_size_spin.setValue(50000)
        self.max_file_size_spin.setSuffix(" MB")
        self.max_file_size_spin.setToolTip("单次操作处理的最大文件大小\n防止处理过大的文件导致系统卡顿")
        scroll_layout.addRow("最大文件大小:", self.max_file_size_spin)
        # 最大文件数
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(100, 100000)
        self.max_files_spin.setValue(10000)
        self.max_files_spin.setToolTip("单次操作处理的最大文件数量\n防止处理过多文件导致内存不足")
        scroll_layout.addRow("单次操作最大文件数:", self.max_files_spin)
        # 路径验证
        self.enable_path_validation_check = QCheckBox("启用路径验证")
        self.enable_path_validation_check.setToolTip("验证文件路径的有效性\n防止访问非法路径")
        scroll_layout.addRow("路径验证:", self.enable_path_validation_check)
        # 文件大小检查
        self.enable_file_size_check = QCheckBox("启用文件大小检查")
        self.enable_file_size_check.setToolTip("检查文件大小是否合理\n防止处理损坏或异常文件")
        scroll_layout.addRow("文件大小检查:", self.enable_file_size_check)
        # 可疑模式检测
        self.enable_suspicious_check = QCheckBox("启用可疑模式检测")
        self.enable_suspicious_check.setToolTip("检测可能有害的操作模式\n提高操作安全性")
        scroll_layout.addRow("可疑模式检测:", self.enable_suspicious_check)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        self.btn_browse_sandbox.clicked.connect(self.browse_sandbox)
        widget.setLayout(layout)
        return widget
        
    def load_settings(self) -> None:
        """加载设置到UI"""
        # 基本设置
        self.folder_path_edit.setText(self.settings.get("folder_path", ""))
        self.preview_only_check.setChecked(self.settings.get("preview_only", True))
        self.skip_existing_check.setChecked(self.settings.get("skip_existing", True))
        self.enable_history_check.setChecked(self.settings.get("enable_history", True))
        self.preview_page_size_spin.setValue(self.settings.get("preview_page_size", 10))
        
        # 文件扩展名
        video_exts = self.settings.get("video_extensions", [])
        if not video_exts:
            video_exts = ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"]
        self.video_extensions_edit.setPlainText("\n".join(video_exts))
        
        metadata_exts = self.settings.get("metadata_extensions", [])
        if not metadata_exts:
            metadata_exts = ["srt", "ass", "ssa", "sub", "idx", "jpg", "png", "nfo"]
        self.metadata_extensions_edit.setPlainText("\n".join(metadata_exts))
        
        # 命名规则
        self.movie_template_edit.setText(self.settings.get("movie_template", "{title} ({year}){ext}"))
        self.tv_template_edit.setText(self.settings.get("tv_template", "{title}.S{season:02d}.E{episode:02d}{ext}"))
        self.special_template_edit.setText(self.settings.get("special_template", "{title}.S00.E{episode:02d}{ext}"))
        
        # 关键词
        tv_keywords = self.settings.get("tv_folder_keywords", [])
        if not tv_keywords:
            tv_keywords = ["电视剧", "剧集", "TV", "Series", "连续剧"]
        self.tv_keywords_edit.setPlainText("\n".join(tv_keywords))
        
        movie_keywords = self.settings.get("movie_folder_keywords", [])
        if not movie_keywords:
            movie_keywords = ["电影", "Movie", "Film", "影片"]
        self.movie_keywords_edit.setPlainText("\n".join(movie_keywords))
        
        special_keywords = self.settings.get("special_keywords", [])
        if not special_keywords:
            special_keywords = ["特辑", "特别篇", "Special", "OVA", "SP"]
        self.special_keywords_edit.setPlainText("\n".join(special_keywords))
        
        # 强制规则
        self.force_tv_check.setChecked(self.settings.get("force_tv_rules", False))
        self.force_movie_check.setChecked(self.settings.get("force_movie_rules", False))
        self.force_special_check.setChecked(self.settings.get("force_special_season", True))
        
        # 高级设置
        self.parallel_processing_check.setChecked(self.settings.get("parallel_processing", True))
        self.max_workers_spin.setValue(self.settings.get("max_workers", 4))
        self.enable_cache_check.setChecked(self.settings.get("enable_incremental_cache", True))
        self.cache_ttl_spin.setValue(self.settings.get("cache_ttl", 300))
        self.cache_max_size_spin.setValue(self.settings.get("cache_max_size_mb", 100))
        self.performance_monitoring_check.setChecked(self.settings.get("performance_monitoring", True))
        self.operation_timeout_spin.setValue(self.settings.get("operation_timeout", 30))
        self.max_retries_spin.setValue(self.settings.get("max_retries", 3))
        
        # 安全设置
        self.sandbox_mode_check.setChecked(self.settings.get("sandbox_mode", True))
        self.sandbox_dir_edit.setText(self.settings.get("sandbox_dir", ".sandbox"))
        self.require_confirmation_check.setChecked(self.settings.get("require_confirmation", True))
        
        security_level = self.settings.get("security_level", "high")
        index = self.security_level_combo.findText(security_level)
        if index >= 0:
            self.security_level_combo.setCurrentIndex(index)
            
        self.max_file_size_spin.setValue(self.settings.get("max_file_size_mb", 50000))
        self.max_files_spin.setValue(self.settings.get("max_files_per_operation", 10000))
        self.enable_path_validation_check.setChecked(self.settings.get("enable_path_validation", True))
        self.enable_file_size_check.setChecked(self.settings.get("enable_file_size_check", True))
        self.enable_suspicious_check.setChecked(self.settings.get("enable_suspicious_detection", True))
        
    def save_settings(self) -> None:
        """保存设置"""
        try:
            # 基本设置
            self.settings["folder_path"] = self.folder_path_edit.text()
            self.settings["preview_only"] = self.preview_only_check.isChecked()
            self.settings["skip_existing"] = self.skip_existing_check.isChecked()
            self.settings["enable_history"] = self.enable_history_check.isChecked()
            self.settings["preview_page_size"] = self.preview_page_size_spin.value()
            
            # 文件扩展名
            video_exts = self.video_extensions_edit.toPlainText().strip().split("\n")
            self.settings["video_extensions"] = [ext.strip() for ext in video_exts if ext.strip()]
            
            metadata_exts = self.metadata_extensions_edit.toPlainText().strip().split("\n")
            self.settings["metadata_extensions"] = [ext.strip() for ext in metadata_exts if ext.strip()]
            
            # 命名规则
            self.settings["movie_template"] = self.movie_template_edit.text()
            self.settings["tv_template"] = self.tv_template_edit.text()
            self.settings["special_template"] = self.special_template_edit.text()
            
            # 关键词
            tv_keywords = self.tv_keywords_edit.toPlainText().strip().split("\n")
            self.settings["tv_folder_keywords"] = [kw.strip() for kw in tv_keywords if kw.strip()]
            
            movie_keywords = self.movie_keywords_edit.toPlainText().strip().split("\n")
            self.settings["movie_folder_keywords"] = [kw.strip() for kw in movie_keywords if kw.strip()]
            
            special_keywords = self.special_keywords_edit.toPlainText().strip().split("\n")
            self.settings["special_keywords"] = [kw.strip() for kw in special_keywords if kw.strip()]
            
            # 强制规则
            self.settings["force_tv_rules"] = self.force_tv_check.isChecked()
            self.settings["force_movie_rules"] = self.force_movie_check.isChecked()
            self.settings["force_special_season"] = self.force_special_check.isChecked()
            
            # 高级设置
            self.settings["parallel_processing"] = self.parallel_processing_check.isChecked()
            self.settings["max_workers"] = self.max_workers_spin.value()
            self.settings["enable_incremental_cache"] = self.enable_cache_check.isChecked()
            self.settings["cache_ttl"] = self.cache_ttl_spin.value()
            self.settings["cache_max_size_mb"] = self.cache_max_size_spin.value()
            self.settings["performance_monitoring"] = self.performance_monitoring_check.isChecked()
            self.settings["operation_timeout"] = self.operation_timeout_spin.value()
            self.settings["max_retries"] = self.max_retries_spin.value()
            
            # 安全设置
            self.settings["sandbox_mode"] = self.sandbox_mode_check.isChecked()
            self.settings["sandbox_dir"] = self.sandbox_dir_edit.text()
            self.settings["require_confirmation"] = self.require_confirmation_check.isChecked()
            self.settings["security_level"] = self.security_level_combo.currentText()
            self.settings["max_file_size_mb"] = self.max_file_size_spin.value()
            self.settings["max_files_per_operation"] = self.max_files_spin.value()
            self.settings["enable_path_validation"] = self.enable_path_validation_check.isChecked()
            self.settings["enable_file_size_check"] = self.enable_file_size_check.isChecked()
            self.settings["enable_suspicious_detection"] = self.enable_suspicious_check.isChecked()
            
            # 保存到配置文件
            self.config_manager.set_setting("settings", self.settings)
            self.config_manager.save_config()
            
            QMessageBox.information(self, "成功", "设置已保存！")
            self.accept()
            
        except Exception as e:
            log_and_show_error(f"保存设置失败：{str(e)}", self)

    def reset_to_default(self) -> None:
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有设置为默认值吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings = DEFAULT_SETTINGS.copy()
            self.load_settings()
            QMessageBox.information(self, "成功", "已重置为默认设置")
            
    def export_settings(self) -> None:
        """导出设置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出设置", "settings_export.json", "JSON文件 (*.json)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"设置已导出到：{file_path}")
                
        except Exception as e:
            log_and_show_error(f"导出设置失败：{str(e)}", self)
            
    def import_settings(self) -> None:
        """导入设置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入设置", "", "JSON文件 (*.json)"
            )
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)
                # 校验关键字段
                required_keys = [
                    "folder_path", "preview_only", "skip_existing", "enable_history",
                    "preview_page_size", "video_extensions", "metadata_extensions",
                    "movie_template", "tv_template", "special_template",
                    "tv_folder_keywords", "movie_folder_keywords", "special_keywords",
                    "force_tv_rules", "force_movie_rules", "force_special_season",
                    "parallel_processing", "max_workers", "enable_incremental_cache",
                    "cache_ttl", "cache_max_size_mb", "performance_monitoring",
                    "operation_timeout", "max_retries", "sandbox_mode", "sandbox_dir",
                    "require_confirmation", "security_level", "max_file_size_mb",
                    "max_files_per_operation", "enable_path_validation",
                    "enable_file_size_check", "enable_suspicious_detection"
                ]
                for key in required_keys:
                    if key not in imported_settings:
                        log_and_show_error(f"设置文件缺少字段：{key}", self)
                        return
                # 合并设置
                self.settings.update(imported_settings)
                self.load_settings()
                QMessageBox.information(self, "成功", f"设置已从 {file_path} 导入")
        except Exception as e:
            log_and_show_error(f"导入设置失败：{str(e)}", self)
            
    def browse_folder(self) -> None:
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择默认文件夹")
        if folder:
            self.folder_path_edit.setText(folder)
            
    def browse_sandbox(self) -> None:
        """浏览沙盒目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择沙盒目录")
        if folder:
            self.sandbox_dir_edit.setText(folder)
            
    def get_settings(self) -> Dict[str, Any]:
        return self.settings
        
    def show_settings_help(self) -> None:
        """显示设置帮助"""
        # 创建帮助对话框
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("设置帮助 - 影视文件重命名工具")
        help_dialog.resize(900, 700)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        help_text = """
        <h2>⚙️ 设置帮助</h2>
        
        <h3>📁 基本设置</h3>
        
        <p><strong>默认文件夹路径：</strong></p>
        <ul>
        <li>设置程序启动时默认打开的影视文件夹路径</li>
        <li>建议设置为您的影视库根目录</li>
        <li>支持相对路径和绝对路径</li>
        </ul>
        
        <p><strong>预览模式?/strong></p>
        <ul>
        <li>默认启用预览模式，确保安全操作</li>
        <li>预览模式下不会实际修改文件</li>
        <li>建议首次使用保持启用状态</li>
        </ul>
        
        <p><strong>跳过已存在文件：</strong></p>
        <ul>
        <li>避免覆盖已重命名的文件</li>
        <li>提高处理效率，避免重复操作</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <p><strong>历史记录?/strong></p>
        <ul>
        <li>记录所有重命名操作的历史</li>
        <li>便于追踪和恢复操作</li>
        <li>占用少量磁盘空间</li>
        </ul>
        
        <p><strong>预览页面大小?/strong></p>
        <ul>
        <li>控制预览表格显示的文件数量</li>
        <li>数值越大，显示越多文件</li>
        <li>建议设置在10-20之间</li>
        </ul>
        
        <p><strong>文件扩展名：</strong></p>
        <ul>
        <li>视频文件扩展名：支持处理的视频文件格式</li>
        <li>元数据文件扩展名：字幕、海报等辅助文件格式</li>
        <li>每行一个扩展名，不包含点号</li>
        </ul>
        
        <h3>📝 命名规则</h3>
        
        <p><strong>命名模板�?/strong></p>
        <ul>
        <li>电影模板：{title} ({year}){ext}</li>
        <li>电视剧模板：{title}.S{season:02d}.E{episode:02d}{ext}</li>
        <li>特辑模板：{title}.S00.E{episode:02d}{ext}</li>
        <li>支持变量：{title}, {season}, {episode}, {year}, {ext}</li>
        </ul>
        
        <p><strong>文件夹关键词�?/strong></p>
        <ul>
        <li>用于识别文件夹类型的关键词</li>
        <li>电视剧关键词：电视剧、剧集、TV、Series、连续剧</li>
        <li>电影关键词：电影、Movie、Film、影片</li>
        <li>特辑关键词：特辑、特别篇、Special、OVA、SP</li>
        <li>每行一个关键词，支持中文和英文</li>
        </ul>
        
        <p><strong>强制规则?/strong></p>
        <ul>
        <li>强制电视剧规则：忽略文件夹名称，强制按电视剧处理</li>
        <li>强制电影规则：忽略文件夹名称，强制按电影处理</li>
        <li>强制特辑规则：将特辑文件识别为S00</li>
        <li>谨慎使用，可能影响识别准确性</li>
        </ul>
        
        <h3>🔧 高级设置</h3>
        
        <p><strong>并行处理?/strong></p>
        <ul>
        <li>启用多线程并行处理，提高处理速度</li>
        <li>建议在多核CPU上启用</li>
        <li>单核CPU建议关闭</li>
        </ul>
        
        <p><strong>最大工作线程数?/strong></p>
        <ul>
        <li>并行处理时使用的工作线程数量</li>
        <li>建议设置为CPU核心数的1-2倍</li>
        <li>过多线程可能导致系统负载过高</li>
        </ul>
        
        <p><strong>智能缓存?/strong></p>
        <ul>
        <li>缓存文件信息，提高重复扫描速度</li>
        <li>减少磁盘I/O操作</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <p><strong>缓存有效期：</strong></p>
        <ul>
        <li>缓存数据的有效时间（秒）</li>
        <li>过期后自动重新扫描</li>
        <li>建议设置在600秒以内</li>
        </ul>
        
        <p><strong>缓存最大大小：</strong></p>
        <ul>
        <li>缓存文件占用的最大磁盘空间</li>
        <li>超过限制时自动清理旧缓存</li>
        <li>建议设置在500MB以内</li>
        </ul>
        
        <p><strong>性能监控?/strong></p>
        <ul>
        <li>监控处理过程中的性能指标</li>
        <li>显示内存使用情况和处理速度</li>
        <li>轻微影响性能，建议按需启用</li>
        </ul>
        
        <p><strong>操作超时时间?/strong></p>
        <ul>
        <li>单个文件处理的最大时间限制</li>
        <li>超时后自动跳过该文件</li>
        <li>建议设置在60秒以内</li>
        </ul>
        
        <p><strong>最大重试次数：</strong></p>
        <ul>
        <li>处理失败时的重试次数</li>
        <li>提高处理成功率，建议设置为3-5次</li>
        </ul>
        
        <h3>🛡️ 安全设置</h3>
        
        <p><strong>沙盒模式?/strong></p>
        <ul>
        <li>在安全环境中测试重命名操作</li>
        <li>不会修改原始文件</li>
        <li>建议首次使用或测试新功能时启用</li>
        </ul>
        
        <p><strong>沙盒目录?/strong></p>
        <ul>
        <li>沙盒模式下的测试目录</li>
        <li>建议设置为临时目录</li>
        <li>确保有足够的磁盘空间</li>
        </ul>
        
        <p><strong>操作确认?/strong></p>
        <ul>
        <li>重要操作前需要用户确认</li>
        <li>防止误操作</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <p><strong>安全级别?/strong></p>
        <ul>
        <li>low：低安全级别，操作限制较少</li>
        <li>medium：中等安全级别，平衡安全性和便利性</li>
        <li>high：高安全级别，严格的操作限制</li>
        <li>建议设置为medium或high</li>
        </ul>
        
        <p><strong>最大文件大小：</strong></p>
        <ul>
        <li>单次操作处理的最大文件大小</li>
        <li>防止处理过大的文件导致系统卡顿</li>
        <li>建议设置在50000MB以内</li>
        </ul>
        
        <p><strong>单次操作最大文件数?/strong></p>
        <ul>
        <li>单次操作处理的最大文件数量</li>
        <li>防止处理过多文件导致内存不足</li>
        <li>建议设置在10000个文件以内</li>
        </ul>
        
        <p><strong>路径验证?/strong></p>
        <ul>
        <li>验证文件路径的有效性</li>
        <li>防止访问非法路径</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <p><strong>文件大小检查：</strong></p>
        <ul>
        <li>检查文件大小是否合理</li>
        <li>防止处理损坏或异常文件</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <p><strong>可疑模式检测：</strong></p>
        <ul>
        <li>检测可能有害的操作模式</li>
        <li>提高操作安全性</li>
        <li>建议保持启用状态</li>
        </ul>
        
        <h3>💡 使用建议</h3>
        
        <ul>
        <li>首次使用建议保持默认设置</li>
        <li>根据实际需求逐步调整设置</li>
        <li>重要操作前先备份文件</li>
        <li>定期导出设置配置</li>
        <li>遇到问题时可以重置为默认设置</li>
        </ul>
        
        <h3>🔧 设置管理</h3>
        
        <ul>
        <li><strong>保存设置</strong>将当前设置保存到配置文件</li>
        <li><strong>导出设置</strong>将设置导出为JSON文件，便于备份和迁移</li>
        <li><strong>导入设置</strong>从JSON文件导入设置</li>
        <li><strong>重置为默认：</strong>将所有设置恢复为默认设置</li>
        </ul>
        
        <h3>🎯 快速配置建?</h3>
        
        <p><strong>新手用户</strong></p>
        <ul>
        <li>保持所有默认设置</li>
        <li>启用预览模式和安全设置</li>
        <li>使用默认的命名模板</li>
        </ul>
        
        <p><strong>进阶用户</strong></p>
        <ul>
        <li>根据硬件配置调整并行处理</li>
        <li>自定义命名模板和关键词</li>
        <li>启用性能监控和缓存</li>
        </ul>
        
        <p><strong>高级用户</strong></p>
        <ul>
        <li>完全自定义所有设置</li>
        <li>根据使用场景调整安全级别</li>
        <li>优化缓存和性能参数</li>
        </ul>
        """
        
        # 创建标签显示帮助内容
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)
        help_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.5;
                padding: 20px;
            }
        """)
        
        scroll_layout.addWidget(help_label)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(help_dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(btn_close)
        layout.addLayout(button_layout)
        
        help_dialog.setLayout(layout)
        help_dialog.exec_()


class ScanWorker(QThread):
    """扫描工作线程"""
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    eta_updated = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    
    def __init__(self, folder_path: str, settings: Dict[str, Any]) -> None:
        super().__init__()
        self.folder_path = folder_path
        self.settings = settings
        self.pr = PatternRecognizer()
        self.renamer: Optional[MediaRenamer] = None
        self._is_cancelled = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
    
    def run(self) -> None:
        try:
            logging.info(f"开始扫描文件夹: {self.folder_path}")
            self.renamer = MediaRenamer(self.settings)
            self.renamer.build_directory_cache(self.folder_path)
            files = []
            for root in self.renamer.cache['dirs']:
                for file_path in self.renamer.cache['dir_files'].get(root, []):
                    file = os.path.basename(file_path)
                    files.append((root, file, file_path))
            results = []
            total_files = len(files)
            start_time = datetime.now()
            for i, (root, file, file_path) in enumerate(files):
                if self._is_cancelled:
                    logging.info("扫描操作被用户取消")
                    break
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.current_file_changed.emit(file)
                # 剩余时间预估
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / (i + 1) if i + 1 > 0 else 0
                eta = avg_time * (total_files - (i + 1))
                eta_str = f"预计剩余: {int(eta // 60)}分{int(eta % 60)}秒"
                self.eta_updated.emit(eta_str)
                res = self.pr.analyze_filename(file, root)
                new_name = ""
                fmt = self.pr.suggest_rename_format(res)
                if fmt:
                    try:
                        new_name = fmt.format(
                            title=res.get("title") or "",
                            season=res.get("season") or 1,
                            episode=res.get("episode") or 1,
                            year=res.get("year") or "",
                            ext=os.path.splitext(file)[1]
                        )
                    except Exception as e:
                        new_name = ""
                        logging.error(f"文件名格式化失败: {file}, 错误: {e}")
                results.append({
                    'file': file,
                    'type': res.get("type"),
                    'title': res.get("title"),
                    'season': res.get("season"),
                    'episode': res.get("episode"),
                    'year': res.get("year"),
                    'new_name': new_name,
                    'file_path': file_path,
                    'root': root
                })
            self.scan_completed.emit(results)
            logging.info(f"扫描完成, 共{len(results)}个文件")
        except Exception as e:
            logging.error(f"扫描异常: {e}")
            self.error_occurred.emit(str(e))


class RenameWorker(QThread):
    """重命名工作线程"""
    progress_updated = pyqtSignal(int)
    rename_completed = pyqtSignal(bool, str)
    eta_updated = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    
    def __init__(self, renamer: MediaRenamer) -> None:
        super().__init__()
        self.renamer = renamer
        self._is_cancelled = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
    
    def run(self) -> None:
        try:
            logging.info("开始重命名操作")
            self.renamer.settings["preview_only"] = False
            files = self.renamer.cache['all_files'] if hasattr(self.renamer, 'cache') and 'all_files' in self.renamer.cache else []
            total_files = len(files) if files else 1
            start_time = datetime.now()
            for i, file_path in enumerate(files):
                if self._is_cancelled:
                    logging.info("重命名操作被用户取消")
                    self.rename_completed.emit(False, "操作已取消")
                    return
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.current_file_changed.emit(os.path.basename(file_path))
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / (i + 1) if i + 1 > 0 else 0
                eta = avg_time * (total_files - (i + 1))
                eta_str = f"预计剩余: {int(eta // 60)}分{int(eta % 60)}秒"
                self.eta_updated.emit(eta_str)
            success = self.renamer.process_directory()
            if success:
                logging.info("重命名操作完成")
                self.rename_completed.emit(True, "重命名操作已完成")
            else:
                logging.error("重命名过程中发生错误")
                self.rename_completed.emit(False, "重命名过程中发生错误")
        except Exception as e:
            logging.error(f"重命名失败: {e}")
            self.rename_completed.emit(False, f"重命名失败: {str(e)}")


class ComparisonDialog(QDialog):
    """重命名对比对话框"""
    
    def __init__(self, original_name: str, new_name: str, file_type: str, 
                 title: str, season: str, episode: str, year: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.original_name = original_name
        self.new_name = new_name
        self.file_type = file_type
        self.title = title
        self.season = season
        self.episode = episode
        self.year = year
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("🔄 重命名对比预览")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("📊 重命名前后对比")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 文件信息
        info_group = QGroupBox("📋 文件信息")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
        
        # 文件类型
        type_label = QLabel(self.file_type)
        type_label.setStyleSheet("color: #3498db; font-weight: bold;")
        info_layout.addRow("🎬 文件类型:", type_label)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        info_layout.addRow("📝 标题:", title_label)
        
        # 季集信息
        if self.season and self.episode:
            season_episode = f"第{self.season}集第{self.episode}集"
            season_label = QLabel(season_episode)
            season_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            info_layout.addRow("📺 季集:", season_label)
        
        # 年份
        if self.year:
            year_label = QLabel(self.year)
            year_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            info_layout.addRow("📅 年份:", year_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 重命名对比组
        comparison_group = QGroupBox("🔄 重命名对比")
        comparison_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        
        comparison_layout = QVBoxLayout()
        
        # 原文件名
        original_layout = QHBoxLayout()
        original_label = QLabel("📄 原文件名:")
        original_label.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 14px;")
        original_name_label = QLabel(self.original_name)
        original_name_label.setStyleSheet("""
            background-color: #fdf2f2;
            border: 2px solid #f5b7b1;
            border-radius: 6px;
            padding: 10px;
            color: #c0392b;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        """)
        original_name_label.setWordWrap(True)
        
        original_layout.addWidget(original_label)
        original_layout.addWidget(original_name_label, 1)
        comparison_layout.addLayout(original_layout)
        
        # 箭头
        arrow_label = QLabel("⬇️")
        arrow_label.setStyleSheet("font-size: 24px; text-align: center; margin: 10px;")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comparison_layout.addWidget(arrow_label)
        
        # 新文件名
        new_layout = QHBoxLayout()
        new_label = QLabel("🆕 新文件名:")
        new_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 14px;")
        new_name_label = QLabel(self.new_name)
        new_name_label.setStyleSheet("""
            background-color: #f0f8f0;
            border: 2px solid #a9dfbf;
            border-radius: 6px;
            padding: 10px;
            color: #229954;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        """)
        new_name_label.setWordWrap(True)
        
        new_layout.addWidget(new_label)
        new_layout.addWidget(new_name_label, 1)
        comparison_layout.addLayout(new_layout)
        
        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)
        
        # 变化分析
        analysis_group = QGroupBox("🔍 变化分析")
        analysis_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        
        analysis_layout = QVBoxLayout()
        
        # 分析变化
        changes = self.analyze_changes()
        for change in changes:
            change_label = QLabel(f"🔄 {change}")
            change_label.setStyleSheet("color: #2c3e50; font-size: 13px; margin: 5px;")
            analysis_layout.addWidget(change_label)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def analyze_changes(self) -> List[str]:
        """分析文件名变化"""
        changes = []
        
        if not self.new_name or self.new_name == self.original_name:
            changes.append("文件名无需修改")
            return changes
        
        # 分析扩展名变化
        original_ext = os.path.splitext(self.original_name)[1]
        new_ext = os.path.splitext(self.new_name)[1]
        if original_ext != new_ext:
            changes.append(f"扩展名从 {original_ext} 改为 {new_ext}")
        
        # 分析文件名主体变化
        original_base = os.path.splitext(self.original_name)[0]
        new_base = os.path.splitext(self.new_name)[0]
        
        if original_base != new_base:
            changes.append("文件名主体已标准化")
            
            # 具体分析变化
            if self.title and self.title not in original_base:
                changes.append(f"添加了标题信息：{self.title}")
            
            if self.file_type == "电视剧" and (self.season or self.episode):
                if self.season and f"S{self.season}" not in original_base:
                    changes.append(f"添加了季数信息：S{self.season}")
                if self.episode and f"E{self.episode}" not in original_base:
                    changes.append(f"添加了集数信息：E{self.episode}")
            
            if self.file_type == "电影" and self.year and self.year not in original_base:
                changes.append(f"添加了年份信息：{self.year}")
        
        # 分析特殊字符和格式
        if any(char in original_base for char in ['[', ']', '(', ')', '_', '.']):
            changes.append("清理了特殊字符和格式")
        
        if len(changes) == 0:
            changes.append("文件名格式已优化")
        
        return changes


class BatchPreviewDialog(QDialog):
    """批量预览对话框"""
    
    def __init__(self, results: List[Dict[str, Any]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.results = results
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI"""
        self.setWindowTitle("👁️ 批量重命名预览")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题和统计
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 批量重命名预览")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 统计信息
        total_files = len(self.results)
        need_rename = sum(1 for r in self.results if r.get('new_name') and r.get('new_name') != r.get('file'))
        no_change = total_files - need_rename
        
        stats_text = f"📈 总计: {total_files} 个文件 | 需要重命名: {need_rename} 个 | 无需修改: {no_change} 个"
        self.stats_label = QLabel(stats_text)
        self.stats_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            padding: 5px 10px;
            background-color: #ecf0f1;
            border-radius: 4px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # 筛选控件
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "需要重命名", "无需修改", "电影", "电视剧", "特辑"])
        self.filter_combo.currentTextChanged.connect(self.filter_preview)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索文件名...")
        self.search_box.textChanged.connect(self.filter_preview)
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(QLabel("搜索:"))
        filter_layout.addWidget(self.search_box, 1)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels([
            "📄 原文件名", "🎬 类型", "📝 标题", "🎬 类型"
        ])
        
        # 设置表格样式
        self.preview_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: white;
                alternate-background-color: #f8f9fa;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # 设置列宽
        header = self.preview_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 原文件名
            header.setSectionResizeMode(1, QHeaderView.Stretch)  # 类型
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # 标题
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # 类型
            
            # 设置表头样式
            header.setStyleSheet("""
                QHeaderView::section {
                    background-color: #34495e;
                    color: white;
                    padding: 10px 6px;
                    border: none;
                    border-right: 1px solid #2c3e50;
                    border-bottom: 1px solid #2c3e50;
                    font-weight: bold;
                    font-size: 12px;
                }
                QHeaderView::section:hover {
                    background-color: #2c3e50;
                }
            """)
        
        # 设置表格属性
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.setWordWrap(True)
        self.preview_table.cellDoubleClicked.connect(self.show_detail_comparison)
        
        layout.addWidget(self.preview_table)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 导出预览")
        export_btn.clicked.connect(self.export_preview)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
            }
        """)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
        """)
        
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 加载数据
        self.load_preview_data()
        
    def load_preview_data(self) -> None:
        """加载预览数据"""
        self.preview_table.setRowCount(0)
        
        for result in self.results:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            
            # 原文件名
            original_item = QTableWidgetItem(result.get('file', ''))
            original_item.setToolTip(f"原始文件名：{result.get('file', '')}")
            self.preview_table.setItem(row, 0, original_item)
            
            # 新文件名
            new_name = result.get('new_name', '')
            new_item = QTableWidgetItem(new_name)
            if new_name and new_name != result.get('file'):
                new_item.setForeground(QColor(39, 174, 96))  # 绿色
                new_item.setBackground(QColor(235, 248, 235))
                new_item.setToolTip(f"将重命名为：{new_name}")
            else:
                new_item.setForeground(QColor(149, 165, 166))  # 灰色
                new_item.setBackground(QColor(245, 245, 245))
                new_item.setToolTip("无需重命名")
            self.preview_table.setItem(row, 1, new_item)
            
            # 类型
            type_item = QTableWidgetItem(result.get('type', ''))
            type_value = str(result.get('type', '')).lower()
            if '电影' in type_value:
                type_item.setForeground(QColor(231, 76, 60))  # 红色
            elif '电视剧' in type_value:
                type_item.setForeground(QColor(52, 152, 219))  # 蓝色
            elif '特辑' in type_value:
                type_item.setForeground(QColor(155, 89, 182))  # 紫色
            self.preview_table.setItem(row, 2, type_item)
            
            # 标题
            title_item = QTableWidgetItem(result.get('title', ''))
            title_item.setToolTip(f"识别到的标题：{result.get('title', '')}")
            self.preview_table.setItem(row, 3, title_item)
        
        # 更新统计
        self.update_stats()
        
    def show_detail_comparison(self, row: int, column: int) -> None:
        """显示详细对比"""
        if row < len(self.results):
            result = self.results[row]
            dialog = ComparisonDialog(
                result.get('file', ''),
                result.get('new_name', ''),
                result.get('type', ''),
                result.get('title', ''),
                str(result.get('season', '')),
                str(result.get('episode', '')),
                str(result.get('year', '')),
                self
            )
            dialog.exec_()
        
    def filter_preview(self) -> None:
        """筛选预览"""
        filter_text = self.filter_combo.currentText()
        search_text = self.search_box.text().lower()
        
        for row in range(self.preview_table.rowCount()):
            show_row = True
            
            # 类型筛选
            if filter_text != "全部":
                type_item = self.preview_table.item(row, 2)
                type_text = type_item.text() if type_item else ""
                
                if filter_text == "需要重命名":
                    new_item = self.preview_table.item(row, 1)
                    new_text = new_item.text() if new_item else ""
                    original_item = self.preview_table.item(row, 0)
                    original_text = original_item.text() if original_item else ""
                    if new_text == original_text or not new_text:
                        show_row = False
                elif filter_text == "无需修改":
                    new_item = self.preview_table.item(row, 1)
                    new_text = new_item.text() if new_item else ""
                    original_item = self.preview_table.item(row, 0)
                    original_text = original_item.text() if original_item else ""
                    if new_text != original_text and new_text:
                        show_row = False
                elif filter_text not in type_text:
                    show_row = False
            
            # 搜索筛选
            if search_text and show_row:
                original_item = self.preview_table.item(row, 0)
                new_item = self.preview_table.item(row, 1)
                title_item = self.preview_table.item(row, 3)
                
                original_text = original_item.text().lower() if original_item else ""
                new_text = new_item.text().lower() if new_item else ""
                title_text = title_item.text().lower() if title_item else ""
                
                if search_text not in original_text and search_text not in new_text and search_text not in title_text:
                    show_row = False
            
            self.preview_table.setRowHidden(row, not show_row)
        
        # 更新统计
        self.update_stats()
        
    def update_stats(self) -> None:
        """更新统计信息"""
        visible_count = sum(1 for row in range(self.preview_table.rowCount()) if not self.preview_table.isRowHidden(row))
        total_count = self.preview_table.rowCount()
        
        # 更新标题中的统计信息
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(f"📈 显示: {visible_count}/{total_count} 个文件")
        
    def export_preview(self) -> None:
        """导出预览结果"""
        try:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "导出预览结果", "rename_preview.csv", "CSV文件 (*.csv);;文本文件 (*.txt)"
            )
            if not file_path:
                return
            is_txt = selected_filter.startswith("文本文件") or file_path.lower().endswith(".txt")
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                if is_txt:
                    # TXT格式，制表符分隔
                    f.write("原文件名\t新文件名\t类型\t标题\t季\t集\t年份\n")
                    for row in range(self.preview_table.rowCount()):
                        if not self.preview_table.isRowHidden(row):
                            original_item = self.preview_table.item(row, 0)
                            original = original_item.text() if original_item else ""
                            new_item = self.preview_table.item(row, 1)
                            new_name = new_item.text() if new_item else ""
                            file_type_item = self.preview_table.item(row, 2)
                            file_type = file_type_item.text() if file_type_item else ""
                            title_item = self.preview_table.item(row, 3)
                            title = title_item.text() if title_item else ""
                            result = self.results[row] if row < len(self.results) else {}
                            season = result.get('season', '')
                            episode = result.get('episode', '')
                            year = result.get('year', '')
                            f.write(f'{original}\t{new_name}\t{file_type}\t{title}\t{season}\t{episode}\t{year}\n')
                else:
                    # CSV格式
                    f.write("原文件名,新文件名,类型,标题,年份\n")
                    for row in range(self.preview_table.rowCount()):
                        if not self.preview_table.isRowHidden(row):
                            original_item = self.preview_table.item(row, 0)
                            original = original_item.text() if original_item else ""
                            new_item = self.preview_table.item(row, 1)
                            new_name = new_item.text() if new_item else ""
                            file_type_item = self.preview_table.item(row, 2)
                            file_type = file_type_item.text() if file_type_item else ""
                            title_item = self.preview_table.item(row, 3)
                            title = title_item.text() if title_item else ""
                            result = self.results[row] if row < len(self.results) else {}
                            season = result.get('season', '')
                            episode = result.get('episode', '')
                            year = result.get('year', '')
                            f.write(f'"{original}","{new_name}","{file_type}","{title}","{season}","{episode}","{year}"\n')
            QMessageBox.information(self, "成功", f"预览结果已导出到：{file_path}")
        except Exception as e:
            log_and_show_error(f"导出失败：{str(e)}", self)


class FileTableWidget(QTableWidget):
    """文件表格组件"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setup_table()
        self.cellClicked.connect(self.on_cell_clicked)
        self.search_text = ""
    
    def setup_table(self) -> None:
        """设置表格"""
        # 设置列数和标头
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "📄 原文件名", "🎬 类型", "📝 标题", "📺 季", "🎯 集", "📅 年份", "💡 建议新名", "🔄 对比预览"
        ])
        
        # 设置表格属性
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        
        # 设置表格样式
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: white;
                alternate-background-color: #f8f9fa;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # 设置列宽
        header = self.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 原文件名
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 类型
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # 标题
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 季
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 集
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 年份
            header.setSectionResizeMode(6, QHeaderView.Stretch)  # 建议新名
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 对比预览
            
            # 设置表头样式
            header.setStyleSheet("""
                QHeaderView::section {
                    background-color: #34495e;
                    color: white;
                    padding: 12px 8px;
                    border: none;
                    border-right: 1px solid #2c3e50;
                    border-bottom: 1px solid #2c3e50;
                    font-weight: bold;
                    font-size: 13px;
                }
                QHeaderView::section:hover {
                    background-color: #2c3e50;
                }
                QHeaderView::section:first {
                    border-top-left-radius: 6px;
                }
                QHeaderView::section:last {
                    border-top-right-radius: 6px;
                }
            """)
        
        # 设置垂直表头样式
        vertical_header = self.verticalHeader()
        if vertical_header:
            vertical_header.setStyleSheet("""
                QHeaderView::section {
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                    padding: 8px 4px;
                    border: none;
                    border-bottom: 1px solid #bdc3c7;
                    font-size: 12px;
                }
            """)
            vertical_header.setDefaultSectionSize(35)
    
    def update_data(self, results: List[Dict[str, Any]]) -> None:
        """更新表格数据"""
        self.setRowCount(0)
        search_text = self.search_text.lower() if self.search_text else ""
        for result in results:
            row = self.rowCount()
            self.insertRow(row)
            for col, key in enumerate(['file', 'type', 'title', 'season', 'episode', 'year', 'new_name']):
                value = result.get(key)
                item = QTableWidgetItem(str(value) if value is not None else "")
                # 高亮匹配内容
                if search_text and col in (0, 1, 2):
                    cell_text = str(value).lower() if value else ""
                    if search_text in cell_text:
                        item.setBackground(QColor(255, 255, 180))  # 浅黄色
                        # 设置特殊颜色和样式
                        if col == 6 and value and value == result.get('file'):
                            # 没有变化的新文件名显示为灰色
                            item.setForeground(QColor(128, 128, 128))
                            item.setBackground(QColor(245, 245, 245))
                elif col == 1:  # 类型
                    # 根据类型设置不同颜色
                    type_value = str(value).lower()
                    if '电影' in type_value:
                        item.setForeground(QColor(231, 76, 60))  # 红色
                    elif '电视剧' in type_value:
                        item.setForeground(QColor(52, 152, 219))  # 蓝色
                    elif '特辑' in type_value:
                        item.setForeground(QColor(155, 89, 182))  # 紫色
                    else:
                        item.setForeground(QColor(149, 165, 166))  # 灰色
                elif col == 3 or col == 4:  # 季和集列
                    # 数字列使用特殊颜色
                    item.setForeground(QColor(39, 174, 96))  # 绿色
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                elif col == 5:  # 年份
                    # 年份列使用特殊颜色
                    item.setForeground(QColor(243, 156, 18))  # 橙色
                
                # 设置工具提示
                if col == 0:  # 原文件名
                    item.setToolTip(f"原始文件名：{value}")
                elif col == 6:  # 建议新名
                    if value and value != result.get('file'):
                        item.setToolTip(f"建议重命名为：{value}")
                    else:
                        item.setToolTip("无需重命名")
                
                self.setItem(row, col, item)
            
            # 添加对比预览
            self.add_comparison_preview(row, result)
    
    def add_comparison_preview(self, row: int, result: Dict[str, Any]) -> None:
        """添加对比预览"""
        original_name = result.get('file', '')
        new_name = result.get('new_name', '')
        
        if not new_name or new_name == original_name:
            # 无需重命名
            preview_text = "🔄 无需重命名"
            preview_item = QTableWidgetItem(preview_text)
            preview_item.setForeground(QColor(149, 165, 166))  # 灰色
            preview_item.setBackground(QColor(245, 245, 245))
            preview_item.setToolTip("文件名无需修改")
        else:
            # 需要重命名，创建对比预览
            preview_text = "👁️ 查看对比"
            preview_item = QTableWidgetItem(preview_text)
            preview_item.setForeground(QColor(52, 152, 219))  # 蓝色
            preview_item.setBackground(QColor(235, 248, 255))
            preview_item.setToolTip("点击查看详细对比")
            
            # 设置为可点击
            preview_item.setFlags(preview_item.flags() | ITEM_IS_ENABLED)
        
        self.setItem(row, 7, preview_item)
    
    def on_cell_clicked(self, row: int, column: int) -> None:
        """处理单元格点击事件"""
        if column == 7:  # 对比预览
            self.show_comparison_dialog(row)
    
    def show_comparison_dialog(self, row: int) -> None:
        """显示对比对话框"""
        # 获取行数
        item0 = self.item(row, 0)
        original_name = item0.text() if item0 else ""
        item1 = self.item(row, 1)
        file_type = item1.text() if item1 else ""
        item2 = self.item(row, 2)
        title = item2.text() if item2 else ""
        item3 = self.item(row, 3)
        season = item3.text() if item3 else ""
        item4 = self.item(row, 4)
        episode = item4.text() if item4 else ""
        item5 = self.item(row, 5)
        year = item5.text() if item5 else ""
        item6 = self.item(row, 6)
        new_name = item6.text() if item6 else ""
        
        # 创建对比对话框
        dialog = ComparisonDialog(original_name, new_name, file_type, title, season, episode, year, self)
        dialog.exec_()
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        copy_action = menu.addAction("复制文件名")
        open_action = menu.addAction("打开所在文件夹")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        selected_row = self.currentRow()
        if selected_row < 0:
            return
        file_item = self.item(selected_row, 0)
        if not file_item:
            return
        file_name = file_item.text()
        if action == copy_action:
            clipboard = QGuiApplication.clipboard() if hasattr(QGuiApplication, 'clipboard') else None
            if clipboard is not None and file_name:
                clipboard.setText(file_name)
        elif action == open_action:
            # 获取文件路径（从主窗口的results获取）
            main_window = self.window()
            results = getattr(main_window, 'results', None)
            if isinstance(results, list) and results:
                for row in results:
                    if row.get('file') == file_name:
                        file_path = row.get('file_path')
                        break
            if file_path and os.path.exists(file_path):
                folder = os.path.dirname(file_path)
                import subprocess
                if sys.platform.startswith('win'):
                    os.startfile(folder)
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', folder])
                else:
                    subprocess.Popen(['xdg-open', folder])


class ControlPanel(QWidget):
    """控制面板组件"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 文件夹选择
        folder_group = QGroupBox("📁 文件夹选择")
        folder_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        
        self.folder_label = QLabel("影视文件夹：")
        self.folder_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.folder_path = QLabel(DEFAULT_SETTINGS["folder_path"])
        self.folder_path.setStyleSheet("""
            QLabel { 
                color: #3498db; 
                background-color: #ecf0f1;
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
        """)
        self.folder_path.setWordWrap(True)
        self.btn_select = QPushButton("📂 选择文件夹")
        self.btn_select.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f5f8b);
                border: 2px solid #1f5f8b;
            }
        """)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path, 1)
        folder_layout.addWidget(self.btn_select)
        folder_group.setLayout(folder_layout)
        
        # 模式选择
        mode_group = QGroupBox("⚙️ 操作模式")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        
        self.radio_preview = QRadioButton("👁️ 预览模式")
        self.radio_preview.setChecked(True)
        self.radio_preview.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                border-radius: 6px;
                background-color: #ecf0f1;
            }
            QRadioButton:hover {
                background-color: #d5dbdb;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 9px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 9px;
                background-color: #3498db;
            }
        """)
        
        self.radio_rename = QRadioButton("✏️ 实际重命名")
        self.radio_rename.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                border-radius: 6px;
                background-color: #ecf0f1;
            }
            QRadioButton:hover {
                background-color: #d5dbdb;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 9px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #e74c3c;
                border-radius: 9px;
                background-color: #e74c3c;
            }
        """)
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_preview)
        self.mode_group.addButton(self.radio_rename)
        
        mode_layout.addWidget(self.radio_preview)
        mode_layout.addWidget(self.radio_rename)
        mode_group.setLayout(mode_layout)
        
        # 操作按钮
        action_group = QGroupBox("🎯 操作")
        action_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        action_layout = QVBoxLayout()
        action_layout.setSpacing(10)
        
        self.btn_scan = QPushButton("🔍 扫描并分组")
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
                border: 2px solid #1e8449;
            }
        """)
        
        self.btn_rename = QPushButton("🚀 执行重命名")
        self.btn_rename.setEnabled(False)
        self.btn_rename.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
                border: 2px solid #a93226;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.btn_cancel = QPushButton("❌ 取消操作")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #e74c3c);
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border: 2px solid #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        action_layout.addWidget(self.btn_scan)
        action_layout.addWidget(self.btn_rename)
        action_layout.addWidget(self.btn_cancel)
        action_group.setLayout(action_layout)
        
        # 设置和帮助按钮组
        settings_group = QGroupBox("🔧 设置与帮助")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        
        self.btn_theme = QPushButton("🎨 主题切换")
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
                border: 2px solid #7d3c98;
            }
        """)
        
        self.btn_settings = QPushButton("⚙️ 设置")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f5f8b);
                border: 2px solid #1f5f8b;
            }
        """)
        
        self.btn_help = QPushButton("❓ 帮助")
        self.btn_help.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e67e22, stop:1 #d35400);
                border: 2px solid #d35400;
            }
        """)
        
        settings_layout.addWidget(self.btn_theme)
        settings_layout.addWidget(self.btn_settings)
        settings_layout.addWidget(self.btn_help)
        settings_group.setLayout(settings_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 3px;
            }
        """)
        
        # 组装布局
        layout.addWidget(folder_group)
        layout.addWidget(mode_group)
        layout.addWidget(action_group)
        layout.addWidget(settings_group)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        
        self.setLayout(layout)


class RenameUI(QWidget):
    """主界面类"""
    
    def __init__(self) -> None:
        super().__init__()
        self.settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.scan_worker: Optional[ScanWorker] = None
        self.rename_worker: Optional[RenameWorker] = None
        self.results: List[Dict[str, Any]] = []
        self.renamer: Optional[MediaRenamer] = None
        
        self.setup_ui()
        self.setup_connections()
        self.setStyleSheet(self.setup_styles())
        
    def setup_ui(self) -> None:
        """设置主界�?""
        self.setWindowTitle("影视文件重命名工�?- PyQt5")
        self.resize(1400, 800)
        self.setMinimumSize(1000, 600)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加标题�?        title_layout = QHBoxLayout()
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
        
        main_layout.addLayout(title_layout)
        
        # 创建分割�?        splitter = QSplitter(Qt.Orientation.Horizontal)
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
        
        # 搜索和筛选区�?        search_group = QGroupBox("🔍 搜索和筛�?)
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
        
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_box, 1)
        search_layout.addWidget(QLabel("类型:"))
        search_layout.addWidget(self.filter_type_combo)
        search_layout.addWidget(self.clear_filter_btn)
        search_layout.addWidget(self.batch_preview_btn)
        search_group.setLayout(search_layout)
        
        # 文件表格
        self.file_table = FileTableWidget()
        
        right_layout.addWidget(search_group)
        right_layout.addWidget(self.file_table)
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比�?        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)
        
        # 添加状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #ecf0f1; border-top: 1px solid #bdc3c7; color: #2c3e50; font-size: 12px; }")
        
        # 状态标签
        self.status_label = QLabel("🚀 就绪")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.status_bar.addWidget(self.status_label)
        
        # 进度指示�?        self.progress_indicator = QProgressBar()
        self.progress_indicator.setVisible(False)
        self.progress_indicator.setMaximumWidth(200)
        self.progress_indicator.setStyleSheet("QProgressBar { border: 1px solid #bdc3c7; border-radius: 4px; text-align: center; background-color: #ecf0f1; color: #2c3e50; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); border-radius: 3px; }")
        self.status_bar.addPermanentWidget(self.progress_indicator)
        
        # 内存使用指示�?        self.memory_label = QLabel("💾 内存: 0 MB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        # 将状态栏添加到主布局
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # 初始化状�?        self.update_status("🚀 就绪")
        
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
        
        # 模式切换
        self.control_panel.radio_rename.toggled.connect(self.on_mode_changed)
        
        # 添加快捷键支�?        self.setup_shortcuts()
        
        if self.scan_worker:
            self.scan_worker.current_file_changed.connect(self.update_current_file)
        if self.rename_worker:
            self.rename_worker.current_file_changed.connect(self.update_current_file)
        
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
        
    def select_folder(self) -> None:
        """选择文件�?""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择影视文件�?, 
            self.settings["folder_path"]
        )
        if folder:
            self.settings["folder_path"] = folder
            self.control_panel.folder_path.setText(folder)
            
    def on_mode_changed(self, checked: bool) -> None:
        """模式改变处理"""
        if checked:
            self.control_panel.btn_rename.setEnabled(len(self.results) > 0)
            
    def scan_folder(self) -> None:
        """扫描文件�?""
        folder = self.settings["folder_path"]
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "错误", "请选择有效的影视文件夹�?)
            return
            
        # 禁用按钮
        self.control_panel.btn_scan.setEnabled(False)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(True)
        
        # 更新状�?        self.update_status("正在扫描文件�?..")
        self.update_progress(0)
        
        # 创建并启动扫描线�?        self.scan_worker = ScanWorker(folder, self.settings)
        self.scan_worker.progress_updated.connect(self.update_progress)
        self.scan_worker.scan_completed.connect(self.on_scan_completed)
        self.scan_worker.error_occurred.connect(self.on_scan_error)
        self.scan_worker.eta_updated.connect(self.update_eta)
        self.scan_worker.current_file_changed.connect(self.update_current_file)
        self.scan_worker.start()
        
    def on_scan_completed(self, results: List[Dict[str, Any]]) -> None:
        """扫描完成处理"""
        self.results = results
        
        # 更新表格
        self.file_table.update_data(results)
        
        # 恢复按钮状�?        self.control_panel.btn_scan.setEnabled(True)
        self.control_panel.btn_rename.setEnabled(self.control_panel.radio_rename.isChecked())
        self.control_panel.btn_cancel.setEnabled(False)
        
        # 更新状�?        self.update_status(f"�?扫描完成，共找到 {len(results)} 个文�?)
        self.update_progress(100)
        self.update_memory_usage()
        
        # 统计文件类型
        type_counts = {}
        for result in results:
            file_type = result.get('type', '未知')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # 显示详细结果统计
        stats_text = f"📊 扫描统计：\n"
        for file_type, count in type_counts.items():
            stats_text += f"�?{file_type}: {count} 个文件\n"
        
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
        """执行重命�?""
        if not self.results:
            QMessageBox.warning(self, "错误", "请先扫描并分析文件夹�?)
            return
        # 大批量操作二次确�?        if len(self.results) > 100:
            reply = QMessageBox.question(
                self,
                "批量重命名确�?,
                f"即将重命�?{len(self.results)} 个文件，是否继续�?,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        # 确认对话�?        reply = QMessageBox.question(
            self,
            "确认重命�?,
            f"确定要对 {len(self.results)} 个文件执行重命名操作吗？\n此操作不可撤销�?,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        # 禁用按钮
        self.control_panel.btn_scan.setEnabled(False)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(True)
        # 更新状�?        self.update_status("正在执行重命名操�?..")
        self.update_progress(0)
        # 创建重命名器
        self.settings["preview_only"] = False
        self.renamer = MediaRenamer(self.settings)
        self.renamer.build_directory_cache(self.settings["folder_path"])
        # 创建并启动重命名线程
        self.rename_worker = RenameWorker(self.renamer)
        self.rename_worker.rename_completed.connect(self.on_rename_completed)
        self.rename_worker.eta_updated.connect(self.update_eta)
        self.rename_worker.current_file_changed.connect(self.update_current_file)
        self.rename_worker.start()
        
    def on_rename_completed(self, success: bool, message: str) -> None:
        """重命名完成处�?""
        # 恢复按钮状�?        self.control_panel.btn_scan.setEnabled(True)
        self.control_panel.btn_rename.setEnabled(False)
        self.control_panel.btn_cancel.setEnabled(False)
        
        # 更新状�?        if success:
            self.update_status("�?重命名操作完�?)
            self.update_progress(100)
        else:
            self.update_status(f"�?重命名失�? {message}")
            self.update_progress(0)
        self.update_memory_usage()
        
        # 显示结果
        if success:
            QMessageBox.information(
                self, 
                "🎉 操作完成", 
                f"{message}\n\n所有文件已成功重命名！"
            )
            # 重新扫描以更新显�?            self.scan_folder()
        else:
            QMessageBox.critical(
                self, 
                "�?操作失败", 
                f"重命名过程中发生错误：\n\n{message}\n\n请检查文件权限和磁盘空间�?
            )
        
    def open_settings(self) -> None:
        """打开设置对话�?""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # 更新设置
            self.settings = dialog.get_settings()
            
            # 更新界面显示
            self.control_panel.folder_path.setText(self.settings["folder_path"])
            
            # 显示设置已更新提�?            QMessageBox.information(self, "设置已更�?, "设置已保存并生效�?)
            
    def open_help(self) -> None:
        """打开帮助对话�?""
        dialog = HelpDialog(self)
        dialog.exec_()
        
    def toggle_theme(self) -> None:
        """切换主题"""
        current_theme = getattr(self, '_current_theme', 'light')
        
        if current_theme == 'light':
            # 切换到深色主�?            self.setStyleSheet(self.get_dark_theme())
            self._current_theme = 'dark'
            self.control_panel.btn_theme.setText("☀�?浅色")
        else:
            # 切换到浅色主�?            self.setStyleSheet(self.get_light_theme())
            self._current_theme = 'light'
            self.control_panel.btn_theme.setText("🌙 深色")
            
    def get_light_theme(self) -> str:
        """获取浅色主题样式"""
        return self.setup_styles()
        
    def get_dark_theme(self) -> str:
        """获取深色主题样式"""
        return """
            QMainWindow {
                background-color: #2d3748;
                color: #e2e8f0;
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
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3182ce, stop:1 #2c5aa0);
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
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c5aa0, stop:1 #1a365d);
                border: 2px solid #1a365d;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a365d, stop:1 #0f2027);
                border: 2px solid #0f2027;
            }
            QPushButton:disabled {
                background-color: #718096;
                color: #a0aec0;
            }
            QLineEdit {
                border: 2px solid #718096;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #4a5568;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border-color: #3182ce;
                outline: none;
            }
            QComboBox {
                border: 2px solid #718096;
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
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e2e8f0;
            }
            QTableWidget {
                gridline-color: #718096;
                selection-background-color: #2b6cb0;
                alternate-background-color: #4a5568;
                background-color: #2d3748;
                border: 1px solid #718096;
                border-radius: 6px;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #4a5568;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #718096;
                font-weight: bold;
                color: #e2e8f0;
            }
            QHeaderView::section:hover {
                background-color: #718096;
            }
            QStatusBar {
                background-color: #4a5568;
                border-top: 1px solid #718096;
                color: #e2e8f0;
            }
            QProgressBar {
                border: 1px solid #718096;
                border-radius: 4px;
                text-align: center;
                background-color: #4a5568;
                color: #e2e8f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3182ce, stop:1 #2c5aa0);
                border-radius: 3px;
            }
            QRadioButton {
                font-size: 14px;
                color: #e2e8f0;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #718096;
                border-radius: 9px;
                background-color: #4a5568;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #3182ce;
                border-radius: 9px;
                background-color: #3182ce;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
            }
        """
        
    def setup_shortcuts(self) -> None:
        """设置快捷�?""
        # 文件操作快捷�?        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.select_folder)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.scan_folder)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.do_rename)
        
        # 设置和帮助快捷键
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.open_settings)
        QShortcut(QKeySequence("F1"), self).activated.connect(self.open_help)
        
        # 模式切换快捷�?        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.show_batch_preview)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self).activated.connect(lambda: self.control_panel.radio_rename.setChecked(True))
        
        # 添加工具提示显示快捷�?        self.control_panel.btn_select.setToolTip("选择文件�?(Ctrl+O)")
        self.control_panel.btn_scan.setToolTip("扫描并分�?(F5)")
        self.control_panel.btn_rename.setToolTip("执行重命名(Ctrl+R)")
        self.control_panel.btn_settings.setToolTip("设置 (Ctrl+S)")
        self.control_panel.btn_help.setToolTip("帮助 (F1)")
        self.control_panel.radio_preview.setToolTip("预览模式")
        self.control_panel.radio_rename.setToolTip("实际重命�?(Ctrl+Shift+R)")
        
    def filter_files(self) -> None:
        """筛选文件"""
        search_text = self.search_box.text().lower()
        filter_type = self.filter_type_combo.currentText()
        self.file_table.search_text = search_text
        for row in range(self.file_table.rowCount()):
            show_row = True
            if search_text:
                file_name_item = self.file_table.item(row, 0)
                title_item = self.file_table.item(row, 2)
                file_type_item = self.file_table.item(row, 1)
                file_name = file_name_item.text().lower() if file_name_item else ""
                title = title_item.text().lower() if title_item else ""
                file_type = file_type_item.text().lower() if file_type_item else ""
                if search_text not in file_name and search_text not in title and search_text not in file_type:
                    show_row = False
            if filter_type != "全部类型":
                file_type_item = self.file_table.item(row, 1)
                file_type = file_type_item.text() if file_type_item else ""
                if filter_type not in file_type:
                    show_row = False
            self.file_table.setRowHidden(row, not show_row)
        # 更新高亮
        self.file_table.update_data(self.results)
        visible_count = sum(1 for row in range(self.file_table.rowCount()) if not self.file_table.isRowHidden(row))
        self.update_status(f"显示 {visible_count}/{len(self.results)} 个文件")
        
    def clear_filters(self) -> None:
        """清除筛选"""
        self.search_box.clear()
        self.filter_type_combo.setCurrentText("全部类型")
        
        # 显示所有行
        for row in range(self.file_table.rowCount()):
            self.file_table.setRowHidden(row, False)
        
        self.update_status(f"显示所有 {len(self.results)} 个文件")
        
    def show_batch_preview(self) -> None:
        """显示批量预览对话框"""
        if not self.results:
            QMessageBox.information(self, "提示", "请先扫描文件")
            return
            
        # 创建批量预览对话框
        dialog = BatchPreviewDialog(self.results, self)
        dialog.exec_()
        
    def update_status(self, message: str) -> None:
        """更新状态栏信息"""
        # 添加状态图标
        if "扫描" in message:
            icon = "🔍"
        elif "重命名" in message:
            icon = "✏️"
        elif "完成" in message:
            icon = "✅"
        elif "错误" in message:
            icon = "❌"
        elif "就绪" in message:
            icon = "🚀"
        else:
            icon = "ℹ️"
        
        self.status_label.setText(f"{icon} {message}")
        
        # 根据状态设置不同的颜色
        if "错误" in message:
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        elif "完成" in message:
            self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        elif "扫描" in message or "重命名" in message:
            self.status_label.setStyleSheet("font-weight: bold; color: #3498db;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            
    def update_progress(self, value: int) -> None:
        """更新进度条"""
        self.progress_indicator.setValue(value)
        if value == 0:
            self.progress_indicator.setVisible(False)
        elif not self.progress_indicator.isVisible():
            self.progress_indicator.setVisible(True)
            
        # 更新进度条颜色
        if value > 0 and value < 100:
            self.progress_indicator.setStyleSheet("QProgressBar { border: 1px solid #bdc3c7; border-radius: 4px; text-align: center; background-color: #ecf0f1; color: #2c3e50; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); border-radius: 3px; }")
        elif value == 100:
            self.progress_indicator.setStyleSheet("QProgressBar { border: 1px solid #bdc3c7; border-radius: 4px; text-align: center; background-color: #ecf0f1; color: #2c3e50; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27ae60, stop:1 #229954); border-radius: 3px; }")
            
    def update_memory_usage(self) -> None:
        """更新内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # 根据内存使用量设置不同颜色
            if memory_mb < 100:
                color = "#27ae60"  # 绿色
                icon = "💾"
            elif memory_mb < 500:
                color = "#f39c12"  # 橙色
                icon = "⚠️"
            else:
                color = "#e74c3c"  # 红色
                icon = "🚨"
                
            self.memory_label.setText(f"{icon} 内存: {memory_mb:.1f} MB")
            self.memory_label.setStyleSheet(f"font-weight: bold; color: {color};")
        except ImportError:
            self.memory_label.setText("💾 内存: 未知")
            self.memory_label.setStyleSheet("font-weight: bold; color: #95a5a6;")
        
    def closeEvent(self, event: Any) -> None:
        """窗口关闭事件"""
        # 保存窗口状态和设置
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        # 自动保存当前设置
        try:
            config_manager = ConfigManager()
            config_manager.set_setting("settings", self.settings)
            config_manager.save_config()
            logging.info("自动保存设置成功")
        except Exception as e:
            logging.error(f"自动保存设置失败: {e}")
        event.accept()
    
    def showEvent(self, event: Any) -> None:
        """窗口显示事件"""
        # 恢复窗口状态
        settings = QSettings()
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        event.accept()
    
    def cancel_operation(self) -> None:
        """取消当前操作"""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            logging.info("用户请求取消扫描操作")
        if self.rename_worker and self.rename_worker.isRunning():
            self.rename_worker.cancel()
            logging.info("用户请求取消重命名操作")
        self.control_panel.btn_cancel.setEnabled(False)
        self.update_status("操作已取消")
    
    def update_eta(self, eta_str: str) -> None:
        """更新剩余时间显示"""
        self.progress_indicator.setFormat(f"%p% 完成 | {eta_str}")
    
    def update_current_file(self, filename: str) -> None:
        if filename:
            self.status_label.setText(f"当前处理：{filename}")


def main() -> None:
    """主函数"""
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    app = QApplication(sys.argv)
    app.setApplicationName("影视文件重命名工具")
    app.setApplicationVersion("1.3")
    app.setOrganizationName("MediaRename")
    ui = RenameUI()
    ui.show()
    sys.exit(app.exec_()) 

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        logging.error(f"程序运行时发生异常: {e}\n{traceback.format_exc()}")
        from PyQt5.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "错误", f"程序运行时发生异常:\n{e}\n\n{traceback.format_exc()}")
        sys.exit(1)
