#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""影视文件智能重命名工具 - NAS API 服务（移动端后端）。

把桌面版解析引擎包装为轻量 HTTP 服务，供手机端（Flutter）调用：
- 解析文件名（复用 core.pattern_recognizer / modules.enhanced_analyzer）
- 扫描目录媒体文件
- 重命名预览与执行（dry_run 默认开启；执行前自动备份）

部署：
    export API_TOKEN=你的随机token          # 必填，鉴权用
    export ALLOWED_ROOT=/volume1/media      # 可选，允许访问的根目录（默认 /）
    cd 电影电视剧重命名单文件版
    uvicorn server.app:app --host 0.0.0.0 --port 8123

文档：启动后访问 http://<NAS-IP>:8123/docs
"""
import logging
import os
import pathlib
import secrets
import shutil
from typing import Any, Dict, List

from fastapi import FastAPI, Header, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 项目根（server/ 的上级）：保证能 import core/ modules/
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT))

from core.version import __version__, APP_NAME  # noqa: E402
from core.pattern_recognizer import PatternRecognizer  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("tv-renamer-api")

# ============ 配置 ============
API_TOKEN = os.environ.get("API_TOKEN", "").strip()
if not API_TOKEN:
    API_TOKEN = secrets.token_urlsafe(24)
    logger.warning("未设置 API_TOKEN，已自动生成（仅本次运行有效）: %s", API_TOKEN)
ALLOWED_ROOT = pathlib.Path(os.environ.get("ALLOWED_ROOT", "/")).resolve()

MEDIA_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".mpg", ".mpeg", ".ts", ".m2ts", ".rmvb", ".iso",
}
SUBTITLE_EXTS = {".srt", ".ass", ".ssa", ".sub", ".idx"}

app = FastAPI(title=f"{APP_NAME} API", version=__version__,
              description="NAS 端影视文件重命名服务（移动端控制）")

# 引擎实例（无 GUI 依赖；统一使用 PatternRecognizer——15 用例参数化验证的解析核心）
_recognizer = PatternRecognizer()


def _sanitize(value: Any) -> Any:
    """递归清理不可 JSON 序列化的对象（如 re.Match）。"""
    import re as _re
    if isinstance(value, _re.Match):
        return str(value.group(0)) if value.group(0) else None
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


def analyze_one(filename: str, folder: str = "") -> Dict[str, Any]:
    """解析单个文件名（复用 PatternRecognizer，含建议名）。"""
    result = _recognizer.analyze_filename(filename, folder)
    result = _sanitize(result)
    result["suggested_name"] = suggest_name(result, pathlib.Path(filename).suffix)
    return result


# ============ 鉴权 ============
def require_token(authorization: str = Header(default="")) -> None:
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="未授权：请提供正确的 Bearer Token")


# ============ 路径安全 ============
def safe_resolve(raw: str) -> pathlib.Path:
    """解析用户路径并校验在允许根目录内（防目录穿越）。"""
    p = pathlib.Path(raw).expanduser()
    if not p.is_absolute():
        p = ALLOWED_ROOT / p
    p = p.resolve()
    try:
        p.relative_to(ALLOWED_ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"路径超出允许根目录: {ALLOWED_ROOT}")
    return p


def is_media_file(name: str) -> bool:
    return pathlib.Path(name).suffix.lower() in MEDIA_EXTS


# ============ 数据模型 ============
class AnalyzeRequest(BaseModel):
    filenames: List[str]
    folder: str = ""


class RenamePreviewRequest(BaseModel):
    path: str                # 文件所在目录
    filenames: List[str]     # 待重命名文件名
    pattern: str = "auto"    # auto / {title} ({year}){ext} / {title}.S{season:02d}.E{episode:02d}{ext}


class RenameRequest(BaseModel):
    path: str
    renames: List[Dict[str, str]]   # [{old, new}, ...]
    dry_run: bool = True            # 默认预览模式


# ============ 建议文件名 ============
def suggest_name(result: Dict[str, Any], ext: str) -> str:
    """根据解析结果生成建议文件名。"""
    media_type = result.get("type") or "unknown"
    title = (result.get("title") or "未知").strip()
    year = result.get("year")
    season = result.get("season")
    episode = result.get("episode")

    if media_type == "tv" and season is not None and episode is not None:
        return f"{title}.S{int(season):02d}.E{int(episode):02d}{ext}"
    if media_type in ("movie", "special") and year:
        return f"{title} ({year}){ext}"
    return f"{title}{ext}"


# ============ 路由 ============
@app.get("/api/health", dependencies=[Depends(require_token)])
def health() -> Dict[str, str]:
    return {"app": APP_NAME, "version": __version__, "status": "ok"}


@app.get("/api/analyze", dependencies=[Depends(require_token)])
def analyze(filename: str = Query(..., description="待解析文件名"),
            folder: str = Query("", description="所属目录（可空）")) -> Dict[str, Any]:
    return analyze_one(filename, folder)


@app.post("/api/analyze-batch", dependencies=[Depends(require_token)])
def analyze_batch(req: AnalyzeRequest) -> List[Dict[str, Any]]:
    if len(req.filenames) > 500:
        raise HTTPException(status_code=400, detail="单次最多 500 个文件")
    return [analyze_one(fn, req.folder) for fn in req.filenames]


@app.get("/api/scan", dependencies=[Depends(require_token)])
def scan(path: str = Query("/", description="要扫描的目录"),
         recursive: bool = Query(False, description="是否递归子目录")) -> Dict[str, Any]:
    root = safe_resolve(path)
    if not root.is_dir():
        raise HTTPException(status_code=404, detail=f"目录不存在: {root}")

    media: List[Dict[str, Any]] = []
    walker = root.rglob("*") if recursive else root.glob("*")
    for f in sorted(walker):
        if f.is_file() and is_media_file(f.name):
            rel = str(f.relative_to(root))
            try:
                info = analyze_one(f.name, str(f.parent))
            except Exception:
                info = {"filename": f.name, "title": f.name, "type": "unknown"}
            media.append({
                "name": f.name,
                "path": str(f),
                "rel_path": rel,
                "size": f.stat().st_size,
                "analysis": info,
                "suggested_name": suggest_name(info, f.suffix),
            })
    return {"path": str(root), "total": len(media), "files": media}


@app.post("/api/rename-preview", dependencies=[Depends(require_token)])
def rename_preview(req: RenamePreviewRequest) -> Dict[str, Any]:
    """为指定文件生成重命名预览（不执行任何改动）。"""
    root = safe_resolve(req.path)
    if not root.is_dir():
        raise HTTPException(status_code=404, detail=f"目录不存在: {root}")

    previews: List[Dict[str, Any]] = []
    for fn in req.filenames:
        src = root / fn
        if not src.exists():
            previews.append({"old": fn, "new": None, "ok": False, "error": "文件不存在"})
            continue
        info = analyze_one(fn, str(root))
        new_name = info["suggested_name"]
        if new_name == fn:
            previews.append({"old": fn, "new": fn, "ok": True, "unchanged": True,
                             "analysis": info})
        else:
            dst = root / new_name
            conflict = dst.exists() and dst != src
            previews.append({"old": fn, "new": new_name, "ok": not conflict,
                             "conflict": conflict, "analysis": info})
    return {"path": str(root), "previews": previews}


@app.post("/api/rename", dependencies=[Depends(require_token)])
def rename(req: RenameRequest) -> Dict[str, Any]:
    """执行重命名（默认 dry_run 仅预览）。"""
    root = safe_resolve(req.path)
    if not root.is_dir():
        raise HTTPException(status_code=404, detail=f"目录不存在: {root}")

    results: List[Dict[str, Any]] = []
    backup_dir = root / ".tv_renamer_backup"
    for item in req.renames[:500]:
        old, new = item.get("old", ""), item.get("new", "")
        src = root / old
        dst = root / new
        if not src.exists():
            results.append({"old": old, "new": new, "ok": False, "error": "源文件不存在"})
            continue
        if not new or new == old:
            results.append({"old": old, "new": new, "ok": True, "skipped": True})
            continue
        if dst.exists() and dst != src:
            results.append({"old": old, "new": new, "ok": False, "error": "目标已存在"})
            continue
        if req.dry_run:
            results.append({"old": old, "new": new, "ok": True, "dry_run": True})
            continue
        # 实际执行：先备份（防误操作）
        try:
            if not backup_dir.exists():
                backup_dir.mkdir()
            shutil.copy2(src, backup_dir / old)
            src.rename(dst)
            results.append({"old": old, "new": new, "ok": True, "backed_up": True})
        except OSError as e:
            results.append({"old": old, "new": new, "ok": False, "error": str(e)})

    return {"path": str(root), "results": results,
            "dry_run": req.dry_run,
            "backup_dir": str(backup_dir) if backup_dir.exists() else None}


@app.exception_handler(Exception)
async def unhandled_exception(request, exc: Exception) -> JSONResponse:
    logger.error("未处理异常 %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": f"服务器错误: {exc}"})


# ============ 网页控制台（PWA）============
# 挂载必须放在所有 API 路由注册之后（FastAPI 按注册顺序匹配，/api/* 优先）。
from fastapi.staticfiles import StaticFiles  # noqa: E402

_STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="web-console")
    logger.info("网页控制台已挂载: %s", _STATIC_DIR)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8123"))
    logger.info("%s API 服务启动（版本 %s）", APP_NAME, __version__)
    logger.info("鉴权 Token: Bearer %s", API_TOKEN)
    logger.info("允许根目录: %s", ALLOWED_ROOT)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
