# -*- coding: utf-8 -*-
"""tanyin-report FD 九段渲染器+时间链断言（批次 6 T13；FD 规格 b0006f2 §一/§二）。

九段→数据源映射（渲染不造数据：每段只从账本/卡片投影，任一段数据源缺失=rc 1 且
缺段清单随报错）：
  ①位置=assets/edges 图谱坐标（资产ID+表面+精确位置〔dedup_key〕）；
  ②资产与接口=read-ledger 子图投影（intent 行+触达边清单，禁手写）；
  ③漏洞描述=类型必须命中矩阵词表（shared/VOCAB.md wstg 集∪K1 基线键；不命中=渲染
    FAIL——「不进 findings 的回归断言」渲染侧兜底）；
  ④等级=tech 严重度（confidence）×biz 影响（impact）双轴并列+G-24 基线 severity_expect
    可复算字段（查表次序=K1 细类后缀→wstg 类→缺省 0.5+披露，knowledge.baseline 同口径）；
  ⑤漏洞原理=evidence 链引用（哪条请求哪个差异：EV 标题/复现命令/观察时刻/差分组）；
  ⑥POC/EXP=EV 卡 raw_request 原文转抄（字节不变，fenced 块）+原始响应摘录=EV 卡正文段
    转抄+变体参数单列「判读说明」（preconditions/role/repro_kind/网络位置/HTTP2-TLS 边界）；
  ⑦危害=EV 卡 raw_excerpt（脱敏 token 化后原文）回显引用+impact；
  ⑧修复建议=类型映射（临时缓解+根治两层）+K1 基线挂标+「修复后哪条 POC 应失效」；
  ⑨复现与验证状态=重放门三态（timeline 重放事件末值 verified/env-diff/unverified）+
    最近重放时刻；未 verified=强制披露行「未通过独立重放门」，禁宣称 verified。

时间链自证（§二）：check_time_chain 断言 evidence.captured_at < finding.added_at
（< report.issued_at 可选）；违反=(False, 违规明细)。
解析实况裁决 R-T13-2：受限 YAML 子集块标量不保留块内空行——raw_request 以无 body GET
形承载（有 body 请求的原文以工件原件为锚），渲染只转抄卡值不增删。
"""
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import cards, query_cmds  # noqa: E402
from ledger.check_cmds import REPLAY_EVENT  # noqa: E402  重放事件形态单源
from ledger.core import Session  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_VOCAB = os.path.join(_REPO, "shared", "VOCAB.md")
_K1 = os.path.join(_REPO, "knowledge", "methodology", "k1-baseline.tsv")
_RENDER_TABLES = ("intents.tsv", "findings.tsv", "assets.tsv", "edges.tsv",
                  "E-index.tsv", "matrix.tsv", "timeline.tsv")
SEGMENTS = ("位置", "涉及资产与接口", "漏洞描述", "等级", "漏洞原理",
            "POC/EXP", "危害", "修复建议", "复现与验证状态")
