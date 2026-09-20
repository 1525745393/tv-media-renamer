#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控器模块
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.operations = {}
        self.start_times = {}
        self.operation_stats = {}
    
    def start_operation(self, operation_name: str):
        """开始监控操作"""
        self.start_times[operation_name] = time.time()
        logger.debug(f"开始监控操作: {operation_name}")
    
    def end_operation(self, operation_name: str, success: bool = True):
        """结束监控操作"""
        if operation_name in self.start_times:
            end_time = time.time()
            duration = end_time - self.start_times[operation_name]
            
            if operation_name not in self.operation_stats:
                self.operation_stats[operation_name] = {
                    'count': 0,
                    'total_time': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'last_time': 0
                }
            
            stats = self.operation_stats[operation_name]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['last_time'] = duration
            
            if success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            if duration < stats['min_time']:
                stats['min_time'] = duration
            if duration > stats['max_time']:
                stats['max_time'] = duration
            
            logger.debug(f"操作完成: {operation_name}, 耗时: {duration:.3f}秒")
            
            # 清理开始时间
            del self.start_times[operation_name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            'total_operations': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'success_rate': 0.0,
            'memory_usage': 0.0,
            'cache_efficiency': 0.0,
            'operations': {}
        }
        
        total_ops = 0
        total_time = 0.0
        total_success = 0
        
        for op_name, stats in self.operation_stats.items():
            total_ops += stats['count']
            total_time += stats['total_time']
            total_success += stats['success_count']
            
            if stats['count'] > 0:
                avg_time = stats['total_time'] / stats['count']
                success_rate = stats['success_count'] / stats['count']
            else:
                avg_time = 0.0
                success_rate = 0.0
            
            summary['operations'][op_name] = {
                'count': stats['count'],
                'total_time': stats['total_time'],
                'average_time': avg_time,
                'success_rate': success_rate,
                'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                'max_time': stats['max_time'],
                'last_time': stats['last_time']
            }
        
        summary['total_operations'] = total_ops
        summary['total_time'] = total_time
        summary['average_time'] = total_time / total_ops if total_ops > 0 else 0.0
        summary['success_rate'] = total_success / total_ops if total_ops > 0 else 0.0
        
        # 获取内存使用情况
        try:
            import psutil
            process = psutil.Process()
            summary['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            summary['memory_usage'] = 0.0
        
        return summary
    
    def get_operation_time(self, operation_name: str) -> float:
        """获取操作耗时"""
        if operation_name in self.operation_stats:
            stats = self.operation_stats[operation_name]
            return stats['last_time'] if stats['count'] > 0 else 0.0
        return 0.0
    
    def reset(self):
        """重置性能统计"""
        self.operations.clear()
        self.start_times.clear()
        self.operation_stats.clear()
        logger.info("性能监控器已重置")
    
    def generate_report(self, report_file: Optional[str] = None) -> str:
        """生成性能报告"""
        summary = self.get_performance_summary()
        
        report = f"""
性能监控报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

总体统计:
- 总操作数: {summary['total_operations']}
- 总耗时: {summary['total_time']:.3f}秒
- 平均耗时: {summary['average_time']:.3f}秒
- 成功率: {summary['success_rate']:.1%}
- 内存使用: {summary['memory_usage']:.1f}MB

详细操作统计:
"""
        
        for op_name, stats in summary['operations'].items():
            report += f"""
{op_name}:
  - 执行次数: {stats['count']}
  - 总耗时: {stats['total_time']:.3f}秒
  - 平均耗时: {stats['average_time']:.3f}秒
  - 最短耗时: {stats['min_time']:.3f}秒
  - 最长耗时: {stats['max_time']:.3f}秒
  - 成功率: {stats['success_rate']:.1%}
"""
        
        if report_file:
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"性能报告已保存到: {report_file}")
            except Exception as e:
                logger.error(f"保存性能报告失败: {e}")
        
        return report 