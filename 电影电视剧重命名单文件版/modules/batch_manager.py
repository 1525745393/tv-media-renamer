#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量操作管理器 - 影视文件重命名工具 v1.3
增强版批量操作功能
"""

import os
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QGroupBox, QComboBox, QSpinBox, QTextEdit, QMessageBox,
    QProgressDialog, QFileDialog, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont

logger = logging.getLogger(__name__)

class EnhancedBatchManager:
    """增强的批量操作管理器"""
    
    def __init__(self):
        self.operations_history = []
        self.batch_config = {
            "selective_rename": True,
            "batch_move": False,
            "create_backup": True,
            "overwrite_existing": False,
            "preserve_structure": True
        }
    
    def selective_rename(self, files: List[Dict[str, Any]], 
                        selected_indices: List[int]) -> List[Dict[str, Any]]:
        """选择性重命名"""
        try:
            selected_files = [files[i] for i in selected_indices if i < len(files)]
            logger.info(f"选择性重命名 {len(selected_files)} 个文件")
            
            # 记录操作
            operation = {
                "type": "selective_rename",
                "timestamp": datetime.now(),
                "files_count": len(selected_files),
                "selected_indices": selected_indices
            }
            self.operations_history.append(operation)
            
            return selected_files
            
        except Exception as e:
            logger.error(f"选择性重命名失败: {e}")
            raise
    
    def batch_move_files(self, files: List[Dict[str, Any]], 
                        target_folder: str, 
                        organize_by_type: bool = True) -> Dict[str, Any]:
        """批量移动文件"""
        try:
            logger.info(f"批量移动 {len(files)} 个文件到 {target_folder}")
            
            # 创建目标文件夹
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            
            # 按类型组织文件
            if organize_by_type:
                return self._organize_and_move(files, target_folder)
            else:
                return self._simple_move(files, target_folder)
                
        except Exception as e:
            logger.error(f"批量移动失败: {e}")
            raise
    
    def _organize_and_move(self, files: List[Dict[str, Any]], 
                          target_folder: str) -> Dict[str, Any]:
        """按类型组织并移动文件"""
        results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "moved_files": []
        }
        
        # 按文件类型分组
        type_groups = {}
        for file_info in files:
            file_type = file_info.get('type', 'unknown')
            if file_type not in type_groups:
                type_groups[file_type] = []
            type_groups[file_type].append(file_info)
        
        # 为每种类型创建子文件夹
        for file_type, type_files in type_groups.items():
            type_folder = os.path.join(target_folder, file_type)
            if not os.path.exists(type_folder):
                os.makedirs(type_folder)
            
            # 移动该类型的文件
            for file_info in type_files:
                try:
                    source_path = file_info.get('file_path', '')
                    if os.path.exists(source_path):
                        filename = os.path.basename(source_path)
                        target_path = os.path.join(type_folder, filename)
                        
                        # 检查目标文件是否存在
                        if os.path.exists(target_path) and not self.batch_config["overwrite_existing"]:
                            # 生成唯一文件名
                            base_name, ext = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(target_path):
                                new_filename = f"{base_name}_{counter}{ext}"
                                target_path = os.path.join(type_folder, new_filename)
                                counter += 1
                        
                        # 移动文件
                        shutil.move(source_path, target_path)
                        file_info['new_path'] = target_path
                        results["moved_files"].append(file_info)
                        results["success"] += 1
                        
                except Exception as e:
                    error_msg = f"移动文件失败 {source_path}: {str(e)}"
                    results["errors"].append(error_msg)
                    results["failed"] += 1
                    logger.error(error_msg)
        
        return results
    
    def _simple_move(self, files: List[Dict[str, Any]], 
                    target_folder: str) -> Dict[str, Any]:
        """简单移动文件"""
        results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "moved_files": []
        }
        
        for file_info in files:
            try:
                source_path = file_info.get('file_path', '')
                if os.path.exists(source_path):
                    filename = os.path.basename(source_path)
                    target_path = os.path.join(target_folder, filename)
                    
                    # 检查目标文件是否存在
                    if os.path.exists(target_path) and not self.batch_config["overwrite_existing"]:
                        base_name, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(target_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            target_path = os.path.join(target_folder, new_filename)
                            counter += 1
                    
                    # 移动文件
                    shutil.move(source_path, target_path)
                    file_info['new_path'] = target_path
                    results["moved_files"].append(file_info)
                    results["success"] += 1
                    
            except Exception as e:
                error_msg = f"移动文件失败 {source_path}: {str(e)}"
                results["errors"].append(error_msg)
                results["failed"] += 1
                logger.error(error_msg)
        
        return results
    
    def create_backup(self, files: List[Dict[str, Any]], 
                     backup_folder: str) -> bool:
        """创建备份"""
        try:
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            
            backup_count = 0
            for file_info in files:
                source_path = file_info.get('file_path', '')
                if os.path.exists(source_path):
                    filename = os.path.basename(source_path)
                    backup_path = os.path.join(backup_folder, filename)
                    
                    # 如果备份文件已存在，添加时间戳
                    if os.path.exists(backup_path):
                        base_name, ext = os.path.splitext(filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_path = os.path.join(backup_folder, f"{base_name}_{timestamp}{ext}")
                    
                    shutil.copy2(source_path, backup_path)
                    backup_count += 1
            
            logger.info(f"创建备份完成，共备份 {backup_count} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.operations_history
    
    def clear_history(self) -> None:
        """清除操作历史"""
        self.operations_history.clear()
        logger.info("操作历史已清除")


class BatchOperationDialog(QDialog):
    """批量操作对话框"""
    
    def __init__(self, files: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.files = files
        self.batch_manager = EnhancedBatchManager()
        self.selected_files = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("批量操作管理器")
        self.setFixedSize(800, 600)
        self.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("🔄 批量操作管理器")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # 操作类型选择
        operation_group = QGroupBox("📋 操作类型")
        operation_layout = QHBoxLayout()
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["选择性重命名", "批量移动", "创建备份"])
        self.operation_combo.currentTextChanged.connect(self.on_operation_changed)
        
        operation_layout.addWidget(QLabel("选择操作:"))
        operation_layout.addWidget(self.operation_combo)
        operation_layout.addStretch()
        
        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)
        
        # 文件选择表格
        files_group = QGroupBox(f"📁 文件列表 ({len(self.files)} 个文件)")
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["选择", "原文件名", "文件类型", "状态"])
        
        # 设置表格属性
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.files_table.setColumnWidth(0, 60)
        
        # 填充文件列表
        self.populate_files_table()
        
        files_layout.addWidget(self.files_table)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        # 操作选项
        options_group = QGroupBox("⚙️ 操作选项")
        options_layout = QFormLayout()
        
        self.create_backup_cb = QCheckBox("创建备份")
        self.create_backup_cb.setChecked(True)
        
        self.overwrite_existing_cb = QCheckBox("覆盖现有文件")
        self.overwrite_existing_cb.setChecked(False)
        
        self.organize_by_type_cb = QCheckBox("按类型组织")
        self.organize_by_type_cb.setChecked(True)
        
        options_layout.addRow("备份选项:", self.create_backup_cb)
        options_layout.addRow("覆盖选项:", self.overwrite_existing_cb)
        options_layout.addRow("组织选项:", self.organize_by_type_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_files)
        
        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all_files)
        
        self.execute_btn = QPushButton("执行操作")
        self.execute_btn.clicked.connect(self.execute_operation)
        self.execute_btn.setStyleSheet("""
            QPushButton { 
                background-color: #28a745; 
                border: none; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 4px; 
                font-weight: bold;
            } 
            QPushButton:hover { 
                background-color: #218838; 
            }
        """)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.execute_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def populate_files_table(self):
        """填充文件表格"""
        self.files_table.setRowCount(len(self.files))
        
        for row, file_info in enumerate(self.files):
            # 选择复选框
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # 默认全选
            self.files_table.setCellWidget(row, 0, checkbox)
            
            # 原文件名
            original_name = file_info.get('original_name', '')
            name_item = QTableWidgetItem(original_name)
            name_item.setToolTip(original_name)
            self.files_table.setItem(row, 1, name_item)
            
            # 文件类型
            file_type = file_info.get('type', '未知')
            type_item = QTableWidgetItem(file_type)
            self.files_table.setItem(row, 2, type_item)
            
            # 状态
            status = file_info.get('status', '待处理')
            status_item = QTableWidgetItem(status)
            
            # 根据状态设置颜色
            if status == '成功':
                status_item.setBackground(QColor('#d4edda'))
                status_item.setForeground(QColor('#155724'))
            elif status == '失败':
                status_item.setBackground(QColor('#f8d7da'))
                status_item.setForeground(QColor('#721c24'))
            else:
                status_item.setBackground(QColor('#e2e3e5'))
                status_item.setForeground(QColor('#383d41'))
            
            self.files_table.setItem(row, 3, status_item)
    
    def on_operation_changed(self, operation: str):
        """操作类型改变"""
        # 根据操作类型启用/禁用相关选项
        if operation == "批量移动":
            self.organize_by_type_cb.setEnabled(True)
        else:
            self.organize_by_type_cb.setEnabled(False)
    
    def select_all_files(self):
        """全选文件"""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_files(self):
        """取消全选"""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def get_selected_files(self) -> List[Dict[str, Any]]:
        """获取选中的文件"""
        selected_files = []
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_files.append(self.files[row])
        return selected_files
    
    def execute_operation(self):
        """执行操作"""
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "警告", "请至少选择一个文件")
            return
        
        operation = self.operation_combo.currentText()
        
        try:
            if operation == "选择性重命名":
                self.execute_selective_rename(selected_files)
            elif operation == "批量移动":
                self.execute_batch_move(selected_files)
            elif operation == "创建备份":
                self.execute_create_backup(selected_files)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行操作失败: {str(e)}")
    
    def execute_selective_rename(self, selected_files: List[Dict[str, Any]]):
        """执行选择性重命名"""
        # 这里可以调用重命名功能
        QMessageBox.information(self, "提示", f"已选择 {len(selected_files)} 个文件进行重命名")
        self.accept()
    
    def execute_batch_move(self, selected_files: List[Dict[str, Any]]):
        """执行批量移动"""
        target_folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if not target_folder:
            return
        
        # 更新批量管理器配置
        self.batch_manager.batch_config["overwrite_existing"] = self.overwrite_existing_cb.isChecked()
        
        # 执行批量移动
        organize_by_type = self.organize_by_type_cb.isChecked()
        results = self.batch_manager.batch_move_files(selected_files, target_folder, organize_by_type)
        
        # 显示结果
        result_text = f"批量移动完成:\n"
        result_text += f"成功: {results['success']} 个文件\n"
        result_text += f"失败: {results['failed']} 个文件\n"
        
        if results['errors']:
            result_text += f"\n错误详情:\n"
            for error in results['errors'][:5]:  # 只显示前5个错误
                result_text += f"• {error}\n"
            if len(results['errors']) > 5:
                result_text += f"... 还有 {len(results['errors']) - 5} 个错误"
        
        QMessageBox.information(self, "批量移动完成", result_text)
        self.accept()
    
    def execute_create_backup(self, selected_files: List[Dict[str, Any]]):
        """执行创建备份"""
        backup_folder = QFileDialog.getExistingDirectory(self, "选择备份文件夹")
        if not backup_folder:
            return
        
        # 创建备份
        success = self.batch_manager.create_backup(selected_files, backup_folder)
        
        if success:
            QMessageBox.information(self, "备份完成", f"已成功备份 {len(selected_files)} 个文件到 {backup_folder}")
        else:
            QMessageBox.warning(self, "备份失败", "创建备份时发生错误")
        
        self.accept() 