#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件分类器 - 影视文件重命名工具 v1.4
"""

import os
import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    file_path: str
    primary_category: str
    secondary_category: str
    confidence: float
    tags: List[str]
    metadata: Dict[str, Any]


class FileClassifier:
    """智能文件分类器"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.classification_rules = self._load_classification_rules()
        self.custom_patterns = self._load_custom_patterns()
        
        # 预定义的分类规则
        self.category_patterns = {
            '电影': {
                'patterns': [
                    r'\b(电影|Movie|Film|Cinema)\b',
                    r'\.(mp4|mkv|avi|mov|wmv|flv|webm)$',
                    r'\d{4}',  # 年份
                    r'\b(BluRay|HDTV|WEB-DL|HDRip|BRRip|DVDRip)\b'
                ],
                'exclude_patterns': [
                    r'[Ss]\d{1,2}[Ee]\d{1,2}',  # 季集格式
                    r'\b(Season|Episode|S\d{2}E\d{2})\b'
                ]
            },
            '电视剧': {
                'patterns': [
                    r'\b(电视剧|剧集|TV|Series|Show)\b',
                    r'[Ss]\d{1,2}[Ee]\d{1,2}',  # 季集格式
                    r'\b(Season|Episode|S\d{2}E\d{2})\b',
                    r'\b(第\d+季|第\d+集)\b'
                ],
                'exclude_patterns': []
            },
            '动画': {
                'patterns': [
                    r'\b(动画|Anime|Cartoon|Animation)\b',
                    r'\b(动漫|日本动画)\b',
                    r'\.(mp4|mkv|avi)$',
                    r'\b(BD|BluRay|HDTV)\b'
                ],
                'exclude_patterns': []
            },
            '纪录片': {
                'patterns': [
                    r'\b(纪录片|Documentary|Doc)\b',
                    r'\b(探索|Discovery|BBC|National Geographic)\b',
                    r'\b(历史|History|Nature|Science)\b'
                ],
                'exclude_patterns': []
            },
            '综艺': {
                'patterns': [
                    r'\b(综艺|Variety|Show|Entertainment)\b',
                    r'\b(娱乐|Entertainment|Comedy)\b',
                    r'\b(访谈|Talk Show|Interview)\b'
                ],
                'exclude_patterns': []
            },
            '音乐': {
                'patterns': [
                    r'\b(音乐|Music|Concert|Live)\b',
                    r'\b(演唱会|Live|Concert|MTV)\b',
                    r'\.(mp3|flac|wav|aac|m4a)$'
                ],
                'exclude_patterns': []
            }
        }
        
        # 质量分类规则
        self.quality_patterns = {
            '4K': r'\b(4K|2160p|UHD|UltraHD)\b',
            '1080p': r'\b(1080p|FHD|FullHD)\b',
            '720p': r'\b(720p|HD)\b',
            '480p': r'\b(480p|SD)\b'
        }
        
        # 来源分类规则
        self.source_patterns = {
            'BluRay': r'\b(BluRay|Blu-Ray|BD)\b',
            'HDTV': r'\b(HDTV|TVRip)\b',
            'WEB-DL': r'\b(WEB-DL|WebRip|WEB)\b',
            'HDRip': r'\b(HDRip|HD-Rip)\b',
            'BRRip': r'\b(BRRip|BR-Rip)\b',
            'DVDRip': r'\b(DVDRip|DVD-Rip)\b'
        }
    
    def _load_classification_rules(self) -> Dict[str, Any]:
        """加载分类规则"""
        try:
            rules_file = "classification_rules.json"
            if os.path.exists(rules_file):
                with open(rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载分类规则失败: {e}")
        
        return {}
    
    def _load_custom_patterns(self) -> Dict[str, List[str]]:
        """加载自定义模式"""
        try:
            patterns_file = "custom_patterns.json"
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载自定义模式失败: {e}")
        
        return {}
    
    def classify_file(self, file_path: str) -> ClassificationResult:
        """分类单个文件"""
        try:
            if not os.path.exists(file_path):
                return ClassificationResult(
                    file_path=file_path,
                    primary_category='未知',
                    secondary_category='未知',
                    confidence=0.0,
                    tags=[],
                    metadata={'error': '文件不存在'}
                )
            
            filename = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            
            # 基础分类
            primary_category = self._classify_primary_category(filename, dir_path)
            secondary_category = self._classify_secondary_category(filename, dir_path)
            
            # 提取标签
            tags = self._extract_tags(filename, dir_path)
            
            # 计算置信度
            confidence = self._calculate_classification_confidence(
                filename, dir_path, primary_category, secondary_category, tags
            )
            
            # 收集元数据
            metadata = self._collect_classification_metadata(file_path, primary_category)
            
            return ClassificationResult(
                file_path=file_path,
                primary_category=primary_category,
                secondary_category=secondary_category,
                confidence=confidence,
                tags=tags,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"分类文件失败 {file_path}: {e}")
            return ClassificationResult(
                file_path=file_path,
                primary_category='未知',
                secondary_category='未知',
                confidence=0.0,
                tags=[],
                metadata={'error': str(e)}
            )
    
    def _classify_primary_category(self, filename: str, dir_path: str) -> str:
        """分类主要类别"""
        # 检查自定义模式
        for category, patterns in self.custom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return category
        
        # 检查预定义模式
        category_scores = defaultdict(float)
        
        for category, rules in self.category_patterns.items():
            score = 0
            
            # 检查包含模式
            for pattern in rules['patterns']:
                if re.search(pattern, filename, re.IGNORECASE):
                    score += 1
            
            # 检查排除模式
            for pattern in rules.get('exclude_patterns', []):
                if re.search(pattern, filename, re.IGNORECASE):
                    score -= 2  # 排除模式权重更高
            
            # 检查目录名
            dir_name = os.path.basename(dir_path)
            for pattern in rules['patterns']:
                if re.search(pattern, dir_name, re.IGNORECASE):
                    score += 0.5
            
            category_scores[category] = score
        
        # 返回得分最高的类别
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        return '未知'
    
    def _classify_secondary_category(self, filename: str, dir_path: str) -> str:
        """分类次要类别"""
        # 基于文件扩展名分类
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']:
            return '视频'
        elif ext in ['.mp3', '.flac', '.wav', '.aac', '.m4a']:
            return '音频'
        elif ext in ['.srt', '.ass', '.sub', '.idx']:
            return '字幕'
        elif ext in ['.nfo', '.vsmeta', '.xml']:
            return '元数据'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return '图片'
        else:
            return '其他'
    
    def _extract_tags(self, filename: str, dir_path: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 质量标签
        for quality, pattern in self.quality_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                tags.append(quality)
        
        # 来源标签
        for source, pattern in self.source_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                tags.append(source)
        
        # 语言标签
        language_patterns = {
            '中文': r'\b(中文|中字|国语|普通话|简中|繁中|CHS|CHT)\b',
            '英文': r'\b(英文|英字|英语|ENG)\b',
            '日文': r'\b(日文|日语|JPN)\b',
            '韩文': r'\b(韩文|韩语|KOR)\b'
        }
        
        for language, pattern in language_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                tags.append(language)
        
        # 编码标签
        codec_patterns = {
            'H.264': r'\b(H\.264|AVC|x264)\b',
            'H.265': r'\b(H\.265|HEVC|x265)\b',
            'VP9': r'\bVP9\b',
            'AV1': r'\bAV1\b'
        }
        
        for codec, pattern in codec_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                tags.append(codec)
        
        # 年份标签
        year_match = re.search(r'\((\d{4})\)', filename)
        if year_match:
            tags.append(f"年份:{year_match.group(1)}")
        
        # 季集标签
        season_episode_match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', filename, re.IGNORECASE)
        if season_episode_match:
            season = season_episode_match.group(1)
            episode = season_episode_match.group(2)
            tags.append(f"第{season}季")
            tags.append(f"第{episode}集")
        
        return tags
    
    def _calculate_classification_confidence(self, filename: str, dir_path: str, 
                                           primary_category: str, secondary_category: str, 
                                           tags: List[str]) -> float:
        """计算分类置信度"""
        confidence = 0.0
        
        # 基础分数
        if primary_category != '未知':
            confidence += 0.3
        
        if secondary_category != '未知':
            confidence += 0.2
        
        # 标签分数
        confidence += len(tags) * 0.05
        
        # 文件名长度分数（更长的文件名通常包含更多信息）
        if len(filename) > 20:
            confidence += 0.1
        
        # 目录名匹配分数
        dir_name = os.path.basename(dir_path)
        if primary_category in dir_name:
            confidence += 0.2
        
        # 特殊模式匹配分数
        if re.search(r'\d{4}', filename):  # 年份
            confidence += 0.1
        
        if re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', filename, re.IGNORECASE):  # 季集
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _collect_classification_metadata(self, file_path: str, primary_category: str) -> Dict[str, Any]:
        """收集分类元数据"""
        metadata = {}
        
        try:
            # 文件基本信息
            stat_info = os.stat(file_path)
            metadata['file_size'] = stat_info.st_size
            metadata['file_size_mb'] = stat_info.st_size / 1024 / 1024
            metadata['modified_time'] = stat_info.st_mtime
            
            # 文件扩展名
            _, ext = os.path.splitext(file_path)
            metadata['extension'] = ext.lower()
            
            # 目录信息
            dir_path = os.path.dirname(file_path)
            metadata['directory'] = dir_path
            metadata['directory_name'] = os.path.basename(dir_path)
            
            # 分类信息
            metadata['primary_category'] = primary_category
            metadata['classification_time'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"收集分类元数据失败: {e}")
            metadata['error'] = str(e)
        
        return metadata
    
    def batch_classify(self, file_paths: List[str]) -> List[ClassificationResult]:
        """批量分类文件"""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.classify_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"批量分类文件失败 {file_path}: {e}")
        
        return results
    
    def get_classification_summary(self, results: List[ClassificationResult]) -> Dict[str, Any]:
        """获取分类摘要"""
        summary = {
            'total_files': len(results),
            'primary_categories': defaultdict(int),
            'secondary_categories': defaultdict(int),
            'tags': defaultdict(int),
            'confidence_stats': {
                'high': 0,    # > 0.8
                'medium': 0,  # 0.5-0.8
                'low': 0      # < 0.5
            },
            'average_confidence': 0.0
        }
        
        total_confidence = 0.0
        
        for result in results:
            # 统计主要类别
            summary['primary_categories'][result.primary_category] += 1
            
            # 统计次要类别
            summary['secondary_categories'][result.secondary_category] += 1
            
            # 统计标签
            for tag in result.tags:
                summary['tags'][tag] += 1
            
            # 统计置信度
            confidence = result.confidence
            total_confidence += confidence
            
            if confidence > 0.8:
                summary['confidence_stats']['high'] += 1
            elif confidence > 0.5:
                summary['confidence_stats']['medium'] += 1
            else:
                summary['confidence_stats']['low'] += 1
        
        # 计算平均置信度
        if results:
            summary['average_confidence'] = total_confidence / len(results)
        
        return summary
    
    def suggest_organization(self, results: List[ClassificationResult]) -> Dict[str, List[str]]:
        """建议文件组织方式"""
        organization = defaultdict(list)
        
        for result in results:
            if result.primary_category != '未知':
                # 基于主要类别组织
                category_path = f"{result.primary_category}"
                
                # 添加年份子目录
                year_tag = next((tag for tag in result.tags if tag.startswith('年份:')), None)
                if year_tag:
                    year = year_tag.split(':')[1]
                    category_path += f"/{year}"
                
                # 添加质量子目录
                quality_tags = [tag for tag in result.tags if tag in ['4K', '1080p', '720p', '480p']]
                if quality_tags:
                    category_path += f"/{quality_tags[0]}"
                
                organization[category_path].append(result.file_path)
        
        return dict(organization)
    
    def export_classification_rules(self, file_path: str) -> bool:
        """导出分类规则"""
        try:
            rules_data = {
                'category_patterns': self.category_patterns,
                'quality_patterns': self.quality_patterns,
                'source_patterns': self.source_patterns,
                'custom_patterns': self.custom_patterns,
                'export_time': datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分类规则已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出分类规则失败: {e}")
            return False
    
    def import_classification_rules(self, file_path: str) -> bool:
        """导入分类规则"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            self.category_patterns = rules_data.get('category_patterns', self.category_patterns)
            self.quality_patterns = rules_data.get('quality_patterns', self.quality_patterns)
            self.source_patterns = rules_data.get('source_patterns', self.source_patterns)
            self.custom_patterns = rules_data.get('custom_patterns', self.custom_patterns)
            
            logger.info(f"分类规则已从文件导入: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导入分类规则失败: {e}")
            return False 