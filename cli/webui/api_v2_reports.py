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
ROUTES = {ROUTE_LIST: None}                 # 尾部赋真身（前向引用；详情/重渲染随循环入表）

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


ROUTES[ROUTE_LIST] = report_list_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。

    UI-1 挂法（api_pages.py）：先过 Handler._session_ok 再调本口——
    dispatch(path, query, server.ledger_dir, battles_dir=server.battles_dir)。
    """
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir, battles_dir=battles_dir)
