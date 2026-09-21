#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果
"""

import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试模块导入"""
    try:
        logger.info("🔍 测试模块导入...")
        
        # 测试核心模块
        from main_window import RenameUI
        logger.info("✅ main_window 导入成功")
        
        from enhanced_analyzer import EnhancedAnalyzer
        logger.info("✅ enhanced_analyzer 导入成功")
        
        from batch_manager import EnhancedBatchManager
        logger.info("✅ batch_manager 导入成功")
        
        from operation_history import EnhancedOperationHistory
        logger.info("✅ operation_history 导入成功")
        
        from smart_analysis_dialog import SmartAnalysisDialog
        logger.info("✅ smart_analysis_dialog 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False

def test_initialization():
    """测试初始化"""
    try:
        logger.info("🔍 测试初始化...")
        
        from core.constants import DEFAULT_SETTINGS
        from enhanced_analyzer import EnhancedAnalyzer
        from batch_manager import EnhancedBatchManager
        from operation_history import EnhancedOperationHistory
        
        # 测试EnhancedAnalyzer初始化
        analyzer = EnhancedAnalyzer(DEFAULT_SETTINGS)
        logger.info("✅ EnhancedAnalyzer 初始化成功")
        
        # 测试EnhancedBatchManager初始化
        batch_manager = EnhancedBatchManager()
        logger.info("✅ EnhancedBatchManager 初始化成功")
        
        # 测试EnhancedOperationHistory初始化
        history = EnhancedOperationHistory("test_history.json", 100)
        logger.info("✅ EnhancedOperationHistory 初始化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始测试修复效果...")
    
    tests = [
        ("模块导入", test_imports),
        ("初始化测试", test_initialization)
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
        logger.info("🎉 所有测试通过！修复成功")
        return 0
    else:
        logger.error("❌ 部分测试失败，需要进一步修复")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 