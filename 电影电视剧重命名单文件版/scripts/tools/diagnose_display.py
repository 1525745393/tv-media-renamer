#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.settings_dialog import SettingsDialog

def diagnose_display():
    """诊断设置对话框显示问题"""
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
        
        print("📋 对话框基本信息:")
        print(f"   - 标题: {dialog.windowTitle()}")
        print(f"   - 大小: {dialog.size().width()}x{dialog.size().height()}")
        print(f"   - 位置: {dialog.pos().x()}, {dialog.pos().y()}")
        
        # 检查选项卡
        if hasattr(dialog, 'tab_widget'):
            print(f"\n📑 选项卡信息:")
            print(f"   - 选项卡数量: {dialog.tab_widget.count()}")
            
            for i in range(dialog.tab_widget.count()):
                tab_name = dialog.tab_widget.tabText(i)
                tab_widget = dialog.tab_widget.widget(i)
                print(f"   - 选项卡 {i+1}: {tab_name}")
                print(f"     - 大小: {tab_widget.size().width()}x{tab_widget.size().height()}")
                print(f"     - 可见: {tab_widget.isVisible()}")
        
        print("\n🔍 显示问题诊断:")
        print("   1. 对话框大小是否足够? (当前: 800x600)")
        print("   2. 所有选项卡是否都能正常切换?")
        print("   3. 设置项是否都被正确加载?")
        print("   4. 是否有滚动条出现?")
        print("   5. 设置项是否被截断或隐藏?")
        
        # 显示对话框
        print("\n🎮 显示设置对话框...")
        print("   请检查上述问题并告诉我具体的问题")
        
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            print("✅ 用户点击了确定")
            settings = dialog.get_settings()
            print(f"📋 成功获取 {len(settings)} 个设置项")
        else:
            print("❌ 用户点击了取消")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
    
    app.quit()

if __name__ == "__main__":
    diagnose_display() 