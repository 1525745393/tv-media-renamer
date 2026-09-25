# -*- coding: utf-8 -*-
"""版本号唯一来源。

版本格式：SemVer（MAJOR.MINOR.PATCH）
- MAJOR：不兼容的架构/行为变更
- MINOR：向后兼容的新功能
- PATCH：向后兼容的缺陷修复

发布新版本流程：
1. 修改 __version__（唯一版本来源）
2. 更新 CHANGELOG.md（Keep a Changelog 标准，分类：新增/修复/改进/废弃/移除/安全）
3. 运行 scripts/check_release.py 自动验证版本一致性
4. 全部测试通过后打 tag（v<版本号>）并创建 GitHub Release
"""

__version__ = "1.4.0"

# 兼容别名
VERSION = __version__

# 应用信息
APP_NAME = "影视文件智能重命名工具"
RELEASE_DATE = "2026-09-25"


def get_version() -> str:
    """获取当前版本号。"""
    return __version__
