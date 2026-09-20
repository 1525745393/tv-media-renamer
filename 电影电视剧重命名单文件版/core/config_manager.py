# -*- coding: utf-8 -*-
"""影视重命名工具 - Config Manager模块

从 core/tv_rename_cache_optimized.py 拆出，保持行为一致。
"""
import os
import json
import time
import glob
import shutil
import logging
from datetime import datetime
from colorama import Fore
from core.constants import DEFAULT_SETTINGS


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
