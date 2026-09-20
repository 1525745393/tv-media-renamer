#!/usr/bin/env bash
# ============================================
#  影视重命名工具 - 仓库一键同步脚本 (Linux/macOS)
#  用法: ./git-sync.sh
#  功能: git add → commit → push
# ============================================
set -e
cd "$(dirname "$0")"

echo "🔍 暂存全部变更..."
git add -A

if git diff --cached --quiet; then
    echo "ℹ️  没有需要提交的变更"
else
    git commit -m "同步 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ 已提交"
fi

echo "🚀 推送远程..."
if git remote -v | grep -q push; then
    git push && echo "✅ 已推送到远程仓库"
else
    echo "⚠️  未配置远程仓库，已完成本地提交"
    echo "   首次推送请执行:"
    echo "     git remote add origin <仓库地址>"
    echo "     git push -u origin main"
fi
