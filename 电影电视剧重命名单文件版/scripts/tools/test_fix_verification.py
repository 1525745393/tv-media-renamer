#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复验证测试脚本
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tv_rename_cache_optimized import MediaRenamer, PatternRecognizer
from core.constants import DEFAULT_SETTINGS

def test_regex_fix():
    """测试正则表达式修复"""
    print("🧪 正则表达式修复验证")
    print("=" * 50)
    
    # 测试PatternRecognizer
    recognizer = PatternRecognizer()
    
    # 测试文件名
    test_files = [
        "WDNYM.2023.EP15.HD1080P.X264.AAC.Mandarin.CHS.BDYS.mp4",
        "NRJLB.2023.EP12.HD1080P.X264.AAC.Mandarin.CHS.BDYS.mp4",
        "Game.of.Thrones.S01E01.1080p.BluRay.x264.mp4",
        "Avengers.Endgame.2019.mkv",
        "权力的游戏.SP01.1080p.mp4"
    ]
    
    print("测试extract_season_episode_optimized方法:")
    for filename in test_files:
        try:
            season, episode, reason = recognizer.extract_season_episode_optimized(filename)
            print(f"  ✅ {filename}")
            print(f"     季数: {season}, 集数: {episode}, 原因: {reason}")
        except Exception as e:
            print(f"  ❌ {filename}: {e}")
    
    print("\n测试analyze_filename方法:")
    for filename in test_files:
        try:
            result = recognizer.analyze_filename(filename)
            print(f"  ✅ {filename}")
            print(f"     类型: {result.get('type')}, 置信度: {result.get('confidence')}")
            print(f"     标题: {result.get('title')}")
        except Exception as e:
            print(f"  ❌ {filename}: {e}")

def test_media_renamer():
    """测试MediaRenamer错误处理"""
    print("\n🧪 MediaRenamer错误处理验证")
    print("=" * 50)
    
    try:
        settings = DEFAULT_SETTINGS.copy()
        renamer = MediaRenamer(settings)
        print("✅ MediaRenamer初始化成功")
        
        # 测试错误处理
        test_filename = "test_file.mp4"
        test_folder = "test_folder"
        
        try:
            result = renamer.smart_analyze_file(test_filename, test_folder)
            print(f"✅ smart_analyze_file调用成功: {result.get('type')}")
        except Exception as e:
            print(f"❌ smart_analyze_file调用失败: {e}")
        
        # 测试错误处理器
        if hasattr(renamer, 'error_handler'):
            print("✅ error_handler属性存在")
            summary = renamer.error_handler.get_error_summary()
            print(f"✅ 错误摘要获取成功: {summary}")
        else:
            print("❌ error_handler属性不存在")
            
    except Exception as e:
        print(f"❌ MediaRenamer测试失败: {e}")

def test_network_path():
    """测试网络路径处理"""
    print("\n🧪 网络路径处理验证")
    print("=" * 50)
    
    network_path = r"\\Nas\nas2\video2\精选电视剧2"
    
    if os.path.exists(network_path):
        print(f"✅ 网络路径可访问: {network_path}")
        
        try:
            settings = DEFAULT_SETTINGS.copy()
            settings['preview_only'] = True
            settings['folder_path'] = network_path
            
            renamer = MediaRenamer(settings)
            print("✅ MediaRenamer网络路径初始化成功")
            
            # 测试单个文件分析
            test_file = "WDNYM.2023.EP15.HD1080P.X264.AAC.Mandarin.CHS.BDYS.mp4"
            result = renamer.smart_analyze_file(test_file, network_path)
            print(f"✅ 文件分析成功: {result.get('type')}")
            
        except Exception as e:
            print(f"❌ 网络路径处理失败: {e}")
    else:
        print(f"❌ 网络路径不可访问: {network_path}")

if __name__ == "__main__":
    test_regex_fix()
    test_media_renamer()
    test_network_path()
    
    print("\n🎉 修复验证完成！") 