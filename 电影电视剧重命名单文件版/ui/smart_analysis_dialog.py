#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析对话框 - 影视文件重命名工具 v1.4
"""

import os
import logging
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel, QProgressBar,
    QTextEdit, QGroupBox, QComboBox, QCheckBox, QSpinBox, QMessageBox,
    QSplitter, QFrame, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

from modules.enhanced_analyzer import EnhancedAnalyzer
from modules.file_classifier import FileClassifier, ClassificationResult
from modules.batch_manager import EnhancedBatchManager

logger = logging.getLogger(__name__)


class SmartAnalysisWorker(QThread):
    """智能分析工作线程"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(list)
    classification_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    
    def __init__(self, file_paths: List[str], settings: Dict[str, Any]):
        super().__init__()
        self.file_paths = file_paths
        self.settings = settings
        self.enhanced_analyzer = EnhancedAnalyzer(settings)
        self.file_classifier = FileClassifier(settings)
        self._cancelled = False
        
    def cancel(self) -> None:
        """取消分析"""
        self._cancelled = True
        
    def run(self) -> None:
        """执行分析"""
        try:
            # 增强文件分析
            self.current_file_changed.emit("开始增强文件分析...")
            file_infos = []
            
            for i, file_path in enumerate(self.file_paths):
                if self._cancelled:
                    return
                
                # 更新进度
                progress = int((i + 1) / len(self.file_paths) * 50)  # 分析占50%
                self.progress_updated.emit(progress)
                self.current_file_changed.emit(os.path.basename(file_path))
                
                try:
                    filename = os.path.basename(file_path)
                    folder_path = os.path.dirname(file_path)
                    file_info = self.enhanced_analyzer.analyze_file(filename, folder_path)
                    if file_info:
                        file_infos.append(file_info)
                except Exception as e:
                    logger.error(f"分析文件失败 {file_path}: {e}")
            
            if self._cancelled:
                return
            
            self.analysis_completed.emit(file_infos)
            
            # 文件分类
            self.current_file_changed.emit("开始文件分类...")
            classification_results = []
            
            for i, file_info in enumerate(file_infos):
                if self._cancelled:
                    return
                
                # 更新进度
                progress = 50 + int((i + 1) / len(file_infos) * 50)  # 分类占50%
                self.progress_updated.emit(progress)
                
                # 确保file_info是字典格式
                if isinstance(file_info, dict):
                    file_path = file_info.get('file_path', '')
                else:
                    # 如果file_info不是字典，尝试转换为字符串
                    file_path = str(file_info) if file_info else ''
                
                if file_path:
                    self.current_file_changed.emit(os.path.basename(file_path))
                    
                    try:
                        classification_result = self.file_classifier.classify_file(file_path)
                        classification_results.append(classification_result)
                    except Exception as e:
                        logger.error(f"分类文件失败 {file_path}: {e}")
                else:
                    logger.warning(f"跳过无效的文件信息: {file_info}")
            
            if not self._cancelled:
                self.classification_completed.emit(classification_results)
                
        except Exception as e:
            logger.error(f"智能分析失败: {e}")
            self.error_occurred.emit(f"智能分析失败: {str(e)}")


