#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全管理器模块
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SecurityManager:
    """安全管理器"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.security_level = settings.get('security_level', 'medium')
        self.max_files_per_operation = settings.get('max_files_per_operation', 1000)
        self.enable_path_validation = settings.get('enable_path_validation', True)
        self.enable_file_size_check = settings.get('enable_file_size_check', True)
        self.enable_suspicious_detection = settings.get('enable_suspicious_detection', True)
        
        # 可疑文件模式
        self.suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
            r'\.com$', r'\.vbs$', r'\.js$', r'\.jar$', r'\.msi$'
        ]
        
        # 危险路径模式
        self.dangerous_paths = [
            r'C:\\Windows', r'C:\\System32', r'C:\\Program Files',
            r'/bin', r'/sbin', r'/usr/bin', r'/usr/sbin', r'/etc'
        ]
    
    def validate_operation(self, directory: str) -> bool:
        """验证操作安全性"""
        try:
            # 检查路径验证
            if self.enable_path_validation and not self._validate_path(directory):
                logger.warning(f"路径验证失败: {directory}")
                return False
            
            # 检查文件数量限制
            if not self._check_file_count_limit(directory):
                logger.warning(f"文件数量超过限制: {directory}")
                return False
            
            # 检查可疑文件
            if self.enable_suspicious_detection and self._has_suspicious_files(directory):
                logger.warning(f"发现可疑文件: {directory}")
                return False
            
            logger.debug(f"操作验证通过: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"操作验证失败: {e}")
            return False
    
    def _validate_path(self, path: str) -> bool:
        """验证路径安全性"""
        try:
            # 检查路径是否存在
            if not os.path.exists(path):
                return False
            
            # 检查路径是否可读
            if not os.access(path, os.R_OK):
                return False
            
            # 检查是否为目录
            if not os.path.isdir(path):
                return False
            
            # 检查是否为危险路径
            import re
            for dangerous_path in self.dangerous_paths:
                if re.search(dangerous_path, path, re.IGNORECASE):
                    logger.warning(f"检测到危险路径: {path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"路径验证错误: {e}")
            return False
    
    def _check_file_count_limit(self, directory: str) -> bool:
        """检查文件数量限制"""
        try:
            file_count = 0
            for root, dirs, files in os.walk(directory):
                file_count += len(files)
                if file_count > self.max_files_per_operation:
                    return False
            return True
            
        except Exception as e:
            logger.error(f"检查文件数量失败: {e}")
            return False
    
    def _has_suspicious_files(self, directory: str) -> bool:
        """检查是否有可疑文件"""
        try:
            import re
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    for pattern in self.suspicious_patterns:
                        if re.search(pattern, file, re.IGNORECASE):
                            logger.warning(f"发现可疑文件: {os.path.join(root, file)}")
                            return True
            return False
            
        except Exception as e:
            logger.error(f"检查可疑文件失败: {e}")
            return False
    
    def validate_file_operation(self, file_path: str, operation: str) -> bool:
        """验证文件操作安全性"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False
            
            # 检查文件大小
            if self.enable_file_size_check:
                file_size = os.path.getsize(file_path)
                max_size = self.settings.get('max_file_size', 10 * 1024 * 1024 * 1024)  # 10GB
                if file_size > max_size:
                    logger.warning(f"文件过大: {file_path} ({file_size} bytes)")
                    return False
            
            # 检查文件权限
            if operation in ['write', 'delete'] and not os.access(file_path, os.W_OK):
                logger.warning(f"文件无写权限: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"文件操作验证失败: {e}")
            return False
    
    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        return {
            'security_level': self.security_level,
            'max_files_per_operation': self.max_files_per_operation,
            'enable_path_validation': self.enable_path_validation,
            'enable_file_size_check': self.enable_file_size_check,
            'enable_suspicious_detection': self.enable_suspicious_detection,
            'suspicious_patterns_count': len(self.suspicious_patterns),
            'dangerous_paths_count': len(self.dangerous_paths)
        } 