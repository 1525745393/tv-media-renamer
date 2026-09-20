#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框测试脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_settings_dialog():
    """测试设置对话框"""
    print("🔍 开始设置对话框测试...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.settings_dialog import SettingsDialog
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 测试设置
        test_settings = {
            'video_exts': ['.mp4', '.mkv', '.avi'],
            'meta_exts': ['.srt', '.ass', '.ssa'],
            'movie_template': '{title} ({year}){ext}',
            'tv_template': '{title}.S{season:02d}E{episode:02d}{ext}',
            'special_template': '{title}.特别篇.E{episode:02d}{ext}',
            'enable_sandbox': False,
            'enable_confirmation': True,
            'max_files_per_operation': 1000,
            'max_workers': 4,
            'cache_size': 1000,
            'enable_logging': True,
            'log_level': 'INFO'
        }
        
        print("1. 创建设置对话框...")
        dialog = SettingsDialog(test_settings)
        print("   ✅ 设置对话框创建成功")
        
        # 测试UI组件
        print("2. 测试UI组件...")
        assert hasattr(dialog, 'video_exts_edit'), "缺少视频扩展名输入框"
        assert hasattr(dialog, 'meta_exts_edit'), "缺少元数据扩展名输入框"
        assert hasattr(dialog, 'movie_template_edit'), "缺少电影模板输入框"
        assert hasattr(dialog, 'tv_template_edit'), "缺少电视剧模板输入框"
        assert hasattr(dialog, 'special_template_edit'), "缺少特辑模板输入框"
        assert hasattr(dialog, 'enable_sandbox_checkbox'), "缺少沙盒模式复选框"
        assert hasattr(dialog, 'enable_confirmation_checkbox'), "缺少操作确认复选框"
        assert hasattr(dialog, 'max_files_spinbox'), "缺少最大文件数输入框"
        assert hasattr(dialog, 'max_workers_spinbox'), "缺少最大工作线程数输入框"
        print("   ✅ UI组件检查通过")
        
        # 测试方法
        print("3. 测试方法...")
        assert hasattr(dialog, '_load_settings'), "缺少加载设置方法"
        assert hasattr(dialog, 'get_settings'), "缺少获取设置方法"
        print("   ✅ 方法检查通过")
        
        # 测试设置加载
        print("4. 测试设置加载...")
        dialog._load_settings()
        print("   ✅ 设置加载成功")
        
        # 测试设置获取
        print("5. 测试设置获取...")
        settings = dialog.get_settings()
        assert isinstance(settings, dict), "设置不是字典类型"
        print("   ✅ 设置获取成功")
        
        print("\n🎉 设置对话框测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 设置对话框测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_completeness():
    """测试设置完整性"""
    print("\n🔧 开始设置完整性测试...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.settings_dialog import SettingsDialog
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 默认设置
        default_settings = {}
        dialog = SettingsDialog(default_settings)
        
        # 检查所有必要的设置项
        required_settings = [
            # 文件类型设置
            'video_extensions',
            'metadata_extensions',
            'tv_folder_keywords',
            'movie_folder_keywords',
            
            # 模板设置
            'movie_template',
            'tv_template',
            'special_template',
            
            # 安全设置
            'security',
            'enable_suspicious_detection',
            'enable_destructive_operation_confirmation',
            'enable_batch_confirmation',
            'confirmation_threshold',
            'confirmation_timeout',
            'forbidden_paths',
            
            # 性能设置
            'performance',
            
            # 日志设置
            'logging',
            'max_errors',
            'enable_logging',
            
            # 缓存设置
            'cache_ttl',
            'cache_max_size_mb',
            'enable_incremental_cache',
            'cache_auto_cleanup',
            
            # 高级设置
            'backup_enabled',
            'backup_interval',
            'performance_monitoring',
            'enable_hash_check',
            'enable_special_check',
            'force_special_season',
            'enable_history',
            'special_keywords',
            'max_file_size_mb',
            'sandbox_directory',
            'auto_cleanup_sandbox',
            'resume_enabled',
            'checkpoint_enabled',
            'batch_mode'
        ]
        
        print("1. 检查设置项完整性...")
        settings = dialog.get_settings()
        
        missing_settings = []
        for setting in required_settings:
            if setting not in settings:
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"   ❌ 缺少设置项: {missing_settings}")
            return False
        else:
            print("   ✅ 所有设置项都存在")
        
        print("2. 检查设置值有效性...")
        # 检查关键设置是否有默认值
        if not settings.get('video_exts'):
            print("   ⚠️ 视频扩展名未设置")
        if not settings.get('movie_template'):
            print("   ⚠️ 电影模板未设置")
        if not settings.get('tv_template'):
            print("   ⚠️ 电视剧模板未设置")
        
        print("   ✅ 设置值检查完成")
        
        print("\n🎉 设置完整性测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 设置完整性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始设置对话框完整性测试")
    print("=" * 50)
    
    # 测试设置对话框
    dialog_ok = test_settings_dialog()
    
    if dialog_ok:
        # 测试设置完整性
        completeness_ok = test_settings_completeness()
        
        if completeness_ok:
            print("\n🎉 设置对话框完整性测试全部通过！")
            print("✅ 对话框功能完整")
            print("✅ 设置项完整")
            print("✅ 可以正常使用")
            return True
        else:
            print("\n❌ 设置完整性测试失败")
            return False
    else:
        print("\n❌ 设置对话框测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 