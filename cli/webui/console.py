# -*- coding: utf-8 -*-
"""webui console（W6 控制台批）——五页只读投影：总览/实时动态/攻击链路/发现/审批。

投影律（同 snapshot/projections）：本模块只读零写入、禁 datetime.now（输出确定性）、
Python 3.9 纯 stdlib；文案律=docs/design/ui-copy-standard-v1.md——上屏值一律人话：
执行阶段名（授权确认→…→沉淀）/验证状态（已验证/待验证/已失效）/智能体/预算预警线。

数据单源（不虚构）：token 经济学=timeline `usage:` 真行；预算=预算树上卷
（query_cmds.budget_tree）；活动流/事件流=timeline 尾部真行；阶段灯=phases_engine
只读 status；收敛四条件=converge_state 同源四件套；图谱节点/边=viz_render 表序；
帧=timeline 行号（节点入场帧=该 id 首次出现的行）；发现验证状态=exploitation_status
事件溯源最新；CVSS=描述/复现/证据原文中在场向量经 ledger.cvss 实算（缺向量=未评定）。
"""
import os
import re

_ID_RE = re.compile(r"\b(?:G|S|INT|AST|CRED|F|FD|EV|E)-[A-Za-z0-9\-]+")

from ledger import core, query_cmds as _qc, viz_render
from ledger import session_view as _sv
from . import snapshot as _snap

# ---- ui-copy-standard-v1 上屏名词（执行阶段名/验证状态）--------------------
PHASE_NAMES = {"P0": "授权确认", "P1": "范围检查", "P2": "预算", "P3": "执行",
               "P4": "复测", "P5": "报告", "P5.5": "签发", "P6.0": "清理",
               "P6": "沉淀"}
PHASE_ORDER = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")
VERIFY_STATES = {"verified": "已验证", "suspected": "待验证",
                 "ruled_out": "已失效"}
ACTIVITY_TAIL = 12
USAGE_NOTE = ("口径: 网关侧 usage 真行外挂统计 · 不采信引擎内建计量 · "
              "无 usage 行=尚无真实用量记录")

_USAGE_RE = re.compile(r"^usage:\s*(.*)$")
_KV_RE = re.compile(r"(\w+)=([^\s]+)")
_CVSS_RE = re.compile(r"CVSS:3\.1/AV:([NALP])/AC:([LH])/PR:([NLH])/UI:([NR])"
                      r"/S:([UC])/C:([HLN])/I:([HLN])/A:([HLN])")


def _tl_index():
    return {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}


def _latest_rows(s, t):
    """事件溯源：同 id 后行覆盖前行（dict 保文件序——确定性）。"""
    out = {}
    for r in s.rows(t):
        out[r[0]] = r
    return out


def _usage_rows(s):
    """timeline usage: 真行 → [{run, tokens, est_tokens, ts}]（契约 15 §6 形态）。"""
    idx = _tl_index()
    out = []
    for r in s.rows("timeline.tsv"):
        m = _USAGE_RE.match(r[idx["event"]].strip())
        if not m:
            continue
        kv = dict(_KV_RE.findall(m.group(1)))
        try:
            tokens = int(kv.get("tokens", 0))
            est = int(kv.get("est_tokens", 0))
        except ValueError:
            continue
        out.append({"run": kv.get("run", ""), "tokens": tokens,
                    "est_tokens": est, "ts": r[idx["timestamp"]]})
    return out


def _battles_view(battles_dir):
    """任务清单（battle 目录实勘）：[{id, n, target, timeline_rows}]。"""
    out = []
    for b in _sv.list_battles(battles_dir):
        home = os.path.join(battles_dir, b["id"])
        gd = _latest_gen(home)
        target, rows = "", 0
        if gd:
            try:
                grows = core.Session(gd).rows("goals.tsv")
                if grows:
                    gi = core.TABLES["goals.tsv"].index("target")
                    target = grows[0][gi]
                with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
                    rows = sum(1 for _ in f)
            except OSError:
                pass
        out.append({"id": b["id"], "n": b["n"], "target": target,
                    "timeline_rows": rows})
    return out


def _latest_gen(home):
    """battle 目录内最新代目录（server._latest_gen 同式；G-r9 < G-r43）。"""
    def key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    try:
        gens = [d for d in os.listdir(home)
                if d.startswith("G-") and os.path.isdir(os.path.join(home, d))]
    except OSError:
        return None
    return os.path.join(home, sorted(gens, key=key)[-1]) if gens else None


def _node_count(s):
    return sum(len(_latest_rows(s, t)) for t, _p in viz_render.NODE_TABLES)


