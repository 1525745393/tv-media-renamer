#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量预览对话框模块 - 影视文件重命名工具 v1.3
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel, QTextEdit, QGroupBox, QSplitter, QProgressBar, QComboBox, QLineEdit, QCheckBox, QFormLayout, QMessageBox, QFileDialog, QMenu, QAction, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import List, Dict, Any
import json
import csv

class BatchPreviewDialog(QDialog):
    """批量预览对话框"""
    
    def __init__(self, results: List[Dict[str, Any]], parent=None) -> None:
        super().__init__(parent)
        self.results = results
        self.filtered_results = results.copy()
        self.setup_ui()
        self.load_preview_data()
        
    def setup_ui(self) -> None:
        """设置界面"""
        self.setWindowTitle("批量预览 - 影视文件重命名工具")
        self.setModal(True)
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：筛选和统计
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 筛选区域
        filter_group = QGroupBox("🔍 筛选条件")
        filter_layout = QFormLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("输入关键词搜索...")
        self.search_box.textChanged.connect(self.filter_preview)
        filter_layout.addRow("搜索:", self.search_box)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部类型", "电影", "电视剧", "特辑", "未知"])
        self.type_combo.currentTextChanged.connect(self.filter_preview)
        filter_layout.addRow("类型:", self.type_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部状态", "待处理", "成功", "失败", "跳过"])
        self.status_combo.currentTextChanged.connect(self.filter_preview)
        filter_layout.addRow("状态:", self.status_combo)
        
        self.only_recognized = QCheckBox("仅显示已识别的文件")
        self.only_recognized.toggled.connect(self.filter_preview)
        filter_layout.addRow("", self.only_recognized)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
        # 统计区域
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)
        
        # 操作区域
        action_group = QGroupBox("⚙️ 操作")
        action_layout = QVBoxLayout()
        
        self.export_btn = QPushButton("📤 导出预览")
        self.export_btn.clicked.connect(self.export_preview)
        self.export_btn.setStyleSheet("QPushButton { background-color: #28a745; border: none; color: white; padding: 8px; border-radius: 4px; } QPushButton:hover { background-color: #218838; }")
        
        self.select_all_btn = QPushButton("✅ 全选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setStyleSheet("QPushButton { background-color: #007bff; border: none; color: white; padding: 8px; border-radius: 4px; } QPushButton:hover { background-color: #0056b3; }")
        
        self.deselect_all_btn = QPushButton("❌ 取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setStyleSheet("QPushButton { background-color: #6c757d; border: none; color: white; padding: 8px; border-radius: 4px; } QPushButton:hover { background-color: #5a6268; }")
        
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.select_all_btn)
        action_layout.addWidget(self.deselect_all_btn)
        action_layout.addStretch()
        
        action_group.setLayout(action_layout)
        left_layout.addWidget(action_group)
        
        left_widget.setLayout(left_layout)
        
        # 右侧：预览表格
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 表格标题
        table_header = QLabel("📋 重命名预览列表")
        table_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        right_layout.addWidget(table_header)
        
        # 预览表格
        self.preview_table = QTableWidget()
        self.setup_preview_table()
        right_layout.addWidget(self.preview_table)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        right_widget.setLayout(right_layout)
        
        # 设置分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 900])
        
        layout.addWidget(splitter)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("QPushButton { background-color: #6c757d; border: none; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #5a6268; }")
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def setup_preview_table(self) -> None:
        """设置预览表格"""
        # 设置列数和标题
        self.preview_table.setColumnCount(7)
        self.preview_table.setHorizontalHeaderLabels([
            "✅ 选择",
            "📁 原文件名",
            "🎬 识别结果", 
            "📝 新文件名",
            "📊 文件类型",
            "📈 状态",
            "🔍 详情"
        ])
        
        # 设置表格属性
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.preview_table.setSelectionMode(QTableWidget.SingleSelection)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.setWordWrap(True)
        
        # 设置列宽
        header = self.preview_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 选择
            header.setSectionResizeMode(1, QHeaderView.Stretch)  # 原文件名
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 识别结果
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # 新文件名
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 文件类型
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 状态
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 详情
        
        # 设置行高
        vertical_header = self.preview_table.verticalHeader()
        if vertical_header:
            vertical_header.setDefaultSectionSize(50)
        
        # 连接信号
        self.preview_table.cellClicked.connect(self.on_cell_clicked)
        self.preview_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview_table.customContextMenuRequested.connect(self.contextMenuEvent)
        
    def load_preview_data(self) -> None:
        """加载预览数据"""
        self.preview_table.setRowCount(len(self.results))
        
        for row, result in enumerate(self.results):
            # 选择复选框
            from PyQt5.QtWidgets import QCheckBox
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # 默认选中
            self.preview_table.setCellWidget(row, 0, checkbox)
            
            # 原文件名
            original_name = result.get('original_name', '')
            original_item = QTableWidgetItem(original_name)
            original_item.setToolTip(original_name)
            self.preview_table.setItem(row, 1, original_item)
            
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
            self.preview_table.setItem(row, 2, recognition_item)
            
            # 新文件名
            new_name = result.get('new_name', '')
            new_item = QTableWidgetItem(new_name)
            new_item.setToolTip(new_name)
            self.preview_table.setItem(row, 3, new_item)
            
            # 文件类型
            file_type = result.get('type', '未知')
            type_item = QTableWidgetItem(file_type)
            type_item.setToolTip(file_type)
            self.preview_table.setItem(row, 4, type_item)
            
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
                
            self.preview_table.setItem(row, 5, status_item)
            
            # 详情按钮
            detail_btn = QPushButton("👁️")
            detail_btn.setToolTip("查看详细信息")
            detail_btn.setFixedSize(30, 25)
            detail_btn.setStyleSheet("QPushButton { background-color: #17a2b8; border: none; color: white; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
            detail_btn.clicked.connect(lambda checked, r=row: self.show_detail_dialog(r))
            self.preview_table.setCellWidget(row, 6, detail_btn)
        
        # 更新统计信息
        self.update_stats()
        
    def filter_preview(self) -> None:
        """筛选预览"""
        search_text = self.search_box.text().lower()
        file_type = self.type_combo.currentText()
        status = self.status_combo.currentText()
        only_recognized = self.only_recognized.isChecked()
        
        self.filtered_results = []
        
        for result in self.results:
            # 搜索文本筛选
            if search_text:
                original_name = result.get('original_name', '').lower()
                title = result.get('title', '').lower()
                new_name = result.get('new_name', '').lower()
                
                if not (search_text in original_name or 
                       search_text in title or 
                       search_text in new_name):
                    continue
            
            # 文件类型筛选
            if file_type != "全部类型":
                result_type = result.get('type', '')
                if result_type != file_type:
                    continue
                    
            # 状态筛选
            if status != "全部状态":
                result_status = result.get('status', '')
                if result_status != status:
                    continue
                    
            # 仅显示已识别
            if only_recognized:
                title = result.get('title', '')
                if not title:
                    continue
                    
            self.filtered_results.append(result)
        
        # 更新表格显示
        self.preview_table.setRowCount(len(self.filtered_results))
        
        for row, result in enumerate(self.filtered_results):
            # 选择复选框
            from PyQt5.QtWidgets import QCheckBox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.preview_table.setCellWidget(row, 0, checkbox)
            
            # 原文件名
            original_name = result.get('original_name', '')
            original_item = QTableWidgetItem(original_name)
            original_item.setToolTip(original_name)
            self.preview_table.setItem(row, 1, original_item)
            
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
            self.preview_table.setItem(row, 2, recognition_item)
            
            # 新文件名
            new_name = result.get('new_name', '')
            new_item = QTableWidgetItem(new_name)
            new_item.setToolTip(new_name)
            self.preview_table.setItem(row, 3, new_item)
            
            # 文件类型
            file_type = result.get('type', '未知')
            type_item = QTableWidgetItem(file_type)
            type_item.setToolTip(file_type)
            self.preview_table.setItem(row, 4, type_item)
            
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
                
            self.preview_table.setItem(row, 5, status_item)
            
            # 详情按钮
            detail_btn = QPushButton("👁️")
            detail_btn.setToolTip("查看详细信息")
            detail_btn.setFixedSize(30, 25)
            detail_btn.setStyleSheet("QPushButton { background-color: #17a2b8; border: none; color: white; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
            detail_btn.clicked.connect(lambda checked, r=row: self.show_detail_dialog(r))
            self.preview_table.setCellWidget(row, 6, detail_btn)
        
        # 更新统计信息
        self.update_stats()
        
    def update_stats(self) -> None:
        """更新统计信息"""
        total_count = len(self.results)
        filtered_count = len(self.filtered_results)
        
        # 统计文件类型
        type_counts = {}
        status_counts = {}
        recognized_count = 0
        
        for result in self.results:
            file_type = result.get('type', '未知')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            status = result.get('status', '待处理')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if result.get('title'):
                recognized_count += 1
        
        # 生成统计文本
        stats_text = f"""
📊 统计信息

📁 文件总数: {total_count}
🔍 筛选结果: {filtered_count}
✅ 已识别: {recognized_count}
❌ 未识别: {total_count - recognized_count}

📂 文件类型分布:
"""
        
        for file_type, count in type_counts.items():
            percentage = (count / total_count) * 100
            stats_text += f"• {file_type}: {count} ({percentage:.1f}%)\n"
            
        stats_text += "\n📈 状态分布:\n"
        for status, count in status_counts.items():
            percentage = (count / total_count) * 100
            stats_text += f"• {status}: {count} ({percentage:.1f}%)\n"
        
        self.stats_text.setPlainText(stats_text)
        
    def show_detail_dialog(self, row: int) -> None:
        """显示详情对话框"""
        if row < len(self.filtered_results):
            result = self.filtered_results[row]
            dialog = DetailDialog(result, self)
            dialog.exec_()
            
    def select_all(self) -> None:
        """全选"""
        for row in range(self.preview_table.rowCount()):
            checkbox = self.preview_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
                
    def deselect_all(self) -> None:
        """取消全选"""
        for row in range(self.preview_table.rowCount()):
            checkbox = self.preview_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
                
    def export_preview(self) -> None:
        """导出预览"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出预览结果",
            "preview_results.csv",
            "CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if not filename:
            return
            
        try:
            if filename.endswith('.csv'):
                self.export_to_csv(filename)
            elif filename.endswith('.json'):
                self.export_to_json(filename)
                
            QMessageBox.information(self, "导出成功", f"预览结果已导出到: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出时发生错误:\n{str(e)}")
            
    def export_to_csv(self, filename: str) -> None:
        """导出为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '原文件名', '标题', '年份', '季数', '集数', 
                '新文件名', '文件类型', '状态', '文件路径'
            ])
            
            # 写入数据
            for result in self.filtered_results:
                writer.writerow([
                    result.get('original_name', ''),
                    result.get('title', ''),
                    result.get('year', ''),
                    result.get('season', ''),
                    result.get('episode', ''),
                    result.get('new_name', ''),
                    result.get('type', ''),
                    result.get('status', ''),
                    result.get('file_path', '')
                ])
                
    def export_to_json(self, filename: str) -> None:
        """导出为JSON格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_results, f, ensure_ascii=False, indent=2)
            
    def on_cell_clicked(self, row: int, column: int) -> None:
        """单元格点击事件"""
        if column == 2:  # 识别结果列
            self.show_detail_dialog(row)
            
    def contextMenuEvent(self, event) -> None:
        """右键菜单事件"""
        menu = QMenu(self)
        
        # 添加菜单项
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self.select_all)
        menu.addAction(select_all_action)
        
        deselect_all_action = QAction("取消全选", self)
        deselect_all_action.triggered.connect(self.deselect_all)
        menu.addAction(deselect_all_action)
        
        menu.addSeparator()
        
        export_action = QAction("导出预览", self)
        export_action.triggered.connect(self.export_preview)
        menu.addAction(export_action)
        
        menu.exec_(event.globalPosition().toPoint())

class DetailDialog(QDialog):
    """详情对话框"""
    
    def __init__(self, result: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.result = result
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置界面"""
        self.setWindowTitle("文件详情")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 基本信息
        info_group = QGroupBox("📋 基本信息")
        info_layout = QFormLayout()
        
        info_text = f"""
        <b>原文件名：</b>{self.result.get('original_name', '')}<br>
        <b>文件路径：</b>{self.result.get('file_path', '')}<br>
        <b>文件大小：</b>{self.result.get('file_size', '')}<br>
        <b>文件类型：</b>{self.result.get('type', '')}<br>
        <b>识别状态：</b>{self.result.get('status', '')}
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addRow(info_label)
        info_group.setLayout(info_layout)
        
        # 识别结果
        result_group = QGroupBox("🎬 识别结果")
        result_layout = QFormLayout()
        
        result_text = f"""
        <b>标题：</b>{self.result.get('title', '未识别')}<br>
        <b>年份：</b>{self.result.get('year', '未识别')}<br>
        <b>季数：</b>{self.result.get('season', '未识别')}<br>
        <b>集数：</b>{self.result.get('episode', '未识别')}<br>
        <b>新文件名：</b>{self.result.get('new_name', '未生成')}
        """
        
        result_label = QLabel(result_text)
        result_label.setWordWrap(True)
        result_layout.addRow(result_label)
        result_group.setLayout(result_layout)
        
        layout.addWidget(info_group)
        layout.addWidget(result_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout) 