@echo off
rem ============================================
rem  影视重命名工具 - 仓库一键同步脚本 (Windows)
rem  用法: 双击 git-sync.bat
rem  功能: git add → commit → push
rem ============================================
cd /d "%~dp0"

echo [1/3] 暂存全部变更...
git add -A

git diff --cached --quiet
if %errorlevel%==0 (
    echo 没有需要提交的变更
) else (
    git commit -m "同步 %date% %time%"
    echo 已提交
)

echo [2/3] 检查远程仓库...
git remote -v | findstr push >nul
if %errorlevel%==0 (
    echo [3/3] 推送远程...
    git push && echo 已推送到远程仓库
) else (
    echo 未配置远程仓库，已完成本地提交
    echo 首次推送请执行:
    echo   git remote add origin ^<仓库地址^>
    echo   git push -u origin main
)

pause
