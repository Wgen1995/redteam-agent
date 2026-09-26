# -*- coding: utf-8 -*-
"""tanyin-report 聚合器（批次 6 T12）——13 表→聚合投影（铁律 7「确定性投影」面）。

投影键（计划 T12 冻结，T13/14/15/17 消费）：
- goal              goals.tsv 末行全列（授权目标）；
- scope_summary     include/exclude/oob/account-grant 计数（amendment 生效行口径）+链头；
- findings          active finding 投影 [{id,title,tech_sev,biz_impact,replay_state,
                    asset,verified}]——verified=exploitation_status==verified（重放门口径）；
                    replay_state=timeline 重放事件末值三态映射 verified/env-diff/unverified；
- matrix            filled/empty/gaps 列表（latest 行键口径，空格=终态门分母）；
- coverage          intents open/closed + 九门通过集（gate_exit_seq）；
- budget_terminal   normal|exhausted（query_cmds.budget_exhausted 单源——终态 B 判据字段）；
- tier_disclosure   timeline `tier=` 事件末值+goals.guard_tier+egress 运行时工件披露；
- limits            覆盖度局限性声明输入（空矩阵格清单+unverified 清单）。

确定性：零墙钟零 LLM，同输入两跑逐字节一致（aggregate(goal_dir, ts) 的 ts 为调用面
保留参数——签发门 issued_at 判定用，不入投影）。缺任一表=EnvironmentError（CLI exit 2
ENV，非门禁 FAIL）。列名一律 TABLES[t].index 取（零硬编码列号）。
报告面 status 过滤口径：仅 status==active 进 findings（R-T12-1，见 HANDOFF）；"" 历史
行不进报告。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import query_cmds  # noqa: E402
from ledger.check_cmds import REPLAY_EVENT  # noqa: E402  重放事件形态单源
from ledger.core import GATE_EXIT_EVENT, Session  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

PROJECTION_KEYS = ("goal", "scope_summary", "findings", "matrix", "coverage",
                   "budget_terminal", "tier_disclosure", "limits")
_TRI = {"VERIFIED": "verified", "REPAIRED": "env-diff", "REJECTED": "unverified"}
_OPEN = {"candidate", "pending", "active"}
_CLOSED = {"done", "rejected", "blocked", "deferred"}
_TIER_RE = re.compile(r'tier[=:]\s*"?([A-Za-z0-9.+-]+)')
def _mv(s):
    return [x for x in (s or "").split(";") if x]


def _idx(t, col):
    return TABLES[t].index(col)


def _cell(t, r, col):
    return r[_idx(t, col)]


def _require_tables(goal_dir):
    missing = [t for t in TABLES if not os.path.isfile(os.path.join(goal_dir, t))]
    if missing:
        raise EnvironmentError("13 表缺（聚合前置，缺表=ENV 2）: " + ", ".join(missing))


def _mv_cells(t, r, col):
    return _mv(_cell(t, r, col))


def _project_goal(s):
    rows = s.rows("goals.tsv")
    return dict(zip(TABLES["goals.tsv"], rows[-1])) if rows else {}


def _project_scope(s):
    rows = s.rows("scope.tsv")
    superseded = {_cell("scope.tsv", r, "amendment_of") for r in rows
                  if _cell("scope.tsv", r, "amendment_of").strip()}
    eff = [r for r in rows if _cell("scope.tsv", r, "id") not in superseded]
    counts = {"include": 0, "exclude": 0, "oob": 0, "account-grant": 0}
    for r in eff:
        k = _cell("scope.tsv", r, "kind")
        if k in counts:
            counts[k] += 1
    heads = sorted(_cell("scope.tsv", r, "id") for r in eff)
    return {"counts": counts, "amendment_heads": heads}


def _replay_states(s):
    """timeline 重放事件按序末值：{引用 id: VERIFIED|REPAIRED|REJECTED}。"""
    out = {}
    ev_i = _idx("timeline.tsv", "event")
    for r in s.rows("timeline.tsv"):
        m = REPLAY_EVENT.match(r[ev_i])
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _project_findings(s):
    latest = query_cmds.latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])
    replay = _replay_states(s)
    out = []
    for key, r in sorted(latest.items()):
        if _cell("findings.tsv", r, "status") != "active":
            continue
        ev_ids = _mv_cells("findings.tsv", r, "evidence_ids") + _mv_cells(
            "findings.tsv", r, "control_evidence_ids")
        rids = [_cell("findings.tsv", r, "id")] + ev_ids
        state = next((replay[x] for x in rids if x in replay), None)
        out.append({
            "id": _cell("findings.tsv", r, "id"),
            "title": _cell("findings.tsv", r, "title"),
            "tech_sev": _cell("findings.tsv", r, "confidence"),
            "biz_impact": _cell("findings.tsv", r, "impact"),
            "replay_state": _TRI.get(state, "unverified"),
            "asset": _cell("findings.tsv", r, "affected_asset_id"),
            "verified": _cell("findings.tsv", r, "exploitation_status") == "verified",
        })
    return out


def _project_matrix(s):
    latest = query_cmds.latest_matrix(s)
    filled, empty = [], []
    for key in sorted(latest):
        r = latest[key]
        st = _cell("matrix.tsv", r, "state").strip()
        if st:
            filled.append({"attack_surface": key[0], "vuln_class": key[1],
                           "state": st})
        else:
            empty.append(key)
    gaps = [k[0] + "/" + k[1] for k in empty]
    return {"filled": filled, "empty": empty, "gaps": gaps}


def _project_coverage(s):
    latest = query_cmds.latest_intents(s)
    open_ids, closed_ids = [], []
    for key, r in sorted(latest.items()):
        st = _cell("intents.tsv", r, "status")
        if st in _OPEN:
            open_ids.append(key[0])
        elif st in _CLOSED:
            closed_ids.append(key[0])
    seq, _bad = s.gate_exit_seq()
    return {"intents_open": len(open_ids), "intents_closed": len(closed_ids),
            "open_ids": open_ids, "closed_ids": closed_ids,
            "gates_passed": seq}


def _project_budget(s):
    return "exhausted" if query_cmds.budget_exhausted(s) else "normal"


def _project_tier(s):
    grow = s.rows("goals.tsv")
    guard_tier = _cell("goals.tsv", grow[-1], "guard_tier") if grow else ""
    ev_i = _idx("timeline.tsv", "event")
    tier_last = ""
    for r in s.rows("timeline.tsv"):
        m = _TIER_RE.search(r[ev_i])
        if m:
            tier_last = m.group(1)
    log_path = os.path.join(s.dir, "egress-log.jsonl")
    lines = 0
    if os.path.isfile(log_path):
        with open(log_path, encoding="utf-8") as f:
            lines = sum(1 for ln in f if ln.strip())
    return {"timeline_tier_last": tier_last, "guard_tier": guard_tier,
            "egress_log_present": os.path.isfile(log_path),
            "egress_log_lines": lines}


def _project_limits(s, findings, matrix):
    return {"empty_matrix_cells": list(matrix["gaps"]),
            "unverified": [f["id"] for f in findings if not f["verified"]]}


def aggregate(goal_dir, ts):
    """13 表→聚合投影 dict（键集=PROJECTION_KEYS；同输入两跑逐字节一致）。"""
    _require_tables(goal_dir)
    s = Session(goal_dir)
    findings = _project_findings(s)
    matrix = _project_matrix(s)
    return {
        "goal": _project_goal(s),
        "scope_summary": _project_scope(s),
        "findings": findings,
        "matrix": matrix,
        "coverage": _project_coverage(s),
        "budget_terminal": _project_budget(s),
        "tier_disclosure": _project_tier(s),
        "limits": _project_limits(s, findings, matrix),
    }


USAGE = "用法: tanyin-report aggregate --goal-dir D --timestamp T [--out report/draft-data.json]"


def main(argv):
    ap = argparse.ArgumentParser(prog="tanyin-report")
    ap.add_argument("cmd")
    ap.add_argument("--goal-dir", default=".")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--fd", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "render":   # 批次 6 T13：FD 九段渲染（--fd <id> | --all）
        from ledger import report_render
        return report_render.cli_render(a.goal_dir, a.fd, a.all, a.out)
    if a.cmd != "aggregate":   # lint/sign 随 T14 交付扩入
        sys.stderr.write("未实现/未知子命令: " + a.cmd + chr(10) + USAGE + chr(10))
        return 2
    try:
        d = aggregate(a.goal_dir, a.timestamp or "2026-09-24T00:00:00Z")
    except EnvironmentError as e:
        sys.stderr.write("环境问题: " + str(e) + chr(10))
        return 2
    except Exception as e:   # 账本损坏等门禁级失败
        print("FAIL " + str(e))
        return 1
    payload = json.dumps(d, ensure_ascii=False, sort_keys=True, indent=1) + chr(10)
    if a.out:
        ddir = os.path.dirname(a.out)
        if ddir:
            os.makedirs(ddir, exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        print("OK\t" + a.out)
    else:
        print(payload, end="")
    return 0