class SmartAnalysisDialog(QDialog):
    """智能分析对话框"""
    
    def __init__(self, file_paths: List[str], settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.settings = settings
        self.file_infos: List[Dict[str, Any]] = []
        self.classification_results: List[ClassificationResult] = []
        self.batch_manager = EnhancedBatchManager()
        self.enhanced_analyzer = EnhancedAnalyzer(settings)
        self.file_classifier = FileClassifier(settings)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self) -> None:
        """设置界面"""
        self.setWindowTitle("智能分析 - 影视文件重命名工具 v1.4")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("🔍 智能文件分析")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 分析结果标签页
        self.setup_analysis_tab()
        
        # 分类结果标签页
        self.setup_classification_tab()
        
        # 批量操作标签页
        self.setup_batch_tab()
        
        # 统计报告标签页
        self.setup_stats_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.btn_start_analysis = QPushButton("🚀 开始智能分析")
        self.btn_start_analysis.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27ae60, stop:1 #229954);
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #229954, stop:1 #1e8449);
            }
        """)
        
        self.btn_export_results = QPushButton("📤 导出结果")
        self.btn_export_results.setEnabled(False)
        self.btn_export_results.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9);
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #1f5f8b);
            }
        """)
        
        self.btn_close = QPushButton("关闭")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        control_layout.addWidget(self.btn_start_analysis)
        control_layout.addWidget(self.btn_export_results)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_close)
        
        main_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9);
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
    def setup_analysis_tab(self) -> None:
        """设置分析结果标签页"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()
        
        # 分析结果表格
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(8)
        self.analysis_table.setHorizontalHeaderLabels([
            "文件名", "类型", "标题", "年份", "质量", "编码", "置信度", "建议"
        ])
        
        # 设置表格样式
        self.analysis_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #bdc3c7;
                font-weight: bold;
            }
        """)
        
        # 设置列宽
        header = self.analysis_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_widget.setLayout(analysis_layout)
        
        self.tab_widget.addTab(analysis_widget, "📊 分析结果")
        
    def setup_classification_tab(self) -> None:
        """设置分类结果标签页"""
        classification_widget = QWidget()
        classification_layout = QVBoxLayout()
        
        # 分类结果表格
        self.classification_table = QTableWidget()
        self.classification_table.setColumnCount(7)
        self.classification_table.setHorizontalHeaderLabels([
            "文件名", "主分类", "次分类", "标签", "置信度", "建议组织", "操作"
        ])
        
        # 设置表格样式
        self.classification_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #bdc3c7;
                font-weight: bold;
            }
        """)
        
        # 设置列宽
        header = self.classification_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.Stretch)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        classification_layout.addWidget(self.classification_table)
        classification_widget.setLayout(classification_layout)
        
        self.tab_widget.addTab(classification_widget, "🏷️ 分类结果")
        
    def setup_batch_tab(self) -> None:
        """设置批量操作标签页"""
        batch_widget = QWidget()
        batch_layout = QVBoxLayout()
        
        # 批量操作控制
        control_group = QGroupBox("批量操作控制")
        control_layout = QHBoxLayout()
        
        self.btn_add_rename_ops = QPushButton("添加重命名操作")
        self.btn_add_move_ops = QPushButton("添加移动操作")
        self.btn_clear_ops = QPushButton("清空操作")
        self.btn_start_batch = QPushButton("开始批量处理")
        self.btn_pause_batch = QPushButton("暂停")
        self.btn_resume_batch = QPushButton("恢复")
        
        control_layout.addWidget(self.btn_add_rename_ops)
        control_layout.addWidget(self.btn_add_move_ops)
        control_layout.addWidget(self.btn_clear_ops)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start_batch)
        control_layout.addWidget(self.btn_pause_batch)
        control_layout.addWidget(self.btn_resume_batch)
        
        control_group.setLayout(control_layout)
        batch_layout.addWidget(control_group)
        
        # 批量操作表格
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(6)
        self.batch_table.setHorizontalHeaderLabels([
            "操作ID", "类型", "源路径", "目标路径", "状态", "错误信息"
        ])
        
        # 设置表格样式
        self.batch_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #bdc3c7;
                font-weight: bold;
            }
        """)
        
        # 设置列宽
        header = self.batch_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 操作ID
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 类型
            header.setSectionResizeMode(2, QHeaderView.Stretch)           # 源路径
            header.setSectionResizeMode(3, QHeaderView.Stretch)           # 目标路径
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 状态
            header.setSectionResizeMode(5, QHeaderView.Stretch)           # 错误信息
        
        batch_layout.addWidget(self.batch_table)
        batch_widget.setLayout(batch_layout)
        
        self.tab_widget.addTab(batch_widget, "⚙️ 批量操作")
        
    def setup_stats_tab(self) -> None:
        """设置统计报告标签页"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        
        # 统计信息显示
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        
        stats_layout.addWidget(self.stats_text)
        stats_widget.setLayout(stats_layout)
        
        self.tab_widget.addTab(stats_widget, "📈 统计报告")
        
    def setup_connections(self) -> None:
        """设置信号连接"""
        self.btn_start_analysis.clicked.connect(self.start_analysis)
        self.btn_export_results.clicked.connect(self.export_results)
        self.btn_close.clicked.connect(self.close)
        
        # 批量操作按钮
        self.btn_add_rename_ops.clicked.connect(lambda: self.add_rename_operations())
        self.btn_add_move_ops.clicked.connect(lambda: self.add_move_operations())
        self.btn_clear_ops.clicked.connect(lambda: self.clear_batch_operations())
        self.btn_start_batch.clicked.connect(lambda: self.start_batch_processing())
        self.btn_pause_batch.clicked.connect(lambda: self.pause_batch_processing())
        self.btn_resume_batch.clicked.connect(lambda: self.resume_batch_processing())
        
    def start_analysis(self) -> None:
        """开始智能分析"""
        if not self.file_paths:
            QMessageBox.warning(self, "警告", "没有文件需要分析")
            return
        
        # 禁用按钮
        self.btn_start_analysis.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建并启动分析线程
        self.analysis_worker = SmartAnalysisWorker(self.file_paths, self.settings)
        self.analysis_worker.progress_updated.connect(self.update_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.classification_completed.connect(self.on_classification_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.current_file_changed.connect(self.update_status)
        self.analysis_worker.start()
        
    def update_progress(self, value: int) -> None:
        """更新进度"""
        self.progress_bar.setValue(value)
        
    def update_status(self, message: str) -> None:
        """更新状态"""
        self.status_label.setText(message)
        
    def on_analysis_completed(self, file_infos: List[Dict[str, Any]]) -> None:
        """分析完成处理"""
        self.file_infos = file_infos
        self.update_analysis_table()
        self.status_label.setText(f"文件分析完成，共分析 {len(file_infos)} 个文件")
        
    def on_classification_completed(self, classification_results: List[ClassificationResult]) -> None:
        """分类完成处理"""
        self.classification_results = classification_results
        self.update_classification_table()
        self.update_stats_tab()
        
        # 恢复按钮状态
        self.btn_start_analysis.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.btn_export_results.setEnabled(True)
        
        self.status_label.setText(f"智能分析完成，共处理 {len(classification_results)} 个文件")
        
    def on_analysis_error(self, error_msg: str) -> None:
        """分析错误处理"""
        self.btn_start_analysis.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "分析错误", f"智能分析过程中发生错误：\n{error_msg}")
        
    def update_analysis_table(self) -> None:
        """更新分析结果表格"""
        self.analysis_table.setRowCount(len(self.file_infos))
        
        for i, file_info in enumerate(self.file_infos):
            # 确保file_info是字典格式
            if not isinstance(file_info, dict):
                logger.warning(f"跳过无效的文件信息: {file_info}")
                continue
            
            # 文件名
            self.analysis_table.setItem(i, 0, QTableWidgetItem(file_info.get('filename', '未知')))
            
            # 类型
            type_item = QTableWidgetItem(file_info.get('file_type', '未知'))
            if file_info.get('file_type') == 'movie':
                type_item.setBackground(QColor('#e8f5e8'))
            elif file_info.get('file_type') == 'tv':
                type_item.setBackground(QColor('#e8f0f8'))
            self.analysis_table.setItem(i, 1, type_item)
            
            # 标题
            self.analysis_table.setItem(i, 2, QTableWidgetItem(file_info.get('title', '')))
            
            # 年份
            self.analysis_table.setItem(i, 3, QTableWidgetItem(file_info.get('year', '')))
            
            # 质量
            self.analysis_table.setItem(i, 4, QTableWidgetItem(file_info.get('quality', '')))
            
            # 编码
            codec = file_info.get('video_codec', '') or file_info.get('audio_codec', '')
            self.analysis_table.setItem(i, 5, QTableWidgetItem(codec))
            
            # 置信度
            confidence = file_info.get('confidence', 0.0)
            confidence_item = QTableWidgetItem(f"{confidence:.2f}")
            if confidence > 0.8:
                confidence_item.setBackground(QColor('#d4edda'))
            elif confidence > 0.5:
                confidence_item.setBackground(QColor('#fff3cd'))
            else:
                confidence_item.setBackground(QColor('#f8d7da'))
            self.analysis_table.setItem(i, 6, confidence_item)
            
            # 建议
            suggestions = []
            if confidence < 0.5:
                suggestions.append("置信度较低，建议手动检查")
            if not file_info.get('title'):
                suggestions.append("缺少标题信息")
            if not file_info.get('year'):
                suggestions.append("缺少年份信息")
            
            suggestion_text = "; ".join(suggestions) if suggestions else "无"
            self.analysis_table.setItem(i, 7, QTableWidgetItem(suggestion_text))
            
    def update_classification_table(self) -> None:
        """更新分类结果表格"""
        self.classification_table.setRowCount(len(self.classification_results))
        
        for i, result in enumerate(self.classification_results):
            # 文件名
            self.classification_table.setItem(i, 0, QTableWidgetItem(os.path.basename(result.file_path)))
            
            # 主分类
            primary_item = QTableWidgetItem(result.primary_category)
            if result.primary_category != '未知':
                primary_item.setBackground(QColor('#d4edda'))
            self.classification_table.setItem(i, 1, primary_item)
            
            # 次分类
            self.classification_table.setItem(i, 2, QTableWidgetItem(result.secondary_category))
            
            # 标签
            tags_text = ", ".join(result.tags) if result.tags else "无"
            self.classification_table.setItem(i, 3, QTableWidgetItem(tags_text))
            
            # 置信度
            confidence_item = QTableWidgetItem(f"{result.confidence:.2f}")
            if result.confidence > 0.8:
                confidence_item.setBackground(QColor('#d4edda'))
            elif result.confidence > 0.5:
                confidence_item.setBackground(QColor('#fff3cd'))
            else:
                confidence_item.setBackground(QColor('#f8d7da'))
            self.classification_table.setItem(i, 4, confidence_item)
            
            # 建议组织
            # 这里可以根据分类结果生成组织建议
            organization_suggestion = f"{result.primary_category}"
            if result.tags:
                year_tags = [tag for tag in result.tags if tag.startswith('年份:')]
                quality_tags = [tag for tag in result.tags if tag in ['4K', '1080p', '720p', '480p']]
                if year_tags:
                    organization_suggestion += f"/{year_tags[0].split(':')[1]}"
                if quality_tags:
                    organization_suggestion += f"/{quality_tags[0]}"
            
            self.classification_table.setItem(i, 5, QTableWidgetItem(organization_suggestion))
            
            # 操作按钮
            action_btn = QPushButton("查看详情")
            action_btn.clicked.connect(lambda checked, row=i: self.show_file_details(row))
            self.classification_table.setCellWidget(i, 6, action_btn)
            
    def show_file_details(self, row: int) -> None:
        """显示文件详情"""
        if row < len(self.classification_results):
            result = self.classification_results[row]
            details = f"""
