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
- NAS API 服务（`server/`）：FastAPI 包装解析引擎为 HTTP 服务，支持鉴权（Bearer Token）、目录扫描、批量解析、重命名预览与执行（自动备份），路径穿越防护，提供 Dockerfile 供群晖部署
- 移动端 Flutter 骨架（`mobile/`）：NAS 地址+Token 登录、目录扫描、重命名预览/执行全流程客户端
- 移动端构建工程（`mobile/android/` + `mobile/ios/`）：按 Flutter stable 官方模板生成（Gradle 9.3.1 / AGP 9.1.0 / Kotlin 2.4.0），含 Android 五档图标与 iOS AppIcon 全套、启动屏、签名与打包说明（本机无 Flutter SDK，待构建验证）
- 发布前自动验证脚本 `scripts/check_release.py`（版本一致性 / CHANGELOG 完整性 / 可选测试回归）
- GitHub Actions CI：push/PR 自动运行全功能测试与核心引擎测试
- MIT License
- 一键发布脚本 `scripts/release.py`：一条命令完成 验证 → Changelog 升级 → 打 tag → 推送 → 自动发布
- 性能基准测试 `scripts/benchmark.py`：9 类标准用例计时，结果自动对比历史基准
- 应用内升级检测 `core/update_checker.py`：启动后后台查询 GitHub 最新 Release，有新版自动提示
- 预发布流程：`v*-rc.*` / `v*-beta.*` 标签自动构建 prerelease，不推送给普通用户

### 改进
- 配置来源统一：`core/tv_rename_cache_optimized.py` 的 `DEFAULT_SETTINGS` 改为从 `core/constants.py` 导入基础配置，消除两套配置漂移
- 核心模块拆分：`PatternRecognizer` / `ConfigManager` / `InteractiveHandler` 拆出为独立文件，原文件 5205 → 4471 行
- 清理生产代码 63 处未使用导入及死代码
- 缓存版本检查与 UI 标题改为引用 `core/version.py`，升级版本号后旧缓存自动失效重建
- 发布流程优化：CI 增加 pip 依赖缓存、编译检查、导入冒烟、GUI 启动验证；ruff（F/E9）与 mypy（新代码渐进式）纳入自动门禁
- 发布验证增强：版本兼容性检查（Python 范围 / 依赖清单 / 入口文件 / 模块导入）与性能基准测试纳入 check_release
- 发布安全增强：Release 自动生成 SHA256 校验文件；workflow 权限最小化；构建产物自动冒烟验证
- 发布说明自动生成：CHANGELOG 提取 + 下载校验指引；预发布标签自动标记 prerelease
- 升级检测可见化：检测到新版本时主窗口状态栏显示横幅（查看详情 / 不再提醒，按版本持久化）
- 测试收敛：临时开发脚本归口 tests/legacy/；新增解析引擎 15 用例参数化测试并纳入 CI

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
