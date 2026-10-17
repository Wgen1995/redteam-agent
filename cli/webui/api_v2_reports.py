# -*- coding: utf-8 -*-
"""api_v2_reports（T4·P7 报告中心）——报告列表/详情/重渲染只读投影，路由前缀 /api/v2/。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式，禁 datetime.now，
输出确定性——同输入两跑逐字节一致）；挂载=ROUTES 单源表由 include 机制
（api_pages.py，UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_report_center.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。
dispatch(path, query, ledger_dir, battles_dir) 与 api_v2_broadcast 同形。

三路由（全过会话门；无豁免）：
  GET /api/v2/report-list.json
      → 每仗一行：状态徽章（草稿/待签发/已签发——确定性文件分类，零墙钟）
        +版本数+最后渲染时间+发现计数+可下载位。
  GET /api/v2/report-detail?battle=N[&goal=G-x]
      → 渲染预览六节（封面/授权摘要/发现表[等级/验证状态徽章]/证据附录/
        覆盖诚实节=已测矩阵+未测清单+原因/方法论附录）+元信息卡
        （渲染输入哈希/版本链/签发状态/双人签发位+pass.json 绑定复检）
        +同输入同输出钉（渲染纯函数两跑，两次哈希比对）。
  GET /api/v2/report-rerender.json?battle=N[&goal=G-x]
      → 「重新渲染」钮懒载：输入指纹+两跑输出哈希+pin_ok（同输入同输出钉）。

状态机（文件分类单源，P5.5 签发门 report_lint.sign_gate 产物消费不重算门）：
  已签发 = report/signed/pass.json 在场（锁定；issued_at=凭证 ts；绑定复检逐件
           sha256 重算——篡改=binding_ok False 诚实披露）；
  待签发 = 有渲染工件（report/draft/*.md 或 findings.json/sarif）而无凭证；
  草稿   = 其余（仗在打数据在账，报告面待聚合）。
版本链 = report/signed/report-<ts>.md 逐版（文件名时间戳定序）；待签发=当前草稿版
  （v=签发版数+1）；双签位 = approvals.tsv decision=approved 行按时间序前两卡
  （签发门 verify-signoff「人工批准在案」同源数据；两把互异 approver=双签就绪）。
"""
import hashlib
import json
import os
import re

from ledger import core
from ledger.session_view import default_battles_dir, list_battles

_ROUTE_NAMES = ("report-list.json", "report-detail", "report-rerender.json")
ROUTE_LIST = "/api/v2/" + _ROUTE_NAMES[0]
ROUTE_DETAIL = "/api/v2/" + _ROUTE_NAMES[1]
ROUTE_RERENDER = "/api/v2/" + _ROUTE_NAMES[2]
ROUTES = {ROUTE_LIST: None, ROUTE_DETAIL: None, ROUTE_RERENDER: None}
#                                    ↑ 尾部赋真身（前向引用；重渲染随循环③入表）

_SIGNED_MD = re.compile(r"^report-(\d{4}-\d{2}-\d{2}T\d{6}Z)\.md$")
_HASH_TRUNC = 12
_GATE_KEYS = ("render", "nine_segments", "burp_pasteable", "dual_fingerprint",
              "time_chain", "authorization", "draft_byte_equal", "artifact_binding",
              "redact_scan", "cleanup_checklist", "tier_disclosure",
              "compliance_six", "empty_rhetoric", "aggregate",
              "terminal_b_disclosure")


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _gen_key(name):
    """G-* 代目录自然序键（server._latest_gen 同律：G-r9 < G-r43）。"""
    digits = [int(d) for d in re.findall(r"\d+", name)]
    return (digits or [0])[0]


def _latest_goal_dir(battle_dir):
    """战目录最新代目录（G-* 自然序）；无=None。"""
    try:
        gens = [d for d in os.listdir(battle_dir)
                if d.startswith("G-") and os.path.isdir(os.path.join(battle_dir, d))]
    except OSError:
        return None
    if not gens:
        return None
    return os.path.join(battle_dir, sorted(gens, key=_gen_key)[-1])


def _cell(t, r, col):
    return r[core.TABLES[t].index(col)]


def _latest_rows(s, tname, key_cols):
    """按业务键取最新行（query_cmds.latest_by 同口径，本地只读实现）。"""
    out, order = {}, []
    for r in s.rows(tname):
        k = tuple(_cell(tname, r, c) for c in key_cols)
        if k not in out:
            order.append(k)
        out[k] = r
    return out, order


