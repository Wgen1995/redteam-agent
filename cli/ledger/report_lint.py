# -*- coding: utf-8 -*-
"""tanyin-report lint/签发门（批次 6 T14）——G-25 Burp 直贴 lint+九段齐+合规六要素+门聚合。

裁决 B（G-25 收口；契约 06 v3 勘误同笔）：
- raw_request=HTTP/1.x 报文文本字节原样（header 原文顺序不重排不补不改、body 原文、
  行尾按原文保留）——Burp Repeater 粘贴即发。
- 「Burp 可贴」机检四规则（burp_pasteable）：①纯文本可解码（无二进制字节/BOM）
  ②请求行形如 METHOD SP PATH SP HTTP/x.x ③含至少一个 Host 头 ④非空 body 有空行分隔；
  HTTP/2 帧/TLS 指定内容出现于 raw=FAIL（why 载「判读说明」——单列披露）。
- Host/Connection 头归属=原文为准，渲染器不重造不增删；渲染只转抄：与 E-index 双指纹
  不符一字=lint FAIL（dual 指纹门=norm.artifact_hashes 单源复算）。

sign_gate 聚合门（出口清单 #10）：全部 active FD 渲染 rc==0+九段齐+burp lint PASS+双指纹
+时间链（issued_at=ts）+redact-scan 零泄漏（子进程）+cleanup-checklist rc==0（子进程——
P6 清理门接线，命令零改动）+tier 披露在+合规六要素齐+禁空话句式；任一不过=rc 1 且 FAIL
明细落报告；全过=rc 0 且落 report/signed/pass.json（签发凭证：goal+ts+各门结果）。
lint=同门不落凭证；sign=lint+凭证（+Task 15 write_all 接线点——本批披露行明示未接线）。
退出码 0/1/2（ENV=缺表等环境问题）。
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import report_agg, report_render  # noqa: E402
from ledger.core import Session  # noqa: E402
from ledger.norm import artifact_hashes  # noqa: E402  双指纹单源（批次 4 评审 C-1）
from ledger.schemas import TABLES  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LEDGER = os.path.join(_REPO, "cli", "tanyin-ledger")
_ENV = {**os.environ, "PYTHONUTF8": "1"}
SEGMENTS = report_render.SEGMENTS   # 九段名单源（渲染器单处定义）
_BAN = ("可能造成重大损失", "危害极大", "影响极其恶劣", "存在重大安全隐患")  # 禁空话句式表


def burp_pasteable(raw):
    """裁决 B 四规则机检。返回 (ok, why)；HTTP/2 帧/TLS 形态 why 必载「判读说明」。"""
    why = []
    if not isinstance(raw, str) or not raw.strip():
        return False, ["raw_request 空或非文本（①失败）"]
    if raw.startswith("\ufeff"):
        why.append("含 BOM（①纯文本可解码失败）")
    for ch in raw:
        if ord(ch) < 32 and ch not in "\t\n\r":
            why.append("含二进制字节 0x%02x（①纯文本可解码失败）" % ord(ch))
            break
    if "HTTP/2" in raw or re.search(r"[\x16\x14\x17]\x03[\x00-\x04]", raw):
        why.append("HTTP/2 帧/TLS 指定内容不入文本直贴——单列「判读说明」段披露（裁决 B）")
    lines = raw.splitlines()
    if not lines or not re.match(r"^[A-Z]+ \S+ HTTP/1\.[01]$", lines[0].strip()):
        why.append("请求行非 METHOD SP PATH SP HTTP/x.x 形（②失败）: %r"
                   % (lines[0] if lines else ""))
    else:
        if not any(ln.lower().startswith("host:") for ln in lines[1:]):
            why.append("缺 Host 头（③失败）")
        if not any(not ln.strip() for ln in lines[1:]):
            rest = lines[1:]
            if any(":" not in ln for ln in rest):
                why.append("非空 body 未有空行分隔（④失败）")
    return (not why), why


def nine_segments(md):
    """缺段清单（空=九段齐；段锚=行首「## 段名」，名单源=report_render.SEGMENTS）。"""
    present = {ln.strip() for ln in md.splitlines()}
    return [seg for seg in SEGMENTS if ("## " + seg) not in present]


def empty_rhetoric(md):
    """禁空话句式命中清单（T13 段⑦注记的 Task 14 落地面；命中行:短语）。"""
    hits = []
    for i, ln in enumerate(md.splitlines(), 1):
        for ban in _BAN:
            if ban in ln:
                hits.append("%d:%s" % (i, ban))
    return hits


