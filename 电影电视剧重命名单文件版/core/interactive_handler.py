# -*- coding: utf-8 -*-
"""影视重命名工具 - Interactive Handler模块

从 core/tv_rename_cache_optimized.py 拆出，保持行为一致。
"""
import os
import sys
import signal
from typing import Optional, List
from colorama import Fore
try:
    import readline  # noqa: F401  # 交互式输入增强
except ImportError:
    pass


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
        except Exception:
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