def _iso_mtime(path):
    """文件 mtime → ISO-Z（文件状态读——非墙钟；无文件=空串）。"""
    try:
        m = os.stat(path).st_mtime
    except OSError:
        return ""
    import datetime
    return datetime.datetime.utcfromtimestamp(m).strftime("%Y-%m-%dT%H:%M:%SZ")


def _signed_versions(goal_dir):
    """report/signed/report-<ts>.md → [{file, ts}]（时间戳升序=版本链）。"""
    out = []
    sdir = os.path.join(goal_dir, "report", "signed")
    try:
        names = sorted(os.listdir(sdir))
    except OSError:
        return out
    for n in names:
        m = _SIGNED_MD.match(n)
        if not m:
            continue
        raw = m.group(1)                      # 2026-10-20T060000Z → 还原冒号
        ts = raw[:11] + raw[11:13] + ":" + raw[13:15] + ":" + raw[15:17] + "Z"
        out.append({"file": "report/signed/" + n, "ts": ts})
    return out


def _draft_files(goal_dir):
    try:
        names = sorted(n for n in os.listdir(os.path.join(goal_dir, "report", "draft"))
                       if n.endswith(".md"))
    except OSError:
        return []
    return ["report/draft/" + n for n in names]


def _has_render(goal_dir):
    """渲染工件在场位（draft 段稿或双工件）。"""
    if _draft_files(goal_dir):
        return True
    return any(os.path.isfile(os.path.join(goal_dir, "report", n))
               for n in ("findings.json", "findings.sarif"))


def _load_pass(goal_dir):
    """report/signed/pass.json → dict | None（坏 JSON=None 诚实降级草稿态）。"""
    p = os.path.join(goal_dir, "report", "signed", "pass.json")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, dict) else None
    except (OSError, ValueError):
        return None


def _pass_binding(goal_dir, cred):
    """凭证 artifacts 绑定复检（逐件 sha256 重算；篡改/缺件=失配清单）。"""
    bad = []
    arts = (cred or {}).get("artifacts") or {}
    for rel in sorted(arts):
        p = os.path.join(goal_dir, rel)
        if not os.path.isfile(p):
            bad.append(rel + "（文件缺）")
            continue
        if _sha256_file(p) != arts[rel]:
            bad.append(rel)
    return {"ok": not bad, "checked": len(arts), "bad": bad}


def _report_state(goal_dir):
    """状态机单源：{status, locked, issued_at, has_render, versions_signed}。"""
    cred = _load_pass(goal_dir)
    has_render = _has_render(goal_dir)
    signed = _signed_versions(goal_dir)
    if cred is not None:
        gates = cred.get("gates") or {}
        gates_pass = all((gates.get(k) or {}).get("status") == "PASS"
                         for k in _GATE_KEYS) if gates else False
        return {"status": "已签发", "locked": True,
                "issued_at": str(cred.get("ts") or ""), "has_render": has_render,
                "versions_signed": len(signed), "gates_pass": gates_pass}
    if has_render:
        return {"status": "待签发", "locked": False, "issued_at": "",
                "has_render": True, "versions_signed": 0, "gates_pass": None}
    return {"status": "草稿", "locked": False, "issued_at": "",
            "has_render": False, "versions_signed": 0, "gates_pass": None}


def _findings_counts(goal_dir):
    """active 发现计数（total/verified——verified=exploitation_status 口径）。"""
    s = core.Session(goal_dir)
    latest, order = _latest_rows(s, "findings.tsv", ["id"])
    total = verified = 0
    for k in order:
        r = latest[k]
        if _cell("findings.tsv", r, "status") != "active":
            continue
        total += 1
        if _cell("findings.tsv", r, "exploitation_status") == "verified":
            verified += 1
    return {"total": total, "verified": verified}


def _last_render(goal_dir, state, signed):
    """最后渲染时间：签发稿文件名时间戳优先；草稿/双工件=mtime；无=空。"""
    if signed:
        return signed[-1]["ts"]
    cand = [os.path.join(goal_dir, f) for f in _draft_files(goal_dir)]
    cand += [os.path.join(goal_dir, "report", n) for n in ("findings.json",
                                                           "findings.sarif")]
    times = [_iso_mtime(p) for p in cand if os.path.isfile(p)]
    return max(times) if times else ""


