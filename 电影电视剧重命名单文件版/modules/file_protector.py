#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件保护模块 - 影视文件重命名工具 v1.3
"""

import os
import shutil
import stat
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class FileProtector:
    """文件保护类"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.protected_extensions = settings.get("protected_extensions", [
            '.exe', '.dll', '.sys', '.bat', '.cmd', '.com', '.scr', '.pif'
        ])
        self.protected_directories = settings.get("protected_directories", [
            'C:\\Windows', 'C:\\System32', 'C:\\Program Files', 'C:\\Program Files (x86)'
        ])
        self.backup_enabled = settings.get("backup_enabled", True)
        self.backup_dir = settings.get("backup_dir", ".backups")
        self.max_backup_size_mb = settings.get("max_backup_size_mb", 1000)
        
        # 确保备份目录存在
        if self.backup_enabled:
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def is_file_protected(self, file_path: str) -> Tuple[bool, str]:
        """检查文件是否受保护"""
        try:
            file_path = os.path.abspath(file_path)
            
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path)
            if ext.lower() in self.protected_extensions:
                return True, f"文件扩展名 {ext} 受保护"
            
            # 检查是否在受保护目录中
            for protected_dir in self.protected_directories:
                if file_path.startswith(protected_dir):
                    return True, f"文件位于受保护目录: {protected_dir}"
            
            # 检查系统文件
            if self._is_system_file(file_path):
                return True, "系统文件受保护"
            
            # 检查隐藏文件
            if self._is_hidden_file(file_path):
                return True, "隐藏文件受保护"
            
            # 检查只读文件
            if self._is_readonly_file(file_path):
                return True, "只读文件受保护"
            
            return False, "文件可以操作"
            
        except Exception as e:
            logger.error(f"检查文件保护状态失败: {e}")
            return True, f"检查失败: {str(e)}"
    
    def _is_system_file(self, file_path: str) -> bool:
        """检查是否为系统文件"""
        try:
            # 检查文件属性
            attrs = os.stat(file_path).st_file_attributes
            return bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)
        except:
            return False
    
    def _is_hidden_file(self, file_path: str) -> bool:
        """检查是否为隐藏文件"""
        try:
            # 检查文件属性
            attrs = os.stat(file_path).st_file_attributes
            return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
        except:
            return False
    
    def _is_readonly_file(self, file_path: str) -> bool:
        """检查是否为只读文件"""
        try:
            # 检查文件权限
            mode = os.stat(file_path).st_mode
            return not bool(mode & stat.S_IWRITE)
        except:
            return False
    
    def check_file_permissions(self, file_path: str) -> Tuple[bool, str]:
        """检查文件权限"""
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查读取权限
            if not os.access(file_path, os.R_OK):
                return False, "没有读取权限"
            
            # 检查写入权限
            if not os.access(file_path, os.W_OK):
                return False, "没有写入权限"
            
            # 检查目录权限
            dir_path = os.path.dirname(file_path)
            if not os.access(dir_path, os.W_OK):
                return False, "目录没有写入权限"
            
            return True, "权限检查通过"
            
        except Exception as e:
            logger.error(f"检查文件权限失败: {e}")
            return False, f"权限检查失败: {str(e)}"
    
    def check_disk_space(self, file_path: str, operation_type: str = "rename") -> Tuple[bool, str]:
        """检查磁盘空间"""
        try:
            dir_path = os.path.dirname(file_path)
            
            # 获取磁盘使用情况
            total, used, free = shutil.disk_usage(dir_path)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 根据操作类型计算所需空间
            required_space = file_size
            if operation_type == "backup":
                required_space *= 2  # 备份需要额外空间
            elif operation_type == "move":
                required_space = file_size  # 移动不需要额外空间
            
            # 检查可用空间
            if free < required_space:
                return False, f"磁盘空间不足，需要 {required_space / 1024 / 1024:.1f} MB，可用 {free / 1024 / 1024:.1f} MB"
            
            return True, f"磁盘空间充足，可用 {free / 1024 / 1024:.1f} MB"
            
        except Exception as e:
            logger.error(f"检查磁盘空间失败: {e}")
            return False, f"磁盘空间检查失败: {str(e)}"
    
    def create_backup(self, file_path: str) -> Tuple[bool, str]:
        """创建文件备份"""
        if not self.backup_enabled:
            return True, "备份功能已禁用"
        
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 检查备份目录大小
            if not self._check_backup_size():
                return False, "备份目录空间不足"
            
            # 创建备份
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"文件备份已创建: {backup_path}")
            return True, backup_path
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False, f"备份失败: {str(e)}"
    
    def _check_backup_size(self) -> bool:
        """检查备份目录大小"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            max_size = self.max_backup_size_mb * 1024 * 1024
            return total_size < max_size
            
        except Exception as e:
            logger.error(f"检查备份目录大小失败: {e}")
            return False
    
    def cleanup_old_backups(self, max_age_days: int = 30) -> int:
        """清理旧备份文件"""
        try:
            cleaned_count = 0
            current_time = datetime.now()
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_days = (current_time - mtime).days
                    
                    if age_days > max_age_days:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"清理旧备份: {filename}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
            return 0
    
    def validate_file_integrity(self, file_path: str) -> Tuple[bool, str]:
        """验证文件完整性"""
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "文件大小为0"
            
            # 检查文件是否可读
            try:
                with open(file_path, 'rb') as f:
                    # 读取文件头部来验证文件完整性
                    header = f.read(1024)
                    if not header:
                        return False, "文件无法读取"
            except Exception as e:
                return False, f"文件读取失败: {str(e)}"
            
            return True, "文件完整性验证通过"
            
        except Exception as e:
            logger.error(f"验证文件完整性失败: {e}")
            return False, f"完整性验证失败: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件详细信息"""
        try:
            stat_info = os.stat(file_path)
            
            return {
                'path': file_path,
                'size': stat_info.st_size,
                'size_mb': stat_info.st_size / 1024 / 1024,
                'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'is_readonly': not bool(stat_info.st_mode & stat.S_IWRITE),
                'is_hidden': bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) if hasattr(stat_info, 'st_file_attributes') else False,
                'is_system': bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM) if hasattr(stat_info, 'st_file_attributes') else False,
                'extension': os.path.splitext(file_path)[1].lower(),
                'filename': os.path.basename(file_path),
                'directory': os.path.dirname(file_path)
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {'error': str(e)}
    
    def safe_rename(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """安全重命名文件"""
        try:
            # 检查源文件
            protected, reason = self.is_file_protected(old_path)
            if protected:
                return False, f"源文件受保护: {reason}"
            
            # 检查权限
            has_permission, reason = self.check_file_permissions(old_path)
            if not has_permission:
                return False, f"权限不足: {reason}"
            
            # 检查磁盘空间
            has_space, reason = self.check_disk_space(old_path, "rename")
            if not has_space:
                return False, f"磁盘空间不足: {reason}"
            
            # 验证文件完整性
            is_valid, reason = self.validate_file_integrity(old_path)
            if not is_valid:
                return False, f"文件完整性验证失败: {reason}"
            
            # 创建备份
            if self.backup_enabled:
                backup_success, backup_result = self.create_backup(old_path)
                if not backup_success:
                    return False, f"备份失败: {backup_result}"
            
            # 检查目标路径
            if os.path.exists(new_path):
                return False, "目标文件已存在"
            
            # 执行重命名
            os.rename(old_path, new_path)
            
            logger.info(f"文件重命名成功: {old_path} -> {new_path}")
            return True, "重命名成功"
            
        except Exception as e:
            logger.error(f"安全重命名失败: {e}")
            return False, f"重命名失败: {str(e)}"
    
    def get_protection_summary(self, file_paths: List[str]) -> Dict[str, Any]:
        """获取文件保护摘要"""
        summary = {
            'total_files': len(file_paths),
            'protected_files': 0,
            'accessible_files': 0,
            'backup_created': 0,
            'errors': []
        }
        
        for file_path in file_paths:
            try:
                # 检查保护状态
                protected, reason = self.is_file_protected(file_path)
                if protected:
                    summary['protected_files'] += 1
                    summary['errors'].append(f"受保护: {file_path} - {reason}")
                else:
                    summary['accessible_files'] += 1
                
                # 检查是否可以创建备份
                if self.backup_enabled and not protected:
                    backup_success, _ = self.create_backup(file_path)
                    if backup_success:
                        summary['backup_created'] += 1
                
            except Exception as e:
                summary['errors'].append(f"检查失败: {file_path} - {str(e)}")
        
        return summary 