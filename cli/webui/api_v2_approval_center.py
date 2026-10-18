# -*- coding: utf-8 -*-
"""api_v2_approval_center（T7·P8-P18 审批中心全局页）——跨任务待审/已决只读
投影，路由 /api/v2/approval-center.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_approval_center.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。

卡片形态=复用 T3 拦截审批页签（api_v2_guard 同形：风险级徽章/工具/命令全文
mono/AI 预审「仅供参考」/批准·拒绝·改参三钮）。风险词表与 AI 预审文案单源=
api_v2_guard（import 复用 _risk_of/_tool_of/layer_of，不造第二份词表——舰间
只读复用，tests 钉形防漂移）。

数据单源（跨任务聚合，判定同源）：
  待审队列 = 各任务 timeline 合并行 revert_cmd 非空且未核销（后续无
             revert:<原事件> 行）未豁免（approvals 无 decision=exempted 且
             note 含原事件文本）——query_cmds._replay_status 同判定；
             按 command_hash 去重留最新行（审批绑定命令哈希不绑定行）；
  已决历史 = approvals.tsv 全行（带所属任务）；
  拦截流水 = guard-reject/tools-reject/gate-fail/egress 行计数（分层词表同源）；
  写入通道 = 既有 /api/approval 只作用于服务端 ledger_dir 对齐的那一个任务
             （approval_aligned_battle——realpath 判同）；其余任务卡=只读展示
             +切任务提示（读面铁律：本层零写）。
"""
import hashlib
import os

from ledger import core
from ledger.session_view import list_battles
from . import api_v2_guard as _guard

ROUTE_CENTER = "/api/v2/approval-center.json"
ROUTES = {ROUTE_CENTER: None}                         # 尾部赋真身（前向引用）

_TL = core.TABLES["timeline.tsv"]
_TLE = {f: i for i, f in enumerate(_TL)}
_AP = core.TABLES["approvals.tsv"]
_APE = {f: i for i, f in enumerate(_AP)}
_RECENT_TAIL = 12


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
    import re
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


def _merged_timeline(battle_dir, gens):
    """全代 timeline 合并 → [(全局行号, cols)]。"""
    out = []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), len(_TL)):
            out.append(cols)
    return list(enumerate(out, 1))


# ------------------------------------------------------------------ 投影 --

def approval_center_view(battles_dir=None, ledger_dir=None, q=None):
    """审批中心投影 → {q, battles, counts, pending[], recent[], flow[],
    approval_aligned_battle}。只读零写入。

    pending 卡=T3 形+battle{ id, n }+writable（仅对齐任务=true）；
    q=子串过滤（命令/事件/任务 id，大小写不敏感）。
    """
    battles = list_battles(battles_dir)
    root = str(battles_dir or "")
    aligned = ""
    try:
        me = os.path.realpath(str(ledger_dir or ""))
    except OSError:
        me = ""
    pending_by_hash = {}
    flow = []
    recent = []
    for meta in battles:
        bid = meta["id"]
        battle_dir = os.path.join(root, bid)
        gens = _gens(battle_dir)
        timeline = _merged_timeline(battle_dir, gens)
        approvals = [cols for _k, cols in _merge_by_id(battle_dir, gens, "approvals.tsv")]
        events = [cols[_TLE["event"]] for _no, cols in timeline]

        if not aligned and me:
            gd = os.path.join(battle_dir, gens[-1]) if gens else battle_dir
            try:
                if gd and os.path.realpath(gd) == me:
                    aligned = bid
            except OSError:
                pass

        for no, cols in timeline:
            revert_cmd = cols[_TLE["revert_cmd"]].strip()
            ev = cols[_TLE["event"]]
            if revert_cmd:
                reverted = any(x == "revert:" + ev for x in events[no:])
                exempted = any(c[_APE["decision"]] == "exempted" and ev in c[_APE["note"]]
                               for c in approvals)
                if not (reverted or exempted):
                    chash = hashlib.sha256(revert_cmd.encode("utf-8")).hexdigest()
                    risk, basis = _guard._risk_of(ev, revert_cmd)
                    pending_by_hash[chash] = {
                        "row": no, "ts": cols[_TLE["timestamp"]],
                        "actor": cols[_TLE["actor"]], "phase": cols[_TLE["phase"]],
                        "event": ev, "command": revert_cmd,
                        "command_hash": chash, "tool": _guard._tool_of(ev),
                        "risk": risk, "risk_basis": basis,
                        "ai_note": ("AI 预审（仅供参考）：风险=%s（%s）；命令哈希 %s… 已锚定"
                                    "%s 第 %d 行；批准/拒绝/改参由操作员终审，结果入链。"
                                    % (risk, basis, chash[:12], bid, no)),
                        "battle": {"id": bid, "n": meta["n"]},
                        "writable": bid == aligned,
                    }
            if _guard.layer_of(ev, cols[_TLE["actor"]]):
                flow.append({"row": no, "ts": cols[_TLE["timestamp"]],
                             "battle": bid,
                             "layer": _guard.layer_of(ev, cols[_TLE["actor"]]),
                             "event": ev[:120]})

        for cols in approvals:
            recent.append({
                "id": cols[_APE["id"]], "decision": cols[_APE["decision"]],
                "approver": cols[_APE["approver"]],
                "timestamp": cols[_APE["timestamp"]], "battle": bid,
            })

    pending = sorted(pending_by_hash.values(),
                     key=lambda x: (x["ts"], x["battle"]["id"], x["row"]))
    recent.sort(key=lambda d: (d["timestamp"], d["battle"], d["id"]))
    recent = recent[-_RECENT_TAIL:]

    if q:
        needle = str(q).strip().lower()
        if needle:
            pending = [c for c in pending if needle in (
                "%s %s %s %s" % (c["command"], c["event"],
                                 c["battle"]["id"], c["tool"])).lower()]

    flow_by_battle = {}
    for f in flow:
        b = flow_by_battle.setdefault(f["battle"], {"id": f["battle"], "flow": 0})
        b["flow"] += 1

    return {
        "q": q or "",
        "battles": battles,
        "counts": {
            "pending": len(pending),
            "by_risk": {"高": sum(1 for c in pending if c["risk"] == "高"),
                        "中": sum(1 for c in pending if c["risk"] == "中"),
                        "低": sum(1 for c in pending if c["risk"] == "低")},
            "battles_with_pending": len({c["battle"]["id"] for c in pending}),
            "flow": len(flow),
            "decisions": len(recent),
        },
        "pending": pending,
        "recent": recent,
        "flow": sorted(flow_by_battle.values(), key=lambda x: x["id"]),
        "approval_aligned_battle": aligned,
        "note": ("三钮写入走既有审批通道（仅对齐任务可写；其余任务卡=只读展示，"
                 "切换该任务后审批）。AI 预审=确定性词表推导，仅供参考。"),
    }


def _center_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = approval_center_view(battles_dir=battles_dir,
                                       ledger_dir=ledger_dir, q=query.get("q"))
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "审批中心参数无效: %s" % e}
    return 200, payload


ROUTES[ROUTE_CENTER] = _center_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
