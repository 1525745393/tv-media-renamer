#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.settings_dialog import SettingsDialog

def test_simple_dialog():
    """简单测试设置对话框显示"""
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
        
        print("📋 检查对话框基本属性...")
        print(f"   - 对话框标题: {dialog.windowTitle()}")
        print(f"   - 对话框大小: {dialog.size().width()}x{dialog.size().height()}")
        
        # 检查是否有选项卡控件
        if hasattr(dialog, 'tab_widget'):
            print(f"   - 选项卡数量: {dialog.tab_widget.count()}")
            for i in range(dialog.tab_widget.count()):
                tab_name = dialog.tab_widget.tabText(i)
                print(f"     - 选项卡 {i+1}: {tab_name}")
        else:
            print("   - 未找到选项卡控件")
        
        print("\n🔍 检查UI组件是否存在...")
        
        # 检查关键UI组件
        key_components = [
            'video_exts_edit', 'meta_exts_edit',
            'movie_template_edit', 'tv_template_edit', 'special_template_edit',
            'enable_sandbox_checkbox', 'enable_confirmation_checkbox',
            'max_workers_spinbox', 'cache_size_spinbox',
            'log_level_combo', 'max_errors_spinbox',
            'cache_ttl_spinbox', 'cache_max_size_spinbox',
            'enable_backup_checkbox', 'enable_performance_monitoring_checkbox',
            'forbidden_paths_edit', 'resume_enabled_checkbox'
        ]
        
        missing_components = []
        for component in key_components:
            if hasattr(dialog, component):
                print(f"   ✅ {component}")
            else:
                print(f"   ❌ {component}")
                missing_components.append(component)
        
        if missing_components:
            print(f"\n⚠️ 缺失的UI组件: {len(missing_components)} 个")
            for component in missing_components:
                print(f"     - {component}")
        else:
            print("\n✅ 所有关键UI组件都存在")
        
        print("\n🎮 显示设置对话框...")
        print("   请检查对话框是否正常显示所有选项卡和设置项")
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            print("✅ 用户点击了确定")
            settings = dialog.get_settings()
            print(f"📋 获取到 {len(settings)} 个设置项")
            
            # 检查关键设置项
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
    test_simple_dialog() 