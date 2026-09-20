#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""性能基准测试脚本：对解析引擎核心路径做标准用例计时。

用法：
    python3 scripts/benchmark.py                # 运行并打印报告
    python3 scripts/benchmark.py --report       # 输出 JSON 报告（末行），供 check_release --benchmark 解析
    python3 scripts/benchmark.py --compare      # 与 benchmark_results.json 基准值对比

每个用例：预热 3 次 + 计时 N 次（默认 50），取中位数（ms）。
"""
import argparse
import json
import pathlib
import statistics
import sys
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULT_FILE = PROJECT_ROOT / "benchmark_results.json"
ITERATIONS = 50

# 标准用例：覆盖电影 / 电视剧 / 中文季集 / 特辑 / 边界
CASES = [
    ("电影-年份", "Avengers.Endgame.2019.1080p.BluRay.x264-GROUP.mkv"),
    ("电影-中文", "流浪地球2.2023.4K.HDR.中字.mkv"),
    ("电影-纯中文", "让子弹飞.2010.1080p.mkv"),
    ("电视剧-SxxExx", "Game.of.Thrones.S08E03.1080p.WEB-DL.DDP5.1.mkv"),
    ("电视剧-中文季集", "琅琊榜.第1季.第2集.1080p.mp4"),
    ("电视剧-纯数字集", "权力的游戏.S01E01.mp4"),
    ("特辑", "One.Piece.Special.2020.1080p.mkv"),
    ("边界-无年份", "Unknown_Title_abc.mp4"),
    ("边界-纯集数文件", "05.mkv"),
]


def load_benchmark() -> dict:
    """加载历史基准值。"""
    if RESULT_FILE.exists():
        try:
            return json.loads(RESULT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def run_case(analyze, name: str, filename: str, n: int = ITERATIONS) -> float:
    """运行单个用例，预热后返回中位数（ms）。"""
    folder = "benchmark"
    for _ in range(3):  # 预热
        analyze(filename, folder)
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        analyze(filename, folder)
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


def main() -> int:
    parser = argparse.ArgumentParser(description="性能基准测试")
    parser.add_argument("--report", action="store_true", help="输出 JSON 报告（末行）")
    parser.add_argument("--compare", action="store_true", help="与历史基准对比")
    parser.add_argument("--iterations", type=int, default=ITERATIONS, help="每用例计时次数")
    args = parser.parse_args()

    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from core.pattern_recognizer import PatternRecognizer
    except ImportError:
        print(f"✗ 无法导入 PatternRecognizer（PYTHONPATH={PROJECT_ROOT}）", file=sys.stderr)
        return 1

    try:
        from core.version import __version__
    except ImportError:
        __version__ = "unknown"

    recognize = PatternRecognizer()
    analyze = recognize.analyze_filename

    cases: dict[str, float] = {}
    print(f"性能基准测试（Python {sys.version.split()[0]}，每用例 {args.iterations} 次取中位数）")
    print("-" * 60)
    for name, filename in CASES:
        median = run_case(analyze, name, filename, args.iterations)
        cases[name] = round(median, 3)
        print(f"  {name:<12} {median:>8.3f} ms  ({filename})")

    # 对比历史基准
    if args.compare:
        old = load_benchmark().get("cases", {})
        if old:
            print("-" * 60)
            print("与历史基准对比（当前 / 历史 / 变化%）")
            for name, cur in sorted(cases.items()):
                base = old.get(name)
                if base:
                    diff = (cur - base) / base * 100
                    flag = "⚠ 变慢" if diff > 10 else ("✓ 变快" if diff < -10 else "  ~")
                    print(f"  {name:<12} {cur:>8.3f} / {base:>8.3f} ms   {diff:>+6.1f}%  {flag}")

    # 保存本次结果
    record = {
        "version": __version__,
        "python": sys.version.split()[0],
        "iterations": args.iterations,
        "cases": cases,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    RESULT_FILE.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.report:
        print(json.dumps(record, ensure_ascii=False))
    else:
        print(f"\n结果已保存: {RESULT_FILE.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