def _versions_count(state, signed):
    if state["locked"]:
        return len(signed)
    return 1 if state["has_render"] else 0


# ---------------------------------------------------------------- ① 列表投影 --

def report_list_view(battles_dir=None):
    """每仗一行 → {battles, counts}（战号升序；只读零写入确定性）。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    battles, counts = [], {"signed": 0, "pending": 0, "draft": 0, "battles": 0}
    for b in list_battles(root):
        battle_dir = os.path.join(root, b["id"])
        gd = _latest_goal_dir(battle_dir)
        item = {"battle": b["id"], "n": b["n"], "goal": "",
                "goal_id": "", "target": "", "status": "草稿", "locked": False,
                "versions": 0, "last_render": "", "has_download": False,
                "findings": {"total": 0, "verified": 0}}
        if gd is not None:
            s = core.Session(gd)
            grows = s.rows("goals.tsv")
            goal = dict(zip(core.TABLES["goals.tsv"], grows[-1])) if grows else {}
            signed = _signed_versions(gd)
            state = _report_state(gd)
            item.update({
                "goal": os.path.basename(gd),
                "goal_id": goal.get("id", ""),
                "target": goal.get("target", ""),
                "status": state["status"],
                "locked": state["locked"],
                "versions": _versions_count(state, signed),
                "last_render": _last_render(gd, state, signed),
                "has_download": state["has_render"],
                "findings": _findings_counts(gd)})
        key = {"已签发": "signed", "待签发": "pending", "草稿": "draft"}[item["status"]]
        counts[key] += 1
        counts["battles"] += 1
        battles.append(item)
    return {"battles": battles, "counts": counts}


def report_list_route(query, ledger_dir=None, battles_dir=None):
    """路由适配层 → (200, payload)；列表无参数无 4xx 面。"""
    return 200, report_list_view(battles_dir=battles_dir if battles_dir else None)


# ---------------------------------------------------------------- ② 详情投影 --

_REPLAY_PROBE = re.compile(r"replay-probe (\S+) verdict=(\S+)")
_REPLAY_COLON = re.compile(r"^replay:((?:EV|FD)-[^:\s]+):(VERIFIED|REPAIRED|REJECTED)")
_TIER_RE = re.compile(r'tier[=:]\s*"?([A-Za-z0-9.+-]+)')
_OPEN_INTENT = {"candidate", "pending", "active"}
_CLOSED_INTENT = {"done", "rejected", "blocked", "deferred"}
_MATRIX_LABEL = {"": "未测", "-": "范围外", "!": "受阻", "?": "存疑"}
_REPRODUCED = {"reproduced", "VERIFIED"}


def _replay_verdicts(s):
    """timeline 重放事件末值（replay-probe 与 replay: 两形并收）：{引用: 裁决}。"""
    out = {}
    ev_i = core.TABLES["timeline.tsv"].index("event")
    for r in s.rows("timeline.tsv"):
        ev = r[ev_i]
        m = _REPLAY_PROBE.search(ev)
        if m:
            out[m.group(1)] = m.group(2).rstrip(",;）)")
            continue
        m = _REPLAY_COLON.match(ev)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _split_ids(s):
    return [x.strip() for x in (s or "").replace(";", ",").split(",") if x.strip()]


def _verify_tri(frow, ev_ids, verdicts):
    """验证状态三态（宪法#41 词表；api_v2_findings 同口径本地单源）。"""
    expl = _cell("findings.tsv", frow, "exploitation_status").strip()
    if expl == "verified":
        return "已验证", "exploitation_status=verified"
    if expl == "ruled_out":
        return "已失效", "exploitation_status=ruled_out"
    hit = next((e for e in ev_ids if verdicts.get(e) in _REPRODUCED), None)
    if hit:
        return "已验证", "最新重放 reproduced（%s）" % hit
    return "待验证", "尚无 reproduced 重放实证"


def _input_fingerprint(goal_dir):
    """渲染输入指纹：13 表+证据卡+工件逐件 sha256 链（排序定序=确定性）。"""
    rels = []
    for tname in core.TABLES:
        if os.path.isfile(os.path.join(goal_dir, tname)):
            rels.append(tname)
    for sub in ("evidence", "artifacts"):
        base = os.path.join(goal_dir, sub)
        for root, _dirs, files in os.walk(base):
            for n in files:
                rels.append(os.path.relpath(os.path.join(root, n),
                                            goal_dir).replace(os.sep, "/"))
    chain = ""
    for rel in sorted(rels):
        fh = _sha256_file(os.path.join(goal_dir, rel))
        chain = hashlib.sha256(
            (chain + "\n" + rel + "\0" + fh).encode("utf-8")).hexdigest()
    return chain, len(rels)


