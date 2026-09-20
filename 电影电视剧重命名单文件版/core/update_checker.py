# -*- coding: utf-8 -*-
"""应用内升级检测。

启动时后台线程查询 GitHub 最新 Release，与当前版本对比：
- 有更新 → 记录日志并回调（GUI 可显示提示）
- 网络失败 / 非 GitHub 环境 → 静默跳过，不影响使用

用法：
    from core.update_checker import UpdateChecker
    checker = UpdateChecker(version="1.3.0", repo="1525745393/tv-media-renamer")
    checker.check_async(on_result=lambda info: print(info))

安全说明：
- 固定 HTTPS 连接 api.github.com（不跟随第三方重定向）
- 仅读取公开 Release 元数据，不做任何写入
- 对比前校验版本号格式（SemVer），忽略异常数据
"""
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

logger = logging.getLogger(__name__)

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
TIMEOUT = 10          # 请求超时（秒）
REQUEST_HEADERS = {
    "User-Agent": "tv-media-renamer-update-checker",
    "Accept": "application/vnd.github+json",
}


def parse_version(v: str) -> Optional[tuple[int, int, int]]:
    """解析 SemVer 字符串为可比较元组；非法返回 None。"""
    if not isinstance(v, str) or not SEMVER_RE.match(v.strip()):
        return None
    try:
        return tuple(int(p) for p in v.strip().split("."))  # type: ignore[return-value]
    except ValueError:
        return None


def is_newer(latest: str, current: str) -> bool:
    """latest 是否严格高于 current（均须为合法 SemVer）。"""
    lv, cv = parse_version(latest), parse_version(current)
    if lv is None or cv is None:
        return False
    return lv > cv  # type: ignore[operator]


class UpdateInfo:
    """升级信息。"""

    def __init__(self, latest_version: str, current_version: str,
                 release_url: str, notes: str = "", prerelease: bool = False) -> None:
        self.latest_version = latest_version
        self.current_version = current_version
        self.release_url = release_url
        self.notes = notes
        self.prerelease = prerelease

    @property
    def has_update(self) -> bool:
        return is_newer(self.latest_version, self.current_version)


class UpdateChecker:
    """后台升级检测器。"""

    def __init__(self, version: str, repo: str = "1525745393/tv-media-renamer") -> None:
        self.version = version
        self.repo = repo
        self._thread: Optional[threading.Thread] = None

    def _fetch_latest(self) -> Optional[dict]:
        """查询 GitHub 最新 Release 元数据（跳过预发布）。"""
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
                if resp.status != 200:
                    logger.debug("升级检测：HTTP %s", resp.status)
                    return None
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, OSError) as e:
            logger.debug("升级检测失败（静默）: %s", e)
            return None
        if not isinstance(data, dict):
            return None
        return data

    def check(self) -> Optional[UpdateInfo]:
        """同步检测（调用方负责网络阻塞）。"""
        data = self._fetch_latest()
        if not data:
            return None
        tag = data.get("tag_name", "")
        latest = tag[1:] if tag.startswith("v") else tag
        url = data.get("html_url", "")
        notes = data.get("body") or ""
        prerelease = bool(data.get("prerelease", False))
        info = UpdateInfo(
            latest_version=latest,
            current_version=self.version,
            release_url=url,
            notes=notes[:500],       # 仅取说明开头用于提示
            prerelease=prerelease,
        )
        if info.has_update:
            logger.info("发现新版本 %s（当前 %s）: %s", latest, self.version, url)
        return info

    def check_async(self, on_result: Optional[Callable[[Optional[UpdateInfo]], None]] = None,
                    delay: float = 2.0) -> None:
        """后台线程检测，不阻塞启动；失败静默。"""

        def _run() -> None:
            time.sleep(delay)  # 等主窗口就绪后再查
            info = self.check()
            if on_result is not None:
                try:
                    on_result(info)
                except Exception:  # noqa: BLE001 回调异常不影响应用
                    logger.debug("升级检测回调异常", exc_info=True)

        self._thread = threading.Thread(target=_run, daemon=True, name="update-check")
        self._thread.start()
