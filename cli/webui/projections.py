# -*- coding: utf-8 -*-
"""webui projections（v0.9b Task B1-B3）——观察面三页只读装配。

投影律（docs/design/tanyin-target-form.md §1/§2）：本模块只读零写入——
core.Session 只读加载；禁 datetime.now（输出确定性：轴序/行序全取文件序）。
三投影：
  matrix_view   覆盖热图——latest_matrix 事件溯源取最新格（query_cmds 单源），
                 frozen=最新行 frozen_at 有无（锚点冻结语义）。
  graph_view    十边图——节点=id+kind（viz_render.NODE_TABLES/LAYER 同源），
                 边=edges.tsv 10 kind 全集，着色锚定 viz_render 渲染语义
                 （attack 金/cross_ref 虚线/supersedes 点线/scope-rel 灰）。
  evidence_view 证据卡——E-index 行+linked_finding→findings.vuln_ref+重放三态
                 verdict（timeline 最新 replay-probe 行，tanyin-replay 同形）。
"""
import re

from ledger import core, viz_render
from ledger.query_cmds import latest_by, latest_matrix

# 10 kind 着色（viz_render.EDGE_STYLE 语义锚+全 kind 两两可区分：
# attack 金 #d4a017、cross_ref 虚 6 4、supersedes 点 2 3、scope-rel 灰 #555c66，
# 其余六边各配独立色值——色值自定但 10 kind 全区分）
EDGE_STYLES = {
    "spawns":       {"color": "#4f8cff", "dash": ""},
    "yields":       {"color": "#39c08e", "dash": ""},
    "derived_from": {"color": "#9a6de0", "dash": ""},
    "proves":       {"color": "#e05e9a", "dash": ""},
    "parent":       {"color": "#c9b458", "dash": ""},
    "attack":       {"color": "#d4a017", "dash": ""},
    "cross_ref":    {"color": "#7aa2f7", "dash": "6 4"},
    "evidences":    {"color": "#2fb9c9", "dash": ""},
    "supersedes":   {"color": "#e07b39", "dash": "2 3"},
    "scope-rel":    {"color": "#555c66", "dash": ""},
}

_REPLAY_PAT = re.compile(r"replay-probe (\S+) verdict=(\S+)")   # check_cmds 同形
VERDICT_KEYS = ("reproduced", "not_reproduced", "manual", "env_diff")


def _session(goal_dir):
    return core.Session(goal_dir)


def matrix_view(goal_dir):
    """覆盖热图投影 → {surfaces, vuln_classes, rows, stats}（只读，零写入）。"""
    s = _session(goal_dir)
    latest = latest_matrix(s)                     # 事件溯源：同键文件序后者覆盖
    mi = {f: i for i, f in enumerate(core.TABLES["matrix.tsv"])}
    surfaces, vclasses, rows = [], [], []
    for r in latest.values():                     # dict 保插入序=首见键序（确定性）
        surf, vc = r[0], r[1]
        if surf not in surfaces:
            surfaces.append(surf)
        if vc not in vclasses:
            vclasses.append(vc)
        rows.append({"attack_surface": surf, "vuln_class": vc,
                     "state": r[mi["state"]].strip(),   # viz_render 同语义：空格态=未检查
                     "reason": r[mi["reason"]],
                     "intent_id": r[mi["intent_id"]], "updated": r[mi["updated"]],
                     "frozen_at": r[mi["frozen_at"]],
                     "frozen": bool(r[mi["frozen_at"]].strip())})
    stats = {"cells": len(rows),
             "set": sum(1 for r in rows if r["state"].strip()),
             "empty": sum(1 for r in rows if not r["state"].strip()),
             "frozen": sum(1 for r in rows if r["frozen"])}
    return {"surfaces": surfaces, "vuln_classes": vclasses, "rows": rows,
            "stats": stats}


def graph_view(goal_dir):
    """十边图投影 → {nodes, edges, edge_style, stats}（只读，零写入）。"""
    s = _session(goal_dir)
    nodes = []
    for t, prefix in viz_render.NODE_TABLES:
        for r in sorted(s.rows(t), key=lambda r: r[0]):
            cand = (t == "intents.tsv"
                    and r[core.TABLES[t].index("status")] == "candidate")
            nodes.append({"id": r[0], "kind": prefix,
                          "layer": viz_render.LAYER[prefix],
                          "label": r[0], "candidate": cand})
    te = {f: i for i, f in enumerate(core.TABLES["edges.tsv"])}
    edges = [{"id": r[0], "kind": r[te["kind"]],
              "src": r[te["source_id"]], "dst": r[te["target_id"]]}
             for r in sorted(s.rows("edges.tsv"), key=lambda r: r[0])]
    return {"nodes": nodes, "edges": edges,
            "edge_style": {k: dict(v) for k, v in EDGE_STYLES.items()},
            "stats": {"nodes": len(nodes), "edges": len(edges)}}


def _replay_verdicts(s):
    """timeline 扫描 replay-probe 行 → {EV id: verdict}（同 id 取最新，文件序后者覆盖）。"""
    tle = {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}
    out = {}
    for r in s.rows("timeline.tsv"):
        m = _REPLAY_PAT.search(r[tle["event"]])
        if m:
            out[m.group(1)] = m.group(2)
    return out


def evidence_view(goal_dir):
    """证据卡投影 → {cards, stats}（只读，零写入）。"""
    s = _session(goal_dir)
    tei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    fd = latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])   # 事件溯源取最新
    tf = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
    verdicts = _replay_verdicts(s)
    cards = []
    for r in sorted(s.rows("E-index.tsv"), key=lambda r: r[0]):
        linked = r[tei["linked_finding"]]
        frow = fd.get((linked,))
        cards.append({
            "id": r[0], "title": r[tei["title"]],
            "source_type": r[tei["source_type"]], "observed_at": r[tei["observed_at"]],
            "network_position": r[tei["network_position"]],
            "repro_command": r[tei["repro_command"]], "repro_kind": r[tei["repro_kind"]],
            "content_hash_raw": r[tei["content_hash_raw"]],
            "content_hash_norm": r[tei["content_hash_norm"]],
            "artifact_path": r[tei["artifact_path"]], "card_path": r[tei["card_path"]],
            "linked_finding": linked, "pair_group": r[tei["pair_group"]],
            "raw_excerpt": r[tei["raw_excerpt"]], "created": r[tei["created"]],
            "vuln_ref": frow[tf["vuln_ref"]] if frow else "",
            "verdict": verdicts.get(r[0], ""),
        })
    stats = {"cards": len(cards), "unprobed": sum(1 for c in cards if not c["verdict"])}
    for k in VERDICT_KEYS:
        stats[k] = sum(1 for c in cards if c["verdict"] == k)
    return {"cards": cards, "stats": stats}
