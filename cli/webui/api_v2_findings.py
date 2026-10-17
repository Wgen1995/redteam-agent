# -*- coding: utf-8 -*-
"""api_v2_findings（T1·P6）——漏洞详情五区只读投影，路由前缀 /api/v2/。

舰间契约：本文件=本舰独写；只读投影零写入（core.Session 只读加载，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_finding_detail.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。

两路由（全过会话门；除 login 外无豁免）：
  GET /api/v2/finding-detail?id=FD-xxx[&goal=G-xxx]
      → 五区数据单源：头区(发现行+CVSS 向量→官方分/验证状态/复测状态)
        +描述区(一句话结论+技术描述+修复建议子卡: 根因/代码位/修复后验证命令)
        +证据区(EV 卡: 类型/时刻/哈希/最新重放裁决/工件哈希核验)
        +重放史区(timeline replay-probe 行 × replay/<EV>/<n>.json 逐次对齐:
          次序/时刻/结果/耗时[elapsed_ms 缺=空]/触发方式[actor 复测=自动])
        +生命线(首次发现→各次重放→自动复测→客户反馈→当前态)
        +证据链完整性(timeline 链逐行重算 + 工件哈希重算 + 引用闭合 → 绿条/红警)。
  GET /api/v2/evidence-raw?id=EV-xxx
      → 证据区「查看原始报文」懒载：请求(卡片 raw_request)+响应(工件原文；
        is_http=工件以 HTTP/ 状态行起 → head=仅头/full=全文)。

CVSS：向量单源——优先序=发现卡 front-matter cvss_vector → 发现卡正文 regex
（描述/复现）→ 证据原文 regex（工件+摘录；UI-1 实勘 findings 行无向量字段，
向量在场才实算，禁虚构）→ v3.1 基础分官方公式服务端计算（缺向量/缺度量=
『待评定』，不造分；等级=真实 impact 高中低）。
"""
import json
import math
import os
import re

from ledger import core
from ledger.norm import artifact_hashes

ROUTE_DETAIL = "/api/v2/finding-detail"
ROUTE_RAW = "/api/v2/evidence-raw"
ROUTES = {ROUTE_DETAIL: None, ROUTE_RAW: None}   # 尾部赋真身（前向引用）

_REPLAY_PAT = re.compile(r"replay-probe (\S+) verdict=(\S+)")   # tanyin-replay 同形
_FEEDBACK_PAT = re.compile(r"feedback|客户反馈", re.I)
_CVSS_VEC_RE = re.compile(r"CVSS:3\.\d/(?:[A-Z]{1,2}:[A-Za-z]+/?)+")
_HASH_TRUNC = 12

# CVSS v3.1 基础分权重（FIRST 官方规格表；PR 改域另有表，见 _cvss_score）
_CVSS_W = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20},
    "AC": {"L": 0.77, "H": 0.44},
    "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
    "PR_C": {"N": 0.85, "L": 0.68, "H": 0.50},      # Scope Changed
    "UI": {"N": 0.85, "R": 0.62},
    "CIA": {"H": 0.56, "L": 0.22, "N": 0.0},
}


def _roundup1(x):
    """FIRST 官方 roundup：先 round(x*100000) 再 ceil 到一位小数（浮点免疫）。"""
    return math.ceil(round(x * 100000) / 10000) / 10


def _cvss_metrics(vector):
    """向量串 → {AV:..,AC:..,PR:..,UI:..,S:..,C:..,I:..,A:..}；缺度量=None。"""
    out = {}
    for part in vector.split("/")[1:]:
        if ":" in part:
            k, _, v = part.partition(":")
            out[k] = v
    return out


def cvss_score_from_vector(vector):
    """v3.1 基础分（官方公式）；八度量缺一=无法评定 → None（待评定律）。"""
    m = _cvss_metrics(vector)
    need = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")
    if any(m.get(k) not in _CVSS_W.get(k, _CVSS_W["CIA"]) and
           not (k in ("S",) and m.get(k) in ("U", "C")) for k in need):
        return None
    try:
        av = _CVSS_W["AV"][m["AV"]]
        ac = _CVSS_W["AC"][m["AC"]]
        ui = _CVSS_W["UI"][m["UI"]]
        pr = (_CVSS_W["PR_C"] if m["S"] == "C" else _CVSS_W["PR"])[m["PR"]]
        c, i, a = (_CVSS_W["CIA"][m[k]] for k in ("C", "I", "A"))
    except KeyError:
        return None
    iss = 1 - (1 - c) * (1 - i) * (1 - a)
    if m["S"] == "C":
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss
    if impact <= 0:
        return 0.0
    return _roundup1(min(impact + 8.22 * av * ac * pr * ui, 10))


