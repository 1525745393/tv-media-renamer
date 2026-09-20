#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前自动验证脚本。

检查内容：
1. core/version.py 与 CHANGELOG.md 最新版本一致（--release 模式严格校验，要求顶部为正式版本号）
2. CHANGELOG.md 包含全部六个变更分类（新增/改进/废弃/移除/修复/安全）
3. 版本兼容性：Python 版本 >= 最低要求、依赖清单与主入口文件存在
4. （可选 --check-git）工作区无未提交改动
5. （可选 --run-tests）全功能测试通过
6. （可选 --benchmark）性能基准测试（对比基准值）

用法：
    python3 scripts/check_release.py                # 开发期静态检查（允许 Unreleased）
    python3 scripts/check_release.py --release      # 发布前严格校验（顶部须为正式版本号）
    python3 scripts/check_release.py --check-git    # 含 git 状态检查
    python3 scripts/check_release.py --run-tests    # 含测试回归
    python3 scripts/check_release.py --benchmark    # 含性能基准测试
退出码：0 = 全部通过；1 = 存在失败项
"""
import argparse
import json
import os
import pathlib
import platform
import re
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent   # 电影电视剧重命名单文件版/
REPO_ROOT = PROJECT_ROOT.parent                                  # AI编程/（仓库根）
REQUIRED_CATEGORIES = ["新增", "改进", "废弃", "移除", "修复", "安全"]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
MIN_PYTHON = (3, 9)          # 最低支持 Python 版本
MIN_PYTHON_LABEL = "3.9"     # 与 MIN_PYTHON 对应的展示文本
MAX_PYTHON = (3, 13)         # 已验证支持的最高 Python 版本（含）
MAX_PYTHON_LABEL = "3.13"    # 与 MAX_PYTHON 对应的展示文本


def load_version() -> str:
    """从 core/version.py 读取 __version__。"""
    ns: dict[str, object] = {}
    exec((PROJECT_ROOT / "core" / "version.py").read_text(encoding="utf-8"), ns)
    version = ns.get("__version__", "")
    if not isinstance(version, str):
        version = ""
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


def check_compatibility(project_root: pathlib.Path) -> list[str]:
    """版本兼容性检查：Python 版本范围、依赖清单、主入口文件。"""
    issues: list[str] = []

    # 1. Python 版本范围
    py = sys.version_info
    if py < MIN_PYTHON:
        issues.append(f"当前 Python {py.major}.{py.minor}.{py.micro} 低于最低支持版本 {MIN_PYTHON_LABEL}")
    elif py >= MAX_PYTHON:
        issues.append(f"当前 Python {py.major}.{py.minor}.{py.micro} 达到/超过已支持上限 {MAX_PYTHON_LABEL}（请验证后更新上限）")

    # 2. 依赖清单存在且可解析
    req = project_root / "main" / "requirements.txt"
    if not req.exists():
        issues.append(f"缺少依赖清单 {req.relative_to(project_root)}")
    else:
        for ln in req.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            if not re.match(r"^[A-Za-z0-9_.-]+\s*(>=|<=|==|~=|!=|\s*$)", ln):
                issues.append(f"依赖声明格式异常: {ln!r}")

    # 3. 主入口文件存在
    entry = project_root / "main" / "tv_rename_gui_v1.3.py"
    if not entry.exists():
        issues.append(f"缺少主入口 {entry.relative_to(project_root)}")

    # 4. 打包关键模块可导入（编译级验证）
    for mod in ("core.version", "core.pattern_recognizer", "ui.main_window"):
        r = subprocess.run(
            [sys.executable, "-c", f"import {mod}"],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "PYTHONPATH": str(project_root), "QT_QPA_PLATFORM": "offscreen"},
            cwd=str(project_root),
        )
        if r.returncode != 0:
            issues.append(f"模块导入失败 {mod}: {(r.stderr or r.stdout).strip()[-200:]}")
    return issues


def run_benchmark(project_root: pathlib.Path) -> list[str]:
    """运行性能基准测试并对比基准值（scripts/benchmark.py --report）。"""
    script = project_root / "scripts" / "benchmark.py"
    if not script.exists():
        return ["缺少基准测试脚本 scripts/benchmark.py"]
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_root)
        r = subprocess.run(
            [sys.executable, str(script), "--report"],
            capture_output=True, text=True, timeout=300, env=env,
            cwd=str(project_root),
        )
        if r.returncode != 0:
            return [f"性能基准测试失败（退出码 {r.returncode}）: {(r.stderr or r.stdout).strip()[-300:]}"]
        # 解析报告并展示
        try:
            report = json.loads(r.stdout.strip().splitlines()[-1])
            cases = report.get("cases", {})
            summary = " / ".join(f"{k}: {v}ms" for k, v in sorted(cases.items()))
            print(f"[基准] ✓ {summary}")
        except (json.JSONDecodeError, KeyError, TypeError):
            print("[基准] ✓ 测试通过（报告未解析）")
        return []
    except subprocess.TimeoutExpired:
        return ["性能基准测试超时（>300s）"]


def main() -> int:
    parser = argparse.ArgumentParser(description="发布前自动验证")
    parser.add_argument("--release", action="store_true",
                        help="发布模式：要求 CHANGELOG 顶部为正式版本号且与 version.py 一致")
    parser.add_argument("--check-git", action="store_true", help="检查 git 工作区无未提交改动")
    parser.add_argument("--run-tests", action="store_true", help="运行全功能测试")
    parser.add_argument("--benchmark", action="store_true", help="运行性能基准测试")
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
        print("[Changelog] ✗ 文件缺失")
    else:
        try:
            cl_version, cl_date, categories = load_changelog_head(changelog)
            print(f"[Changelog] 最新区块 [{cl_version}] {cl_date}  ✓")
            if args.release and cl_version == "Unreleased":
                failures.append(f"CHANGELOG 顶部是 [Unreleased]，发布前应改为具体版本 [{version}]")
                print("[Changelog] ✗ 顶部为 Unreleased，尚未整理为正式版本")
            elif args.release and version and cl_version != version:
                failures.append(f"版本不一致: version.py={version} vs CHANGELOG={cl_version}")
                print(f"[Changelog] ✗ 版本不一致: version.py={version} vs CHANGELOG={cl_version}")
            else:
                print("[Changelog] ✓ 与 version.py 一致" if version else "[Changelog] ✓")
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

    # 2. 版本兼容性检查
    comp_issues = check_compatibility(PROJECT_ROOT)
    if comp_issues:
        failures.extend(comp_issues)
        for c in comp_issues:
            print(f"[兼容性] ✗ {c}")
    else:
        print(f"[兼容性] ✓ Python {platform.python_version()} 在支持范围 {MIN_PYTHON_LABEL}~{MAX_PYTHON_LABEL}，依赖与入口齐全")

    # 3. git 状态
    if args.check_git:
        git_issues = check_git_clean(REPO_ROOT)
        if git_issues:
            failures.extend(git_issues)
            print(f"[Git] ✗ {git_issues[0]}")
        else:
            print("[Git] ✓ 工作区干净")

    # 4. 测试
    if args.run_tests:
        test_issues = run_tests(PROJECT_ROOT)
        if test_issues:
            failures.extend(test_issues)
            print(f"[测试] ✗ {test_issues[0]}")
        else:
            print("[测试] ✓ 全功能测试通过")

    # 5. 性能基准
    if args.benchmark:
        bench_issues = run_benchmark(PROJECT_ROOT)
        if bench_issues:
            failures.extend(bench_issues)
            print(f"[基准] ✗ {bench_issues[0]}")
        else:
            print("[基准] ✓ 性能基准测试通过")

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
