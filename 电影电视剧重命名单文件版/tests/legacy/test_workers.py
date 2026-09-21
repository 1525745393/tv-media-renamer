#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试workers模块
"""

import sys
import os

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.tv_rename_cache_optimized import MediaRenamer
    from core.constants import DEFAULT_SETTINGS
    
    print("✅ 成功导入MediaRenamer和DEFAULT_SETTINGS")
    
    # 创建MediaRenamer实例
    renamer = MediaRenamer(DEFAULT_SETTINGS)
    print("✅ 成功创建MediaRenamer实例")
    
    print("✅ 测试通过")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc() 