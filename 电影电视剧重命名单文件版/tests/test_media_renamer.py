#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MediaRenamer类
"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

try:
    from core.tv_rename_cache_optimized import MediaRenamer
    from core.constants import DEFAULT_SETTINGS
    
    print("✅ 成功导入MediaRenamer和DEFAULT_SETTINGS")
    
    # 创建MediaRenamer实例
    print("🔄 正在创建MediaRenamer实例...")
    renamer = MediaRenamer(DEFAULT_SETTINGS)
    print("✅ MediaRenamer实例创建成功")
    
    # 测试smart_analyze_file方法
    print("🔄 测试smart_analyze_file方法...")
    test_filename = "Avengers.Endgame.2019.mkv"
    test_folder = "test_folder"
    
    result = renamer.smart_analyze_file(test_filename, test_folder)
    print(f"✅ smart_analyze_file方法调用成功，结果: {result}")
    
    print("🎉 所有测试通过！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc() 