文件路径: {result.file_path}
主分类: {result.primary_category}
次分类: {result.secondary_category}
置信度: {result.confidence:.2f}
标签: {', '.join(result.tags) if result.tags else '无'}

元数据:
"""
            for key, value in result.metadata.items():
                details += f"  {key}: {value}\n"
            
            QMessageBox.information(self, "文件详情", details)
            
    def update_stats_tab(self) -> None:
        """更新统计报告标签页"""
        if not self.file_infos or not self.classification_results:
            return
        
        # 获取分析摘要
        analysis_summary = self.enhanced_analyzer.get_analysis_summary(self.file_infos)
        
        # 获取分类摘要
        classification_summary = self.file_classifier.get_classification_summary(self.classification_results)
        
        # 生成统计报告
        stats_text = f"""
📊 智能分析统计报告
{'='*50}

📁 文件分析统计:
  总文件数: {analysis_summary['total_files']}
  文件类型分布:
"""
        
        for file_type, count in analysis_summary['file_types'].items():
            stats_text += f"    {file_type}: {count} 个文件\n"
        
        stats_text += f"""
  媒体类型分布:
"""
        for media_type, count in analysis_summary['media_types'].items():
            stats_text += f"    {media_type}: {count} 个文件\n"
        
        stats_text += f"""
  年份分布:
