#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速扫描测试 - 验证优化效果
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.workers import ScanWorker
from core.constants import DEFAULT_SETTINGS

def quick_test():
    """快速测试扫描速度"""
    print("🚀 快速扫描测试")
    print("=" * 40)
    
    # 测试文件夹
    test_folder = "test_data/test_media_folder"
    if not os.path.exists(test_folder):
        print(f"❌ 测试文件夹不存在: {test_folder}")
        return
    
    # 使用优化配置
    settings = DEFAULT_SETTINGS.copy()
    settings.update({
        'max_workers': 8,
        'chunk_size': 100,
        'fast_mode': True
    })
    
    print(f"📁 测试文件夹: {test_folder}")
    print(f"⚙️  配置: {settings['max_workers']}线程, {settings['chunk_size']}批处理, 快速模式")
    print()
    
    # 创建扫描工作线程
    scan_worker = ScanWorker(test_folder, settings)
    
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
    
    print("📊 测试结果:")
    print(f"   ⏱️  耗时: {elapsed_time:.2f} 秒")
    print(f"   📁 结果数: {results_count}")
    print(f"   ⚡ 速度: {speed:.1f} 文件/秒")
    
    if speed > 10:
        print("✅ 扫描速度优化成功！")
    else:
        print("⚠️  扫描速度需要进一步优化")
    
    # 显示扫描到的文件
    if results_count > 0:
        print(f"\n📋 扫描到的文件:")
        for i, result in enumerate(scan_worker._results[:5]):  # 显示前5个
            print(f"   {i+1}. {result.get('original_name', '未知')} -> {result.get('new_name', '未知')}")
        if results_count > 5:
            print(f"   ... 还有 {results_count - 5} 个文件")

if __name__ == "__main__":
    quick_test() 