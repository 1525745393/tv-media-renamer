#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化功能测试脚本
"""

import sys
import os
import logging

# 添加父目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """测试基本模块导入"""
    logger.info("🔍 测试基本模块导入...")
    
    try:
        # 测试核心模块
        from main_window import RenameUI
        logger.info("✅ main_window 导入成功")
        
        from modules.workers import ScanWorker, RenameWorker
        logger.info("✅ workers 导入成功")
        
        from core.constants import DEFAULT_SETTINGS
        logger.info("✅ constants 导入成功")
        
        from enhanced_analyzer import EnhancedAnalyzer
        logger.info("✅ enhanced_analyzer 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 基本模块导入失败: {e}")
        return False

def test_enhanced_analyzer():
    """测试增强分析器"""
    logger.info("🔍 测试增强分析器...")
    
    try:
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
        logger.info(f"   置信度: {result.get('confidence', 0):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 增强分析器测试失败: {e}")
        return False

def test_batch_manager():
    """测试批量操作管理器"""
    logger.info("🔍 测试批量操作管理器...")
    
    try:
        from batch_manager import EnhancedBatchManager
        
        batch_manager = EnhancedBatchManager()
        
        # 模拟文件数据
        test_files = [
            {'file_path': '/test/movie1.mp4', 'type': 'movie', 'title': 'Test Movie 1'},
            {'file_path': '/test/tv1.mp4', 'type': 'tv', 'title': 'Test TV 1'}
        ]
        
        # 测试选择性重命名
        selected_files = batch_manager.selective_rename(test_files, [0])
        logger.info(f"✅ 选择性重命名: 选择了 {len(selected_files)} 个文件")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 批量操作管理器测试失败: {e}")
        return False

def test_operation_history():
    """测试操作历史系统"""
    logger.info("🔍 测试操作历史系统...")
    
    try:
        from core.operation_history import EnhancedOperationHistory, OperationType
        
        history = EnhancedOperationHistory("test_history.json")
        
        # 测试添加操作
        op_id = history.add_operation(
            OperationType.RENAME,
            "/test/original.txt",
            "/test/new.txt",
            "测试重命名操作"
        )
        logger.info(f"✅ 添加操作: {op_id}")
        
        # 测试统计信息
        stats = history.get_statistics()
        logger.info(f"✅ 操作统计: 总操作 {stats['total_operations']} 个")
        
        # 清理测试文件
        if os.path.exists("test_history.json"):
            os.remove("test_history.json")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 操作历史系统测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始简化功能测试...")
    logger.info("=" * 50)
    
    tests = [
        ("基本模块导入", test_basic_imports),
        ("增强分析器", test_enhanced_analyzer),
        ("批量操作管理器", test_batch_manager),
        ("操作历史系统", test_operation_history)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 测试: {test_name}")
        logger.info("-" * 30)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！程序功能正常")
        return 0
    else:
        logger.warning(f"⚠️ 部分测试失败，请检查相关功能")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 