#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前自动验证脚本。

检查内容：
1. core/version.py 与 CHANGELOG.md 最新版本一致（--release 模式严格校验，要求顶部为正式版本号）
2. CHANGELOG.md 包含全部六个变更分类（新增/改进/废弃/移除/修复/安全）
3. （可选 --check-git）工作区无未提交改动
4. （可选 --run-tests）全功能测试通过

用法：
    python3 scripts/check_release.py                # 开发期静态检查（允许 Unreleased）
    python3 scripts/check_release.py --release      # 发布前严格校验（顶部须为正式版本号）
    python3 scripts/check_release.py --check-git    # 含 git 状态检查
    python3 scripts/check_release.py --run-tests    # 含测试回归
退出码：0 = 全部通过；1 = 存在失败项
"""
import argparse
import os
import pathlib
import re
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent   # 电影电视剧重命名单文件版/
REPO_ROOT = PROJECT_ROOT.parent                                  # AI编程/（仓库根）
REQUIRED_CATEGORIES = ["新增", "改进", "废弃", "移除", "修复", "安全"]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def load_version() -> str:
    """从 core/version.py 读取 __version__。"""
    ns = {}
    exec((PROJECT_ROOT / "core" / "version.py").read_text(encoding="utf-8"), ns)
    version = ns.get("__version__", "")
    if not SEMVER_RE.match(version):
        raise ValueError(f"core/version.py 中 __version__ 非法: {version!r}（应为 SemVer x.y.z）")
    return version


def load_changelog_head(changelog: pathlib.Path) -> tuple[str, str, set[str]]:
    """解析 CHANGELOG.md 顶部最新版本块，返回 (版本, 日期, 分类集合)。"""
    text = changelog.read_text(encoding="utf-8")
    m = re.search(r"^## \[(Unreleased|\d+\.\d+\.\d+)\] ?-? ?(\S*)$", text, re.M)
    if not m:
        raise ValueError(f"{changelog} 缺少版本区块（## [x.y.z] - 日期）")
    version = m.group(1)
    if version != "Unreleased" and not SEMVER_RE.match(version):
        raise ValueError(f"CHANGELOG 版本非法: {version!r}")
    date = m.group(2)
    # 该区块内出现的分类标题
    block_end = text.find("\n## [", m.end())
    block = text[m.start():block_end if block_end != -1 else len(text)]
    categories = set(re.findall(r"^### (.+)$", block, re.M))
    return version, date, categories


def check_git_clean(project_root: pathlib.Path) -> list[str]:
    """检查 git 工作区状态。"""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return [f"git status 执行失败: {r.stderr.strip()}"]
        changed = [line for line in r.stdout.splitlines() if line.strip()]
        if changed:
            return [f"工作区有 {len(changed)} 个未提交改动（先 commit 再发布）"]
        return []
    except FileNotFoundError:
        return ["未找到 git 命令，跳过 git 检查"]


def run_tests(project_root: pathlib.Path) -> list[str]:
    """运行全功能测试。"""
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_root)
        env["QT_QPA_PLATFORM"] = "offscreen"  # 无头环境运行 PyQt 测试
        r = subprocess.run(
            [sys.executable, str(project_root / "tests" / "test_all_features.py")],
            capture_output=True, text=True, timeout=300, env=env,
            cwd=str(project_root),
        )
        last = [ln for ln in r.stdout.splitlines() if "测试结果" in ln]
        if r.returncode != 0:
            return [f"全功能测试失败（退出码 {r.returncode}）: {last[-1] if last else r.stdout[-300:]}" ]
        return []
    except subprocess.TimeoutExpired:
        return ["全功能测试超时（>300s）"]


def main() -> int:
    parser = argparse.ArgumentParser(description="发布前自动验证")
    parser.add_argument("--release", action="store_true",
                        help="发布模式：要求 CHANGELOG 顶部为正式版本号且与 version.py 一致")
    parser.add_argument("--check-git", action="store_true", help="检查 git 工作区无未提交改动")
    parser.add_argument("--run-tests", action="store_true", help="运行全功能测试")
    args = parser.parse_args()

    failures: list[str] = []
    print("=" * 56)
    print("发布前自动验证")
    print("=" * 56)

    # 1. 版本一致性
    try:
        version = load_version()
        print(f"[版本] core/version.py  __version__ = {version}  ✓")
    except (ValueError, OSError) as e:
        failures.append(str(e))
        print(f"[版本] ✗ {e}")
        version = None

    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        failures.append(f"未找到 {changelog.relative_to(REPO_ROOT)}")
        print(f"[Changelog] ✗ 文件缺失")
    else:
        try:
            cl_version, cl_date, categories = load_changelog_head(changelog)
            print(f"[Changelog] 最新区块 [{cl_version}] {cl_date}  ✓")
            if args.release and cl_version == "Unreleased":
                failures.append(f"CHANGELOG 顶部是 [Unreleased]，发布前应改为具体版本 [{version}]")
                print(f"[Changelog] ✗ 顶部为 Unreleased，尚未整理为正式版本")
            elif args.release and version and cl_version != version:
                failures.append(f"版本不一致: version.py={version} vs CHANGELOG={cl_version}")
                print(f"[Changelog] ✗ 版本不一致: version.py={version} vs CHANGELOG={cl_version}")
            else:
                print(f"[Changelog] ✓ 与 version.py 一致" if version else "[Changelog] ✓")
            # 分类合法性（Keep a Changelog：只要求出现的分类属于六类之一，不要求每版本齐全）
            invalid = [c for c in categories if c not in REQUIRED_CATEGORIES]
            if invalid:
                failures.append(f"CHANGELOG 最新区块含非法分类: {', '.join(invalid)}（合法: {'/'.join(REQUIRED_CATEGORIES)}）")
                print(f"[Changelog] ✗ 非法分类: {', '.join(invalid)}")
            else:
                print(f"[Changelog] ✓ 变更分类合法（{len(categories)} 个分类）")
        except ValueError as e:
            failures.append(str(e))
            print(f"[Changelog] ✗ {e}")

    # 2. git 状态
    if args.check_git:
        git_issues = check_git_clean(REPO_ROOT)
        if git_issues:
            failures.extend(git_issues)
            print(f"[Git] ✗ {git_issues[0]}")
        else:
            print("[Git] ✓ 工作区干净")

    # 3. 测试
    if args.run_tests:
        test_issues = run_tests(PROJECT_ROOT)
        if test_issues:
            failures.extend(test_issues)
            print(f"[测试] ✗ {test_issues[0]}")
        else:
            print("[测试] ✓ 全功能测试通过")

    print("=" * 56)
    if failures:
        print(f"结果: FAIL（{len(failures)} 项需处理）")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("结果: PASS ✓ 可以发布")
    return 0


if __name__ == "__main__":
    sys.exit(main())
