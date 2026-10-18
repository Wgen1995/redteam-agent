# -*- coding: utf-8 -*-
"""api_v2_cockpit（驾驶舱舰·功能27）——产品驾驶舱四路聚合只读投影，前缀 /api/v2/。

舰间契约：本文件=驾驶舱舰独写（唯一新 API 件）；只读投影零写入（一切文件
r 模式，禁 datetime.now——战场钟=全账 timeline 最大行时刻，api_v2_retest
同律，同输入两跑一致）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）_OPTIONAL_MODULES 可选件通道分发——挂法钉在
tests/test_webui_pagespec_cockpit*.py。设计唯一正文
docs/design/2026-10-20-cockpit-ui-blueprint.md（四问+词表62+五秒三问63）。

四路由（全过会话门；读 TSV 真数据，严禁假数占位）：
  GET /api/v2/cockpit.json
      → 首页四问直答聚合：问一 打出什么漏洞了（验真漏洞榜：只有
        exploitation_status=verified 且 status=active 的进榜，每枚带
        名字/多严重/在哪/证据链接）；问二 正在打什么（在途任务+最近
        时间线）；问三 什么在等我（待审批+求助，跨仗扫）；问四 花多少钱
        （budget.tsv 聚合 vs goals 帽三段余量条）。
  GET /api/v2/cockpit-findings.json
      → 漏洞页：全量漏洞+证据袋（EV 卡引用+角色[证实/对照，来自
        evidence_ids/control_evidence_ids]+版本[pair_group 同组多次捕获
        按 observed_at 排 v1/v2/v3]）+上次验真 X 天前（战场钟推算）+
        待复验队列位（api_v2_retest 队序同律：可复测先列，最久未验先列）。
  GET /api/v2/cockpit-knowledge.json
      → 知识库页：打法卡（knowledge/cp-index.tsv 真索引）+哨兵规则
        （knowledge/engineering/sentinels-v1.tsv 真规则库）+蒸馏草稿人审
        入口（knowledge/staging/ 真文件；蒸馏舰在飞，行落即显）。
  GET /api/v2/cockpit-inbox.json
      → 收件箱：待审批（timeline revert_cmd 未销账推导，approval_center
        同义自持实现）+求助（battle 根 ask.md 非空，watchdog ask:human
        通道同位）+批量同类聚合（同工具一票组）。

词表律（宪法62）：屏上字段名全人话——finding→漏洞 / intent→任务 /
warrior→士兵 / credential→钥匙 / asset→目标 / EV卡→证据；投影 JSON 的
key 为代码标识符不受限，上屏由页面词表负责。
"""
import datetime
import os
import re

from ledger import core
from ledger.session_view import list_battles

ROUTE_COCKPIT = "/api/v2/cockpit.json"
ROUTE_FINDINGS = "/api/v2/cockpit-findings.json"
ROUTE_KNOWLEDGE = "/api/v2/cockpit-knowledge.json"
ROUTE_INBOX = "/api/v2/cockpit-inbox.json"
ROUTES = {ROUTE_COCKPIT: None, ROUTE_FINDINGS: None,
          ROUTE_KNOWLEDGE: None, ROUTE_INBOX: None}   # 尾部赋真身（前向引用）

_IMPACT_RANK = {"高": 0, "中": 1, "低": 2}
_DONE_INTENT = ("done", "failed", "cancelled", "superseded")
_INTENT_ZH = {"pending": "排队中", "running": "执行中", "blocked": "受阻",
              "waiting": "等回复", "done": "已完成", "failed": "失败",
              "cancelled": "已取消", "superseded": "已被替代"}
