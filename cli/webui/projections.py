# -*- coding: utf-8 -*-
"""webui projections（v0.9b Task B1-B3）——观察面三页只读装配。

投影律（docs/design/tanyin-target-form.md §1/§2）：本模块只读零写入——
core.Session 只读加载；禁 datetime.now（输出确定性：轴序/行序全取文件序）。
三投影：
  matrix_view   覆盖热图——latest_matrix 事件溯源取最新格（query_cmds 单源），
                 frozen=最新行 frozen_at 有无（锚点冻结语义）。
  graph_view    十边图——节点=ARTEX 式富卡（2026-10-16 图升级批·数据段）：
                 num 全图唯一短编号（按类型计数 T1/I3/F12/V7 式）+badge 类型中文名
                 +title 完整句（意图=目的原文前120字/发现=完整标题/事实=摘要前80字/
                 其余=id+简述）+status 三态（进行中/已完成/未证实，未证实=candidate
                 或终态未证成→淡显标记）+impact（发现才有）+layer（NODE_TABLES/LAYER
                 同源）；事件溯源 latest-wins（同 id 追加行取最新）。
                 边=edges.tsv 10 kind 全集+label（kind 原文），着色锚定 viz_render
                 渲染语义（attack 金/cross_ref 虚线/supersedes 点线/scope-rel 灰）。
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


# --- 图升级批·数据段（2026-10-16 计划·ARTEX 对标）单源常量 --------------------
# 类型中文名徽章与短编号字母（发现=V 漏洞语义；编号=字母+类型内计数，全图唯一）
BADGES = {"G": "目标", "INT": "意图", "AST": "资产", "CRED": "凭据",
          "F": "事实", "FD": "发现", "EV": "证据"}
NUM_PREFIX = {"G": "T", "INT": "I", "AST": "A", "CRED": "C",
              "F": "F", "FD": "V", "EV": "E"}
ST_IN_FLIGHT, ST_DONE, ST_UNVERIFIED = "进行中", "已完成", "未证实"
# 资产在册词表（write_cmds 联查断言同源：{1,in_scope,true}=内，out_of_scope=外）
_ASSET_IN_SCOPE = {"1", "in_scope", "true"}
TITLE_CLIP = {"INT": 120, "F": 80}          # 意图=目的原文前120字/事实=摘要前80字


def _latest_rows(s, t):
    """事件溯源：同 id 追加行后者覆盖前者（状态迁移整行复制语义；dict 保文件序）。"""
    out = {}
    for r in s.rows(t):
        out[r[0]] = r
    return out


def _brief(prefix, r, tf):
    """「id+简述」的人读简述（各表最自述的一格，空链逐级兜底）。"""
    if prefix == "G":                       # 目标：objective 战役叙述最自述
        return r[tf["objective"]].strip() or r[tf["target"]].strip()
    if prefix == "AST":                     # 资产：value 即身份
        return r[tf["value"]].strip() or r[tf["type"]].strip()
    if prefix == "CRED":                    # 凭据：账号+角色
        brief = " ".join(x for x in (r[tf["username_ref"]].strip(),
                                     r[tf["role"]].strip()) if x)
        return brief or r[tf["kind"]].strip()
    return r[tf["title"]].strip()           # 证据：E-index title 原文


def _card_title(prefix, r, tf):
    """节点卡完整句 title（计划钉：意图=目的原文前120字/发现=完整标题/
    事实=摘要前80字/其余=id+简述；逐级兜底保非空）。"""
    if prefix == "INT":
        purpose = r[tf["detail"]].strip() or r[tf["title"]].strip()
        return purpose[:TITLE_CLIP[prefix]] or r[0]
    if prefix == "FD":                      # 发现=完整标题（不截断）
        return r[tf["title"]].strip() or r[0]
    if prefix == "F":
        summary = r[tf["detail"]].strip()
        return summary[:TITLE_CLIP[prefix]] or r[0]
    brief = _brief(prefix, r, tf)
    return " ".join(x for x in (r[0], brief) if x)


def _card_status(prefix, r, tf, verdicts):
    """节点卡三态 status：已完成=正向终态/未证实=candidate·终态未证成·待验（淡显）/
    进行中=在途。判定据各表单源：意图状态机（write_cmds 终态单源 done/rejected）、
    发现 exploitation_status、证据重放 verdict（timeline 最新 replay-probe 行）、
    事实 confidence 在册、资产 in_scope 词表、凭据 status 活性。"""
    if prefix == "INT":
        st = r[tf["status"]].strip()
        if st == "done":
            return ST_DONE
        if not st or st in ("candidate", "rejected"):   # 提议未证实/终态未证成
            return ST_UNVERIFIED
        return ST_IN_FLIGHT          # pending/active 在途；blocked/deferred 有复活臂
    if prefix == "FD":
        return (ST_DONE if r[tf["exploitation_status"]].strip() == "verified"
                else ST_UNVERIFIED)  # suspected/ruled_out/空=实证未竟
    if prefix == "EV":
        v = verdicts.get(r[0], "")
        if v == "reproduced":
            return ST_DONE
        if v == "not_reproduced":
            return ST_UNVERIFIED
        return ST_IN_FLIGHT if v else ST_UNVERIFIED     # manual/env_diff 在途；未重放待验
    if prefix == "F":
        return ST_DONE if r[tf["confidence"]].strip() else ST_UNVERIFIED
    if prefix == "AST":
        return (ST_DONE if r[tf["in_scope"]].strip() in _ASSET_IN_SCOPE
                else ST_UNVERIFIED)                     # 范围外=未证实在战役内
    if prefix == "CRED":
        return ST_IN_FLIGHT if r[tf["status"]].strip() == "active" else ST_UNVERIFIED
    return ST_IN_FLIGHT             # G：授权战役在途（目标无终态列）


def graph_view(goal_dir):
    """十边图投影 → {nodes, edges, edge_style, stats}（只读，零写入）。
    节点=ARTEX 式富卡：num/badge/title/status(+unverified 淡显标记)/impact(发现)，
    id/kind/layer/label/candidate 旧字段保留（graph.html 现页零破坏）。"""
    s = _session(goal_dir)
    verdicts = _replay_verdicts(s)              # 证据重放态单源（timeline 最新行）
    nodes = []
    for t, prefix in viz_render.NODE_TABLES:
        tf = {f: i for i, f in enumerate(core.TABLES[t])}
        for cnt, (rid, r) in enumerate(sorted(_latest_rows(s, t).items()), 1):
            cand = (t == "intents.tsv"
                    and r[tf["status"]] == "candidate")
            status = _card_status(prefix, r, tf, verdicts)
            node = {"id": rid, "num": "%s%d" % (NUM_PREFIX[prefix], cnt),
                    "kind": prefix, "badge": BADGES[prefix],
                    "title": _card_title(prefix, r, tf), "status": status,
                    "unverified": status == ST_UNVERIFIED,
                    "layer": viz_render.LAYER[prefix],
                    "label": rid, "candidate": cand}
            if prefix == "FD":                  # impact 仅发现携带（高/中/低）
                node["impact"] = r[tf["impact"]]
            nodes.append(node)
    te = {f: i for i, f in enumerate(core.TABLES["edges.tsv"])}
    edges = [{"id": r[0], "kind": r[te["kind"]], "label": r[te["kind"]],
              "src": r[te["source_id"]], "dst": r[te["target_id"]]}
             for r in sorted(s.rows("edges.tsv"), key=lambda r: r[0])]
    return {"nodes": nodes, "edges": edges,
            "edge_style": {k: dict(v) for k, v in EDGE_STYLES.items()},
            "stats": {"nodes": len(nodes), "edges": len(edges),
                      "unverified": sum(1 for n in nodes if n["unverified"])}}


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
            # v0.9d 收口批（主会话裁决①）：挂接发现行就在手边——只读带出四字段，
            # 供总览发现流 severity 徽章/高危置顶用（finding-stream-priority 规格）。
            "finding_title": frow[tf["title"]] if frow else "",
            "finding_impact": frow[tf["impact"]] if frow else "",
            "finding_status": frow[tf["status"]] if frow else "",
            "finding_asset": frow[tf["affected_asset_id"]] if frow else "",
        })
    stats = {"cards": len(cards), "unprobed": sum(1 for c in cards if not c["verdict"])}
    for k in VERDICT_KEYS:
        stats[k] = sum(1 for c in cards if c["verdict"] == k)
    return {"cards": cards, "stats": stats}
