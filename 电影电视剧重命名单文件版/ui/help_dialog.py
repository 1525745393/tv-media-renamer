#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帮助对话框模块 - 影视文件重命名工具 v1.3
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QTextEdit, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class HelpDialog(QDialog):
    """帮助对话框"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置界面"""
        self.setWindowTitle("帮助 - 影视文件重命名工具 v1.3")
        self.setModal(True)
        self.resize(900, 700)
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 快速开始标签页
        self.tab_widget.addTab(self.create_quick_start_tab(), "快速开始")
        
        # 使用说明标签页
        self.tab_widget.addTab(self.create_usage_tab(), "使用说明")
        
        # 命名规则标签页
        self.tab_widget.addTab(self.create_naming_rules_tab(), "命名规则")
        
        # 常见问题标签页
        self.tab_widget.addTab(self.create_faq_tab(), "常见问题")
        
        # 关于标签页
        self.tab_widget.addTab(self.create_about_tab(), "关于")
        
        layout.addWidget(self.tab_widget)
        
        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setStyleSheet("QPushButton { background-color: #28a745; border: none; color: white; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #218838; }")
        
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_quick_start_tab(self) -> QWidget:
        """创建快速开始标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # type: ignore
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # type: ignore
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # 欢迎信息
        welcome_group = QGroupBox("🎬 欢迎使用影视文件重命名工具")
        welcome_layout = QVBoxLayout()
        
        welcome_text = QTextEdit()
        welcome_text.setReadOnly(True)
        welcome_text.setMaximumHeight(100)
        welcome_text.setPlainText("""
欢迎使用影视文件重命名工具 v1.3 智能分析版！

这是一个智能的影视文件重命名工具，可以帮助您：
• 🔍 智能识别电影、电视剧、动画、纪录片等信息
• 📝 批量重命名文件，支持选择性操作
• 🏷️ 多标签分类系统，支持主分类和次分类
• 📊 置信度评分和智能建议
• 🔄 撤销/重做功能，支持多级操作历史
• 🛡️ 文件保护机制，安全可靠
• ⚡ 多线程处理，高效快速
• 📈 实时进度监控和性能优化

本工具支持的文件格式：
• 视频：MP4, MKV, AVI, MOV, WMV, FLV, WEBM
• 字幕：SRT, ASS, SSA, SUB
• 其他：NFO, JPG, PNG, TXT
        """.strip())
        
        welcome_layout.addWidget(welcome_text)
        welcome_group.setLayout(welcome_layout)
        content_layout.addWidget(welcome_group)
        
        # 快速开始步骤
        steps_group = QGroupBox("📋 快速开始步骤")
        steps_layout = QVBoxLayout()
        
        steps_text = QTextEdit()
        steps_text.setReadOnly(True)
        steps_text.setPlainText("""
1. 📁 选择文件夹
   • 点击"选择文件夹"按钮或使用快捷键 Ctrl+O
   • 选择包含影视文件的文件夹
   • 支持拖拽文件夹到程序窗口
   • 支持子文件夹扫描

2. 🔍 智能分析
   • 点击"智能分析"按钮或使用快捷键 Ctrl+A
   • 程序会自动分析文件夹中的影视文件
   • 在智能分析对话框中查看详细结果
   • 查看文件分类、置信度评分和建议

3. 📝 批量操作
   • 在智能分析对话框中查看分析结果
   • 使用批量操作标签页管理重命名和移动操作
   • 支持选择性操作和批量处理
   • 可以预览重命名结果

4. 🚀 执行重命名
   • 确认预览结果无误后
   • 点击"执行重命名"按钮或使用快捷键 Ctrl+R
   • 等待操作完成，查看实时进度

5. ✅ 完成
   • 查看重命名结果
   • 如有需要可以使用撤销功能（Ctrl+Z）
   • 查看操作历史记录
        """.strip())
        
        steps_layout.addWidget(steps_text)
        steps_group.setLayout(steps_layout)
        content_layout.addWidget(steps_group)
        
        # 注意事项
        notes_group = QGroupBox("⚠️ 注意事项")
        notes_layout = QVBoxLayout()
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(150)
        notes_text.setPlainText("""
