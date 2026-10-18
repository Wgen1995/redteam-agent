# -*- coding: utf-8 -*-
"""api_v2_llm（LLM 录制页）——模型对话记录只读投影，路由前缀 /api/v2/。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_llm_recordings.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。

数据单源：cli/warrior/transcript.py（质量律 R4 原始对话存档）写的
<goal_dir>/transcripts/<INT-id>.jsonl——一意图一文件，append-only 跨重启
续写；行结构 ts/battle/warrior/intent/turn/model/role/content(+usage 可选)。
本投影不铸账本行、不改表、不重写 transcript——坏行不静默吞（bad_lines
如实披露），usage 缺席=0 不虚构估算。

两路由（全过会话门；除 login 外无豁免）：
  GET /api/v2/llm-transcripts[?goal=G-xxx]
      → 录制列表单源：意图升序，逐条=意图/标题(intents.tsv 反查，缺=空)/
        智能体/模型道(去重排序)/轮数(最大 turn)/有效行数/坏行数/
        token 耗(usage 求和)+总计。
  GET /api/v2/llm-transcript-detail?id=INT-xxx[&goal=G-xxx]
      → 逐行原文对（mono 页消费）：ts/role/model/turn/content 原文保真+
        usage 原样透传（缺=None）——请求/响应即 user/assistant 行对。
"""
import json
import os
import re

from ledger import core

ROUTE_LIST = "/api/v2/llm-transcripts"
ROUTE_DETAIL = "/api/v2/llm-transcript-detail"
ROUTES = {ROUTE_LIST: None, ROUTE_DETAIL: None}   # 尾部赋真身（前向引用）

DIR_NAME = "transcripts"          # 与 cli/warrior/transcript.py 同名单源
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
_IT = core.TABLES["intents.tsv"]


def _goal_dir(base, goal):
    """goal= 同名目录优先（本 goal 内子目录，次选同辈）——多战宿主可定位。"""
    if not goal:
        return base
    for cand in (os.path.join(base, goal), os.path.join(os.path.dirname(base), goal)):
        if os.path.isdir(cand):
            return cand
    return base


def _load_jsonl(path):
    """jsonl → (rows, bad)；文件不可读=None（不存在/目录=调用方判 404）。"""
    rows, bad = [], 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    bad += 1
                    continue
                if not isinstance(row, dict):
                    bad += 1
                    continue
                rows.append(row)
    except OSError:
        return None, 0
    return rows, bad


def _usage_tokens(usage):
    """usage dict → (prompt_tokens, completion_tokens)；缺席/坏值=0,0。"""
    pt = ct = 0
    if isinstance(usage, dict):
        try:
            pt = int(usage.get("prompt_tokens") or 0)
            ct = int(usage.get("completion_tokens") or 0)
        except (TypeError, ValueError):
            pt = ct = 0
    return pt, ct


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _intent_titles(gd):
    """intents.tsv → {id: title}（后行覆盖前行=最新态；缺表={}）。"""
    out = {}
    for r in core.Session(gd).rows("intents.tsv"):
        out[r[_IT.index("id")]] = r[_IT.index("title")]
    return out


def _agg(iid, rows, bad, titles):
    """单意图聚合：模型道/轮数/token/首末时刻（文件序=时间序，append-only）。"""
    models = set()
    pt = ct = 0
    turns = 0
    warrior = ""
    first_ts = ""
    last_ts = ""
    for r in rows:
        m = str(r.get("model") or "")
        if m:
            models.add(m)
        a, b = _usage_tokens(r.get("usage"))
        pt += a
        ct += b
        turns = max(turns, _int(r.get("turn")))
        w = str(r.get("warrior") or "")
        if w:
            warrior = w
        ts = str(r.get("ts") or "")
        if ts:
            last_ts = ts
            if not first_ts:
                first_ts = ts
    return {"intent": iid, "title": titles.get(iid, ""), "warrior": warrior,
            "models": sorted(models), "turns": turns, "lines": len(rows),
            "bad_lines": bad, "prompt_tokens": pt, "completion_tokens": ct,
            "first_ts": first_ts, "last_ts": last_ts}


# ---------------------------------------------------------------- 投影 ① --

def list_transcripts(query, ledger_dir):
    """录制列表 → (200, {goal, items[], totals})；意图升序确定性。"""
    gd = _goal_dir(ledger_dir, (query.get("goal") or "").strip())
    tdir = os.path.join(gd, DIR_NAME)
    try:
        names = sorted(os.listdir(tdir))
    except OSError:
        names = []
    titles = _intent_titles(gd)
    items = []
    for name in names:
        if not name.endswith(".jsonl"):
            continue
        iid = name[:-len(".jsonl")]
        if not _SAFE_ID.match(iid):
            continue                      # 越界名/隐藏文件不上列表
        rows, bad = _load_jsonl(os.path.join(tdir, name))
        if rows is None:
            continue
        items.append(_agg(iid, rows, bad, titles))
    items.sort(key=lambda i: i["intent"])
    totals = {
        "intents": len(items),
        "lines": sum(i["lines"] for i in items),
        "prompt_tokens": sum(i["prompt_tokens"] for i in items),
        "completion_tokens": sum(i["completion_tokens"] for i in items),
    }
    return 200, {"goal": os.path.basename(os.path.normpath(gd)),
                 "items": items, "totals": totals}


# ---------------------------------------------------------------- 投影 ② --

def transcript_detail(query, ledger_dir):
    """逐行原文 → (200, {goal, intent, title, lines[], …})；坏行披露不静默。"""
    gd = _goal_dir(ledger_dir, (query.get("goal") or "").strip())
    iid = (query.get("id") or "").strip()
    if not iid:
        return 400, {"error": "缺 id 参数（INT-xxx）"}
    if not _SAFE_ID.match(iid):
        return 400, {"error": "id 含非法字符（意图号须字母数字及 _ . -）"}
    rows, bad = _load_jsonl(os.path.join(gd, DIR_NAME, iid + ".jsonl"))
    if rows is None:
        return 404, {"error": "无此录制: %s" % iid}
    lines = []
    for r in rows:
        content = r.get("content")
        lines.append({
            "ts": str(r.get("ts") or ""),
            "role": str(r.get("role") or ""),
            "model": str(r.get("model") or ""),
            "turn": _int(r.get("turn")),
            "content": content if isinstance(content, str) else str(content),
            "usage": r.get("usage") if isinstance(r.get("usage"), dict) else None,
        })
    agg = _agg(iid, rows, bad, _intent_titles(gd))
    return 200, {
        "goal": os.path.basename(os.path.normpath(gd)),
        "intent": iid, "title": agg["title"], "warrior": agg["warrior"],
        "models": agg["models"], "turns": agg["turns"],
        "prompt_tokens": agg["prompt_tokens"],
        "completion_tokens": agg["completion_tokens"],
        "bad_lines": bad, "lines": lines,
    }


ROUTES[ROUTE_LIST] = list_transcripts
ROUTES[ROUTE_DETAIL] = transcript_detail


def dispatch(path, query, ledger_dir):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir)
