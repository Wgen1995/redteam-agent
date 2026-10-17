# -*- coding: utf-8 -*-
"""api_v2_guard（T3·P5.8）——拦截审批页签只读投影，路由 /api/v2/guard.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_approval.py。

数据单源（spec §P5.8：approvals+guard 流水[timeline 过滤]）：
  待审队列 = revert_cmd 非空且未核销（后续无 revert:<原事件> 行）未豁免
             （approvals 无 decision=exempted 且 note 含原事件文本）的 timeline 行
             ——query_cmds._replay_status 同判定，跨代只读重实现；按 command_hash
             去重留最新行（审批绑定命令哈希不绑定行——重试同命令不重复占卡）；
             三钮写入走既有 /api/approval（页面 command_hash 连接取签名，本层零写）。
  四层流水 = timeline 拦截行分层：L1 账本级（gate-fail 阶段门/卡审批门）·
             L2 执行通道（guard-reject 门链/卡层门链）· L3 宿主 hook ·
             L4 egress 代理（2026-09-20 融合档 §4 四层纵深同taxonomy）。
  扩展审批分支 = assets 范围外行（分域异步门：范围外新资产挂起，主战在已授权域
             继续）+scope 修订行接入判定（amendment matcher 命中=已接入）+
             主战继续提示（全停仅限法务红线：授权窗口到期/急停/预算硬顶）。

风险分级与 AI 预审=确定性词表推导（单源于此），预审文案恒标「仅供参考」，
批准/拒绝/改参由操作员终审——AI 不上桌决策（宪法读面铁律）。
"""
import hashlib
import os
import re

from ledger import core
from ledger.session_view import list_battles

ROUTE_GUARD = "/api/v2/guard.json"
ROUTES = {ROUTE_GUARD: None}                         # 尾部赋真身（前向引用）

_CARD_PAT = re.compile(r"card=(\S+)")
_RISK_HIGH = ("egress", "外发", "oob", "l3", "rm -f", "drop ", "mkfs", "破坏", "越权")
_RISK_MID = ("deny", "l2", "upload", "inject", "写操作", "token")
_FLOW_VERBS = ("guard-reject", "tools-reject", "gate-fail", "egress")
_MAIN_HINT = ("分域异步门：范围外新资产自动挂起扩展审批，主战在已授权域继续零停顿；"
              "全停仅限法务红线（授权窗口到期/急停/预算硬顶触底）。")


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_tsv_rows(path, nfields):
    text = _read_text(path)
    if text is None:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        out.append((cols + [""] * nfields)[:nfields] if len(cols) < nfields else cols)
    return out


def _gens(battle_dir):
    """G-* 子目自然序（G-r2<G-r10；server._latest_gen 同律）；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


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


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir) —— 有战用战，无战回落主账本。"""
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return [], None, str(ledger_dir or "")
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return battles, None, None
    return battles, picked, os.path.join(root, picked["id"])


def _read_dirs(battle_dir, gens):
    if gens:
        return [os.path.join(battle_dir, g) for g in gens]
    return [battle_dir] if battle_dir else []


def _merged_timeline(battle_dir, gens):
    """全代 timeline 合并 → [(全局行号, cols)]。"""
    nf = len(core.TABLES["timeline.tsv"])
    out = []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), nf):
            out.append(cols)
    return list(enumerate(out, 1))


