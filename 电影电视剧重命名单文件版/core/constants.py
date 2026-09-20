# constants.py

MOVIE_TYPE = "电影"
TV_TYPE = "电视剧"
SPECIAL_TYPE = "特辑"

DEFAULT_MOVIE_TEMPLATE = "{title} ({year}){ext}"
DEFAULT_TV_TEMPLATE = "{title}.S{season:02d}.E{episode:02d}{ext}"
DEFAULT_SPECIAL_TEMPLATE = "{title}.S00.E{episode:02d}{ext}"

# 默认设置
DEFAULT_SETTINGS = {
    # 文件类型设置
    "video_extensions": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "metadata_extensions": [".srt", ".ass", ".ssa", ".sub", ".nfo", ".vsmeta"],
    "audio_extensions": [".aac", ".ac3", ".dts", ".flac", ".mp3", ".wav", ".m4a"],
    
    # 文件类型检查选项
    "enable_movie_check": True,  # 检查电影文件
    "enable_tv_check": True,     # 检查电视剧文件
    "enable_special_check": True, # 检查特辑文件
    "force_movie_rules": False,   # 强制应用电影命名规则
    "force_tv_rules": False,      # 强制应用电视剧命名规则
    
    # 命名规则设置
    "movie_template": "{title} ({year})",
    "tv_template": "{title}.S{season:02d}.E{episode:02d}",
    "special_template": "{title}.S00.E{episode:02d}",
    
    # 性能设置
    "max_workers": 8,  # 最大工作线程数
    "chunk_size": 100,  # 批量处理文件数
    "cache_ttl": 3600,  # 缓存有效期（秒）- 从300秒增加到1小时
    "fast_mode": True,  # 启用快速扫描模式
    
    # 安全设置
    "backup_enabled": True,
    "backup_dir": ".backups",
    "confirm_operations": True,
    "sandbox_mode": False,
    
    # 日志设置
    "log_level": "INFO",
    "log_rotation": True,
    "max_log_size": 10 * 1024 * 1024,  # 10MB
    "max_log_files": 5,
    
    # 历史记录设置
    "max_history": 100,
    "auto_save_history": True,
    
    # 界面设置
    "theme": "light",
    "window_width": 1400,
    "window_height": 800,
    "auto_save_settings": True
} 