"""
        for year, count in analysis_summary['years'].items():
            stats_text += f"    {year}: {count} 个文件\n"
        
        stats_text += f"""
🏷️ 分类统计:
  主分类分布:
"""
        for category, count in classification_summary['primary_categories'].items():
            stats_text += f"    {category}: {count} 个文件\n"
        
        stats_text += f"""
  次分类分布:
"""
        for category, count in classification_summary['secondary_categories'].items():
            stats_text += f"    {category}: {count} 个文件\n"
        
        stats_text += f"""
  置信度统计:
    高置信度 (>0.8): {classification_summary['confidence_stats']['high']} 个文件
    中置信度 (0.5-0.8): {classification_summary['confidence_stats']['medium']} 个文件
    低置信度 (<0.5): {classification_summary['confidence_stats']['low']} 个文件
    平均置信度: {classification_summary['average_confidence']:.2f}
"""
        
        self.stats_text.setText(stats_text)
        
    def add_rename_operations(self) -> None:
        """添加重命名操作"""
        if not self.file_infos:
            QMessageBox.warning(self, "警告", "请先进行文件分析")
            return
        
        # 这里可以根据分析结果生成重命名操作
        # 示例：为每个文件生成标准化的新文件名
        valid_files = []
        for i, file_info in enumerate(self.file_infos):
            # 确保file_info是字典格式
            if not isinstance(file_info, dict):
                logger.warning(f"跳过无效的文件信息: {file_info}")
                continue
                
            if file_info.get('title') and file_info.get('confidence', 0) > 0.5:
                # 生成新文件名
                new_name = self.generate_standard_filename(file_info)
                if new_name != file_info.get('filename'):
                    valid_files.append(file_info)
                    # 使用selective_rename方法
                    self.batch_manager.selective_rename([file_info], [len(valid_files) - 1])
        
        self.update_batch_table()
        QMessageBox.information(self, "成功", f"已添加 {len(valid_files)} 个重命名操作")
        
    def add_move_operations(self) -> None:
        """添加移动操作"""
        if not self.file_infos:
            QMessageBox.warning(self, "警告", "请先进行文件分析")
            return
        
        # 按类型组织文件
        organization = {}
        for file_info in self.file_infos:
            # 确保file_info是字典格式
            if not isinstance(file_info, dict):
                logger.warning(f"跳过无效的文件信息: {file_info}")
                continue
                
            file_type = file_info.get('file_type', 'unknown')
            if file_type not in organization:
                organization[file_type] = []
            organization[file_type].append(file_info)
        
        # 为每种类型创建移动操作
        for file_type, files in organization.items():
            if files:
                # 使用batch_move_files方法
                self.batch_manager.batch_move_files(files, f"organized/{file_type}")
        
        QMessageBox.information(self, "成功", f"已添加移动操作，建议组织到 {len(organization)} 个目录")
        
    def generate_standard_filename(self, file_info: Dict[str, Any]) -> str:
        """生成标准文件名"""
        try:
            # 获取文件扩展名
            filename = file_info.get('filename', 'unknown')
            _, ext = os.path.splitext(filename)
            
            # 构建新文件名
            parts = []
            
            if file_info.get('title'):
                parts.append(file_info['title'])
            
            if file_info.get('year'):
                parts.append(f"({file_info['year']})")
            
            if file_info.get('file_type') == 'tv' and file_info.get('season') and file_info.get('episode'):
                parts.append(f"S{file_info['season']:02d}E{file_info['episode']:02d}")
            elif file_info.get('file_type') == 'tv' and file_info.get('season'):
                parts.append(f"S{file_info['season']:02d}")
            
            if file_info.get('quality'):
                parts.append(file_info['quality'])
            
            codec = file_info.get('video_codec', '') or file_info.get('audio_codec', '')
            if codec:
                parts.append(codec)
            
            new_name = ".".join(parts) + ext
            return new_name
            
        except Exception as e:
            logger.error(f"生成标准文件名失败: {e}")
            return file_info.get('filename', 'unknown')
        
    def clear_batch_operations(self) -> None:
        """清除批量操作"""
        self.batch_manager.clear_history()
        self.update_batch_table()
        
    def start_batch_processing(self) -> None:
        """开始批量处理"""
        try:
            operations = self.batch_manager.get_operation_history()
            if not operations:
                QMessageBox.warning(self, "警告", "没有可执行的批量操作")
                return
            
            # 这里可以添加实际的批量处理逻辑
            QMessageBox.information(self, "成功", f"开始执行 {len(operations)} 个批量操作")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量处理失败: {str(e)}")
            
    def pause_batch_processing(self) -> None:
        """暂停批量处理"""
        self.status_label.setText("批量处理已暂停")
        
    def resume_batch_processing(self) -> None:
        """恢复批量处理"""
        self.status_label.setText("批量处理已恢复")
        
    def on_batch_status_changed(self, operation: Any) -> None:
        """批量操作状态改变"""
        self.update_batch_table()
        
    def on_batch_completed(self) -> None:
        """批量处理完成"""
        self.status_label.setText("批量处理完成")
        QMessageBox.information(self, "完成", "批量处理已完成")
        
    def update_batch_table(self) -> None:
        """更新批量操作表格"""
        operations = self.batch_manager.get_operation_history()
        self.batch_table.setRowCount(len(operations))
        
        for i, operation in enumerate(operations):
            # 操作ID
            self.batch_table.setItem(i, 0, QTableWidgetItem(operation.get('id', f'op_{i}')))
            
            # 类型
            type_item = QTableWidgetItem(operation.get('type', 'unknown'))
            if operation.get('type') == 'selective_rename':
                type_item.setBackground(QColor('#e8f5e8'))
            elif operation.get('type') == 'batch_move':
                type_item.setBackground(QColor('#e8f0f8'))
            self.batch_table.setItem(i, 1, type_item)
            
            # 源路径
            self.batch_table.setItem(i, 2, QTableWidgetItem(operation.get('source_path', '')))
            
            # 目标路径
            self.batch_table.setItem(i, 3, QTableWidgetItem(operation.get('target_path', '')))
            
            # 状态
            status_item = QTableWidgetItem(operation.get('status', 'pending'))
            if operation.get('status') == 'completed':
                status_item.setBackground(QColor('#d4edda'))
            elif operation.get('status') == 'failed':
                status_item.setBackground(QColor('#f8d7da'))
            elif operation.get('status') == 'processing':
                status_item.setBackground(QColor('#fff3cd'))
            self.batch_table.setItem(i, 4, status_item)
            
            # 错误信息
            error_text = operation.get('error_message', '')
            self.batch_table.setItem(i, 5, QTableWidgetItem(error_text))
            
    def export_results(self) -> None:
        """导出分析结果"""
        try:
            import json
            from datetime import datetime
            
            # 准备导出数据
            export_data = {
                'export_time': datetime.now().isoformat(),
                'file_count': len(self.file_paths),
                'file_infos': [],
                'classification_results': [],
                'batch_operations': []
            }
            
            # 导出文件信息
            for file_info in self.file_infos:
                file_info_dict = {
                    'filename': file_info.get('filename', ''),
                    'file_path': file_info.get('file_path', ''),
                    'file_size': file_info.get('file_size', 0),
                    'file_type': file_info.get('file_type', ''),
                    'title': file_info.get('title', ''),
                    'year': file_info.get('year', ''),
                    'season': file_info.get('season'),
                    'episode': file_info.get('episode'),
                    'quality': file_info.get('quality', ''),
                    'languages': file_info.get('languages', []),
                    'video_codec': file_info.get('video_codec', ''),
                    'audio_codec': file_info.get('audio_codec', ''),
                    'confidence': file_info.get('confidence', 0.0),
                    'metadata': file_info.get('metadata', {})
                }
                export_data['file_infos'].append(file_info_dict)
            
            # 导出分类结果
            for result in self.classification_results:
                result_dict = {
                    'file_path': result.file_path,
                    'primary_category': result.primary_category,
                    'secondary_category': result.secondary_category,
                    'confidence': result.confidence,
                    'tags': result.tags,
                    'metadata': result.metadata
                }
                export_data['classification_results'].append(result_dict)
            
            # 导出批量操作
            operations = self.batch_manager.get_operation_history()
            for operation in operations:
                operation_dict = {
                    'operation_id': operation.get('id', ''),
                    'operation_type': operation.get('type', ''),
                    'source_path': operation.get('source_path', ''),
                    'target_path': operation.get('target_path', ''),
                    'status': operation.get('status', ''),
                    'error_message': operation.get('error_message', ''),
                    'timestamp': operation.get('timestamp', '')
                }
                export_data['batch_operations'].append(operation_dict)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"smart_analysis_results_{timestamp}.json"
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "导出成功", f"分析结果已导出到: {export_file}")
            
        except Exception as e:
            logger.error(f"导出结果失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出结果失败: {str(e)}") 