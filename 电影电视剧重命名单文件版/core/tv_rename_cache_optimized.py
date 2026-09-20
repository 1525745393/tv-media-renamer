#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群辉适配版：影视文件重命名工具 v1.3（智能优化版）
功能亮点：
1. 支持电影和电视剧不同命名规则
2. 自动根据文件夹路径中的关键词识别类型（"电视剧"或"电影"）
3. 电影命名格式：电影_名称 (发行_年份).ext
4. 电视剧命名格式：电视_节目_名称.SXX.EYY.ext
5. 电视特辑处理：S00
6. 文件夹类型自动识别：路径中有"电视剧"则按电视剧规则处理，有"电影"则按电影规则处理
7. 优化版v1.0：增强异常处理、详细日志记录、错误诊断
8. I/O优化版v1.1：大幅减少磁盘I/O操作，提升性能
9. 智能优化版v1.3：AI智能识别、批量处理优化、高级安全防护
"""

# ==== 版本更新说明 ====
# v1.3 智能优化版新增功能：
# 1. AI智能识别：基于文件名模式的智能类型识别
# 2. 批量处理优化：支持多目录并行处理，断点续传
# 3. 高级安全防护：沙盒模式、操作确认、安全验证
# 4. 性能监控：实时性能统计、内存使用监控
# 5. 智能缓存：增量缓存更新、缓存自动清理
# 6. 错误恢复：自动错误恢复、详细错误报告
# 7. 用户界面优化：更友好的交互界面、进度显示
# 8. 配置管理：配置文件导入导出、设置备份
# 9. 日志增强：分类日志、日志轮转、性能日志
# 10. 兼容性提升：支持更多文件格式、更好的跨平台支持
#
# v1.1 I/O优化版功能：
# 1. 正则表达式优化：简化year_pattern为更高效的模式r'(\d{4})'
# 2. 文件哈希计算：使用更快的MD5算法替代默认算法
# 3. 缓存路径修复：修正_cache_file的变量名拼写错误
# 4. 路径处理优化：使用os.path.join替代字符串拼接
# 5. 特辑模板修复：修正变量名错误(极title→title)
# 6. 缓存优化：减少文件系统调用次数
# 7. 元数据处理：优化批量元数据更新效率
# 8. 修复交互式设置中的颜色代码错误(Fore.CAN→Fore.CYAN)
# 9. 优化版v1.0新增：增加traceback详细异常信息，进度显示同步日志
# 10. 版本管理：规范化版本命名和文档
# 11. I/O优化版v1.1新增：
#     - 批量文件存在性检查：预先缓存目录文件列表
#     - 文件大小缓存：在缓存中存储文件大小信息
#     - 元数据文件批量处理：一次性处理所有元数据文件
#     - 历史记录批量写入：减少历史文件I/O频率
#     - 缓存更新优化：减少缓存文件写入次数
#     - 文件存在性缓存：避免重复的os.path.exists调用
# =================

import os
import re
import json
import logging
import hashlib
import shutil
import traceback
import signal
import sys
import glob
import concurrent.futures
from logging.handlers import RotatingFileHandler
from typing import Tuple, Dict, List, Optional, Union
from datetime import datetime
import time
from collections import defaultdict
from colorama import init, Fore, Style
# 基础默认配置统一来源于 core/constants.py（单一来源），本文件仅覆盖运行引擎需要的差异键
from core.constants import DEFAULT_SETTINGS as _BASE_DEFAULT_SETTINGS
# 在文件头部导入 guessit
try:
    from guessit import guessit
    GUESSIT_AVAILABLE = True
except ImportError:
    GUESSIT_AVAILABLE = False

# 可选依赖：psutil 用于内存监控（如果未安装，程序仍可正常运行，只是禁用内存监控功能）

# 尝试导入readline（Windows环境下可能不可用）
try:
    import readline
except ImportError:
    readline = None

# 初始化 colorama
init(autoreset=True)

# 常量定义
HISTORY_FILE = "rename_history.json"
CACHE_FILE = "media_rename_cache.json"

# ===================== 交互式改进 =====================
class InteractiveHandler:
    """交互式输入处理器"""
    
    def __init__(self):
        self.original_sigint = signal.getsignal(signal.SIGINT)
        self.setup_signal_handlers()
        self.setup_readline()
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            print(Fore.YELLOW + "\n\n⚠️  操作被用户中断 (Ctrl+C)")
            print(Fore.CYAN + "正在安全退出...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def setup_readline(self):
        """设置readline以支持Tab补全"""
        if readline is None:
            return
            
        try:
            # 设置Tab补全
            readline.set_completer(self.path_completer)
            readline.parse_and_bind("tab: complete")
            readline.set_completer_delims(' \t\n`!@#$%^&*()=+[{]}\\|;:\'",<>?')
        except Exception as e:
            # 在某些环境下readline可能不可用
            pass
    
    def path_completer(self, text, state):
        """路径补全器"""
        if not text:
            return None
        
        # 获取可能的补全
        matches = []
        
        # 当前目录补全
        if text.startswith('./'):
            text = text[2:]
            base_path = '.'
        elif text.startswith('../'):
            text = text[3:]
            base_path = '..'
        elif text.startswith('/'):
            base_path = '/'
        else:
            base_path = '.'
            if text:
                base_path = text.rsplit('/', 1)[0] if '/' in text else '.'
                text = text.rsplit('/', 1)[1] if '/' in text else text
        
        try:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    if item.startswith(text):
                        if os.path.isdir(os.path.join(base_path, item)):
                            matches.append(os.path.join(base_path, item) + '/')
                        else:
                            matches.append(os.path.join(base_path, item))
        except (OSError, PermissionError):
            pass
        
        # 返回匹配项
        if state < len(matches):
            return matches[state]
        return None
    
    def safe_input(self, prompt: str, default: str = "", allow_empty: bool = False) -> str:
        """安全的输入函数，支持默认值和中断处理"""
        try:
            if default:
                user_input = input(f"{prompt} (默认: {default}): ").strip()
            else:
                user_input = input(prompt).strip()
            
            if not user_input and not allow_empty:
                return default
            return user_input
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️  输入被中断")
            return default if default else ""
        except EOFError:
            print(Fore.YELLOW + "\n\n⚠️  输入结束")
            return default if default else ""
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """确认操作"""
        try:
            default_text = "Y/n" if default else "y/N"
            response = input(f"{message} ({default_text}): ").strip().lower()
            
            if not response:
                return default
            return response in ['y', 'yes', '是', '1', 'true']
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️  操作被取消")
            return False
    
    def select_from_list(self, items: List[str], title: str = "请选择") -> Optional[int]:
        """从列表中选择"""
        if not items:
            return None
        
        print(Fore.CYAN + f"\n{title}:")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        
        try:
            choice = input(f"\n请选择 (1-{len(items)}): ").strip()
            if not choice:
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(items):
                return choice_num - 1
            else:
                print(Fore.RED + f"无效选择: {choice}")
                return None
        except (ValueError, KeyboardInterrupt):
            return None

# ===================== 配置管理 =====================
class ConfigManager:
    """配置管理器：处理配置的加载、保存、备份和验证"""
    
    def __init__(self, config_file: str = "config.json", backup_dir: str = "config_backups"):
        self.config_file = config_file
        self.backup_dir = backup_dir
        self.settings = {}  # 延迟初始化
        self.last_backup = 0
        self._init_backup_dir()
        self._init_settings()
    
    def _init_settings(self):
        """初始化设置"""
        global DEFAULT_SETTINGS
        if 'DEFAULT_SETTINGS' in globals():
            self.settings = DEFAULT_SETTINGS.copy()
        else:
            # 如果DEFAULT_SETTINGS还未定义，使用基本设置
            self.settings = {
                "folder_path": "/volume2/NAS2/video2/影视库",
                "movie_template": "{title} ({year}){ext}",
                "tv_template": "{title}.S{season:02d}.E{episode:02d}{ext}",
                "special_template": "{title}.S00.E{episode:02d}{ext}",
                "preview_only": True,
                "video_extensions": [".mp4", ".mkv", ".avi", ".mov", ".ts", ".flv", ".wmv", ".mpg", ".mpeg", ".rmvb", ".webm"],
                "metadata_extensions": [".srt", ".nfo", ".ass", ".vsmeta", ".sub"],
                "enable_history": True,
                "skip_existing": True,
                "preview_page_size": 10,
                "cache_ttl": 300,
                "enable_hash_check": False,
                "tv_folder_keywords": ["电视剧", "剧集", "TV", "Series"],
                "movie_folder_keywords": ["电影", "Movie", "Film"],
                "force_tv_rules": False,
                "force_movie_rules": False,
                "enable_special_check": True,
                "special_keywords": ["特辑", "特别篇", "Special"],
                "force_special_season": True,
                "enable_incremental_cache": True,
                "cache_auto_cleanup": True,
                "cache_max_size_mb": 100
            }
    
    def _init_backup_dir(self):
        """初始化备份目录"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # 合并配置，保留默认值
                self.settings.update(loaded_settings)
                return True
            return False
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            # 检查是否需要备份
            if self.settings.get("backup_enabled", True):
                self._create_backup()
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False
    
    def _create_backup(self):
        """创建配置备份"""
        now = time.time()
        if now - self.last_backup >= self.settings.get("backup_interval", 3600):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"config_backup_{timestamp}.json")
                shutil.copy2(self.config_file, backup_file)
                self.last_backup = now
                
                # 清理旧备份
                self._cleanup_old_backups()
            except Exception as e:
                logging.warning(f"创建配置备份失败: {e}")
    
    def _cleanup_old_backups(self):
        """清理旧的配置备份"""
        try:
            backups = sorted(glob.glob(os.path.join(self.backup_dir, "config_backup_*.json")))
            max_backups = 10  # 最多保留10个备份
            if len(backups) > max_backups:
                for old_backup in backups[:-max_backups]:
                    os.remove(old_backup)
        except Exception as e:
            logging.warning(f"清理旧备份失败: {e}")
    
    def export_config(self, export_file: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_file: str) -> bool:
        """从文件导入配置"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # 验证导入的配置
            if self._validate_config(imported_settings):
                # 备份当前配置
                self._create_backup()
                # 更新配置
                self.settings.update(imported_settings)
                # 保存新配置
                return self.save_config()
            return False
        except Exception as e:
            logging.error(f"导入配置失败: {e}")
            return False
    
    def _validate_config(self, config: dict) -> bool:
        """验证配置有效性"""
        required_keys = [
            "folder_path",
            "movie_template",
            "tv_template",
            "special_template",
            "video_extensions",
            "metadata_extensions"
        ]
        
        # 检查必需的键
        for key in required_keys:
            if key not in config:
                logging.error(f"配置缺少必需的键: {key}")
                return False
        
        # 验证路径
        if not os.path.exists(config["folder_path"]):
            logging.warning(f"配置的文件夹路径不存在: {config['folder_path']}")
        
        # 验证扩展名列表
        if not isinstance(config["video_extensions"], list) or \
           not isinstance(config["metadata_extensions"], list):
            logging.error("扩展名必须是列表类型")
            return False
        
        # 验证模板
        required_placeholders = {
            "movie_template": ["{title}", "{year}", "{ext}"],
            "tv_template": ["{title}", "{season}", "{episode}", "{ext}"],
            "special_template": ["{title}", "{episode}", "{ext}"]
        }
        
        for template_key, placeholders in required_placeholders.items():
            if template_key in config:
                template = config[template_key]
                for placeholder in placeholders:
                    if placeholder not in template:
                        logging.error(f"{template_key} 缺少必需的占位符: {placeholder}")
                        return False
        
        return True
    
    def get_setting(self, key: str, default=None):
        """获取配置项值"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value) -> bool:
        """设置配置项值"""
        try:
            self.settings[key] = value
            return True
        except Exception as e:
            logging.error(f"设置配置项失败: {e}")
            return False
    
    def show_config(self):
        """显示当前配置"""
        print(Fore.CYAN + "\n当前配置:")
        for key, value in self.settings.items():
            # 敏感信息脱敏
            if key in ["api_key", "secret_key"]:
                value = "*" * 8
            print(f"  {key}: {value}")

# ===================== 智能识别 =====================
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

# ===================== 性能监控与报告 =====================
class PerformanceMonitor:
    """性能监控器：监控系统性能并生成报告"""
    
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = {}
        self.memory_usage = []
        self.cpu_usage = []
        self.disk_io = {}
        self.error_counts = {}
        self.success_counts = {}
        
    def start_operation(self, operation_name: str):
        """开始监控操作"""
        self.operation_times[operation_name] = {
            'start': time.time(),
            'memory_start': self._get_memory_usage()
        }
    
    def end_operation(self, operation_name: str, success: bool = True):
        """结束监控操作"""
        if operation_name in self.operation_times:
            end_time = time.time()
            start_data = self.operation_times[operation_name]
            duration = end_time - start_data['start']
            memory_end = self._get_memory_usage()
            memory_diff = memory_end - start_data['memory_start']
            
            self.operation_times[operation_name].update({
                'end': end_time,
                'duration': duration,
                'memory_end': memory_end,
                'memory_diff': memory_diff,
                'success': success
            })
            
            # 更新统计
            if success:
                self.success_counts[operation_name] = self.success_counts.get(operation_name, 0) + 1
            else:
                self.error_counts[operation_name] = self.error_counts.get(operation_name, 0) + 1
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # psutil 未安装时返回 0，不影响程序运行
            return 0.0
    
    def get_performance_summary(self) -> dict:
        """获取性能摘要"""
        total_time = time.time() - self.start_time
        total_operations = len(self.operation_times)
        successful_operations = sum(1 for op in self.operation_times.values() if op.get('success', False))
        
        # 计算平均操作时间
        avg_duration = sum(op.get('duration', 0) for op in self.operation_times.values()) / max(total_operations, 1)
        
        # 计算内存使用趋势
        memory_trend = "stable"
        if len(self.memory_usage) > 1:
            if self.memory_usage[-1] > self.memory_usage[0] * 1.2:
                memory_trend = "increasing"
            elif self.memory_usage[-1] < self.memory_usage[0] * 0.8:
                memory_trend = "decreasing"
        
        return {
            'total_time': total_time,
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': (successful_operations / max(total_operations, 1)) * 100,
            'avg_operation_time': avg_duration,
            'memory_trend': memory_trend,
            'current_memory_mb': self._get_memory_usage(),
            'error_summary': dict(self.error_counts),
            'success_summary': dict(self.success_counts)
        }
    
    def generate_report(self, report_file: Optional[str] = None) -> str:
        """生成性能报告"""
        summary = self.get_performance_summary()
        
        report_lines = [
            "=" * 60,
            "性能监控报告",
            "=" * 60,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总运行时间: {summary['total_time']:.2f} 秒",
            f"总操作数: {summary['total_operations']}",
            f"成功操作数: {summary['successful_operations']}",
            f"成功率: {summary['success_rate']:.1f}%",
            f"平均操作时间: {summary['avg_operation_time']:.3f} 秒",
            f"当前内存使用: {summary['current_memory_mb']:.1f} MB",
            f"内存趋势: {summary['memory_trend']}",
            "",
            "详细操作统计:",
            "-" * 40
        ]
        
        # 添加详细操作统计
        for op_name, op_data in self.operation_times.items():
            success_count = self.success_counts.get(op_name, 0)
            error_count = self.error_counts.get(op_name, 0)
            total_count = success_count + error_count
            
            report_lines.extend([
                f"操作: {op_name}",
                f"  执行次数: {total_count}",
                f"  成功次数: {success_count}",
                f"  失败次数: {error_count}",
                f"  平均耗时: {op_data.get('duration', 0):.3f} 秒",
                f"  内存变化: {op_data.get('memory_diff', 0):.1f} MB",
                ""
            ])
        
        # 添加错误分析
        if self.error_counts:
            report_lines.extend([
                "错误分析:",
                "-" * 40
            ])
            for error_type, count in self.error_counts.items():
                report_lines.append(f"  {error_type}: {count} 次")
            report_lines.append("")
        
        # 添加建议
        report_lines.extend([
            "性能建议:",
            "-" * 40
        ])
        
        if summary['success_rate'] < 90:
            report_lines.append("⚠️  成功率较低，建议检查错误日志")
        
        if summary['avg_operation_time'] > 5:
            report_lines.append("⚠️  操作时间较长，建议优化处理逻辑")
        
        if summary['current_memory_mb'] > 500:
            report_lines.append("⚠️  内存使用较高，建议检查内存泄漏")
        
        if summary['memory_trend'] == "increasing":
            report_lines.append("⚠️  内存使用呈上升趋势，可能存在内存泄漏")
        
        report_lines.append("✅ 性能监控完成")
        report_lines.append("=" * 60)
        
        report_content = "\n".join(report_lines)
        
        # 保存到文件
        if report_file:
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
            except Exception as e:
                logging.error(f"保存性能报告失败: {e}")
        
        return report_content
    
    def reset(self):
        """重置监控数据"""
        self.start_time = time.time()
        self.operation_times.clear()
        self.memory_usage.clear()
        self.cpu_usage.clear()
        self.disk_io.clear()
        self.error_counts.clear()
        self.success_counts.clear()

# ===================== 常量定义 =====================
# 基础配置来源于 core/constants.py，此处仅覆盖/扩展运行引擎需要的差异键；
# 新增配置键请优先维护在 core/constants.py，避免两处漂移。
DEFAULT_SETTINGS = {
    **_BASE_DEFAULT_SETTINGS,
    # 路径与命名模板（模板必须包含 {ext}，渲染时直接 format）
    "folder_path": "/volume2/NAS2/video2/影视库",  # 建议修改为你的实际影视库路径
    "movie_template": "{title} ({year}){ext}",  # 电影命名模板
    "tv_template": "{title}.S{season:02d}.E{episode:02d}{ext}",  # 电视剧命名模板
    "special_template": "{title}.S00.E{episode:02d}{ext}",  # 电视特辑模板
    "preview_only": True,
    "video_extensions": [
        ".mp4", ".mkv", ".avi", ".mov", ".ts", ".flv", ".wmv", ".mpg", ".mpeg", ".rmvb", ".webm"
    ],
    "metadata_extensions": [".srt", ".nfo", ".ass", ".vsmeta", ".sub", ".ssa"],
    # v1.3新增配置
    "sandbox_mode": True,  # 是否启用沙盒模式
    "sandbox_dir": ".sandbox",  # 沙盒目录
    "parallel_processing": True,  # 是否启用并行处理
    "max_workers": 4,  # 最大并行工作线程数
    "auto_cleanup": True,  # 是否自动清理缓存和临时文件
    "cache_ttl": 3600,  # 缓存有效期（秒）- 默认1小时
    "operation_timeout": 30,  # 单个操作超时时间（秒）
    "max_retries": 3,  # 操作失败最大重试次数
    "security_level": "high",  # 安全级别：low, medium, high
    "require_confirmation": True,  # 是否需要用户确认重要操作
    "backup_enabled": True,  # 是否启用配置备份
    "backup_interval": 3600,  # 配置备份间隔（秒）
    "log_rotation": True,  # 是否启用日志轮转
    "max_log_size": 10485760,  # 单个日志文件最大大小（字节）
    "max_log_files": 5,  # 最大保留日志文件数
    "performance_monitoring": True,  # 是否启用性能监控
    "memory_limit": 1073741824,  # 最大内存使用限制（字节）
    "enable_history": True,
    "skip_existing": True,
    "preview_page_size": 10,
    "enable_hash_check": False,  # 是否启用哈希检查
    "tv_folder_keywords": ["电视剧", "剧集", "TV", "Series"],  # 电视剧文件夹关键词
    "movie_folder_keywords": ["电影", "Movie", "Film"],  # 电影文件夹关键词
    "force_tv_rules": False,  # 强制使用电视剧规则
    "force_movie_rules": False,  # 强制使用电影规则
    "enable_special_check": True,  # 是否启用特辑检查
    "special_keywords": ["特辑", "特别篇", "Special"],  # 特辑关键词
    "force_special_season": True,  # 强制将特辑识别为S00季
    "enable_incremental_cache": True,  # 是否启用增量缓存更新
    "cache_auto_cleanup": True,  # 是否自动清理过期缓存
    "cache_max_size_mb": 100  # 缓存最大大小(MB)
}

HISTORY_FILE = "rename_history.json"
CACHE_FILE = "media_rename_cache.json"

# ===================== 全局对象初始化 =====================
# 全局配置管理器
config_manager = ConfigManager()

# 全局智能识别器
pattern_recognizer = PatternRecognizer()

# 全局性能监控器
performance_monitor = PerformanceMonitor()