• 建议在重命名前备份重要文件
• 确保有足够的磁盘空间
• 关闭可能占用文件的程序
• 首次使用建议先使用智能分析功能
• 支持撤销/重做功能，但建议谨慎操作
• 如遇到问题请查看日志文件
• 程序支持多线程处理，请耐心等待
• 智能分析功能需要文件名包含足够信息
• 置信度评分低于0.5的文件建议手动检查
        """.strip())
        
        notes_layout.addWidget(notes_text)
        notes_group.setLayout(notes_layout)
        content_layout.addWidget(notes_group)
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
        
    def create_usage_tab(self) -> QWidget:
        """创建使用说明标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # 界面说明
        interface_group = QGroupBox("🖥️ 界面说明")
        interface_layout = QVBoxLayout()
        
        interface_text = QTextEdit()
        interface_text.setReadOnly(True)
        interface_text.setPlainText("""
左侧控制面板：
• 📁 文件夹选择：选择要处理的文件夹
• 🔍 智能分析：打开智能分析对话框
• ⚡ 主要操作：扫描、重命名、取消操作
• 🛠️ 工具：主题切换、设置、帮助

右侧文件表格：
• 📁 原文件名：文件的原始名称
• 🎬 识别结果：自动识别的影视信息
• 📝 新文件名：重命名后的文件名
• 📊 文件类型：电影、电视剧、动画、纪录片等
• 📈 状态：待处理、成功、失败、跳过
• 🔍 操作：预览、编辑、跳过按钮

智能分析对话框：
• 📊 分析结果：显示文件分析详情（标题、年份、质量、编码等）
• 🏷️ 分类结果：显示文件分类信息（主分类、次分类、标签）
• 📝 批量操作：管理批量重命名和移动操作
• 📈 统计报告：显示分析统计信息

底部状态栏：
• 🚀 状态信息：当前操作状态
• 📊 进度条：操作进度显示
• 💾 内存使用：程序内存占用
        """.strip())
        
        interface_layout.addWidget(interface_text)
        interface_group.setLayout(interface_layout)
        content_layout.addWidget(interface_group)
        
        # 搜索和筛选
        search_group = QGroupBox("🔍 搜索和筛选")
        search_layout = QVBoxLayout()
        
        search_text = QTextEdit()
        search_text.setReadOnly(True)
        search_text.setPlainText("""
搜索功能：
• 支持按文件名搜索
• 支持按标题搜索
• 支持按类型搜索
• 实时搜索，输入即搜索

筛选功能：
• 按文件类型筛选
• 支持电影、电视剧、特辑筛选
• 支持全部类型显示
• 可清除所有筛选条件

批量预览：
• 查看所有文件的重命名预览
• 支持详细对比
• 可导出预览结果
        """.strip())
        
        search_layout.addWidget(search_text)
        search_group.setLayout(search_layout)
        content_layout.addWidget(search_group)
        
        # 操作说明
        operation_group = QGroupBox("⚙️ 操作说明")
        operation_layout = QVBoxLayout()
        
        operation_text = QTextEdit()
        operation_text.setReadOnly(True)
        operation_text.setPlainText("""
扫描操作：
• 自动识别文件格式
• 提取影视信息
• 生成重命名预览
• 支持批量处理

重命名操作：
• 支持批量重命名
• 自动备份原文件
• 支持撤销操作
• 错误处理和恢复

预览功能：
• 详细文件信息
• 识别结果展示
• 重命名对比
• 支持编辑修改
        """.strip())
        
        operation_layout.addWidget(operation_text)
        operation_group.setLayout(operation_layout)
        content_layout.addWidget(operation_group)
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
        
    def create_naming_rules_tab(self) -> QWidget:
        """创建命名规则标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # 模板变量
        variables_group = QGroupBox("📝 模板变量说明")
        variables_layout = QVBoxLayout()
        
        variables_text = QTextEdit()
        variables_text.setReadOnly(True)
        variables_text.setPlainText("""
基本变量：
{title} - 影视标题
{year} - 发行年份
{season} - 季数（电视剧）
{episode} - 集数（电视剧）
{ext} - 文件扩展名

质量变量：
{quality} - 视频质量（1080p, 720p等）
{resolution} - 分辨率
{codec} - 视频编码
{bitrate} - 比特率

音频变量：
{audio} - 音频信息
{audio_codec} - 音频编码
{audio_channels} - 声道数
{audio_language} - 音频语言

字幕变量：
{subtitle} - 字幕信息
{subtitle_language} - 字幕语言
{subtitle_format} - 字幕格式