_TRI = {"VERIFIED": "verified", "REPAIRED": "env-diff", "REJECTED": "unverified"}
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")
# 修复建议类型映射（静态模板；K1 挂标+POC 失效标注段内拼接——零 LLM 零语义判断）
_FIX_MAP = {
    # v0.5b G2 扩全（渗透专家项：修复建议最后一公里——七族补齐）
    "authz.diff": "根治：对齐角色的对象级授权校验（服务端逐对象判属主）；临时缓解：下线暴露接口或限内网。",
    "authn.missing": "根治：管理面补认证与会话门禁；临时缓解：访问源限制+告警观测。",
    "inj.sql": "根治：参数化查询/预编译语句，禁字符串拼接；临时缓解：WAF 规则+错误回显收敛。",
    "inj.xss": "根治：输出编码按上下文（HTML/JS/URL 分境）+CSP 收敛；临时缓解：输入过滤黑名单+WAF。",
    "inj.ssrf": "根治：目标白名单+协议/内网段禁入（含重定向跟进封禁）；临时缓解：出口代理黑白名单+禁 169.254/127./10./172.16-31。",
    "inj.deser": "根治：禁不可信反序列化（换 JSON/带签名的序列化）；临时缓解：类型白名单+依赖升级去 gadget。",
    "rce.cmd": "根治：命令参数化（数组形+禁 shell=True）+命令白名单；临时缓解：运行账户降权+沙箱+出网封禁。",
    "idor": "根治：资源属主校验进服务端（逐对象 authz，勿信前端传参 id）；临时缓解：id 加随机化+访问审计告警。",
    "lfi.path": "根治：路径参数白名单化+chroot/base_dir 校验（realpath 前缀比对）；临时缓解：禁 ../ 与绝对路径输入+文件黑名单。",
    "redirect.open": "根治：跳转目标白名单（同域/显式登记域）；临时缓解：跳转中间确认页+禁参数直跳外域。",
}
_FIX_DEFAULT = "按类型基线处置（先临时缓解收敛暴露面，再根治；两层建议均挂 K1 基线条目复评）。"


def _idx(t, col):
    return TABLES[t].index(col)


def _cell(t, r, col):
    return r[_idx(t, col)]