_REPLAY_PAT = re.compile(r"replay-probe (EV-\S+) verdict=")
_REPLAY2_PAT = re.compile(r"replay:(EV-\S+):")
_WARN_PCT = 80.0                       # 预算预警线（api_v2_tasks 同律）
_RECENT_TAIL = 8                       # 首页最近时间线条数（首屏有界）
_TOP_N = 10                            # 漏洞榜上限（首屏有界）


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _tsv_rows(path, tname):
    """tsv 文本→列行（core.Session 同形：unesc 反转义+补宽；缺件=空）。"""
    text = _read_text(path)
    if not text:
        return []
    width = len(core.TABLES[tname])
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = [core.unesc(c) for c in line.split("\t")]
        out.append(cols + [""] * (width - len(cols)))
    return out


def _cell(tname, r, col):
    return r[core.TABLES[tname].index(col)]


def _gens(battle_dir):
    """G-* 代目自然序（server._latest_gen 同律：G-r2<G-r10）；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


def _read_dirs(battle_dir, gens):
    if gens:
        return [os.path.join(battle_dir, g) for g in gens]
    return [battle_dir] if battle_dir else []


def _merge_by_id(battle_dir, gens, tname):
    """表行跨代合并：同 id 后代胜，保首现次序 → [(id, cols)]。"""
    by_id, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for r in _tsv_rows(os.path.join(d, tname), tname):
            key = _cell(tname, r, "id").strip() if "id" in core.TABLES[tname] \
                else r[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = r
    return [(k, by_id[k]) for k in order]


def _merged_timeline(battle_dir, gens):
    """全代 timeline 合并 → [(全局行号, cols)]（行号供页面账本锚定）。"""
    out = []
    for d in _read_dirs(battle_dir, gens):
        out.extend(_tsv_rows(os.path.join(d, "timeline.tsv"), "timeline.tsv"))
    return list(enumerate(out, 1))


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir)——给了 battles_dir 用战根
    （battle 选仗，缺省=最新），没给=单账本回落主账本（不猜家目录——
    演示/测试给单账本即得单账本，输出跨机确定）。"""
    if not battles_dir:
        return [], None, str(ledger_dir or "")
    battles = list_battles(battles_dir)
    if not battles:
        return [], None, str(ledger_dir or "")
    meta = None
    m = re.search(r"(\d+)", str(battle or ""))
    if m:
        n = int(m.group(1))
        for b in battles:
            if b["n"] == n:
                meta = b
                break
        if meta is None:
            raise ValueError("battle 不存在: %s" % battle)
    else:
        meta = battles[-1]
    return battles, meta, os.path.join(str(battles_dir), meta["id"])


def _goal_of(battle_dir, gens):
    """goals 合并末行 → dict（goals 单行制；无=诚实空 dict）。"""
    rows_ = _merge_by_id(battle_dir, gens, "goals.tsv")
    if not rows_:
        return {}
    last = rows_[-1][1]
    return {c: _cell("goals.tsv", last, c) for c in core.TABLES["goals.tsv"]}


