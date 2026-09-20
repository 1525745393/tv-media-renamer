#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描速度优化器 - 影视文件重命名工具
"""

import os
import time
import logging
import hashlib
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

logger = logging.getLogger(__name__)

class ScanSpeedOptimizer:
    """扫描速度优化器"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.cache = {}
        self.file_hashes = {}
        self.skip_patterns = self._compile_skip_patterns()
        self.fast_patterns = self._compile_fast_patterns()
        
    def _compile_skip_patterns(self) -> List[re.Pattern]:
        """编译跳过模式"""
        patterns = [
            r'sample', r'trailer', r'preview', r'广告', r'广告片',
            r'\.tmp$', r'\.temp$', r'\.bak$', r'\.old$',
            r'\.nfo$', r'\.srt$', r'\.ass$', r'\.sub$'
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_fast_patterns(self) -> Dict[str, re.Pattern]:
        """编译快速识别模式"""
        return {
            'tv_season_episode': re.compile(r'[Ss](\d{1,2})[Ee](\d{1,2})', re.IGNORECASE),
            'tv_episode_only': re.compile(r'[Ee](\d{1,2})', re.IGNORECASE),
            'movie_year': re.compile(r'\((\d{4})\)', re.IGNORECASE),
            'movie_year_dash': re.compile(r'(\d{4})', re.IGNORECASE),
            'special_keywords': re.compile(r'(特辑|特别篇|Special|SP|OVA)', re.IGNORECASE)
        }
    
    def should_skip_file(self, filename: str) -> bool:
        """快速判断是否应该跳过文件"""
        filename_lower = filename.lower()
        
        # 检查文件扩展名
        allowed_extensions = self.settings.get('video_extensions', ['.mp4', '.mkv', '.avi'])
        _, ext = os.path.splitext(filename)
        if ext.lower() not in allowed_extensions:
            return True
        
        # 检查跳过模式
        for pattern in self.skip_patterns:
            if pattern.search(filename):
                return True
        
        return False
    
    def fast_analyze_file(self, filename: str, folder_path: str = '') -> Dict[str, Any]:
        """快速分析文件（不使用guessit）"""
        name = os.path.splitext(filename)[0]
        folder_name = os.path.basename(folder_path) if folder_path else ''
        
        # 快速类型判断
        file_type = None
        confidence = 0.0
        season = None
        episode = None
        year = None
        title = None
        
        # 检查电视剧模式
        season_episode_match = self.fast_patterns['tv_season_episode'].search(name)
        if season_episode_match:
            file_type = 'tv'
            confidence = 0.9
            season = int(season_episode_match.group(1))
            episode = int(season_episode_match.group(2))
            title = self._extract_title_fast(name, season_episode_match)
        
        # 检查仅集数模式
        elif self.fast_patterns['tv_episode_only'].search(name):
            file_type = 'tv'
            confidence = 0.7
            episode_match = self.fast_patterns['tv_episode_only'].search(name)
            episode = int(episode_match.group(1))
            title = self._extract_title_fast(name, episode_match)
        
        # 检查电影模式
        elif self.fast_patterns['movie_year'].search(name) or self.fast_patterns['movie_year_dash'].search(name):
            file_type = 'movie'
            confidence = 0.8
            year_match = self.fast_patterns['movie_year'].search(name) or self.fast_patterns['movie_year_dash'].search(name)
            year = year_match.group(1)
            title = self._extract_title_fast(name, year_match)
        
        # 检查特辑模式
        elif self.fast_patterns['special_keywords'].search(name):
            file_type = 'special'
            confidence = 0.6
            title = self._extract_title_fast(name, None)
        
        # 根据文件夹名称调整
        if folder_name:
            confidence = self._adjust_confidence_by_folder(file_type, folder_name, confidence)
        
        return {
            'type': file_type,
            'confidence': confidence,
            'season': season,
            'episode': episode,
            'year': year,
            'title': title or name,
            'pattern_matched': 'fast_analysis'
        }
    
    def _extract_title_fast(self, name: str, match: Optional[re.Match]) -> str:
        """快速提取标题"""
        if match:
            # 移除匹配的部分
            title = name[:match.start()] + name[match.end():]
        else:
            title = name
        
        # 快速清理
        title = re.sub(r'[._-]+', ' ', title)  # 替换分隔符
        title = re.sub(r'\[.*?\]', '', title)  # 移除方括号内容
        title = re.sub(r'\(.*?\)', '', title)  # 移除圆括号内容
        title = re.sub(r'\s+', ' ', title).strip()  # 合并空格
        
        return title
    
    def _adjust_confidence_by_folder(self, file_type: str, folder_name: str, confidence: float) -> float:
        """根据文件夹名称调整置信度"""
        folder_lower = folder_name.lower()
        
        if file_type == 'tv':
            tv_keywords = ['剧集', '电视剧', 'tv', 'series', 'season', '季']
            if any(kw in folder_lower for kw in tv_keywords):
                confidence += 0.1
        elif file_type == 'movie':
            movie_keywords = ['电影', 'movie', 'film', '影片']
            if any(kw in folder_lower for kw in movie_keywords):
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def batch_scan_optimized(self, folder_path: str, max_workers: int = 8) -> List[Dict[str, Any]]:
        """优化的批量扫描"""
        logger.info(f"🚀 开始优化扫描: {folder_path}")
        start_time = time.time()
        
        # 收集所有文件
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not self.should_skip_file(file):
                    all_files.append(file_path)
        
        logger.info(f"📊 找到 {len(all_files)} 个候选文件")
        
        # 分批处理
        batch_size = 100
        batches = [all_files[i:i + batch_size] for i in range(0, len(all_files), batch_size)]
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for batch_index, batch in enumerate(batches):
                logger.info(f"🔄 处理批次 {batch_index + 1}/{len(batches)} ({len(batch)}个文件)")
                
                # 提交批次任务
                future_to_file = {
                    executor.submit(self._analyze_single_file_optimized, file_path): file_path
                    for file_path in batch
                }
                
                # 收集结果
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result(timeout=5)  # 5秒超时
                        if result and result.get('type'):
                            results.append(result)
                        completed += 1
                    except Exception as e:
                        logger.error(f"分析文件失败 {file_path}: {e}")
                        completed += 1
                
                # 更新进度
                progress = int(completed / len(all_files) * 100)
                logger.info(f"📈 进度: {progress}% ({completed}/{len(all_files)})")
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ 扫描完成: {len(results)} 个有效文件，耗时 {elapsed_time:.2f} 秒")
        logger.info(f"⚡ 平均速度: {len(all_files) / elapsed_time:.1f} 文件/秒")
        
        return results
    
    def _analyze_single_file_optimized(self, file_path: str) -> Optional[Dict[str, Any]]:
        """优化的单文件分析"""
        try:
            # 检查缓存
            file_hash = self._get_file_hash_fast(file_path)
            if file_path in self.cache and self.cache[file_path]['hash'] == file_hash:
                return self.cache[file_path]['result']
            
            # 快速分析
            filename = os.path.basename(file_path)
            folder_path = os.path.dirname(file_path)
            result = self.fast_analyze_file(filename, folder_path)
            
            # 添加文件信息
            result['original_name'] = filename
            result['file_path'] = file_path
            result['status'] = '待处理'
            
            # 生成新文件名
            result['new_name'] = self._generate_new_filename_fast(result, filename)
            
            # 缓存结果
            self.cache[file_path] = {
                'result': result,
                'hash': file_hash,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
            return None
    
    def _get_file_hash_fast(self, file_path: str) -> str:
        """快速文件哈希计算"""
        try:
            stat = os.stat(file_path)
            # 使用文件大小和修改时间作为简单哈希
            hash_input = f"{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception:
            return ""
    
    def _generate_new_filename_fast(self, result: Dict[str, Any], original_filename: str) -> str:
        """快速生成新文件名"""
        try:
            _, ext = os.path.splitext(original_filename)
            title = result.get('title', '')
            year = result.get('year', '')
            season = result.get('season')
            episode = result.get('episode')
            file_type = result.get('type', '')
            
            if file_type == 'movie' and title:
                if year:
                    return f"{title} ({year}){ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'tv' and title:
                if season and episode:
                    return f"{title}.S{season:02d}E{episode:02d}{ext}"
                elif episode:
                    return f"{title}.E{episode:02d}{ext}"
                else:
                    return f"{title}{ext}"
            elif file_type == 'special' and title:
                if episode:
                    return f"{title}.S00.E{episode:02d}{ext}"
                else:
                    return f"{title}.S00{ext}"
            else:
                return original_filename
                
        except Exception as e:
            logger.error(f"生成新文件名失败: {e}")
            return original_filename
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            'cache_size': len(self.cache),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'skip_patterns_count': len(self.skip_patterns),
            'fast_patterns_count': len(self.fast_patterns)
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        # 这里需要在实际使用中统计
        return 0.0  # 占位符

# 使用示例
if __name__ == "__main__":
    # 测试优化器
    settings = {
        'video_extensions': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'],
        'max_workers': 8
    }
    
    optimizer = ScanSpeedOptimizer(settings)
    
    # 测试文件夹
    test_folder = "test_data/test_media_folder"
    if os.path.exists(test_folder):
        results = optimizer.batch_scan_optimized(test_folder)
        print(f"扫描结果: {len(results)} 个文件")
        for result in results[:5]:  # 显示前5个结果
            print(f"- {result['original_name']} -> {result['new_name']} ({result['type']})")
    else:
        print(f"测试文件夹不存在: {test_folder}") 