def _detail_core(goal_dir):
    """详情六节主体（封面/授权/发现/证据/覆盖/方法论）——markdown 同源。"""
    s = core.Session(goal_dir)
    grows = s.rows("goals.tsv")
    goal = dict(zip(core.TABLES["goals.tsv"], grows[-1])) if grows else {}
    verdicts = _replay_verdicts(s)

    # —— 授权摘要：scope 生效行（amendment_of 豁免口径=report_agg 同律） ——
    srows = s.rows("scope.tsv")
    superseded = {_cell("scope.tsv", r, "amendment_of") for r in srows
                  if _cell("scope.tsv", r, "amendment_of").strip()}
    eff = [r for r in srows if _cell("scope.tsv", r, "id") not in superseded]
    sc = {"include": 0, "exclude": 0, "oob": 0, "account-grant": 0}
    for r in eff:
        k = _cell("scope.tsv", r, "kind")
        if k in sc:
            sc[k] += 1

    # —— 发现表：active 行 × 验证状态徽章 ——
    flatest, forder = _latest_rows(s, "findings.tsv", ["id"])
    alatest, _a = _latest_rows(s, "assets.tsv", ["id"])
    fd_rows, counts = [], {"total": 0, "verified": 0, "pending": 0, "ruled_out": 0}
    ev_of_fd = {}
    for k in forder:
        r = flatest[k]
        if _cell("findings.tsv", r, "status") != "active":
            continue
        fid = _cell("findings.tsv", r, "id")
        ids = _split_ids(_cell("findings.tsv", r, "evidence_ids")) + \
            _split_ids(_cell("findings.tsv", r, "control_evidence_ids"))
        ev_of_fd[fid] = ids
        state, basis = _verify_tri(r, ids, verdicts)
        impact = _cell("findings.tsv", r, "impact")
        counts["total"] += 1
        if state == "已验证":
            counts["verified"] += 1
        elif state == "已失效":
            counts["ruled_out"] += 1
        else:
            counts["pending"] += 1
        fd_rows.append({"id": fid, "title": _cell("findings.tsv", r, "title"),
                        "impact": impact, "verify_state": state,
                        "verify_basis": basis,
                        "asset": _cell("assets.tsv", alatest.get(
                            (_cell("findings.tsv", r, "affected_asset_id"),), []),
                            "value") if alatest.get(
                            (_cell("findings.tsv", r, "affected_asset_id"),)) else "",
                        "evidence_count": len(ids)})

    # —— 证据附录：active 发现挂接 EV（findings 引用 ∪ linked_finding 反指） ——
    elatest, _e = _latest_rows(s, "E-index.tsv", ["id"])
    ev_ids = set()
    for ids in ev_of_fd.values():
        ev_ids.update(ids)
    for k, r in elatest.items():
        lf = _cell("E-index.tsv", r, "linked_finding")
        if lf in ev_of_fd:
            ev_ids.add(k[0])
    evidence = []
    for k in sorted(elatest):
        if k[0] not in ev_ids:
            continue
        r = elatest[k]
        h = _cell("E-index.tsv", r, "content_hash_raw")
        evidence.append({"id": k[0], "title": _cell("E-index.tsv", r, "title"),
                         "observed_at": _cell("E-index.tsv", r, "observed_at"),
                         "hash_trunc": h[:_HASH_TRUNC],
                         "artifact_path": _cell("E-index.tsv", r, "artifact_path"),
                         "linked_finding": _cell("E-index.tsv", r, "linked_finding")})

    # —— 覆盖诚实节：已测矩阵（x）+未测清单（空/-/!/? 含原因）+未跑意图 ——
    mlatest, morder = _latest_rows(s, "matrix.tsv", ["attack_surface", "vuln_class"])
    tested, untested = [], []
    for k in morder:
        r = mlatest[k]
        st = _cell("matrix.tsv", r, "state").strip()
        cell = {"attack_surface": k[0], "vuln_class": k[1]}
        if st == "x":
            tested.append(dict(cell, state="x"))
        else:
            untested.append(dict(cell, label=_MATRIX_LABEL.get(st, "未测"),
                                 reason=_cell("matrix.tsv", r, "reason")))
    total_cells = len(tested) + len(untested)
    closure = ("%.1f%%（%d/%d）" % (100.0 * len(tested) / total_cells,
                                    len(tested), total_cells)) if total_cells else "n/a"
    ilatest, iorder = _latest_rows(s, "intents.tsv", ["id"])
    intents_open = [k[0] for k in iorder
                    if _cell("intents.tsv", ilatest[k], "status") in _OPEN_INTENT]
    intents_closed_n = sum(1 for k in iorder
                           if _cell("intents.tsv", ilatest[k], "status")
                           in _CLOSED_INTENT)

    # —— 方法论附录：门序/预算终态/档位披露/时间链 ——
    gates, _bad = s.gate_exit_seq()
    try:
        from ledger import query_cmds as _qc
        budget_terminal = "exhausted" if _qc.budget_exhausted(s) else "normal"
    except Exception:
        budget_terminal = ""
    tier_last = ""
    ev_i = core.TABLES["timeline.tsv"].index("event")
    for r in s.rows("timeline.tsv"):
        m = _TIER_RE.search(r[ev_i])
        if m:
            tier_last = m.group(1)
    chain_ok, _ = s.verify_chain()
    methodology = {"gates_passed": gates, "intents_open": len(intents_open),
                   "intents_closed": intents_closed_n,
                   "budget_terminal": budget_terminal,
                   "guard_tier": goal.get("guard_tier", ""),
                   "timeline_tier_last": tier_last,
                   "timeline_rows": len(s.rows("timeline.tsv")),
                   "chain_ok": chain_ok}
    cover = {"report_no": goal.get("id", ""), "target": goal.get("target", ""),
             "objective": goal.get("objective", ""),
             "signer": goal.get("signer", ""),
             "valid_from": goal.get("valid_from", ""),
             "valid_until": goal.get("valid_until", ""),
             "budget": goal.get("budget", ""),
             "guard_tier": goal.get("guard_tier", "")}
    authz = {"auth_doc": goal.get("auth_doc", ""),
             "auth_sha256": goal.get("auth_sha256", ""),
             "sha_trunc": (goal.get("auth_sha256", "") or "")[:_HASH_TRUNC],
             "signer": goal.get("signer", ""),
             "scope_counts": sc,
             "amendment_heads": sorted(_cell("scope.tsv", r, "id") for r in eff)}
    return {"cover": cover, "authorization": authz,
            "findings": {"rows": fd_rows, "counts": counts},
            "evidence": evidence,
            "coverage": {"tested": tested, "untested": untested,
                         "intents_open": intents_open, "closure": closure},
            "methodology": methodology}