# ---------------------------------------------------------------- 卡片解析 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _read_text_loose(path):
    """宽容读（bytes→utf-8 replace）：证据工件可含非法 utf-8/二进制段，不炸。"""
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except OSError:
        return ""


def _split_card(text):
    """'---\n...\n---\n正文' → (front-matter 文本, 正文)；非卡形=None。"""
    if not text.startswith("---"):
        return None, ""
    parts = text.split("\n---\n", 1)
    if len(parts) != 2 or not parts[0][3:].strip():
        return None, ""
    return parts[0][3:], parts[1]


def _parse_fm(fm):
    if fm is None:
        return {}
    from ledger.phases_engine import parse_yaml, PhasesSyntaxError
    try:
        fields = parse_yaml(fm)
    except PhasesSyntaxError:
        return {}
    return fields if isinstance(fields, dict) else {}


def _card(goal_dir, card_path):
    return _split_card(_read_text(os.path.join(goal_dir, card_path)))


def _sections(body):
    """正文 '## 标题' 分节 → {标题: 文本}（findings-cards 模板同形）。"""
    secs, cur = {}, ""
    for line in body.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            secs.setdefault(cur, [])
        elif cur is not None and cur:
            secs[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in secs.items()}


def _labeled(text, label):
    """'根因: xxx' 行取值（修复建议叙述子卡三件）；缺=空串。"""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(label + ":"):
            return s[len(label) + 1:].strip()
    return ""


# ---------------------------------------------------------------- 通用小件 --

def _goal_dir(base, goal):
    """goal= 同名目录优先（本 goal 内子目录，次选同辈）——多战宿主可定位。"""
    if not goal:
        return base
    for cand in (os.path.join(base, goal), os.path.join(os.path.dirname(base), goal)):
        if os.path.isdir(cand):
            return cand
    return base


def _latest(s, tname):
    out = {}
    for r in s.rows(tname):
        out[r[0]] = r
    return out


def _replay_events(s):
    """timeline 扫描 → [(ev_id, verdict, ts, actor)] 文件序（同形 projections）。"""
    tle = {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}
    out = []
    for r in s.rows("timeline.tsv"):
        m = _REPLAY_PAT.search(r[tle["event"]])
        if m:
            out.append((m.group(1), m.group(2), r[tle["timestamp"]], r[tle["actor"]]))
    return out


def _replay_json(goal_dir, ev_id, seq):
    """replay/<EV>/<seq>.json（tanyin-replay 落盘形）；缺/坏=None。"""
    p = os.path.join(goal_dir, "replay", ev_id, "%d.json" % seq)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _trigger(actor):
    a = (actor or "").strip().lower()
    return "自动复测" if ("复测" in (actor or "") or a in ("auto", "retest")) else "手动"


def _hash_check(goal_dir, ev_row):
    """工件哈希重算 vs 在册 content_hash_raw → (ok: True/False/None, 细节)。"""
    tei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    art = ev_row[tei["artifact_path"]]
    p = os.path.join(goal_dir, art) if art else None
    if not p or not os.path.isfile(p):
        return None, "工件缺失，无法重算: %s" % (art or "（无路径）")
    with open(p, "rb") as f:
        raw, _norm = artifact_hashes(f.read())
    ok = raw == ev_row[tei["content_hash_raw"]]
    return ok, ("重算一致" if ok else "工件与在册哈希不符（疑似被改动）")


# ------------------------------------------------------------------ 投影 ① --

