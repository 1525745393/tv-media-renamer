#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制面板模块 - 影视文件重命名工具 v1.3
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QGroupBox, QRadioButton, QButtonGroup, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ControlPanel(QWidget):
    """控制面板类"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件夹选择区域
        folder_group = QGroupBox("📁 文件夹选择")
        folder_layout = QVBoxLayout()
        
        # 文件夹路径显示
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("请选择影视文件夹...")
        self.folder_path.setReadOnly(True)
        self.folder_path.setStyleSheet("QLineEdit { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; background-color: #f8f9fa; }")
        
        # 选择按钮
        self.btn_select = QPushButton("📂 选择文件夹")
        self.btn_select.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27ae60, stop:1 #229954); border: none; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #229954, stop:1 #1e8449); }")
        
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(self.btn_select)
        folder_group.setLayout(folder_layout)
        
        # 操作模式区域
        mode_group = QGroupBox("🎯 操作模式")
        mode_layout = QVBoxLayout()
        
        self.radio_preview = QRadioButton("👁️ 预览模式")
        self.radio_preview.setChecked(True)
        self.radio_preview.setToolTip("仅预览重命名结果，不实际修改文件")
        
        self.radio_rename = QRadioButton("✏️ 重命名模式")
        self.radio_rename.setToolTip("实际执行文件重命名操作")
        
        mode_layout.addWidget(self.radio_preview)
        mode_layout.addWidget(self.radio_rename)
        mode_group.setLayout(mode_layout)
        
        # 主要操作区域
        action_group = QGroupBox("⚡ 主要操作")
        action_layout = QVBoxLayout()
        
        self.btn_scan = QPushButton("🔍 扫描文件")
        self.btn_scan.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); border: none; color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #21618c); }")
        self.btn_scan.setToolTip("扫描选定文件夹中的影视文件")
        
        self.btn_rename = QPushButton("🚀 开始重命名")
        self.btn_rename.setEnabled(False)
        self.btn_rename.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e67e22, stop:1 #d35400); border: none; color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; font-size: 14px; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d35400, stop:1 #ba4a00); } QPushButton:disabled { background-color: #95a5a6; color: #7f8c8d; }")
        self.btn_rename.setToolTip("执行文件重命名操作")
        
        self.btn_cancel = QPushButton("❌ 取消操作")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet("QPushButton { background-color: #e74c3c; border: none; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; } QPushButton:disabled { background-color: #95a5a6; color: #7f8c8d; }")
        self.btn_cancel.setToolTip("取消当前正在进行的操作")
        
        # 撤销重做区域
        undo_group = QGroupBox("↩️ 撤销重做")
        undo_layout = QHBoxLayout()
        
        self.btn_undo = QPushButton("↩️ 撤销")
        self.btn_undo.setEnabled(False)
        self.btn_undo.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f39c12, stop:1 #e67e22); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e67e22, stop:1 #d35400); } QPushButton:disabled { background-color: #95a5a6; color: #7f8c8d; }")
        self.btn_undo.setToolTip("撤销上一步操作 (Ctrl+Z)")
        
        self.btn_redo = QPushButton("↪️ 重做")
        self.btn_redo.setEnabled(False)
        self.btn_redo.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16a085, stop:1 #138d75); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #138d75, stop:1 #117a65); } QPushButton:disabled { background-color: #95a5a6; color: #7f8c8d; }")
        self.btn_redo.setToolTip("重做上一步操作 (Ctrl+Y)")
        
        undo_layout.addWidget(self.btn_undo)
        undo_layout.addWidget(self.btn_redo)
        undo_group.setLayout(undo_layout)
        
        action_layout.addWidget(self.btn_scan)
        action_layout.addWidget(self.btn_rename)
        action_layout.addWidget(self.btn_cancel)
        action_layout.addWidget(undo_group)
        action_group.setLayout(action_layout)
        
        # 工具区域
        tools_group = QGroupBox("🛠️ 工具")
        tools_layout = QVBoxLayout()
        
        self.btn_theme = QPushButton("🌙 深色主题")
        self.btn_theme.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34495e, stop:1 #2c3e50); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c3e50, stop:1 #1a252f); }")
        self.btn_theme.setToolTip("切换深色/浅色主题")
        
        self.btn_settings = QPushButton("⚙️ 设置")
        self.btn_settings.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9b59b6, stop:1 #8e44ad); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e44ad, stop:1 #7d3c98); }")
        self.btn_settings.setToolTip("打开设置对话框")
        
        self.btn_help = QPushButton("❓ 帮助")
        self.btn_help.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); border: none; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #21618c); }")
        self.btn_help.setToolTip("查看帮助信息")
        
        tools_layout.addWidget(self.btn_theme)
        tools_layout.addWidget(self.btn_settings)
        tools_layout.addWidget(self.btn_help)
        tools_group.setLayout(tools_layout)
        
        # 添加所有组件到主布局
        layout.addWidget(folder_group)
        layout.addWidget(mode_group)
        layout.addWidget(action_group)
        layout.addWidget(tools_group)
        layout.addStretch()  # 添加弹性空间
        
        self.setLayout(layout)
        
        # 设置固定宽度
        self.setFixedWidth(320) 