# ===================== 日志配置 =====================
def setup_logging():
    """配置增强日志系统"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 主日志文件
    log_file = os.path.join(log_dir, f'media_rename_{datetime.now().strftime("%Y%m%d")}.log')
    # 错误日志文件
    error_log_file = os.path.join(log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')
    # 安全日志文件
    security_log_file = os.path.join(log_dir, f'security_{datetime.now().strftime("%Y%m%d")}.log')
    # 性能日志文件
    performance_log_file = os.path.join(log_dir, f'performance_{datetime.now().strftime("%Y%m%d")}.log')
    
    logger = logging.getLogger("MediaRenamer")
    logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以捕获所有日志
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 详细格式器（用于文件日志）
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 简洁格式器（用于控制台）
    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname).1s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 主日志处理器（INFO级别及以上）
    main_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(detailed_formatter)
    logger.addHandler(main_handler)
    
    # 错误日志处理器（ERROR级别及以上）
    error_handler = RotatingFileHandler(
        error_log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # 安全日志处理器（专门记录安全相关事件）
    security_handler = RotatingFileHandler(
        security_log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(detailed_formatter)
    logger.addHandler(security_handler)
    
    # 性能日志处理器（DEBUG级别，记录性能数据）
    performance_handler = RotatingFileHandler(
        performance_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    performance_handler.setLevel(logging.DEBUG)
    performance_handler.setFormatter(detailed_formatter)
    logger.addHandler(performance_handler)
    
    # 控制台日志处理器（WARNING级别及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # 添加自定义过滤器
    class SecurityFilter(logging.Filter):
        def filter(self, record):
            return getattr(record, 'security_event', False)
    
    class PerformanceFilter(logging.Filter):
        def filter(self, record):
            return getattr(record, 'performance_event', False)
    
    security_handler.addFilter(SecurityFilter())
    performance_handler.addFilter(PerformanceFilter())
    
    return logger

class SecurityLogger:
    """安全日志记录器"""
    def __init__(self, logger):
        self.logger = logger
    
    def log_file_access(self, file_path: str, operation: str, user: Optional[str] = None):
        """记录文件访问"""
        record = self.logger.makeRecord(
            'MediaRenamer', logging.INFO, '', 0, 
            f"文件访问: {operation} - {file_path}",
            (), None
        )
        record.security_event = True
        record.user = user or os.getenv('USERNAME', 'unknown')
        self.logger.handle(record)
    
    def log_permission_denied(self, file_path: str, operation: str):
        """记录权限拒绝"""
        record = self.logger.makeRecord(
            'MediaRenamer', logging.WARNING, '', 0,
            f"权限拒绝: {operation} - {file_path}",
            (), None
        )
        record.security_event = True
        self.logger.handle(record)
    
    def log_suspicious_activity(self, activity: str, details: str):
        """记录可疑活动"""
        record = self.logger.makeRecord(
            'MediaRenamer', logging.WARNING, '', 0,
            f"可疑活动: {activity} - {details}",
            (), None
        )
        record.security_event = True
        self.logger.handle(record)

class PerformanceLogger:
    """性能日志记录器"""
    def __init__(self, logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """开始计时"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str, additional_info: str = ""):
        """结束计时并记录"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            record = self.logger.makeRecord(
                'MediaRenamer', logging.DEBUG, '', 0,
                f"性能: {operation} - 耗时: {duration:.3f}秒 {additional_info}",
                (), None
            )
            record.performance_event = True
            self.logger.handle(record)
            del self.start_times[operation]
    
    def log_memory_usage(self, operation: str):
        """记录内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            record = self.logger.makeRecord(
                'MediaRenamer', logging.DEBUG, '', 0,
                f"内存使用: {operation} - {memory_mb:.1f}MB",
                (), None
            )
            record.performance_event = True
            self.logger.handle(record)
        except ImportError:
            # psutil 未安装时不记录内存使用，但不影响程序运行
            pass

