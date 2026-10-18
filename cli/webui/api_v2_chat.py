# -*- coding: utf-8 -*-
"""api_v2_chat（壳重排 IA v2 舰）——对话面消息流只读投影，前缀 /api/v2/。

舰间契约：本文件=本舰独写（唯一新 API 件，只读零写）；一切文件 r 模式、
零墙钟（now 类一律不取——战场钟=数据内时刻，同输入两跑一致，
api_v2_cockpit 同律）。挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_chat_face.py
（_V2MountHandler，同 tests/test_command_converse.py 先例）。

设计权威 docs/design/2026-10-20-full-history-synthesis.md §⑥推导一/二
（对话=输入面第一公民：开仗/指挥/@派活）；对话页机制借 ARTEX 前端图§六.1
通用件不借结构——1s 尾轮询+key 去重+不乐观回声+渐进披露。

一路由（只读投影，全过会话门）：
  GET /api/v2/chat-log?goal=G&battle=N&limit=120
      → 对话气泡事件流：timeline+ask+approval 四类事件——
        kind=command  指挥（timeline 行 event 前缀 battle-say/warrior-steer，
                      即操作员话语与转向注入=右泡）
        kind=warrior  士兵/系统（其余 timeline 行=左泡）
        kind=ask      求助（battle 根 ask.md 非空，watchdog ask:human 同位）
        kind=approval 待审批（timeline revert_cmd 未销账推导，approval_center
                      同义自持实现；带 row 供回复四分类 join /api/approval）
      每事件带稳定 key（tl:<行>/ask:1/ap:<行>）供前端 key 去重；按 (ts,
      kind序, 行号) 升序；limit=尾窗条数（默认 120，帽 400——渐进披露的服务
      员面）。counts.total=全量条数（尾窗不足时前端知道还有更早）。

词表律（宪法62）：屏上字段名全人话——本模块 text 一律人话动词句
（api_v2_broadcast.VERB_ZH 单源借译，不造第二词表）；JSON key 为代码
标识符不受限，上屏由页面词表负责。
"""
import os

from . import api_v2_cockpit as _cp

ROUTE_CHAT_LOG = "/api/v2/chat-log"
ROUTES = {ROUTE_CHAT_LOG: None}                       # 尾部赋真身（前向引用）
POST_ROUTES = {}            # 只读零写：无 POST 面（写走既有 propose/steer-reply）

KIND_COMMAND = "command"       # 指挥（操作员话语/转向注入）
KIND_WARRIOR = "warrior"       # 士兵/系统
KIND_ASK = "ask"               # 求助
KIND_APPROVAL = "approval"     # 待审批

# 指挥事件前缀（battle-say=操作员话语；warrior-steer=四分类转向/情报注入，
# cli/warrior/steer.py write_steer 事件形）
_COMMAND_PREFIX = ("battle-say", "warrior-steer")
# kind 排序稳定序（同时刻时：士兵叙述→指挥→求助→待审批）
_KIND_RANK = {KIND_WARRIOR: 0, KIND_COMMAND: 1, KIND_ASK: 2, KIND_APPROVAL: 3}

TAIL_DEFAULT = 120             # 尾窗默认（渐进披露首屏有界）
TAIL_MAX = 400                 # 尾窗帽（大账只投影用户正在看的窗口）
POLL_MS = 1000                 # 页面尾轮询节拍（ARTEX 对话页同律 1s）


def _verb_zh(event):
    return _cp._verb_zh(event)                      # 人话动词单源借译


def _is_command(event):
    head = str(event or "").split(" ", 1)[0]
    return any(head.startswith(p) for p in _COMMAND_PREFIX)