def finding_detail(query, ledger_dir):
    """五区全量投影 → (status, payload)。只读零写入、确定性输出。"""
    gd = _goal_dir(ledger_dir, (query.get("goal") or "").strip())
    fid = (query.get("id") or "").strip()
    if not fid:
        return 400, {"error": "缺 id 参数（FD-xxx）"}
    s = core.Session(gd)
    frow = _latest(s, "findings.tsv").get(fid)
    if frow is None:
        return 404, {"error": "发现不存在: %s" % fid}
    tf = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}

    finding = {k: frow[i] for k, i in tf.items()}

    # —— 证据装配：findings.evidence_ids ∪ linked_finding 反指（排序定序） ——
    ev_latest = _latest(s, "E-index.tsv")
    tei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    ids = [x.strip() for x in frow[tf["evidence_ids"]].split(",") if x.strip()]
    for r in s.rows("E-index.tsv"):
        if r[tei["linked_finding"]] == fid and r[0] not in ids:
            ids.append(r[0])
    events = _replay_events(s)
    by_ev = {}
    for ev_id, verdict, ts, actor in events:
        by_ev.setdefault(ev_id, []).append((verdict, ts, actor))

    evidence, hash_checks, fallback_cmds = [], [], []
    for ev_id in sorted(ids):
        r = ev_latest.get(ev_id)
        if r is None:
            hash_checks.append({"name": "证据引用", "ok": False,
                                "detail": "evidence_ids 引用未闭合: %s" % ev_id})
            continue
        runs = by_ev.get(ev_id, [])
        verdict = runs[-1][0] if runs else ""
        ok, detail = _hash_check(gd, r)
        hash_checks.append({"name": "证据哈希 " + ev_id, "ok": ok, "detail": detail})
        fm, _body = _card(gd, r[tei["card_path"]])
        fields = _parse_fm(fm)
        raw_req = (fields.get("raw_request") or "")
        repro = r[tei["repro_command"]].strip()
        if repro and repro not in fallback_cmds:
            fallback_cmds.append(repro)
        evidence.append({
            "id": ev_id, "title": r[tei["title"]],
            "source_type": r[tei["source_type"]],
            "observed_at": r[tei["observed_at"]],
            "network_position": r[tei["network_position"]],
            "repro_command": repro, "repro_kind": r[tei["repro_kind"]],
            "content_hash_raw": r[tei["content_hash_raw"]],
            "hash_trunc": r[tei["content_hash_raw"]][:_HASH_TRUNC],
            "content_hash_norm": r[tei["content_hash_norm"]],
            "artifact_path": r[tei["artifact_path"]],
            "card_path": r[tei["card_path"]],
            "raw_excerpt": r[tei["raw_excerpt"]],
            "verdict": verdict, "hash_ok": ok,
            "has_request": bool(str(raw_req).strip()),
            "has_artifact": bool(r[tei["artifact_path"]]) and
            os.path.isfile(os.path.join(gd, r[tei["artifact_path"]])),
        })

    # —— CVSS：卡 front-matter → 卡正文(描述/复现) → 证据原文；缺=待评定 ——
    fm, body = _card(gd, frow[tf["card_path"]])
    fields = _parse_fm(fm)
    secs = _sections(body)
    vector = str(fields.get("cvss_vector") or "").strip()
    src = "finding-card"
    if not vector:
        m = _CVSS_VEC_RE.search((fm or "") + "\n" + body)
        if m:
            vector, src = m.group(0).rstrip("/"), "finding-card-regex"
    if not vector:                       # 兜底③：证据原文（工件宽容读+在册摘录）
        for e in evidence:
            blob = _read_text_loose(os.path.join(gd, e["artifact_path"])) \
                if e["artifact_path"] else ""
            m = _CVSS_VEC_RE.search(blob + "\n" + e["raw_excerpt"])
            if m:
                vector, src = m.group(0).rstrip("/"), "evidence-raw"
                break
    score = cvss_score_from_vector(vector) if vector else None
    cvss = {"vector": vector, "score": score, "pending": score is None,
            "source": src if vector else ""}

    # —— 验证状态（宪法#41：三态→验证状态 已验证/待验证/已失效） ——
    expl = frow[tf["exploitation_status"]].strip()
    reproduced = [e["id"] for e in evidence if e["verdict"] == "reproduced"]
    if expl == "verified":
        v_state, v_basis = "已验证", "exploitation_status=verified"
    elif expl == "ruled_out":
        v_state, v_basis = "已失效", "exploitation_status=ruled_out"
    elif reproduced:
        v_state = "已验证"
        v_basis = "最新重放 reproduced（%s）" % reproduced[0]
    else:
        v_state, v_basis = "待验证", "尚无 reproduced 重放实证"

    # —— 重放史：timeline 行 × replay JSON 逐次对齐（次序全 timeline 序） ——
    replays = []
    per_ev_seen = {}
    for ev_id, verdict, ts, actor in events:
        if ev_id not in ev_latest or (ev_id not in ids and
                                      ev_latest[ev_id][tei["linked_finding"]] != fid):
            continue
        if ev_id in ids:
            per_ev_seen[ev_id] = per_ev_seen.get(ev_id, 0) + 1
            j = _replay_json(gd, ev_id, per_ev_seen[ev_id]) or {}
            replays.append({"seq": len(replays) + 1, "ev_id": ev_id, "at": ts,
                            "verdict": verdict,
                            "duration_ms": j.get("elapsed_ms"),
                            "trigger": _trigger(actor)})

    # —— 复测状态（P5.5 域只读摘览） ——
    if not replays:
        retest = {"state": "未复测", "runs": 0, "last_at": ""}
    else:
        last = replays[-1]["verdict"]
        state = {"reproduced": "复测完成·漏洞仍存在",
                 "not-reproduced": "复测完成·未复现（疑似已修复）",
                 "env-diff": "复测受阻·环境差异",
                 "manual": "复测完成·人工判定"}.get(last, "复测完成")
        retest = {"state": state, "runs": len(replays), "last_at": replays[-1]["at"]}

    # —— 修复建议子卡：根因/代码位/修复后验证命令（卡未撰写=诚实空） ——
    fix_text = secs.get("修复建议叙述", "")
    written = bool(fix_text) and "待 LLM 撰写" not in fix_text
    fix = {"written": written,
           "root_cause": _labeled(fix_text, "根因") if written else "",
           "code_location": _labeled(fix_text, "代码位") if written else "",
           "verify_command": _labeled(fix_text, "修复后验证") if written else "",
           "fallback_commands": fallback_cmds}

    # —— 证据链完整性：账本时间链 + 工件哈希 + 引用闭合 ——
    ok, bad = s.verify_chain()
    n_tl = len(s.rows("timeline.tsv"))
    checks = [{"name": "账本时间链", "ok": ok,
               "detail": ("断链于第 %d 行" % bad) if not ok
               else "timeline %d 行连续" % n_tl}]
    checks.extend(hash_checks)
    chain = {"ok": not any(c["ok"] is False for c in checks), "checks": checks}

    # —— 生命线：首次发现→各次重放→自动复测→客户反馈→当前态 ——
    lifeline = [{"at": frow[tf["created"]], "kind": "first",
                 "label": "首次发现", "verdict": ""}]
    tle = {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}
    for r in s.rows("timeline.tsv"):
        if _FEEDBACK_PAT.search(r[tle["event"]]):
            lifeline.append({"at": r[tle["timestamp"]], "kind": "feedback",
                             "label": "客户反馈", "verdict": ""})
    for rp in replays:
        lifeline.append({"at": rp["at"], "kind": rp["trigger"] == "自动复测" and
                         "retest" or "replay",
                         "label": rp["trigger"] == "自动复测" and "自动复测" or
                         "第 %d 次重放" % rp["seq"], "verdict": rp["verdict"]})
    lifeline.sort(key=lambda e: e["at"])
    lifeline.append({"at": replays[-1]["at"] if replays else frow[tf["created"]],
                     "kind": "current", "label": "当前·" + v_state, "verdict": ""})

    return 200, {
        "goal": os.path.basename(os.path.normpath(gd)),
        "finding": finding, "cvss": cvss,
        "verification": {"state": v_state, "basis": v_basis},
        "retest": retest, "fix": fix,
        "tech_desc": "" if "待 LLM 撰写" in secs.get("漏洞叙述", "")
        else secs.get("漏洞叙述", ""),
        "steps": secs.get("复现步骤", ""),
        "evidence": evidence, "chain": chain,
        "replays": replays, "lifeline": lifeline,
    }


