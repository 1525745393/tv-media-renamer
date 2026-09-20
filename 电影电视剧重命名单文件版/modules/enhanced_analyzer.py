#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能分析器 - 影视文件重命名工具 v1.3
支持更多文件格式和多语言识别
"""

import os
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedAnalyzer:
    """增强的智能分析器"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.supported_formats = {
            # 视频格式
            'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.mts', '.m2ts'],
            # 音频格式
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.ape'],
            # 字幕格式
            'subtitle': ['.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt'],
            # 图片格式
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            # 文档格式
            'document': ['.pdf', '.txt', '.doc', '.docx', '.nfo']
        }
        
        # 多语言支持
        self.language_patterns = {
            'chinese': {
                'patterns': [r'[\u4e00-\u9fff]+'],
                'keywords': ['中文', '国语', '粤语', '台语', '中字', '中英双字']
            },
            'english': {
                'patterns': [r'[a-zA-Z\s]+'],
                'keywords': ['eng', 'english', '英字', '英音']
            },
            'japanese': {
                'patterns': [r'[\u3040-\u309f\u30a0-\u30ff]+'],
                'keywords': ['jpn', 'japanese', '日语', '日字']
            },
            'korean': {
                'patterns': [r'[\uac00-\ud7af]+'],
                'keywords': ['kor', 'korean', '韩语', '韩字']
            }
        }
        
        # 增强的文件类型识别规则
        self.file_type_rules = {
            'movie': {
                'patterns': [
                    r'(\d{4})',  # 年份
                    r'(1080p|720p|4K|2160p)',  # 分辨率
                    r'(BluRay|WEB-DL|HDRip|BRRip|DVDRip)',  # 来源
                    r'(x264|x265|HEVC|AVC)',  # 编码
                    r'(AC3|AAC|DTS|FLAC)',  # 音频编码
                ],
                'keywords': ['movie', 'film', '电影', '影片']
            },
            'tv': {
                'patterns': [
                    r'S(\d{1,2})E(\d{1,2})',  # 季集格式
                    r'Season\s*(\d{1,2})',  # Season格式
                    r'Episode\s*(\d{1,2})',  # Episode格式
                    r'第(\d{1,2})季',  # 中文季格式
                    r'第(\d{1,2})集',  # 中文集格式
                ],
                'keywords': ['tv', 'series', '电视剧', '剧集', '连续剧']
            },
            'special': {
                'patterns': [
                    r'(OVA|SP|Special|特别篇|特典)',  # 特辑标识
                    r'S00E(\d{1,2})',  # 特辑季集格式
                ],
                'keywords': ['ova', 'special', '特辑', '特别篇', '特典']
            }
        }
    
    def analyze_file(self, filename: str, folder_path: str = "") -> Dict[str, Any]:
        """分析文件（增强版）"""
        try:
            logger.info(f"开始分析文件: {filename}")
            
            # 基础信息
            result = {
                'filename': filename,
                'folder_path': folder_path,
                'file_path': os.path.join(folder_path, filename) if folder_path else filename,
                'file_size': 0,
                'file_type': 'unknown',
                'media_type': 'unknown',
                'title': '',
                'year': '',
                'season': None,
                'episode': None,
                'quality': '',
                'source': '',
                'audio_codec': '',
                'video_codec': '',
                'languages': [],
                'subtitles': [],
                'confidence': 0.0
            }
            
            # 获取文件信息
            self._get_file_info(result)
            
            # 分析文件名
            self._analyze_filename(result)
            
            # 分析文件夹结构
            if folder_path:
                self._analyze_folder_structure(result)
            
            # 计算置信度
            self._calculate_confidence(result)
            
            logger.info(f"文件分析完成: {result['title']} ({result['year']})")
            return result
            
        except Exception as e:
            logger.error(f"文件分析失败 {filename}: {e}")
            return self._create_error_result(filename, str(e))
    
    def _get_file_info(self, result: Dict[str, Any]) -> None:
        """获取文件基本信息"""
        try:
            file_path = result['file_path']
            if os.path.exists(file_path):
                # 文件大小
                result['file_size'] = os.path.getsize(file_path)
                
                # 文件扩展名
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                
                # 确定媒体类型
                for media_type, formats in self.supported_formats.items():
                    if ext in formats:
                        result['media_type'] = media_type
                        break
                
                # 确定文件类型
                result['file_type'] = self._determine_file_type(result['filename'])
                
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
    
    def _determine_file_type(self, filename: str) -> str:
        """确定文件类型"""
        filename_lower = filename.lower()
        
        # 检查各种文件类型规则
        for file_type, rules in self.file_type_rules.items():
            # 检查关键词
            for keyword in rules['keywords']:
                if keyword.lower() in filename_lower:
                    return file_type
            
            # 检查模式
            for pattern in rules['patterns']:
                if re.search(pattern, filename, re.IGNORECASE):
                    return file_type
        
        # 默认返回unknown
        return 'unknown'
    
    def _analyze_filename(self, result: Dict[str, Any]) -> None:
        """分析文件名"""
        filename = result['filename']
        
        # 移除扩展名
        name_without_ext = os.path.splitext(filename)[0]
        
        # 提取年份
        year_match = re.search(r'(\d{4})', name_without_ext)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= datetime.now().year + 1:
                result['year'] = str(year)
        
        # 提取质量信息
        quality_patterns = [
            r'(1080p|720p|480p|360p|4K|2160p|UHD)',
            r'(HD|SD|LD)',
            r'(BluRay|WEB-DL|HDRip|BRRip|DVDRip|CAM|TS|TC)'
        ]
        
        for pattern in quality_patterns:
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                if 'p' in match.group(1) or 'K' in match.group(1):
                    result['quality'] = match.group(1)
                else:
                    result['source'] = match.group(1)
        
        # 提取编码信息
        codec_patterns = {
            'video': r'(x264|x265|HEVC|AVC|H.264|H.265)',
            'audio': r'(AC3|AAC|DTS|FLAC|MP3|OGG)'
        }
        
        for codec_type, pattern in codec_patterns.items():
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                if codec_type == 'video':
                    result['video_codec'] = match.group(1)
                else:
                    result['audio_codec'] = match.group(1)
        
        # 提取季集信息
        self._extract_season_episode(result, name_without_ext)
        
        # 提取标题
        self._extract_title(result, name_without_ext)
        
        # 检测语言
        self._detect_languages(result, name_without_ext)
    
    def _extract_season_episode(self, result: Dict[str, Any], filename: str) -> None:
        """提取季集信息"""
        # 标准格式 S01E01
        season_episode_match = re.search(r'S(\d{1,2})E(\d{1,2})', filename, re.IGNORECASE)
        if season_episode_match:
            result['season'] = int(season_episode_match.group(1))
            result['episode'] = int(season_episode_match.group(2))
            return
        
        # 中文格式 第1季第1集
        chinese_match = re.search(r'第(\d{1,2})季.*?第(\d{1,2})集', filename)
        if chinese_match:
            result['season'] = int(chinese_match.group(1))
            result['episode'] = int(chinese_match.group(2))
            return
        
        # 单独的季节信息
        season_match = re.search(r'Season\s*(\d{1,2})', filename, re.IGNORECASE)
        if season_match:
            result['season'] = int(season_match.group(1))
        
        # 单独的集数信息
        episode_match = re.search(r'Episode\s*(\d{1,2})', filename, re.IGNORECASE)
        if episode_match:
            result['episode'] = int(episode_match.group(1))
    
    def _extract_title(self, result: Dict[str, Any], filename: str) -> None:
        """提取标题"""
        # 移除扩展名
        title = filename
        
        # 移除年份
        title = re.sub(r'\d{4}', '', title)
        
        # 移除季集信息
        title = re.sub(r'S\d{1,2}E\d{1,2}', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Season\s*\d{1,2}', '', title, flags=re.IGNORECASE)
        title = re.sub(r'Episode\s*\d{1,2}', '', title, flags=re.IGNORECASE)
        title = re.sub(r'第\d{1,2}季.*?第\d{1,2}集', '', title)
        
        # 移除质量信息
        title = re.sub(r'(1080p|720p|480p|360p|4K|2160p|UHD)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'(HD|SD|LD)', '', title, flags=re.IGNORECASE)
        
        # 移除来源信息
        title = re.sub(r'(BluRay|WEB-DL|HDRip|BRRip|DVDRip|CAM|TS|TC)', '', title, flags=re.IGNORECASE)
        
        # 移除编码信息
        title = re.sub(r'(x264|x265|HEVC|AVC|H.264|H.265)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'(AC3|AAC|DTS|FLAC|MP3|OGG)', '', title, flags=re.IGNORECASE)
        
        # 移除特殊字符
        title = re.sub(r'[._-]+', ' ', title)
        title = re.sub(r'[\[\](){}]', '', title)
        
        # 清理多余空格
        title = re.sub(r'\s+', ' ', title).strip()
        
        # 移除语言标识
        for lang_info in self.language_patterns.values():
            for keyword in lang_info['keywords']:
                title = re.sub(rf'\b{re.escape(keyword)}\b', '', title, flags=re.IGNORECASE)
        
        # 如果标题为空，使用原始文件名
        if not title:
            title = os.path.splitext(result['filename'])[0]
        
        result['title'] = title
    
    def _detect_languages(self, result: Dict[str, Any], filename: str) -> None:
        """检测语言"""
        detected_languages = []
        
        for lang_code, lang_info in self.language_patterns.items():
            # 检查模式
            for pattern in lang_info['patterns']:
                if re.search(pattern, filename):
                    detected_languages.append(lang_code)
                    break
            
            # 检查关键词
            for keyword in lang_info['keywords']:
                if keyword.lower() in filename.lower():
                    detected_languages.append(lang_code)
                    break
        
        result['languages'] = list(set(detected_languages))  # 去重
    
    def _analyze_folder_structure(self, result: Dict[str, Any]) -> None:
        """分析文件夹结构"""
        folder_path = result['folder_path']
        if not folder_path:
            return
        
        # 获取文件夹名称
        folder_name = os.path.basename(folder_path)
        
        # 如果文件名中没有标题信息，尝试从文件夹名获取
        if not result['title'] or result['title'] == os.path.splitext(result['filename'])[0]:
            # 分析文件夹名
            folder_title = self._extract_title_from_folder(folder_name)
            if folder_title and folder_title != folder_name:
                result['title'] = folder_title
        
        # 检查父文件夹
        parent_folder = os.path.dirname(folder_path)
        if parent_folder:
            parent_name = os.path.basename(parent_folder)
            # 如果父文件夹看起来像年份
            if re.match(r'^\d{4}$', parent_name):
                if not result['year']:
                    result['year'] = parent_name
    
    def _extract_title_from_folder(self, folder_name: str) -> str:
        """从文件夹名提取标题"""
        # 移除常见的文件夹标识
        title = folder_name
        
        # 移除年份
        title = re.sub(r'\d{4}', '', title)
        
        # 移除季集信息
        title = re.sub(r'Season\s*\d{1,2}', '', title, flags=re.IGNORECASE)
        title = re.sub(r'第\d{1,2}季', '', title)
        
        # 移除特殊字符
        title = re.sub(r'[._-]+', ' ', title)
        title = re.sub(r'[\[\](){}]', '', title)
        
        # 清理多余空格
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> None:
        """计算分析置信度"""
        confidence = 0.0
        
        # 基础分数
        if result['title']:
            confidence += 20.0
        
        if result['year']:
            confidence += 15.0
        
        if result['season'] is not None:
            confidence += 15.0
        
        if result['episode'] is not None:
            confidence += 15.0
        
        if result['quality']:
            confidence += 10.0
        
        if result['source']:
            confidence += 10.0
        
        if result['languages']:
            confidence += 5.0
        
        # 文件类型识别分数
        if result['file_type'] != 'unknown':
            confidence += 10.0
        
        # 媒体类型识别分数
        if result['media_type'] != 'unknown':
            confidence += 5.0
        
        # 文件大小合理性检查
        if result['file_size'] > 0:
            if result['media_type'] == 'video' and result['file_size'] > 10 * 1024 * 1024:  # 10MB
                confidence += 5.0
            elif result['media_type'] == 'audio' and result['file_size'] > 1024 * 1024:  # 1MB
                confidence += 5.0
        
        result['confidence'] = min(confidence, 100.0)
    
    def _create_error_result(self, filename: str, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'filename': filename,
            'title': '',
            'year': '',
            'season': None,
            'episode': None,
            'file_type': 'unknown',
            'media_type': 'unknown',
            'quality': '',
            'source': '',
            'languages': [],
            'confidence': 0.0,
            'error': error_msg
        }
    
    def get_analysis_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取分析摘要"""
        summary = {
            'total_files': len(results),
            'file_types': {},
            'media_types': {},
            'years': {},
            'languages': {},
            'avg_confidence': 0.0,
            'high_confidence_files': 0,
            'low_confidence_files': 0
        }
        
        total_confidence = 0.0
        
        for result in results:
            # 文件类型统计
            file_type = result.get('file_type', 'unknown')
            summary['file_types'][file_type] = summary['file_types'].get(file_type, 0) + 1
            
            # 媒体类型统计
            media_type = result.get('media_type', 'unknown')
            summary['media_types'][media_type] = summary['media_types'].get(media_type, 0) + 1
            
            # 年份统计
            year = result.get('year', '')
            if year:
                summary['years'][year] = summary['years'].get(year, 0) + 1
            
            # 语言统计
            languages = result.get('languages', [])
            for lang in languages:
                summary['languages'][lang] = summary['languages'].get(lang, 0) + 1
            
            # 置信度统计
            confidence = result.get('confidence', 0.0)
            total_confidence += confidence
            
            if confidence >= 70.0:
                summary['high_confidence_files'] += 1
            elif confidence < 30.0:
                summary['low_confidence_files'] += 1
        
        if results:
            summary['avg_confidence'] = total_confidence / len(results)
        
        return summary 