def _merge_by_id(battle_dir, gens, tname):
    nf = len(core.TABLES[tname])
    by_id, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, tname), nf):
            key = cols[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = cols
    return [(k, by_id[k]) for k in order]


# ---------------------------------------------------------------- 分类单源 --

def layer_of(event, actor):
    """拦截行 → 四层之一（账本/执行通道/宿主 hook/egress 代理）；非拦截=空。"""
    ev = (event or "").strip()
    a = (actor or "").strip()
    first = ev.split(" ", 1)[0]
    if a == "egress" or first.startswith("egress"):
        return "L4·egress 代理"
    if a == "hook" or first.startswith("hook"):
        return "L3·宿主 hook"
    if ev.startswith("tools-reject"):
        return "L1·账本级" if "approval-required" in ev else "L2·执行通道"
    if ev.startswith("guard-reject"):
        return "L2·执行通道"
    if first.startswith("gate-fail"):
        return "L1·账本级"
    return ""


def _risk_of(event, revert_cmd):
    """(风险级, 依据) —— 确定性词表推导；单源于此。"""
    text = (event + " " + (revert_cmd or "")).lower()
    for k in _RISK_HIGH:
        if k in text:
            return "高", "命中高危关键词 %s" % k
    for k in _RISK_MID:
        if k in text:
            return "中", "命中中危关键词 %s" % k
    return "低", "未命中风险词表"


def _tool_of(event):
    m = _CARD_PAT.search(event or "")
    if m:
        return m.group(1)
    first = (event or "").split(" ")
    return first[0] if first and first[0] else "账本事件"


def _flow_rule(event):
    ev = (event or "").strip()
    parts = ev.split(" ")
    if ev.startswith("guard-reject ") and len(parts) > 1:
        return parts[1]
    if ev.startswith("tools-reject"):
        return "卡层门链"
    return parts[0] if parts and parts[0] else ""


def _flow_command(event):
    """被拦命令抽取：cmd=到行尾/host=token/其余=规则段原文。"""
    ev = (event or "").strip()
    i = ev.find("cmd=")
    if i >= 0:
        return ev[i + 4:]
    i = ev.find("host=")
    if i >= 0:
        return ev[i + 5:].split(" ", 1)[0]
    m = _CARD_PAT.search(ev)
    if m:
        return m.group(1)
    parts = ev.split(" ", 2)
    return parts[2] if len(parts) > 2 else ev


# ------------------------------------------------------------------ 投影 --

def guard_view(battles_dir=None, battle=None, ledger_dir=None):
    """拦截审批页签投影 → {battle, battles, goal, approval_aligned, counts,
    pending[], flow[], recent[], extended{items,amendments,hint}}。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    gens = _gens(battle_dir) if battle_dir else []
    goal_dir = (os.path.join(battle_dir, gens[-1]) if gens else str(battle_dir or ""))
    goal = gens[-1] if gens else os.path.basename(os.path.normpath(goal_dir))

    tle = {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}
    timeline = _merged_timeline(battle_dir, gens)

    # —— 待审队列：revert 未核销未豁免，按 command_hash 去重留最新 ——
    approvals = [cols for _k, cols in _merge_by_id(battle_dir, gens, "approvals.tsv")]
    tap = {f: i for i, f in enumerate(core.TABLES["approvals.tsv"])}
    events = [cols[tle["event"]] for _no, cols in timeline]
    pending_by_hash = {}
    for no, cols in timeline:
        revert_cmd = cols[tle["revert_cmd"]].strip()
        ev = cols[tle["event"]]
        if not revert_cmd:
            continue
        reverted = any(x == "revert:" + ev for x in events[no:])
        exempted = any(cols2[tap["decision"]] == "exempted" and ev in cols2[tap["note"]]
                       for cols2 in approvals)
        if reverted or exempted:
            continue
        chash = hashlib.sha256(revert_cmd.encode("utf-8")).hexdigest()
        risk, basis = _risk_of(ev, revert_cmd)
        pending_by_hash[chash] = {
            "row": no, "ts": cols[tle["timestamp"]], "actor": cols[tle["actor"]],
            "phase": cols[tle["phase"]], "event": ev, "command": revert_cmd,
            "command_hash": chash, "tool": _tool_of(ev),
            "risk": risk, "risk_basis": basis,
            "ai_note": ("AI 预审（仅供参考）：风险=%s（%s）；命令哈希 %s… 已锚定账本"
                        "第 %d 行；批准/拒绝/改参由操作员终审，结果入链。"
                        % (risk, basis, chash[:12], no)),
        }
    pending = sorted(pending_by_hash.values(), key=lambda x: (x["ts"], x["row"]))

    # —— 四层拦截流水：guard-reject / tools-reject / gate-fail / egress ——
    flow = []
    for no, cols in timeline:
        ev = cols[tle["event"]]
        actor = cols[tle["actor"]]
        if not (ev.startswith(_FLOW_VERBS) or layer_of(ev, actor)):
            continue
        layer = layer_of(ev, actor)
        if not layer:
            continue
        flow.append({
            "row": no, "ts": cols[tle["timestamp"]], "layer": layer,
            "rule": _flow_rule(ev), "command": _flow_command(ev),
            "result": "未过（阶段门）" if ev.startswith("gate-fail") else "拦截",
        })

    # —— 扩展审批分支：范围外资产挂起 + 修订接入判定 + 主战继续提示 ——
    ta = {f: i for i, f in enumerate(core.TABLES["assets.tsv"])}
    tsc = {f: i for i, f in enumerate(core.TABLES["scope.tsv"])}
    amendments = []
    for _sid, cols in _merge_by_id(battle_dir, gens, "scope.tsv"):
        if cols[tsc["amendment_of"]].strip():
            amendments.append({
                "id": cols[0], "kind": cols[tsc["kind"]],
                "matcher": cols[tsc["matcher"]],
                "amendment_of": cols[tsc["amendment_of"]],
                "note": cols[tsc["note"]], "created": cols[tsc["created"]],
            })

    def _linked(value):
        for am in amendments:
            m = am["matcher"]
            if m and (value == m or value.endswith("." + m)):
                return True
        return False

    ext_items = []
    for _aid, cols in _merge_by_id(battle_dir, gens, "assets.tsv"):
        if cols[ta["in_scope"]].strip() != "out_of_scope":
            continue
        value = cols[ta["value"]].strip()
        ext_items.append({
            "id": cols[0], "type": cols[ta["type"]], "value": value,
            "created": cols[ta["created"]],
            "status": "已接入" if _linked(value) else "挂起",
        })
    ext_items.sort(key=lambda x: (x["status"] != "挂起", x["created"], x["id"]))

    try:
        aligned = (os.path.realpath(goal_dir) == os.path.realpath(str(ledger_dir or ""))
                   if goal_dir else False)
    except OSError:
        aligned = False

    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles, "goal": goal, "approval_aligned": aligned,
        "counts": {
            "pending": len(pending), "flow": len(flow),
            "extended_pending": sum(1 for x in ext_items if x["status"] == "挂起"),
            "extended_linked": sum(1 for x in ext_items if x["status"] == "已接入"),
        },
        "pending": pending, "flow": flow,
        "recent": [{"id": c[0], "decision": c[tap["decision"]],
                    "approver": c[tap["approver"]], "timestamp": c[tap["timestamp"]]}
                   for c in approvals[-5:]],
        "extended": {"items": ext_items, "amendments": amendments,
                     "hint": _MAIN_HINT},
    }


def guard_route(query, ledger_dir=None, battles_dir=None):
    """路由层：ValueError=422；error 形=404；正常=200。"""
    try:
        payload = guard_view(battles_dir=battles_dir, battle=query.get("battle"),
                             ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_GUARD] = guard_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
