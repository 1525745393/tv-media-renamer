#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键发布脚本：简化发布流程为一条命令。

流程（自动化）：
1. 读取 core/version.py 的 __version__（SemVer，唯一来源）
2. 运行 scripts/check_release.py --release --check-git（+可选 --run-tests）自动验证
3. 更新 CHANGELOG.md：Unreleased → 正式版本（自动补日期），并在顶部新建空 Unreleased
4. git commit + 打 tag（v<版本>）
5. git push + git push --tags（触发 GitHub Actions 自动构建发布）

用法：
    python3 scripts/release.py                    # 预览模式（只打印将执行的操作）
    python3 scripts/release.py --execute          # 实际执行
    python3 scripts/release.py --version 1.4.0    # 指定版本号（默认读 version.py）
    python3 scripts/release.py --skip-tests       # 跳过测试回归（仅静态校验）

环境变量：
    GH_TOKEN    可选。设置后用于 push（内联凭证助手）；否则使用 git 默认凭据。
"""
import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def run(cmd: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          check=check, timeout=300)


def git_push_env() -> list[str]:
    """构造带内联凭证的 git 环境（若提供了 GH_TOKEN）。"""
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        return []
    return [
        "-c",
        "credential.helper=!f() { echo \"username=x-access-token\"; echo \"password=$GH_TOKEN\"; }; f",
    ]


def bump_changelog(changelog: pathlib.Path, version: str) -> bool:
    """把顶部 [Unreleased] 改为 [version] - 日期，并在顶部新建空 Unreleased 区块。

    返回 True 表示执行了替换；False 表示无需改动（顶部已是该版本）。
    """
    text = changelog.read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()
    new_block = "## [Unreleased]\n\n### 新增\n\n### 改进\n\n### 修复\n\n"
    if f"## [{version}]" in text:
        return False  # 顶部已是该版本，无需重复
    if not re.search(r"^## \[Unreleased\]", text, re.M):
        raise SystemExit("✗ CHANGELOG.md 缺少顶部 [Unreleased] 区块，无法自动发布")
    updated = re.sub(
        r"^## \[Unreleased\](\s*\n)",
        lambda m: new_block + f"## [{version}] - {today}" + m.group(1),
        text,
        count=1,
        flags=re.M,
    )
    changelog.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="一键发布")
    parser.add_argument("--execute", action="store_true", help="实际执行（默认仅预览）")
    parser.add_argument("--version", default="", help="版本号（默认读 version.py）")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试回归")
    args = parser.parse_args()

    print("=" * 56)
    print("一键发布流程")
    print("=" * 56)

    # 1. 读取版本
    ns: dict[str, object] = {}
    exec((PROJECT_ROOT / "core" / "version.py").read_text(encoding="utf-8"), ns)  # noqa: S102
    version = ns.get("__version__", "")
    if args.version:
        version = args.version
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        raise SystemExit(f"✗ 版本号非法: {version!r}（应为 SemVer x.y.z）")
    print(f"[1/5] 版本: {version}")

    # 2. 自动验证
    test_flag = [] if args.skip_tests else ["--run-tests"]
    check = run([sys.executable, "scripts/check_release.py", "--release", "--check-git", *test_flag],
                PROJECT_ROOT, check=False)
    print(check.stdout)
    if check.returncode != 0:
        raise SystemExit("✗ 发布前验证失败，已中止（请修复后重试）")
    print("[2/5] ✓ 发布前验证通过")

    # 3. CHANGELOG 升级
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        raise SystemExit(f"✗ 未找到 {changelog}")
    changed = bump_changelog(changelog, version)
    print(f"[3/5] ✓ CHANGELOG 已更新为 [{version}]（{'重建 Unreleased' if changed else '已是该版本'}）")

    if not args.execute:
        print("\n预览模式（未做任何改动）。确认后加 --execute 实际执行：")
        print(f"  python3 scripts/release.py --execute --version {version}")
        return 0

    # 4. 提交 + 打 tag
    git_extra = git_push_env()
    run(["git", "add", "-A"], REPO_ROOT)
    run(["git", "commit", "-m", f"release: v{version}"], REPO_ROOT)
    run(["git", "tag", f"v{version}"], REPO_ROOT)
    print("[4/5] ✓ 已提交并打 tag v" + version)

    # 5. 推送
    run(["git", *git_extra, "push", "origin", "main"], REPO_ROOT)
    run(["git", *git_extra, "push", "origin", "tag", f"v{version}"], REPO_ROOT)
    print("[5/5] ✓ 已推送（GitHub Actions 将自动构建并发布 Release）")

    print("=" * 56)
    print("发布已触发。可在 Actions 页查看构建进度：")
    print("  https://github.com/1525745393/tv-media-renamer/actions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