def compliance_six(data):
    """合规六要素缺项清单（数据源=report_agg.aggregate 投影；空=齐备）。

    授权与范围声明（goal+include）/方法学映射 WSTG（矩阵词表锚 filled≥1）/覆盖度与
    局限性（limits+matrix+coverage 投影键在档）/技术×业务风险分级（findings 双轴非空）
    /整改优先级与复测建议（findings 携 replay_state 复测依据）/等保占位段（占位常量，
    T15 模板渲染）。"""
    missing = []
    goal = data.get("goal") or {}
    counts = (data.get("scope_summary") or {}).get("counts") or {}
    if not goal.get("id") or not counts.get("include"):
        missing.append("授权与范围声明（goals/scope include 缺）")
    if not (data.get("matrix") or {}).get("filled"):
        missing.append("方法学映射 WSTG（矩阵 filled 空——类型词表锚缺）")
    for key in ("limits", "matrix", "coverage"):
        if key not in data:
            missing.append("覆盖度与局限性（投影键 %s 缺）" % key)
            break
    findings = data.get("findings") or []
    if not all(f.get("tech_sev") and f.get("biz_impact") for f in findings):
        missing.append("技术×业务风险分级（findings 双轴缺）")
    if not all(f.get("replay_state") for f in findings):
        missing.append("整改优先级与复测建议（findings 复测依据缺）")
    return missing


def _subprocess_gate(name, args, gates):
    """fail-closed 子进程门（tanyin-ledger 面退出码 0=过）；rc=2 视为门 FAIL 明细载。"""
    try:
        r = subprocess.run([sys.executable, _LEDGER] + args, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=120, env=_ENV)
    except subprocess.TimeoutExpired:
        gates[name] = {"status": "FAIL", "detail": "子进程超时"}
        return False
    ok = r.returncode == 0
    detail = (r.stdout.strip().splitlines() or [""])[0][:160]
    gates[name] = {"status": "PASS" if ok else "FAIL",
                   "detail": detail + ("" if ok else " rc=%d" % r.returncode)}
    return ok


