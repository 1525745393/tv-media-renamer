#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览和实际重命名一致性测试脚本
"""

import sys
import os
import time
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.workers import ScanWorker
from core.constants import DEFAULT_SETTINGS

def create_test_files():
    """创建测试文件"""
    test_dir = tempfile.mkdtemp(prefix="rename_test_")
    
    # 创建测试文件
    test_files = [
        "Avengers.Endgame.2019.mkv",
        "Game.of.Thrones.S01E01.1080p.BluRay.x264.mp4",
        "权力的游戏.SP01.1080p.mp4",
        "复仇者联盟4：终局之战 (2019).mp4",
        "Game.of.Thrones.S02E01.1080p.BluRay.x264.mp4"
    ]
    
    for filename in test_files:
        file_path = os.path.join(test_dir, filename)
        with open(file_path, 'w') as f:
            f.write(f"Test content for {filename}")
    
    return test_dir, test_files

def test_preview_consistency():
    """测试预览和实际重命名的一致性"""
    print("🧪 预览和实际重命名一致性测试")
    print("=" * 60)
    
    # 创建测试环境
    test_dir, test_files = create_test_files()
    print(f"📁 创建测试目录: {test_dir}")
    print(f"📄 测试文件: {len(test_files)} 个")
    
    try:
        # 配置设置
        settings = DEFAULT_SETTINGS.copy()
        settings['folder_path'] = test_dir
        
        # 第一步：扫描并获取预览结果
        print("\n🔍 第一步：扫描文件获取预览结果")
        scan_worker = ScanWorker(test_dir, settings)
        scan_worker.run()
        
        preview_results = scan_worker._results if hasattr(scan_worker, '_results') else []
        print(f"📊 扫描结果: {len(preview_results)} 个文件")
        
        # 显示预览结果
        print("\n📋 预览结果:")
        for i, result in enumerate(preview_results[:3]):  # 只显示前3个
            print(f"  {i+1}. {result.get('original_name', '未知')} -> {result.get('new_name', '未知')} ({result.get('type', '未知')})")
        
        # 第二步：模拟实际重命名（不实际重命名，只生成新文件名）
        print("\n🔄 第二步：模拟实际重命名")
        
        # 使用相同的文件名生成逻辑
        actual_results = []
        for result in preview_results:
            original_name = result.get('original_name', '')
            file_type = result.get('type', '')
            title = result.get('title', '')
            year = result.get('year', '')
            season = result.get('season')
            episode = result.get('episode')
            
            # 使用与ScanWorker相同的generate_new_filename逻辑
            _, ext = os.path.splitext(original_name)
            
            # 清理标题
            if title:
                import re
                clean_title = re.sub(r'[\\/*?:"<>|$$$$\.\!_]', ' ', title).strip()
                clean_title = re.sub(r'[Ss]\d{2}[ ._]?E\d{2}', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title)
                clean_title = re.sub(r'\[\s*\]', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                title = clean_title
            
            # 生成新文件名
            if file_type == 'movie' and title:
                if year:
                    new_name = f"{title} ({year}){ext}"
                else:
                    new_name = f"{title}{ext}"
            elif file_type == 'tv' and title:
                if season == 0:  # 特辑
                    if episode:
                        episode_str = str(episode).zfill(2)
                        new_name = f"{title}.S00.E{episode_str}{ext}"
                    else:
                        new_name = f"{title}.S00{ext}"
                elif season and episode:
                    season_str = str(season).zfill(2)
                    episode_str = str(episode).zfill(2)
                    new_name = f"{title}.S{season_str}E{episode_str}{ext}"
                elif episode:
                    episode_str = str(episode).zfill(2)
                    new_name = f"{title}.E{episode_str}{ext}"
                else:
                    new_name = f"{title}{ext}"
            elif file_type == 'special' and title:
                if episode:
                    episode_str = str(episode).zfill(2)
                    new_name = f"{title}.S00.E{episode_str}{ext}"
                else:
                    new_name = f"{title}.S00{ext}"
            else:
                new_name = original_name
            
            actual_results.append({
                'original_name': original_name,
                'new_name': new_name,
                'type': file_type
            })
        
        # 显示实际结果
        print("\n📋 实际重命名结果:")
        for i, result in enumerate(actual_results[:3]):  # 只显示前3个
            print(f"  {i+1}. {result.get('original_name', '未知')} -> {result.get('new_name', '未知')} ({result.get('type', '未知')})")
        
        # 第三步：比较结果
        print("\n🔍 第三步：比较预览和实际结果")
        
        if len(preview_results) != len(actual_results):
            print(f"❌ 结果数量不一致: 预览={len(preview_results)}, 实际={len(actual_results)}")
            return False
        
        inconsistencies = []
        for i, (preview, actual) in enumerate(zip(preview_results, actual_results)):
            preview_name = preview.get('new_name', '')
            actual_name = actual.get('new_name', '')
            
            if preview_name != actual_name:
                inconsistencies.append({
                    'index': i,
                    'original': preview.get('original_name', ''),
                    'preview': preview_name,
                    'actual': actual_name
                })
        
        # 显示比较结果
        if not inconsistencies:
            print("✅ 预览和实际重命名完全一致！")
            print(f"📊 测试文件数: {len(preview_results)}")
            return True
        else:
            print(f"❌ 发现 {len(inconsistencies)} 个不一致:")
            for inc in inconsistencies:
                print(f"  文件 {inc['index']+1}: {inc['original']}")
                print(f"    预览: {inc['preview']}")
                print(f"    实际: {inc['actual']}")
                print()
            return False
    
    finally:
        # 清理测试环境
        print(f"\n🧹 清理测试目录: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)

def test_template_consistency():
    """测试模板设置的一致性"""
    print("\n🧪 模板设置一致性测试")
    print("=" * 60)
    
    # 测试不同的模板设置
    test_cases = [
        {
            'name': '默认模板',
            'settings': DEFAULT_SETTINGS.copy()
        },
        {
            'name': '自定义电影模板',
            'settings': {
                **DEFAULT_SETTINGS,
                'movie_template': '{title} [{year}]{ext}'
            }
        },
        {
            'name': '自定义电视剧模板',
            'settings': {
                **DEFAULT_SETTINGS,
                'tv_template': '{title} - S{season:02d}E{episode:02d}{ext}'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 测试: {test_case['name']}")
        print(f"   电影模板: {test_case['settings']['movie_template']}")
        print(f"   电视剧模板: {test_case['settings']['tv_template']}")
        print(f"   特辑模板: {test_case['settings']['special_template']}")

if __name__ == "__main__":
    # 运行一致性测试
    success = test_preview_consistency()
    
    # 运行模板测试
    test_template_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 预览和实际重命名一致性测试通过")
    else:
        print("❌ 预览和实际重命名一致性测试失败")
    print("=" * 60) 