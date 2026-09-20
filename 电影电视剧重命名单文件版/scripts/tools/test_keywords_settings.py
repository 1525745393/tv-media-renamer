#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.settings_dialog import SettingsDialog

def test_keywords_settings():
    """测试电影和电视剧关键词设置"""
    app = QApplication(sys.argv)
    
    # 测试设置
    test_settings = {
        'video_extensions': ['.mp4', '.mkv', '.avi'],
        'metadata_extensions': ['.srt', '.ass', '.nfo'],
        'tv_folder_keywords': ['电视剧', '剧集', 'TV', 'Series'],
        'movie_folder_keywords': ['电影', 'Movie', 'Film'],
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
        print("🚀 测试电影和电视剧关键词设置...")
        dialog = SettingsDialog(test_settings)
        
        print("📋 检查关键词设置UI组件...")
        
        # 检查UI组件是否存在
        if hasattr(dialog, 'tv_folder_keywords_edit'):
            print("   ✅ 电视剧关键词编辑框存在")
            tv_keywords = dialog.tv_folder_keywords_edit.text()
            print(f"   - 当前值: {tv_keywords}")
        else:
            print("   ❌ 电视剧关键词编辑框不存在")
        
        if hasattr(dialog, 'movie_folder_keywords_edit'):
            print("   ✅ 电影关键词编辑框存在")
            movie_keywords = dialog.movie_folder_keywords_edit.text()
            print(f"   - 当前值: {movie_keywords}")
        else:
            print("   ❌ 电影关键词编辑框不存在")
        
        print("\n🎮 显示设置对话框...")
        print("   请检查文件类型选项卡中的关键词设置")
        
        result = dialog.exec_()
        
        if result == dialog.Accepted:
            print("✅ 用户点击了确定")
            settings = dialog.get_settings()
            
            # 检查关键词设置
            print("\n🔍 检查关键词设置...")
            
            if 'tv_folder_keywords' in settings:
                tv_keywords = settings['tv_folder_keywords']
                print(f"   ✅ 电视剧关键词: {tv_keywords}")
            else:
                print("   ❌ 电视剧关键词未保存")
            
            if 'movie_folder_keywords' in settings:
                movie_keywords = settings['movie_folder_keywords']
                print(f"   ✅ 电影关键词: {movie_keywords}")
            else:
                print("   ❌ 电影关键词未保存")
            
            print(f"\n📋 总共获取到 {len(settings)} 个设置项")
        else:
            print("❌ 用户点击了取消")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    app.quit()

if __name__ == "__main__":
    test_keywords_settings() 