class ErrorHandler:
    """增强错误处理器"""
    def __init__(self, logger):
        self.logger = logger
        self.error_counts = {}
        self.error_threshold = 10  # 错误阈值
        self.error_window = 300  # 错误窗口（秒）
        self.error_timestamps = {}
    
    def handle_error(self, error: Exception, context: str, file_path: Optional[str] = None, 
                    operation: Optional[str] = None, severity: str = "ERROR"):
        """处理错误"""
        error_key = f"{type(error).__name__}:{context}"
        current_time = time.time()
        
        # 更新错误计数
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
            self.error_timestamps[error_key] = []
        
        self.error_counts[error_key] += 1
        self.error_timestamps[error_key].append(current_time)
        
        # 清理过期的错误记录
        self.error_timestamps[error_key] = [
            ts for ts in self.error_timestamps[error_key] 
            if current_time - ts < self.error_window
        ]
        
        # 检查是否超过错误阈值
        recent_errors = len(self.error_timestamps[error_key])
        if recent_errors >= self.error_threshold:
            self.logger.critical(
                f"错误频率过高: {error_key} - {recent_errors}次错误在{self.error_window}秒内"
            )
        
        # 记录详细错误信息
        error_msg = f"错误详情: {context}"
        if file_path:
            error_msg += f" - 文件: {file_path}"
        if operation:
            error_msg += f" - 操作: {operation}"
        error_msg += f" - 错误: {str(error)}"
        
        if severity == "CRITICAL":
            self.logger.critical(error_msg, exc_info=True)
        elif severity == "ERROR":
            self.logger.error(error_msg, exc_info=True)
        elif severity == "WARNING":
            self.logger.warning(error_msg)
        else:
            self.logger.info(error_msg)
    
    def get_error_summary(self) -> dict:
        """获取错误摘要"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts),
            'recent_errors': {
                key: len(timestamps) for key, timestamps in self.error_timestamps.items()
            }
        }
    
    def reset_error_counts(self):
        """重置错误计数"""
        self.error_counts.clear()
        self.error_timestamps.clear()

    def _handle_error(self, error: Exception, context: str, file_path: Optional[str] = None, 
                     operation: Optional[str] = None, severity: str = "ERROR"):
        """统一的错误处理方法"""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'file_path': file_path,
            'operation': operation,
            'severity': severity,
            'timestamp': datetime.now()
        }
        
        # 记录错误
        self.error_contexts.append(error_info)
        self.error_counts[error_info['type']] += 1
        
        # 根据严重程度处理
        if severity == "CRITICAL":
            self.logger.critical(f"严重错误: {error_info['message']} (上下文: {error_info['context']})")
        elif severity == "ERROR":
            self.logger.error(f"错误: {error_info['message']} (文件: {error_info['file_path']})")
        else:
            self.logger.warning(f"警告: {error_info['message']}")
        
        # 检查错误数量限制
        if len(self.error_contexts) > self.max_errors:
            self.logger.warning(f"错误数量超过限制 ({self.max_errors})，停止处理")
            return False
        
        return True

# ===================== 核心功能类 =====================
class MediaRenamer:
    def __init__(self, settings: dict):
        # === 初始化方法组 ===
        self._init_core_components(settings)
        self._init_security_components(settings)
        self._init_performance_components(settings)
        self._init_logging_components(settings)
        
        # 设置日志
        setup_logging()
        
        # 初始化增强组件
        self.security_logger = SecurityLogger(self.logger)
        self.performance_logger = PerformanceLogger(self.logger)
        self.error_handler = ErrorHandler(self.logger)
        
        # v1.3新增：集成配置管理器和性能监控器
        try:
            self.config_manager = config_manager
            self.pattern_recognizer = pattern_recognizer
            self.performance_monitor = performance_monitor
            
            # 加载配置
            if self.settings.get("backup_enabled", True):
                self.config_manager.load_config()
            
            # 启动性能监控
            if self.settings.get("performance_monitoring", True):
                self.performance_monitor.start_operation("initialization")
        except NameError:
            # 如果全局变量未定义，创建本地实例
            self.config_manager = ConfigManager()
            self.pattern_recognizer = PatternRecognizer()
            self.performance_monitor = PerformanceMonitor()
            self.logger.warning("使用本地配置管理器实例")
        
        # 安全设置
        self.security_settings = {
            'max_file_size_mb': settings.get('max_file_size_mb', 50000),  # 50GB
            'allowed_extensions': set(settings.get('video_extensions', []) + 
                                    settings.get('metadata_extensions', [])),
            'forbidden_paths': settings.get('forbidden_paths', ['/system', '/boot', '/etc', '/usr', '/var', '/proc', '/dev', 'C:\\Windows', 'C:\\System32']),
            'max_files_per_operation': settings.get('max_files_per_operation', 10000),
            'enable_path_validation': settings.get('enable_path_validation', True),
            'enable_file_size_check': settings.get('enable_file_size_check', True),
            'enable_suspicious_detection': settings.get('enable_suspicious_detection', True),
            # 新增：沙盒模式和安全确认设置
            'enable_sandbox_mode': settings.get('enable_sandbox_mode', False),
            'sandbox_directory': settings.get('sandbox_directory'),
            'enable_operation_confirmation': settings.get('enable_operation_confirmation', True),
            'confirmation_threshold': settings.get('confirmation_threshold', 10),  # 超过此数量的操作需要确认
            'enable_destructive_operation_confirmation': settings.get('enable_destructive_operation_confirmation', True),  # 删除/覆盖操作确认
            'enable_batch_confirmation': settings.get('enable_batch_confirmation', True),  # 批量操作确认
            'confirmation_timeout': settings.get('confirmation_timeout', 30),  # 确认超时时间（秒）
        }
        
        # 操作统计
        self.operation_stats = {
            'start_time': time.time(),
            'files_processed': 0,
            'files_renamed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'last_operation_time': time.time(),
            'sandbox_operations': 0,
            'confirmed_operations': 0,
            'rejected_operations': 0,
        }
        
        # 沙盒模式相关
        self.sandbox_mode = False
        self.sandbox_directory = None
        self.sandbox_mapping = {}  # 原始路径到沙盒路径的映射
        self.sandbox_operations = []  # 沙盒操作记录
        
        # 安全确认相关
        self.pending_confirmations = {}  # 待确认的操作
        self.confirmation_history = []  # 确认历史
        
        # 文件路径设置
        self.history_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            HISTORY_FILE
        )
        self.cache_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            CACHE_FILE
        )
    
    # === 初始化方法组 ===
    def _init_core_components(self, settings: dict):
        """初始化核心组件"""
        self.settings = settings
        self.cache = {}
        self.history = []
        self.history_buffer = []
        self.history_file = "rename_history.json"
        # 移除这里的cache_file设置，让后面的代码统一设置
        
        # 文件类型设置
        self.video_exts = settings.get('video_exts', ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'])
        self.meta_exts = settings.get('meta_exts', ['.srt', '.ass', '.ssa', '.sub', '.idx', '.nfo'])
        
        # 模板设置
        self.movie_template = settings.get('movie_template', '{title} ({year}){ext}')
        self.tv_template = settings.get('tv_template', '{title}.S{season:02d}E{episode:02d}{ext}')
        self.special_template = settings.get('special_template', '{title}.特别篇.E{episode:02d}{ext}')
        
        # 初始化日志器
        self.logger = logging.getLogger("MediaRenamer")
        
        # 错误统计
        self.error_counts = defaultdict(int)
        self.error_contexts = []
        self.max_errors = settings.get('max_errors', 100)
    
    def _init_security_components(self, settings: dict):
        """初始化安全组件"""
        self.sandbox_mode = False
        self.sandbox_directory = None
        self.sandbox_mapping = {}
        self.sandbox_operations = []
        
        # 安全设置
        self.security_settings = settings.get('security', {})
        self.enable_sandbox = self.security_settings.get('enable_sandbox', False)
        self.enable_confirmation = self.security_settings.get('enable_confirmation', True)
        self.max_files_per_operation = self.security_settings.get('max_files_per_operation', 1000)
    
    def _init_performance_components(self, settings: dict):
        """初始化性能组件"""
        self.performance_monitor = PerformanceMonitor()
        self.operation_stats = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'error_files': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 缓存优化设置
        self._cache_buffer = {}
        self._dirty_flags = set()
        self._flush_threshold = 100
        self._cache_write_count = 0
    
    def _init_logging_components(self, settings: dict):
        """初始化日志组件"""
        self.logger = logging.getLogger("MediaRenamer")
        self.error_handler = ErrorHandler(self.logger)
        self.security_logger = SecurityLogger(self.logger)
        self.performance_logger = PerformanceLogger(self.logger)
        
        # 设置日志
        setup_logging()
        
        # 初始化增强组件
        self.security_logger = SecurityLogger(self.logger)
        self.performance_logger = PerformanceLogger(self.logger)
        self.error_handler = ErrorHandler(self.logger)
        
        # v1.3新增：集成配置管理器和性能监控器
        try:
            self.config_manager = config_manager
            self.pattern_recognizer = pattern_recognizer
            self.performance_monitor = performance_monitor
            
            # 加载配置
            if self.settings.get("backup_enabled", True):
                self.config_manager.load_config()
            
            # 启动性能监控
            if self.settings.get("performance_monitoring", True):
                self.performance_monitor.start_operation("initialization")
        except NameError:
            # 如果全局变量未定义，创建本地实例
            self.config_manager = ConfigManager()
            self.pattern_recognizer = PatternRecognizer()
            self.performance_monitor = PerformanceMonitor()
            self.logger.warning("使用本地配置管理器实例")
        
        # 安全设置
        self.security_settings = {
            'max_file_size_mb': settings.get('max_file_size_mb', 50000),  # 50GB
            'allowed_extensions': set(settings.get('video_extensions', []) + 
                                    settings.get('metadata_extensions', [])),
            'forbidden_paths': settings.get('forbidden_paths', ['/system', '/boot', '/etc', '/usr', '/var', '/proc', '/dev', 'C:\\Windows', 'C:\\System32']),
            'max_files_per_operation': settings.get('max_files_per_operation', 10000),
            'enable_path_validation': settings.get('enable_path_validation', True),
            'enable_file_size_check': settings.get('enable_file_size_check', True),
            'enable_suspicious_detection': settings.get('enable_suspicious_detection', True),
            # 新增：沙盒模式和安全确认设置
            'enable_sandbox_mode': settings.get('enable_sandbox_mode', False),
            'sandbox_directory': settings.get('sandbox_directory'),
            'enable_operation_confirmation': settings.get('enable_operation_confirmation', True),
            'confirmation_threshold': settings.get('confirmation_threshold', 10),  # 超过此数量的操作需要确认
            'enable_destructive_operation_confirmation': settings.get('enable_destructive_operation_confirmation', True),  # 删除/覆盖操作确认
            'enable_batch_confirmation': settings.get('enable_batch_confirmation', True),  # 批量操作确认
            'confirmation_timeout': settings.get('confirmation_timeout', 30),  # 确认超时时间（秒）
        }
        
        # 操作统计
        self.operation_stats = {
            'start_time': time.time(),
            'files_processed': 0,
            'files_renamed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'last_operation_time': time.time(),
            'sandbox_operations': 0,
            'confirmed_operations': 0,
            'rejected_operations': 0,
        }
        
        # 沙盒模式相关
        self.sandbox_mode = False
        self.sandbox_directory = None
        self.sandbox_mapping = {}  # 原始路径到沙盒路径的映射
        self.sandbox_operations = []  # 沙盒操作记录
        
        # 安全确认相关
        self.pending_confirmations = {}  # 待确认的操作
        self.confirmation_history = []  # 确认历史
        
        # 文件路径设置
        self.history_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            HISTORY_FILE
        )
        self.cache_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            CACHE_FILE
        )
        
        # 增量扫描与断点续传优化
        self.checkpoint_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'checkpoint.json'
        )
        self.checkpoint = self._load_checkpoint() or {}
        
        # 缓存相关
        self.cache = self._load_cache() or {}
        self.preview_data = []  # 存储预览数据
        self.last_scan_time = 0  # 上次扫描时间
        self.hash_cache = {}  # 文件哈希值缓存
        self.error_files = []  # 新增：记录错误文件及原因
        
        # 检查断点续传
        if self.checkpoint.get('resume_enabled', False):
            self._resume_from_checkpoint()
        
        # I/O优化：新增缓存
        self.dir_files_cache = {}  # 目录文件列表缓存
        self.file_exists_cache = {}  # 文件存在性缓存
        self.metadata_cache = {}  # 元数据文件缓存
        self.history_buffer = []  # 历史记录缓冲区
        self.history_buffer_size = 50  # 缓冲区大小
        self.pending_cache_updates = []  # 待更新的缓存项
        self.file_hash_cache = {}  # 文件哈希值缓存（用于增量扫描）
        self.processing_queue = []  # 待处理文件队列
        self.processed_files = set()  # 已处理文件集合
        self.failed_files = set()  # 失败文件集合
        
        # 批量操作优化
        self.batch_mode = False  # 批量模式标志
        self.batch_directories = []  # 批量处理目录列表
        self.batch_rules = {}  # 批量重命名规则
        self.parallel_workers = 4  # 并行工作线程数
        
        # 编译正则表达式（电影和电视剧通用）-- 优化1：简化正则表达式提高效率
        self.year_pattern = re.compile(r'(\d{4})')  # 优化后的年份模式
        self.episode_patterns = [
            re.compile(r"S(\d{1,2})[ ._\-]*E(\d{1,3})", re.IGNORECASE),  # S01E02
            re.compile(r"(\d{1,2})[xX](\d{1,3})"),                        # 1x02
            re.compile(r"S(\d{1,2})[ ._\-]*EP?(\d{1,3})", re.IGNORECASE),# S01EP02/S1EP2
            re.compile(r"EP?(\d{1,3})", re.IGNORECASE),                    # EP02/E02
            re.compile(r"[Ee][ ._\-]?(\d{1,3})", re.IGNORECASE),          # E02
            re.compile(r"第\s*(\d{1,3})\s*[集话回章]", re.UNICODE),         # 第2集/第2话
            re.compile(r"(\d{1,3})[ ._\-]of[ ._\-](\d{1,3})", re.IGNORECASE), # 2 of 12
            re.compile(r"(\d{1,2})[ ._\-](\d{1,3})"),                    # 1-02, 1_02
            re.compile(r"\[(\d{1,3})\]"),                                # [01]
            re.compile(r"【(\d{1,3})】"),                                  # 【01】
            # 新增中文文件名格式支持
            re.compile(r"(\d{1,3})\s*$", re.UNICODE),                     # 文件名末尾的数字 (如: 宝莲灯前传 01)
            re.compile(r"\s+(\d{1,3})\s*\.", re.UNICODE),                 # 空格+数字+扩展名 (如: 宝莲灯前传 01.mp4)
            re.compile(r"[^\d](\d{1,3})[^\d]", re.UNICODE),               # 非数字+数字+非数字 (通用格式)
        ]
        self.special_pattern = re.compile(r"(特辑|特别篇|Special)", re.IGNORECASE)
        
        # 沙盒模式和安全确认功能
        self._init_sandbox_mode()
        self._init_operation_confirmation()
        
        # 注册程序退出时的清理函数
        import atexit
        atexit.register(self._cleanup_on_exit)
        
        # 记录初始化完成
        self.logger.info("MediaRenamer 初始化完成，安全防护已启用")
        self.performance_logger.log_memory_usage("初始化")

    def _init_sandbox_mode(self):
        """初始化沙盒模式"""
        self.sandbox_mode = self.security_settings.get('enable_sandbox_mode', False)
        self.sandbox_directory = self.security_settings.get('sandbox_directory')
        
        if self.sandbox_mode and not self.sandbox_directory:
            # 自动创建沙盒目录
            import tempfile
            self.sandbox_directory = os.path.join(
                tempfile.gettempdir(), 
                f"media_renamer_sandbox_{int(time.time())}"
            )
            self.security_settings['sandbox_directory'] = self.sandbox_directory
        
        if self.sandbox_directory and not os.path.exists(self.sandbox_directory):
            try:
                os.makedirs(self.sandbox_directory, exist_ok=True)
                self.logger.info(f"沙盒目录已创建: {self.sandbox_directory}")
            except Exception as e:
                self.logger.error(f"创建沙盒目录失败: {e}")
                self.sandbox_mode = False

    def _init_operation_confirmation(self):
        """初始化操作确认功能"""
        self.confirmation_enabled = self.security_settings.get('enable_operation_confirmation', True)
        self.confirmation_threshold = self.security_settings.get('confirmation_threshold', 10)
        self.destructive_confirmation = self.security_settings.get('enable_destructive_operation_confirmation', True)
        self.batch_confirmation = self.security_settings.get('enable_batch_confirmation', True)
        self.confirmation_timeout = self.security_settings.get('confirmation_timeout', 30)

    def enable_sandbox_mode(self, sandbox_dir: Optional[str] = None) -> bool:
        """启用沙盒模式"""
        try:
            if sandbox_dir:
                self.sandbox_directory = sandbox_dir
            elif not self.sandbox_directory:
                import tempfile
                self.sandbox_directory = os.path.join(
                    tempfile.gettempdir(), 
                    f"media_renamer_sandbox_{int(time.time())}"
                )
            
            if not os.path.exists(self.sandbox_directory):
                os.makedirs(self.sandbox_directory, exist_ok=True)
            
            self.sandbox_mode = True
            self.security_settings['enable_sandbox_mode'] = True
            self.security_settings['sandbox_directory'] = self.sandbox_directory
            
            self.logger.info(f"沙盒模式已启用: {self.sandbox_directory}")
            print(Fore.GREEN + f"✅ 沙盒模式已启用: {self.sandbox_directory}")
            return True
            
        except Exception as e:
            self.logger.error(f"启用沙盒模式失败: {e}")
            print(Fore.RED + f"❌ 启用沙盒模式失败: {e}")
            return False

    def disable_sandbox_mode(self) -> bool:
        """禁用沙盒模式"""
        try:
            self.sandbox_mode = False
            self.security_settings['enable_sandbox_mode'] = False
            
            # 清理沙盒目录（可选）
            if self.sandbox_directory and os.path.exists(self.sandbox_directory):
                try:
                    response = input(Fore.YELLOW + "是否清理沙盒目录？(y/N): ").strip().lower()
                    cleanup = response in ['y', 'yes', '是', '1', 'true']
                    if cleanup:
                        shutil.rmtree(self.sandbox_directory)
                        self.logger.info(f"沙盒目录已清理: {self.sandbox_directory}")
                except (KeyboardInterrupt, EOFError):
                    self.logger.info("用户取消清理沙盒目录")
            
            self.logger.info("沙盒模式已禁用")
            print(Fore.GREEN + "✅ 沙盒模式已禁用")
            return True
            
        except Exception as e:
            self.logger.error(f"禁用沙盒模式失败: {e}")
            print(Fore.RED + f"❌ 禁用沙盒模式失败: {e}")
            return False

    def get_sandbox_path(self, original_path: str) -> str:
        """获取文件在沙盒中的路径"""
        if not self.sandbox_mode or not self.sandbox_directory:
            return original_path
        
        # 保持目录结构
        rel_path = os.path.relpath(original_path, self.settings["folder_path"])
        sandbox_path = os.path.join(self.sandbox_directory, rel_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
        
        return sandbox_path

    def copy_to_sandbox(self, file_path: str) -> bool:
        """将文件复制到沙盒目录"""
        if not self.sandbox_mode:
            return True
        
        try:
            sandbox_path = self.get_sandbox_path(file_path)
            
            if not os.path.exists(sandbox_path):
                shutil.copy2(file_path, sandbox_path)
                self.sandbox_mapping[file_path] = sandbox_path
                self.logger.debug(f"文件已复制到沙盒: {file_path} → {sandbox_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"复制文件到沙盒失败: {file_path} - {e}")
            return False

    def require_confirmation(self, operation: str, files: List[str], operation_type: str = "normal") -> bool:
        """检查是否需要用户确认"""
        if not self.confirmation_enabled:
            return True
        
        # 检查操作类型
        if operation_type == "destructive" and not self.destructive_confirmation:
            return True
        
        if operation_type == "batch" and not self.batch_confirmation:
            return True
        
        # 检查文件数量阈值
        if len(files) <= self.confirmation_threshold:
            return True
        
        # 需要确认
        print(Fore.YELLOW + "\n" + "="*60)
        print(Fore.RED + "⚠️ 操作确认")
        print(Fore.YELLOW + "="*60)
        print(Fore.CYAN + f"操作类型: {operation}")
        print(Fore.CYAN + f"文件数量: {len(files)}")
        print(Fore.CYAN + f"操作类型: {operation_type}")
        
        if len(files) <= 20:
            print(Fore.YELLOW + "\n涉及文件:")
            for i, file_path in enumerate(files[:10], 1):
                print(f"  {i}. {os.path.basename(file_path)}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
        else:
            print(Fore.YELLOW + f"\n涉及 {len(files)} 个文件")
        
        # 沙盒模式提示
        if self.sandbox_mode:
            print(Fore.GREEN + f"\n🔒 沙盒模式已启用，操作将在沙盒目录中执行: {self.sandbox_directory}")
        
        # 确认选项
        print(Fore.CYAN + "\n确认选项:")
        print("  y/Y - 确认执行")
        print("  n/N - 取消操作")
        print("  p/P - 预览模式")
        print("  s/S - 启用沙盒模式")
        print("  d/D - 禁用沙盒模式")
        print(f"  t/T - 设置超时时间 (当前: {self.confirmation_timeout}秒)")
        
        try:
            import threading
            import queue
            
            # 设置超时
            response_queue = queue.Queue()
            
            def get_user_input():
                try:
                    response = input(Fore.YELLOW + f"\n请确认操作 (超时: {self.confirmation_timeout}秒): ").strip().lower()
                    response_queue.put(response)
                except (KeyboardInterrupt, EOFError):
                    response_queue.put("n")
            
            # 启动输入线程
            input_thread = threading.Thread(target=get_user_input, daemon=True)
            input_thread.start()
            
            # 等待用户输入或超时
            try:
                response = response_queue.get(timeout=self.confirmation_timeout)
            except queue.Empty:
                print(Fore.RED + f"\n⏰ 确认超时 ({self.confirmation_timeout}秒)，操作已取消")
                return False
            
            # 处理用户响应
            if response in ['y', 'yes', '是', '1', 'true']:
                print(Fore.GREEN + "✅ 操作已确认")
                self.operation_stats['confirmed_operations'] += 1
                return True
            elif response in ['n', 'no', '否', '0', 'false']:
                print(Fore.RED + "❌ 操作已取消")
                self.operation_stats['rejected_operations'] += 1
                return False
            elif response in ['p', 'preview']:
                print(Fore.CYAN + "🔍 切换到预览模式")
                self.settings["preview_only"] = True
                return True
            elif response in ['s', 'sandbox']:
                print(Fore.GREEN + "🔒 启用沙盒模式")
                self.enable_sandbox_mode()
                return True
            elif response in ['d', 'disable_sandbox']:
                print(Fore.YELLOW + "🔓 禁用沙盒模式")
                self.disable_sandbox_mode()
                return True
            elif response in ['t', 'timeout']:
                try:
                    new_timeout = input(Fore.YELLOW + "请输入新的超时时间(秒): ").strip()
                    self.confirmation_timeout = int(new_timeout)
                    self.security_settings['confirmation_timeout'] = self.confirmation_timeout
                    print(Fore.GREEN + f"✅ 超时时间已设置为 {self.confirmation_timeout} 秒")
                    return self.require_confirmation(operation, files, operation_type)
                except ValueError:
                    print(Fore.RED + "❌ 无效的超时时间")
                    return False
            else:
                print(Fore.RED + "❌ 无效选择，操作已取消")
                self.operation_stats['rejected_operations'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"确认操作失败: {e}")
            print(Fore.RED + f"❌ 确认操作失败: {e}")
            return False

    def safe_rename_operation(self, old_path: str, new_path: str, operation_type: str = "normal") -> bool:
        """安全的重命名操作"""
        try:
            # 安全检查
            if not self._safe_file_operation("rename", old_path, lambda: None):
                return False
            
            # 沙盒模式处理
            if self.sandbox_mode:
                sandbox_old = self.get_sandbox_path(old_path)
                sandbox_new = self.get_sandbox_path(new_path)
                
                # 确保文件在沙盒中
                if not os.path.exists(sandbox_old):
                    if not self.copy_to_sandbox(old_path):
                        return False
                
                # 在沙盒中执行重命名
                if os.name == 'nt':
                    shutil.move(sandbox_old, sandbox_new)
                else:
                    os.rename(sandbox_old, sandbox_new)
                
                # 记录沙盒操作
                self.sandbox_operations.append({
                    'time': datetime.now().isoformat(),
                    'operation': 'rename',
                    'original_old': old_path,
                    'original_new': new_path,
                    'sandbox_old': sandbox_old,
                    'sandbox_new': sandbox_new,
                    'type': operation_type
                })
                
                self.operation_stats['sandbox_operations'] += 1
                self.logger.info(f"沙盒重命名: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
                
            else:
                # 正常模式
                if os.name == 'nt':
                    shutil.move(old_path, new_path)
                else:
                    os.rename(old_path, new_path)
                
                self.logger.info(f"重命名: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "重命名操作", old_path, "rename")
            return False

    def get_sandbox_status(self) -> dict:
        """获取沙盒状态信息"""
        return {
            'enabled': self.sandbox_mode,
            'directory': self.sandbox_directory,
            'file_count': len(self.sandbox_mapping),
            'operation_count': len(self.sandbox_operations),
            'total_operations': self.operation_stats['sandbox_operations']
        }

    def show_sandbox_info(self):
        """显示沙盒信息"""
        status = self.get_sandbox_status()
        
        print(Fore.BLUE + "\n" + "="*60)
        print(Fore.CYAN + "沙盒模式信息")
        print(Fore.BLUE + "="*60)
        print(Fore.CYAN + f"状态: {'启用' if status['enabled'] else '禁用'}")
        
        if status['enabled']:
            print(Fore.CYAN + f"沙盒目录: {status['directory']}")
            print(Fore.CYAN + f"映射文件数: {status['file_count']}")
            print(Fore.CYAN + f"操作记录数: {status['operation_count']}")
            print(Fore.CYAN + f"总操作数: {status['total_operations']}")
            
            if status['operation_count'] > 0:
                print(Fore.YELLOW + "\n最近操作:")
                for op in self.sandbox_operations[-5:]:
                    print(f"  {op['time']}: {os.path.basename(op['original_old'])} → {os.path.basename(op['original_new'])}")
        
        print("="*60)

    def _cleanup_on_exit(self):
        """程序退出时的清理工作"""
        try:
            # 最终化历史记录
            self._finalize_history()
            
            # 保存缓存
            self._save_cache()
            
            # 清理沙盒（如果启用）
            if self.sandbox_mode and self.sandbox_directory:
                cleanup = self.security_settings.get('auto_cleanup_sandbox', False)
                if cleanup and os.path.exists(self.sandbox_directory):
                    shutil.rmtree(self.sandbox_directory)
                    self.logger.info(f"沙盒目录已自动清理: {self.sandbox_directory}")
            
            self.logger.info("程序退出清理完成")
            
        except Exception as e:
            self.logger.error(f"程序退出清理失败: {e}")

    def _load_cache(self) -> Optional[dict]:
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                    # 验证缓存数据
                    if self._validate_cache_data(cache_data):
                        self.cache = cache_data
                        self.logger.info("✅ 缓存加载成功")
                        return cache_data
                    else:
                        self.logger.warning("⚠️ 缓存数据无效，将重新扫描")
                        
        except Exception as e:
            self.logger.error(f"❌ 加载缓存失败: {e}")
            
        return None
    
    def _validate_cache_data(self, cache_data: dict) -> bool:
        """验证缓存数据有效性"""
        try:
            # 检查基本结构
            if not isinstance(cache_data, dict):
                return False
                
            # 检查必要字段
            required_fields = ['version', 'last_scan', 'files', 'folders']
            for field in required_fields:
                if field not in cache_data:
                    return False
            
            # 检查版本兼容性
            if cache_data.get('version') != '1.3':
                return False
                
            return True
            
        except Exception:
            return False
    
    def should_refresh_cache(self, folder_path: str) -> bool:
        """智能判断是否需要刷新缓存"""
        if not self.cache:
            return True
            
        try:
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                return True
            
            # 获取文件夹修改时间
            folder_mtime = os.path.getmtime(folder_path)
            
            # 检查缓存中的文件夹信息
            if 'folders' not in self.cache:
                return True
                
            folder_info = self.cache['folders'].get(folder_path)
            if not folder_info:
                return True
            
            # 检查修改时间
            cached_mtime = folder_info.get('mtime', 0)
            if folder_mtime > cached_mtime:
                self.logger.info(f"📁 文件夹已修改，需要刷新缓存: {folder_path}")
                return True
            
            # 检查缓存TTL
            cache_ttl = self.settings.get('cache_ttl', 3600)
            current_time = time.time()
            last_scan = self.cache.get('last_scan', 0)
            
            if current_time - last_scan > cache_ttl:
                self.logger.info(f"⏰ 缓存已过期 (TTL: {cache_ttl}秒)")
                return True
            
            self.logger.info("✅ 缓存有效，跳过扫描")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 检查缓存状态失败: {e}")
            return True

    def _save_cache(self):
        """保存缓存数据（优化版）"""
        try:
            # 添加缓存版本和统计信息
            self.cache['version'] = 2
            self.cache['total_files'] = len(self.cache.get('files', {}))
            self.cache['total_dirs'] = len(self.cache.get('dirs', []))
            self.cache['cache_size_mb'] = len(json.dumps(self.cache, ensure_ascii=False).encode('utf-8')) / (1024 * 1024)
            
            # 异步保存缓存（避免阻塞主线程）
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"缓存保存成功: {self.cache['total_files']}个文件, {self.cache['cache_size_mb']:.2f}MB")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")

    def _validate_file_cache(self, file_path: str, file_info: dict) -> bool:
        """验证文件缓存是否有效"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # 检查文件修改时间
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = file_info.get('mtime', 0)
            
            if abs(current_mtime - cached_mtime) > 1:  # 允许1秒误差
                return False
            
            # 检查文件大小
            current_size = os.path.getsize(file_path)
            cached_size = file_info.get('size', 0)
            
            if current_size != cached_size:
                return False
            
            return True
        except OSError:
            return False

    def _load_checkpoint(self) -> Optional[dict]:
        """加载断点续传数据"""
        if not os.path.exists(self.checkpoint_file):
            return None
            
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                self.logger.info("断点续传数据加载成功")
                return checkpoint
        except Exception as e:
            self.logger.warning(f"加载断点续传数据失败: {e}")
            return None

    def _save_checkpoint(self):
        """保存断点续传数据"""
        try:
            checkpoint_data = {
                'timestamp': time.time(),
                'resume_enabled': True,
                'processed_files': list(self.processed_files),
                'failed_files': list(self.failed_files),
                'processing_queue': self.processing_queue,
                'current_directory': self.settings.get('folder_path', ''),
                'batch_mode': self.batch_mode,
                'batch_directories': self.batch_directories,
                'total_files': len(self.processing_queue) + len(self.processed_files) + len(self.failed_files)
            }
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug("断点续传数据已保存")
        except Exception as e:
            self.logger.error(f"保存断点续传数据失败: {e}")

    def _resume_from_checkpoint(self):
        """从断点恢复处理"""
        if not self.checkpoint:
            return
            
        print(Fore.YELLOW + "\n🔄 检测到断点续传数据")
        print(Fore.CYAN + f"已处理文件: {len(self.checkpoint.get('processed_files', []))}")
        print(Fore.RED + f"失败文件: {len(self.checkpoint.get('failed_files', []))}")
        print(Fore.BLUE + f"待处理文件: {len(self.checkpoint.get('processing_queue', []))}")
        
        try:
            response = input(Fore.YELLOW + "是否从断点继续处理?(Y/n): ").strip().lower()
            if not response or response in ['y', 'yes', '是', '1', 'true']:
                self.processed_files = set(self.checkpoint.get('processed_files', []))
                self.failed_files = set(self.checkpoint.get('failed_files', []))
                self.processing_queue = self.checkpoint.get('processing_queue', [])
                self.batch_mode = self.checkpoint.get('batch_mode', False)
                self.batch_directories = self.checkpoint.get('batch_directories', [])
                
                print(Fore.GREEN + "✅ 断点续传已启用")
            else:
                # 清除断点数据
                self._clear_checkpoint()
                print(Fore.YELLOW + "断点续传已禁用")
        except (KeyboardInterrupt, EOFError):
            # 清除断点数据
            self._clear_checkpoint()
            print(Fore.YELLOW + "断点续传已禁用")

    def _clear_checkpoint(self):
        """清除断点续传数据"""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
            self.checkpoint = {}
            self.processed_files.clear()
            self.failed_files.clear()
            self.processing_queue.clear()
            self.logger.info("断点续传数据已清除")
        except Exception as e:
            self.logger.error(f"清除断点续传数据失败: {e}")

    def _incremental_scan(self, folder_path: str) -> List[str]:
        """增量扫描：只扫描变动的文件"""
        self.logger.info("执行增量扫描")
        
        if not self.cache:
            # 如果没有缓存，执行完整扫描
            self.build_directory_cache(folder_path)
            return list(self.cache.get('files', {}).keys())
        
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        changed_files = []
        
        # 检查现有文件是否有变化
        for file_path, file_info in self.cache.get('files', {}).items():
            if not self._validate_file_cache(file_path, file_info):
                changed_files.append(file_path)
        
        # 扫描新文件
        for root, _, files in os.walk(folder_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() not in video_exts:
                    continue
                
                full_path = os.path.join(root, file)
                if full_path not in self.cache.get('files', {}):
                    changed_files.append(full_path)
        
        # 检查删除的文件
        for file_path in self.cache.get('files', {}):
            if not os.path.exists(file_path):
                changed_files.append(file_path)
        
        self.logger.info(f"增量扫描完成: 发现 {len(changed_files)} 个变动文件")
        return changed_files

    def _calculate_file_hash_fast(self, file_path: str) -> str:
        """快速计算文件哈希（仅用于增量扫描）"""
        if file_path in self.file_hash_cache:
            return self.file_hash_cache[file_path]
        
        try:
            # 只读取文件的前1MB来计算快速哈希
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                data = f.read(1024 * 1024)  # 1MB
                hasher.update(data)
            
            file_hash = hasher.hexdigest()
            self.file_hash_cache[file_path] = file_hash
            return file_hash
        except Exception as e:
            self.logger.warning(f"计算文件快速哈希失败 {file_path}: {e}")
            return ""

    def _batch_process_directories(self, directories: List[str]) -> bool:
        """批量处理多个目录"""
        self.batch_mode = True
        self.batch_directories = directories
        
        print(Fore.BLUE + f"\n🔄 批量处理模式: {len(directories)} 个目录")
        
        total_files = 0
        total_processed = 0
        total_skipped = 0
        total_errors = 0
        
        start_time = time.time()
        
        # 并行扫描所有目录
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # 提交所有目录的扫描任务
            future_to_dir = {
                executor.submit(self._scan_directory_for_batch, directory): directory
                for directory in directories
            }
            
            # 收集所有文件
            all_files = []
            for future in concurrent.futures.as_completed(future_to_dir):
                directory = future_to_dir[future]
                try:
                    files = future.result()
                    all_files.extend(files)
                    total_files += len(files)
                    print(Fore.CYAN + f"目录 {os.path.basename(directory)}: 发现 {len(files)} 个文件")
                except Exception as e:
                    self.logger.error(f"扫描目录失败 {directory}: {e}")
                    print(Fore.RED + f"❌ 扫描目录失败: {directory}")
        
        # 构建处理队列
        self.processing_queue = all_files
        
        # 并行处理文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            future_to_file = {
                executor.submit(self._process_file_batch, file_info): file_info
                for file_info in all_files
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
                file_info = future_to_file[future]
                try:
                    result = future.result()
                    if result == "processed":
                        total_processed += 1
                        self.processed_files.add(file_info['file_path'])
                    elif result == "skipped":
                        total_skipped += 1
                    elif result == "error":
                        total_errors += 1
                        self.failed_files.add(file_info['file_path'])
                    
                    # 保存断点
                    if i % 100 == 0:
                        self._save_checkpoint()
                    
                    # 进度显示
                    if i % 50 == 0:
                        elapsed = time.time() - start_time
                        print(Fore.CYAN + f"已处理 {i}/{total_files} 个文件, 耗时: {elapsed:.1f}秒...")
                        
                except Exception as e:
                    total_errors += 1
                    self.failed_files.add(file_info['file_path'])
                    self.logger.error(f"处理文件异常: {file_info['file_path']}\n{traceback.format_exc()}")
        
        elapsed = time.time() - start_time
        
        # 显示结果
        print(Fore.BLUE + "\n" + "="*60)
        print(Fore.CYAN + f"批量处理完成! 共处理 {total_files} 个文件")
        print(Fore.GREEN + f"成功重命名: {total_processed} 个文件")
        print(Fore.YELLOW + f"跳过文件: {total_skipped} 个")
        if total_errors > 0:
            print(Fore.RED + f"错误文件: {total_errors} 个")
        print(Fore.CYAN + f"总耗时: {elapsed:.2f} 秒")
        print("="*60)
        
        # 最终化历史记录
        self._finalize_history()
        
        # 清除断点数据
        self._clear_checkpoint()
        
        return True

    def _scan_directory_for_batch(self, directory: str) -> List[dict]:
        """为批量处理扫描单个目录"""
        if not os.path.isdir(directory):
            return []
        
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        files = []
        
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext.lower() in video_exts:
                    file_path = os.path.join(root, filename)
                    try:
                        file_info = {
                            'file_path': file_path,
                            'directory': root,
                            'filename': filename,
                            'size': os.path.getsize(file_path),
                            'mtime': os.path.getmtime(file_path)
                        }
                        files.append(file_info)
                    except OSError as e:
                        self.logger.warning(f"无法访问文件 {file_path}: {e}")
        
        return files

    def _process_file_batch(self, file_info: dict) -> Union[str, bool]:
        """批量处理单个文件"""
        file_path = file_info['file_path']
        directory = file_info['directory']
        filename = file_info['filename']
        
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        meta_exts = self.settings["metadata_extensions"]
        skip_existing = self.settings["skip_existing"]
        
        return self.process_file(
            directory, filename, file_path, 
            self.settings["preview_only"], 
            video_exts, meta_exts, skip_existing
        )

    def _incremental_cache_update(self, folder_path: str):
        """增量更新缓存"""
        self.logger.info("执行增量缓存更新")
        
        if not self.cache:
            self.build_directory_cache(folder_path)
            return
        
        current_time = time.time()
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        
        # 验证现有缓存
        valid_files = {}
        invalid_files = set()
        
        for file_path, file_info in self.cache.get('files', {}).items():
            if self._validate_file_cache(file_path, file_info):
                valid_files[file_path] = file_info
            else:
                invalid_files.add(file_path)
        
        # 扫描新文件和目录
        new_files = {}
        new_dirs = set()
        
        for root, _, files in os.walk(folder_path):
            if root not in self.cache.get('dirs', []):
                new_dirs.add(root)
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() not in video_exts:
                    continue
                
                full_path = os.path.join(root, file)
                if full_path not in valid_files:
                    try:
                        file_info = {
                            'size': os.path.getsize(full_path),
                            'mtime': os.path.getmtime(full_path),
                            'name': file
                        }
                        new_files[full_path] = file_info
                    except OSError as e:
                        self.logger.warning(f"无法访问文件 {full_path}: {e}")
        
        # 更新缓存
        self.cache['files'].update(new_files)
        self.cache['dirs'].extend(list(new_dirs))
        self.cache['last_scan'] = current_time
        
        # 更新目录文件映射
        for file_path in new_files:
            root = os.path.dirname(file_path)
            if root not in self.cache['dir_files']:
                self.cache['dir_files'][root] = []
            self.cache['dir_files'][root].append(file_path)
        
        # 移除无效文件
        for file_path in invalid_files:
            if file_path in self.cache['files']:
                del self.cache['files'][file_path]
            root = os.path.dirname(file_path)
            if root in self.cache['dir_files'] and file_path in self.cache['dir_files'][root]:
                self.cache['dir_files'][root].remove(file_path)
        
        # 统计更新信息
        updated_count = len(new_files)
        removed_count = len(invalid_files)
        self.logger.info(f"增量更新完成: 新增{updated_count}个文件, 移除{removed_count}个文件")
        
        # 保存更新后的缓存
        self._save_cache()

    def build_directory_cache(self, folder_path: str):
        """构建目录缓存（I/O优化版）"""
        current_time = time.time()
        
        # 检查缓存是否有效
        cache_ttl = self.settings.get('cache_ttl', 300)
        if self.cache and current_time - self.cache.get('last_scan', 0) < cache_ttl:
            self.logger.info("使用现有缓存")
            return
        
        # 如果缓存存在但过期，尝试增量更新
        if self.cache and self.settings.get('enable_incremental_cache', True):
            self._incremental_cache_update(folder_path)
            return
        
        # 完全重建缓存
        self.logger.info(f"构建目录缓存: {folder_path}")
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        meta_exts = [ext.lower() for ext in self.settings["metadata_extensions"]]
        
        self.cache = {
            'dirs': [],
            'dir_files': {},  # 按目录分组的文件
            'files': {},
            'metadata_files': {},  # 新增：元数据文件缓存
            'last_scan': current_time,
            'version': 3
        }
        
        # 清空I/O优化缓存
        self.dir_files_cache.clear()
        self.file_exists_cache.clear()
        self.metadata_cache.clear()
        
        total_files = 0
        total_dirs = 0
        total_metadata = 0
        
        for root, _, files in os.walk(folder_path):
            # 缓存目录信息
            self.cache['dirs'].append(root)
            self.cache['dir_files'][root] = []
            self.cache['metadata_files'][root] = []
            total_dirs += 1
            
            # 缓存目录文件列表（I/O优化）
            self.dir_files_cache[root] = set(files)
            
            # 分类处理文件
            for file in files:
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                full_path = os.path.join(root, file)
                
                # 缓存文件存在性（I/O优化）
                self.file_exists_cache[full_path] = True
                
                if ext_lower in video_exts:
                    # 视频文件
                    try:
                        file_info = {
                            'size': os.path.getsize(full_path),
                            'mtime': os.path.getmtime(full_path),
                            'name': file
                        }
                        self.cache['files'][full_path] = file_info
                        self.cache['dir_files'][root].append(full_path)
                        total_files += 1
                    except OSError as e:
                        self.logger.warning(f"无法访问文件 {full_path}: {e}")
                elif ext_lower in meta_exts:
                    # 元数据文件（I/O优化）
                    self.cache['metadata_files'][root].append(full_path)
                    self.metadata_cache[full_path] = {
                        'name': file,
                        'ext': ext_lower,
                        'base_name': os.path.splitext(file)[0]
                    }
                    total_metadata += 1
        
        # 保存缓存
        self._save_cache()
        self.logger.info(f"缓存构建完成: {total_files}个视频文件, {total_metadata}个元数据文件, {total_dirs}个目录")

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        if not self.cache:
            return {'status': 'no_cache'}
        
        stats = {
            'status': 'valid',
            'total_files': len(self.cache.get('files', {})),
            'total_dirs': len(self.cache.get('dirs', [])),
            'last_scan': self.cache.get('last_scan', 0),
            'cache_size_mb': self.cache.get('cache_size_mb', 0),
            'version': self.cache.get('version', 1)
        }
        
        # 计算缓存年龄
        current_time = time.time()
        stats['age_seconds'] = current_time - stats['last_scan']
        stats['age_minutes'] = stats['age_seconds'] / 60
        
        return stats

    def clear_cache(self):
        """清理缓存"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                self.logger.info("缓存文件已清理")
            
            self.cache = {}
            print(Fore.GREEN + "✅ 缓存已清理")
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
            print(Fore.RED + f"❌ 清理缓存失败: {e}")

    def show_cache_info(self):
        """显示缓存信息"""
        stats = self.get_cache_stats()
        
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.BLUE + " 缓存信息")
        print(Fore.CYAN + "="*60)
        
        if stats['status'] == 'no_cache':
            print(Fore.YELLOW + "📁 无缓存数据")
            return
        
        print(f"📊 文件总数: {stats['total_files']}")
        print(f"📁 目录总数: {stats['total_dirs']}")
        print(f"💾 缓存大小: {stats['cache_size_mb']:.2f} MB")
        print(f"🕒 缓存年龄: {stats['age_minutes']:.1f} 分钟")
        print(f"📋 缓存版本: v{stats['version']}")
        
        # 缓存状态评估
        cache_ttl = self.settings.get('cache_ttl', 300)
        if stats['age_seconds'] < cache_ttl:
            print(Fore.GREEN + f"✅ 缓存状态: 有效 (TTL: {cache_ttl}秒)")
        else:
            print(Fore.YELLOW + f"⚠️ 缓存状态: 已过期 (TTL: {cache_ttl}秒)")
        
        print("="*60)

    def process_directory(self) -> bool:
        """处理目录中的所有影视文件（并发优化版）"""
        folder_path = self.settings["folder_path"]
        preview = self.settings["preview_only"]
        video_exts = [ext.lower() for ext in self.settings["video_extensions"]]
        meta_exts = self.settings["metadata_extensions"]
        skip_existing = self.settings["skip_existing"]
        
        if not os.path.isdir(folder_path):
            self.logger.error(f"目录不存在: {folder_path}")
            print(Fore.RED + f"错误: 目录不存在 {folder_path}")
            return False
        
        # 构建目录缓存
        start_scan = time.time()
        self.build_directory_cache(folder_path)
        scan_time = time.time() - start_scan
        self.logger.info(f"目录扫描完成，耗时: {scan_time:.2f}秒")
        
        self.logger.info(f"开始处理目录: {folder_path}")
        print(Fore.BLUE + f"\n正在扫描目录: {folder_path} (扫描耗时: {scan_time:.2f}秒)")
        
        total_files = 0
        processed_files = 0
        skipped_files = 0
        error_files = 0
        
        start_time = time.time()
        
        # 重置预览数据
        self.preview_data = []
        self.hash_cache = {}  # 清空哈希缓存
        
        # 收集所有要处理的文件
        all_files_to_process = []
        for root in self.cache['dirs']:
            current_dir_files = self.cache['dir_files'].get(root, [])
            for file_path in current_dir_files:
                file_info = self.cache['files'].get(file_path, {})
                if not file_info:
                    continue
                all_files_to_process.append(file_path)
        
        # 批量操作确认
        if not preview and len(all_files_to_process) > 0:
            operation_type = "batch" if len(all_files_to_process) > self.confirmation_threshold else "normal"
            if not self.require_confirmation("批量重命名", all_files_to_process, operation_type):
                print(Fore.YELLOW + "操作已取消")
                return False
        
        # 处理所有目录
        for root in self.cache['dirs']:
            current_dir_files = self.cache['dir_files'].get(root, [])
            file_infos = []
            for file_path in current_dir_files:
                file_info = self.cache['files'].get(file_path, {})
                if not file_info:
                    continue
                file = file_info['name']
                file_infos.append((root, file, file_path))
            total_files += len(file_infos)
            
            # 多线程并发处理
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                future_to_file = {
                    executor.submit(self.process_file, root, file, file_path, preview, video_exts, meta_exts, skip_existing): (root, file, file_path)
                    for (root, file, file_path) in file_infos
                }
                
                for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
                    root, file, file_path = future_to_file[future]
                    try:
                        result = future.result(timeout=30)  # 添加超时
                    except concurrent.futures.TimeoutError:
                        result = "error"
                        error_info = {
                            'file': file,
                            'reason': '处理超时',
                            'dir': root,
                            'file_path': file_path,
                            'new_name': None,
                            'traceback': '处理超时30秒'
                        }
                        self.error_files.append(error_info)
                        self.logger.error(f"处理文件超时: {file_path}")
                        print(Fore.RED + f"  ❌ {file} (超时)")
                    except Exception as e:
                        result = "error"
                        tb = traceback.format_exc()
                        error_info = {
                            'file': file,
                            'reason': f'未处理异常: {e}',
                            'dir': root,
                            'file_path': file_path,
                            'new_name': None,
                            'traceback': tb
                        }
                        self.error_files.append(error_info)
                        self.logger.error(f"处理文件异常: {file_path}\n{tb}")
                        print(Fore.RED + f"  ❌ {file}")
                        print(f"    路径: {file_path}")
                        print(f"    目录: {root}")
                        print(f"    错误详情: {str(e)}")
                    
                    if result == "processed":
                        processed_files += 1
                    elif result == "skipped":
                        skipped_files += 1
                    elif result == "error":
                        error_files += 1
                    
                    # 进度显示（每50个文件显示一次）
                    if i % 50 == 0:
                        elapsed = time.time() - start_time
                        print(Fore.CYAN + f"已处理 {i} 个文件, 耗时: {elapsed:.1f}秒...")
                        self.logger.info(f"已处理 {i} 个文件, 耗时: {elapsed:.1f}秒...")
        
        elapsed = time.time() - start_time
        
        # 最终化历史记录（I/O优化）
        self._finalize_history()
        
        # 如果是预览模式，显示所有文件的重命名对比
        if preview and self.preview_data:
            self.show_folder_preview()
        
        print(Fore.BLUE + "\n" + "="*60)
        print(Fore.CYAN + f"扫描完成! 共处理 {total_files} 个文件")
        print(Fore.GREEN + f"成功重命名: {processed_files} 个文件")
        print(Fore.YELLOW + f"跳过文件: {skipped_files} 个")
        if error_files > 0:
            print(Fore.RED + f"错误文件: {error_files} 个")
        print(Fore.CYAN + f"总耗时: {elapsed:.2f} 秒")
        print("="*60)
        # 新增：允许用户查看跳过和错误文件
        if skipped_files > 0 or error_files > 0:
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.YELLOW + "📋 查看详细信息")
            print(Fore.CYAN + "="*60)
            print("v - 查看所有跳过和错误文件")
            print("s - 查看跳过文件")
            print("e - 查看错误文件")
            print("q - 跳过查看")
            print("Ctrl+C - 中断操作")
            
            try:
                action = input(Fore.YELLOW + "\n请选择操作: ").strip().lower()
                if action == 'v':
                    self._show_skipped_files()
                    self._show_error_files()
                elif action == 's':
                    self._show_skipped_files()
                elif action == 'e':
                    self._show_error_files()
                elif action == 'q':
                    print(Fore.CYAN + "跳过查看详细信息")
                else:
                    print(Fore.RED + "无效选择，跳过查看")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                return True
        
        self.logger.info(
            f"处理完成: 总计={total_files}, 成功={processed_files}, "
            f"跳过={skipped_files}, 错误={error_files}, 耗时={elapsed:.2f}秒"
        )
        return True

    def _show_skipped_files(self):
        """显示跳过的文件"""
        print(Fore.YELLOW + "\n" + "="*60)
        print(Fore.YELLOW + "📁 跳过文件列表")
        print(Fore.YELLOW + "="*60)
        
        skipped_count = 0
        
        # 检查预览数据中的跳过文件
        for data in self.preview_data:
            if not data.get('valid', True):
                print(f"  {Fore.YELLOW}⚠️  {data['old_name']} → {data['new_name']}")
                skipped_count += 1
        
        # 检查缓存中的跳过文件（非视频文件等）
        if hasattr(self, 'cache') and 'files' in self.cache:
            for file_path, file_info in self.cache['files'].items():
                file_name = file_info.get('name', os.path.basename(file_path))
                file_ext = os.path.splitext(file_name)[1].lower()
                
                # 检查是否为非视频文件
                if file_ext not in [ext.lower() for ext in self.settings.get("video_extensions", [])]:
                    print(f"  {Fore.YELLOW}⚠️  {file_name} (非视频文件)")
                    skipped_count += 1
        
        if skipped_count == 0:
            print(Fore.GREEN + "  没有跳过的文件")
        else:
            print(Fore.CYAN + f"\n  共跳过 {skipped_count} 个文件")

    def _show_error_files(self):
        """显示错误文件"""
        if not self.error_files:
            print(Fore.GREEN + "\n  没有错误文件")
            return
            
        print(Fore.RED + "\n" + "="*60)
        print(Fore.RED + "❌ 错误文件列表")
        print(Fore.RED + "="*60)
        
        # 分组展示
        from collections import defaultdict
        grouped = defaultdict(list)
        for err in self.error_files:
            grouped[err['reason']].append(err)
        
        for reason, items in grouped.items():
            print(Fore.MAGENTA + f"\n【{reason}】({len(items)}个文件)")
            for err in items:
                print(f"  {Fore.RED}❌ {err['file']}")
                print(f"    路径: {err['file_path']}")
                print(f"    目录: {err['dir']}")
                if err['new_name']:
                    print(f"    建议新名: {err['new_name']}")
                if err.get('traceback'):
                    print(f"    错误详情: {err['traceback'][:200]}...")
                print()

    def show_folder_preview(self):
        """显示整个文件夹的重命名预览（支持分页）"""
        # 修复4：修正字符串连接错误 -- 修复2
        print(Fore.CYAN + "\n" + "="*80)
        print(Fore.BLUE + " 文件夹重命名预览汇总")
        print(Fore.CYAN + "="*80)
        
        # 按目录分组预览数据
        dir_groups = {}
        for data in self.preview_data:
            dir_path = data['info']['dir_path']
            if dir_path not in dir_groups:
                dir_groups[dir_path] = []
            dir_groups[dir_path].append(data)
        
        # 分页设置
        page_size = self.settings["preview_page_size"]
        dir_keys = list(dir_groups.keys())
        total_pages = (len(dir_keys) + page_size - 1) // page_size
        page = 0
        
        # 计算最长文件名用于对齐
        max_old_name_len = max(len(data['old_name']) for data in self.preview_data) + 5
        max_old_name_len = min(max_old_name_len, 50)
        
        while page < total_pages:
            print(Fore.YELLOW + f"\n第 {page + 1} 页 (共 {total_pages} 页)")
            print(Fore.CYAN + "-" * 80)
            
            # 显示当前页的目录
            start_idx = page * page_size
            end_idx = min((page + 1) * page_size, len(dir_keys))
            current_dirs = dir_keys[start_idx:end_idx]
            
            for dir_path in current_dirs:
                files = dir_groups[dir_path]
                # 按季和集正序排序
                files = sorted(files, key=lambda d: (d['info'].get('season', 0), d['info'].get('episode', 0)))
                # 简化路径显示
                display_path = os.path.basename(dir_path) if len(dir_path) > 50 else dir_path
                    
                print(Fore.YELLOW + f"\n 目录: {display_path}")
                print(Fore.WHITE + "-" * 80)
                
                # 显示目录内的文件对比
                print(f"{'原文件名':<{max_old_name_len}} → {'新文件名':<50}")
                print(Fore.WHITE + "-" * 80)
                
                for data in files:
                    status = Fore.GREEN + "✓" if data.get('valid', True) else Fore.YELLOW + "⚠"
                    old_name = (data['old_name'][:max_old_name_len-1] + '...') if len(data['old_name']) > max_old_name_len else data['old_name']
                    new_name = (data['new_name'][:47] + '...') if len(data['new_name']) > 50 else data['new_name']
                    
                    print(f"{status} {Fore.RED}{old_name:<{max_old_name_len}} {Fore.RESET}→ {Fore.GREEN}{new_name}")
                    # 显示元数据文件（去重）
                    if data.get('metadata'):
                        shown_metas = set()
                        for meta in data['metadata']:
                            if meta['old'] not in shown_metas:
                                meta_old = (meta['old'][:45] + '...') if len(meta['old']) > 48 else meta['old']
                                meta_new = (meta['new'][:48] + '...') if len(meta['new']) > 50 else meta['new']
                                print(f"   {Fore.MAGENTA}{meta_old:<48} → {meta_new}")
                                shown_metas.add(meta['old'])
                    # 单文件统计信息（全局格式）
                    # meta_count = len(data.get('metadata', []))
                    # valid = data.get('valid', True)
                    # print("统计：")
                    # print(f"  总文件数: 1")
                    # print(f"  视频文件数: 1")
                    # print(f"  视频元数据文件数: {meta_count}")
                    # print(f"  跳过文件数: {1 if not valid else 0}")
                    # print(f"  错误文件数: {1 if not valid and any(err['file'] == data['old_name'] for err in self.error_files) else 0}")
                    # print(f"  成功重命名视频文件数: {1 if valid else 0}")
                    # print(f"  成功重命名视频元数据文件数: {meta_count if valid else 0}")
                
                print(Fore.WHITE + "-" * 80)

                # 目录级统计
                total_files = len(files)
                video_files = total_files
                skipped_files = sum(1 for d in files if not d.get('valid', True))
                error_files = sum(1 for d in files if not d.get('valid', True) and any(err['file'] == d['old_name'] for err in self.error_files))
                renamed_video_files = sum(1 for d in files if d.get('valid', True))
                metadata_files = sum(len(d.get('metadata', [])) for d in files)
                renamed_metadata_files = sum(len(d.get('metadata', [])) for d in files if d.get('valid', True))

                print("统计：")
                print(f"  总文件数: {total_files}")
                print(f"  视频文件数: {video_files}")
                print(f"  视频元数据文件数: {metadata_files}")
                print(f"  跳过文件数: {skipped_files}")
                print(f"  错误文件数: {error_files}")
                print(f"  成功重命名视频文件数: {renamed_video_files}")
                print(f"  成功重命名视频元数据文件数: {renamed_metadata_files}")
                print("-" * 80)
            
            # 分页控制
            if page + 1 < total_pages:
                print(Fore.CYAN + "\n" + "="*80)
                print(Fore.YELLOW + "📄 分页控制")
                print("Enter - 继续下一页")
                print("q - 退出预览")
                print("数字 - 跳转到指定页")
                print("目录名 - 跳转到指定目录")
                print("Ctrl+C - 中断操作")
                
                try:
                    action = input(Fore.YELLOW + "\n请选择操作: ").strip()
                    if action == 'q':
                        break
                    elif action.isdigit():
                        # 数字跳转
                        target_page = int(action) - 1
                        if 0 <= target_page < total_pages:
                            page = target_page
                            continue
                        else:
                            print(Fore.RED + f"页码超出范围: {action}")
                            continue
                    elif action:
                        # 支持目录名或完整路径跳转
                        found = False
                        for idx, dir_path in enumerate(dir_keys):
                            if action in dir_path or os.path.basename(dir_path) == action:
                                page = idx // page_size
                                found = True
                                break
                        if not found:
                            print(Fore.RED + f"未找到目录: {action}")
                            continue
                        else:
                            continue  # 跳转后自动刷新该页
                except KeyboardInterrupt:
                    print(Fore.YELLOW + "\n\n⚠️  预览被用户中断")
                    break
            page += 1
        
        print(Fore.CYAN + "="*80 + "\n")

        # 全局统计信息（所有分页和所有文件输出的最后）
        total_files = len(self.preview_data)
        video_files = total_files
        skipped_files = sum(1 for d in self.preview_data if not d.get('valid', True))
        error_files = len(self.error_files)
        renamed_video_files = sum(1 for d in self.preview_data if d.get('valid', True))
        metadata_files = sum(len(d.get('metadata', [])) for d in self.preview_data)
        renamed_metadata_files = sum(len(d.get('metadata', [])) for d in self.preview_data if d.get('valid', True))

        print("统计信息：")
        print(f"  总文件数: {total_files}")
        print(f"  视频文件数: {video_files}")
        print(f"  视频元数据文件数: {metadata_files}")
        print(f"  跳过文件数: {skipped_files}")
        print(f"  错误文件数: {error_files}")
        print(f"  成功重命名视频文件数: {renamed_video_files}")
        print(f"  成功重命名视频元数据文件数: {renamed_metadata_files}")

    def show_detailed_preview(self, old_name: str, new_name: str, info: dict):
        """显示详细的重命名预览"""
        # 简化路径显示
        dir_path = info['dir_path']
        display_path = os.path.basename(dir_path) if len(dir_path) > 50 else dir_path
        
        print(Fore.CYAN + "\n" + "="*80)
        print(Fore.BLUE + " 文件重命名详细预览")
        print(Fore.CYAN + "="*80)
        
        # 显示解析出的元数据
        print(Fore.YELLOW + "\n 解析出的元数据:")
        media_type = "电影" if info.get('is_movie') else "电视剧"
        print(f"  文件类型: {Fore.CYAN}{media_type}")
        print(f"  标题: {Fore.CYAN}{info['title']}")
        
        if 'year' in info:
            print(f"  年份: {Fore.CYAN}{info['year']}")
        
        if 'season' in info and 'episode' in info:
            if info['season'] == 0:
                print(f"  特辑集数: {Fore.CYAN}E{info['episode']:02d}")
            else:
                print(f"  季数: {Fore.CYAN}S{info['season']:02d}")
                print(f"  集数: {Fore.CYAN}E{info['episode']:02d}")
            
        print(f"  扩展名: {Fore.CYAN}{info['ext']}")
        print(f"  所在目录: {Fore.CYAN}{display_path}")
        
        # 文件名对比
        print(Fore.YELLOW + "\n 重命名对比:")
        print(f"{Fore.RED}原文件名: {old_name}")
        print(f"{Fore.GREEN}新文件名: {new_name}")
        
        # 差异高亮显示
        print(Fore.YELLOW + "\n 差异高亮:")
        max_len = max(len(old_name), len(new_name))
        for i in range(max_len):
            old_char = old_name[i] if i < len(old_name) else ' '
            new_char = new_name[i] if i < len(new_name) else ' '
            
            if old_char == new_char:
                print(Fore.WHITE + old_char, end='')
            else:
                print(Fore.RED + old_char + Fore.RESET + " → " + Fore.GREEN + new_char, end='')
        print()
        
        # 显示元数据文件影响（I/O优化版）
        print(Fore.YELLOW + "\n 关联的元数据文件:")
        file_base_old = os.path.splitext(old_name)[0]  # 不带扩展名的文件名
        file_base_new = os.path.splitext(new_name)[0]  # 不带扩展名的文件名
        full_old_path = os.path.join(info['dir_path'], old_name)
        full_new_path = os.path.join(info['dir_path'], new_name)
        
        found_metadata = False
        metadata_list = []
        seen_metas = set()  # 用于跟踪已处理的元数据文件
        
        # 使用缓存的元数据文件列表（I/O优化）
        dir_metadata_files = self.cache.get('metadata_files', {}).get(info['dir_path'], [])
        dir_files_set = self.dir_files_cache.get(info['dir_path'], set())
        
        # 检查所有可能的元数据文件类型
        for ext in self.settings["metadata_extensions"]:
            # 类型1: 完整文件名 + 扩展名
            meta_file1 = full_old_path + ext
            if meta_file1 in self.file_exists_cache and meta_file1 not in seen_metas:
                seen_metas.add(meta_file1)
                new_meta = full_new_path + ext
                print(f"  {Fore.RED}{os.path.basename(meta_file1)} → {Fore.GREEN}{os.path.basename(new_meta)}")
                found_metadata = True
                metadata_list.append({
                    'old': os.path.basename(meta_file1),
                    'new': os.path.basename(new_meta)
                })
                
            # 类型2: 基础名 + 扩展名
            meta_file2 = os.path.splitext(full_old_path)[0] + ext
            if meta_file2 in self.file_exists_cache and meta_file2 not in seen_metas:
                seen_metas.add(meta_file2)
                new_meta = os.path.splitext(full_new_path)[0] + ext
                print(f"  {Fore.RED}{os.path.basename(meta_file2)} → {Fore.GREEN}{os.path.basename(new_meta)}")
                found_metadata = True
                metadata_list.append({
                    'old': os.path.basename(meta_file2),
                    'new': os.path.basename(new_meta)
                })
                
            # 处理大小写变体
            for case in [str.lower, str.upper]:
                case_ext = case(ext)
                
                # 类型1大小写变体
                meta_file3 = full_old_path + case_ext
                if meta_file3 in self.file_exists_cache and meta_file3 not in seen_metas:
                    seen_metas.add(meta_file3)
                    new_meta = full_new_path + case_ext
                    print(f"  {Fore.RED}{os.path.basename(meta_file3)} → {Fore.GREEN}{os.path.basename(new_meta)}")
                    found_metadata = True
                    metadata_list.append({
                        'old': os.path.basename(meta_file3),
                        'new': os.path.basename(new_meta)
                    })
                
                # 类型2大小写变体
                meta_file4 = os.path.splitext(full_old_path)[0] + case_ext
                if meta_file4 in self.file_exists_cache and meta_file4 not in seen_metas:
                    seen_metas.add(meta_file4)
                    new_meta = os.path.splitext(full_new_path)[0] + case_ext
                    print(f"  {Fore.RED}{os.path.basename(meta_file4)} → {Fore.GREEN}{os.path.basename(new_meta)}")
                    found_metadata = True
                    metadata_list.append({
                        'old': os.path.basename(meta_file4),
                        'new': os.path.basename(new_meta)
                    })
        
        # 额外处理：文件名匹配的文件（使用缓存）
        for file in dir_files_set:
            file_path = os.path.join(info['dir_path'], file)
            file_base = os.path.splitext(file)[0]
            
            # 检查是否可能是元数据文件（文件名相同但扩展名不同）
            if file_base == file_base_old and file_path != full_old_path:
                # 获取文件扩展名
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                
                # 检查是否是元数据扩展
                if any(ext_lower == meta_ext.lower() for meta_ext in self.settings["metadata_extensions"]):
                    # 构建新文件名
                    new_meta = file.replace(file_base_old, file_base_new)
                    new_meta_path = os.path.join(info['dir_path'], new_meta)
                    # 添加到元数据列表
                    metadata_list.append({
                        'old': file,
                        'new': new_meta
                    })
        
        if not found_metadata:
            print("  未找到关联的元数据文件")
            
            # 显示目录中存在的元数据文件
            print(Fore.YELLOW + "  目录中存在的元数据文件:")
            metadata_files = []
            for file in dir_files_set:
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                if any(ext_lower == meta_ext.lower() for meta_ext in self.settings["metadata_extensions"]):
                    metadata_files.append(file)
            
            if metadata_files:
                for file in metadata_files:
                    print(f"    - {file}")
            else:
                print("    无")
        
        # 冲突检测（I/O优化版）
        new_path = os.path.join(info['dir_path'], new_name)
        if new_path in self.file_exists_cache:
            print(Fore.RED + "\n⚠️ 警告: 目标文件已存在!")
            try:
                # 使用缓存的文件大小信息（I/O优化）
                existing_size = self.cache['files'].get(new_path, {}).get('size', 0)
                current_size = self.cache['files'].get(os.path.join(info['dir_path'], old_name), {}).get('size', 0)
                
                # 如果缓存中没有大小信息，则获取
                if existing_size == 0:
                    existing_size = os.path.getsize(new_path)
                if current_size == 0:
                    current_size = os.path.getsize(os.path.join(info['dir_path'], old_name))
                
                print(f"  现有文件大小: {existing_size} 字节")
                print(f"  当前文件大小: {current_size} 字节")
                
                if existing_size == current_size:
                    if self.settings.get("enable_hash_check", False):
                        # 计算文件哈希以进一步验证
                        existing_hash = self._calculate_file_hash(new_path)
                        current_hash = self._calculate_file_hash(os.path.join(info['dir_path'], old_name))
                        
                        if existing_hash == current_hash:
                            print(Fore.YELLOW + "  文件大小和哈希相同，可能是重复文件")
                        else:
                            print(Fore.YELLOW + "  文件大小相同但哈希不同，可能是不同内容")
                            if hasattr(self, 'error_files'):
                                self.error_files.append({
                                    'file': old_name,
                                    'reason': '文件冲突(大小相同但内容不同)',
                                    'dir': info['dir_path'],
                                    'file_path': os.path.join(info['dir_path'], old_name),
                                    'new_name': new_name
                                })
                    else:
                        print(Fore.YELLOW + "  文件大小相同，可能是重复文件")
                else:
                    print(Fore.YELLOW + "  文件大小不同，可能发生冲突")
            except OSError as e:
                print(Fore.RED + f"  无法获取文件信息: {e}")
        
        print(Fore.CYAN + "="*80 + "\n")  # 修复8: 修正颜色代码从 Fore.CAN 到 Fore.CYAN
        
        # 保存预览数据用于汇总（I/O优化版）
        self.preview_data.append({
            'old_name': old_name,
            'new_name': new_name,
            'info': info,
            'metadata': metadata_list,
            'valid': new_path not in self.file_exists_cache  # 标记是否有效
        })

    def _calculate_file_hash(self, file_path: str, algorithm: str = "md5", block_size: int = 65536) -> str:
        """计算文件哈希值（使用缓存避免重复计算）-- 优化2：使用更快的MD5算法"""
        # 检查文件是否在哈希缓存中
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
        
        # 优化2：默认使用更快的MD5算法
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    hasher.update(data)
            # 保存到缓存
            file_hash = hasher.hexdigest()
            self.hash_cache[file_path] = file_hash
            return file_hash
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def _detect_folder_type(self, root: str) -> Optional[str]:
        """检测文件夹类型：路径中包含指定关键词则返回对应的类型"""
        root_lower = root.lower()
        
        # 强制规则优先级最高
        if self.settings["force_tv_rules"]:
            return "tv"
        elif self.settings["force_movie_rules"]:
            return "movie"
        
        # 检查电视剧关键词
        for keyword in self.settings["tv_folder_keywords"]:
            if keyword.lower() in root_lower:
                return "tv"
        
        # 检查电影关键词
        for keyword in self.settings["movie_folder_keywords"]:
            if keyword.lower() in root_lower:
                return "movie"
                
        return None  # 未检测到关键词

    def process_file(self, root: str, file: str, file_path: str, preview: bool, 
                    video_exts: List[str], meta_exts: List[str],
                    skip_existing: bool) -> Union[str, bool]:
        """处理单个文件（优化版本）"""
        try:
            name, ext = os.path.splitext(file)
            ext_lower = ext.lower()
            
            # 检查文件扩展名
            if ext_lower not in video_exts:
                return "skipped"
            
            # 检查文件是否在缓存中（可选检查，不影响处理）
            cache_files = self.cache.get('files', {})
            if file_path not in cache_files:
                # 如果文件不在缓存中，记录但不跳过
                self.logger.warning(f"文件不在缓存中: {file_path}")
            
            # 第一步：检测文件夹类型
            folder_type = self._detect_folder_type(root)
            
            # 检查是否为特辑（新版：根据设置项动态判断）
            is_special = False
            if self.settings.get('enable_special_check', True):
                special_keywords = self.settings.get('special_keywords', ['特辑','特别篇','Special'])
                special_pattern = re.compile(r"(" + "|".join(map(re.escape, special_keywords)) + r")", re.IGNORECASE)
                if special_pattern.search(file):
                    is_special = True
                    if self.settings.get('force_special_season', True):
                        season = 0
            
            # === 使用优化的模式识别 ===
            if folder_type == "tv":
                # 使用优化的季数集数提取
                season, episode, reason = self._extract_season_episode_optimized(file)
                if episode is None:
                    self.logger.error(f"未能提取到集数，跳过: {file} ({reason})")
                    print(Fore.RED + f"  [错误] 未能提取到集数，跳过: {file} ({reason})")
                    if hasattr(self, 'error_files'):
                        self.error_files.append({
                            'file': file,
                            'reason': reason or '未能提取到集数',
                            'dir': root,
                            'file_path': file_path,
                            'new_name': None
                        })
                    return "error"
                if season is None:
                    season = 1
                
                # 使用优化的标题年份提取
                title, year = self._extract_title_year_optimized(os.path.basename(root))
                
                # 检查是否为特辑
                if season is None:
                    season = 0
                if is_special:
                    season = 0
                    
                # 生成新文件名
                if season == 0:
                    new_name = self.settings["special_template"].format(
                        title=title,
                        episode=episode,
                        ext=ext
                    )
                else:
                    new_name = self.settings["tv_template"].format(
                        title=title,
                        season=season,
                        episode=episode,
                        ext=ext
                    )
                    
                file_type = "电视剧"
                info = {
                    'dir_path': root,
                    'title': title,
                    'season': season,
                    'episode': episode,
                    'ext': ext,
                    'is_movie': False
                }
                
            elif folder_type == "movie":
                # 路径中有"电影"关键词，强制使用电影规则
                title, year = self._extract_title_year_optimized(file)
                
                # 生成新文件名
                new_name = self.settings["movie_template"].format(
                    title=title,
                    year=year,
                    ext=ext
                )
                file_type = "电影"
                info = {
                    'dir_path': root,
                    'title': title,
                    'year': year,
                    'ext': ext,
                    'is_movie': True
                }
                
            else:
                # 未检测到关键词，使用智能识别逻辑
                season, episode, reason = self._extract_season_episode_optimized(file)
                
                if episode is not None:
                    # 如果提取到集数，按电视剧处理
                    title, year = self._extract_title_year_optimized(os.path.basename(root))
                    
                    # 检查是否为特辑
                    if season is None:
                        season = 1
                    if is_special:
                        season = 0
                        
                    # 生成新文件名
                    if season == 0:
                        new_name = self.settings["special_template"].format(
                            title=title,
                            episode=episode,
                            ext=ext
                        )
                    else:
                        new_name = self.settings["tv_template"].format(
                            title=title,
                            season=season,
                            episode=episode,
                            ext=ext
                        )
                        
                    file_type = "电视剧"
                    info = {
                        'dir_path': root,
                        'title': title,
                        'season': season,
                        'episode': episode,
                        'ext': ext,
                        'is_movie': False
                    }
                elif season is not None and episode is None:
                    self.logger.error(f"未能提取到集数，跳过: {file} ({reason})")
                    print(Fore.RED + f"  [错误] 未能提取到集数，跳过: {file} ({reason})")
                    if hasattr(self, 'error_files'):
                        self.error_files.append({
                            'file': file,
                            'reason': reason or '未能提取到集数',
                            'dir': root,
                            'file_path': file_path,
                            'new_name': None
                        })
                    return "error"
                else:
                    # 未提取到集数，按电影处理
                    title, year = self._extract_title_year_optimized(file)
                    
                    # 生成新文件名
                    new_name = self.settings["movie_template"].format(
                        title=title,
                        year=year,
                        ext=ext
                    )
                    file_type = "电影"
                    info = {
                        'dir_path': root,
                        'title': title,
                        'year': year,
                        'ext': ext,
                        'is_movie': True
                    }
            
            # === 使用优化的标题清理 ===
            clean_title = self._clean_title_optimized(info['title'])
            info['title'] = clean_title
            
            # 更新新文件名中的标题
            if file_type == "电视剧":
                if season == 0:
                    new_name = self.settings["special_template"].format(
                        title=clean_title,
                        episode=info['episode'],
                        ext=ext
                    )
                else:
                    new_name = self.settings["tv_template"].format(
                        title=clean_title,
                        season=info['season'],
                        episode=info['episode'],
                        ext=ext
                    )
            else:
                new_name = self.settings["movie_template"].format(
                    title=clean_title,
                    year=info['year'],
                    ext=ext
                )
            
            # 优化4：使用更可靠的路径拼接方式
            new_path = os.path.join(root, new_name)
            
            # 检查是否已正确命名
            if file == new_name:
                self.logger.debug(f"文件名已正确: {file}")
                return "skipped"
            
            # 检查目标文件是否存在（I/O优化版）
            if skip_existing and new_path in self.file_exists_cache:
                # 检查文件是否相同
                try:
                    # 使用缓存的文件大小信息（I/O优化）
                    existing_size = self.cache['files'].get(new_path, {}).get('size', 0)
                    current_size = self.cache['files'].get(file_path, {}).get('size', 0)
                    
                    # 如果缓存中没有大小信息，则获取
                    if existing_size == 0:
                        existing_size = os.path.getsize(new_path)
                    if current_size == 0:
                        current_size = os.path.getsize(file_path)
                    
                    if existing_size == current_size:
                        if self.settings.get("enable_hash_check", False):
                            # 计算文件哈希以进一步验证
                            existing_hash = self._calculate_file_hash(new_path)
                            current_hash = self._calculate_file_hash(file_path)
                            
                            if existing_hash == current_hash:
                                self.logger.warning(f"目标文件已存在且相同: {new_path}")
                                print(Fore.YELLOW + f"  [跳过] 目标已存在且相同: {file} → {new_name}")
                            else:
                                self.logger.error(f"文件冲突: {file} 和 {os.path.basename(new_path)} (大小相同但哈希不同)")
                                print(Fore.RED + f"  [错误] 文件冲突: {file} → {new_name} (大小相同但内容不同)")
                                if hasattr(self, 'error_files'):
                                    self.error_files.append({
                                        'file': file,
                                        'reason': '文件冲突(大小相同但内容不同)',
                                        'dir': root,
                                        'file_path': file_path,
                                        'new_name': new_name
                                    })
                        else:
                            self.logger.warning(f"目标文件已存在且大小相同: {new_path}")
                            print(Fore.YELLOW + f"  [跳过] 目标已存在且大小相同: {file} → {new_name}")
                    else:
                        self.logger.error(f"文件冲突: {file} 和 {os.path.basename(new_path)}")
                        print(Fore.RED + f"  [错误] 文件冲突: {file} → {new_name}")
                        if hasattr(self, 'error_files'):
                            self.error_files.append({
                                'file': file,
                                'reason': '文件冲突(大小不同)',
                                'dir': root,
                                'file_path': file_path,
                                'new_name': new_name
                            })
                except OSError as e:
                    self.logger.warning(f"目标文件已存在但无法比较: {new_path}")
                    print(Fore.YELLOW + f"  [跳过] 目标已存在: {file} → {new_name}")
                return "skipped"
            
            if preview:
                # 增强的预览输出
                self.show_detailed_preview(
                    old_name=file,
                    new_name=new_name,
                    info=info
                )
                return "processed"
            else:
                try:
                    # 使用安全的重命名操作
                    if self.safe_rename_operation(file_path, new_path, "normal"):
                        self._rename_metadata(file_path, new_path, meta_exts)
                        self._add_history(file_path, new_path)
                        
                        # 更新缓存（I/O优化版）
                        if file_path in self.cache['files']:
                            # 更新缓存中的文件路径
                            file_info = self.cache['files'].pop(file_path)
                            file_info['name'] = new_name
                            self.cache['files'][new_path] = file_info
                            
                            # 更新目录文件列表
                            if root in self.cache['dir_files']:
                                if file_path in self.cache['dir_files'][root]:
                                    self.cache['dir_files'][root].remove(file_path)
                                self.cache['dir_files'][root].append(new_path)
                            
                            # 更新I/O优化缓存
                            self._update_file_cache(file_path, new_path)
                            
                            # 更新目录文件列表缓存
                            if root in self.dir_files_cache:
                                old_file_name = os.path.basename(file_path)
                                new_file_name = os.path.basename(new_path)
                                self.dir_files_cache[root].discard(old_file_name)
                                self.dir_files_cache[root].add(new_file_name)
                        
                        print(Fore.GREEN + f"  [成功] {file} → {new_name} ({file_type})")
                        self.logger.info(f"重命名: {file} → {new_name} ({file_type})")
                        return "processed"
                    else:
                        self.logger.error(f"安全重命名失败 {file}")
                        print(Fore.RED + f"  [失败] {file}: 安全重命名失败")
                        return "error"
                except Exception as e:
                    self.logger.error(f"重命名失败 {file}: {e}")
                    print(Fore.RED + f"  [失败] {file}: {str(e)}")
                    return "error"
                    
        except Exception as e:
            # 使用统一的错误处理
            self.error_handler.handle_error(e, "处理文件", file_path, "process_file")
            return "error"

    def _extract_title_year(self, text: str) -> Tuple[str, str]:
        """从文本中提取标题和年份--修复版（年份不带括号）"""
        # 优先匹配括号或方括号内的年份
        year_match = re.search(r'[\(\[]\s*(\d{4})\s*[\)\]]', text)
        if year_match:
            year = year_match.group(1)
        else:
            # 其次匹配任意位置的4位数字
            year_match = re.search(r'(\d{4})', text)
            year = year_match.group(1) if year_match else "0000"
        # 去除所有年份片段（包括括号）
        clean_text = re.sub(r'[\(\[]\s*\d{4}\s*[\)\]]', '', text)
        clean_text = re.sub(r'(\d{4})', '', clean_text)
        # 移除 SxxEyy/Sxx Eyy 片段
        clean_text = re.sub(r'[Ss]\d{2}[ ._]?E\d{2}', '', clean_text)
        # 清理标题
        title = re.sub(r'[\\/*?:"<>|$$$$\.\!_]', ' ', clean_text).strip()
        title = re.sub(r'\s+', ' ', title)  # 合并多余空格
        # 去除所有 []
        title = re.sub(r'\[\s*\]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title, year

    def _extract_season_episode(self, filename: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """从文件名中提取季数和集数信息（增强版）"""
        season = None
        episode = None
        reason = None
        try:
            # 首先尝试提取集数和季数
            for pattern in self.episode_patterns:
                match = pattern.search(filename)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # S01E02、1x02、S1EP2、1-02等
                        season = int(groups[0]) if groups[0] else None
                        episode = int(groups[1])
                        break
                    elif len(groups) == 1:
                        # EP02、E02、[01]、【01】、第2集等
                        episode = int(groups[0])
                        season = None  # 先不设，后续推断
                        break
            # 智能推断季数
            if episode is not None and (season is None or season == 0):
                # 从文件夹名推断季数
                folder_name = os.path.basename(os.path.dirname(filename)) if os.path.sep in filename else ""
                # 匹配 Season 2/S2/第2季
                m = re.search(r"S(eason)?[ ._]*(\\d{1,2})", folder_name, re.IGNORECASE)
                if not m:
                    m = re.search(r"第\\s*(\\d{1,2})\\s*季", folder_name)
                if m:
                    season = int(m.group(2) if m.lastindex == 2 else m.group(1))
                else:
                    season = 1  # 默认第一季
            # 如果成功提取到集数，检查是否为整季打包
            if episode is not None:
                # 只有在文件名中明确包含整季关键词时才判定为整季打包
                # 注意：EP格式的文件通常不是整季打包，所以需要更严格的检测
                if re.search(r'\b(complete|full|season|整季|全集|全季|完整版)\b', filename, re.IGNORECASE):
                    # 额外检查：如果文件名包含EP格式，通常不是整季打包
                    if re.search(r'\bEP\d+\b', filename, re.IGNORECASE):
                        # EP格式的文件，即使包含整季关键词，也按单集处理
                        return season, episode, reason
                    reason = "疑似整季打包"
                    return None, None, reason
                # 否则返回成功提取的集数
                return season, episode, reason
            # 如果没有提取到集数，再检查其他情况
            if re.search(r'\d+', filename):
                reason = "文件名有数字但未能识别为集数"
            else:
                reason = "文件名无集数信息"
            return season, episode, reason
        except (ValueError, TypeError) as e:
            reason = f"数字转换错误: {e}"
            return None, None, reason
        except Exception as e:
            reason = f"提取集数时发生异常: {e}"
            return None, None, reason

    def _rename_metadata_file(self, old_path: str, new_path: str):
        """重命名单个元数据文件（辅助函数）"""
        if os.path.exists(old_path):
            try:
                # 对于Windows系统，使用shutil.move处理跨设备重命名
                if os.name == 'nt':
                    shutil.move(old_path, new_path)
                else:
                    os.rename(old_path, new_path)
                self.logger.debug(f"重命名元数据: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
                return True
            except Exception as e:
                self.logger.warning(f"元数据重命名失败 {old_path}: {e}")
        return False

    def _rename_metadata(self, old_path: str, new_path: str, exts: List[str]):
        """重命名关联的元数据文件（I/O优化版）"""
        file_base_old = os.path.splitext(old_path)[0]  # 不带扩展名的文件名
        file_base_new = os.path.splitext(new_path)[0]  # 不带扩展名的文件名
        dir_path = os.path.dirname(old_path)
        
        # 使用缓存的目录文件列表（I/O优化）
        dir_files_set = self.dir_files_cache.get(dir_path, set())
        
        # 处理所有可能的元数据文件类型
        extensions_to_check = []
        for ext in exts:
            extensions_to_check.append(ext)
            extensions_to_check.append(ext.lower())
            extensions_to_check.append(ext.upper())
        
        # 处理已知扩展名格式
        processed_paths = set()
        for ext in extensions_to_check:
            # 类型1: 完整文件名 + 扩展名
            meta_old = old_path + ext
            if meta_old in self.file_exists_cache and meta_old not in processed_paths:
                self._rename_metadata_file(meta_old, new_path + ext)
                processed_paths.add(meta_old)
                # 更新缓存
                self._update_file_cache(meta_old, new_path + ext)
            
            # 类型2: 基础名 + 扩展名
            meta_old_base = file_base_old + ext
            if meta_old_base in self.file_exists_cache and meta_old_base not in processed_paths:
                self._rename_metadata_file(meta_old_base, file_base_new + ext)
                processed_paths.add(meta_old_base)
                # 更新缓存
                self._update_file_cache(meta_old_base, file_base_new + ext)
        
        # 处理目录中文件名匹配的文件
        file_base_old_name = os.path.basename(file_base_old)
        file_base_new_name = os.path.basename(file_base_new)
        
        for file in dir_files_set:
            file_full_path = os.path.join(dir_path, file)
            file_base = os.path.splitext(file)[0]
            
            # 跳过已经处理过的文件
            if file_full_path in processed_paths:
                continue
                
            # 检查是否可能是元数据文件（文件名相同但扩展名不同）
            if file_base == file_base_old_name and file_full_path != old_path:
                # 获取文件扩展名
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                
                # 检查是否是元数据扩展
                if any(ext_lower == meta_ext.lower() for meta_ext in self.settings["metadata_extensions"]):
                    # 构建新文件名
                    new_meta = file.replace(file_base_old_name, file_base_new_name)
                    new_meta_path = os.path.join(dir_path, new_meta)
                    self._rename_metadata_file(file_full_path, new_meta_path)
                    # 更新缓存
                    self._update_file_cache(file_full_path, new_meta_path)
    
    def _update_file_cache(self, old_path: str, new_path: str):
        """更新文件缓存（I/O优化）"""
        # 更新文件存在性缓存
        if old_path in self.file_exists_cache:
            self.file_exists_cache[new_path] = True
            del self.file_exists_cache[old_path]
        
        # 更新元数据缓存
        if old_path in self.metadata_cache:
            self.metadata_cache[new_path] = self.metadata_cache[old_path].copy()
            self.metadata_cache[new_path]['name'] = os.path.basename(new_path)
            del self.metadata_cache[old_path]

    def _add_history(self, old_path: str, new_path: str):
        """添加历史记录（I/O优化版）"""
        if not self.settings.get("enable_history", True):
            return
            
        record = {
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'old': old_path,
            'new': new_path
        }
        
        # 添加到缓冲区（I/O优化）
        self.history_buffer.append(record)
        
        # 当缓冲区满时批量写入
        if len(self.history_buffer) >= self.history_buffer_size:
            self._flush_history_buffer()
    
    def _flush_history_buffer(self):
        """刷新历史记录缓冲区"""
        if not self.history_buffer:
            return
            
        try:
            history = self._load_history()
            
            for record in self.history_buffer:
                dir_key = os.path.dirname(record['old'])
                history.setdefault(dir_key, []).append(record)
            
            self._save_history(history)
            self.history_buffer.clear()
            self.logger.debug(f"历史记录缓冲区已刷新，写入 {len(self.history_buffer)} 条记录")
        except Exception as e:
            self.logger.error(f"刷新历史记录缓冲区失败: {e}")
    
    def _finalize_history(self):
        """最终化历史记录（程序结束时调用）"""
        self._flush_history_buffer()

    def _load_history(self) -> dict:
        """加载历史记录"""
        if not os.path.exists(self.history_file):
            return {}
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载历史记录失败: {e}")
            return {}

    def _save_history(self, history: dict):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")

    def undo_last(self, directory: Optional[str] = None) -> bool:
        """撤销最后一次操作"""
        if not directory:
            directory = self.settings["folder_path"]
            
        history = self._load_history()
        if not history.get(directory):
            print(Fore.YELLOW + f"目录 {directory} 没有可撤销的操作")
            return False
            
        # 获取最新记录
        if not history[directory]:
            print(Fore.YELLOW + f"目录 {directory} 没有可撤销的操作")
            return False
            
        record = history[directory][-1]
        
        try:
            # 撤销主文件
            if not os.path.exists(record['new']):
                print(Fore.RED + f"文件不存在: {record['new']}")
                return False
                
            if os.path.exists(record['old']):
                print(Fore.RED + f"目标文件已存在: {record['old']}")
                return False
                
            os.rename(record['new'], record['old'])
            
            # 撤销元数据文件
            old_base = os.path.splitext(record['old'])[0]
            new_base = os.path.splitext(record['new'])[0]
            
            for ext in self.settings["metadata_extensions"]:
                try:
                    meta_old = old_base + ext
                    meta_new = new_base + ext
                    
                    if os.path.exists(meta_new):
                        # 对于Windows系统，使用shutil.move处理跨设备重命名
                        if os.name == 'nt':
                            shutil.move(meta_new, meta_old)
                        else:
                            os.rename(meta_new, meta_old)
                except FileNotFoundError:
                    continue
            
            # 更新历史记录
            history[directory].pop()
            if not history[directory]:
                del history[directory]
            self._save_history(history)
            
            # 更新缓存
            self.cache = {}
            if directory:
                self.build_directory_cache(directory)
            
            print(Fore.GREEN + f"撤销成功: {os.path.basename(record['new'])} → {os.path.basename(record['old'])}")
            return True
        except Exception as e:
            print(Fore.RED + f"撤销失败: {e}")
            return False

    def show_history(self, directory: Optional[str] = None):
        """显示历史记录"""
        if not directory:
            directory = self.settings["folder_path"]
            
        history = self._load_history()
        if not history.get(directory):
            print(Fore.YELLOW + f"目录 {directory} 没有历史记录")
            return
            
        print(Fore.CYAN + f"\n{directory} 的历史记录:")
        for idx, record in enumerate(reversed(history[directory]), start=1):
            print(f"[{idx}] 时间: {record['time']}")
            print(f"    原文件: {os.path.basename(record['old'])}")
            print(f"    新文件: {os.path.basename(record['new'])}")
            print("-" * 50)

    def show_settings(self):
        """显示当前设置"""
        print(Fore.CYAN + "\n当前设置:")
        print(f"  电影命名模板: {self.settings['movie_template']}")
        print(f"  电视剧命名模板: {self.settings['tv_template']}")
        print(f"  电视特辑命名模板: {self.settings['special_template']}")
        print(f"  视频扩展名: {', '.join(self.settings['video_extensions'])}")
        print(f"  元数据扩展名: {', '.join(self.settings['metadata_extensions'])}")
        print(f"  预览模式: {'开启' if self.settings['preview_only'] else '关闭'}")
        print(f"  历史记录: {'开启' if self.settings['enable_history'] else '关闭'}")
        print(f"  跳过已存在文件: {'开启' if self.settings['skip_existing'] else '关闭'}")
        print(f"  预览分页大小: {self.settings['preview_page_size']}")
        print(f"  缓存有效期: {self.settings['cache_ttl']} 秒")
        print(f"  文件哈希检查: {'开启' if self.settings['enable_hash_check'] else '关闭'}")
        print(f"  电视剧文件夹关键词: {', '.join(self.settings['tv_folder_keywords'])}")
        print(f"  电影文件夹关键词: {', '.join(self.settings['movie_folder_keywords'])}")
        print(f"  强制电视剧规则: {'开启' if self.settings['force_tv_rules'] else '关闭'}")
        print(f"  强制电影规则: {'开启' if self.settings['force_movie_rules'] else '关闭'}")
        print(f"  启用特辑检查: {'开启' if self.settings['enable_special_check'] else '关闭'}")
        print(f"  特辑关键词: {', '.join(self.settings['special_keywords'])}")
        print(f"  强制特辑季: {'开启' if self.settings['force_special_season'] else '关闭'}")
        print(f"  增量缓存更新: {'开启' if self.settings.get('enable_incremental_cache', True) else '关闭'}")
        print(f"  自动清理过期缓存: {'开启' if self.settings.get('cache_auto_cleanup', True) else '关闭'}")
        print(f"  缓存最大大小: {self.settings.get('cache_max_size_mb', 100)} MB")
        print(f"  历史记录缓冲区大小: {self.history_buffer_size}")
        print(f"  I/O优化: 启用")

    def _validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """验证文件路径安全性"""
        try:
            # 检查路径是否在禁止列表中
            for forbidden_path in self.security_settings['forbidden_paths']:
                if forbidden_path in file_path:
                    self.security_logger.log_suspicious_activity(
                        "访问禁止路径", f"尝试访问: {file_path}"
                    )
                    return False, f"路径被禁止访问: {forbidden_path}"
            
            # 检查路径规范化
            normalized_path = os.path.normpath(file_path)
            if normalized_path != file_path:
                self.security_logger.log_suspicious_activity(
                    "路径规范化", f"原始路径: {file_path}, 规范化后: {normalized_path}"
                )
                return False, "路径包含可疑字符"
            
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in self.security_settings['allowed_extensions']:
                self.security_logger.log_suspicious_activity(
                    "不允许的文件类型", f"文件: {file_path}, 扩展名: {ext}"
                )
                return False, f"不允许的文件类型: {ext}"
            
            return True, "路径验证通过"
            
        except Exception as e:
            self.error_handler.handle_error(e, "路径验证", file_path, "validate_path")
            return False, f"路径验证异常: {str(e)}"

    def _validate_file_size(self, file_path: str) -> Tuple[bool, str]:
        """验证文件大小安全性"""
        try:
            if not self.security_settings['enable_file_size_check']:
                return True, "文件大小检查已禁用"
            
            file_size = os.path.getsize(file_path)
            max_size_bytes = self.security_settings['max_file_size_mb'] * 1024 * 1024
            
            if file_size > max_size_bytes:
                self.security_logger.log_suspicious_activity(
                    "文件过大", f"文件: {file_path}, 大小: {file_size / (1024*1024):.1f}MB"
                )
                return False, f"文件过大: {file_size / (1024*1024):.1f}MB"
            
            return True, "文件大小验证通过"
            
        except Exception as e:
            self.error_handler.handle_error(e, "文件大小验证", file_path, "validate_size")
            return False, f"文件大小验证异常: {str(e)}"

    def _detect_suspicious_patterns(self, file_path: str) -> Tuple[bool, str]:
        """检测可疑模式"""
        try:
            if not self.security_settings['enable_suspicious_detection']:
                return True, "可疑模式检测已禁用"
            
            filename = os.path.basename(file_path)
            
            # 检测可疑字符模式
            suspicious_patterns = [
                r'\.\.',  # 路径遍历
                r'[<>:"|?*]',  # 非法字符
                r'\.(exe|bat|cmd|com|pif|scr|vbs|js)$',  # 可执行文件
                r'\.(php|asp|jsp|aspx)$',  # Web脚本
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    self.security_logger.log_suspicious_activity(
                        "可疑文件名模式", f"文件: {filename}, 模式: {pattern}"
                    )
                    return False, f"检测到可疑模式: {pattern}"
            
            return True, "可疑模式检测通过"
            
        except Exception as e:
            self.error_handler.handle_error(e, "可疑模式检测", file_path, "detect_patterns")
            return False, f"可疑模式检测异常: {str(e)}"

    def _safe_file_operation(self, operation: str, file_path: str, func, *args, **kwargs):
        """安全文件操作包装器"""
        try:
            # 记录文件访问
            self.security_logger.log_file_access(file_path, operation)
            
            # 路径验证
            if self.security_settings['enable_path_validation']:
                is_valid, message = self._validate_file_path(file_path)
                if not is_valid:
                    raise SecurityError(f"路径验证失败: {message}")
            
            # 文件大小验证
            if os.path.exists(file_path):
                is_valid, message = self._validate_file_size(file_path)
                if not is_valid:
                    raise SecurityError(f"文件大小验证失败: {message}")
            
            # 可疑模式检测
            is_valid, message = self._detect_suspicious_patterns(file_path)
            if not is_valid:
                raise SecurityError(f"可疑模式检测失败: {message}")
            
            # 执行操作
            result = func(*args, **kwargs)
            
            # 更新操作统计
            self.operation_stats['files_processed'] += 1
            self.operation_stats['last_operation_time'] = time.time()
            
            return result
            
        except PermissionError as e:
            self.security_logger.log_permission_denied(file_path, operation)
            self.error_handler.handle_error(e, f"权限错误 - {operation}", file_path, operation, "WARNING")
            raise
        except SecurityError as e:
            self.error_handler.handle_error(e, f"安全错误 - {operation}", file_path, operation, "ERROR")
            raise
        except Exception as e:
            self.error_handler.handle_error(e, f"操作错误 - {operation}", file_path, operation, "ERROR")
            raise

    def _check_operation_limits(self, operation: str, file_count: int = 1):
        """检查操作限制"""
        try:
            # 检查文件数量限制
            if file_count > self.security_settings['max_files_per_operation']:
                raise SecurityError(
                    f"文件数量超限: {file_count} > {self.security_settings['max_files_per_operation']}"
                )
            
            # 检查操作频率
            current_time = time.time()
            time_since_last = current_time - self.operation_stats['last_operation_time']
            if time_since_last < 0.1:  # 100ms内不允许重复操作
                raise SecurityError(f"操作过于频繁: {time_since_last:.3f}秒")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "操作限制检查", operation=operation)
            raise

    def get_operation_stats(self) -> dict:
        """获取操作统计信息"""
        current_time = time.time()
        duration = current_time - self.operation_stats['start_time']
        
        stats = self.operation_stats.copy()
        stats.update({
            'duration_seconds': duration,
            'files_per_second': stats['files_processed'] / max(duration, 1),
            'success_rate': (stats['files_renamed'] / max(stats['files_processed'], 1)) * 100,
            'error_summary': self.error_handler.get_error_summary()
        })
        
        return stats

    def show_operation_stats(self):
        """显示操作统计信息"""
        stats = self.get_operation_stats()
        
        print(Fore.BLUE + "\n" + "="*60)
        print(Fore.CYAN + "操作统计信息")
        print(Fore.BLUE + "="*60)
        print(Fore.GREEN + f"处理文件数: {stats['files_processed']}")
        print(Fore.GREEN + f"成功重命名: {stats['files_renamed']}")
        print(Fore.YELLOW + f"跳过文件数: {stats['files_skipped']}")
        print(Fore.RED + f"失败文件数: {stats['files_failed']}")
        print(Fore.CYAN + f"运行时间: {stats['duration_seconds']:.1f}秒")
        print(Fore.CYAN + f"处理速度: {stats['files_per_second']:.2f}文件/秒")
        print(Fore.CYAN + f"成功率: {stats['success_rate']:.1f}%")
        
        # 错误摘要
        error_summary = stats['error_summary']
        if error_summary['total_errors'] > 0:
            print(Fore.RED + f"\n错误统计:")
            print(Fore.RED + f"总错误数: {error_summary['total_errors']}")
            for error_type, count in error_summary['error_types'].items():
                print(Fore.RED + f"  {error_type}: {count}次")
        
        # v1.3新增：显示性能监控信息
        if self.settings.get("performance_monitoring", True):
            perf_summary = self.performance_monitor.get_performance_summary()
            print(Fore.MAGENTA + f"\n性能监控:")
            print(Fore.MAGENTA + f"当前内存使用: {perf_summary['current_memory_mb']:.1f} MB")
            print(Fore.MAGENTA + f"内存趋势: {perf_summary['memory_trend']}")
            print(Fore.MAGENTA + f"平均操作时间: {perf_summary['avg_operation_time']:.3f} 秒")
        
        print("="*60)
    
    def generate_performance_report(self, report_file: Optional[str] = None):
        """生成性能报告"""
        if not self.settings.get("performance_monitoring", True):
            print(Fore.YELLOW + "性能监控已禁用")
            return
        
        # 结束初始化操作
        self.performance_monitor.end_operation("initialization", True)
        
        # 生成报告
        report_content = self.performance_monitor.generate_report(report_file)
        
        if report_file:
            print(Fore.GREEN + f"✅ 性能报告已保存到: {report_file}")
        else:
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "性能报告")
            print(Fore.CYAN + "="*60)
            print(report_content)
    
    def smart_analyze_file(self, filename: str, folder_path: str) -> dict:
        """智能分析文件"""
        # 使用智能识别器分析文件名
        analysis = self.pattern_recognizer.analyze_filename(filename)
        
        # 根据文件夹名称增强识别
        folder_name = os.path.basename(folder_path)
        analysis = self.pattern_recognizer.enhance_confidence(analysis, folder_name)
        
        # 建议重命名格式
        suggested_format = self.pattern_recognizer.suggest_rename_format(analysis)
        if suggested_format:
            analysis['suggested_format'] = suggested_format
        
        return analysis
    
    def export_config(self, export_file: Optional[str] = None):
        """导出当前配置"""
        if not export_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"config_export_{timestamp}.json"
        
        if self.config_manager.export_config(export_file):
            print(Fore.GREEN + f"✅ 配置已导出到: {export_file}")
        else:
            print(Fore.RED + f"❌ 配置导出失败")
    
    def import_config(self, import_file: str):
        """导入配置"""
        if self.config_manager.import_config(import_file):
            print(Fore.GREEN + f"✅ 配置已从 {import_file} 导入")
            # 重新加载配置
            self.settings.update(self.config_manager.settings)
        else:
            print(Fore.RED + f"❌ 配置导入失败")
    
    def show_smart_analysis(self, file_path: str):
        """显示智能分析结果"""
        filename = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)
        
        analysis = self.smart_analyze_file(filename, folder_path)
        
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.BLUE + "智能分析结果")
        print(Fore.CYAN + "="*60)
        print(f"文件名: {filename}")
        print(f"文件夹: {os.path.basename(folder_path)}")
        print(f"识别类型: {analysis['type'] or '未知'}")
        print(f"置信度: {analysis['confidence']:.1%}")
        
        if analysis['pattern_matched']:
            print(f"匹配模式: {analysis['pattern_matched']}")
        
        if analysis['title']:
            print(f"提取标题: {analysis['title']}")
        
        if analysis['season'] is not None:
            print(f"季数: {analysis['season']}")
        
        if analysis['episode'] is not None:
            print(f"集数: {analysis['episode']}")
        
        if analysis['year']:
            print(f"年份: {analysis['year']}")
        
        if analysis.get('suggested_format'):
            print(f"建议格式: {analysis['suggested_format']}")
        
        print("="*60)

    def _calculate_file_hash_safe(self, file_path: str, algorithm: str = "md5", chunk_size: int = 8192) -> str:
        """安全的大文件哈希计算 - 分块处理"""
        try:
            if algorithm.lower() == "md5":
                hash_obj = hashlib.md5()
            elif algorithm.lower() == "sha1":
                hash_obj = hashlib.sha1()
            elif algorithm.lower() == "sha256":
                hash_obj = hashlib.sha256()
            else:
                raise ValueError(f"不支持的哈希算法: {algorithm}")
            
            # 分块读取，避免内存溢出
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    # === 新增的优化方法 ===
    def _extract_season_episode_optimized(self, filename: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """使用优化的模式识别提取季数和集数"""
        # 创建PatternRecognizer实例（如果还没有）
        if not hasattr(self, 'pattern_recognizer'):
            self.pattern_recognizer = PatternRecognizer()
        
        return self.pattern_recognizer.extract_season_episode_optimized(filename)

    def _extract_title_year_optimized(self, text: str) -> Tuple[str, str]:
        """使用优化的模式识别提取标题和年份"""
        if not hasattr(self, 'pattern_recognizer'):
            self.pattern_recognizer = PatternRecognizer()
        
        return self.pattern_recognizer.extract_title_year_optimized(text)

    def _clean_title_optimized(self, title: str) -> str:
        """使用优化的正则表达式清理标题"""
        if not hasattr(self, 'pattern_recognizer'):
            self.pattern_recognizer = PatternRecognizer()
        
        return self.pattern_recognizer._clean_title_optimized(title)

    def _check_memory_usage(self):
        """检查内存使用情况"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent / 100
            if memory_percent > 0.8:  # 80%内存使用率阈值
                self._trigger_memory_cleanup()
                self.logger.warning(f"内存使用率过高 ({memory_percent:.1%})，已触发清理")
        except ImportError:
            # psutil不可用，跳过内存检查
            pass

    def _trigger_memory_cleanup(self):
        """触发内存清理"""
        # 清理缓存
        if len(self._cache_buffer) > 1000:
            self._flush_cache_buffer()
        
        # 清理历史记录
        if len(self.history) > 1000:
            self.history = self.history[-500:]  # 保留最近500条
        
        # 强制垃圾回收
        import gc
        gc.collect()

    def get_settings_for_ui(self) -> dict:
        """获取UI友好的配置格式"""
        return {
            'video_exts': self.video_exts,
            'meta_exts': self.meta_exts,
            'movie_template': self.movie_template,
            'tv_template': self.tv_template,
            'special_template': self.special_template,
            'enable_sandbox': self.enable_sandbox,
            'enable_confirmation': self.enable_confirmation,
            'max_files_per_operation': self.max_files_per_operation,
            'enable_path_validation': self.security_settings.get('enable_path_validation', True),
            'enable_file_size_check': self.security_settings.get('enable_file_size_check', True),
            'max_workers': self.settings.get('performance', {}).get('max_workers', 4),
            'cache_size': self.settings.get('performance', {}).get('cache_size', 1000),
            'batch_size': self.settings.get('performance', {}).get('batch_size', 100),
            'memory_threshold': self.settings.get('performance', {}).get('memory_threshold', 0.8),
            'log_level': self.settings.get('logging', {}).get('level', 'INFO'),
            'max_errors': self.max_errors,
            'enable_performance_logging': self.settings.get('logging', {}).get('enable_performance_logging', True)
        }

    def update_settings_from_ui(self, ui_settings: dict):
        """从UI更新设置"""
        try:
            # 更新文件类型设置
            if 'video_exts' in ui_settings:
                self.video_exts = ui_settings['video_exts']
            if 'meta_exts' in ui_settings:
                self.meta_exts = ui_settings['meta_exts']
            
            # 更新模板设置
            if 'movie_template' in ui_settings:
                self.movie_template = ui_settings['movie_template']
            if 'tv_template' in ui_settings:
                self.tv_template = ui_settings['tv_template']
            if 'special_template' in ui_settings:
                self.special_template = ui_settings['special_template']
            
            # 更新安全设置
            if 'enable_sandbox' in ui_settings:
                self.enable_sandbox = ui_settings['enable_sandbox']
            if 'enable_confirmation' in ui_settings:
                self.enable_confirmation = ui_settings['enable_confirmation']
            if 'max_files_per_operation' in ui_settings:
                self.max_files_per_operation = ui_settings['max_files_per_operation']
            
            # 更新安全设置字典
            if 'enable_path_validation' in ui_settings:
                self.security_settings['enable_path_validation'] = ui_settings['enable_path_validation']
            if 'enable_file_size_check' in ui_settings:
                self.security_settings['enable_file_size_check'] = ui_settings['enable_file_size_check']
            
            # 更新性能设置
            if 'max_workers' in ui_settings:
                if 'performance' not in self.settings:
                    self.settings['performance'] = {}
                self.settings['performance']['max_workers'] = ui_settings['max_workers']
            
            if 'cache_size' in ui_settings:
                if 'performance' not in self.settings:
                    self.settings['performance'] = {}
                self.settings['performance']['cache_size'] = ui_settings['cache_size']
            
            if 'batch_size' in ui_settings:
                if 'performance' not in self.settings:
                    self.settings['performance'] = {}
                self.settings['performance']['batch_size'] = ui_settings['batch_size']
            
            if 'memory_threshold' in ui_settings:
                if 'performance' not in self.settings:
                    self.settings['performance'] = {}
                self.settings['performance']['memory_threshold'] = ui_settings['memory_threshold']
            
            # 更新日志设置
            if 'log_level' in ui_settings:
                if 'logging' not in self.settings:
                    self.settings['logging'] = {}
                self.settings['logging']['level'] = ui_settings['log_level']
            
            if 'max_errors' in ui_settings:
                self.max_errors = ui_settings['max_errors']
            
            if 'enable_performance_logging' in ui_settings:
                if 'logging' not in self.settings:
                    self.settings['logging'] = {}
                self.settings['logging']['enable_performance_logging'] = ui_settings['enable_performance_logging']
            
            self.logger.info("设置已从UI更新")
            
        except Exception as e:
            self.logger.error(f"从UI更新设置失败: {e}")

    def get_error_summary_for_ui(self) -> dict:
        """获取UI友好的错误摘要"""
        return {
            'total_errors': len(self.error_contexts),
            'error_types': dict(self.error_counts),
            'recent_errors': self.error_contexts[-10:] if self.error_contexts else [],
            'can_continue': len(self.error_contexts) < self.max_errors
        }

class SecurityError(Exception):
    """安全相关异常"""
    pass

# ===================== 交互式设置 =====================
def interactive_settings():
    """交互式设置参数（文件夹类型自适应版）"""
    settings = DEFAULT_SETTINGS.copy()
    
    # 创建交互式处理器
    interactive_handler = InteractiveHandler()
    
    print(Fore.BLUE + "\n" + "="*60)
    print(Fore.CYAN + " 影视文件重命名工具设置")
    print(Fore.BLUE + "="*60)
    print(Fore.YELLOW + "💡 提示: 使用 Tab 键补全路径，Ctrl+C 中断操作")
    print(Fore.BLUE + "="*60)
    
    # 设置目录路径
    print(Fore.YELLOW + "\n步骤 1/8: 设置影视库目录")
    while True:
        try:
            path = interactive_handler.safe_input(
                Fore.YELLOW + "请输入影视库目录路径",
                settings['folder_path']
            )
            
            if not path:
                path = settings['folder_path']
            
            if os.path.isdir(path):
                settings['folder_path'] = os.path.abspath(path)
                print(Fore.GREEN + f"✅ 已设置目录: {settings['folder_path']}")
                break
            print(Fore.RED + "❌ 目录不存在，请重新输入")
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
            return settings
    
    # 设置电影命名模板
    print(Fore.YELLOW + "\n步骤 2/8: 设置电影命名模板")
    print(Fore.CYAN + "可用变量: {title}, {year}, {ext}")
    try:
        template = interactive_handler.safe_input(
            Fore.YELLOW + "请输入电影命名模板",
            settings['movie_template']
        )
        if template:
            settings['movie_template'] = template
        print(Fore.GREEN + f"✅ 电影命名模板: {settings['movie_template']}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 设置电视剧命名模板
    print(Fore.YELLOW + "\n步骤 3/8: 设置电视剧命名模板")
    print(Fore.CYAN + "可用变量: {title}, {season}, {episode}, {ext}")
    try:
        template = interactive_handler.safe_input(
            Fore.YELLOW + "请输入电视剧命名模板",
            settings['tv_template']
        )
        if template:
            settings['tv_template'] = template
        print(Fore.GREEN + f"✅ 电视剧命名模板: {settings['tv_template']}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 设置电视特辑命名模板
    print(Fore.YELLOW + "\n步骤 4/8: 设置电视特辑命名模板")
    print(Fore.CYAN + "可用变量: {title}, {episode}, {ext}")
    try:
        template = interactive_handler.safe_input(
            Fore.YELLOW + "请输入电视特辑命名模板",
            settings['special_template']
        )
        if template:
            settings['special_template'] = template
        print(Fore.GREEN + f"✅ 电视特辑命名模板: {settings['special_template']}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 设置视频扩展名
    print(Fore.YELLOW + "\n步骤 5/8: 设置视频文件扩展名")
    print("当前支持的扩展名: " + ", ".join(settings['video_extensions']))
    print("1. 使用默认扩展名")
    print("2. 自定义扩展名")
    try:
        choice = interactive_handler.safe_input(Fore.YELLOW + "请选择 (1-2)", "1")
        if choice == "2":
            exts = interactive_handler.safe_input("请输入扩展名，用空格分隔 (如 .mp4 .mkv)", ".mp4 .mkv .avi").split()
            if exts:
                settings['video_extensions'] = exts
        print(Fore.GREEN + "✅ 支持的视频扩展名: " + ", ".join(settings['video_extensions']))
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 设置元数据扩展名
    print(Fore.YELLOW + "\n步骤 6/8: 设置元数据文件扩展名")
    print("当前支持的扩展名: " + ", ".join(settings['metadata_extensions']))
    print("1. 使用默认扩展名")
    print("2. 自定义扩展名")
    try:
        choice = interactive_handler.safe_input(Fore.YELLOW + "请选择 (1-2)", "1")
        if choice == "2":
            exts = interactive_handler.safe_input("请输入扩展名，用空格分隔 (如 .srt .nfo)", ".srt .nfo .ass").split()
            if exts:
                settings['metadata_extensions'] = exts
        print(Fore.GREEN + "✅ 支持的元数据扩展名: " + ", ".join(settings['metadata_extensions']))
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 高级设置
    print(Fore.YELLOW + "\n步骤 7/8: 高级设置")
    try:
        # 新增：清理缓存选项
        clear_cache = interactive_handler.confirm_action(
            Fore.YELLOW + "是否清理缓存文件?", False
        )
        if clear_cache:
            cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media_rename_cache.json')
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    print(Fore.GREEN + "✅ 缓存文件已清理!")
                except Exception as e:
                    print(Fore.RED + f"❌ 缓存清理失败: {e}")
            else:
                print(Fore.YELLOW + "ℹ️ 未找到缓存文件，无需清理。")
        
        # 历史记录设置
        enable_history = interactive_handler.confirm_action(
            Fore.YELLOW + "启用重命名历史记录?", settings['enable_history']
        )
        settings['enable_history'] = enable_history
        
        # 跳过现有文件设置
        skip_existing = interactive_handler.confirm_action(
            Fore.YELLOW + "跳过目标已存在的文件?", settings['skip_existing']
        )
        settings['skip_existing'] = skip_existing
        
        # 哈希检查设置
        enable_hash = interactive_handler.confirm_action(
            Fore.YELLOW + "启用文件哈希检查?", settings['enable_hash_check']
        )
        settings['enable_hash_check'] = enable_hash
        
        # 缓存设置
        cache_ttl_str = interactive_handler.safe_input(
            Fore.YELLOW + "目录缓存有效期(秒)",
            str(settings['cache_ttl'])
        )
        try:
            cache_ttl = int(cache_ttl_str)
            settings['cache_ttl'] = max(60, min(cache_ttl, 3600))  # 限制在60-3600秒之间
            print(Fore.GREEN + f"✅ 缓存有效期: {settings['cache_ttl']} 秒")
        except ValueError:
            print(Fore.YELLOW + f"ℹ️ 使用默认缓存有效期: {settings['cache_ttl']} 秒")
        
        # 预览分页设置
        page_size_str = interactive_handler.safe_input(
            Fore.YELLOW + "预览模式每页显示文件数",
            str(settings['preview_page_size'])
        )
        try:
            page_size = int(page_size_str)
            settings['preview_page_size'] = max(5, min(page_size, 50))  # 限制在5-50之间
            print(Fore.GREEN + f"✅ 预览分页大小: {settings['preview_page_size']}")
        except ValueError:
            print(Fore.YELLOW + f"ℹ️ 使用默认分页大小: {settings['preview_page_size']}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # 新增：文件夹类型关键词设置
    print(Fore.YELLOW + "\n步骤 8/8: 文件夹类型检测关键词")
    print("检测到以下关键词的文件夹会自动应用相应规则：")
    
    try:
        # 电视剧关键词
        tv_keywords = interactive_handler.safe_input(
            Fore.YELLOW + "电视剧文件夹关键词(用逗号分隔)",
            ','.join(settings['tv_folder_keywords'])
        )
        if tv_keywords:
            settings['tv_folder_keywords'] = [k.strip() for k in tv_keywords.split(',')]
        print(Fore.GREEN + "✅ 电视剧关键词: " + ", ".join(settings['tv_folder_keywords']))
        
        # 电影关键词
        movie_keywords = interactive_handler.safe_input(
            Fore.YELLOW + "电影文件夹关键词(用逗号分隔)",
            ','.join(settings['movie_folder_keywords'])
        )
        if movie_keywords:
            settings['movie_folder_keywords'] = [k.strip() for k in movie_keywords.split(',')]
        print(Fore.GREEN + "✅ 电影关键词: " + ", ".join(settings['movie_folder_keywords']))
        
        # 强制规则设置
        force_tv = interactive_handler.confirm_action(
            Fore.YELLOW + "强制所有文件使用电视剧规则?", settings['force_tv_rules']
        )
        settings['force_tv_rules'] = force_tv
        
        force_movie = interactive_handler.confirm_action(
            Fore.YELLOW + "强制所有文件使用电影规则?", settings['force_movie_rules']
        )
        settings['force_movie_rules'] = force_movie
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # ========== 特辑文件设置 ==========
    print(Fore.MAGENTA + "\n==== 特辑文件设置 ====")
    try:
        # 启用特辑检查
        enable_special = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用特辑文件检查?", True
        )
        settings['enable_special_check'] = enable_special
        
        # 只有启用特辑检查时，才显示后续设置
        if settings['enable_special_check']:
            # 特辑关键词
            default_keywords = ['特辑','特别篇','Special']
            special_keywords = interactive_handler.safe_input(
                Fore.YELLOW + "特辑关键词(用逗号分隔)",
                ','.join(default_keywords)
            )
            if special_keywords:
                settings['special_keywords'] = [k.strip() for k in special_keywords.split(',')]
            else:
                settings['special_keywords'] = default_keywords
            print(Fore.GREEN + "✅ 特辑关键词: " + ", ".join(settings['special_keywords']))
            
            # 强制特辑季
            force_special_season = interactive_handler.confirm_action(
                Fore.YELLOW + "强制将特辑识别为S00季?", True
            )
            settings['force_special_season'] = force_special_season
            print(Fore.GREEN + f"✅ 强制特辑季: {'开启' if settings['force_special_season'] else '关闭'}")
        
        print(Fore.MAGENTA + "==== 特辑文件设置结束 ====")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # ========== 缓存设置 ==========
    print(Fore.MAGENTA + "\n==== 缓存设置 ====")
    try:
        # 增量缓存更新
        enable_incremental = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用增量缓存更新?", settings.get('enable_incremental_cache', True)
        )
        settings['enable_incremental_cache'] = enable_incremental
        print(Fore.GREEN + f"✅ 增量缓存更新: {'开启' if enable_incremental else '关闭'}")
        
        # 自动清理过期缓存
        auto_cleanup = interactive_handler.confirm_action(
            Fore.YELLOW + "是否自动清理过期缓存?", settings.get('cache_auto_cleanup', True)
        )
        settings['cache_auto_cleanup'] = auto_cleanup
        print(Fore.GREEN + f"✅ 自动清理过期缓存: {'开启' if auto_cleanup else '关闭'}")
        
        # 缓存最大大小
        max_size_str = interactive_handler.safe_input(
            Fore.YELLOW + "缓存最大大小(MB)",
            str(settings.get('cache_max_size_mb', 100))
        )
        try:
            max_size = int(max_size_str)
            settings['cache_max_size_mb'] = max(10, min(max_size, 1000))  # 限制在10-1000MB之间
            print(Fore.GREEN + f"✅ 缓存最大大小: {settings['cache_max_size_mb']} MB")
        except ValueError:
            print(Fore.YELLOW + f"ℹ️ 使用默认缓存大小: {settings.get('cache_max_size_mb', 100)} MB")
        
        print(Fore.MAGENTA + "==== 缓存设置结束 ====")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    # ========== v1.3新增设置 ==========
    print(Fore.MAGENTA + "\n==== v1.3 智能优化设置 ====")
    try:
        # 智能识别设置
        enable_smart_recognition = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用智能文件名识别?", True
        )
        settings['enable_smart_recognition'] = enable_smart_recognition
        print(Fore.GREEN + f"✅ 智能识别: {'开启' if enable_smart_recognition else '关闭'}")
        
        # 性能监控设置
        enable_performance_monitoring = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用性能监控?", True
        )
        settings['performance_monitoring'] = enable_performance_monitoring
        print(Fore.GREEN + f"✅ 性能监控: {'开启' if enable_performance_monitoring else '关闭'}")
        
        # 并行处理设置
        enable_parallel_processing = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用并行处理?", True
        )
        settings['parallel_processing'] = enable_parallel_processing
        print(Fore.GREEN + f"✅ 并行处理: {'开启' if enable_parallel_processing else '关闭'}")
        
        if enable_parallel_processing:
            max_workers_str = interactive_handler.safe_input(
                Fore.YELLOW + "最大并行工作线程数",
                str(settings.get('max_workers', 4))
            )
            try:
                max_workers = int(max_workers_str)
                settings['max_workers'] = max(1, min(max_workers, 16))  # 限制在1-16之间
                print(Fore.GREEN + f"✅ 最大工作线程数: {settings['max_workers']}")
            except ValueError:
                print(Fore.YELLOW + f"ℹ️ 使用默认工作线程数: {settings.get('max_workers', 4)}")
        
        # 沙盒模式设置
        enable_sandbox_mode = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用沙盒模式?", True
        )
        settings['sandbox_mode'] = enable_sandbox_mode
        print(Fore.GREEN + f"✅ 沙盒模式: {'开启' if enable_sandbox_mode else '关闭'}")
        
        # 配置备份设置
        enable_backup = interactive_handler.confirm_action(
            Fore.YELLOW + "是否启用配置备份?", True
        )
        settings['backup_enabled'] = enable_backup
        print(Fore.GREEN + f"✅ 配置备份: {'开启' if enable_backup else '关闭'}")
        
        # 安全级别设置
        print(Fore.YELLOW + "\n安全级别设置:")
        print("1. 低 - 基本安全检查")
        print("2. 中 - 标准安全检查")
        print("3. 高 - 严格安全检查")
        security_choice = interactive_handler.safe_input(
            Fore.YELLOW + "请选择安全级别 (1-3)",
            "3"
        )
        security_levels = {1: "low", 2: "medium", 3: "high"}
        if security_choice.isdigit() and int(security_choice) in security_levels:
            settings['security_level'] = security_levels[int(security_choice)]
            print(Fore.GREEN + f"✅ 安全级别: {settings['security_level']}")
        else:
            settings['security_level'] = "high"
            print(Fore.YELLOW + f"ℹ️ 使用默认安全级别: high")
        
        print(Fore.MAGENTA + "==== v1.3 智能优化设置结束 ====")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
        return settings
    
    print(Fore.GREEN + "\n✅ 所有设置已完成!")
    return settings