def _fd_checks(goal_dir, s, fd_id, fd_row, draft_path, gates):
    """单 FD 渲染/九段/burp/双指纹门；返回全部通过与否。"""
    ok_all = True
    if os.path.isfile(draft_path):
        with open(draft_path, encoding="utf-8") as f:
            md = f.read()
        src = "draft"
    else:
        rc, md = report_render.render_fd(goal_dir, fd_id)
        src = "render"
        if rc != 0:
            g = gates.setdefault("render", {"status": "FAIL", "detail": ""})
            g["status"] = "FAIL"
            g["detail"] += ("%s: %s；" % (fd_id, md))
            return False
        os.makedirs(os.path.dirname(draft_path), exist_ok=True)
        with open(draft_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
    miss = nine_segments(md)
    if miss:
        gates["nine_segments"].update(
            status="FAIL", detail=gates["nine_segments"]["detail"]
            + "%s 缺段: %s；" % (fd_id, ",".join(miss)))
        ok_all = False
    evs = report_render._evidence_rows(s, fd_row)
    for r in evs:
        ei = TABLES["E-index.tsv"]
        card = report_render._load_card(goal_dir, r)
        raw = (card or {}).get("raw_request") or ""
        if not raw.strip():
            continue
        ok, why = burp_pasteable(raw)
        if not ok:
            det = gates["burp_pasteable"]["detail"] \
                + "%s/%s: %s；" % (fd_id, r[ei.index("id")], "; ".join(why))
            gates["burp_pasteable"].update(status="FAIL", detail=det)
            ok_all = False
        art = r[ei.index("artifact_path")]
        art_path = os.path.join(goal_dir, art) if art else ""
        if not art or not os.path.isfile(art_path):
            det = gates["dual_fingerprint"]["detail"] \
                + "%s/%s: 工件缺，双指纹不可核；" % (fd_id, r[ei.index("id")])
            gates["dual_fingerprint"].update(status="FAIL", detail=det)
            ok_all = False
            continue
        with open(art_path, "rb") as f:
            data = f.read()
        raw_h, norm_h = artifact_hashes(data)
        if (raw_h, norm_h) != (r[ei.index("content_hash_raw")],
                               r[ei.index("content_hash_norm")]):
            det = gates["dual_fingerprint"]["detail"] \
                + "%s/%s: 与 E-index 双指纹不符一字=FAIL（裁决 B）" % (fd_id, r[ei.index("id")])
            gates["dual_fingerprint"].update(status="FAIL", detail=det)
            ok_all = False
        elif src == "draft" and raw not in md:
            det = gates["dual_fingerprint"]["detail"] \
                + "%s/%s: 渲染转抄与 EV 卡原文不符一字=FAIL（裁决 B）" % (fd_id, r[ei.index("id")])
            gates["dual_fingerprint"].update(status="FAIL", detail=det)
            ok_all = False
    return ok_all


def sign_gate(goal_dir, ts, write_credential=True):
    """签发门聚合。返回 (rc, report)；全过=0 且（write_credential 时）落
    report/signed/pass.json；任一门不过=1；缺表等环境问题=2。"""
    gates = {k: {"status": "PASS", "detail": ""}
             for k in ("render", "nine_segments", "burp_pasteable", "dual_fingerprint",
                       "time_chain", "redact_scan", "cleanup_checklist", "tier_disclosure",
                       "compliance_six", "empty_rhetoric", "aggregate")}
    try:
        data = report_agg.aggregate(goal_dir, ts or "2026-09-24T00:00:00Z")
    except EnvironmentError as e:
        return 2, {"error": "ENV: %s" % e}
    os.makedirs(os.path.join(goal_dir, "report", "draft"), exist_ok=True)
    s = Session(goal_dir)
    ok_all = True
    fds = report_render.active_fd_ids(s)
    for fd_id in fds:
        fd_row = report_render._fd_row(s, fd_id)
        if not _fd_checks(goal_dir, s, fd_id, fd_row,
                          os.path.join(goal_dir, "report", "draft", fd_id + ".md"), gates):
            ok_all = False
    ok, why = report_render.check_time_chain(goal_dir, issued_at=ts)
    if not ok:
        gates["time_chain"].update(status="FAIL", detail=why)
        ok_all = False
    if not _subprocess_gate("redact_scan",
                            ["redact-scan", "--goal-dir", os.path.abspath(goal_dir),
                             "--target=" + os.path.abspath(os.path.join(goal_dir, "report"))],
                            gates):
        ok_all = False
    if not _subprocess_gate("cleanup_checklist",
                            ["cleanup-checklist", "--goal-dir", os.path.abspath(goal_dir),
                             "--verify"], gates):
        ok_all = False
    tier = data.get("tier_disclosure") or {}
    if not (tier.get("guard_tier") or tier.get("timeline_tier_last")):
        gates["tier_disclosure"].update(status="FAIL", detail="guard_tier/timeline tier 均缺")
        ok_all = False
    miss6 = compliance_six(data)
    if miss6:
        gates["compliance_six"].update(status="FAIL", detail="；".join(miss6))
        ok_all = False
    # 禁空话句式（已落盘/新渲染的 draft 全查）
    draft_dir = os.path.join(goal_dir, "report", "draft")
    for fn in sorted(os.listdir(draft_dir)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(draft_dir, fn), encoding="utf-8") as f:
            hits = empty_rhetoric(f.read())
        if hits:
            gates["empty_rhetoric"].update(status="FAIL", detail="%s: %s" % (fn, hits))
            ok_all = False
    if not ok_all:
        for g in gates.values():
            if g["status"] == "PASS":
                g["detail"] = ""
        return 1, {"goal": os.path.basename(os.path.normpath(goal_dir)), "ts": ts,
                   "gates": gates}
    for g in gates.values():
        g["detail"] = ""
    rep = {"goal": os.path.basename(os.path.normpath(goal_dir)), "ts": ts, "gates": gates}
    if write_credential:
        signed = os.path.join(goal_dir, "report", "signed")
        os.makedirs(signed, exist_ok=True)
        payload = json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
        with open(os.path.join(signed, "pass.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
    return 0, rep


def cmd_lint(goal_dir, ts):
    """tanyin-report lint——同签发门判定，不落凭证（exit 同 gate）。"""
    rc, rep = sign_gate(goal_dir, ts, write_credential=False)
    print(json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1))
    return rc


def cmd_sign(goal_dir, ts):
    """tanyin-report sign——lint 同判定+落签发凭证（+T15 write_all 接线点，本批披露未接线）。"""
    if not ts:
        sys.stderr.write("用法: sign --goal-dir D --timestamp T（issued_at 显式，禁墙钟）\n")
        return 2
    rc, rep = sign_gate(goal_dir, ts, write_credential=True)
    print(json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1))
    if rc == 0:
        print("OK\t签发凭证 report/signed/pass.json（goal=%s ts=%s）"
              % (os.path.basename(os.path.normpath(goal_dir)), ts))
        print("DISCLOSE\t双工件写盘未接线（批次 6 T15 report_artifacts.write_all）"
              "——本跑仅落签发凭证")
    return rc


def gate_entry(goal_dir, argv):
    """phases_engine P5 断言分发入口（tanyin-redact R13 同构；argv 尾旗标原样容忍）。"""
    ts = None
    for tok in argv:
        if tok.startswith("--timestamp="):
            ts = tok.split("=", 1)[1]
    return cmd_lint(goal_dir, ts)


GATE_ENTRY = gate_entry

