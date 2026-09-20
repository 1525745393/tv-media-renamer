#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作线程模块 - 影视文件重命名工具 v1.3
"""

import os
import time
import logging
import hashlib
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QThread, pyqtSignal
from core.tv_rename_cache_optimized import MediaRenamer

logger = logging.getLogger(__name__)


class SmartCache:
    """智能缓存类"""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
        self.file_hashes = {}
    
    def get_file_hash(self, file_path: str) -> str:
        """获取文件哈希值"""
        try:
            stat = os.stat(file_path)
            # 使用文件大小和修改时间作为简单哈希
            hash_input = f"{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception:
            return ""
    
    def get_cached_result(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if file_path not in self.cache:
            return None
        
        cache_entry = self.cache[file_path]
        current_time = time.time()
        
        # 检查是否过期
        if current_time - cache_entry['timestamp'] > self.ttl:
            del self.cache[file_path]
            return None
        
        # 检查文件是否被修改
        current_hash = self.get_file_hash(file_path)
        if current_hash != cache_entry['file_hash']:
            del self.cache[file_path]
            return None
        
        return cache_entry['result']
    
    def set_cached_result(self, file_path: str, result: Dict[str, Any]) -> None:
        """设置缓存结果"""
        self.cache[file_path] = {
            'result': result,
            'timestamp': time.time(),
            'file_hash': self.get_file_hash(file_path)
        }
    
    def clear_expired(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'total_entries': len(self.cache),
            'cache_size_mb': sum(len(str(entry)) for entry in self.cache.values()) / 1024 / 1024
        }


class ScanWorker(QThread):
    """扫描工作线程"""
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    eta_updated = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    
    def __init__(self, folder_path: str, settings: Dict[str, Any]) -> None:
        super().__init__()
        self.folder_path = folder_path
        self.settings = settings
        self._cancelled = False
        self._results = []  # 存储扫描结果
        self.cache = SmartCache(settings.get("cache_ttl", 3600))
        # 优化：增加并行线程数，使用CPU核心数
        self.max_workers = min(settings.get("max_workers", 8), os.cpu_count() or 8)
        # 优化：增加批量处理文件数
        self.chunk_size = settings.get("chunk_size", 100)
        # 优化：启用快速模式
        self.fast_mode = settings.get("fast_mode", True)
        
    def cancel(self) -> None:
        """取消扫描"""
        self._cancelled = True
        
    def run(self) -> None:
        """执行扫描"""
        try:
            logger.info(f"开始扫描文件夹: {self.folder_path}")
            
            # 初始化开始时间
            self.start_time = time.time()
            
            if not os.path.exists(self.folder_path):
                self.error_occurred.emit("选择的文件夹不存在")
                return
                
            if not os.path.isdir(self.folder_path):
                self.error_occurred.emit("选择的路径不是文件夹")
                return
            
            # 获取所有文件
            all_files = []
            for root, dirs, files in os.walk(self.folder_path):
                if self._cancelled:
                    return
                    
                for file in files:
                    if self._cancelled:
                        return
                        
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            
            # 优化：快速过滤文件
            allowed_extensions = set(self.settings.get("video_extensions", [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]))
            exclude_patterns = self.settings.get("exclude_patterns", ["sample", "trailer", "preview"])
            
            media_files = []
            for i, file_path in enumerate(all_files):
                if self._cancelled:
                    return
                    
                # 更新进度
                progress = int((i + 1) / len(all_files) * 100)
                self.progress_updated.emit(progress)
                
                # 更新当前文件
                self.current_file_changed.emit(os.path.basename(file_path))
                
                # 快速检查文件扩展名
                _, ext = os.path.splitext(file_path)
                if ext.lower() not in allowed_extensions:
                    continue
                
                # 快速检查排除模式
                filename_lower = os.path.basename(file_path).lower()
                if any(pattern.lower() in filename_lower for pattern in exclude_patterns):
                    continue
                
                media_files.append(file_path)
                
                # 计算ETA
                if i > 0:
                    elapsed_time = time.time() - self.start_time
                    avg_time_per_file = elapsed_time / (i + 1)
                    remaining_files = len(all_files) - (i + 1)
                    eta_seconds = avg_time_per_file * remaining_files
                    eta_str = self.format_time(eta_seconds)
                    self.eta_updated.emit(f"预计剩余时间: {eta_str}")
            
            # 并行分析文件
            results = self.analyze_files_parallel(media_files)
            self._results = results  # 保存结果到实例变量
            
            logger.info(f"扫描完成，找到 {len(results)} 个媒体文件")
            self.scan_completed.emit(results)
            
        except Exception as e:
            logger.error(f"扫描过程中发生错误: {e}")
            self.error_occurred.emit(f"扫描失败: {str(e)}")
    
    def analyze_files_parallel(self, media_files: List[str]) -> List[Dict[str, Any]]:
        """并行分析文件（优化版）"""
        results = []
        try:
            renamer = MediaRenamer(self.settings)
        except Exception as e:
            logger.error(f"创建MediaRenamer实例失败: {e}")
            # 使用默认设置创建实例
            default_settings = {
                'video_exts': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'],
                'meta_exts': ['.srt', '.ass', '.ssa', '.sub', '.idx', '.nfo'],
                'movie_template': '{title} ({year}){ext}',
                'tv_template': '{title}.S{season:02d}E{episode:02d}{ext}',
                'special_template': '{title}.特别篇.E{episode:02d}{ext}',
                'max_errors': 100
            }
            renamer = MediaRenamer(default_settings)
        
        # 优化：分批处理文件，减少内存占用
        chunks = [media_files[i:i + self.chunk_size] for i in range(0, len(media_files), self.chunk_size)]
        
        logger.info(f"📊 并行扫描优化: {len(media_files)}个文件，{len(chunks)}个批次，{self.max_workers}个线程")
        
        # 使用线程池进行并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 分批提交任务
            for chunk_index, chunk in enumerate(chunks):
                if self._cancelled:
                    break
                
                logger.info(f"🔄 处理批次 {chunk_index + 1}/{len(chunks)} ({len(chunk)}个文件)")
                
                # 提交当前批次的任务
                future_to_file = {
                    executor.submit(self.analyze_single_file, file_path, renamer): file_path
                    for file_path in chunk
                }
                
                completed_in_chunk = 0
                last_file_path = ""  # 初始化文件路径变量
                for future in as_completed(future_to_file):
                    if self._cancelled:
                        break
                    
                    file_path = future_to_file[future]
                    last_file_path = file_path  # 保存最后一个处理的文件路径
                    try:
                        result = future.result(timeout=30)  # 添加超时控制
                        if result:
                            results.append(result)
                        completed_in_chunk += 1
                    except Exception as e:
                        logger.error(f"分析文件失败 {file_path}: {e}")
                        error_result = {
                            'original_name': os.path.basename(file_path),
                            'file_path': file_path,
                            'type': '未知',
                            'status': '分析失败',
                            'error': str(e)
                        }
                        results.append(error_result)
                        completed_in_chunk += 1
                
                # 更新进度
                total_completed = (chunk_index * self.chunk_size) + completed_in_chunk
                progress = int(total_completed / len(media_files) * 100)
                self.progress_updated.emit(progress)
                if last_file_path:  # 使用保存的文件路径
                    self.current_file_changed.emit(os.path.basename(last_file_path))
        
        return results
    
    def analyze_single_file(self, file_path: str, renamer: MediaRenamer) -> Optional[Dict[str, Any]]:
        """分析单个文件（优化版）"""
        try:
            # 检查缓存
            cached_result = self.cache.get_cached_result(file_path)
            if cached_result:
                return cached_result
            
            # 快速预检查
            filename = os.path.basename(file_path)
            if self._should_skip_file_fast(filename):
                return None
            
            # 分析文件
            folder_path = os.path.dirname(file_path)
            result = renamer.smart_analyze_file(filename, folder_path)
            
            if result:
                # 检查文件类型检查选项
                file_type = result.get('type', '')
                
                # 根据设置决定是否处理特定类型的文件
                if file_type == 'movie' and not self.settings.get('enable_movie_check', True):
                    return None
                elif file_type == 'tv' and not self.settings.get('enable_tv_check', True):
                    return None
                elif file_type == 'special' and not self.settings.get('enable_special_check', True):
                    return None
                
                # 强制应用规则
                if self.settings.get('force_movie_rules', False):
                    result['type'] = 'movie'
                elif self.settings.get('force_tv_rules', False):
                    result['type'] = 'tv'
                
                result['original_name'] = filename
                result['file_path'] = file_path
                result['status'] = '待处理'
                
                # 生成新文件名
                new_name = self.generate_new_filename(result, filename)
                result['new_name'] = new_name
                
                # 缓存结果
                self.cache.set_cached_result(file_path, result)
                
                return result
                
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
            raise
        
        return None
    
    def _should_skip_file_fast(self, filename: str) -> bool:
        """快速判断是否应该跳过文件"""
        filename_lower = filename.lower()
        
        # 快速跳过模式
        skip_patterns = [
            'sample', 'trailer', 'preview', '广告', '广告片',
            '.tmp', '.temp', '.bak', '.old', '.nfo', '.srt', '.ass', '.sub'
        ]
        
        for pattern in skip_patterns:
            if pattern in filename_lower:
                return True
        
        return False
    
    def generate_new_filename(self, result: Dict[str, Any], original_filename: str) -> str:
        """根据分析结果生成新文件名"""
        try:
            # 获取文件扩展名
            _, ext = os.path.splitext(original_filename)
            
            # 获取分析结果
            title = result.get('title', '')
            year = result.get('year', '')
            season = result.get('season')
            episode = result.get('episode')
            file_type = result.get('type', '')
            
            # 清理标题中的特殊字符（与原始代码保持一致）
            if title:
                import re
                clean_title = re.sub(r'[\\/*?:"<>|$$$$\.\!_]', ' ', title).strip()
                # 移除 SxxEyy/Sxx Eyy 片段
                clean_title = re.sub(r'[Ss]\d{2}[ ._]?E\d{2}', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title)  # 合并多余空格
                # 去除所有 []
                clean_title = re.sub(r'\[\s*\]', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                title = clean_title
            
            # 根据文件类型生成新文件名（与原始代码保持一致）
            if file_type == 'movie' and title:
                if year:
                    return f"{title} ({year}){ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'tv' and title:
                if season == 0:  # 特辑
                    if episode:
                        episode_str = str(episode).zfill(2)
                        return f"{title}.S00.E{episode_str}{ext}"
                    else:
                        return f"{title}.S00{ext}"
                elif season and episode:
                    season_str = str(season).zfill(2)
                    episode_str = str(episode).zfill(2)
                    return f"{title}.S{season_str}E{episode_str}{ext}"
                elif episode:
                    episode_str = str(episode).zfill(2)
                    return f"{title}.E{episode_str}{ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'special' and title:
                if episode:
                    episode_str = str(episode).zfill(2)
                    return f"{title}.S00.E{episode_str}{ext}"
                else:
                    return f"{title}.S00{ext}"
            else:
                return original_filename
                
        except Exception as e:
            logger.error(f"生成新文件名失败: {e}")
            return original_filename
    
    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"


class RenameWorker(QThread):
    """重命名工作线程"""
    progress_updated = pyqtSignal(int)
    rename_completed = pyqtSignal(bool, str)
    eta_updated = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    
    def __init__(self, renamer: MediaRenamer, files_to_rename: List[Dict[str, Any]]) -> None:
        super().__init__()
        self.renamer = renamer
        self.files_to_rename = files_to_rename
        self._cancelled = False
        self.max_workers = 4
        
    def cancel(self) -> None:
        """取消重命名"""
        self._cancelled = True
        
    def run(self) -> None:
        """执行重命名"""
        try:
            logger.info(f"开始重命名 {len(self.files_to_rename)} 个文件")
            
            # 初始化开始时间
            self.start_time = time.time()
            
            # 并行重命名文件
            success_count = 0
            error_count = 0
            error_messages = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_file = {
                    executor.submit(self.rename_single_file, file_info): file_info
                    for file_info in self.files_to_rename
                }
                
                completed = 0
                for future in as_completed(future_to_file):
                    if self._cancelled:
                        break
                    
                    file_info = future_to_file[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                            error_messages.append(f"重命名失败: {file_info.get('original_name', '未知文件')}")
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"重命名异常: {file_info.get('original_name', '未知文件')} - {str(e)}")
                    
                    # 更新进度
                    completed += 1
                    progress = int(completed / len(self.files_to_rename) * 100)
                    self.progress_updated.emit(progress)
                    self.current_file_changed.emit(file_info.get('original_name', '未知文件'))
                    
                    # 计算ETA
                    if completed > 0:
                        elapsed_time = time.time() - self.start_time
                        avg_time_per_file = elapsed_time / completed
                        remaining_files = len(self.files_to_rename) - completed
                        eta_seconds = avg_time_per_file * remaining_files
                        eta_str = self.format_time(eta_seconds)
                        self.eta_updated.emit(f"预计剩余时间: {eta_str}")
            
            # 生成结果消息
            if error_count == 0:
                message = f"成功重命名 {success_count} 个文件"
                self.rename_completed.emit(True, message)
            else:
                message = f"成功重命名 {success_count} 个文件，失败 {error_count} 个文件"
                if error_messages:
                    message += f"\n\n错误详情:\n" + "\n".join(error_messages[:5])  # 只显示前5个错误
                self.rename_completed.emit(False, message)
            
        except Exception as e:
            logger.error(f"重命名过程中发生错误: {e}")
            self.rename_completed.emit(False, f"重命名失败: {str(e)}")
    
    def rename_single_file(self, file_info: Dict[str, Any]) -> bool:
        """重命名单个文件"""
        try:
            file_path = file_info.get('file_path')
            new_name = file_info.get('new_name')
            
            if not file_path or not new_name:
                return False
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False
            
            # 生成新文件路径
            dir_path = os.path.dirname(file_path)
            new_file_path = os.path.join(dir_path, new_name)
            
            # 检查目标文件是否已存在
            if os.path.exists(new_file_path) and new_file_path != file_path:
                # 生成唯一文件名
                base_name, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(new_file_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    new_file_path = os.path.join(dir_path, new_name)
                    counter += 1
            
            # 执行重命名
            os.rename(file_path, new_file_path)
            return True
            
        except Exception as e:
            logger.error(f"重命名文件失败 {file_info.get('file_path', '未知')}: {e}")
            return False
    
    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时" 