#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.settings_dialog import SettingsDialog

def test_dialog_display():
    """测试设置对话框显示"""
    app = QApplication(sys.argv)
    
    # 测试设置
    test_settings = {
        'video_extensions': ['.mp4', '.mkv', '.avi', '.mov'],
        'metadata_extensions': ['.srt', '.ass', '.nfo'],
        'movie_template': '{title} ({year}){ext}',
        'tv_template': '{title}.S{season:02d}E{episode:02d}{ext}',
        'special_template': '{title}.特别篇.E{episode:02d}{ext}',
        'performance': {
            'max_workers': 4,
            'cache_size': 1000,
            'batch_size': 100,
            'memory_threshold': 0.8
        },
        'logging': {
            'level': 'INFO',
            'enable_performance_logging': True
        },
        'security': {
            'enable_sandbox': False,
            'enable_confirmation': True,
            'enable_path_validation': True,
            'enable_file_size_check': True,
            'max_files_per_operation': 1000
        },
        'cache_ttl': 3600,
        'cache_max_size_mb': 100,
        'enable_incremental_cache': True,
        'cache_auto_cleanup': True,
        'backup_enabled': True,
        'backup_interval': 3600,
        'performance_monitoring': True,
        'enable_hash_check': False,
        'enable_special_check': True,
        'force_special_season': True,
        'enable_history': True,
        'special_keywords': ['特辑', '特别篇', 'Special'],
        'max_file_size_mb': 50000,
        'enable_suspicious_detection': True,
        'enable_destructive_operation_confirmation': True,
        'enable_batch_confirmation': True,
        'confirmation_threshold': 10,
        'confirmation_timeout': 30,
        'sandbox_directory': '',
        'auto_cleanup_sandbox': False,
        'forbidden_paths': ['/system', '/boot', '/etc', 'C:\\Windows'],
        'resume_enabled': False,
        'checkpoint_enabled': True,
        'batch_mode': False,
        'max_errors': 100,
        'enable_logging': True
    }
    
    try:
        print("🚀 创建设置对话框...")
        dialog = SettingsDialog(test_settings)
        
        print("📋 检查对话框属性...")
        print(f"   - 对话框标题: {dialog.windowTitle()}")
        print(f"   - 对话框大小: {dialog.size().width()}x{dialog.size().height()}")
        print(f"   - 选项卡数量: {dialog.tab_widget.count()}")
        
        # 检查每个选项卡
        for i in range(dialog.tab_widget.count()):
            tab_name = dialog.tab_widget.tabText(i)
            print(f"   - 选项卡 {i+1}: {tab_name}")
        
        print("\n🔍 检查UI组件...")
        
        # 检查文件类型选项卡
        print("   文件类型选项卡:")
        print(f"     - 视频扩展名编辑框: {hasattr(dialog, 'video_exts_edit')}")
        print(f"     - 元数据扩展名编辑框: {hasattr(dialog, 'meta_exts_edit')}")
        
        # 检查模板选项卡
        print("   模板选项卡:")
        print(f"     - 电影模板编辑框: {hasattr(dialog, 'movie_template_edit')}")
        print(f"     - 电视剧模板编辑框: {hasattr(dialog, 'tv_template_edit')}")
        print(f"     - 特辑模板编辑框: {hasattr(dialog, 'special_template_edit')}")
        
        # 检查安全选项卡
        print("   安全选项卡:")
        print(f"     - 沙盒复选框: {hasattr(dialog, 'enable_sandbox_checkbox')}")
        print(f"     - 确认复选框: {hasattr(dialog, 'enable_confirmation_checkbox')}")
        print(f"     - 路径验证复选框: {hasattr(dialog, 'enable_path_validation_checkbox')}")
        print(f"     - 文件大小检查复选框: {hasattr(dialog, 'enable_file_size_check_checkbox')}")
        print(f"     - 最大文件数: {hasattr(dialog, 'max_files_spinbox')}")
        print(f"     - 可疑检测复选框: {hasattr(dialog, 'enable_suspicious_detection_checkbox')}")
        print(f"     - 破坏性确认复选框: {hasattr(dialog, 'enable_destructive_confirmation_checkbox')}")
        print(f"     - 批量确认复选框: {hasattr(dialog, 'enable_batch_confirmation_checkbox')}")
        print(f"     - 确认阈值: {hasattr(dialog, 'confirmation_threshold_spinbox')}")
        print(f"     - 确认超时: {hasattr(dialog, 'confirmation_timeout_spinbox')}")
        print(f"     - 禁止路径编辑框: {hasattr(dialog, 'forbidden_paths_edit')}")
        
        # 检查性能选项卡
        print("   性能选项卡:")
        print(f"     - 最大工作线程数: {hasattr(dialog, 'max_workers_spinbox')}")
        print(f"     - 缓存大小: {hasattr(dialog, 'cache_size_spinbox')}")
        print(f"     - 批处理大小: {hasattr(dialog, 'batch_size_spinbox')}")
        print(f"     - 内存阈值: {hasattr(dialog, 'memory_threshold_spinbox')}")
        
        # 检查日志选项卡
        print("   日志选项卡:")
        print(f"     - 日志级别下拉框: {hasattr(dialog, 'log_level_combo')}")
        print(f"     - 最大错误数: {hasattr(dialog, 'max_errors_spinbox')}")
        print(f"     - 启用日志复选框: {hasattr(dialog, 'enable_logging_checkbox')}")
        print(f"     - 性能日志复选框: {hasattr(dialog, 'enable_performance_logging_checkbox')}")
        
        # 检查缓存选项卡
        print("   缓存选项卡:")
        print(f"     - 缓存有效期: {hasattr(dialog, 'cache_ttl_spinbox')}")
        print(f"     - 缓存最大大小: {hasattr(dialog, 'cache_max_size_spinbox')}")
        print(f"     - 增量缓存复选框: {hasattr(dialog, 'enable_incremental_cache_checkbox')}")
        print(f"     - 自动清理复选框: {hasattr(dialog, 'cache_auto_cleanup_checkbox')}")
        
        # 检查高级选项卡
        print("   高级选项卡:")
        print(f"     - 备份启用复选框: {hasattr(dialog, 'enable_backup_checkbox')}")
        print(f"     - 备份间隔: {hasattr(dialog, 'backup_interval_spinbox')}")
        print(f"     - 性能监控复选框: {hasattr(dialog, 'enable_performance_monitoring_checkbox')}")
        print(f"     - 哈希检查复选框: {hasattr(dialog, 'enable_hash_check_checkbox')}")
        print(f"     - 特辑检查复选框: {hasattr(dialog, 'enable_special_check_checkbox')}")
        print(f"     - 强制特辑季数复选框: {hasattr(dialog, 'force_special_season_checkbox')}")
        print(f"     - 操作历史复选框: {hasattr(dialog, 'enable_history_checkbox')}")
        print(f"     - 特辑关键词编辑框: {hasattr(dialog, 'special_keywords_edit')}")
        print(f"     - 最大文件大小: {hasattr(dialog, 'max_file_size_spinbox')}")
        print(f"     - 沙盒目录编辑框: {hasattr(dialog, 'sandbox_directory_edit')}")
        print(f"     - 自动清理沙盒复选框: {hasattr(dialog, 'auto_cleanup_sandbox_checkbox')}")
        print(f"     - 恢复功能复选框: {hasattr(dialog, 'resume_enabled_checkbox')}")
        print(f"     - 检查点功能复选框: {hasattr(dialog, 'checkpoint_enabled_checkbox')}")
        print(f"     - 批处理模式复选框: {hasattr(dialog, 'batch_mode_checkbox')}")
        
        print("\n✅ 设置对话框显示检查完成")
        
        # 显示对话框
        print("\n🎮 显示设置对话框...")
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            print("✅ 用户点击了确定")
            settings = dialog.get_settings()
            print(f"📋 获取到 {len(settings)} 个设置项")
        else:
            print("❌ 用户点击了取消")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    app.quit()

if __name__ == "__main__":
    test_dialog_display() 