def _cap_num(seg):
    """帽段解析：'2M'/'50000'/'40' → 数（K/M/G 后缀；空/坏=0）。"""
    s = str(seg or "").strip()
    if not s:
        return 0.0
    m = re.match(r"^([0-9.]+)\s*([KkMmGg]?)$", s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    scale = {"": 1.0, "k": 1e3, "m": 1e6, "g": 1e9}[m.group(2).lower()]
    return float(m.group(1)) * scale


def _to_num(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return 0.0


def _epoch(ts):
    """ISO Z 时刻→epoch 秒；坏/空=None（确定性：不取墙钟）。"""
    try:
        return datetime.datetime.strptime(str(ts).strip(),
                                           "%Y-%m-%dT%H:%M:%SZ"
                                           ).replace(tzinfo=datetime.timezone.utc
                                                     ).timestamp()
    except ValueError:
        return None


def _dur_text(days):
    if days is None:
        return "—"
    if days >= 1:
        return "%d 天前" % int(days)
    return "不足 1 天前"


def _verb_zh(event):
    """时间线动词→人话（api_v2_broadcast.VERB_ZH 单源借译，不造第二词表）。"""
    from . import api_v2_broadcast as _b
    head = str(event or "").split(" ", 1)[0].rstrip(":")
    return _b.VERB_ZH.get(head, _b._FALLBACK_ZH)


# ---------------------------------------------------------------- 问一·漏洞榜 --

def _vuln_leaderboard(battle_dir, gens, goal):
    """问一：只有验真+在册的漏洞进榜（严重度先行；首屏 ≤10 枚）。"""
    assets = {k: r for k, r in _merge_by_id(battle_dir, gens, "assets.tsv")}
    out = []
    for fid, r in _merge_by_id(battle_dir, gens, "findings.tsv"):
        if (_cell("findings.tsv", r, "exploitation_status") != "verified"
                or _cell("findings.tsv", r, "status") != "active"):
            continue
        ev_ids = [e for e in str(_cell("findings.tsv", r, "evidence_ids")
                                or "").split(";") if e.strip()]
        ast_id = _cell("findings.tsv", r, "affected_asset_id")
        where = ""
        if ast_id and ast_id in assets:
            where = _cell("assets.tsv", assets[ast_id], "value") or ast_id
        elif ast_id:
            where = ast_id
        elif goal.get("target"):
            where = goal["target"]
        out.append({
            "id": fid,
            "title": _cell("findings.tsv", r, "title"),
            "impact": _cell("findings.tsv", r, "impact") or "低",
            "confidence": _cell("findings.tsv", r, "confidence"),
            "where": where or "（未登记位置）",
            "evidence": ev_ids,
            "detail_url": "/p/finding-detail?id=" + fid,
            "created": _cell("findings.tsv", r, "created"),
        })
    out.sort(key=lambda v: (_IMPACT_RANK.get(v["impact"], 9),
                            v["created"], v["id"]))
    return {"total": len(out), "top": out[:_TOP_N]}


# ---------------------------------------------------------------- 问二·活池 --

def _live_pool(battle_dir, gens):
    """问二：在途任务（status 未终态）+最近时间线（人话动词）。"""
    intents = []
    for iid, r in _merge_by_id(battle_dir, gens, "intents.tsv"):
        status = _cell("intents.tsv", r, "status")
        if status in _DONE_INTENT:
            continue
        intents.append({"id": iid,
                        "title": _cell("intents.tsv", r, "title") or iid,
                        "status": status,
                        "status_zh": _INTENT_ZH.get(status, status or "待执行"),
                        "kind": _cell("intents.tsv", r, "kind"),
                        "created": _cell("intents.tsv", r, "created")})
    tl = _merged_timeline(battle_dir, gens)
    recent = [{"row": no, "ts": _cell("timeline.tsv", c, "timestamp"),
               "actor": _cell("timeline.tsv", c, "actor"),
               "text": _verb_zh(_cell("timeline.tsv", c, "event")),
               "event": _cell("timeline.tsv", c, "event")}
              for no, c in tl[-_RECENT_TAIL:]]
    recent.reverse()
    return {"inflight_count": len(intents), "intents": intents,
            "recent": recent}


# ---------------------------------------------------------- 问三·什么在等我 --

def _scan_waiting(battles_dir, ledger_dir):
    """跨仗扫：待审批（revert_cmd 未销账）+求助（ask.md 非空）。

    待审批推导=approval_center 同义自持实现：timeline 行 revert_cmd 非空，
    且无后续 revert:<event> 销账、无豁免（approvals decision=exempted 且
    note 含事件名）。
    """
    pending, asks = [], []
    battles = list_battles(battles_dir) if battles_dir else []
    if battles:
        roots = [(m["id"], os.path.join(str(battles_dir), m["id"]))
                 for m in battles]
    elif ledger_dir:
        # 单账本回落：账本目形 battle-N/G-x → 仗根=父目，否则账本目自身
        ld = str(ledger_dir)
        root = (os.path.dirname(ld.rstrip(os.sep))
                if os.path.basename(ld.rstrip(os.sep)).startswith("G-")
                else ld)
        roots = [(os.path.basename(root.rstrip(os.sep)) or "主账本", root)]
    for bid, bdir in roots:
        gens = _gens(bdir)
        tl = _merged_timeline(bdir, gens)
        events = [_cell("timeline.tsv", c, "event") for _no, c in tl]
        approvals = [r for _k, r in _merge_by_id(bdir, gens, "approvals.tsv")]
        for no, c in tl:
            revert = _cell("timeline.tsv", c, "revert_cmd").strip()
            if not revert:
                continue
            ev = _cell("timeline.tsv", c, "event")
            if any(x == "revert:" + ev for x in events[no:]):
                continue
            if any(_cell("approvals.tsv", a, "decision") == "exempted"
                   and ev in _cell("approvals.tsv", a, "note")
                   for a in approvals):
                continue
            cmd_head = " ".join(revert.split()[:2])
            pending.append({"battle": bid, "row": no,
                            "ts": _cell("timeline.tsv", c, "timestamp"),
                            "actor": _cell("timeline.tsv", c, "actor"),
                            "phase": _cell("timeline.tsv", c, "phase"),
                            "event": ev, "command": revert,
                            "tool": revert.split()[0] if revert.split() else "",
                            "group_label": cmd_head})
        # 求助：battle 根 ask.md 非空（watchdog ask:human 通道同位）
        text = _read_text(os.path.join(bdir, "ask.md"))
        if text and text.strip():
            first = text.strip().splitlines()[0].strip()
            asks.append({"battle": bid, "question": first,
                         "detail_url": "/p/inbox"})
    pending.sort(key=lambda a: (a["ts"], a["battle"], a["row"]))
    asks.sort(key=lambda a: a["battle"])
    groups = {}
    for a in pending:
        g = groups.setdefault(a["group_label"],
                              {"label": a["group_label"], "count": 0,
                               "battles": []})
        g["count"] += 1
        if a["battle"] not in g["battles"]:
            g["battles"].append(a["battle"])
    group_list = sorted(groups.values(),
                        key=lambda g: (-g["count"], g["label"]))
    return pending, asks, group_list


# ---------------------------------------------------------------- 问四·消费 --

def _budget_view(battle_dir, gens, goal):
    """问四：budget.tsv 聚合 vs goals 帽三段（token;请求;小时）余量条。"""
    used = {"tokens": 0.0, "requests": 0.0, "hours": 0.0, "usd": 0.0}
    rows_n = 0
    for d in _read_dirs(battle_dir, gens):
        for r in _tsv_rows(os.path.join(d, "budget.tsv"), "budget.tsv"):
            rows_n += 1
            used["tokens"] += _to_num(_cell("budget.tsv", r, "token_delta"))
            used["requests"] += _to_num(_cell("budget.tsv", r, "requests_delta"))
            used["hours"] += _to_num(_cell("budget.tsv", r, "hours_delta"))
            used["usd"] += _to_num(_cell("budget.tsv", r, "dollars_delta"))
    parts = str(goal.get("budget") or "").split(";")
    caps = {"tokens": _cap_num(parts[0]) if len(parts) > 0 else 0.0,
            "requests": _cap_num(parts[1]) if len(parts) > 1 else 0.0,
            "hours": _cap_num(parts[2]) if len(parts) > 2 else 0.0}
    pct, over = {}, {}
    for k in ("tokens", "requests", "hours"):
        pct[k] = round(used[k] / caps[k] * 100.0, 1) if caps[k] > 0 else 0.0
        over[k] = bool(caps[k] > 0 and used[k] > caps[k])
    return {"rows_n": rows_n,
            "used": {k: (int(v) if v == int(v) else round(v, 2))
                     for k, v in used.items()},
            "cap": {k: (int(v) if v == int(v) else v) for k, v in caps.items()},
            "pct": pct, "over": over, "warn_pct": _WARN_PCT,
            "goal": {"target": goal.get("target") or "",
                     "objective": goal.get("objective") or "",
                     "budget_raw": goal.get("budget") or ""}}


# ---------------------------------------------------------------- 四问总装 --

def cockpit_view(ledger_dir=None, battles_dir=None, battle=None):
    """首页四问投影 → {battle, battles, q1_vulns, q2_live, q3_waiting, q4_budget}。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    gens = _gens(battle_dir) if battle_dir else []
    goal = _goal_of(battle_dir, gens)
    pending, asks, _groups = _scan_waiting(battles_dir, ledger_dir)
    return {
        "battle": ({"id": meta["id"], "n": meta["n"],
                    "goal": goal.get("id") or ""}
                   if meta else
                   {"id": os.path.basename(str(battle_dir or "")).rstrip("/") or
                    os.path.basename(str(ledger_dir or "")),
                    "n": None, "goal": goal.get("id") or ""}),
        "battles": battles,
        "q1_vulns": _vuln_leaderboard(battle_dir, gens, goal),
        "q2_live": _live_pool(battle_dir, gens),
        "q3_waiting": {"counts": {"pending_approvals": len(pending),
                                  "asks": len(asks)},
                       "pending_approvals": pending[:_TOP_N],
                       "asks": asks[:_TOP_N]},
        "q4_budget": _budget_view(battle_dir, gens, goal),
    }


# ---------------------------------------------------------------- 漏洞页 --

def findings_view(ledger_dir=None, battles_dir=None, battle=None):
    """漏洞页投影：全量漏洞+证据袋+上次验真+待复验队列位。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    gens = _gens(battle_dir) if battle_dir else []
    frows = _merge_by_id(battle_dir, gens, "findings.tsv")
    erows = _merge_by_id(battle_dir, gens, "E-index.tsv")
    evmap = {k: r for k, r in erows}
    assets = {k: r for k, r in _merge_by_id(battle_dir, gens, "assets.tsv")}
    goal = _goal_of(battle_dir, gens)
    tl = _merged_timeline(battle_dir, gens)

    # 版本组：pair_group → 同组 EV（按 observed_at,id 排=v1/v2/v3）
    pg = {}
    for eid, r in erows:
        g = _cell("E-index.tsv", r, "pair_group").strip()
        if g:
            pg.setdefault(g, []).append(eid)
    for g in pg:
        pg[g].sort(key=lambda e: (_cell("E-index.tsv", evmap[e], "observed_at"), e))

    def _versions(eid):
        r = evmap.get(eid)
        if r is None:
            return [{"ver": 1, "artifact": "", "observed_at": "", "title": ""}]
        g = _cell("E-index.tsv", r, "pair_group").strip()
        members = pg.get(g, [eid]) if g else [eid]
        out = []
        for i, m in enumerate(members, 1):
            mr = evmap.get(m)
            out.append({"ver": i,
                        "artifact": _cell("E-index.tsv", mr, "artifact_path")
                        if mr else "",
                        "observed_at": _cell("E-index.tsv", mr, "observed_at")
                        if mr else "",
                        "title": _cell("E-index.tsv", mr, "title") if mr else ""})
        return out

    # 战场钟+每 EV 末次验真时刻（replay 两形，api_v2_retest 同律）
    now_s = None
    last_by_ev = {}
    for _no, c in tl:
        ts = _cell("timeline.tsv", c, "timestamp")
        es = _epoch(ts)
        if es is not None and (now_s is None or es > now_s):
            now_s = es
        ev_txt = _cell("timeline.tsv", c, "event")
        for pat in (_REPLAY_PAT, _REPLAY2_PAT):
            m = pat.search(ev_txt)
            if m:
                prev = last_by_ev.get(m.group(1))
                if prev is None or ts > prev:
                    last_by_ev[m.group(1)] = ts

    items = []
    for fid, r in frows:
        status = _cell("findings.tsv", r, "status")
        expl = _cell("findings.tsv", r, "exploitation_status")
        ev_primary = [e for e in str(_cell("findings.tsv", r, "evidence_ids")
                                    or "").split(";") if e.strip()]
        ev_control = [e for e in str(_cell("findings.tsv", r,
                                           "control_evidence_ids")
                                     or "").split(";") if e.strip()]
        seen, bag = set(), []
        for role, lst in (("证实", ev_primary), ("对照", ev_control)):
            for e in lst:
                if e in seen:
                    continue
                seen.add(e)
                bag.append({"ev_id": e, "role": role,
                            "title": _cell("E-index.tsv", evmap[e], "title")
                            if e in evmap else "",
                            "versions": _versions(e)})
        ev_all = list(seen)
        last_at = ""
        for e in ev_all:
            t = last_by_ev.get(e, "")
            if t and (not last_at or t > last_at):
                last_at = t
        since_days = None
        if last_at and now_s is not None:
            ls = _epoch(last_at)
            if ls is not None:
                since_days = max(0, int((now_s - ls) // 86400))
        ast_id = _cell("findings.tsv", r, "affected_asset_id")
        if ast_id and ast_id in assets:
            where = _cell("assets.tsv", assets[ast_id], "value") or ast_id
        elif ast_id:
            where = ast_id
        elif goal.get("target"):
            where = goal["target"]
        else:
            where = "（未登记位置）"
        items.append({
            "id": fid, "title": _cell("findings.tsv", r, "title"),
            "impact": _cell("findings.tsv", r, "impact") or "低",
            "where": where,
            "confidence": _cell("findings.tsv", r, "confidence"),
            "status": status, "exploitation_status": expl,
            "created": _cell("findings.tsv", r, "created"),
            "evidence_bag": bag,
            "last_verified_at": last_at,
            "since_last_days": since_days,
            "since_last_text": (_dur_text(since_days)
                                if since_days is not None else "未复测"),
            "replayable": bool(ev_all),
            "queue_pos": 0, "detail_url": "/p/finding-detail?id=" + fid,
            "retest_url": "/p/retest",
        })
    # 待复验队位：可复测先列，最久未验先列（api_v2_retest 队序同律）
    ordered = sorted((f for f in items if f["replayable"]),
                     key=lambda f: (f["last_verified_at"] or f["created"],
                                    f["id"]))
    for i, f in enumerate(ordered, 1):
        f["queue_pos"] = i
    items.sort(key=lambda f: (0 if (f["exploitation_status"] == "verified"
                                    and f["status"] == "active") else
                              1 if f["status"] == "active" else 2,
                              _IMPACT_RANK.get(f["impact"], 9),
                              f["created"], f["id"]))
    raw_rows = 0
    for d in _read_dirs(battle_dir, gens):
        raw_rows += len(_tsv_rows(os.path.join(d, "findings.tsv"),
                                  "findings.tsv"))
    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else
                   {"id": os.path.basename(str(battle_dir or "")).rstrip("/"),
                    "n": None}),
        "battles": battles,
        # total=同 id 后代胜合并后在册数；raw_rows=盘上行数（含历史重写行）
        "counts": {"total": len(frows),
                   "raw_rows": raw_rows,
                   "active": sum(1 for f in items if f["status"] == "active"),
                   "verified_active": sum(
                       1 for f in items
                       if f["exploitation_status"] == "verified"
                       and f["status"] == "active")},
        "items": items,
    }


# ---------------------------------------------------------------- 知识库页 --

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def knowledge_view():
    """知识库页投影：打法卡+哨兵规则+蒸馏草稿（knowledge/ 真文件只读消费；
    蒸馏舰在飞——staging 行落即显，本层零写入零缓存）。"""
    root = _repo_root()
    patterns = []
    idx = os.path.join(root, "knowledge", "cp-index.tsv")
    lines = [l for l in (_read_text(idx) or "").splitlines() if l.strip()]
    for l in lines[1:]:
        cols = l.split("\t")
        patterns.append({"id": cols[0] if cols else "",
                         "title": cols[1] if len(cols) > 1 else "",
                         "source_id": cols[2] if len(cols) > 2 else "",
                         "source_topic": cols[3] if len(cols) > 3 else "",
                         "status": cols[4] if len(cols) > 4 else "",
                         "updated": cols[5] if len(cols) > 5 else ""})
    sentinels = []
    sp = os.path.join(root, "knowledge", "engineering", "sentinels-v1.tsv")
    slines = [l for l in (_read_text(sp) or "").splitlines()
              if l.strip() and not l.startswith("#")]
    for l in slines[1:]:
        cols = l.split("\t")
        sentinels.append({"id": cols[0] if cols else "",
                          "signal": cols[1] if len(cols) > 1 else "",
                          "judge": cols[2] if len(cols) > 2 else "",
                          "action": cols[3] if len(cols) > 3 else "",
                          "note": cols[4] if len(cols) > 4 else ""})
    staging_rows = []
    stp = os.path.join(root, "knowledge", "staging", "staging.tsv")
    stlines = [l for l in (_read_text(stp) or "").splitlines() if l.strip()]
    for l in stlines[1:]:
        cols = l.split("\t")
        staging_rows.append({"staging_id": cols[0] if cols else "",
                             "page_id": cols[1] if len(cols) > 1 else "",
                             "class": cols[2] if len(cols) > 2 else "",
                             "title": cols[3] if len(cols) > 3 else "",
                             "status": cols[5] if len(cols) > 5 else ""})
    intake = os.path.join(root, "knowledge", "staging", "gensift-intake")
    intake_files = 0
    for _dir, _sub, files in os.walk(intake):
        intake_files += len(files)
    return {
        "patterns": patterns, "sentinels": sentinels,
        "staging": {"rows": staging_rows,
                    "pending_count": sum(1 for r in staging_rows
                                         if r["status"] != "approved"),
                    "intake_files": intake_files},
        "counts": {"patterns": len(patterns), "sentinels": len(sentinels),
                   "staging_pending": sum(1 for r in staging_rows
                                          if r["status"] != "approved")},
        "techniques_url": "/p/techniques",
    }


# ---------------------------------------------------------------- 收件箱 --

def inbox_view(ledger_dir=None, battles_dir=None):
    """收件箱投影：待审批+求助+批量同类聚合（按「等久了」排，同类一票）。"""
    pending, asks, groups = _scan_waiting(battles_dir, ledger_dir)
    return {"pending_approvals": pending, "asks": asks, "groups": groups,
            "counts": {"pending_approvals": len(pending),
                       "asks": len(asks),
                       "groups": len(groups)},
            "approval_center_url": "/p/approval-center"}


# ---------------------------------------------------------------- 路由层 --

def _cockpit_route(query, ledger_dir=None, battles_dir=None):
    try:
        return 200, cockpit_view(ledger_dir=ledger_dir, battles_dir=battles_dir,
                                 battle=query.get("battle"))
    except ValueError as e:
        return 422, {"error": str(e)}


def _findings_route(query, ledger_dir=None, battles_dir=None):
    try:
        return 200, findings_view(ledger_dir=ledger_dir,
                                  battles_dir=battles_dir,
                                  battle=query.get("battle"))
    except ValueError as e:
        return 422, {"error": str(e)}


def _knowledge_route(query, ledger_dir=None, battles_dir=None):
    return 200, knowledge_view()


def _inbox_route(query, ledger_dir=None, battles_dir=None):
    return 200, inbox_view(ledger_dir=ledger_dir, battles_dir=battles_dir)


ROUTES[ROUTE_COCKPIT] = _cockpit_route
ROUTES[ROUTE_FINDINGS] = _findings_route
ROUTES[ROUTE_KNOWLEDGE] = _knowledge_route
ROUTES[ROUTE_INBOX] = _inbox_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """/api/v2/cockpit* 四路由分发 → (status, payload) | None（非本域）。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