# ===================== 主菜单 =====================
def main_menu():
    """主菜单界面"""
    print(Fore.BLUE + "\n" + "="*70)
    print(Fore.CYAN + "🎬 影视文件重命名工具 v1.3 智能优化版")
    print(Fore.BLUE + "="*70)
    print(Fore.YELLOW + "💡 提示: 使用 Ctrl+C 中断操作，Tab 补全路径")
    print(Fore.CYAN + "📖 支持电影、电视剧、特辑等多种格式智能识别")
    print(Fore.BLUE + "="*70)
    
    # 创建交互式处理器
    interactive_handler = InteractiveHandler()
    
    settings = interactive_settings()
    renamer = MediaRenamer(settings)
    
    while True:
        print(Fore.BLUE + "\n" + "="*70)
        print(Fore.CYAN + "📋 主菜单")
        print(Fore.BLUE + "="*70)
        
        # 核心功能
        print(Fore.GREEN + "🚀 核心功能:")
        print("  1. 🎯 执行重命名")
        print("  2. 🔄 增量扫描重命名")
        print("  3. 📦 批量处理多目录")
        print("  4. 👀 预览文件夹重命名")
        
        # 管理功能
        print(Fore.YELLOW + "\n📁 管理功能:")
        print("  5. ↩️ 撤销最后一次重命名")
        print("  6. 📋 查看重命名历史")
        print("  7. 💾 缓存管理")
        
        # 设置功能
        print(Fore.CYAN + "\n⚙️ 设置功能:")
        print("  8. 🔧 修改设置")
        print("  9. 📊 查看当前设置")
        print("  10. 🛡️ 安全防护设置")
        print("  11. 🔒 沙盒模式管理")
        
        # 高级功能
        print(Fore.MAGENTA + "\n🔬 高级功能:")
        print("  12. 📈 操作统计信息")
        print("  13. 🧠 智能分析文件")
        print("  14. 📤 导出配置")
        print("  15. 📥 导入配置")
        print("  16. 📊 生成性能报告")
        
        # 退出
        print(Fore.RED + "\n❌ 退出:")
        print("  17. 👋 退出程序")
        
        print(Fore.BLUE + "="*70)
        print(Fore.YELLOW + "💡 快捷键: Ctrl+C 中断操作 | 数字键快速选择")
        
        try:
            choice = interactive_handler.safe_input(Fore.YELLOW + "\n🎯 请选择操作 (1-17)", "1")
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️  程序被用户中断")
            break
        
        if choice == "1":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🎯 执行重命名")
            print(Fore.CYAN + "="*60)
            print("1. 👀 预览模式 (显示详细对比)")
            print("2. ✨ 执行模式 (实际重命名文件)")
            try:
                mode = interactive_handler.safe_input(Fore.YELLOW + "请选择模式 (1-2)", "1")
                
                if mode == "1":
                    renamer.settings["preview_only"] = True
                    renamer.process_directory()
                elif mode == "2":
                    renamer.settings["preview_only"] = False
                    confirm = interactive_handler.confirm_action(
                        Fore.RED + "⚠️ 确定要实际重命名文件吗？", False
                    )
                    if confirm:
                        renamer.process_directory()
                else:
                    print(Fore.RED + "❌ 无效选择")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "2":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🔄 增量扫描重命名")
            print(Fore.CYAN + "="*60)
            print("1. 👀 预览模式 (仅扫描变动文件)")
            print("2. ✨ 执行模式 (重命名变动文件)")
            try:
                mode = interactive_handler.safe_input(Fore.YELLOW + "请选择模式 (1-2)", "1")
                
                if mode == "1":
                    renamer.settings["preview_only"] = True
                    changed_files = renamer._incremental_scan(renamer.settings["folder_path"])
                    print(Fore.CYAN + f"发现 {len(changed_files)} 个变动文件")
                    if changed_files:
                        renamer.process_directory()
                elif mode == "2":
                    renamer.settings["preview_only"] = False
                    changed_files = renamer._incremental_scan(renamer.settings["folder_path"])
                    print(Fore.CYAN + f"发现 {len(changed_files)} 个变动文件")
                    if changed_files:
                        confirm = interactive_handler.confirm_action(
                            Fore.RED + "⚠️ 确定要重命名这些变动文件吗？", False
                        )
                        if confirm:
                            renamer.process_directory()
                    else:
                        print(Fore.YELLOW + "ℹ️ 没有发现变动文件")
                else:
                    print(Fore.RED + "❌ 无效选择")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "3":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "📦 批量处理多目录")
            print(Fore.CYAN + "="*60)
            try:
                print(Fore.YELLOW + "请输入要处理的目录路径，每行一个，输入空行结束:")
                directories = []
                while True:
                    try:
                        directory = interactive_handler.safe_input(
                            Fore.CYAN + f"目录 {len(directories) + 1}:", 
                            allow_empty=True
                        )
                        if not directory:
                            break
                        if os.path.isdir(directory):
                            directories.append(os.path.abspath(directory))
                            print(Fore.GREEN + f"✅ 已添加: {directory}")
                        else:
                            print(Fore.RED + f"❌ 目录不存在: {directory}")
                    except KeyboardInterrupt:
                        break
                
                if directories:
                    print(Fore.CYAN + f"\n将处理 {len(directories)} 个目录:")
                    for i, directory in enumerate(directories, 1):
                        print(f"  {i}. {directory}")
                    
                    print("\n1. 👀 预览模式")
                    print("2. ✨ 执行模式")
                    mode = interactive_handler.safe_input(Fore.YELLOW + "请选择模式 (1-2)", "1")
                    
                    if mode == "1":
                        renamer.settings["preview_only"] = True
                        renamer._batch_process_directories(directories)
                    elif mode == "2":
                        renamer.settings["preview_only"] = False
                        confirm = interactive_handler.confirm_action(
                            Fore.RED + "⚠️ 确定要批量重命名这些目录中的文件吗？", False
                        )
                        if confirm:
                            renamer._batch_process_directories(directories)
                    else:
                        print(Fore.RED + "❌ 无效选择")
                else:
                    print(Fore.YELLOW + "ℹ️ 未添加任何目录")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "4":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "👀 预览文件夹重命名")
            print(Fore.CYAN + "="*60)
            try:
                renamer.settings["preview_only"] = True
                renamer.process_directory()
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  预览被用户中断")
                
        elif choice == "5":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "↩️ 撤销重命名")
            print(Fore.CYAN + "="*60)
            try:
                directory = interactive_handler.safe_input(
                    Fore.YELLOW + "输入要撤销的目录路径 (直接回车使用当前目录)",
                    renamer.settings["folder_path"]
                )
                if not directory:
                    directory = renamer.settings["folder_path"]
                if renamer.undo_last(directory):
                    print(Fore.GREEN + "✅ 撤销操作成功完成!")
                else:
                    print(Fore.RED + "❌ 撤销操作失败")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
            
        elif choice == "6":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "📋 查看历史记录")
            print(Fore.CYAN + "="*60)
            try:
                directory = interactive_handler.safe_input(
                    Fore.YELLOW + "输入要查看的目录路径 (直接回车使用当前目录)",
                    renamer.settings["folder_path"]
                )
                if not directory:
                    directory = renamer.settings["folder_path"]
                renamer.show_history(directory)
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
            
        elif choice == "7":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "💾 缓存管理")
            print(Fore.CYAN + "="*60)
            print("1. 📊 查看缓存信息")
            print("2. 🔄 重建缓存")
            print("3. 🧹 清理缓存")
            print("4. ⚙️ 缓存设置")
            print("5. ↩️ 返回主菜单")
            
            try:
                cache_choice = interactive_handler.safe_input(Fore.YELLOW + "\n请选择操作 (1-5)", "1")
                
                if cache_choice == "1":
                    renamer.show_cache_info()
                elif cache_choice == "2":
                    confirm = interactive_handler.confirm_action(
                        Fore.YELLOW + "确定要重建缓存吗？这将重新扫描所有文件。", False
                    )
                    if confirm:
                        renamer.cache = {}
                        renamer.build_directory_cache(renamer.settings["folder_path"])
                        print(Fore.GREEN + "✅ 缓存重建完成")
                elif cache_choice == "3":
                    confirm = interactive_handler.confirm_action(
                        Fore.YELLOW + "确定要清理缓存吗？", False
                    )
                    if confirm:
                        renamer.clear_cache()
                elif cache_choice == "4":
                    print(Fore.CYAN + "\n当前缓存设置:")
                    print(f"  缓存有效期: {renamer.settings.get('cache_ttl', 300)} 秒")
                    print(f"  增量缓存更新: {'开启' if renamer.settings.get('enable_incremental_cache', True) else '关闭'}")
                    print(f"  自动清理过期缓存: {'开启' if renamer.settings.get('cache_auto_cleanup', True) else '关闭'}")
                    print(f"  缓存最大大小: {renamer.settings.get('cache_max_size_mb', 100)} MB")
                elif cache_choice == "5":
                    continue
                else:
                    print(Fore.RED + "❌ 无效选择")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                continue
                
        elif choice == "8":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🔧 修改设置")
            print(Fore.CYAN + "="*60)
            try:
                settings = interactive_settings()
                renamer = MediaRenamer(settings)
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  设置被用户中断")
            
        elif choice == "9":
            renamer.show_settings()
            
        elif choice == "10":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🛡️ 安全防护设置")
            print(Fore.CYAN + "="*60)
            print("1. 🛡️ 查看当前安全设置")
            print("2. ⚙️ 修改安全设置")
            print("3. 📊 查看安全日志")
            print("4. 🔄 重置错误计数")
            print("5. ↩️ 返回主菜单")
            
            try:
                security_choice = interactive_handler.safe_input(Fore.YELLOW + "\n请选择操作 (1-5)", "1")
                
                if security_choice == "1":
                    print(Fore.CYAN + "\n当前安全设置:")
                    print(f"  最大文件大小: {renamer.security_settings['max_file_size_mb']} MB")
                    print(f"  允许的文件类型: {', '.join(renamer.security_settings['allowed_extensions'])}")
                    print(f"  禁止访问路径: {', '.join(renamer.security_settings['forbidden_paths']) if renamer.security_settings['forbidden_paths'] else '无'}")
                    print(f"  单次操作最大文件数: {renamer.security_settings['max_files_per_operation']}")
                    print(f"  路径验证: {'开启' if renamer.security_settings['enable_path_validation'] else '关闭'}")
                    print(f"  文件大小检查: {'开启' if renamer.security_settings['enable_file_size_check'] else '关闭'}")
                    print(f"  可疑模式检测: {'开启' if renamer.security_settings['enable_suspicious_detection'] else '关闭'}")
                    
                elif security_choice == "2":
                    print(Fore.YELLOW + "\n修改安全设置:")
                    
                    # 最大文件大小
                    max_size_str = interactive_handler.safe_input(
                        Fore.YELLOW + f"最大文件大小(MB) [当前: {renamer.security_settings['max_file_size_mb']}]",
                        str(renamer.security_settings['max_file_size_mb'])
                    )
                    try:
                        max_size = int(max_size_str)
                        renamer.security_settings['max_file_size_mb'] = max(100, min(max_size, 50000))
                        print(Fore.GREEN + f"✅ 最大文件大小: {renamer.security_settings['max_file_size_mb']} MB")
                    except ValueError:
                        print(Fore.YELLOW + "ℹ️ 保持当前设置")
                    
                    # 单次操作最大文件数
                    max_files_str = interactive_handler.safe_input(
                        Fore.YELLOW + f"单次操作最大文件数 [当前: {renamer.security_settings['max_files_per_operation']}]",
                        str(renamer.security_settings['max_files_per_operation'])
                    )
                    try:
                        max_files = int(max_files_str)
                        renamer.security_settings['max_files_per_operation'] = max(100, min(max_files, 100000))
                        print(Fore.GREEN + f"✅ 单次操作最大文件数: {renamer.security_settings['max_files_per_operation']}")
                    except ValueError:
                        print(Fore.YELLOW + "ℹ️ 保持当前设置")
                    
                    # 安全功能开关
                    path_validation = interactive_handler.confirm_action(
                        Fore.YELLOW + "启用路径验证?",
                        renamer.security_settings['enable_path_validation']
                    )
                    renamer.security_settings['enable_path_validation'] = path_validation
                    print(Fore.GREEN + f"✅ 路径验证: {'开启' if path_validation else '关闭'}")
                    
                    file_size_check = interactive_handler.confirm_action(
                        Fore.YELLOW + "启用文件大小检查?",
                        renamer.security_settings['enable_file_size_check']
                    )
                    renamer.security_settings['enable_file_size_check'] = file_size_check
                    print(Fore.GREEN + f"✅ 文件大小检查: {'开启' if file_size_check else '关闭'}")
                    
                    suspicious_detection = interactive_handler.confirm_action(
                        Fore.YELLOW + "启用可疑模式检测?",
                        renamer.security_settings['enable_suspicious_detection']
                    )
                    renamer.security_settings['enable_suspicious_detection'] = suspicious_detection
                    print(Fore.GREEN + f"✅ 可疑模式检测: {'开启' if suspicious_detection else '关闭'}")
                    
                elif security_choice == "3":
                    print(Fore.CYAN + "\n安全日志信息:")
                    error_summary = renamer.error_handler.get_error_summary()
                    print(f"  总错误数: {error_summary['total_errors']}")
                    print(f"  错误类型数: {len(error_summary['error_types'])}")
                    print(f"  最近错误数: {sum(error_summary['recent_errors'].values())}")
                    print(Fore.YELLOW + "\n请查看 logs/security_*.log 文件获取详细安全日志")
                    
                elif security_choice == "4":
                    confirm = interactive_handler.confirm_action(
                        Fore.YELLOW + "确定要重置错误计数吗？", False
                    )
                    if confirm:
                        renamer.error_handler.reset_error_counts()
                        print(Fore.GREEN + "✅ 错误计数已重置")
                        
                elif security_choice == "5":
                    continue
                else:
                    print(Fore.RED + "❌ 无效选择")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                continue
                
        elif choice == "11":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🔒 沙盒模式管理")
            print(Fore.CYAN + "="*60)
            print("1. 🔒 启用沙盒模式")
            print("2. 🔓 禁用沙盒模式")
            print("3. 📊 查看沙盒状态")
            print("4. 🧹 清理沙盒目录")
            print("5. ⚙️ 沙盒设置")
            print("6. ↩️ 返回主菜单")
            
            try:
                sandbox_choice = interactive_handler.safe_input(Fore.YELLOW + "\n请选择操作 (1-6)", "1")
                
                if sandbox_choice == "1":
                    sandbox_dir = interactive_handler.safe_input(
                        Fore.YELLOW + "输入沙盒目录路径 (直接回车使用默认路径)",
                        allow_empty=True
                    )
                    if renamer.enable_sandbox_mode(sandbox_dir if sandbox_dir else None):
                        print(Fore.GREEN + "✅ 沙盒模式已启用")
                    else:
                        print(Fore.RED + "❌ 启用沙盒模式失败")
                        
                elif sandbox_choice == "2":
                    if renamer.disable_sandbox_mode():
                        print(Fore.GREEN + "✅ 沙盒模式已禁用")
                    else:
                        print(Fore.RED + "❌ 禁用沙盒模式失败")
                        
                elif sandbox_choice == "3":
                    renamer.show_sandbox_info()
                    
                elif sandbox_choice == "4":
                    if renamer.sandbox_mode and renamer.sandbox_directory:
                        confirm = interactive_handler.confirm_action(
                            Fore.RED + "确定要清理沙盒目录吗？这将删除所有沙盒中的文件。", False
                        )
                        if confirm:
                            try:
                                shutil.rmtree(renamer.sandbox_directory)
                                renamer.sandbox_mapping.clear()
                                renamer.sandbox_operations.clear()
                                print(Fore.GREEN + "✅ 沙盒目录已清理")
                            except Exception as e:
                                print(Fore.RED + f"❌ 清理沙盒目录失败: {e}")
                    else:
                        print(Fore.YELLOW + "ℹ️ 沙盒模式未启用")
                        
                elif sandbox_choice == "5":
                    print(Fore.CYAN + "\n沙盒模式设置:")
                    print(f"  沙盒模式: {'启用' if renamer.sandbox_mode else '禁用'}")
                    print(f"  沙盒目录: {renamer.sandbox_directory or '未设置'}")
                    print(f"  操作确认: {'启用' if renamer.confirmation_enabled else '禁用'}")
                    print(f"  确认阈值: {renamer.confirmation_threshold} 个文件")
                    print(f"  确认超时: {renamer.confirmation_timeout} 秒")
                    
                elif sandbox_choice == "6":
                    continue
                else:
                    print(Fore.RED + "❌ 无效选择")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                continue
                
        elif choice == "12":
            renamer.show_operation_stats()
            
        elif choice == "13":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "🧠 智能分析文件")
            print(Fore.CYAN + "="*60)
            try:
                file_path = interactive_handler.safe_input(
                    Fore.YELLOW + "请输入要分析的文件路径",
                    allow_empty=True
                )
                if file_path and os.path.exists(file_path):
                    renamer.show_smart_analysis(file_path)
                else:
                    print(Fore.RED + "❌ 文件不存在或路径无效")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "14":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "📤 导出配置")
            print(Fore.CYAN + "="*60)
            try:
                export_file = interactive_handler.safe_input(
                    Fore.YELLOW + "请输入导出文件路径 (直接回车使用默认路径)",
                    allow_empty=True
                )
                renamer.export_config(export_file if export_file else None)
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "15":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "📥 导入配置")
            print(Fore.CYAN + "="*60)
            try:
                import_file = interactive_handler.safe_input(
                    Fore.YELLOW + "请输入要导入的配置文件路径"
                )
                if import_file and os.path.exists(import_file):
                    renamer.import_config(import_file)
                else:
                    print(Fore.RED + "❌ 配置文件不存在")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
                
        elif choice == "16":
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.BLUE + "📊 生成性能报告")
            print(Fore.CYAN + "="*60)
            try:
                report_file = interactive_handler.safe_input(
                    Fore.YELLOW + "请输入报告文件路径 (直接回车显示在控制台)",
                    allow_empty=True
                )
                renamer.generate_performance_report(report_file if report_file else None)
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  操作被用户中断")
            
        elif choice == "17":
            print(Fore.GREEN + "\n👋 感谢使用影视文件重命名工具!")
            print(Fore.CYAN + "🎬 祝您观影愉快，再见!")
            break
            
        else:
            print(Fore.RED + "❌ 无效选择，请重新输入")
        
        # 操作完成后暂停，让用户查看结果
        if choice in ["1", "2", "3", "4"]:
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.YELLOW + "按 Enter 键返回主菜单...")
            try:
                input()
            except KeyboardInterrupt:
                pass

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        print(Fore.RED + f"\n程序发生未预期错误: {e}")
        logging.getLogger("MediaRenamer").exception("未处理的异常")
        print("请查看日志文件获取详细信息")