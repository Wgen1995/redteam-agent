# -*- coding: utf-8 -*-
"""api_v2_workspace（T7·P8-P18 工作区页）——任务工件浏览+下载只读投影，
路由 /api/v2/workspace.json（下载=同路由 path 参数）。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，读输出确定性）；挂载=ROUTES 单源表由 include 机制
（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_workspace.py（_V2MountHandler）：会话门复用
Handler._session_ok，缺会话=401 JSON。dispatch(path, query, ledger_dir,
battles_dir) 与 api_v2_broadcast 同形（本域不依赖主账本目录，入参原样收下）。

数据单源（spec §P8-P18 工作区：工件浏览+下载）：
  工件清单 = battles/<battle-N>/ 工作区实勘（目录漫游有界：深度≤3、条目
             ≤800，超出如实截断标 truncated——不虚报全量，诚实法条）；
  工件类别 = 确定性后缀/位置推导：报告(.md 根层)/摘要(*-summary.json)/
             指令(directive|mission.txt)/结算(settle-report.txt)/日志(.log|
             runner.out)/账本表(.tsv)/证据(evidence|replay 内)/代目(G-* 目录)；
  下载     = path 参数：路径监狱（拒 .. 与绝对路径——只出任务根）、大小上限
             MAX_DOWNLOAD=2MB（超出=413 如实报上限）、b64 装载（页端组
             blob 落盘）；mime=扩展名推导（缺省 application/octet-stream）。
"""
import base64
import os
import re

from ledger.session_view import list_battles

ROUTE_WS = "/api/v2/workspace.json"
ROUTES = {ROUTE_WS: None}                              # 尾部赋真身（前向引用）

MAX_WALK_DEPTH = 3
MAX_ENTRIES = 800
MAX_DOWNLOAD = 2 * 1024 * 1024                          # 2MB（b64 装载上限）

_MIME = {
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".log": "text/plain; charset=utf-8",
    ".json": "application/json",
    ".tsv": "text/tab-separated-values; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".raw": "application/octet-stream",
}


def _read_int(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None，布尔无语义：%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数：%r" % (name, value))


def _kind_of(rel, is_dir, name):
    """工件类别：确定性后缀/位置推导（单源于此，不虚构）。"""
    if is_dir:
        if name.startswith("G-"):
            return "代目"
        if name in ("evidence", "replay", "replay.old"):
            return "证据"
        return "目录"
    low = name.lower()
    if rel.startswith("G-") and "/evidence" in rel:
        return "证据"
    if low.endswith("-summary.json"):
        return "摘要"
    if low.endswith(".md"):
        return "报告"
    if name in ("directive.txt", "mission.txt"):
        return "指令"
    if name == "settle-report.txt":
        return "结算"
    if low.endswith((".log", ".out")):
        return "日志"
    if low.endswith(".tsv"):
        return "账本表"
    if low.endswith(".json"):
        return "摘要"
    return "文件"


def _walk_bounded(root):
    """有界漫游 → (entries, truncated)。entries=按路径字典序（确定性）。"""
    entries = []
    truncated = False
    stack = [(root, "")]
    while stack:
        base, rel = stack.pop(0)
        try:
            names = sorted(os.listdir(base))
        except OSError:
            continue
        for name in names:
            sub_rel = (rel + "/" + name) if rel else name
            full = os.path.join(base, name)
            is_dir = os.path.isdir(full)
            if len(entries) >= MAX_ENTRIES:
                truncated = True
                return entries, truncated
            try:
                size = 0 if is_dir else os.path.getsize(full)
            except OSError:
                size = 0
            entries.append({
                "path": sub_rel, "name": name, "kind": _kind_of(sub_rel, is_dir, name),
                "dir": is_dir, "size": size,
            })
            depth = sub_rel.count("/")
            if is_dir and depth + 1 < MAX_WALK_DEPTH:
                stack.append((full, sub_rel))
    entries.sort(key=lambda e: e["path"])
    return entries, truncated


def workspace_view(battles_dir=None, battle=None, path=None, ledger_dir=None):
    """工作区投影：无 path=工件清单；有 path=下载装载（b64）。

    清单 → {battle, battles, counts, entries[], truncated}；
    下载 → {name, path, size, mime, b64}（路径监狱/大小上限诚实拒）。
    """
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return {"error": "尚无任务工作区（无 battles 目录）", "battles": []}
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    home = os.path.join(str(root), picked["id"])

    if path is not None:
        return _download(home, picked, str(path))

    entries, truncated = _walk_bounded(home)
    counts = {}
    for e in entries:
        if not e["dir"]:
            counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    return {
        "battle": {"id": picked["id"], "n": picked["n"]},
        "battles": battles,
        "counts": counts,
        "entries": entries,
        "truncated": truncated,
        "note": ("工件=任务工作区实勘（有界漫游：深度≤%d、条目≤%d）；"
                 "下载≤2MB（超出如实拒，大件走报告导出）。"
                 % (MAX_WALK_DEPTH, MAX_ENTRIES)),
    }


def _download(home, picked, rel):
    """路径监狱+大小上限 → (status, {name,size,mime,b64}|error)。"""
    rel = rel.replace("\\", "/").strip()
    if not rel or rel.startswith("/") or rel.startswith("~"):
        return 422, {"error": "路径非法（只接受任务根内相对路径）: %s" % rel}
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return 422, {"error": "路径越界（禁 .. ——只出任务根）: %s" % rel}
    full = os.path.join(home, *parts)
    try:
        real_home = os.path.realpath(home)
        real_full = os.path.realpath(full)
    except OSError:
        return 404, {"error": "工件不存在: %s" % rel}
    if real_full != real_home and not real_full.startswith(real_home + os.sep):
        return 422, {"error": "路径越界（解析后出任务根）: %s" % rel}
    if not os.path.isfile(real_full):
        return 404, {"error": "工件不存在或不是文件: %s" % rel}
    try:
        size = os.path.getsize(real_full)
    except OSError:
        return 404, {"error": "工件不可读: %s" % rel}
    if size > MAX_DOWNLOAD:
        return 413, {"error": "工件 %s 为 %d 字节，超过 2MB 下载上限"
                      % (rel, size)}
    try:
        with open(real_full, "rb") as f:
            data = f.read()
    except OSError:
        return 404, {"error": "工件不可读: %s" % rel}
    ext = os.path.splitext(rel)[1].lower()
    return 200, {
        "battle": {"id": picked["id"], "n": picked["n"]},
        "path": rel, "name": parts[-1], "size": size,
        "mime": _MIME.get(ext, "application/octet-stream"),
        "b64": base64.b64encode(data).decode("ascii"),
    }


def _workspace_route(query, ledger_dir=None, battles_dir=None):
    try:
        result = workspace_view(battles_dir=battles_dir, battle=query.get("battle"),
                                path=query.get("path"), ledger_dir=ledger_dir)
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "工作区参数无效: %s" % e}
    if isinstance(result, tuple):                    # 下载支路=(status, payload)
        return result
    payload = result                                 # 清单支路=dict
    if "error" in payload:
        code = 404
        if "路径" in payload["error"]:
            code = 422
        return code, payload
    return 200, payload


ROUTES[ROUTE_WS] = _workspace_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
