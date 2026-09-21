#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析引擎参数化用例测试（表驱动）。

覆盖：电影（年份/中文/无年份）、电视剧（SxxExx/中文季集/纯数字集/EP 格式）、
特辑关键词、边界（无法识别/纯集数文件）。

用法：python3 tests/test_pattern_recognizer.py（退出码 0 = 全部通过）
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# 用例表：(文件名, 期望 type, 期望 title, 期望 season, 期望 episode, 期望 year)
CASES = [
    # 电影
    ("Avengers.Endgame.2019.1080p.BluRay.x264.mkv", "movie", "Avengers Endgame", None, None, "2019"),
    ("The.Matrix.1999.4K.HDR.BluRay.x265.mkv", "movie", "The Matrix", None, None, "1999"),
    ("Inception.2010.mkv", "movie", "Inception", None, None, "2010"),
    ("阿凡达.2009.mp4", "movie", "阿凡达", None, None, "2009"),
    ("流浪地球2.2023.4K.HDR.中字.mkv", "movie", "流浪地球2", None, None, "2023"),
    ("让子弹飞.2010.1080p.mkv", "movie", "让子弹飞", None, None, "2010"),
    # 电视剧
    ("Game.of.Thrones.S08E03.1080p.WEB-DL.mkv", "tv", "Game of Thrones", 8, 3, None),
    ("Breaking.Bad.S05E16.720p.WEB-DL.x264.mp4", "tv", "Breaking Bad", 5, 16, None),
    ("Friends.S01E01.720p.mkv", "tv", "Friends", 1, 1, None),
    ("权力的游戏.S01E01.mp4", "tv", "权力的游戏", 1, 1, None),
    ("琅琊榜.第1季.第2集.1080p.mp4", "tv", "琅琊榜", 1, 2, None),
    ("Stranger.Things.EP04.1080p.mkv", "tv", "Stranger Things", None, 4, None),
    ("05.mkv", "tv", "05", None, 5, None),
    # 特辑关键词（当前实现：含年份时优先判 movie）
    ("One.Piece.Special.2020.1080p.mkv", "movie", "One Piece Special", None, None, "2020"),
    # 边界
    ("Unknown_Title_abc.mp4", "movie", "Unknown Title abc", None, None, None),
]


def test_pattern_cases() -> bool:
    """表驱动：逐个用例断言关键解析字段。"""
    logger.info("🔍 测试解析引擎（%d 个参数化用例）...", len(CASES))
    from core.pattern_recognizer import PatternRecognizer

    recognizer = PatternRecognizer()
    failed = 0
    for filename, exp_type, exp_title, exp_season, exp_episode, exp_year in CASES:
        result = recognizer.analyze_filename(filename)
        checks = [
            ("type", result.get("type"), exp_type),
            ("title", result.get("title"), exp_title),
            ("season", result.get("season"), exp_season),
            ("episode", result.get("episode"), exp_episode),
            ("year", result.get("year"), exp_year),
        ]
        errors = [f"{k}={actual!r}(期望 {expected!r})" for k, actual, expected in checks
                  if actual != expected]
        if errors:
            failed += 1
            logger.error("❌ %s: %s", filename, ", ".join(errors))
        else:
            logger.info("✅ %s -> %s | %s", filename, result.get("type"), result.get("title"))

    if failed:
        logger.error("❌ 解析用例失败 %d/%d", failed, len(CASES))
        return False
    logger.info("✅ 解析引擎 %d/%d 用例通过", len(CASES), len(CASES))
    return True


def main() -> int:
    results = [test_pattern_cases()]
    passed = sum(1 for r in results if r)
    logger.info("📊 测试结果: %d/%d 通过", passed, len(results))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
