#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件表格模块 - 影视文件重命名工具 v1.3
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAction,
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QGroupBox, QSplitter, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import List, Dict, Any

class FileTableWidget(QTableWidget):
    """文件表格组件"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setup_table()
        
    def setup_table(self) -> None:
        """设置表格（增强版）"""
        # 设置列数和标题 - 添加预览列
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "📁 原文件名",
            "🎬 识别结果", 
            "📝 新文件名",
            "👁️ 预览",  # 新增预览列
            "📊 文件类型",
            "📈 状态",
            "🔍 操作"
        ])
        
        # 设置表格属性
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        
        # 设置列宽
        header = self.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 原文件名
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 识别结果
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # 新文件名
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 预览
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 文件类型
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 状态
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 操作
        
        # 设置行高
        vheader = self.verticalHeader()
        if vheader:
            vheader.setDefaultSectionSize(60)
        
        # 连接信号
        self.cellClicked.connect(self.on_cell_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        
    def update_data(self, results: List[Dict[str, Any]]) -> None:
        """更新表格数据（增强版）"""
        self.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # 原文件名
            original_name = result.get('original_name', '')
            original_item = QTableWidgetItem(original_name)
            original_item.setToolTip(original_name)
            self.setItem(row, 0, original_item)
            
            # 识别结果
            title = result.get('title', '')
            season = result.get('season', '')
            episode = result.get('episode', '')
            year = result.get('year', '')
            
            if title:
                recognition_text = f"{title}"
                if year:
                    recognition_text += f" ({year})"
                if season and episode:
                    # 确保season和episode是字符串
                    season_str = str(season).zfill(2) if season else ''
                    episode_str = str(episode).zfill(2) if episode else ''
                    recognition_text += f" S{season_str}E{episode_str}"
                elif season:
                    season_str = str(season).zfill(2) if season else ''
                    recognition_text += f" S{season_str}"
            else:
                recognition_text = "未识别"
                
            recognition_item = QTableWidgetItem(recognition_text)
            recognition_item.setToolTip(recognition_text)
            self.setItem(row, 1, recognition_item)
            
            # 新文件名
            new_name = result.get('new_name', '')
            new_item = QTableWidgetItem(new_name)
            new_item.setToolTip(new_name)
            self.setItem(row, 2, new_item)
            
            # 预览按钮
            self.add_preview_button(row, result)
            
            # 文件类型
            file_type = result.get('type', '未知')
            type_item = QTableWidgetItem(file_type)
            type_item.setToolTip(file_type)
            self.setItem(row, 4, type_item)
            
            # 状态
            status = result.get('status', '待处理')
            status_item = QTableWidgetItem(status)
            status_item.setToolTip(status)
            
            # 根据状态设置颜色
            if status == '成功':
                status_item.setBackground(QColor('#d4edda'))
                status_item.setForeground(QColor('#155724'))
            elif status == '失败':
                status_item.setBackground(QColor('#f8d7da'))
                status_item.setForeground(QColor('#721c24'))
            elif status == '跳过':
                status_item.setBackground(QColor('#fff3cd'))
                status_item.setForeground(QColor('#856404'))
            else:
                status_item.setBackground(QColor('#e2e3e5'))
                status_item.setForeground(QColor('#383d41'))
                
            self.setItem(row, 5, status_item)
            
            # 操作按钮
            self.add_action_buttons(row, result)
    
    def add_preview_button(self, row: int, result: Dict[str, Any]) -> None:
        """添加预览按钮"""
        # 创建预览按钮
        preview_btn = QPushButton("👁️ 预览")
        preview_btn.setToolTip("点击查看重命名预览详情")
        preview_btn.setFixedSize(80, 30)
        preview_btn.setStyleSheet("""
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17a2b8, stop:1 #138496); 
                border: none; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
            } 
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #138496, stop:1 #117a8b); 
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #117a8b, stop:1 #0f6674); 
            }
        """)
        preview_btn.clicked.connect(lambda: self.show_preview_dialog(row, result))
        
        # 设置按钮到表格
        self.setCellWidget(row, 3, preview_btn)
            
    def add_action_buttons(self, row: int, result: Dict[str, Any]) -> None:
        """添加操作按钮（更新列位置）"""
        # 创建操作按钮容器
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(5, 2, 5, 2)
        action_layout.setSpacing(5)
        
        # 编辑按钮
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("编辑重命名规则")
        edit_btn.setFixedSize(30, 25)
        edit_btn.setStyleSheet("QPushButton { background-color: #ffc107; border: none; color: white; border-radius: 3px; } QPushButton:hover { background-color: #e0a800; }")
        edit_btn.clicked.connect(lambda: self.edit_rename_rule(row, result))
        
        # 跳过按钮
        skip_btn = QPushButton("⏭️")
        skip_btn.setToolTip("跳过此文件")
        skip_btn.setFixedSize(30, 25)
        skip_btn.setStyleSheet("QPushButton { background-color: #6c757d; border: none; color: white; border-radius: 3px; } QPushButton:hover { background-color: #5a6268; }")
        skip_btn.clicked.connect(lambda: self.skip_file(row, result))
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(skip_btn)
        action_layout.addStretch()
        
        action_widget.setLayout(action_layout)
        self.setCellWidget(row, 6, action_widget)  # 更新列位置
        
    def show_preview_dialog(self, row: int, result: Dict[str, Any]) -> None:
        """显示预览对话框（增强版）"""
        dialog = EnhancedPreviewDialog(result, self)
        dialog.exec_()
        
    def edit_rename_rule(self, row: int, result: Dict[str, Any]) -> None:
        """编辑重命名规则"""
        # 这里可以实现编辑重命名规则的功能
        QMessageBox.information(self, "编辑", "编辑重命名规则功能待实现")
        
    def skip_file(self, row: int, result: Dict[str, Any]) -> None:
        """跳过文件"""
        result['status'] = '跳过'
        status_item = QTableWidgetItem('跳过')
        status_item.setBackground(QColor('#fff3cd'))
        status_item.setForeground(QColor('#856404'))
        self.setItem(row, 4, status_item)
        
    def on_cell_clicked(self, row: int, column: int) -> None:
        """单元格点击事件"""
        if column == 1:  # 识别结果列
            self.show_recognition_details(row)
            
    def show_recognition_details(self, row: int) -> None:
        """显示识别详情"""
        # 这里可以显示更详细的识别信息
        pass
        
    def contextMenuEvent(self, event) -> None:
        """右键菜单事件"""
        menu = QMenu(self)
        
        # 添加菜单项
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self.selectAll)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        copy_action = QAction("复制文件名", self)
        copy_action.triggered.connect(self.copy_filename)
        menu.addAction(copy_action)
        
        export_action = QAction("导出列表", self)
        export_action.triggered.connect(self.export_list)
        menu.addAction(export_action)
        
        menu.exec_(event.globalPosition().toPoint())
        
    def copy_filename(self) -> None:
        """复制文件名"""
        # 实现复制功能
        pass
        
    def export_list(self) -> None:
        """导出列表"""
        # 实现导出功能
        pass
        
    def filter_files(self, search_text: str, file_type: str) -> None:
        """筛选文件"""
        if not hasattr(self, '_all_results'):
            return
            
        filtered_results = []
        
        for result in self._all_results:
            # 搜索文本筛选
            if search_text:
                search_lower = search_text.lower()
                original_name = result.get('original_name', '').lower()
                title = result.get('title', '').lower()
                new_name = result.get('new_name', '').lower()
                
                if not (search_lower in original_name or 
                       search_lower in title or 
                       search_lower in new_name):
                    continue
            
            # 文件类型筛选
            if file_type != "全部类型":
                result_type = result.get('type', '')
                if result_type != file_type:
                    continue
                    
            filtered_results.append(result)
        
        # 更新表格显示
        self.update_data(filtered_results)
        
    def set_all_results(self, results: List[Dict[str, Any]]) -> None:
        """设置所有结果数据（用于筛选）"""
        self._all_results = results

class EnhancedPreviewDialog(QDialog):
    """增强的预览对话框"""
    
    def __init__(self, result: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.result = result
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置界面"""
        self.setWindowTitle("重命名预览详情")
        self.setFixedSize(600, 500)
        self.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("📝 重命名预览详情")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：文件信息
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 文件基本信息
        info_group = QGroupBox("📁 文件信息")
        info_layout = QVBoxLayout()
        
        original_name = self.result.get('original_name', '')
        file_path = self.result.get('file_path', '')
        
        info_layout.addWidget(QLabel(f"原文件名: {original_name}"))
        info_layout.addWidget(QLabel(f"文件路径: {file_path}"))
        info_layout.addWidget(QLabel(f"文件类型: {self.result.get('type', '未知')}"))
        info_layout.addWidget(QLabel(f"状态: {self.result.get('status', '待处理')}"))
        
        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)
        
        # 识别结果
        recognition_group = QGroupBox("🎬 识别结果")
        recognition_layout = QVBoxLayout()
        
        title = self.result.get('title', '')
        year = self.result.get('year', '')
        season = self.result.get('season', '')
        episode = self.result.get('episode', '')
        
        recognition_layout.addWidget(QLabel(f"标题: {title or '未识别'}"))
        recognition_layout.addWidget(QLabel(f"年份: {year or '未知'}"))
        recognition_layout.addWidget(QLabel(f"季数: {season or '未知'}"))
        recognition_layout.addWidget(QLabel(f"集数: {episode or '未知'}"))
        
        recognition_group.setLayout(recognition_layout)
        left_layout.addWidget(recognition_group)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # 右侧：重命名预览
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 重命名对比
        rename_group = QGroupBox("🔄 重命名对比")
        rename_layout = QVBoxLayout()
        
        # 原文件名
        original_label = QLabel("原文件名:")
        original_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        rename_layout.addWidget(original_label)
        
        original_text = QTextEdit()
        original_text.setPlainText(original_name)
        original_text.setMaximumHeight(60)
        original_text.setStyleSheet("QTextEdit { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; }")
        rename_layout.addWidget(original_text)
        
        # 箭头
        arrow_label = QLabel("⬇️")
        arrow_label.setAlignment(Qt.AlignCenter)
        arrow_label.setStyleSheet("font-size: 20px; margin: 5px;")
        rename_layout.addWidget(arrow_label)
        
        # 新文件名
        new_label = QLabel("新文件名:")
        new_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        rename_layout.addWidget(new_label)
        
        new_name = self.result.get('new_name', '')
        new_text = QTextEdit()
        new_text.setPlainText(new_name)
        new_text.setMaximumHeight(60)
        new_text.setStyleSheet("QTextEdit { background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; }")
        rename_layout.addWidget(new_text)
        
        rename_group.setLayout(rename_layout)
        right_layout.addWidget(rename_group)
        
        # 重命名规则
        rule_group = QGroupBox("📋 重命名规则")
        rule_layout = QVBoxLayout()
        
        file_type = self.result.get('type', '')
        if file_type == 'movie':
            rule_text = "电影命名规则: {title} ({year})"
        elif file_type == 'tv':
            if season == 0:
                rule_text = "特辑命名规则: {title}.S00.E{episode:02d}"
            else:
                rule_text = "电视剧命名规则: {title}.S{season:02d}E{episode:02d}"
        else:
            rule_text = "未知类型，保持原文件名"
        
        rule_label = QLabel(rule_text)
        rule_label.setWordWrap(True)
        rule_label.setStyleSheet("color: #6c757d; font-style: italic;")
        rule_layout.addWidget(rule_label)
        
        rule_group.setLayout(rule_layout)
        right_layout.addWidget(rule_group)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([250, 350])
        layout.addWidget(splitter)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton { 
                background-color: #6c757d; 
                border: none; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 4px; 
                font-weight: bold;
            } 
            QPushButton:hover { 
                background-color: #5a6268; 
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout) 