def overview_view(goal_dir, battles_dir, tail=ACTIVITY_TAIL):
    """总览页投影：任务卡+四卡+token 经济学+活动流+任务清单（只读真数）。"""
    s = core.Session(goal_dir)
    grows = s.rows("goals.tsv")
    gi = {f: i for i, f in enumerate(core.TABLES["goals.tsv"])}
    goal = {"id": grows[0][0] if grows else "",
            "target": grows[0][gi["target"]] if grows else "",
            "objective": grows[0][gi["objective"]] if grows else ""}
    fd = _qc.latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])
    fi = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
    states = [r[fi["exploitation_status"]].strip() for r in fd.values()]
    usage = _usage_rows(s)
    tl = s.rows("timeline.tsv")
    return {
        "goal": goal,
        "cards": {
            "verified_findings": sum(1 for x in states if x == "verified"),
            "findings_total": len(states),
            "graph_nodes": _node_count(s),
            "evidence_cards": len(s.rows("E-index.tsv")),
            "budget": _snap.budget_view(s),
            "timeline_rows": len(tl),
        },
        "token_usage": {
            "runs": usage,
            "total_tokens": sum(u["tokens"] for u in usage),
            "total_est_tokens": sum(u["est_tokens"] for u in usage),
            "note": USAGE_NOTE,
        },
        "activity": [_snap.row_to_event(r) for r in tl[-tail:]],
        "battles": _battles_view(battles_dir),
        "phase_names": PHASE_NAMES,
    }

def live_view(goal_dir, battles_dir, tail=ACTIVITY_TAIL):
    """实时动态页投影：九阶段灯+预算烧速+收敛四条件+事件流（全部真推导）。"""
    s = core.Session(goal_dir)
    raw = _snap.phases_status(goal_dir)                 # phases_engine 只读 status
    phases = [{"id": pid, "name": PHASE_NAMES[pid],
               "result": raw.get(pid, "PENDING")} for pid in PHASE_ORDER]
    bi = {f: i for i, f in enumerate(core.TABLES["budget.tsv"])}
    cum_t = cum_r = 0.0
    series = []
    for r in s.rows("budget.tsv"):
        try:
            cum_t += float(r[bi["token_delta"]] or 0)
            cum_r += float(r[bi["requests_delta"]] or 0)
        except ValueError:
            pass
        series.append({"ts": r[bi["timestamp"]],
                       "token_delta": int(r[bi["token_delta"]] or 0),
                       "cum_tokens": int(cum_t), "cum_requests": int(cum_r)})
    budget = _snap.budget_view(s)
    budget["series"] = series
    gaps = _qc.matrix_gap_cells(s)
    facts_open = _qc.unconsumed_facts(s)
    intents_blocked = _qc.blocked_intents(s)
    over = _qc.budget_exhausted(s)
    conditions = [
        {"key": "matrix_gaps", "name": "测试矩阵空格清零",
         "ok": not gaps, "count": len(gaps)},
        {"key": "unconsumed_facts", "name": "无未消费事实",
         "ok": not facts_open, "count": len(facts_open)},
        {"key": "blocked_intents", "name": "无阻塞测试项",
         "ok": not intents_blocked, "count": len(intents_blocked)},
        {"key": "budget_exhausted", "name": "预算未穿顶",
         "ok": not over, "count": 1 if over else 0},
    ]
    state = _qc.converge_state(s)
    tl = s.rows("timeline.tsv")
    return {"phases": phases, "budget": budget,
            "convergence": {"state": state, "conditions": conditions},
            "events": [_snap.row_to_event(r) for r in tl[-tail:]],
            "timeline_rows": len(tl)}

# ---- 攻击链路（图例色=数据编码色，非界面装饰；帧=timeline 行号）-------------
NODE_COLORS = {"G": "#e8b34b", "INT": "#a78bfa", "AST": "#5aa9e6",
               "CRED": "#d4a017", "F": "#8b949f", "FD": "#e8635a",
               "EV": "#3ddc97"}
EDGE_KIND_CN = {"spawns": "生成", "yields": "得出", "derived_from": "推导自",
                "proves": "证明", "parent": "隶属于", "attack": "攻击路径",
                "cross_ref": "交叉引用", "evidences": "证据支撑",
                "supersedes": "取代", "scope-rel": "范围关系"}


def _born_rows(s):
    """timeline 行号 → 各 id 首次出现行（1 基）：真实入场帧（不虚构时刻）。"""
    idx = _tl_index()
    born = {}
    for no, r in enumerate(s.rows("timeline.tsv"), 1):
        ev = r[idx["event"]]
        for token in _ID_RE.findall(ev):
            if token not in born:
                born[token] = no
    return born