def _build_markdown(goal_name, state, core_p):
    """canonical Markdown 投影（封面→授权→发现→证据→覆盖诚实→方法论）。"""
    cov, auth = core_p["cover"], core_p["authorization"]
    lines = ["# 渗透测试报告 · %s" % (cov["report_no"] or goal_name), "",
             "- 目标: %s（%s）" % (cov["target"], cov["objective"]),
             "- 授权窗口: %s ~ %s" % (cov["valid_from"], cov["valid_until"]),
             "- 报告状态: %s%s" % (state["status"],
                                   "（锁定·签发时刻 %s）" % state["issued_at"]
                                   if state["locked"] else ""),
             "- 预算上限: %s" % cov["budget"],
             "- 强度档: guard %s" % cov["guard_tier"], ""]
    lines += ["## 授权与范围",
              "- 签署方: %s" % auth["signer"],
              "- 授权书: %s（sha256=%s）" % (auth["auth_doc"], auth["auth_sha256"]),
              "- 范围计数: include=%d exclude=%d oob=%d account-grant=%d"
              % (auth["scope_counts"]["include"], auth["scope_counts"]["exclude"],
                 auth["scope_counts"]["oob"], auth["scope_counts"]["account-grant"]),
              "- 修订头: %s" % (", ".join(auth["amendment_heads"]) or "无"), ""]
    lines.append("## 发现明细")
    if core_p["findings"]["rows"]:
        for f in core_p["findings"]["rows"]:
            lines.append("- %s %s: 等级=%s 验证状态=%s 证据=%d"
                         % (f["id"], f["title"], f["impact"], f["verify_state"],
                            f["evidence_count"]))
    else:
        lines.append("- 无 active finding")
    lines.append("")
    lines.append("## 证据附录")
    if core_p["evidence"]:
        for e in core_p["evidence"]:
            lines.append("- %s %s observed=%s sha256=%s… 挂接=%s"
                         % (e["id"], e["title"], e["observed_at"], e["hash_trunc"],
                            e["linked_finding"] or "—"))
    else:
        lines.append("- 无挂接证据")
    lines.append("")
    cv = core_p["coverage"]
    lines.append("## 覆盖诚实")
    lines.append("已测矩阵（state=x）:")
    lines += ["- %s × %s = x" % (t["attack_surface"], t["vuln_class"])
              for t in cv["tested"]] or ["-（无）"]
    lines.append("未测清单（含原因）:")
    lines += ["- %s × %s [%s] %s" % (u["attack_surface"], u["vuln_class"],
                                     u["label"], u["reason"] or "原因未记录")
              for u in cv["untested"]] or ["-（无——全格已测）"]
    lines.append("未跑意图: %s" % (", ".join(cv["intents_open"]) or "无"))
    lines.append("闭合率: %s" % cv["closure"])
    lines.append("")
    m = core_p["methodology"]
    lines += ["## 方法论",
              "- 门通过序: %s" % (", ".join(m["gates_passed"]) or "无"),
              "- intents: open=%d closed=%d" % (m["intents_open"],
                                                m["intents_closed"]),
              "- 预算终态: %s" % (m["budget_terminal"] or "—"),
              "- 守卫档: %s（timeline 末值 %s）" % (m["guard_tier"],
                                                    m["timeline_tier_last"] or "无"),
              "- timeline 行数: %d（链完整=%s）"
              % (m["timeline_rows"], "是" if m["chain_ok"] else "否"), ""]
    return "\n".join(lines)


