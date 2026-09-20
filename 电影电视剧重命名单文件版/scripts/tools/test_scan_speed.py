#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描速度测试脚本
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.workers import ScanWorker
from core.constants import DEFAULT_SETTINGS

def test_scan_speed():
    """测试扫描速度"""
    print("🚀 扫描速度优化测试")
    print("=" * 50)
    
    # 测试文件夹
    test_folder = "test_data/test_media_folder"
    if not os.path.exists(test_folder):
        print(f"❌ 测试文件夹不存在: {test_folder}")
        return
    
    # 测试设置
    settings = DEFAULT_SETTINGS.copy()
    
    # 测试不同配置
    test_configs = [
        {
            'name': '默认配置',
            'settings': settings.copy()
        },
        {
            'name': '优化配置',
            'settings': {
                **settings,
                'max_workers': 8,
                'chunk_size': 100,
                'fast_mode': True
            }
        },
        {
            'name': '高性能配置',
            'settings': {
                **settings,
                'max_workers': 12,
                'chunk_size': 200,
                'fast_mode': True
            }
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n📊 测试配置: {config['name']}")
        print(f"   最大线程数: {config['settings']['max_workers']}")
        print(f"   批处理大小: {config['settings']['chunk_size']}")
        print(f"   快速模式: {config['settings']['fast_mode']}")
        
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
        results_count = len(scan_worker._results) if hasattr(scan_worker, '_results') else 0
        
        # 计算速度
        speed = results_count / elapsed_time if elapsed_time > 0 else 0
        
        result = {
            'config_name': config['name'],
            'elapsed_time': elapsed_time,
            'results_count': results_count,
            'speed': speed
        }
        results.append(result)
        
        print(f"   ⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"   📁 结果数: {results_count}")
        print(f"   ⚡ 速度: {speed:.1f} 文件/秒")
    
    # 显示对比结果
    print("\n" + "=" * 50)
    print("📈 性能对比结果")
    print("=" * 50)
    
    baseline = results[0]
    for result in results:
        if result == baseline:
            print(f"{result['config_name']}: {result['speed']:.1f} 文件/秒 (基准)")
        else:
            improvement = (result['speed'] / baseline['speed'] - 1) * 100
            print(f"{result['config_name']}: {result['speed']:.1f} 文件/秒 ({improvement:+.1f}%)")
    
    # 推荐配置
    best_result = max(results, key=lambda x: x['speed'])
    print(f"\n🏆 推荐配置: {best_result['config_name']}")
    print(f"   速度: {best_result['speed']:.1f} 文件/秒")
    print(f"   耗时: {best_result['elapsed_time']:.2f} 秒")

if __name__ == "__main__":
    test_scan_speed() 