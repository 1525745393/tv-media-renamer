#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速功能测试
"""

import sys
import os
import logging

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试模块导入"""
    try:
        logger.info("🔍 测试模块导入...")
        
        # 测试核心模块
        from ui.main_window import RenameUI
        logger.info("✅ main_window 导入成功")
        
        from modules.enhanced_analyzer import EnhancedAnalyzer
        logger.info("✅ enhanced_analyzer 导入成功")
        
        from modules.batch_manager import EnhancedBatchManager
        logger.info("✅ batch_manager 导入成功")
        
        from core.operation_history import EnhancedOperationHistory
        logger.info("✅ operation_history 导入成功")
        
        from core.constants import DEFAULT_SETTINGS
        logger.info("✅ constants 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False

def test_analyzer():
    """测试分析器"""
    try:
        logger.info("🔍 测试分析器...")
        
        from modules.enhanced_analyzer import EnhancedAnalyzer
        from core.constants import DEFAULT_SETTINGS
        
        analyzer = EnhancedAnalyzer(DEFAULT_SETTINGS)
        
        # 测试文件分析
        test_file = "Avengers.Endgame.2019.1080p.BluRay.x264.mkv"
        result = analyzer.analyze_file(test_file)
        
        logger.info(f"✅ 分析文件: {test_file}")
        logger.info(f"   标题: {result.get('title', 'N/A')}")
        logger.info(f"   年份: {result.get('year', 'N/A')}")
        logger.info(f"   类型: {result.get('file_type', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分析器测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始快速测试...")
    
    tests = [
        ("模块导入", test_imports),
        ("分析器功能", test_analyzer)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 测试: {test_name}")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} 通过")
        else:
            logger.error(f"❌ {test_name} 失败")
    
    logger.info(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！程序可以正常运行")
        return 0
    else:
        logger.error("❌ 部分测试失败，程序可能有问题")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 