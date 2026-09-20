# Changelog

本文件记录「影视文件智能重命名工具」的版本变更，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 标准，版本号遵循 [语义化版本 SemVer](https://semver.org/lang/zh-CN/)（MAJOR.MINOR.PATCH）。

## 变更分类

- **新增**（Added）：新功能
- **改进**（Changed）：现有功能的变更/优化
- **废弃**（Deprecated）：即将移除的功能
- **移除**（Removed）：已移除的功能
- **修复**（Fixed）：缺陷修复
- **安全**（Security）：安全相关修复

## [Unreleased]

### 新增
- 版本管理与 Changelog 系统：`core/version.py` 作为版本号唯一来源，`CHANGELOG.md` 按 Keep a Changelog 标准维护
- 发布前自动验证脚本 `scripts/check_release.py`（版本一致性 / CHANGELOG 完整性 / 可选测试回归）
- GitHub Actions CI：push/PR 自动运行全功能测试与核心引擎测试
- MIT License

### 改进
- 配置来源统一：`core/tv_rename_cache_optimized.py` 的 `DEFAULT_SETTINGS` 改为从 `core/constants.py` 导入基础配置，消除两套配置漂移
- 核心模块拆分：`PatternRecognizer` / `ConfigManager` / `InteractiveHandler` 拆出为独立文件，原文件 5205 → 4471 行
- 清理生产代码 63 处未使用导入及死代码
- 缓存版本检查与 UI 标题改为引用 `core/version.py`，升级版本号后旧缓存自动失效重建

### 修复
- 移除编码损坏无法编译的单文件版 `tv_rename_gui.py`（源文件含 64 处 U+FFFD，不可恢复）
- `DEFAULT_SETTINGS` 中 `cache_ttl` 字典重复键（86400 被 300 覆盖），统一为 3600 秒

### 安全
- GitHub 访问令牌不落盘：凭证仅以内联方式用于单次推送，`git remote` 无令牌明文

## [1.3.0] - 2026-09-21

首个正式发布（对应 GitHub Release v1.3）。

### 新增
- 智能解析引擎：正则模式 + guessit 兜底，识别电影 / 电视剧 / 特辑
- 批量处理：多线程扫描、目录缓存、预览后统一重命名
- 智能分析对话框：逐文件解析元数据并给出重命名建议
- 撤销 / 重做：操作历史记录，误操作可回退
- 文件保护：元数据文件（字幕等）联动重命名
- 中文季集模式：支持「第1季.第2集」格式识别
- 性能监控：内存 / CPU 使用统计与报告

### 改进
- 年份提取统一取最后合理年份，过滤 1080/2160 等分辨率误判
- 置信度按匹配模式分级（精确 > 模糊）
- 批量模式下电视剧标题取自所在文件夹名

### 修复
- 解析引擎标题提取改为区间切片，避免全局替换污染
- 修正测试脚本 PYTHONPATH 与 QKeySequence 导入问题（全功能测试 6/6）

---

[Unreleased]: https://github.com/1525745393/tv-media-renamer/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/1525745393/tv-media-renamer/releases/tag/v1.3
