# -*- coding: utf-8 -*-
"""影视重命名工具 - Pattern Recognizer模块

从 core/tv_rename_cache_optimized.py 拆出，保持行为一致。
"""
import os
import re
from typing import Optional, Tuple
try:
    from guessit import guessit
    GUESSIT_AVAILABLE = True
except ImportError:
    guessit = None
    GUESSIT_AVAILABLE = False


class PatternRecognizer:
    """智能模式识别器：用于识别和分类文件名模式"""
    
    def __init__(self):
        # === 预编译正则表达式 - 性能优化 ===
        self._compiled_patterns = {
            # 电视剧季数集数模式
            'tv_season_episode': re.compile(r'[Ss](\d{1,2})[ ._]?[Ee](\d{1,2})', re.IGNORECASE),
            'tv_chinese_season_episode': re.compile(r'第(\d{1,2})季[^第]*第(\d{1,2})集', re.IGNORECASE),
            'tv_episode_only': re.compile(r'[Ee](\d{1,2})', re.IGNORECASE),
            'tv_episode_ep': re.compile(r'[Ee][Pp][ ._]?(\d{1,2})(?![0-9])', re.IGNORECASE),  # 新增：支持EP01格式，包括分隔符，确保数字后面不是数字
            'tv_season_only': re.compile(r'[Ss](\d{1,2})', re.IGNORECASE),
            
            # 新增：纯数字集数模式（支持01.mp4、1.mp4等格式）
            'tv_episode_number_only': re.compile(r'^(\d{1,2})\.(mp4|mkv|avi|mov|wmv|flv|webm)$', re.IGNORECASE),
            'tv_episode_number_with_title': re.compile(r'^(.+?)[ ._](\d{1,2})(?<!\d)\.(mp4|mkv|avi|mov|wmv|flv|webm)$', re.IGNORECASE),
            'tv_episode_number_with_title_no_separator': re.compile(r'^(.+?)(?<!\d)(\d{1,2})\.(mp4|mkv|avi|mov|wmv|flv|webm)$', re.IGNORECASE),
            
            # 电影年份模式
            'movie_year': re.compile(r'(\d{4})', re.IGNORECASE),
            
            # 特辑关键词模式
            'special_keywords': re.compile(r'(特辑|特别篇|Special|OVA|SP)', re.IGNORECASE),
            
            # 文件名清理模式
            'clean_title': re.compile(r'[\\/*?:"<>|$$$$\.\!_]', re.IGNORECASE),
            'season_episode_clean': re.compile(r'[Ss]\d{2}[ ._]?E\d{2}', re.IGNORECASE),
            'bracket_clean': re.compile(r'\[\s*\]', re.IGNORECASE),
            'multiple_spaces': re.compile(r'\s+', re.IGNORECASE)
        }
        
        # 常见的电视剧模式
        self.tv_patterns = {
            'season_episode': re.compile(r'[Ss](\d{1,2})[ ._]?[Ee](\d{1,2})', re.IGNORECASE),
            'episode_only': re.compile(r'[Ee](\d{1,2})', re.IGNORECASE),
            'episode_ep': re.compile(r'[Ee][Pp][ ._]?(\d{1,2})(?![0-9])', re.IGNORECASE),  # 新增：支持EP01格式，包括分隔符，确保数字后面不是数字
            'chinese_episode': re.compile(r'第(\d{1,2})集', re.IGNORECASE),
            'chinese_season_episode': re.compile(r'第(\d{1,2})季[^第]*第(\d{1,2})集', re.IGNORECASE),
            'episode_word': re.compile(r'Episode[ ._]?(\d{1,2})', re.IGNORECASE),
            'episode_number': re.compile(r'(\d{1,2})[ ._]?[Ee]', re.IGNORECASE),
            # 新增：纯数字集数模式（在无扩展名的文件名上匹配）
            'episode_number_only': re.compile(r'^\d{1,2}$'),
            'episode_number_with_title': re.compile(r'^(.+?)[ ._](\d{1,2})(?<!\d)$', re.IGNORECASE),
            'episode_number_with_title_no_separator': re.compile(r'^(.+?)(?<!\d)(\d{1,2})$', re.IGNORECASE)
        }
        
        # 常见的电影模式
        self.movie_patterns = {
            'year_brackets': r'.*\((\d{4})\).*',  # 电影名 (2023)
            'year_square': r'.*\[(\d{4})\].*',  # 电影名 [2023]
            'year_dot': r'.*\.(\d{4})\.',  # 电影名.2023.
            'year_simple': r'.*(\d{4}).*',  # 电影名2023
            # 扩展模式
            'title_year_chinese': r'(.+)[(（【\[]?(\d{4})[)）】\]]?',  # 电影名(2023)
            'title_year_end': r'(.+?)(\d{4})$',  # 电影名2023
        }
        # 特殊模式（如特辑）
        self.special_patterns = {
            'special': r'SP\d*',  # SP, SP1
            'ova': r'OVA\d*',  # OVA, OVA1
            'extra': r'特别篇|特典|番外|花絮',
        }
        # 文件夹关键词（可在外部传入）
        self.tv_folder_keywords = ["电视剧", "剧集", "TV", "Series"]
        self.movie_folder_keywords = ["电影", "Movie", "Film"]
    
    def _clean_name(self, name: str) -> str:
        """清理名称中的分隔符、多余空格与首尾括号"""
        if not name:
            return ''
        name = re.sub(r'[._\-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'^[\(\)\[\]\{\}【】（）\s]+', '', name)
        name = re.sub(r'[\(\)\[\]\{\}【】（）\s]+$', '', name)
        return name.strip()

    def _extract_year(self, text: str) -> Tuple[Optional[str], int]:
        """查找文本中最后一个合理年份（1900-2100），返回 (年份, 起始位置)。
        过滤掉 1080/2160 等分辨率数字，避免被误认为年份。"""
        matches = list(re.finditer(r'(?<!\d)(?:19\d{2}|20\d{2}|2100)(?!\d)', text))
        if not matches:
            return None, -1
        m = matches[-1]
        return m.group(0), m.start()

    def extract_title(self, filename: str, match: Optional[re.Match] = None, info: Optional[dict] = None) -> str:
        # 优先 guessit
        if info and info.get('title'):
            return str(info['title']).strip()
        name = os.path.splitext(filename)[0]
        if match:
            # 优先使用非数字分组作为标题（如 title_year_chinese 的标题分组）
            title_group = None
            for group in match.groups():
                if group and not group.isdigit() and group in name:
                    title_group = group
                    break
            if title_group:
                name = title_group
            else:
                # 否则只移除匹配区间本身，避免全局误删（如把 S01E01 删成 SE）
                start, end = match.span()
                name = name[:start] + name[end:]
        return self._clean_name(name)

    def analyze_filename_guessit(self, filename: str) -> Optional[dict]:
        if not GUESSIT_AVAILABLE:
            return None
        info = guessit(filename)
        result = {
            'type': None,
            'confidence': 0.0,
            'season': info.get('season'),
            'episode': info.get('episode'),
            'year': info.get('year'),
            'title': None,
            'pattern_matched': 'guessit',
            'raw': info
        }
        if info.get('type') == 'episode':
            result['type'] = 'tv'
            result['confidence'] = 0.95
        elif info.get('type') == 'movie':
            result['type'] = 'movie'
            result['confidence'] = 0.95
        # 智能提取title
        result['title'] = self.extract_title(filename, None, info)
        return result

    def analyze_filename_regex(self, filename: str, folder_path: str = '') -> dict:
        candidates = []
        name = os.path.splitext(filename)[0]
        # 各模式基础置信度：更精确的模式优先，避免模糊模式（如 year_simple）抢占正确结果
        tv_conf = {
            'season_episode': 0.95,
            'episode_ep': 0.90,
            'chinese_episode': 0.90,
            'chinese_season_episode': 0.93,
            'episode_word': 0.90,
            'episode_only': 0.85,
            'episode_number': 0.80,
            'episode_number_with_title': 0.80,
            'episode_number_with_title_no_separator': 0.80,
            'episode_number_only': 0.75,
        }
        movie_conf = {
            'year_brackets': 0.85,
            'year_square': 0.85,
            'year_dot': 0.85,
            'title_year_chinese': 0.80,
            'title_year_end': 0.80,
            'year_simple': 0.70,
        }
        # TV
        for pattern_name, pattern in self.tv_patterns.items():
            match = pattern.search(name)
            if not match:
                continue
            season = None
            episode = None
            if pattern_name in ('season_episode', 'chinese_season_episode'):
                season = int(match.group(1))
                episode = int(match.group(2))
            elif pattern_name in ('episode_number_with_title', 'episode_number_with_title_no_separator'):
                episode = int(match.group(2))
            elif pattern_name == 'episode_number_only':
                episode = int(match.group(0))
            else:
                episode = int(match.group(1))
            title, tv_year = self._extract_tv_title_year(name, match, pattern_name)
            candidates.append({
                'type': 'tv', 'pattern': pattern_name, 'match': match,
                'confidence': tv_conf[pattern_name], 'season': season,
                'episode': episode, 'year': tv_year, 'title': title,
            })
        # Movie
        for pattern_name, pattern in self.movie_patterns.items():
            match = re.search(pattern, name)
            if not match:
                continue
            # 年份统一取文件名中最后一个合理年份，避免 1080/2160 被误判
            year, year_pos = self._extract_year(name)
            if not year:
                continue
            title_part = name[:year_pos]
            # 特例：整个文件名就是年份（如 2012.mkv），年份视为标题
            if self._clean_name(title_part) == '':
                title = year
                year = None
            else:
                title = self._clean_name(title_part)
            candidates.append({
                'type': 'movie', 'pattern': pattern_name, 'match': match,
                'confidence': movie_conf[pattern_name], 'year': year,
                'title': title,
            })
        # Special
        for pattern_name, pattern in self.special_patterns.items():
            match = re.search(pattern, name, re.IGNORECASE)
            if not match:
                continue
            title, _ = self._extract_tv_title_year(name, match, pattern_name)
            candidates.append({
                'type': 'special', 'pattern': pattern_name, 'match': match,
                'confidence': 0.6, 'title': title,
            })
        # 结合文件夹名提升置信度
        folder_lower = folder_path.lower() if folder_path else ''
        for cand in candidates:
            if cand['type'] == 'tv' and any(k.lower() in folder_lower for k in self.tv_folder_keywords):
                cand['confidence'] += 0.1
            if cand['type'] == 'movie' and any(k.lower() in folder_lower for k in self.movie_folder_keywords):
                cand['confidence'] += 0.1
        # 选置信度最高
        if candidates:
            best = max(candidates, key=lambda x: x['confidence'])
            result = {
                'type': best['type'],
                'confidence': best['confidence'],
                'pattern_matched': best['pattern'],
                'season': best.get('season'),
                'episode': best.get('episode'),
                'year': best.get('year'),
                'title': best.get('title'),
                'candidates': candidates
            }
            return result
        # 未识别
        return {'type': None, 'confidence': 0.0, 'pattern_matched': None, 'season': None, 'episode': None, 'year': None, 'title': None, 'candidates': []}

    def _extract_tv_title_year(self, name: str, match: re.Match, pattern_name: str) -> Tuple[str, Optional[str]]:
        """电视剧/特辑标题提取：取季集标记之前的文本；锚定模式取标题分组。
        剔除标题中夹带的年份（如 三体.2023.S01E01 → 标题 三体、年份 2023）。"""
        if pattern_name in ('episode_number_with_title', 'episode_number_with_title_no_separator'):
            raw = match.group(1)
        elif pattern_name == 'episode_number_only':
            raw = match.group(0)
        else:
            raw = name[:match.start()]
        year, pos = self._extract_year(raw)
        if year:
            raw = raw[:pos] + raw[pos + 4:]
        return self._clean_name(raw), year

    def analyze_filename(self, filename: str, folder_path: str = '') -> dict:
        # 快速模式：优先使用正则表达式，跳过guessit
        regex_result = self.analyze_filename_regex(filename, folder_path)
        
        # 只有在正则表达式无法识别时才使用guessit
        if regex_result['confidence'] < 0.5 and GUESSIT_AVAILABLE:
            guessit_result = self.analyze_filename_guessit(filename)
            if guessit_result and guessit_result['type'] in ('tv', 'movie') and guessit_result['confidence'] >= 0.8:
                return guessit_result
            # 如果 guessit 有部分信息但置信度低，可补全
            if guessit_result and regex_result['type'] and regex_result['confidence'] < 0.8:
                for k in ['season', 'episode', 'year', 'title']:
                    if not regex_result.get(k) and guessit_result.get(k):
                        regex_result[k] = guessit_result[k]
            # 确保title有值
            if not regex_result.get('title') and guessit_result and guessit_result.get('title'):
                regex_result['title'] = guessit_result['title']
        
        return regex_result
    
    def enhance_confidence(self, result: dict, folder_name: str) -> dict:
        """根据文件夹名称增强识别置信度"""
        if not result['type']:
            return result
        
        # 根据文件夹名称调整置信度
        folder_indicators = {
            'tv': ['剧集', '电视剧', 'TV', 'Season', '季'],
            'movie': ['电影', 'Movie', 'Movies', '影片'],
            'special': ['特别篇', 'Special', 'SP', 'OVA']
        }
        
        for media_type, indicators in folder_indicators.items():
            if any(ind in folder_name for ind in indicators):
                if result['type'] == media_type:
                    result['confidence'] += 0.2
                else:
                    result['confidence'] -= 0.1
        
        # 确保置信度在有效范围内
        result['confidence'] = max(0.0, min(1.0, result['confidence']))
        return result
    
    def suggest_rename_format(self, result: dict) -> Optional[str]:
        if not result['type']:
            return None
        if result['type'] == 'tv':
            if result['season'] and result['episode']:
                return "{title}.S{season:02d}.E{episode:02d}{ext}"
            elif result['episode']:
                return "{title}.E{episode:02d}{ext}"
        elif result['type'] == 'movie' and result['year']:
            return "{title} ({year}){ext}"
        elif result['type'] == 'special':
            return "{title}.Special{ext}"
        return None

    def extract_season_episode_optimized(self, filename: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """使用预编译正则表达式提取季数和集数 - 优化版本"""
        # 优先使用预编译的正则表达式
        season_episode_match = self._compiled_patterns['tv_season_episode'].search(filename)
        if season_episode_match:
            season = int(season_episode_match.group(1))
            episode = int(season_episode_match.group(2))
            return season, episode, "季数集数模式"
        
        # 中文季集模式（第1季第2集）
        chinese_season_episode_match = self._compiled_patterns['tv_chinese_season_episode'].search(filename)
        if chinese_season_episode_match:
            season = int(chinese_season_episode_match.group(1))
            episode = int(chinese_season_episode_match.group(2))
            return season, episode, "中文季集模式"
        
        # 只找到集数的情况（E01格式）
        episode_match = self._compiled_patterns['tv_episode_only'].search(filename)
        if episode_match:
            episode = int(episode_match.group(1))
            return None, episode, "仅集数模式"
        
        # 新增：EP格式集数（EP01格式）
        episode_ep_match = self._compiled_patterns['tv_episode_ep'].search(filename)
        if episode_ep_match:
            episode = int(episode_ep_match.group(1))
            # 验证集数范围（1-99）
            if 1 <= episode <= 99:
                return None, episode, "EP集数模式"
            else:
                return None, None, "EP集数超出范围"
        
        # 新增：纯数字集数模式（01.mp4、1.mp4等）
        episode_number_only_match = self._compiled_patterns['tv_episode_number_only'].search(filename)
        if episode_number_only_match:
            episode = int(episode_number_only_match.group(1))
            # 验证集数范围（1-99）
            if 1 <= episode <= 99:
                return None, episode, "纯数字集数模式"
            else:
                return None, None, "纯数字集数超出范围"
        
        # 新增：标题+数字集数模式（步步惊心 01.mp4等）
        episode_number_with_title_match = self._compiled_patterns['tv_episode_number_with_title'].search(filename)
        if episode_number_with_title_match:
            episode = int(episode_number_with_title_match.group(2))
            # 验证集数范围（1-99）
            if 1 <= episode <= 99:
                return None, episode, "标题+数字集数模式"
            else:
                return None, None, "标题+数字集数超出范围"
        
        # 新增：标题+数字集数模式（无分隔符，如你好旧时光30.mp4）
        episode_number_with_title_no_separator_match = self._compiled_patterns['tv_episode_number_with_title_no_separator'].search(filename)
        if episode_number_with_title_no_separator_match:
            episode = int(episode_number_with_title_no_separator_match.group(2))
            # 验证集数范围（1-99）
            if 1 <= episode <= 99:
                return None, episode, "标题+数字集数模式(无分隔符)"
            else:
                return None, None, "标题+数字集数超出范围"
        
        # 只找到季数的情况
        season_match = self._compiled_patterns['tv_season_only'].search(filename)
        if season_match:
            season = int(season_match.group(1))
            return None, None, "仅季数模式"
        
        # 回退到原有模式（兼容性）
        for pattern_name, pattern in self.tv_patterns.items():
            match = pattern.search(filename)
            if match:
                # 原有的处理逻辑
                if 'season_episode' in pattern_name:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    return season, episode, "兼容模式"
                elif 'episode_only' in pattern_name or 'episode_ep' in pattern_name:
                    episode = int(match.group(1))
                    return None, episode, "兼容模式"
                elif 'episode_number_only' in pattern_name:
                    episode = int(match.group(1))
                    if 1 <= episode <= 99:
                        return None, episode, "兼容纯数字模式"
                elif 'episode_number_with_title' in pattern_name:
                    episode = int(match.group(2))
                    if 1 <= episode <= 99:
                        return None, episode, "兼容标题+数字模式"
        
        return None, None, "未找到匹配模式"
    
    def extract_title_year_optimized(self, text: str) -> Tuple[str, str]:
        """提取标题和年份 - 修复版：标题取最后一个合理年份之前的文本，
        年份为 1900-2100 的 4 位数字（过滤 1080/2160 等分辨率）。"""
        # 去掉扩展名
        base, ext = os.path.splitext(text)
        if not ext:
            base = text
        year, pos = self._extract_year(base)
        title = base[:pos] if year else base
        title = self._clean_name(title)
        return title, (year or '未知')
    
    def _clean_title_optimized(self, title: str) -> str:
        """使用预编译正则表达式清理标题 - 优化版本"""
        # 移除特殊字符
        title = self._compiled_patterns['clean_title'].sub(' ', title)
        
        # 移除季数集数片段
        title = self._compiled_patterns['season_episode_clean'].sub('', title)
        
        # 移除空括号
        title = self._compiled_patterns['bracket_clean'].sub('', title)
        
        # 合并多余空格
        title = self._compiled_patterns['multiple_spaces'].sub(' ', title).strip()
        
        return title