# ------------------------------------------------------------------ 投影 ② --

def evidence_raw(query, ledger_dir):
    """原始报文投影 → (status, {has_request, request, response{is_http,head,full},
    hash_ok, hash_detail})；响应仅头/全文两档由页端切换（服务端全量只读给）。"""
    gd = _goal_dir(ledger_dir, (query.get("goal") or "").strip())
    ev_id = (query.get("id") or "").strip()
    if not ev_id:
        return 400, {"error": "缺 id 参数（EV-xxx）"}
    s = core.Session(gd)
    r = _latest(s, "E-index.tsv").get(ev_id)
    if r is None:
        return 404, {"error": "证据不存在: %s" % ev_id}
    tei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    fm, _body = _card(gd, r[tei["card_path"]])
    fields = _parse_fm(fm)
    request = str(fields.get("raw_request") or "").rstrip("\n")
    art = os.path.join(gd, r[tei["artifact_path"]]) if r[tei["artifact_path"]] else None
    text = _read_text(art) if art and os.path.isfile(art) else ""
    is_http = text.startswith("HTTP/")
    head = text
    if is_http:
        for sep in ("\r\n\r\n", "\n\n"):
            if sep in text:
                head = text.split(sep, 1)[0]
                break
    ok, detail = _hash_check(gd, r)
    return 200, {"id": ev_id, "title": r[tei["title"]],
                 "has_request": bool(request.strip()), "request": request,
                 "response": {"is_http": is_http, "head": head, "full": text},
                 "hash_ok": ok, "hash_detail": detail}


ROUTES[ROUTE_DETAIL] = finding_detail
ROUTES[ROUTE_RAW] = evidence_raw


def dispatch(path, query, ledger_dir):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir)
