#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框模块 - 影视文件重命名工具 v1.3
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit, QSpinBox, QCheckBox, QComboBox, QPushButton, QTabWidget, QWidget, QTextEdit, QScrollArea, QFileDialog, QDialogButtonBox, QLabel
from PyQt5.QtCore import Qt
from typing import Dict, Any
import os


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, settings: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.settings = settings.copy()
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(800, 600)  # 增加对话框大小
        
        layout = QVBoxLayout()
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 文件类型选项卡
        file_types_tab = self._create_file_types_tab()
        self.tab_widget.addTab(file_types_tab, "文件类型")
        
        # 模板选项卡
        templates_tab = self._create_templates_tab()
        self.tab_widget.addTab(templates_tab, "命名模板")
        
        # 安全选项卡
        security_tab = self._create_security_tab()
        self.tab_widget.addTab(security_tab, "安全设置")
        
        # 性能选项卡
        performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(performance_tab, "性能设置")
        
        # 日志选项卡
        logging_tab = self._create_logging_tab()
        self.tab_widget.addTab(logging_tab, "日志设置")
        
        # 缓存选项卡
        cache_tab = self._create_cache_tab()
        self.tab_widget.addTab(cache_tab, "缓存设置")
        
        # 高级选项卡
        advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, "高级设置")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _create_file_types_tab(self):
        """创建文件类型选项卡"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        
        # 视频文件扩展名
        video_group = QGroupBox("视频文件扩展名")
        video_layout = QVBoxLayout()
        
        self.video_exts_edit = QLineEdit()
        self.video_exts_edit.setPlaceholderText("用逗号分隔，如: .mp4,.mkv,.avi")
        video_layout.addWidget(self.video_exts_edit)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # 元数据文件扩展名
        meta_group = QGroupBox("元数据文件扩展名")
        meta_layout = QVBoxLayout()
        
        self.meta_exts_edit = QLineEdit()
        self.meta_exts_edit.setPlaceholderText("用逗号分隔，如: .srt,.ass,.ssa")
        meta_layout.addWidget(self.meta_exts_edit)
        
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)
        
        # 音频文件扩展名
        audio_group = QGroupBox("音频文件扩展名")
        audio_layout = QVBoxLayout()
        
        self.audio_exts_edit = QLineEdit()
        self.audio_exts_edit.setPlaceholderText("用逗号分隔，如: .aac,.ac3,.dts,.flac,.mp3")
        audio_layout.addWidget(self.audio_exts_edit)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # 电视剧文件夹关键词
        tv_keywords_group = QGroupBox("电视剧文件夹关键词")
        tv_keywords_layout = QVBoxLayout()
        
        self.tv_folder_keywords_edit = QLineEdit()
        self.tv_folder_keywords_edit.setPlaceholderText("用逗号分隔，如: 电视剧,剧集,TV,Series")
        tv_keywords_layout.addWidget(self.tv_folder_keywords_edit)
        
        tv_keywords_group.setLayout(tv_keywords_layout)
        layout.addWidget(tv_keywords_group)
        
        # 电影文件夹关键词
        movie_keywords_group = QGroupBox("电影文件夹关键词")
        movie_keywords_layout = QVBoxLayout()
        
        self.movie_folder_keywords_edit = QLineEdit()
        self.movie_folder_keywords_edit.setPlaceholderText("用逗号分隔，如: 电影,Movie,Film")
        movie_keywords_layout.addWidget(self.movie_folder_keywords_edit)
        
        movie_keywords_group.setLayout(movie_keywords_layout)
        layout.addWidget(movie_keywords_group)
        
        # 文件类型检查选项
        file_check_group = QGroupBox("文件类型检查选项")
        file_check_layout = QVBoxLayout()
        
        # 检查电影文件
        self.enable_movie_check_checkbox = QCheckBox("检查电影文件")
        self.enable_movie_check_checkbox.setToolTip("启用后会在扫描时识别和处理电影文件")
        file_check_layout.addWidget(self.enable_movie_check_checkbox)
        
        # 检查电视剧文件
        self.enable_tv_check_checkbox = QCheckBox("检查电视剧文件")
        self.enable_tv_check_checkbox.setToolTip("启用后会在扫描时识别和处理电视剧文件")
        file_check_layout.addWidget(self.enable_tv_check_checkbox)
        
        # 检查特辑文件
        self.enable_special_check_checkbox = QCheckBox("检查特辑文件")
        self.enable_special_check_checkbox.setToolTip("启用后会在扫描时识别和处理特辑文件")
        file_check_layout.addWidget(self.enable_special_check_checkbox)
        
        # 强制电影规则
        self.force_movie_rules_checkbox = QCheckBox("强制应用电影命名规则")
        self.force_movie_rules_checkbox.setToolTip("启用后会强制将文件按电影规则处理，忽略其他识别结果")
        file_check_layout.addWidget(self.force_movie_rules_checkbox)
        
        # 强制电视剧规则
        self.force_tv_rules_checkbox = QCheckBox("强制应用电视剧命名规则")
        self.force_tv_rules_checkbox.setToolTip("启用后会强制将文件按电视剧规则处理，忽略其他识别结果")
        file_check_layout.addWidget(self.force_tv_rules_checkbox)
        
        file_check_group.setLayout(file_check_layout)
        layout.addWidget(file_check_group)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        return scroll_area
    
    def _create_templates_tab(self):
        """创建模板选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 电影模板
        movie_group = QGroupBox("电影命名模板")
        movie_layout = QVBoxLayout()
        
        self.movie_template_edit = QLineEdit()
        self.movie_template_edit.setPlaceholderText("{title} ({year}){ext}")
        movie_layout.addWidget(self.movie_template_edit)
        
        movie_group.setLayout(movie_layout)
        layout.addWidget(movie_group)
        
        # 电视剧模板
        tv_group = QGroupBox("电视剧命名模板")
        tv_layout = QVBoxLayout()
        
        self.tv_template_edit = QLineEdit()
        self.tv_template_edit.setPlaceholderText("{title}.S{season:02d}E{episode:02d}{ext}")
        tv_layout.addWidget(self.tv_template_edit)
        
        tv_group.setLayout(tv_layout)
        layout.addWidget(tv_group)
        
        # 特辑模板
        special_group = QGroupBox("特辑命名模板")
        special_layout = QVBoxLayout()
        
        self.special_template_edit = QLineEdit()
        self.special_template_edit.setPlaceholderText("{title}.特别篇.E{episode:02d}{ext}")
        special_layout.addWidget(self.special_template_edit)
        
        special_group.setLayout(special_layout)
        layout.addWidget(special_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_security_tab(self):
        """创建安全选项卡"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        
        # 沙盒模式
        self.enable_sandbox_checkbox = QCheckBox("启用沙盒模式")
        layout.addWidget(self.enable_sandbox_checkbox)
        
        # 操作确认
        self.enable_confirmation_checkbox = QCheckBox("启用操作确认")
        layout.addWidget(self.enable_confirmation_checkbox)
        
        # 路径验证
        self.enable_path_validation_checkbox = QCheckBox("启用路径验证")
        layout.addWidget(self.enable_path_validation_checkbox)
        
        # 文件大小检查
        self.enable_file_size_check_checkbox = QCheckBox("启用文件大小检查")
        layout.addWidget(self.enable_file_size_check_checkbox)
        
        # 最大文件数
        max_files_group = QGroupBox("单次操作最大文件数")
        max_files_layout = QHBoxLayout()
        
        self.max_files_spinbox = QSpinBox()
        self.max_files_spinbox.setRange(1, 100000)
        self.max_files_spinbox.setValue(1000)
        max_files_layout.addWidget(self.max_files_spinbox)
        
        max_files_group.setLayout(max_files_layout)
        layout.addWidget(max_files_group)
        
        # 可疑文件检测
        self.enable_suspicious_detection_checkbox = QCheckBox("启用可疑文件检测")
        layout.addWidget(self.enable_suspicious_detection_checkbox)
        
        # 破坏性操作确认
        self.enable_destructive_confirmation_checkbox = QCheckBox("启用破坏性操作确认")
        layout.addWidget(self.enable_destructive_confirmation_checkbox)
        
        # 批量操作确认
        self.enable_batch_confirmation_checkbox = QCheckBox("启用批量操作确认")
        layout.addWidget(self.enable_batch_confirmation_checkbox)
        
        # 确认阈值
        threshold_group = QGroupBox("确认阈值 (文件数量)")
        threshold_layout = QHBoxLayout()
        
        self.confirmation_threshold_spinbox = QSpinBox()
        self.confirmation_threshold_spinbox.setRange(1, 1000)
        self.confirmation_threshold_spinbox.setValue(10)
        threshold_layout.addWidget(self.confirmation_threshold_spinbox)
        
        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        
        # 确认超时时间
        timeout_group = QGroupBox("确认超时时间 (秒)")
        timeout_layout = QHBoxLayout()
        
        self.confirmation_timeout_spinbox = QSpinBox()
        self.confirmation_timeout_spinbox.setRange(5, 300)
        self.confirmation_timeout_spinbox.setValue(30)
        timeout_layout.addWidget(self.confirmation_timeout_spinbox)
        
        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)
        
        # 禁止路径设置
        forbidden_paths_group = QGroupBox("禁止访问的路径")
        forbidden_paths_layout = QVBoxLayout()
        
        self.forbidden_paths_edit = QTextEdit()
        self.forbidden_paths_edit.setMaximumHeight(100)
        self.forbidden_paths_edit.setPlaceholderText("每行一个路径，如:\n/system\n/boot\n/etc\nC:\\Windows")
        forbidden_paths_layout.addWidget(self.forbidden_paths_edit)
        
        forbidden_paths_group.setLayout(forbidden_paths_layout)
        layout.addWidget(forbidden_paths_group)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        return scroll_area
    
    def _load_settings(self):
        """加载设置到UI"""
        try:
            # 文件类型设置
            video_exts = self.settings.get('video_extensions', ['.mp4', '.mkv', '.avi'])
            self.video_exts_edit.setText(','.join(video_exts))
            
            meta_exts = self.settings.get('metadata_extensions', ['.srt', '.ass', '.ssa'])
            self.meta_exts_edit.setText(','.join(meta_exts))
            
            # 音频文件扩展名
            audio_exts = self.settings.get('audio_extensions', ['.aac', '.ac3', '.dts', '.flac', '.mp3'])
            self.audio_exts_edit.setText(','.join(audio_exts))
            
            # 电视剧文件夹关键词
            tv_keywords = self.settings.get('tv_folder_keywords', ['电视剧', '剧集', 'TV', 'Series'])
            self.tv_folder_keywords_edit.setText(','.join(tv_keywords))
            
            # 电影文件夹关键词
            movie_keywords = self.settings.get('movie_folder_keywords', ['电影', 'Movie', 'Film'])
            self.movie_folder_keywords_edit.setText(','.join(movie_keywords))
            
            # 文件类型检查选项
            self.enable_movie_check_checkbox.setChecked(self.settings.get('enable_movie_check', True))
            self.enable_tv_check_checkbox.setChecked(self.settings.get('enable_tv_check', True))
            self.enable_special_check_checkbox.setChecked(self.settings.get('enable_special_check', True))
            self.force_movie_rules_checkbox.setChecked(self.settings.get('force_movie_rules', False))
            self.force_tv_rules_checkbox.setChecked(self.settings.get('force_tv_rules', False))
            
            # 模板设置
            self.movie_template_edit.setText(self.settings.get('movie_template', '{title} ({year}){ext}'))
            self.tv_template_edit.setText(self.settings.get('tv_template', '{title}.S{season:02d}E{episode:02d}{ext}'))
            self.special_template_edit.setText(self.settings.get('special_template', '{title}.特别篇.E{episode:02d}{ext}'))
            
            # 安全设置
            security_settings = self.settings.get('security', {})
            self.enable_sandbox_checkbox.setChecked(security_settings.get('enable_sandbox', False))
            self.enable_confirmation_checkbox.setChecked(security_settings.get('enable_confirmation', True))
            self.enable_path_validation_checkbox.setChecked(security_settings.get('enable_path_validation', True))
            self.enable_file_size_check_checkbox.setChecked(security_settings.get('enable_file_size_check', True))
            self.max_files_spinbox.setValue(security_settings.get('max_files_per_operation', 1000))
            
            # 性能设置
            performance_settings = self.settings.get('performance', {})
            self.max_workers_spinbox.setValue(performance_settings.get('max_workers', 4))
            self.cache_size_spinbox.setValue(performance_settings.get('cache_size', 1000))
            self.batch_size_spinbox.setValue(performance_settings.get('batch_size', 100))
            self.memory_threshold_spinbox.setValue(int(performance_settings.get('memory_threshold', 0.8) * 100))
            
            # 快速模式设置
            self.enable_fast_mode_checkbox.setChecked(self.settings.get('fast_mode', True))
            
            # 日志设置
            logging_settings = self.settings.get('logging', {})
            log_level = logging_settings.get('level', 'INFO')
            index = self.log_level_combo.findText(log_level)
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)
            
            self.max_errors_spinbox.setValue(self.settings.get('max_errors', 100))
            self.enable_logging_checkbox.setChecked(self.settings.get('enable_logging', True))
            self.enable_performance_logging_checkbox.setChecked(logging_settings.get('enable_performance_logging', True))
            
            # 缓存设置
            self.cache_ttl_spinbox.setValue(self.settings.get('cache_ttl', 3600))
            self.cache_max_size_spinbox.setValue(self.settings.get('cache_max_size_mb', 100))
            self.enable_incremental_cache_checkbox.setChecked(self.settings.get('enable_incremental_cache', True))
            self.cache_auto_cleanup_checkbox.setChecked(self.settings.get('cache_auto_cleanup', True))
            
            # 高级设置
            self.enable_backup_checkbox.setChecked(self.settings.get('backup_enabled', True))
            self.backup_interval_spinbox.setValue(self.settings.get('backup_interval', 3600))
            self.enable_performance_monitoring_checkbox.setChecked(self.settings.get('performance_monitoring', True))
            self.enable_hash_check_checkbox.setChecked(self.settings.get('enable_hash_check', False))
            self.enable_special_check_checkbox.setChecked(self.settings.get('enable_special_check', True))
            self.force_special_season_checkbox.setChecked(self.settings.get('force_special_season', True))
            self.enable_history_checkbox.setChecked(self.settings.get('enable_history', True))
            
            special_keywords = self.settings.get('special_keywords', ['特辑','特别篇','Special'])
            self.special_keywords_edit.setText(','.join(special_keywords))
            
            self.max_file_size_spinbox.setValue(self.settings.get('max_file_size_mb', 50000))
            
            # 安全设置 - 新增项
            self.enable_suspicious_detection_checkbox.setChecked(self.settings.get('enable_suspicious_detection', True))
            self.enable_destructive_confirmation_checkbox.setChecked(self.settings.get('enable_destructive_operation_confirmation', True))
            self.enable_batch_confirmation_checkbox.setChecked(self.settings.get('enable_batch_confirmation', True))
            self.confirmation_threshold_spinbox.setValue(self.settings.get('confirmation_threshold', 10))
            self.confirmation_timeout_spinbox.setValue(self.settings.get('confirmation_timeout', 30))
            
            # 沙盒设置
            self.sandbox_directory_edit.setText(self.settings.get('sandbox_directory', ''))
            self.auto_cleanup_sandbox_checkbox.setChecked(self.settings.get('auto_cleanup_sandbox', False))
            
            # 禁止路径设置
            forbidden_paths = self.settings.get('forbidden_paths', ['/system', '/boot', '/etc', '/usr', '/var', '/proc', '/dev', 'C:\\Windows', 'C:\\System32'])
            self.forbidden_paths_edit.setPlainText('\n'.join(forbidden_paths))
            
            # 检查点设置
            self.resume_enabled_checkbox.setChecked(self.settings.get('resume_enabled', False))
            self.checkpoint_enabled_checkbox.setChecked(self.settings.get('checkpoint_enabled', True))
            self.batch_mode_checkbox.setChecked(self.settings.get('batch_mode', False))
            
        except Exception as e:
            print(f"加载设置到UI失败: {e}")
    
    def get_settings(self) -> dict:
        """获取UI中的设置"""
        try:
            settings = {}
            
            # 文件类型设置
            video_exts_text = self.video_exts_edit.text().strip()
            settings['video_extensions'] = [ext.strip() for ext in video_exts_text.split(',') if ext.strip()]
            
            meta_exts_text = self.meta_exts_edit.text().strip()
            settings['metadata_extensions'] = [ext.strip() for ext in meta_exts_text.split(',') if ext.strip()]
            
            # 音频文件扩展名
            audio_exts_text = self.audio_exts_edit.text().strip()
            settings['audio_extensions'] = [ext.strip() for ext in audio_exts_text.split(',') if ext.strip()]
            
            # 电视剧文件夹关键词
            tv_keywords_text = self.tv_folder_keywords_edit.text().strip()
            settings['tv_folder_keywords'] = [kw.strip() for kw in tv_keywords_text.split(',') if kw.strip()]
            
            # 电影文件夹关键词
            movie_keywords_text = self.movie_folder_keywords_edit.text().strip()
            settings['movie_folder_keywords'] = [kw.strip() for kw in movie_keywords_text.split(',') if kw.strip()]
            
            # 文件类型检查选项
            settings['enable_movie_check'] = self.enable_movie_check_checkbox.isChecked()
            settings['enable_tv_check'] = self.enable_tv_check_checkbox.isChecked()
            settings['enable_special_check'] = self.enable_special_check_checkbox.isChecked()
            settings['force_movie_rules'] = self.force_movie_rules_checkbox.isChecked()
            settings['force_tv_rules'] = self.force_tv_rules_checkbox.isChecked()
            
            # 模板设置
            settings['movie_template'] = self.movie_template_edit.text().strip()
            settings['tv_template'] = self.tv_template_edit.text().strip()
            settings['special_template'] = self.special_template_edit.text().strip()
            
            # 安全设置
            settings['security'] = {
                'enable_sandbox': self.enable_sandbox_checkbox.isChecked(),
                'enable_confirmation': self.enable_confirmation_checkbox.isChecked(),
                'enable_path_validation': self.enable_path_validation_checkbox.isChecked(),
                'enable_file_size_check': self.enable_file_size_check_checkbox.isChecked(),
                'max_files_per_operation': self.max_files_spinbox.value()
            }
            settings['enable_suspicious_detection'] = self.enable_suspicious_detection_checkbox.isChecked()
            settings['enable_destructive_operation_confirmation'] = self.enable_destructive_confirmation_checkbox.isChecked()
            settings['enable_batch_confirmation'] = self.enable_batch_confirmation_checkbox.isChecked()
            settings['confirmation_threshold'] = self.confirmation_threshold_spinbox.value()
            settings['confirmation_timeout'] = self.confirmation_timeout_spinbox.value()
            
            # 性能设置
            settings['performance'] = {
                'max_workers': self.max_workers_spinbox.value(),
                'cache_size': self.cache_size_spinbox.value(),
                'batch_size': self.batch_size_spinbox.value(),
                'memory_threshold': self.memory_threshold_spinbox.value() / 100.0
            }
            
            # 快速模式设置
            settings['fast_mode'] = self.enable_fast_mode_checkbox.isChecked()
            
            # 日志设置
            settings['logging'] = {
                'level': self.log_level_combo.currentText(),
                'enable_performance_logging': self.enable_performance_logging_checkbox.isChecked()
            }
            settings['max_errors'] = self.max_errors_spinbox.value()
            settings['enable_logging'] = self.enable_logging_checkbox.isChecked()
            
            # 缓存设置
            settings['cache_ttl'] = self.cache_ttl_spinbox.value()
            settings['cache_max_size_mb'] = self.cache_max_size_spinbox.value()
            settings['enable_incremental_cache'] = self.enable_incremental_cache_checkbox.isChecked()
            settings['cache_auto_cleanup'] = self.cache_auto_cleanup_checkbox.isChecked()
            
            # 高级设置
            settings['backup_enabled'] = self.enable_backup_checkbox.isChecked()
            settings['backup_interval'] = self.backup_interval_spinbox.value()
            settings['performance_monitoring'] = self.enable_performance_monitoring_checkbox.isChecked()
            settings['enable_hash_check'] = self.enable_hash_check_checkbox.isChecked()
            settings['enable_special_check'] = self.enable_special_check_checkbox.isChecked()
            settings['force_special_season'] = self.force_special_season_checkbox.isChecked()
            settings['enable_history'] = self.enable_history_checkbox.isChecked()
            
            special_keywords = self.special_keywords_edit.text().strip()
            settings['special_keywords'] = [kw.strip() for kw in special_keywords.split(',') if kw.strip()]
            
            settings['max_file_size_mb'] = self.max_file_size_spinbox.value()
            
            # 沙盒设置
            settings['sandbox_directory'] = self.sandbox_directory_edit.text().strip() or None
            settings['auto_cleanup_sandbox'] = self.auto_cleanup_sandbox_checkbox.isChecked()
            
            # 禁止路径设置
            forbidden_paths_text = self.forbidden_paths_edit.toPlainText().strip()
            settings['forbidden_paths'] = [p.strip() for p in forbidden_paths_text.split('\n') if p.strip()]
            
            # 检查点设置
            settings['resume_enabled'] = self.resume_enabled_checkbox.isChecked()
            settings['checkpoint_enabled'] = self.checkpoint_enabled_checkbox.isChecked()
            settings['batch_mode'] = self.batch_mode_checkbox.isChecked()
            
            return settings
            
        except Exception as e:
            print(f"获取UI设置失败: {e}")
            return {}
    
    def _select_sandbox_directory(self):
        """选择沙盒目录"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择沙盒目录",
            self.sandbox_directory_edit.text() or os.path.expanduser("~")
        )
        if directory:
            self.sandbox_directory_edit.setText(directory)
    
    def _create_cache_tab(self):
        """创建缓存选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 缓存有效期
        ttl_group = QGroupBox("缓存有效期 (秒)")
        ttl_layout = QHBoxLayout()
        
        self.cache_ttl_spinbox = QSpinBox()
        self.cache_ttl_spinbox.setRange(60, 86400)  # 1分钟到24小时
        self.cache_ttl_spinbox.setValue(3600)  # 默认1小时
        ttl_layout.addWidget(self.cache_ttl_spinbox)
        
        ttl_group.setLayout(ttl_layout)
        layout.addWidget(ttl_group)
        
        # 缓存最大大小
        max_size_group = QGroupBox("缓存最大大小 (MB)")
        max_size_layout = QHBoxLayout()
        
        self.cache_max_size_spinbox = QSpinBox()
        self.cache_max_size_spinbox.setRange(10, 10000)
        self.cache_max_size_spinbox.setValue(100)
        max_size_layout.addWidget(self.cache_max_size_spinbox)
        
        max_size_group.setLayout(max_size_layout)
        layout.addWidget(max_size_group)
        
        # 缓存选项
        self.enable_incremental_cache_checkbox = QCheckBox("启用增量缓存更新")
        layout.addWidget(self.enable_incremental_cache_checkbox)
        
        self.cache_auto_cleanup_checkbox = QCheckBox("自动清理过期缓存")
        layout.addWidget(self.cache_auto_cleanup_checkbox)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_performance_tab(self):
        """创建性能选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 最大工作线程数
        workers_group = QGroupBox("最大工作线程数")
        workers_layout = QHBoxLayout()
        
        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 16)
        self.max_workers_spinbox.setValue(4)
        workers_layout.addWidget(self.max_workers_spinbox)
        
        workers_group.setLayout(workers_layout)
        layout.addWidget(workers_group)
        
        # 缓存大小
        cache_group = QGroupBox("缓存大小")
        cache_layout = QHBoxLayout()
        
        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(100, 10000)
        self.cache_size_spinbox.setValue(1000)
        cache_layout.addWidget(self.cache_size_spinbox)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # 批处理大小
        batch_group = QGroupBox("批处理大小")
        batch_layout = QHBoxLayout()
        
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(10, 1000)
        self.batch_size_spinbox.setValue(100)
        batch_layout.addWidget(self.batch_size_spinbox)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        # 内存阈值
        memory_group = QGroupBox("内存使用阈值 (%)")
        memory_layout = QHBoxLayout()
        
        self.memory_threshold_spinbox = QSpinBox()
        self.memory_threshold_spinbox.setRange(50, 95)
        self.memory_threshold_spinbox.setValue(80)
        memory_layout.addWidget(self.memory_threshold_spinbox)
        
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        # 快速模式
        self.enable_fast_mode_checkbox = QCheckBox("启用快速扫描模式")
        self.enable_fast_mode_checkbox.setToolTip("启用快速扫描模式，跳过复杂的文件分析以提高速度")
        layout.addWidget(self.enable_fast_mode_checkbox)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_logging_tab(self):
        """创建日志选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 日志级别
        level_group = QGroupBox("日志级别")
        level_layout = QHBoxLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        level_layout.addWidget(self.log_level_combo)
        
        level_group.setLayout(level_layout)
        layout.addWidget(level_group)
        
        # 最大错误数
        max_errors_group = QGroupBox("最大错误数")
        max_errors_layout = QHBoxLayout()
        
        self.max_errors_spinbox = QSpinBox()
        self.max_errors_spinbox.setRange(10, 10000)
        self.max_errors_spinbox.setValue(100)
        max_errors_layout.addWidget(self.max_errors_spinbox)
        
        max_errors_group.setLayout(max_errors_layout)
        layout.addWidget(max_errors_group)
        
        # 启用日志
        self.enable_logging_checkbox = QCheckBox("启用日志记录")
        layout.addWidget(self.enable_logging_checkbox)
        
        # 性能日志
        self.enable_performance_logging_checkbox = QCheckBox("启用性能日志")
        layout.addWidget(self.enable_performance_logging_checkbox)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_advanced_tab(self):
        """创建高级选项卡"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        
        # 备份设置
        backup_group = QGroupBox("备份设置")
        backup_layout = QVBoxLayout()
        
        self.enable_backup_checkbox = QCheckBox("启用配置备份")
        backup_layout.addWidget(self.enable_backup_checkbox)
        
        backup_interval_layout = QHBoxLayout()
        backup_interval_layout.addWidget(QLabel("备份间隔 (秒):"))
        
        self.backup_interval_spinbox = QSpinBox()
        self.backup_interval_spinbox.setRange(300, 86400)  # 5分钟到24小时
        self.backup_interval_spinbox.setValue(3600)  # 默认1小时
        backup_interval_layout.addWidget(self.backup_interval_spinbox)
        
        backup_layout.addLayout(backup_interval_layout)
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # 性能监控
        performance_group = QGroupBox("性能监控")
        performance_layout = QVBoxLayout()
        
        self.enable_performance_monitoring_checkbox = QCheckBox("启用性能监控")
        performance_layout.addWidget(self.enable_performance_monitoring_checkbox)
        
        performance_group.setLayout(performance_layout)
        layout.addWidget(performance_group)
        
        # 文件处理设置
        file_processing_group = QGroupBox("文件处理设置")
        file_processing_layout = QVBoxLayout()
        
        self.enable_hash_check_checkbox = QCheckBox("启用文件哈希检查")
        file_processing_layout.addWidget(self.enable_hash_check_checkbox)
        
        self.enable_special_check_checkbox = QCheckBox("启用特辑检查")
        file_processing_layout.addWidget(self.enable_special_check_checkbox)
        
        self.force_special_season_checkbox = QCheckBox("强制特辑季数")
        file_processing_layout.addWidget(self.force_special_season_checkbox)
        
        self.enable_history_checkbox = QCheckBox("启用操作历史")
        file_processing_layout.addWidget(self.enable_history_checkbox)
        
        file_processing_group.setLayout(file_processing_layout)
        layout.addWidget(file_processing_group)
        
        # 特辑关键词
        special_keywords_group = QGroupBox("特辑关键词")
        special_keywords_layout = QVBoxLayout()
        
        self.special_keywords_edit = QLineEdit()
        self.special_keywords_edit.setPlaceholderText("用逗号分隔，如: 特辑,特别篇,Special")
        special_keywords_layout.addWidget(self.special_keywords_edit)
        
        special_keywords_group.setLayout(special_keywords_layout)
        layout.addWidget(special_keywords_group)
        
        # 最大文件大小
        max_file_size_group = QGroupBox("最大文件大小 (MB)")
        max_file_size_layout = QHBoxLayout()
        
        self.max_file_size_spinbox = QSpinBox()
        self.max_file_size_spinbox.setRange(100, 1000000)  # 100MB到1TB
        self.max_file_size_spinbox.setValue(50000)  # 默认50GB
        max_file_size_layout.addWidget(self.max_file_size_spinbox)
        
        max_file_size_group.setLayout(max_file_size_layout)
        layout.addWidget(max_file_size_group)
        
        # 沙盒设置
        sandbox_group = QGroupBox("沙盒设置")
        sandbox_layout = QVBoxLayout()
        
        # 沙盒目录
        sandbox_dir_layout = QHBoxLayout()
        sandbox_dir_layout.addWidget(QLabel("沙盒目录:"))
        
        self.sandbox_directory_edit = QLineEdit()
        self.sandbox_directory_edit.setPlaceholderText("留空使用默认沙盒目录")
        sandbox_dir_layout.addWidget(self.sandbox_directory_edit)
        
        sandbox_dir_button = QPushButton("浏览")
        sandbox_dir_button.clicked.connect(self._select_sandbox_directory)
        sandbox_dir_layout.addWidget(sandbox_dir_button)
        
        sandbox_layout.addLayout(sandbox_dir_layout)
        
        # 自动清理沙盒
        self.auto_cleanup_sandbox_checkbox = QCheckBox("自动清理沙盒")
        sandbox_layout.addWidget(self.auto_cleanup_sandbox_checkbox)
        
        sandbox_group.setLayout(sandbox_layout)
        layout.addWidget(sandbox_group)
        
        # 检查点设置
        checkpoint_group = QGroupBox("检查点设置")
        checkpoint_layout = QVBoxLayout()
        
        self.resume_enabled_checkbox = QCheckBox("启用恢复功能")
        checkpoint_layout.addWidget(self.resume_enabled_checkbox)
        
        self.checkpoint_enabled_checkbox = QCheckBox("启用检查点功能")
        checkpoint_layout.addWidget(self.checkpoint_enabled_checkbox)
        
        self.batch_mode_checkbox = QCheckBox("启用批处理模式")
        checkpoint_layout.addWidget(self.batch_mode_checkbox)
        
        checkpoint_group.setLayout(checkpoint_layout)
        layout.addWidget(checkpoint_group)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        return scroll_area 