def _signature_slots(goal_dir):
    """双人签发位：approvals approved 行按时间序前两卡（+双签就绪位）。"""
    s = core.Session(goal_dir)
    approved = []
    for r in s.rows("approvals.tsv"):
        if _cell("approvals.tsv", r, "decision") != "approved":
            continue
        approved.append({"approver": _cell("approvals.tsv", r, "approver"),
                         "timestamp": _cell("approvals.tsv", r, "timestamp"),
                         "note": _cell("approvals.tsv", r, "note")})
    approved.sort(key=lambda x: (x["timestamp"], x["approver"]))
    slots = []
    for i in range(2):
        if i < len(approved):
            slots.append(dict(approved[i], slot=i + 1, filled=True))
        else:
            slots.append({"slot": i + 1, "filled": False, "approver": "",
                          "timestamp": "", "note": ""})
    signers = [a["approver"] for a in approved]
    dual = len(signers) >= 2 and len(set(signers)) >= 2
    return slots, dual


def _version_chain(goal_dir, state, signed):
    """版本链：签发稿逐版（ts 升序）；未签发=当前草稿版收尾。"""
    out = []
    for i, v in enumerate(signed):
        out.append({"v": i + 1, "kind": "signed", "ts": v["ts"], "file": v["file"],
                    "sha256": _sha256_file(os.path.join(goal_dir, v["file"]))})
    if not state["locked"] and state["has_render"]:
        out.append({"v": len(out) + 1, "kind": "draft", "ts": "",
                    "file": "report/draft/*", "sha256": ""})
    return out


def _resolve_goal(battles, root, goal, ledger_dir):
    """goal 名 → (goal_dir, battle dict|None)；battles 根内倒序找（新战优先）。"""
    for b in reversed(battles):
        gd = _latest_goal_dir(os.path.join(root, b["id"]))
        if gd is not None and os.path.basename(gd) == goal:
            return gd, {"id": b["id"], "n": b["n"]}
    if ledger_dir:
        for cand in (os.path.join(ledger_dir, goal),
                     os.path.join(os.path.dirname(str(ledger_dir)), goal)):
            if os.path.isdir(cand):
                return cand, None
    return None, None


