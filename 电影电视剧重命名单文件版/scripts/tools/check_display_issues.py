#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.settings_dialog import SettingsDialog

def check_display_issues():
    """检查设置对话框显示问题"""
    app = QApplication(sys.argv)
    
    # 测试设置
    test_settings = {
        'video_extensions': ['.mp4', '.mkv', '.avi'],
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
        
        print("📋 检查对话框显示属性...")
        print(f"   - 对话框标题: {dialog.windowTitle()}")
        print(f"   - 对话框大小: {dialog.size().width()}x{dialog.size().height()}")
        print(f"   - 对话框位置: {dialog.pos().x()}, {dialog.pos().y()}")
        
        # 检查选项卡
        if hasattr(dialog, 'tab_widget'):
            print(f"   - 选项卡数量: {dialog.tab_widget.count()}")
            for i in range(dialog.tab_widget.count()):
                tab_name = dialog.tab_widget.tabText(i)
                tab_widget = dialog.tab_widget.widget(i)
                print(f"     - 选项卡 {i+1}: {tab_name}")
                print(f"       - 选项卡大小: {tab_widget.size().width()}x{tab_widget.size().height()}")
                
                # 检查选项卡内容是否可见
                if hasattr(tab_widget, 'children'):
                    children_count = len(tab_widget.children())
                    print(f"       - 子控件数量: {children_count}")
        
        print("\n🔍 检查各选项卡的UI组件...")
        
        # 检查每个选项卡的关键组件
        tab_components = {
            "文件类型": ['video_exts_edit', 'meta_exts_edit'],
            "命名模板": ['movie_template_edit', 'tv_template_edit', 'special_template_edit'],
            "安全设置": ['enable_sandbox_checkbox', 'enable_confirmation_checkbox', 'enable_path_validation_checkbox', 
                        'enable_file_size_check_checkbox', 'max_files_spinbox', 'enable_suspicious_detection_checkbox',
                        'enable_destructive_confirmation_checkbox', 'enable_batch_confirmation_checkbox',
                        'confirmation_threshold_spinbox', 'confirmation_timeout_spinbox', 'forbidden_paths_edit'],
            "性能设置": ['max_workers_spinbox', 'cache_size_spinbox', 'batch_size_spinbox', 'memory_threshold_spinbox'],
            "日志设置": ['log_level_combo', 'max_errors_spinbox', 'enable_logging_checkbox', 'enable_performance_logging_checkbox'],
            "缓存设置": ['cache_ttl_spinbox', 'cache_max_size_spinbox', 'enable_incremental_cache_checkbox', 'cache_auto_cleanup_checkbox'],
            "高级设置": ['enable_backup_checkbox', 'backup_interval_spinbox', 'enable_performance_monitoring_checkbox',
                        'enable_hash_check_checkbox', 'enable_special_check_checkbox', 'force_special_season_checkbox',
                        'enable_history_checkbox', 'special_keywords_edit', 'max_file_size_spinbox',
                        'sandbox_directory_edit', 'auto_cleanup_sandbox_checkbox', 'resume_enabled_checkbox',
                        'checkpoint_enabled_checkbox', 'batch_mode_checkbox']
        }
        
        for tab_name, components in tab_components.items():
            print(f"\n   {tab_name}选项卡:")
            missing_components = []
            for component in components:
                if hasattr(dialog, component):
                    # 检查组件是否可见
                    widget = getattr(dialog, component)
                    if hasattr(widget, 'isVisible'):
                        if widget.isVisible():
                            print(f"     ✅ {component} (可见)")
                        else:
                            print(f"     ⚠️ {component} (不可见)")
                            missing_components.append(component)
                    else:
                        print(f"     ✅ {component}")
                else:
                    print(f"     ❌ {component}")
                    missing_components.append(component)
            
            if missing_components:
                print(f"     ⚠️ 缺失或不可见的组件: {len(missing_components)} 个")
        
        print("\n🎮 显示设置对话框...")
        print("   请检查以下问题:")
        print("   1. 所有选项卡是否都能正常切换")
        print("   2. 所有设置项是否都可见")
        print("   3. 是否有滚动条出现")
        print("   4. 设置项是否被截断或隐藏")
        
        # 显示对话框
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            print("✅ 用户点击了确定")
            settings = dialog.get_settings()
            print(f"📋 获取到 {len(settings)} 个设置项")
            
            # 检查关键设置项
            print("\n🔍 检查关键设置项:")
            key_settings = ['video_extensions', 'metadata_extensions', 'movie_template', 'performance', 'logging', 'security']
            for setting in key_settings:
                if setting in settings:
                    print(f"   ✅ {setting}")
                else:
                    print(f"   ❌ {setting}")
        else:
            print("❌ 用户点击了取消")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    app.quit()

if __name__ == "__main__":
    check_display_issues() 