其他变量：
{group} - 发布组
{source} - 视频源
{edition} - 版本信息
{comment} - 注释信息
        """.strip())
        
        variables_layout.addWidget(variables_text)
        variables_group.setLayout(variables_layout)
        content_layout.addWidget(variables_group)
        
        # 命名示例
        examples_group = QGroupBox("💡 命名示例")
        examples_layout = QVBoxLayout()
        
        examples_text = QTextEdit()
        examples_text.setReadOnly(True)
        examples_text.setPlainText("""
电影命名示例：
原文件：Avengers.Endgame.2019.1080p.BluRay.x264.mkv
模板：{title} ({year}){ext}
结果：复仇者联盟4：终局之战 (2019).mkv

电视剧命名示例：
原文件：Game.of.Thrones.S01E01.1080p.BluRay.x264.mkv
模板：{title}.S{season:02d}.E{episode:02d}{ext}
结果：权力的游戏.S01.E01.mkv

带质量信息：
模板：{title} ({year}) [{quality}]{ext}
结果：复仇者联盟4：终局之战 (2019) [1080p].mkv

带音频信息：
模板：{title}.S{season:02d}.E{episode:02d} [{audio}]{ext}
结果：权力的游戏.S01.E01 [DTS-HD.MA.5.1].mkv

完整模板：
模板：{title} ({year}) [{quality}] [{audio}] [{subtitle}]{ext}
结果：复仇者联盟4：终局之战 (2019) [1080p] [DTS-HD.MA.5.1] [中英字幕].mkv
        """.strip())
        
        examples_layout.addWidget(examples_text)
        examples_group.setLayout(examples_layout)
        content_layout.addWidget(examples_group)
        
        # 自定义规则
        custom_group = QGroupBox("🔧 自定义规则")
        custom_layout = QVBoxLayout()
        
        custom_text = QTextEdit()
        custom_text.setReadOnly(True)
        custom_text.setPlainText("""
高级模板语法：
• 格式化数字：{season:02d} 显示为 01, 02, 03...
• 条件显示：{quality?[{}]} 只有存在质量信息时才显示
• 默认值：{title|未知标题} 如果标题为空则显示默认值
• 大小写：{title:upper} 转换为大写
• 截取：{title:10} 截取前10个字符

正则表达式：
• 支持正则表达式匹配
• 可提取文件名中的特定信息
• 支持分组和替换

自定义函数：
• 支持自定义Python函数
• 可进行复杂的信息处理
• 支持外部API调用
        """.strip())
        
        custom_layout.addWidget(custom_text)
        custom_group.setLayout(custom_layout)
        content_layout.addWidget(custom_group)
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
        
    def create_faq_tab(self) -> QWidget:
        """创建常见问题标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # 常见问题
        faq_group = QGroupBox("❓ 常见问题")
        faq_layout = QVBoxLayout()
        
        faq_text = QTextEdit()
        faq_text.setReadOnly(True)
        faq_text.setPlainText("""
Q: 为什么扫描不到我的文件？
A: 请检查：
   • 文件扩展名是否在支持列表中
   • 文件是否被其他程序占用
   • 文件夹路径是否正确
   • 是否有足够的访问权限

Q: 识别结果不准确怎么办？
A: 可以：
   • 手动编辑识别结果
   • 调整命名模板
   • 使用更详细的文件名
   • 检查文件命名规范

Q: 重命名失败怎么办？
A: 可能原因：
   • 文件被其他程序占用
   • 磁盘空间不足
   • 权限不足
   • 文件名包含特殊字符

Q: 如何撤销重命名操作？
A: 方法：
   • 使用撤销功能（如果启用）
   • 从备份文件夹恢复
   • 使用系统还原点
   • 重新下载文件

Q: 支持哪些文件格式？
A: 支持格式：
   • 视频：MP4, MKV, AVI, MOV, WMV, FLV, WEBM
   • 字幕：SRT, ASS, SSA, SUB
   • 音频：AAC, AC3, DTS, FLAC, MP3

Q: 如何提高识别准确率？
A: 建议：
   • 使用标准的文件命名格式
   • 包含年份和季数信息
   • 避免使用特殊字符
   • 保持文件名简洁明了

Q: 程序运行缓慢怎么办？
A: 优化方法：
   • 减少扫描深度
   • 降低线程数量
   • 关闭不必要的功能
   • 增加系统内存

Q: 如何备份设置？
A: 备份方法：
   • 使用设置导出功能
   • 备份配置文件
   • 保存自定义模板
   • 记录重要设置
        """.strip())
        
        faq_layout.addWidget(faq_text)
        faq_group.setLayout(faq_layout)
        content_layout.addWidget(faq_group)
        
        # 故障排除
        troubleshooting_group = QGroupBox("🔧 故障排除")
        troubleshooting_layout = QVBoxLayout()
        
        troubleshooting_text = QTextEdit()
        troubleshooting_text.setReadOnly(True)
        troubleshooting_text.setPlainText("""
程序无法启动：
• 检查Python版本（需要3.7+）
• 检查PyQt5是否正确安装
• 检查依赖模块是否完整
• 查看错误日志

扫描卡住：
• 检查文件夹大小
• 检查文件数量
• 降低扫描深度
• 减少线程数量

识别失败：
• 检查文件名格式
• 检查网络连接
• 更新识别数据库
• 手动输入信息

重命名失败：
• 检查文件权限
• 检查磁盘空间
• 关闭占用程序
• 使用管理员权限

性能问题：
• 关闭其他程序
• 增加系统内存
• 使用SSD硬盘
• 优化设置参数

崩溃问题：
• 更新到最新版本
• 检查系统兼容性
• 重新安装程序
• 联系技术支持
        """.strip())
        
        troubleshooting_layout.addWidget(troubleshooting_text)
        troubleshooting_group.setLayout(troubleshooting_layout)
        content_layout.addWidget(troubleshooting_group)
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
        
    def create_about_tab(self) -> QWidget:
        """创建关于标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 程序信息
        info_group = QGroupBox("ℹ️ 程序信息")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setPlainText("""
