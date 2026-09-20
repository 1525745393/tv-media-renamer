#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件类型检查选项测试脚本
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.workers import ScanWorker
from core.constants import DEFAULT_SETTINGS

def test_file_type_options():
    """测试文件类型检查选项"""
    print("🧪 文件类型检查选项测试")
    print("=" * 50)
    
    # 测试文件夹
    test_folder = "test_data/test_media_folder"
    if not os.path.exists(test_folder):
        print(f"❌ 测试文件夹不存在: {test_folder}")
        return
    
    # 测试不同配置
    test_configs = [
        {
            'name': '默认配置（全部启用）',
            'settings': {
                **DEFAULT_SETTINGS,
                'enable_movie_check': True,
                'enable_tv_check': True,
                'enable_special_check': True,
                'force_movie_rules': False,
                'force_tv_rules': False
            }
        },
        {
            'name': '仅检查电影',
            'settings': {
                **DEFAULT_SETTINGS,
                'enable_movie_check': True,
                'enable_tv_check': False,
                'enable_special_check': False,
                'force_movie_rules': False,
                'force_tv_rules': False
            }
        },
        {
            'name': '仅检查电视剧',
            'settings': {
                **DEFAULT_SETTINGS,
                'enable_movie_check': False,
                'enable_tv_check': True,
                'enable_special_check': False,
                'force_movie_rules': False,
                'force_tv_rules': False
            }
        },
        {
            'name': '强制电影规则',
            'settings': {
                **DEFAULT_SETTINGS,
                'enable_movie_check': True,
                'enable_tv_check': True,
                'enable_special_check': True,
                'force_movie_rules': True,
                'force_tv_rules': False
            }
        },
        {
            'name': '强制电视剧规则',
            'settings': {
                **DEFAULT_SETTINGS,
                'enable_movie_check': True,
                'enable_tv_check': True,
                'enable_special_check': True,
                'force_movie_rules': False,
                'force_tv_rules': True
            }
        }
    ]
    
    for config in test_configs:
        print(f"\n📊 测试配置: {config['name']}")
        print(f"   检查电影: {config['settings']['enable_movie_check']}")
        print(f"   检查电视剧: {config['settings']['enable_tv_check']}")
        print(f"   检查特辑: {config['settings']['enable_special_check']}")
        print(f"   强制电影规则: {config['settings']['force_movie_rules']}")
        print(f"   强制电视剧规则: {config['settings']['force_tv_rules']}")
        
        # 创建扫描工作线程
        scan_worker = ScanWorker(test_folder, config['settings'])
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行扫描
        scan_worker.run()
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 获取结果
        results = scan_worker._results if hasattr(scan_worker, '_results') else []
        
        # 统计文件类型
        type_counts = {}
        for result in results:
            file_type = result.get('type', '未知')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        print(f"   ⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"   📁 结果数: {len(results)}")
        print(f"   📊 文件类型分布:")
        for file_type, count in type_counts.items():
            print(f"      • {file_type}: {count} 个")
        
        # 显示前3个结果
        if results:
            print(f"   📋 前3个结果:")
            for i, result in enumerate(results[:3]):
                print(f"      {i+1}. {result.get('original_name', '未知')} -> {result.get('new_name', '未知')} ({result.get('type', '未知')})")
    
    print("\n" + "=" * 50)
    print("✅ 文件类型检查选项测试完成")

if __name__ == "__main__":
    test_file_type_options() 