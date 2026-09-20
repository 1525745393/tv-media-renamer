# 影视文件智能重命名工具（tv-media-renamer）

基于 PyQt5 的影视文件批量重命名工具，自动识别**电影 / 电视剧 / 特辑**的文件类型、标题、年份、季数、集数，按规则批量重命名并支持预览、撤销、智能分析、缓存加速。

主项目位于 `电影电视剧重命名单文件版/`（GUI + 核心引擎 + 测试）。

## 功能特性

- 🎬 **智能解析**：正则模式 + guessit 兜底，识别 `Avengers.Endgame.2019`、`三体.2023.S01E01.4K`、`辛普森一家.第1季.第2集` 等常见命名
- 🗂️ **类型识别**：电影按「标题 (年份)」、电视剧按「标题.Sxx.Exx」、特辑单独规则
- ⚡ **批量处理**：多线程扫描 + 目录缓存，快速预览后统一重命名
- ↩️ **撤销/重做**：操作历史记录，误操作可回退
- 🧠 **智能分析**：逐文件解析元数据并给出重命名建议
- 🛡️ **文件保护**：元数据文件（字幕等）联动重命名

## 运行环境

- Python 3.8+（已在 3.12 验证）
- 依赖：`pip install PyQt5 colorama guessit psutil`

## 快速开始

```bash
# 完整版
cd 电影电视剧重命名单文件版
pip install -r main/requirements.txt
python3 main/tv_rename_gui_v1.3.py

# 运行测试
python3 tests/test_all_features.py        # 全功能测试（6/6 通过）
env PYTHONPATH=. python3 tests/test_media_renamer.py
```

## 目录结构

```
电影电视剧重命名单文件版/
├── main/          # 程序入口（tv_rename_gui_v1.3.py）
├── core/          # 核心引擎（解析/季集/年份/批量/历史）
├── ui/            # 界面层（主窗口/设置/批量预览/智能分析）
├── modules/       # 功能模块（线程/批量/分类/保护）
├── tests/         # 自动化测试
├── scripts/       # 启动脚本 + 调试工具
├── config/        # 运行配置
└── docs/          # 文档与历史报告
```

## 解析规则示例

| 文件名 | 识别结果 |
|---|---|
| `Avengers.Endgame.2019.mkv` | 电影 · Avengers Endgame · 2019 |
| `The.Witcher.S01E01.1080p.mkv` | 电视剧 · The Witcher · S1E1 |
| `三体.2023.S01E01.4K.mp4` | 电视剧 · 三体 · S1E1 · 2023 |
| `辛普森一家.第1季.第2集.mp4` | 电视剧 · 辛普森一家 · S1E2 |

## 说明

- 批量模式下，电视剧标题取自**所在文件夹名**（系列剧按文件夹组织）；电影标题取自文件名
- 运行时日志、缓存、备份不纳入版本控制（见 `.gitignore`）
