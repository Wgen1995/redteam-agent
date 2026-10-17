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