def _pending_approvals(battle_dir, gens):
    """待审批行（timeline revert_cmd 未销账、无豁免）——approval_center 同义
    自持实现（单仗面，不跨仗扫；律同 api_v2_cockpit._scan_waiting）。"""
    tl = _cp._merged_timeline(battle_dir, gens)
    events = [_cp._cell("timeline.tsv", c, "event") for _no, c in tl]
    approvals = [r for _k, r in _cp._merge_by_id(battle_dir, gens,
                                                 "approvals.tsv")]
    out = []
    for no, c in tl:
        revert = _cp._cell("timeline.tsv", c, "revert_cmd").strip()
        if not revert:
            continue
        ev = _cp._cell("timeline.tsv", c, "event")
        if any(x == "revert:" + ev for x in events[no:]):
            continue                                # 已销账
        if any(_cp._cell("approvals.tsv", a, "decision") == "exempted"
               and ev in _cp._cell("approvals.tsv", a, "note")
               for a in approvals):
            continue                                # 预授权豁免
        parts = ev.split()
        tool = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
        out.append({
            "key": "ap:%d" % no, "kind": KIND_APPROVAL,
            "ts": _cp._cell("timeline.tsv", c, "timestamp"),
            "actor": _cp._cell("timeline.tsv", c, "actor"),
            "row": no,
            "text": "待审批：%s（命令 %s；确认后清理 %s）" % (
                _verb_zh(ev), tool,
                revert.split()[0] if revert.split() else ""),
            "event": ev, "command": revert,
            "detail_url": "/p/approval-center",
        })
    return out


def chat_log(query, ledger_dir=None, battles_dir=None):
    """GET /api/v2/chat-log → (200, 事件流) | (422, {error})。

    只读投影四类事件为对话气泡；query: goal/battle/limit。
    """
    q = query if isinstance(query, dict) else {}
    try:
        limit = int(str(q.get("limit") or TAIL_DEFAULT).strip() or
                    TAIL_DEFAULT)
    except (TypeError, ValueError):
        limit = TAIL_DEFAULT
    limit = max(1, min(limit, TAIL_MAX))
    try:
        battles, meta, battle_dir = _cp._resolve(
            battles_dir, str(q.get("battle") or "").strip(), ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if not battle_dir:
        battle_dir = str(ledger_dir or "")

    gens = _cp._gens(battle_dir) if battle_dir else []
    battle_id = (meta["id"] if meta else
                 os.path.basename(str(battle_dir).rstrip(os.sep)) or
                 os.path.basename(str(ledger_dir or "").rstrip(os.sep)))

    events = []
    # —— timeline 两类：指挥（右泡）/士兵（左泡）——
    for no, c in _cp._merged_timeline(battle_dir, gens):
        ev = _cp._cell("timeline.tsv", c, "event")
        events.append({
            "key": "tl:%d" % no,
            "kind": KIND_COMMAND if _is_command(ev) else KIND_WARRIOR,
            "ts": _cp._cell("timeline.tsv", c, "timestamp"),
            "actor": _cp._cell("timeline.tsv", c, "actor"),
            "row": no,
            "text": _verb_zh(ev),
            "event": ev,
        })
    # —— 求助：battle 根 ask.md 非空（watchdog ask:human 同位）——
    ask_text = _cp._read_text(os.path.join(battle_dir, "ask.md"))
    if ask_text and ask_text.strip():
        first = ask_text.strip().splitlines()[0].strip()
        events.append({
            "key": "ask:1", "kind": KIND_ASK,
            "ts": events[-1]["ts"] if events else "",
            "actor": "士兵", "text": "求助：" + first,
            "detail_url": "/p/inbox",
        })
    # —— 待审批（回复四分类按钮的挂点）——
    events.extend(_pending_approvals(battle_dir, gens))

    events.sort(key=lambda e: (e["ts"], _KIND_RANK.get(e["kind"], 9),
                               str(e["key"])))
    total = len(events)
    tail = events[-limit:]
    counts = {KIND_COMMAND: 0, KIND_WARRIOR: 0, KIND_ASK: 0, KIND_APPROVAL: 0,
              "total": total}
    for e in events:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    return 200, {
        "battle": {"id": battle_id, "n": meta["n"] if meta else None},
        "events": tail,
        "counts": counts,
        "limit": limit,
        "poll_ms": POLL_MS,
        "read_only": True,
        "reply_route": "/api/v2/steer-reply",       # 四分类既有面
        "propose_route": "/api/v2/battle/propose",  # 对话建任务既有面
        "at_search_route": "/api/v2/at-search",     # @引用既有面
    }


def _chat_log_route(query, ledger_dir=None, battles_dir=None):
    return chat_log(query, ledger_dir=ledger_dir, battles_dir=battles_dir)


ROUTES[ROUTE_CHAT_LOG] = _chat_log_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口（GET）→ (status, payload) | None（非本域路由）。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
