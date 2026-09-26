# -*- coding: utf-8 -*-
"""tanyin-report 双工件+叙述过滤+终稿签发面（批次 6 T15；契约 13 兑现）。

- findings_json：**全量+生命周期**（VulnClaw findings.json 同型；来源=13 表投影零新
  事实）——每 finding 含 id/title/severity 双轴/replay_state/lifecycle/evidence_ids/
  asset。lifecycle 三桶映射（R-T15-1，零新事实确定性映射）：
    rejected        = status=="superseded"（tombstone 合并）或 exploitation_status==
                      "ruled_out"（排除）；
    repair-candidate= 重放末值 REPAIRED（POC 不再复现=修复候选确认；报告面三态显示
                      env-diff）；
    active          = 其余（status∈{"", "active"} 账本活集口径，write_cmds 同款）。
- findings_sarif：**SARIF 2.1.0 仅 verified**（报告纳入门=exploitation_status==
  verified，unverified 一律不进）；ruleId=漏洞类型（矩阵词表锚 vuln_class）；level=
  biz impact 映射（高→error／中→warning／低→note，未列值→warning 兜底）；
  message.text=title+影响简述；locations[0].physicalLocation.artifactLocation=EV 卡片
  相对路径（EV↔SARIF 位置映射；uri 恒 POSIX 斜杠跨平台）。
- narrative_filter：LLM 叙述段机械清洗（VulnClaw report/filter 同型正则集，清单）：
  ①think/thinking/reasoning 标签连内容（含未闭合尾段）②TOOL_CALL 标记行
  ③Round N／第 N 轮轮次行 ④[LLM XXX] 调试行与 ── 分隔线行 ⑤[结果]/[输出] 前缀剥除
  ⑥连续空行收敛。
- write_all：sign 时落 report/findings.json+report/findings.sarif+report/signed/
  report-<ts>.md（终稿=聚合投影+FD 九段渲染+合规六要素章节〔契约 13 §1，等保占位段
  =常量文本，R11 法务过审对象〕+执行摘要经 narrative_filter）；返回工件路径表。
  文件名时间戳剥冒号（Windows 禁列，R-T15-2 跨平台）。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import report_agg, report_render  # noqa: E402
from ledger.core import Session  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
TOOL_NAME = "tanyin-report"
_LEVEL = {"高": "error", "中": "warning", "低": "note",
          "critical": "error", "high": "error", "medium": "warning",
          "low": "note", "info": "note"}
# 等保占位段（契约 13 §1 条目 6/§6：批次 6 出口前人工法务过审一次；R11 过审对象）
_DJBJ_PLACEHOLDER = (
    "等保 2.0（GB/T 22239-2019）映射段：本段为占位模板，映射结论以法务过审稿为准"
    "（R11：批次 6 出口前人工法务过审一次，模板版本化留痕；各客户法务差异交付时二次确认）。")
_THINK_PAIRED = re.compile(
    r"<(think|thinking|reasoning)\b[^>]*>[\s\S]*?</\1>", re.IGNORECASE)
_THINK_OPEN = re.compile(
    r"<(think|thinking|reasoning)\b[^>]*>[\s\S]*\Z", re.IGNORECASE)
_ROUND_LINE = re.compile(
    r"^\s*(──\s*)?(Cycle\s*\d+\s*\|\s*)?Round\s+\d+(\s*──\s*)?$", re.IGNORECASE)
# 注（M-1 收尾）：_SEP_LINE 收窄为纯标线前，「── Round 7 ──」尾部带空格形原被旧
# _SEP_LINE 一并吞掉——收窄暴露该缺口，尾部组改 (\s*──\s*)?（既有测试
# test_multiline_think_and_round 即规约；『──事实──』等内容行不受影响）。
_ROUND_CN = re.compile(r"^\s*第\s*\d+\s*轮\s*$")
_SEP_LINE = re.compile(r"^\s*─+\s*$")  # 纯标线（M-1 收窄：『──事实──』包裹行保留，反例入册）
_LLM_LINE = re.compile(r"^\s*\[LLM\s+[A-Z_]+\].*$")
_RESULT_PREFIX = re.compile(r"^\s*\[(结果|输出)\]\s*:?")


def _cell(t, row, col):
    return row[TABLES[t].index(col)]


def _posix(rel):
    return (rel or "").replace("\\", "/")


def _replay_tri(replay, fd_row, fid):
    """重放末值→报告面三态（report_agg 同口径）。"""
    ids = [fid]
    for col in ("evidence_ids", "control_evidence_ids"):
        ids += [x for x in _cell("findings.tsv", fd_row, col).split(";") if x]
    state = next((replay[x] for x in ids if x in replay), None)
    return report_agg._TRI.get(state, "unverified")


def _lifecycle(status, exploitation, tri):
    """三桶确定性映射（R-T15-1；模块 docstring 映射表）。"""
    if status == "superseded" or exploitation == "ruled_out":
        return "rejected"
    if tri == "env-diff":   # 重放末值 REPAIRED=修复候选确认
        return "repair-candidate"
    return "active"


def _goal_brief(s):
    rows = s.rows("goals.tsv")
    if not rows:
        return {}
    last = dict(zip(TABLES["goals.tsv"], rows[-1]))
    return {"id": last.get("id", ""), "target": last.get("target", "")}


def findings_json(goal_dir):
    """全量+生命周期 findings 文档（VulnClaw 同型；零墙钟确定性）。"""
    report_agg._require_tables(goal_dir)
    s = Session(goal_dir)
    replay = report_agg._replay_states(s)
    assets = {r[0]: _cell("assets.tsv", r, "value")
              for r in report_render._latest_by_id(s, "assets.tsv").values()}
    findings, buckets = [], {"active": 0, "rejected": 0, "repair-candidate": 0}
    for key, r in sorted(report_render._latest_by_id(s, "findings.tsv").items()):
        fid = key[0]
        status = _cell("findings.tsv", r, "status")
        exploitation = _cell("findings.tsv", r, "exploitation_status")
        tri = _replay_tri(replay, r, fid)
        life = _lifecycle(status, exploitation, tri)
        buckets[life] += 1
        aid = _cell("findings.tsv", r, "affected_asset_id")
        ev_ids = []
        for col in ("evidence_ids", "control_evidence_ids"):
            ev_ids += [x for x in _cell("findings.tsv", r, col).split(";") if x]
        included = life == "active" and exploitation == "verified"
        findings.append({
            "id": fid,
            "title": _cell("findings.tsv", r, "title"),
            "tech_sev": _cell("findings.tsv", r, "confidence"),
            "biz_impact": _cell("findings.tsv", r, "impact"),
            "replay_state": tri,
            "lifecycle": life,
            "evidence_ids": ev_ids,
            "asset": assets.get(aid, ""),
            "verified": included,
        })
    # verified 口径=SARIF 报告纳入门（active+exploitation_status==verified）——
    # summary.verified 与 findings.sarif 结果数恒一致（VulnClaw findings_output 同款纪律）；
    # 独立重放三态另载 replay_state 字段（重放门与纳入门分列，不混标）。
    verified = [f["id"] for f in findings if f["verified"]]
    return {
        "schema_version": "1.0",
        "tool": {"name": TOOL_NAME},
        "goal": _goal_brief(s),
        "summary": {"total": len(findings), "verified": len(verified), **buckets},
        "verified": verified,
        "findings": findings,
    }


def findings_sarif(goal_dir):
    """SARIF 2.1.0 仅 verified（报告纳入门）；EV↔SARIF 位置映射。"""
    report_agg._require_tables(goal_dir)
    s = Session(goal_dir)
    replay = report_agg._replay_states(s)
    latest_f = report_render._latest_by_id(s, "findings.tsv")
    rules, rule_index, results = [], {}, []
    for fid in report_render.active_fd_ids(s):
        fd_row = latest_f.get((fid,))
        if fd_row is None:
            continue
        if _cell("findings.tsv", fd_row, "exploitation_status") != "verified":
            continue                       # 报告纳入门：unverified 一律不进 SARIF
        anchor = report_render._type_anchor(s, fd_row)
        rule_id = anchor[1] if anchor else "unknown-class"
        if rule_id not in rule_index:
            rule_index[rule_id] = len(rules)
            rules.append({"id": rule_id, "name": rule_id,
                          "shortDescription": {"text": rule_id}})
        evs = report_render._evidence_rows(s, fd_row)
        uris = [_posix(_cell("E-index.tsv", e, "card_path"))
                for e in evs if _cell("E-index.tsv", e, "card_path").strip()]
        uri = uris[0] if uris else fid     # 无卡兜底=finding id 锚（门内不会走到）
        title = _cell("findings.tsv", fd_row, "title")
        brief = _cell("findings.tsv", fd_row, "description_brief")
        impact = _cell("findings.tsv", fd_row, "impact")
        results.append({
            "ruleId": rule_id,
            "level": _LEVEL.get(impact, "warning"),
            "message": {"text": title + (" — " + brief if brief else "")},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}}}],
            "properties": {
                "finding_id": fid,
                "replay_state": _replay_tri(replay, fd_row, fid),
                "tech_sev": _cell("findings.tsv", fd_row, "confidence"),
                "biz_impact": impact,
            },
        })
    return {
        "$schema": SARIF_SCHEMA_URI,
        "version": SARIF_VERSION,
        "runs": [{"tool": {"driver": {"name": TOOL_NAME, "rules": rules}},
                  "results": results}],
    }


def narrative_filter(text):
    """LLM 叙述段机械清洗（正则清单见模块 docstring；零语义判断）。"""
    out = _THINK_PAIRED.sub("", text or "")
    out = _THINK_OPEN.sub("", out)
    kept = []
    for ln in out.splitlines():
        if ("TOOL_CALL" in ln or _ROUND_LINE.match(ln) or _ROUND_CN.match(ln)
                or _SEP_LINE.match(ln) or _LLM_LINE.match(ln)):
            continue
        kept.append(_RESULT_PREFIX.sub("", ln))
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(kept))
    return out.strip()


def _six_sections(agg, fj):
    """合规六要素章节（契约 13 §1；数据源=aggregate 投影+findings_json 生命周期）。"""
    goal = agg.get("goal") or {}
    sc = (agg.get("scope_summary") or {}).get("counts") or {}
    heads = (agg.get("scope_summary") or {}).get("amendment_heads") or []
    s1 = "\n".join([
        "- 授权目标: %s（%s）" % (goal.get("id", ""), goal.get("target", "")),
        "- 授权书: %s（sha256=%s，签署方=%s）" % (goal.get("auth_doc", ""),
                                                goal.get("auth_sha256", ""),
                                                goal.get("signer", "")),
        "- 有效窗口: %s ~ %s" % (goal.get("valid_from", ""), goal.get("valid_until", "")),
        "- 范围计数: include=%d exclude=%d oob=%d account-grant=%d"
        % (sc.get("include", 0), sc.get("exclude", 0), sc.get("oob", 0),
           sc.get("account-grant", 0)),
        "- 修订史生效链头: %s" % (", ".join(heads) or "无"),
    ])
    m = agg.get("matrix") or {}
    s2 = "\n".join(["- %s × %s = %s" % (f["attack_surface"], f["vuln_class"], f["state"])
                     for f in m.get("filled", [])]
                    + (["- 空格（WSTG 词表锚未命中）: %s" % ", ".join(m.get("gaps", []))]
                       if m.get("gaps") else [])) or "- 矩阵空（无命中行）"
    cov = agg.get("coverage") or {}
    lim = agg.get("limits") or {}
    s3 = "\n".join([
        "- intents: open=%d closed=%d" % (cov.get("intents_open", 0),
                                          cov.get("intents_closed", 0)),
        "- 门通过序: %s" % (", ".join(cov.get("gates_passed", [])) or "无"),
        "- 局限性: 矩阵空格=%s；unverified=%s"
        % (", ".join(lim.get("empty_matrix_cells", [])) or "无",
           ", ".join(lim.get("unverified", [])) or "无"),
    ])
    fs = agg.get("findings") or []
    life = {f["id"]: f["lifecycle"] for f in fj.get("findings", [])}
    s4 = "\n".join(["- %s %s: tech=%s × biz=%s"
                     % (f["id"], f["title"], f["tech_sev"], f["biz_impact"])
                     for f in fs]) or "- 无 active finding"
    order = {"verified": 0, "env-diff": 1, "unverified": 2}
    s5 = "\n".join([
        "- %s（三态=%s，lifecycle=%s）: 复测依据=POC 独立重放门；整改优先级按"
        " verified>env-diff>unverified 排列"
        % (f["id"], f["replay_state"], life.get(f["id"], "active"))
        for f in sorted(fs, key=lambda x: (order.get(x["replay_state"], 9), x["id"]))])
    s5 = s5 or "- 无 active finding"
    return [("## 授权与范围声明", s1), ("## 方法学映射（WSTG↔章节）", s2),
            ("## 覆盖度与局限性", s3), ("## 技术×业务风险分级", s4),
            ("## 整改优先级与复测建议", s5), ("## 等保占位段", _DJBJ_PLACEHOLDER)]


def _final_report(goal_dir, ts, fj, sar):
    """终稿 md=聚合投影+FD 九段渲染+合规六要素+执行摘要（经 narrative_filter）。"""
    agg = report_agg.aggregate(goal_dir, ts)
    summary = ("目标 %s：共 %d 项 finding（active=%d rejected=%d repair-candidate=%d），"
               "其中 verified=%d 项入 SARIF 双工件；预算终态=%s；守门档位=%s。"
               % (fj["goal"].get("target", ""), fj["summary"]["total"],
                  fj["summary"]["active"], fj["summary"]["rejected"],
                  fj["summary"]["repair-candidate"], fj["summary"]["verified"],
                  agg.get("budget_terminal", ""),
                  (agg.get("tier_disclosure") or {}).get("guard_tier", "")))
    parts = ["# 渗透测试报告终稿 · %s" % fj["goal"].get("id", ""), "",
             "- 签发时刻: %s" % ts, "", "## 执行摘要", narrative_filter(summary), ""]
    parts += ["%s\n%s\n" % (h, body) for h, body in _six_sections(agg, fj)]
    parts.append("## 发现详情（FD 九段渲染）")
    draft_dir = os.path.join(goal_dir, "report", "draft")
    for fid in report_render.active_fd_ids(Session(goal_dir)):
        p = os.path.join(draft_dir, fid + ".md")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                md = f.read()
        else:
            rc, md = report_render.render_fd(goal_dir, fid)
            if rc != 0:
                raise ValueError("终稿渲染 FAIL: " + md)
        parts.append(md)
        parts.append("")
    return "\n".join(parts)


def write_all(goal_dir, ts):
    """sign 落盘三工件；返回工件路径表（findings.json/findings.sarif/report-<ts>.md）。"""
    fj = findings_json(goal_dir)
    sar = findings_sarif(goal_dir)
    report_dir = os.path.join(goal_dir, "report")
    os.makedirs(report_dir, exist_ok=True)
    paths = []
    for name, doc in (("findings.json", fj), ("findings.sarif", sar)):
        p = os.path.join(report_dir, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
        paths.append(p)
    signed = os.path.join(report_dir, "signed")
    os.makedirs(signed, exist_ok=True)
    p = os.path.join(signed, "report-%s.md" % ts.replace(":", ""))   # R-T15-2
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(_final_report(goal_dir, ts, fj, sar))
    paths.append(p)
    return paths