def report_detail_view(battles_dir=None, battle=None, goal=None, ledger_dir=None):
    """报告详情投影 → dict（六节+元信息卡+markdown+钉）；坏战号 ValueError。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    battles = list_battles(root)
    gd, battle_info = None, None
    if battle is not None:
        n = _norm_battle(battle)
        if n is None:
            raise ValueError("battle 无法解析为整数: %r" % (battle,))
        hit = [b for b in battles if b["n"] == n]
        if not hit:
            return {"error": "battle 不存在: %s" % n,
                    "battles": [{"id": b["id"], "n": b["n"]} for b in battles]}
        gd = _latest_goal_dir(os.path.join(root, hit[0]["id"]))
        if gd is None:
            return {"error": "battle-%d 无记录目录（G-*）——先立项" % n,
                    "battles": [{"id": b["id"], "n": b["n"]} for b in battles]}
        battle_info = {"id": hit[0]["id"], "n": n}
    elif goal:
        gd, battle_info = _resolve_goal(battles, root, goal, ledger_dir)
        if gd is None:
            return {"error": "goal 不存在: %s" % goal,
                    "battles": [{"id": b["id"], "n": b["n"]} for b in battles]}
    else:
        return {"error": "缺 battle/goal 参数（battle=N 或 goal=G-xx）"}
    state = _report_state(gd)
    signed = _signed_versions(gd)
    cred = _load_pass(gd)
    slots, dual = _signature_slots(gd)
    core_p = _detail_core(gd)
    goal_name = os.path.basename(gd)
    md1 = _build_markdown(goal_name, state, core_p)
    md2 = _build_markdown(goal_name, state, core_p)
    h1 = hashlib.sha256(md1.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(md2.encode("utf-8")).hexdigest()
    in_hash, in_files = _input_fingerprint(gd)
    cred_out = None
    if cred is not None:
        bind = _pass_binding(gd, cred)
        gates = cred.get("gates") or {}
        cred_out = {"ts": str(cred.get("ts") or ""),
                    "gates_pass": state["gates_pass"],
                    "gates": {k: (gates.get(k) or {}).get("status", "")
                              for k in sorted(gates)},
                    "artifacts": len(cred.get("artifacts") or {}),
                    "binding_ok": bind["ok"], "bad": bind["bad"]}
    meta = {"input_hash": in_hash, "input_files": in_files,
            "render_hash": h1, "render_runs": [h1, h2], "pin_ok": h1 == h2,
            "output_chars": len(md1),
            "versions": _version_chain(gd, state, signed),
            "signatures": slots, "dual_complete": dual,
            "credential": cred_out,
            "downloads": {"md_route": "/api/report/download"}}
    return {"battle": battle_info, "goal": goal_name,
            "state": {"status": state["status"], "locked": state["locked"],
                      "issued_at": state["issued_at"],
                      "gates_pass": state["gates_pass"]},
            "cover": core_p["cover"], "authorization": core_p["authorization"],
            "findings": core_p["findings"], "evidence": core_p["evidence"],
            "coverage": core_p["coverage"], "methodology": core_p["methodology"],
            "meta": meta, "markdown": md1}


def render_pin(goal_dir):
    """同输入同输出钉：渲染纯函数两跑 → 两次哈希+pin_ok（只读零写入）。"""
    state = _report_state(goal_dir)
    core_p = _detail_core(goal_dir)
    md1 = _build_markdown(os.path.basename(goal_dir), state, core_p)
    md2 = _build_markdown(os.path.basename(goal_dir), state, core_p)
    h1 = hashlib.sha256(md1.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(md2.encode("utf-8")).hexdigest()
    in_hash, in_files = _input_fingerprint(goal_dir)
    return {"input_hash": in_hash, "input_files": in_files,
            "render_hash": h1, "render_runs": [h1, h2], "pin_ok": h1 == h2,
            "output_chars": len(md1)}


def _norm_battle(value):
    """battle 参数归一 int（battle-N/N/int）；不可解析=None（422 面）。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    s = str(value or "")
    if s.startswith("battle-"):
        s = s[7:]
    return int(s) if s.isdigit() else None


def report_detail_route(query, ledger_dir=None, battles_dir=None):
    """路由适配层：ValueError=422（坏参）；error 形=404；缺参=400；正常=200。"""
    try:
        payload = report_detail_view(
            battles_dir=battles_dir if battles_dir else None,
            battle=query.get("battle"),
            goal=(query.get("goal") or "").strip() or None,
            ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        code = 400 if "缺 battle/goal" in payload["error"] else 404
        return code, payload
    return 200, payload


ROUTES[ROUTE_LIST] = report_list_route
ROUTES[ROUTE_DETAIL] = report_detail_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。

    UI-1 挂法（api_pages.py）：先过 Handler._session_ok 再调本口——
    dispatch(path, query, server.ledger_dir, battles_dir=server.battles_dir)。
    """
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir, battles_dir=battles_dir)