def graph_view(goal_dir, battles_dir):
    """攻击链路页投影：节点（含入场帧）+边+真实图例（7 节点型+10 边型）+帧数。"""
    from . import projections as _proj
    s = core.Session(goal_dir)
    tl = s.rows("timeline.tsv")
    frames = len(tl)
    born = _born_rows(s)
    base = _proj.graph_view(goal_dir)          # 富卡单源（num/badge/title/status）
    nodes = []
    for n in base["nodes"]:
        n2 = dict(n)
        n2["born_row"] = born.get(n["id"], frames)   # 无入场行=末帧（记录缺失诚实降级）
        n2["color"] = NODE_COLORS[n["kind"]]
        nodes.append(n2)
    born_by_id = {n["id"]: n["born_row"] for n in nodes}
    edges = []
    for e in base["edges"]:
        e2 = dict(e)
        sb = born_by_id.get(e["src"], frames)
        db = born_by_id.get(e["dst"], frames)
        e2["born_row"] = max(sb, db)            # 两端都到场边才在场
        edges.append(e2)
    node_kinds = [{"kind": k, "name": _proj.BADGES[k],
                   "color": NODE_COLORS[k]}
                  for _t, k in viz_render.NODE_TABLES]   # 元组=(表名, 前缀)
    edge_kinds = [{"kind": k, "name": EDGE_KIND_CN[k],
                   "color": _proj.EDGE_STYLES[k]["color"]}
                  for k in EDGE_KIND_CN]
    return {"nodes": nodes, "edges": edges,
            "node_kinds": node_kinds, "edge_kinds": edge_kinds,
            "edge_style": base["edge_style"],
            "timeline_rows": frames,
            "replay": {"frames": frames,
                        "note": "演变回放：回到任意历史时刻看攻击链路（帧=记录行号）"}}

# ---- 发现库（验证状态三态 + CVSS 实算 + 证据原文抽屉）-----------------------
_CVSS_SEV_CN = {"critical": "严重", "high": "高", "medium": "中",
                "low": "低", "none": "无"}


def _cvss_of(texts):
    """文本堆里找 CVSS:3.1 向量 → ledger.cvss 实算；缺向量=None（未评定）。"""
    from ledger import cvss as _cvss
    for text in texts:
        m = _CVSS_RE.search(text or "")
        if not m:
            continue
        av, ac, pr, ui, sc, c, i, a = m.groups()
        try:
            score = _cvss.base(av, ac, pr, ui, sc, c, i, a)
        except ValueError:
            continue
        return {"vector": m.group(0), "score": round(score, 1),
                "severity": _CVSS_SEV_CN[_cvss.severity(score)]}
    return None


def findings_view(goal_dir, battles_dir):
    """发现页投影：验证状态三态+CVSS+挂接证据原文（事件溯源最新，只读）。"""
    s = core.Session(goal_dir)
    fd = _qc.latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])
    fi = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
    ei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    ev_rows = {r[0]: r for r in s.rows("E-index.tsv")}   # 证据 id → 行
    findings = []
    for key in sorted(fd):
        r = fd[key]                       # latest_by 键=元组，行内取 id
        rid = r[fi["id"]]
        state = VERIFY_STATES.get(r[fi["exploitation_status"]].strip(),
                                  "待验证")
        ev_ids = [x for x in re.split(r"[;,\s]+",
                                      r[fi["evidence_ids"]] or "") if x]
        ev_ids += [eid for eid, e in ev_rows.items()
                   if e[ei["linked_finding"]] == rid and eid not in ev_ids]
        evid = []
        for eid in ev_ids:
            e = ev_rows.get(eid)
            if e is None:
                continue
            evid.append({"id": eid, "title": e[ei["title"]],
                         "request": e[ei["repro_command"]],
                         "response": e[ei["raw_excerpt"]]})
        texts = [r[fi["description_brief"]], r[fi["reproducible_steps"]]]
        texts += [e["request"] + "\n" + e["response"] for e in evid]
        findings.append({
            "id": rid, "title": r[fi["title"]],
            "verify_state": state,
            "impact": r[fi["impact"]],
            "confidence": r[fi["confidence"]],
            "vuln_ref": r[fi["vuln_ref"]],
            "asset": r[fi["affected_asset_id"]],
            "created": r[fi["created"]],
            "description": r[fi["description_brief"]],
            "steps": r[fi["reproducible_steps"]],
            "cvss": _cvss_of(texts),
            "evidence": evid,
        })
    states = {v: sum(1 for f in findings if f["verify_state"] == v)
              for v in ("已验证", "待验证", "已失效")}
    return {"findings": findings, "total": len(findings),
            "states": states, "state_names": list(VERIFY_STATES.values())}