def _parse_iso(s):
    """ISO8601→aware datetime（Z→+00:00；naive 按 UTC；不可解析=None）。"""
    s = (s or "").strip()
    if not _ISO.match(s):
        return None
    t = s.replace(" ", "T")
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    if len(t) > 5 and t[-5] in "+-" and ":" not in t[-5:]:
        t = t[:-2] + ":" + t[-2:]
    try:
        dt = datetime.fromisoformat(t)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _k1_rows():
    """K1 基线表 {行键: (severity_expect, cost_hint, rationale_brief)}（缺文件=空表）。"""
    out = {}
    try:
        with open(_K1, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return out
    for ln in lines[1:]:
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if len(parts) >= 3:
            out[parts[0]] = (parts[1], parts[2], parts[3] if len(parts) > 3 else "")
    return out


def _vocab_set():
    """矩阵词表=VOCAB wstg 集∪K1 基线行键（含细类后缀）。"""
    vocab = set()
    try:
        with open(_VOCAB, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln.startswith("- "):
                    vocab.add(ln[2:].strip().split()[0])
    except OSError:
        pass
    for key in _k1_rows():
        vocab.add(key)
        if ":" in key:
            vocab.add(key.split(":", 1)[1])
    return vocab


def _k1_lookup(vuln_class):
    """查表次序=细类后缀→wstg 类→缺省 0.5（knowledge.baseline_lookup 同口径）。"""
    rows = _k1_rows()
    if vuln_class in rows:
        return float(rows[vuln_class][0]), vuln_class
    for key, v in rows.items():
        if ":" in key and key.split(":", 1)[1] == vuln_class:
            return float(v[0]), key
    parent = vuln_class.split(":", 1)[0]
    if parent in rows:
        return float(rows[parent][0]), parent
    return 0.5, ""


def _latest_by_id(s, t):
    return query_cmds.latest_by(s.rows(t), t, ["id"])


def _fd_row(s, fd_id):
    return _latest_by_id(s, "findings.tsv").get((fd_id,))


def _type_anchor(s, fd_row):
    """矩阵锚行：同 intent 的行中优先 state=x（命中行），取最后一条（事件溯源末值）。"""
    iid = _cell("findings.tsv", fd_row, "intent_id")
    ii = _idx("matrix.tsv", "intent_id")
    hits = [r for r in s.rows("matrix.tsv") if r[ii] == iid]
    pool = [r for r in hits if _cell("matrix.tsv", r, "state").strip() == "x"] or hits
    if not pool:
        return None
    r = pool[-1]
    return _cell("matrix.tsv", r, "attack_surface"), _cell("matrix.tsv", r, "vuln_class")


def _evidence_rows(s, fd_row):
    """finding 证据行（evidence_ids+control_evidence_ids 引用闭合内）。"""
    ids = []
    for col in ("evidence_ids", "control_evidence_ids"):
        ids += [x for x in _cell("findings.tsv", fd_row, col).split(";") if x]
    eindex = _latest_by_id(s, "E-index.tsv")
    return [eindex[(i,)] for i in ids if (i,) in eindex]


def _load_card(goal_dir, eindex_row):
    p = os.path.join(goal_dir, _cell("E-index.tsv", eindex_row, "card_path"))
    try:
        return cards.parse_ev_card(p)
    except (cards.CardError, OSError):
        return None


def _harm_lines(ev_pairs):
    """v0.6 H2：逐 EV 危害行——每张有回显的 EV 各占一行（修「只转抄首 EV」结构冲突）。"""
    return ["- %s: %s" % (eid, ex.strip())
            for eid, ex in ev_pairs if ex and ex.strip()]


def _replay_line(s, fd_id, ev_ids):
    """三态+最近重放时刻（timeline 重放事件末值，事件溯源序）。"""
    ev_i = _idx("timeline.tsv", "event")
    ts_i = _idx("timeline.tsv", "timestamp")
    state, last_ts = None, ""
    for r in s.rows("timeline.tsv"):
        m = REPLAY_EVENT.match(r[ev_i])
        if m and (m.group(1) == fd_id or m.group(1) in ev_ids):
            state, last_ts = m.group(2), r[ts_i]
    return _TRI.get(state, "unverified"), last_ts


def _segment_text(goal_dir, s, fd_row):
    """逐段投影；返回 (sections, missing, fatal)。"""
    missing, fatal = [], []
    fd_id = _cell("findings.tsv", fd_row, "id")
    anchor = _type_anchor(s, fd_row)
    evs = _evidence_rows(s, fd_row)
    ev_cards = [(r, _load_card(goal_dir, r)) for r in evs]
    poc = next(((r, c) for r, c in ev_cards
                if c and (c.get("raw_request") or "").strip()), None)
    excerpt = next(((_cell("E-index.tsv", r, "raw_excerpt"))
                    for r, _c in ev_cards
                    if _cell("E-index.tsv", r, "raw_excerpt").strip()), "")
    ev_ids = [_cell("E-index.tsv", r, "id") for r, _c in ev_cards]
    replay_tri, replay_ts = _replay_line(s, fd_id, ev_ids)
    verified = _cell("findings.tsv", fd_row, "exploitation_status") == "verified"
    sections = {}
    aid = _cell("findings.tsv", fd_row, "affected_asset_id")
    asset = _latest_by_id(s, "assets.tsv").get((aid,)) if aid else None
    iid = _cell("findings.tsv", fd_row, "intent_id")
    intent = _latest_by_id(s, "intents.tsv").get((iid,))
    # ①位置
    if asset is None or anchor is None:
        missing.append("①位置（资产/矩阵锚缺失: %s）" % (aid or "无"))
    else:
        sections["位置"] = "\n".join([
            "- 资产: %s（%s）%s" % (aid, _cell("assets.tsv", asset, "type"),
                                   _cell("assets.tsv", asset, "value")),
            "- 攻击表面: %s" % anchor[0],
            "- 精确位置: %s" % _cell("findings.tsv", fd_row, "dedup_key"),
        ])
    # ②涉及资产与接口（read-ledger 子图投影）
    if intent is None:
        missing.append("②涉及资产与接口（intent 缺失: %s）" % iid)
    else:
        edges = [r for r in s.rows("edges.tsv")
                 if iid in (_cell("edges.tsv", r, "source_id"),
                            _cell("edges.tsv", r, "target_id"))
                 or aid and aid in (_cell("edges.tsv", r, "source_id"),
                                    _cell("edges.tsv", r, "target_id"))]
        lines = ["- 意图: %s（engine=%s kind=%s status=%s）" % (
            iid, _cell("intents.tsv", intent, "engine"),
            _cell("intents.tsv", intent, "kind"),
            _cell("intents.tsv", intent, "status"))]
        for e in edges:
            lines.append("- 边: %s %s %s→%s（provenance=%s）" % (
                _cell("edges.tsv", e, "id"), _cell("edges.tsv", e, "kind"),
                _cell("edges.tsv", e, "source_id"), _cell("edges.tsv", e, "target_id"),
                _cell("edges.tsv", e, "provenance")))
        if not edges:
            lines.append("- 图谱触达边=0（read-ledger 投影）")
        sections["涉及资产与接口"] = "\n".join(lines)
    # ③漏洞描述（类型必须命中矩阵词表）
    if anchor is None:
        missing.append("③漏洞描述（矩阵锚缺失）")
    else:
        if anchor[1] not in _vocab_set():
            fatal.append("类型不在矩阵词表: %s（词表=shared/VOCAB.md∪K1 基线键）" % anchor[1])
        sections["漏洞描述"] = "\n".join([
            "- 类型: %s（命中矩阵词表）" % anchor[1],
            "- 影响: %s" % _cell("findings.tsv", fd_row, "description_brief"),
        ])
    # ④等级（双轴并列+G-24 基线可复算字段）
    if anchor is None:
        missing.append("④等级（矩阵锚缺失）")
    else:
        sev, key = _k1_lookup(anchor[1])
        sections["等级"] = "\n".join([
            "- tech 严重度: %s" % _cell("findings.tsv", fd_row, "confidence"),
            "- 类型基线 severity_expect=%s（键=%s，G-24 基线表可复算）" % (sev, key or "缺省 0.5"),
            "- biz 影响: %s（资产=%s）" % (_cell("findings.tsv", fd_row, "impact"), aid),
        ])
    # ⑤漏洞原理（evidence 链引用）
    if not evs:
        missing.append("⑤漏洞原理（证据链为空）")
    else:
        lines = []
        for r in evs:
            pg = _cell("E-index.tsv", r, "pair_group")
            lines.append("- %s %s：repro=%s（observed_at=%s，network=%s%s）" % (
                _cell("E-index.tsv", r, "id"), _cell("E-index.tsv", r, "title"),
                _cell("E-index.tsv", r, "repro_command"),
                _cell("E-index.tsv", r, "observed_at"),
                _cell("E-index.tsv", r, "network_position"),
                ("，差分组=" + pg) if pg.strip() else ""))
        sections["漏洞原理"] = "\n".join(lines)
    # ⑥POC/EXP（EV 卡原文转抄+判读说明单列）
    if poc is None:
        missing.append("⑥POC/EXP（无含 raw_request 的 EV 卡）")
    else:
        r, c = poc
        raw = c.get("raw_request") or ""
        lines = ["### raw_request（EV 卡原文转抄，字节不变；Burp 直贴）", "", "~~~", raw, "~~~", ""]
        try:
            with open(os.path.join(goal_dir, _cell("E-index.tsv", r, "card_path")),
                      encoding="utf-8") as f:
                body = f.read()
        except OSError:
            body = ""
        tail = body.split("## 原始响应摘录（脱敏+定长）与判定依据", 1)
        if len(tail) == 2 and tail[1].strip():
            lines += ["### 原始响应摘录（EV 卡正文转抄）", "", tail[1].strip(), ""]
        note = ["- preconditions: %s" % (c.get("preconditions") or "无"),
                "- role: %s" % (c.get("role") or "未适用"),
                "- repro_kind: %s" % _cell("E-index.tsv", r, "repro_kind"),
                "- network_position: %s" % _cell("E-index.tsv", r, "network_position"),
                "- HTTP/2 帧/TLS 指定类变体不入文本直贴——单列本「判读说明」段披露（裁决 B）"]
        lines += ["### 判读说明（变体参数单列，不改原始证据）", ""] + note + [""]
        sections["POC/EXP"] = "\n".join(lines)
    # ⑦危害（v0.6 H2：逐 EV 全量回显——修「只转抄首 EV vs lint 查全 EV」结构冲突）
    _hl = _harm_lines([(_cell("E-index.tsv", r, "id"),
                        _cell("E-index.tsv", r, "raw_excerpt"))
                       for r, _c in ev_cards])
    if not _hl:
        missing.append("⑦危害（无 raw_excerpt 回显引用）")
    else:
        sections["危害"] = "\n".join(
            ["- 实际回显（EV 卡 raw_excerpt，脱敏 token 化后原文，逐 EV 全量）:"] + _hl
            + ["- 此环境影响: %s（资产=%s）" % (
                _cell("findings.tsv", fd_row, "impact"), aid)])
    # ⑧修复建议（类型映射+K1 挂标+POC 应失效标注）
    if anchor is None:
        missing.append("⑧修复建议（矩阵锚缺失）")
    else:
        k1 = _k1_rows()
        k1_key = anchor[1] if anchor[1] in k1 else next(
            (k for k in k1 if ":" in k and k.split(":", 1)[1] == anchor[1]), anchor[1])
        if k1_key in k1:
            k1_line = "K1 挂标: %s（cost_hint=%s，rationale=%s）" % (
                k1_key, k1[k1_key][1], k1[k1_key][2])
        else:
            k1_line = "K1 挂标: %s（基线无行，缺省 0.5 披露）" % k1_key
        lines = ["- 建议: %s" % _FIX_MAP.get(anchor[1], _FIX_DEFAULT), "- " + k1_line]
        if poc is not None:
            lines.append("- 修复后哪条 POC 应失效: %s（请求不再复现=修复有效）"
                         % _cell("E-index.tsv", poc[0], "id"))
        sections["修复建议"] = "\n".join(lines)
    # ⑨复现与验证状态（三态+最近重放时刻+强制披露）
    st_lines = ["- 重放门三态: %s" % replay_tri]
    if replay_ts:
        st_lines.append("- 最近重放时刻: %s" % replay_ts)
    if verified:
        st_lines.append("- verified：是（独立重放门通过）")
    else:
        st_lines.append("- 未通过独立重放门：本 finding 未维持 verified（三态=%s），"
                        "不得宣称 verified" % replay_tri)
    sections["复现与验证状态"] = "\n".join(st_lines)
    return sections, missing, fatal


def _require_render_tables(goal_dir):
    missing = [t for t in _RENDER_TABLES if not os.path.isfile(os.path.join(goal_dir, t))]
    if missing:
        raise EnvironmentError("缺表（渲染前置）: " + ", ".join(missing))


def render_fd(goal_dir, fd_id):
    """渲染一张 FD 九段 markdown。返回 (rc, md)：rc=0 且 md=九段全文；rc=1 时 md=缺段/词表 FAIL 明细。"""
    _require_render_tables(goal_dir)
    s = Session(goal_dir)
    fd_row = _fd_row(s, fd_id)
    if fd_row is None:
        return 1, "渲染 FAIL: findings 无此 id: %s" % fd_id
    sections, missing, fatal = _segment_text(goal_dir, s, fd_row)
    if missing or fatal:
        msgs = (["缺段: " + "; ".join(missing)] if missing else []) + fatal
        return 1, "渲染 FAIL: " + "；".join(msgs)
    title = _cell("findings.tsv", fd_row, "title")
    parts = ["# %s · %s" % (fd_id, title), ""]
    for seg in SEGMENTS:
        parts.append("## " + seg)
        parts.append(sections[seg])
        parts.append("")
    return 0, "\n".join(parts)


def active_fd_ids(s):
    """报告面 active finding id 集（report_agg 同口径：仅 status==active，R-T12-1）。"""
    latest = _latest_by_id(s, "findings.tsv")
    return sorted(k[0] for k, r in latest.items()
                  if _cell("findings.tsv", r, "status") == "active")


def check_time_chain(goal_dir, issued_at=None):
    """断言 evidence.captured_at < finding.added_at（< report.issued_at 可选）。

    返回 (ok, why)；违规明细含证据/finding id；时间不可解析=fail-closed 记违规。"""
    _require_render_tables(goal_dir)
    s = Session(goal_dir)
    latest_e = _latest_by_id(s, "E-index.tsv")
    issued = _parse_iso(issued_at) if issued_at else "skip"
    if issued is None:
        return False, "issued_at 不可解析: %r" % issued_at
    bad = []
    for key, f in sorted(_latest_by_id(s, "findings.tsv").items()):
        if _cell("findings.tsv", f, "status") != "active":
            continue
        fid = key[0]
        added_raw = _cell("findings.tsv", f, "created")
        added = _parse_iso(added_raw)
        if issued_at and added is not None and added >= issued:
            bad.append("%s: added_at(%s) >= issued_at(%s)" % (fid, added_raw, issued_at))
        ev_ids = [x for col in ("evidence_ids", "control_evidence_ids")
                  for x in _cell("findings.tsv", f, col).split(";") if x]
        pairs = [latest_e[(i,)] for i in ev_ids if (i,) in latest_e]
        pairs += [r for k, r in sorted(latest_e.items())
                  if _cell("E-index.tsv", r, "linked_finding") == fid]
        seen = set()
        for r in pairs:
            evid = _cell("E-index.tsv", r, "id")
            if evid in seen:
                continue
            seen.add(evid)
            cap_raw = _cell("E-index.tsv", r, "observed_at")
            cap = _parse_iso(cap_raw)
            if cap is None or added is None:
                bad.append("%s/%s: 时间不可解析（captured=%r added=%r）——时间链无法自证"
                           % (evid, fid, cap_raw, added_raw))
            elif cap >= added:
                bad.append("%s: captured_at(%s) >= %s added_at(%s)——先有证据后有结论被违反"
                           % (evid, cap_raw, fid, added_raw))
    if bad:
        return False, "；".join(bad)
    return True, ""


def render_all(goal_dir, outdir):
    """全部 active FD 渲染落盘 outdir/<fd>.md。返回 (rc, [(fd, rc, msg)])。"""
    _require_render_tables(goal_dir)
    s = Session(goal_dir)
    results = []
    os.makedirs(outdir, exist_ok=True)
    for fid in active_fd_ids(s):
        rc, md = render_fd(goal_dir, fid)
        if rc == 0:
            with open(os.path.join(outdir, fid + ".md"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(md)
            print("OK\trender\t" + fid)
        else:
            print("FAIL\trender\t" + fid + "\t" + md)
        results.append((fid, rc, md))
    return (0 if all(rc == 0 for _f, rc, _m in results) else 1), results


def cli_render(goal_dir, fd, all_flag, out):
    """tanyin-report render 子命令（--fd <id> | --all；--out 文件路径（--fd）或目录（--all））。"""
    try:
        if all_flag:
            outdir = out or os.path.join("report", "draft")
            rc, _results = render_all(goal_dir, outdir)
            return rc
        if not fd:
            sys.stderr.write("用法: render --fd <FD-id> | --all [--out <路径>]\n")
            return 2
        rc, md = render_fd(goal_dir, fd)
        if rc != 0:
            sys.stderr.write(md + "\n")
            return 1
        if out:
            path = out
        else:
            path = os.path.join(goal_dir, "report", "draft", fd + ".md")
        if os.path.isdir(path):
            path = os.path.join(path, fd + ".md")
        ddir = os.path.dirname(path)
        if ddir:
            os.makedirs(ddir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("OK\t" + path)
        return 0
    except EnvironmentError as e:
        sys.stderr.write("环境问题: " + str(e) + "\n")
        return 2