影视文件重命名工具 v1.3

开发语言：Python 3.7+
GUI框架：PyQt5
支持平台：Windows, macOS, Linux

主要功能：
• 智能影视文件识别
• 批量文件重命名
• 多种命名模板
• 预览和撤销功能
• 安全备份机制
• 多语言支持

技术特点：
• 模块化设计
• 多线程处理
• 缓存优化
• 错误恢复
• 日志记录
• 配置管理

开发团队：
• 主要开发者：[开发者姓名]
• 界面设计：[设计师姓名]
• 测试支持：[测试人员姓名]

版权信息：
• 版权所有 © 2024
• 开源协议：MIT License
• 项目地址：[项目地址]
        """.strip())
        
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 更新日志
        changelog_group = QGroupBox("📝 更新日志")
        changelog_layout = QVBoxLayout()
        
        changelog_text = QTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setPlainText("""
v1.3 (2024-01-XX)
• 新增深色主题支持
• 优化文件识别算法
• 改进用户界面设计
• 增加批量预览功能
• 修复已知问题

v1.2 (2024-01-XX)
• 新增设置对话框
• 增加帮助系统
• 优化性能表现
• 改进错误处理
• 增加日志功能

v1.1 (2024-01-XX)
• 新增撤销功能
• 增加备份机制
• 优化扫描速度
• 改进识别准确率
• 修复界面问题

v1.0 (2024-01-XX)
• 初始版本发布
• 基本重命名功能
• 文件识别支持
• 简单用户界面
• 基础设置选项
        """.strip())
        
        changelog_layout.addWidget(changelog_text)
        changelog_group.setLayout(changelog_layout)
        layout.addWidget(changelog_group)
        
        # 联系方式
        contact_group = QGroupBox("📞 联系方式")
        contact_layout = QVBoxLayout()
        
        contact_text = QTextEdit()
        contact_text.setReadOnly(True)
        contact_text.setMaximumHeight(150)
        contact_text.setPlainText("""
技术支持：
• 邮箱：[support@example.com]
• 网站：[https://example.com]
• 论坛：[https://forum.example.com]
• GitHub：[https://github.com/example]

反馈建议：
• 问题报告：[https://github.com/example/issues]
• 功能建议：[https://github.com/example/discussions]
• 代码贡献：[https://github.com/example/pulls]

社区支持：
• QQ群：[群号]
• 微信群：[二维码]
• Discord：[邀请链接]
• Telegram：[频道链接]

文档资源：
• 用户手册：[文档链接]
• API文档：[API链接]
• 开发指南：[开发文档]
• 常见问题：[FAQ链接]
        """.strip())
        
        contact_layout.addWidget(contact_text)
        contact_group.setLayout(contact_layout)
        layout.addWidget(contact_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget 