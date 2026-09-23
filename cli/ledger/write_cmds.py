# -*- coding: utf-8 -*-
"""tanyin-ledger 写命令组（批次 1 T3-T6）——19 条写命令（契约 02 写 18 + 终审归写的 set-cred-status）。
契约：contracts/01（13 表 147 字段，contracts-v2 + v2 勘误 findings.vuln_ref/intents.kind+nday-verify）、
contracts/02（终审裁决：写 19/查 11/校验 10）、contracts/02a（41 签名终审冻结）。
共同纪律：
- 先全量校验后写入：REJECT=stderr 单行 REJECT<TAB><命令名><TAB><中文原因>、exit 1，13 表零字节变更；
- 成功=追加目标表行（列数=契约字段数，core.esc 转义）+ 追加 timeline 事件行
  （prev=现链尾 hash，hash=core.row_hash(prev, 本行其余字段按 timeline 列序不含 hash)）；
- ID 一律 core.next_id 铸造；枚举/引用闭合/dedup_key 唯一逐条校验；
- 时间戳一律取自必填 --timestamp（批次 1 确定性口径；02a 载 created/updated/timestamp 为「命令铸造」，见文末探知注记）；
- Tier 0 硬门：无 goals 行时一切写命令 REJECT，唯 add-goal 豁免（02 探知项 3 起草裁决）；
- 参数 --key=value（本批）；经临时文件/stdin 传参场景 TODO（契约 01 §1 参数化纪律，待批次补通道）。
"""
import hashlib
import ipaddress
import os
import re
import sys

from .core import TABLES, SCHEMA_VERSION, GENESIS, GATE_ORDER, esc, next_id, row_hash, write_tsv
from . import state_md

TAB = chr(9)


class Reject(Exception):
    """写前拒收（exit 1）。"""


class Usage(Exception):
    """用法错误（exit 2）。"""


# ---------------------------------------------------------------- 基础工具

def _parse(rest, allowed):
    args = {}
    for tok in rest:
        if not tok.startswith("--") or "=" not in tok:
            raise Usage("参数须为 --key=value 形式: " + tok)
        k, v = tok[2:].split("=", 1)
        if k not in allowed:
            raise Usage("未知参数 --" + k)
        if k in args:
            raise Usage("重复参数 --" + k)
        args[k] = v
    return args


def _req(args, keys):
    for k in keys:
        if not args.get(k, ""):
            raise Reject("必填参数缺失或为空: --" + k)


def _row(tname, **kw):
    r = [""] * len(TABLES[tname])
    for k, v in kw.items():
        r[TABLES[tname].index(k)] = "" if v is None else str(v)
    if "schema_version" in TABLES[tname]:
        r[TABLES[tname].index("schema_version")] = SCHEMA_VERSION
    return r


def _mv(s):
    return [x for x in (s or "").split(";") if x]


def _clean(s):
    return "".join(ch for ch in (s or "") if ord(ch) >= 32 or ch in TAB + chr(13) + chr(10))


def _trunc(s, n):
    return (s or "")[:n]


def _hex64(s):
    return bool(re.match(r"^[0-9a-fA-F]{64}$", s or ""))


_INTENT_KINDS = {"recon", "surface", "matrix-test", "deep-dive", "authz-diff", "nday-verify"}  # 01 v2 勘误
INTENT_ORIGINS = {"entity", "concept", "precedent", "adjacency", "llm", "recon-event", "mixed"}
GATES = set(GATE_ORDER)  # 九门枚举单源：core.GATE_ORDER（跳门检测同源）
EDGE_KINDS = {"spawns", "yields", "derived_from", "proves", "parent", "attack",
              "cross_ref", "evidences", "supersedes", "scope-rel"}
_EDGE_DIR = {
    "spawns": ({"goals.tsv"}, {"intents.tsv"}),
    "yields": ({"intents.tsv"}, {"facts.tsv"}),
    "derived_from": ({"facts.tsv"}, {"intents.tsv"}),
    "proves": ({"intents.tsv"}, {"findings.tsv"}),
    "parent": ({"assets.tsv"}, {"assets.tsv"}),
    "attack": ({"findings.tsv", "assets.tsv"}, {"assets.tsv", "findings.tsv"}),
    "evidences": ({"findings.tsv"}, {"E-index.tsv"}),
    "supersedes": ({"findings.tsv"}, {"findings.tsv"}),
    "scope-rel": ({"assets.tsv"}, {"scope.tsv"}),
}
_CRED_STATUS = {"active", "expired", "invalidated", "revoked"}
_APPROVE_DECISIONS = {"approved", "rejected", "exempted", "knowledge-approved"}

# redact：落盘前掩码检出「cookie/token/密码形态」真值（§8.4 关卡 2）；占位符豁免。
# 语法为高精确度起草集（契约仅载形态描述），见文末探知注记。
_VAULT_PH = re.compile(r"\{\{vault:cred-\d+\}\}")
_REDACT = [
    (re.compile(r"(?i)set-cookie\s*:"), "cookie 真值"),
    (re.compile(r"(?i)\bcookie\s*[:=]"), "cookie 真值"),
    (re.compile(r"(?i)\b(sessionid|jsessionid|phpsessid|csrf_token|xsrf-token)[-_:]"), "会话标识真值"),
    (re.compile(r"(?i)\b(bearer|token|jwt|api[_-]?key|secret|password|passwd|pwd)\b\s*[:=]\s*\S"), "凭据真值"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-.=+/]{16,}"), "token 真值"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\."), "JWT 真值"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "私钥真值"),
]


def _redact_hit(text):
    t = _VAULT_PH.sub(" ", text or "")
    for pat, why in _REDACT:
        if pat.search(t):
            return why
    return None


def _seg_int(s):
    return bool(re.match(r"^\d+[kKmMgG]?$", s or ""))


def _seg_num(s):
    return bool(re.match(r"^-?\d+(\.\d+)?[kKmMgG]?$", s or ""))


def _matcher_ok(m):
    if not m:
        return False
    if m == "*":
        return True
    if "/" in m:
        try:
            ipaddress.ip_network(m, strict=False)
            return True
        except ValueError:
            return False
    return bool(re.match(r"^(\*\.)?([a-z0-9](-*[a-z0-9])*\.)+[a-z]{2,}(:\d+)?$", m or "", re.I))


def _match_value(value, matcher):
    """CIDR/域名后缀/通配机械匹配（§4.4，非 LLM）。"""
    if not matcher:
        return False
    if "/" in matcher:
        try:
            return ipaddress.ip_address(value.strip()) in ipaddress.ip_network(matcher, strict=False)
        except ValueError:
            return False
    if matcher == "*":
        return True
    m = matcher.lower().split(":")[0]
    if m.startswith("*."):
        suf = m[2:]
        v = value.lower().rstrip(".")
        return v == suf or v.endswith("." + suf)
    v = value.lower().rstrip(".")
    return v == m or v.endswith("." + m)


def _vulnref_ok(refs):
    for s in _mv(refs):
        if not (re.match(r"^CVE-\d{4}-\d{4,}$", s, re.I) or re.match(r"^CWE-\d+$", s)
                or re.match(r"^GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}$", s)):
            return False
    return True


def _activation_ok(a):
    return len((a or "").split(";")) == 3 and all(p for p in a.split(";"))


# ---------------------------------------------------------------- 会话上下文

class Ctx(object):
    def __init__(self, goal_dir):
        from . import core
        self.core = core
        self.s = core.Session(goal_dir)
        self.gid = self.s.goal_id

    def rows(self, t):
        return self.s.data[t]

    def idx(self, t, f):
        return TABLES[t].index(f)

    def val(self, t, row, f):
        return row[self.idx(t, f)]

    def ids(self, t):
        return [r[0] for r in self.rows(t)]

    def all_ids(self):
        out = set()
        for t in ("goals.tsv", "scope.tsv", "intents.tsv", "facts.tsv", "findings.tsv",
                  "assets.tsv", "edges.tsv", "approvals.tsv", "E-index.tsv", "creds.tsv"):
            out |= set(self.ids(t))
        return out

    def latest(self, t, rid):
        out = None
        for r in self.rows(t):
            if r[0] == rid:
                out = r
        return out

    def tier0(self):
        if not self.rows("goals.tsv"):
            raise Reject("Tier0 硬门：无 goals 行（先 add-goal 立项）")

    def new_id(self, t, prefix):
        return next_id(self.rows(t), prefix, self.gid)

    def eff_scope(self):
        rows = self.rows("scope.tsv")
        fi = self.idx("scope.tsv", "amendment_of")
        superseded = {r[fi] for r in rows if r[fi]}
        return [r for r in rows if r[0] not in superseded]

    def approved(self, ap_id):
        r = self.latest("approvals.tsv", ap_id) if ap_id else None
        return r is not None and self.val("approvals.tsv", r, "decision") == "approved"

    def event(self, ts, ev, actor="CLI", phase="", revert=""):
        tl = self.rows("timeline.tsv")
        prev = tl[-1][self.idx("timeline.tsv", "hash")] if tl else GENESIS
        wo = [ts, actor, phase, ev, revert, prev, SCHEMA_VERSION]
        h = row_hash(prev, wo)
        row = [ts, actor, phase, ev, revert, prev, h, SCHEMA_VERSION]
        tl.append(row)
        return row

    def append(self, t, row):
        assert len(row) == len(TABLES[t]), "列数!=契约字段数: " + t
        self.rows(t).append(row)

    def commit(self, tables):
        for t in sorted(tables):
            write_tsv(os.path.join(self.s.dir, t), self.rows(t))

    def write_file(self, relpath, text):
        p = os.path.join(self.s.dir, relpath)
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:  # LF 字节纪律（Windows 不译 CRLF）
            f.write(text)


def _ok_line(obj, tname, rows):
    print("OK" + TAB + str(obj) + TAB + tname)
    for r in rows:
        print(TAB.join(esc(c) for c in r))


def _scope_common(ctx, args):
    kind = args.get("kind", "")
    if kind not in {"include", "exclude", "oob", "account-grant"}:
        raise Reject("kind 不在四值枚举 {include,exclude,oob,account-grant}: " + kind)
    matcher = args.get("matcher", "")
    if not matcher:
        raise Reject("matcher 空=REJECT")
    if not _matcher_ok(matcher):
        raise Reject("matcher 语法不合法（须 CIDR 网段/域名后缀/通配）: " + matcher)
    account = args.get("account", "")
    actions = args.get("permitted-actions", "")
    if kind == "account-grant":
        if not account or not actions:
            raise Reject("account-grant 行须 account＋permitted_actions")
    if account.startswith("CRED-") and account not in ctx.ids("creds.tsv"):
        raise Reject("account 为 CRED 引用但引用闭合失败: " + account)
    return kind, matcher, account, actions


# ---------------------------------------------------------------- 1 add-goal

def _add_goal(goal_dir, rest):
    args = _parse(rest, {"target", "objective", "auth-doc", "auth-sha256", "signer", "valid-from",
                         "valid-until", "rate-limit", "window", "emergency-contact", "budget",
                         "dollar-budget", "language", "business-context", "model-tier", "guard-tier",
                         "timestamp", "phase"})
    _req(args, ["target", "objective", "auth-doc", "auth-sha256", "signer", "valid-from",
                "valid-until", "budget", "model-tier", "guard-tier", "timestamp"])
    ctx = Ctx(goal_dir)
    if ctx.rows("goals.tsv"):
        raise Reject("goals 已有行（§4.3 每次测试一行，不允许重复立项）")
    for f in ("auth-doc", "auth-sha256", "signer", "valid-from", "valid-until"):
        if not args[f]:
            raise Reject("授权结构化字段空=REJECT（不存在「先记上再补」）: --" + f)
    if not _hex64(args["auth-sha256"]):
        raise Reject("auth_sha256 非 sha256 hex")
    seg = args["budget"].split(";")
    if len(seg) != 3 or not all(_seg_int(x) for x in seg):
        raise Reject("budget 非 token;requests;hours 三段整数: " + args["budget"])
    db = args.get("dollar-budget", "")
    if db and not _seg_num(db):
        raise Reject("dollar_budget 非浮点: " + db)
    if args["model-tier"] not in {"strong", "weak"}:
        raise Reject("model_tier 不在 {strong,weak}: " + args["model-tier"])
    if args["guard-tier"] not in {"T1", "T2", "T3"}:
        raise Reject("guard_tier 不在 {T1,T2,T3}: " + args["guard-tier"])
    if args["valid-until"] <= args["valid-from"]:
        raise Reject("valid_until<=valid_from（授权窗口非法）")
    rid = ctx.new_id("goals.tsv", "G")
    row = _row("goals.tsv", id=rid, target=_clean(args["target"]), objective=_clean(args["objective"]),
               auth_doc=args["auth-doc"], auth_sha256=args["auth-sha256"], signer=args["signer"],
               valid_from=args["valid-from"], valid_until=args["valid-until"],
               rate_limit=args.get("rate-limit", ""), window=args.get("window", ""),
               emergency_contact=args.get("emergency-contact", ""), budget=args["budget"],
               dollar_budget=db, language=args.get("language", ""),
               business_context=_clean(args.get("business-context", "")), model_tier=args["model-tier"],
               guard_tier=args["guard-tier"], created=args["timestamp"])
    ctx.append("goals.tsv", row)
    ctx.event(args["timestamp"], "add-goal " + rid, phase=args.get("phase", ""))
    ctx.commit({"goals.tsv", "timeline.tsv"})
    _ok_line(rid, "goals.tsv", [row])
    return 0


# ---------------------------------------------------------------- 2 add-scope

def _add_scope(goal_dir, rest):
    args = _parse(rest, {"kind", "matcher", "account", "permitted-actions", "note", "timestamp", "phase"})
    _req(args, ["kind", "matcher", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    kind, matcher, account, actions = _scope_common(ctx, args)
    rid = ctx.new_id("scope.tsv", "S")
    row = _row("scope.tsv", id=rid, kind=kind, matcher=matcher, account=account,
               permitted_actions=actions, amendment_of="", note=_clean(args.get("note", "")),
               created=args["timestamp"])
    ctx.append("scope.tsv", row)
    ctx.event(args["timestamp"], "add-scope " + rid, phase=args.get("phase", ""))
    ctx.commit({"scope.tsv", "timeline.tsv"})
    _ok_line(rid, "scope.tsv", [row])
    return 0


# ---------------------------------------------------------------- 3 add-intent

def _add_intent(goal_dir, rest):
    args = _parse(rest, {"title", "detail", "engine", "kind", "origin", "via", "budget-share",
                         "activation", "cred", "asset", "actions", "timestamp", "phase"})
    _req(args, ["title", "engine", "kind", "origin", "budget-share", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    kind = args["kind"]
    origin = args["origin"]
    if kind not in _INTENT_KINDS:
        raise Reject("kind 不在枚举 {recon,surface,matrix-test,deep-dive,authz-diff,nday-verify}: " + kind)
    if origin not in INTENT_ORIGINS:
        raise Reject("origin 不在枚举 {entity,concept,precedent,adjacency,llm,recon-event,mixed}: " + origin)
    seg = args["budget-share"].split(";")
    if len(seg) not in (3, 4) or not all(_seg_num(x) for x in seg):
        raise Reject("budget_share 非 token;requests;hours[;dollars] 三/四段数值: " + args["budget-share"])
    activation = args.get("activation", "")
    if activation and not _activation_ok(activation):
        raise Reject("activation 须 field;op;value 三段: " + activation)
    asset = args.get("asset", "")
    if asset:
        arow = ctx.latest("assets.tsv", asset)
        if arow is None:
            raise Reject("asset 引用闭合失败: " + asset)
        ins = ctx.val("assets.tsv", arow, "in_scope")
        if ins not in {"1", "in_scope", "true"}:
            raise Reject("界外资产禁止派生 intent（%s=%s，§4.4 账本级禁止）" % (asset, ins))
    if kind == "authz-diff":
        cred = args.get("cred", "")
        if not cred:
            raise Reject("kind=authz-diff 须 --cred 引用 CRED 行（§4.10 硬门）")
        crow = ctx.latest("creds.tsv", cred)
        if crow is None:
            raise Reject("cred 引用闭合失败: " + cred)
        if ctx.val("creds.tsv", crow, "status") != "active":
            raise Reject("authz-diff 硬门：CRED 行 status!=active: " + cred)
        allowed = set(_mv(ctx.val("creds.tsv", crow, "permitted_actions")))
        for act in _mv(args.get("actions", "")):
            if act not in allowed:
                raise Reject("authz-diff 硬门：permitted_actions 不覆盖计划动作 %s（%s）" % (act, cred))
    dedup = (asset or "-") + "+" + kind + "+" + args["title"]
    if dedup in {ctx.val("intents.tsv", r, "dedup_key") for r in ctx.rows("intents.tsv")}:
        raise Reject("dedup_key 重复（资产+技法类机械判重）: " + dedup)
    rid = ctx.new_id("intents.tsv", "INT")
    row = _row("intents.tsv", id=rid, title=_clean(args["title"]), detail=_clean(args.get("detail", "")),
               status="pending" if origin == "recon-event" else "candidate", engine=args["engine"],
               kind=kind, origin=origin, score="", via=args.get("via", ""), dedup_key=dedup,
               budget_share=args["budget-share"], activation=activation, reason="",
               created=args["timestamp"])
    ctx.append("intents.tsv", row)
    ctx.event(args["timestamp"], "add-intent " + rid, phase=args.get("phase", ""))
    ctx.commit({"intents.tsv", "timeline.tsv"})
    _ok_line(rid, "intents.tsv", [row])
    return 0


# ---------------------------------------------------------------- 4 set-intent-status

_INTENT_ARROWS = {
    "candidate": {"pending", "rejected", "deferred"},
    "pending": {"active"},
    "active": {"done", "blocked"},
    "blocked": {"active"},
    "done": set(),
    "rejected": set(),
    "deferred": set(),
}


def _set_intent_status(goal_dir, rest):
    args = _parse(rest, {"id", "status", "reason", "activation", "approval", "timestamp", "phase"})
    _req(args, ["id", "status", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    cur = ctx.latest("intents.tsv", args["id"])
    if cur is None:
        raise Reject("id 引用闭合失败: " + args["id"])
    st = args["status"]
    if st not in {"candidate", "pending", "active", "done", "blocked", "rejected", "deferred"}:
        raise Reject("status 不在状态机枚举: " + st)
    cur_st = ctx.val("intents.tsv", cur, "status")
    if st not in _INTENT_ARROWS.get(cur_st, set()):
        raise Reject("status 转移不沿状态机（%s→%s，§4.5）" % (cur_st, st))
    reason = args.get("reason", "")
    if st in {"rejected", "blocked", "deferred"} and not reason:
        raise Reject("status=%s 须附 reason（强制）" % st)
    activation = args.get("activation", "") or ctx.val("intents.tsv", cur, "activation")
    if st == "deferred" and not _activation_ok(activation):
        raise Reject("deferred 附 activation 须 field;op;value 三段: " + activation)
    if cur_st == "blocked" and st == "active":
        ap = args.get("approval", "")
        if not ap or not ctx.approved(ap):
            raise Reject("blocked 不可自动复活：须 --approval 指向 approved 行")
    row = list(cur)
    row[ctx.idx("intents.tsv", "status")] = st
    row[ctx.idx("intents.tsv", "reason")] = reason
    row[ctx.idx("intents.tsv", "activation")] = activation
    row[ctx.idx("intents.tsv", "created")] = args["timestamp"]
    ctx.append("intents.tsv", row)
    ctx.event(args["timestamp"], "set-intent-status %s:%s" % (args["id"], st), phase=args.get("phase", ""))
    ctx.commit({"intents.tsv", "timeline.tsv"})
    _ok_line(args["id"] + "(追加新行)", "intents.tsv", [row])
    return 0


# ---------------------------------------------------------------- 5 add-fact

def _add_fact(goal_dir, rest):
    args = _parse(rest, {"intent-id", "kind", "target", "detail", "confidence", "timestamp", "phase"})
    _req(args, ["intent-id", "kind", "target", "detail", "confidence", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if args["kind"] not in {"port", "service", "http", "info", "vuln-clue", "authz"}:
        raise Reject("kind 不在枚举 {port,service,http,info,vuln-clue,authz}: " + args["kind"])
    if ctx.latest("intents.tsv", args["intent-id"]) is None:
        raise Reject("intent_id 引用闭合失败: " + args["intent-id"])
    try:
        cf = float(args["confidence"])
    except ValueError:
        raise Reject("confidence 非浮点: " + args["confidence"])
    if not (0.0 <= cf <= 1.0):
        raise Reject("confidence 不在 [0,1]: " + args["confidence"])
    detail = _trunc(_clean(args["detail"]), 2000)
    why = _redact_hit(detail)
    if why:
        raise Reject("detail redact 校验检出真值模式（%s）——落盘前掩码 REJECT" % why)
    rid = ctx.new_id("facts.tsv", "F")
    row = _row("facts.tsv", id=rid, intent_id=args["intent-id"], kind=args["kind"],
               target=_trunc(_clean(args["target"]), 2000), detail=detail,
               confidence=args["confidence"], created=args["timestamp"])
    ctx.append("facts.tsv", row)
    ctx.event(args["timestamp"], "add-fact " + rid, phase=args.get("phase", ""))
    ctx.commit({"facts.tsv", "timeline.tsv"})
    _ok_line(rid, "facts.tsv", [row])
    return 0


# ---------------------------------------------------------------- 6 add-finding

def _add_finding(goal_dir, rest):
    args = _parse(rest, {"intent-id", "title", "confidence", "impact", "exploitation-status",
                         "auth-context", "scope-check", "description-brief", "reproducible-steps",
                         "affected-asset-id", "evidence-ids", "control-evidence-ids", "vuln-ref",
                         "timestamp", "phase"})
    _req(args, ["intent-id", "title", "confidence", "impact", "exploitation-status", "scope-check",
                "description-brief", "reproducible-steps", "affected-asset-id", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if ctx.latest("intents.tsv", args["intent-id"]) is None:
        raise Reject("intent_id 引用闭合失败: " + args["intent-id"])
    if ctx.latest("assets.tsv", args["affected-asset-id"]) is None:
        raise Reject("affected_asset_id 引用闭合失败: " + args["affected-asset-id"])
    if args["confidence"] not in {"C1", "C2", "C3", "\u2796\U0001f6d1"}:
        raise Reject("confidence 不在 {C1,C2,C3,\u2796\U0001f6d1}: " + args["confidence"])
    if args["impact"] not in {"\u9ad8", "\u4e2d", "\u4f4e"}:
        raise Reject("impact 不在 {高,中,低}: " + args["impact"])
    if args["exploitation-status"] not in {"verified", "suspected", "ruled_out"}:
        raise Reject("exploitation_status 不在 {verified,suspected,ruled_out}: " + args["exploitation-status"])
    if args["scope-check"] not in {"in_scope", "boundary-verified"}:
        raise Reject("scope_check 不在 {in_scope,boundary-verified}: " + args["scope-check"])
    steps = _mv(args["reproducible-steps"])
    if not steps:
        raise Reject("reproducible_steps ≥1 强制——无可复现步骤的观察一律是 fact（铁律 4），改走 add-fact")
    brief = _clean(args["description-brief"])
    if len(brief) > 200:
        raise Reject("description_brief>200 字")
    ev_ids = _mv(args.get("evidence-ids", ""))
    if not ev_ids:
        if args["confidence"] == "C2":
            raise Reject("confidence=C2 须附条件可达性证据（evidence_ids 非空，否则降 C3）")
        raise Reject("evidence_ids 空=REJECT（finding 须证据支撑，铁律 4）")
    ev_all = set(ctx.ids("E-index.tsv"))
    for e in ev_ids + _mv(args.get("control-evidence-ids", "")):
        if e not in ev_all:
            raise Reject("evidence 引用闭合失败: " + e)
    auth_ctx = args.get("auth-context", "")
    if auth_ctx and not (auth_ctx.startswith("CRED-") and auth_ctx in ctx.ids("creds.tsv")):
        raise Reject("auth_context 须空（未认证）或 CRED-{id} 闭合: " + auth_ctx)
    vref = args.get("vuln-ref", "")
    if not _vulnref_ok(vref):
        raise Reject("vuln_ref 编号须 CVE/CWE/GHSA 形态: " + vref)
    dedup = args["affected-asset-id"] + "+" + (vref if vref else args["title"])
    active_keys = set()
    for fid in {r[0] for r in ctx.rows("findings.tsv")}:
        frow = ctx.latest("findings.tsv", fid)
        if ctx.val("findings.tsv", frow, "status") in ("", "active"):
            active_keys.add(ctx.val("findings.tsv", frow, "dedup_key"))
    if dedup in active_keys:
        raise Reject("dedup_key=%s 与既有 active 行同键——走 supersede-finding 合并" % dedup)
    rid = ctx.new_id("findings.tsv", "FD")
    card = "findings-cards/%s.md" % rid
    row = _row("findings.tsv", id=rid, intent_id=args["intent-id"], title=_clean(args["title"]),
               confidence=args["confidence"], impact=args["impact"],
               exploitation_status=args["exploitation-status"], auth_context=auth_ctx, dedup_key=dedup,
               vuln_ref=vref, scope_check=args["scope-check"], description_brief=brief,
               reproducible_steps=args["reproducible-steps"], affected_asset_id=args["affected-asset-id"],
               evidence_ids=args["evidence-ids"], control_evidence_ids=args.get("control-evidence-ids", ""),
               card_path=card, status="active", created=args["timestamp"])
    ctx.append("findings.tsv", row)
    ctx.event(args["timestamp"], "add-finding " + rid, phase=args.get("phase", ""))
    ctx.commit({"findings.tsv", "timeline.tsv"})
    ctx.write_file(card, "---\nid: %s\ndedup_key: %s\nscope_check: %s\nexploitation_status: %s\n"
                         "confidence: %s\nimpact: %s\nauth_context: %s\nevidence_ids: [%s]\n"
                         "control_evidence_ids: [%s]\naffected_asset_id: %s\npair_group: \n---\n"
                         "## 漏洞叙述\n（待 LLM 撰写，只能引用账本已有数据）\n"
                         "## 复现步骤\n（引用 EV 卡片 POC 四要素，不复制原文）\n"
                         "## 修复建议叙述\n（待 LLM 撰写）\n"
                   % (rid, dedup, args["scope-check"], args["exploitation-status"], args["confidence"],
                      args["impact"], auth_ctx, ", ".join(ev_ids),
                      ", ".join(_mv(args.get("control-evidence-ids", ""))), args["affected-asset-id"]))
    _ok_line(rid, "findings.tsv", [row])
    return 0


# ---------------------------------------------------------------- 7 supersede-finding

def _supersede_finding(goal_dir, rest):
    args = _parse(rest, {"id", "superseded-by", "timestamp", "phase"})
    _req(args, ["id", "superseded-by", "timestamp"])
    ctx = Ctx(goal_dir)
    return _supersede_body(ctx, args)


def _supersede_body(ctx, args):
    ctx.tier0()
    src, dst = args["id"], args["superseded-by"]
    if src == dst:
        raise Reject("自指合并非法")
    srow = ctx.latest("findings.tsv", src)
    drow = ctx.latest("findings.tsv", dst)
    if srow is None or drow is None:
        raise Reject("id 引用闭合失败: %s/%s" % (src, dst))
    if ctx.val("findings.tsv", srow, "status") not in ("", "active"):
        raise Reject("被合并行 status!=active（已 superseded 不可再合并）")
    if ctx.val("findings.tsv", srow, "dedup_key") != ctx.val("findings.tsv", drow, "dedup_key"):
        raise Reject("两行 dedup_key 不同键——跨键合并须人工裁决，本命令不允许")
    succ = {}
    for r in ctx.rows("edges.tsv"):
        if ctx.val("edges.tsv", r, "kind") == "supersedes":
            succ.setdefault(ctx.val("edges.tsv", r, "source_id"), set()).add(
                ctx.val("edges.tsv", r, "target_id"))
    seen, stack = set(), [dst]
    while stack:
        n = stack.pop()
        if n == src:
            raise Reject("互指/成环合并非法")
        for m in succ.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    for r in ctx.rows("edges.tsv"):
        if (ctx.val("edges.tsv", r, "kind"), ctx.val("edges.tsv", r, "source_id"),
                ctx.val("edges.tsv", r, "target_id")) == ("supersedes", src, dst):
            raise Reject("supersedes 边已存在（幂等拒收）")
    erow = _row("edges.tsv", id=ctx.new_id("edges.tsv", "E"), kind="supersedes", source_id=src,
                target_id=dst, provenance="supersede-finding", created=args["timestamp"])
    trow = list(srow)
    trow[ctx.idx("findings.tsv", "status")] = "superseded"
    trow[ctx.idx("findings.tsv", "created")] = args["timestamp"]
    ctx.append("edges.tsv", erow)
    ctx.append("findings.tsv", trow)
    ctx.event(args["timestamp"], "supersede-finding %s->%s" % (src, dst), phase=args.get("phase", ""))
    ctx.commit({"edges.tsv", "findings.tsv", "timeline.tsv"})
    _ok_line(erow[0] + "(supersedes 边)", "edges.tsv", [erow, trow])
    return 0


# ---------------------------------------------------------------- 8 add-asset

def _add_asset(goal_dir, rest):
    args = _parse(rest, {"type", "value", "meta", "timestamp", "phase"})
    _req(args, ["type", "value", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    atype = args["type"]
    if atype in {"pivot", "foothold"}:
        raise Reject("type=%s 批次 4 前启用=REJECT（§4.8）" % atype)
    if atype not in {"root-domain", "subdomain", "ip", "service", "app", "endpoint", "source-code"}:
        raise Reject("type 不在九值枚举: " + atype)
    value = _clean(args["value"])
    if not value:
        raise Reject("value 空=REJECT")
    for r in ctx.rows("assets.tsv"):
        if ctx.val("assets.tsv", r, "type") == atype and ctx.val("assets.tsv", r, "value") == value:
            raise Reject("同 type+value 资产重复已存在（判重）: %s/%s" % (atype, value))
    hit = False
    for r in ctx.eff_scope():
        kind = ctx.val("scope.tsv", r, "kind")
        if kind not in {"include", "exclude"}:
            continue
        if _match_value(value, ctx.val("scope.tsv", r, "matcher")):
            if kind == "exclude":
                hit = False
                break
            hit = True
    rid = ctx.new_id("assets.tsv", "AST")
    row = _row("assets.tsv", id=rid, type=atype, value=value, meta=_clean(args.get("meta", "")),
               in_scope="in_scope" if hit else "out_of_scope", created=args["timestamp"])
    ctx.append("assets.tsv", row)
    ctx.event(args["timestamp"], "add-asset %s(%s)" % (rid, row[ctx.idx("assets.tsv", "in_scope")]),
              phase=args.get("phase", ""))
    ctx.commit({"assets.tsv", "timeline.tsv"})
    _ok_line(rid, "assets.tsv", [row])
    return 0


# ---------------------------------------------------------------- 9 add-edge

def _add_edge(goal_dir, rest):
    args = _parse(rest, {"kind", "source-id", "target-id", "provenance", "timestamp", "phase"})
    _req(args, ["kind", "source-id", "target-id", "provenance", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    kind = args["kind"]
    if kind not in EDGE_KINDS:
        raise Reject("kind 不在 10 边枚举（新增边类型须 bump schema_version）: " + kind)
    src, dst = args["source-id"], args["target-id"]
    if kind == "cross_ref":
        allids = ctx.all_ids()
        if src not in allids:
            raise Reject("source_id 引用闭合失败: " + src)
        if dst not in allids:
            raise Reject("target_id 引用闭合失败: " + dst)
    else:
        stabs, ttabs = _EDGE_DIR[kind]
        s_hit = [t for t in stabs if src in ctx.ids(t)]
        t_hit = [t for t in ttabs if dst in ctx.ids(t)]
        if not s_hit:
            raise Reject("source_id 引用闭合失败或方向不符（%s 方向）: %s" % (kind, src))
        if not t_hit:
            raise Reject("target_id 引用闭合失败或方向不符（%s 方向）: %s" % (kind, dst))
    for r in ctx.rows("edges.tsv"):
        if (ctx.val("edges.tsv", r, "kind"), ctx.val("edges.tsv", r, "source_id"),
                ctx.val("edges.tsv", r, "target_id")) == (kind, src, dst):
            raise Reject("同 kind+source+target 边重复（幂等判重）")
    rid = ctx.new_id("edges.tsv", "E")
    row = _row("edges.tsv", id=rid, kind=kind, source_id=src, target_id=dst,
               provenance=_clean(args["provenance"]), created=args["timestamp"])
    ctx.append("edges.tsv", row)
    ctx.event(args["timestamp"], "add-edge %s(%s)" % (rid, kind), phase=args.get("phase", ""))
    ctx.commit({"edges.tsv", "timeline.tsv"})
    _ok_line(rid, "edges.tsv", [row])
    return 0


# ---------------------------------------------------------------- 10 add-evidence

_NORM_DROP = re.compile(r"(?i)(nonce|timestamp|x-request-id|^date:)")
_ISO_TS = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")


def _hashes(ctx, artifact):
    p = os.path.join(ctx.s.dir, artifact) if artifact else None
    data = b""
    if p and os.path.isfile(p):
        with open(p, "rb") as f:
            data = f.read()
    raw = hashlib.sha256(data).hexdigest()
    try:
        text = data.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        norm = raw
    else:
        keep = []
        for ln in text.splitlines():
            if _NORM_DROP.search(ln):
                continue
            keep.append(_ISO_TS.sub("<TS>", ln))
        norm = hashlib.sha256(("\n".join(keep)).encode("utf-8")).hexdigest()
    return raw, norm


def _add_evidence(goal_dir, rest):
    args = _parse(rest, {"title", "source-type", "observed-at", "network-position", "repro-command",
                         "repro-kind", "artifact", "raw-excerpt", "linked-finding", "pair-group",
                         "timestamp", "phase"})
    _req(args, ["title", "source-type", "observed-at", "network-position", "repro-command",
                "repro-kind", "artifact", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if args["source-type"] not in {"command", "capture", "file", "log", "manual"}:
        raise Reject("source_type 不在 {command,capture,file,log,manual}: " + args["source-type"])
    if args["repro-kind"] not in {"single", "sequence", "concurrent"}:
        raise Reject("repro_kind 不在 {single,sequence,concurrent}: " + args["repro-kind"])
    np = args["network-position"]
    if np not in {"internet", "intranet", "same-host"} and not np.startswith("jumphost:"):
        raise Reject("network_position 不在 {internet,intranet,same-host,jumphost:<name>}: " + np)
    for f in ("repro-command", "raw-excerpt"):
        why = _redact_hit(args.get(f, ""))
        if why:
            raise Reject("%s redact 校验检出真值模式（%s）——凭据一律 {{vault:cred-N}} 占位符" % (f, why))
    artifact = args["artifact"]
    if artifact in {ctx.val("E-index.tsv", r, "artifact_path") for r in ctx.rows("E-index.tsv")}:
        raise Reject("artifact_path 只增不覆盖——同路径已存在（重跑另存 -r2）: " + artifact)
    lf = args.get("linked-finding", "")
    if lf and ctx.latest("findings.tsv", lf) is None:
        raise Reject("linked_finding 引用闭合失败: " + lf)
    excerpt = _trunc(_clean(args.get("raw-excerpt", "")), 200)
    raw_h, norm_h = _hashes(ctx, artifact)
    rid = ctx.new_id("E-index.tsv", "EV")
    card = "evidence/%s.md" % rid
    row = _row("E-index.tsv", id=rid, title=_clean(args["title"]), source_type=args["source-type"],
               observed_at=args["observed-at"], network_position=np,
               repro_command=_clean(args["repro-command"]), repro_kind=args["repro-kind"],
               content_hash_raw=raw_h, content_hash_norm=norm_h, artifact_path=artifact,
               card_path=card, linked_finding=lf, pair_group=args.get("pair-group", ""),
               raw_excerpt=excerpt, created=args["timestamp"])
    ctx.append("E-index.tsv", row)
    ctx.event(args["timestamp"], "add-evidence " + rid, phase=args.get("phase", ""))
    ctx.commit({"E-index.tsv", "timeline.tsv"})
    ctx.write_file(card, "---\nid: %s\ntitle: %s\nsource_type: %s\nobserved_at: %s\n"
                         "network_position: %s\npreconditions: []\nraw_request: ''\nexpected: {}\n"
                         "cleanup: ''\npair_group: %s\nrole: \n---\n"
                         "## 原始响应摘录（脱敏+定长）与判定依据\n%s\n"
                   % (rid, _clean(args["title"]), args["source-type"], args["observed-at"], np,
                      args.get("pair-group", ""), excerpt))
    _ok_line(rid, "E-index.tsv", [row])
    return 0


# ---------------------------------------------------------------- 11 approve

def _approve(goal_dir, rest):
    args = _parse(rest, {"command-hash", "decision", "approver", "note", "verify-signoff",
                         "knowledge", "timestamp", "phase"})
    ctx = Ctx(goal_dir)
    if "verify-signoff" in args:
        rows = [r for r in ctx.rows("approvals.tsv")
                if ctx.val("approvals.tsv", r, "decision") == "approved"]
        if args.get("command-hash"):
            rows = [r for r in rows if ctx.val("approvals.tsv", r, "command_hash") == args["command-hash"]]
        if rows:
            print("PASS 签发 approved 行存在（%d 行）" % len(rows))
            return 0
        print("FAIL 无签发行")
        return 1
    if "knowledge" in args:
        rows = [r for r in ctx.rows("approvals.tsv")
                if ctx.val("approvals.tsv", r, "decision") == "knowledge-approved"]
        if rows:
            print("PASS 知识审批行存在（%d 行）" % len(rows))
            return 0
        print("FAIL 知识审批 approved 行缺失")
        return 1
    _req(args, ["command-hash", "decision", "approver", "timestamp"])
    ctx.tier0()
    if not _hex64(args["command-hash"]):
        raise Reject("command_hash 非 hex")
    if args["decision"] not in _APPROVE_DECISIONS:
        raise Reject("decision 不在建议值域 {approved,rejected,exempted,knowledge-approved}: " + args["decision"])
    rid = ctx.new_id("approvals.tsv", "AP")
    row = _row("approvals.tsv", id=rid, command_hash=args["command-hash"], decision=args["decision"],
               approver=args["approver"], timestamp=args["timestamp"], note=_clean(args.get("note", "")))
    ctx.append("approvals.tsv", row)
    ctx.event(args["timestamp"], "approve %s(%s)" % (rid, args["decision"]), phase=args.get("phase", ""))
    ctx.commit({"approvals.tsv", "timeline.tsv"})
    _ok_line(rid, "approvals.tsv", [row])
    return 0


# ---------------------------------------------------------------- 12 matrix-set

def _matrix_prefix(reason):
    for p in ("submatrix:", "authz-diff:"):
        if (reason or "").startswith(p):
            return p
    return ""


def _matrix_set(goal_dir, rest):
    args = _parse(rest, {"attack-surface", "vuln-class", "state", "reason", "intent-id", "timestamp", "phase"})
    _req(args, ["attack-surface", "vuln-class", "state", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    rows = ctx.rows("matrix.tsv")
    if not rows:
        raise Reject("matrix.tsv 未初始化（先 matrix-init）")
    key_rows = [r for r in rows if r[0] == args["attack-surface"] and r[1] == args["vuln-class"]]
    if not key_rows:
        raise Reject("行键不存在于 matrix.tsv（不允许置格行外新键）: %s×%s"
                     % (args["attack-surface"], args["vuln-class"]))
    state = args["state"]
    if state not in {"x", "?", "-", "!"}:
        raise Reject("state 不在 {x,?,-,!}（空态=未检查由 init 生成）: " + state)
    reason = args.get("reason", "")
    if state in {"-", "!"} and not reason:
        raise Reject("state=%s 须附 reason" % state)
    prev_prefix = _matrix_prefix(ctx.val("matrix.tsv", key_rows[-1], "reason"))
    if _matrix_prefix(reason) != prev_prefix:
        raise Reject("reason 前缀与行类别不符（现行类别前缀=%r）: %s" % (prev_prefix or "无", reason))
    iid = args.get("intent-id", "")
    if iid and ctx.latest("intents.tsv", iid) is None:
        raise Reject("intent_id 引用闭合失败: " + iid)
    row = _row("matrix.tsv", attack_surface=args["attack-surface"], vuln_class=args["vuln-class"],
               state=state, reason=reason, intent_id=iid, updated=args["timestamp"], frozen_at="")
    ctx.append("matrix.tsv", row)
    ctx.event(args["timestamp"], "matrix-set %s×%s=%s" % (args["attack-surface"], args["vuln-class"], state),
              phase=args.get("phase", ""))
    ctx.commit({"matrix.tsv", "timeline.tsv"})
    _ok_line("置格 %s×%s=%s" % (args["attack-surface"], args["vuln-class"], state), "matrix.tsv", [row])
    return 0


# ---------------------------------------------------------------- 13 checkpoint

def _checkpoint(goal_dir, rest):
    # --release 为旗标（02a 终审补全 5 授权追加）：本地归一为 --release=1，不动全局 _parse
    rest = [("--release=1" if tok == "--release" else tok) for tok in rest]
    args = _parse(rest, {"phase", "event", "timestamp", "session", "release",
                         "round", "note", "spawn"})
    _req(args, ["timestamp", "session"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    phase = args.get("phase", "")
    if phase and phase not in GATES:
        raise Reject("phase 不在九门枚举 {P0,P1,P2,P3,P4,P5,P5.5,P6.0,P6}: " + phase)
    release = bool(args.get("release"))
    spawn = args.get("spawn", "fresh")
    if spawn not in ("fresh", "auto", "manual"):
        raise Reject("spawn 不在 {fresh,auto,manual}: " + spawn)
    handoff = [ln for ln in (args.get("note") or "").split("\n") if ln != ""]
    if state_md.would_overflow(handoff):   # 预检前置：拒收=timeline 也零变更
        raise Reject("state.md 将超行数硬顶 200——压缩 handoff")
    sp = os.path.join(ctx.s.dir, "state.md")
    fields, _, perrs = state_md.parse_state(sp)
    if perrs:
        raise Reject("state.md 损坏（先 tanyin-phases rebuild-state 对账重建）: " + perrs[0])
    if fields and fields["session_status"] == "active" \
            and fields["session"] != args["session"]:
        raise Reject("单活跃会话：session=%s 持锁未释放（接管走 tanyin-phases restart --spawn manual）"
                     % fields["session"])
    # revision ≡ 落账后 timeline 行数（state-rebuild 对账基准=timeline 行数，既有口径不变）；
    # timeline 先行（第一事实源）：kill -9 撕裂态=timeline 领先 state → state-rebuild FAIL →
    # rebuild-state 以 timeline 为准重建（设计 §4.1 快照损坏=对账重建）
    rev = len(ctx.rows("timeline.tsv")) + 1
    ev = "checkpoint revision=%d%s" % (rev, " release" if release else "")
    if args.get("event"):
        ev += " " + args["event"]
    ctx.event(args["timestamp"], ev, actor="总控", phase=phase)
    ctx.commit({"timeline.tsv"})
    new_fields = {
        "revision": str(rev),
        "goal": ctx.rows("goals.tsv")[0][0] if ctx.rows("goals.tsv") else "",
        "phase": phase,
        "round": args.get("round", "0"),
        "session": args["session"],
        "session_status": "released" if release else "active",
        "spawn": spawn,
        "updated": args["timestamp"],
        "resume_kit": "resume-kit.md",
        "snapshot": state_md.snapshot_from_session(ctx.s),
    }
    state_md.write_state(sp, new_fields, handoff)
    print("OK" + TAB + "revision=%d" % rev)
    return 0


# ---------------------------------------------------------------- 14 append-timeline

def _append_timeline(goal_dir, rest):
    args = _parse(rest, {"actor", "phase", "event", "revert-cmd", "approval", "timestamp"})
    _req(args, ["actor", "phase", "event", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if args["actor"] not in {"总控", "子代理", "CLI", "人工"}:
        raise Reject("actor 不在 {总控,子代理,CLI,人工}: " + args["actor"])
    ev = args["event"]
    revert = args.get("revert-cmd", "")
    if ev.startswith("request:") and not revert:
        raise Reject("外部副作用类 event（request:）须 --revert-cmd（分层登记）")
    if revert == "irreversible" and not ctx.approved(args.get("approval", "")):
        raise Reject("revert_cmd=irreversible 须 --approval 指向 approved 行（L3 逐条审批）")
    row = ctx.event(args["timestamp"], ev, actor=args["actor"], phase=args["phase"], revert=revert)
    ctx.commit({"timeline.tsv"})
    print("OK" + TAB + "hash=" + row[ctx.idx("timeline.tsv", "hash")][:8])
    print(TAB.join(esc(c) for c in row))
    return 0


# ---------------------------------------------------------------- 15 matrix-freeze

def _matrix_freeze(goal_dir, rest):
    args = _parse(rest, {"timestamp", "phase"})
    _req(args, ["timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    rows = ctx.rows("matrix.tsv")
    if not rows:
        raise Reject("matrix.tsv 未初始化（matrix-init 产物缺失）")
    fi = ctx.idx("matrix.tsv", "frozen_at")
    if any(r[fi] for r in rows):
        raise Reject("不可重复冻结（already-frozen，锚点已冻结）")
    for r in rows:
        r[fi] = args["timestamp"]
    ctx.event(args["timestamp"], "matrix-freeze rows=%d" % len(rows), phase=args.get("phase", ""))
    ctx.commit({"matrix.tsv", "timeline.tsv"})
    print("OK" + TAB + "frozen rows=%d" % len(rows))
    return 0


# ---------------------------------------------------------------- 16 budget-log

def _budget_log(goal_dir, rest):
    args = _parse(rest, {"token-delta", "requests-delta", "hours-delta", "dollars-delta",
                         "scope", "note", "timestamp", "phase"})
    _req(args, ["token-delta", "requests-delta", "hours-delta", "scope", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if not re.match(r"^-?\d+$", args["token-delta"]) or not re.match(r"^-?\d+$", args["requests-delta"]):
        raise Reject("token/requests 增量须整数")
    if not _seg_num(args["hours-delta"]):
        raise Reject("hours 增量须数值: " + args["hours-delta"])
    dollars = args.get("dollars-delta", "") or "0"
    if not _seg_num(dollars):
        raise Reject("dollars 增量须数值: " + dollars)
    scope = args["scope"]
    if scope != "goal":
        if not scope.startswith("INT-") or ctx.latest("intents.tsv", scope) is None:
            raise Reject("scope 须 goal 或 INT-{id} 引用闭合: " + scope)
    grow = ctx.rows("goals.tsv")[-1]
    db = ctx.val("goals.tsv", grow, "dollar_budget")
    if db in ("", "0") and float(dollars) != 0.0:
        raise Reject("goals.dollar_budget 空（第四维关）而 dollars_delta≠0——不累计（ADR-P4⑥）")
    row = _row("budget.tsv", timestamp=args["timestamp"], token_delta=args["token-delta"],
               requests_delta=args["requests-delta"], hours_delta=args["hours-delta"],
               dollars_delta=dollars, scope=scope, note=_clean(args.get("note", "")))
    ctx.append("budget.tsv", row)
    ctx.event(args["timestamp"], "budget-log " + scope, phase=args.get("phase", ""))
    ctx.commit({"budget.tsv", "timeline.tsv"})
    _ok_line("budget", "budget.tsv", [row])
    return 0


# ---------------------------------------------------------------- 17 add-cred

_BASE_ROLES = {"admin", "operator", "user", "anonymous"}


def _add_cred(goal_dir, rest):
    args = _parse(rest, {"kind", "role", "username-ref", "secret-ref", "scope-asset",
                         "obtained-via-intent", "parent-cred", "valid-from", "valid-until",
                         "permitted-actions", "note", "material", "timestamp", "phase"})
    _req(args, ["kind", "role", "username-ref", "secret-ref", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    kind = args["kind"]
    if kind not in {"static-cred", "session"}:
        raise Reject("kind 二分 {static-cred,session}（材质入 kind=REJECT，材质走 --material）: " + kind)
    material = args.get("material", "")
    if material not in ("", "ntlm-hash", "ssh-key", "x509"):
        raise Reject("material 不在 {ntlm-hash,ssh-key,x509,空}: " + material)
    if not args["role"]:
        raise Reject("role 空=REJECT")
    ordinal = len({r[0] for r in ctx.rows("creds.tsv")}) + 1
    secret = args["secret-ref"]
    m = re.match(r"^\{\{vault:cred-(\d+)\}\}$", secret)
    if not m:
        raise Reject("secret_ref 必须 {{vault:cred-N}} 占位符形态（真值永不进账本）: " + secret)
    if int(m.group(1)) != ordinal:
        raise Reject("secret_ref 占位符 N 须=creds 行序号（期望 %d）: %s" % (ordinal, secret))
    parent = args.get("parent-cred", "")
    if kind == "session" and not parent:
        raise Reject("kind=session 须 parent_cred（父凭据）")
    if parent and ctx.latest("creds.tsv", parent) is None:
        raise Reject("parent_cred 引用闭合失败: " + parent)
    ovi = args.get("obtained-via-intent", "")
    if ovi and ctx.latest("intents.tsv", ovi) is None:
        raise Reject("obtained_via_intent 引用闭合失败: " + ovi)
    vf, vu = args.get("valid-from", ""), args.get("valid-until", "")
    if vf and vu and vu <= vf:
        raise Reject("valid_until<=valid_from")
    acts = _mv(args.get("permitted-actions", ""))
    if acts:
        grants = [r for r in ctx.eff_scope() if ctx.val("scope.tsv", r, "kind") == "account-grant"]
        if not grants:
            raise Reject("permitted_actions 未被对应 account-grant 行覆盖（scope 无 account-grant 行）")
        covered = set()
        for r in grants:
            covered |= set(_mv(ctx.val("scope.tsv", r, "permitted_actions")))
        for a in acts:
            if a not in covered:
                raise Reject("permitted_actions 未被对应 account-grant 行覆盖: " + a)
    rid = ctx.new_id("creds.tsv", "CRED")
    row = _row("creds.tsv", id=rid, kind=kind, role=args["role"], username_ref=args["username-ref"],
               secret_ref=secret, scope_asset=args.get("scope-asset", ""), obtained_via_intent=ovi,
               parent_cred=parent, valid_from=vf, valid_until=vu, status="active",
               permitted_actions=args.get("permitted-actions", ""), note=_clean(args.get("note", "")),
               created=args["timestamp"], material=material)
    ctx.append("creds.tsv", row)
    ctx.event(args["timestamp"], "add-cred " + rid, phase=args.get("phase", ""))
    ctx.commit({"creds.tsv", "timeline.tsv"})
    _ok_line(rid, "creds.tsv", [row])
    return 0


# ---------------------------------------------------------------- 18 amend-scope

def _p0_over(ctx):
    """P0 后判定【推导起草】：timeline 出现 P1-P6 阶段事件即视为 P0 已过。"""
    for r in ctx.rows("timeline.tsv"):
        if re.match(r"^P[1-6]", ctx.val("timeline.tsv", r, "phase") or ""):
            return True
    return False


def _amend_scope(goal_dir, rest):
    args = _parse(rest, {"amendment-of", "kind", "matcher", "account", "permitted-actions",
                         "note", "approval", "timestamp", "phase"})
    _req(args, ["amendment-of", "kind", "matcher", "note", "timestamp"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    if ctx.latest("scope.tsv", args["amendment-of"]) is None:
        raise Reject("amendment_of 引用闭合失败: " + args["amendment-of"])
    kind, matcher, account, actions = _scope_common(ctx, args)
    if not _clean(args["note"]):
        raise Reject("note 空=REJECT（修订理由+批准人）")
    if _p0_over(ctx):
        ap = args.get("approval", "")
        if not ap or not ctx.approved(ap):
            raise Reject("P0 后修订未经审批=账本级 REJECT——须 --approval 指向 approved 行")
    rid = ctx.new_id("scope.tsv", "S")
    row = _row("scope.tsv", id=rid, kind=kind, matcher=matcher, account=account,
               permitted_actions=actions, amendment_of=args["amendment-of"],
               note=_clean(args["note"]), created=args["timestamp"])
    ctx.append("scope.tsv", row)
    ctx.event(args["timestamp"], "amend-scope %s->%s" % (rid, args["amendment-of"]),
              phase=args.get("phase", ""))
    ctx.commit({"scope.tsv", "timeline.tsv"})
    _ok_line(rid + "(修订行)", "amendment_of=" + args["amendment-of"], [row])
    return 0


# ---------------------------------------------------------------- 19 set-cred-status

def _set_cred_status(goal_dir, rest):
    args = _parse(rest, {"id", "status", "note", "approval", "timestamp", "phase"})
    _req(args, ["id", "timestamp"])
    ctx = Ctx(goal_dir)
    cur = ctx.latest("creds.tsv", args["id"])
    if cur is None:
        if "status" not in args:
            print("#count=0")
            return 0
        raise Reject("id 引用闭合失败: " + args["id"])
    cur_st = ctx.val("creds.tsv", cur, "status")
    if "status" not in args:
        print(args["id"] + TAB + cur_st)
        return 0
    ctx.tier0()
    st = args["status"]
    if st not in _CRED_STATUS:
        raise Reject("status 不在 {active,expired,invalidated,revoked}: " + st)
    if st == "active" and cur_st in {"revoked", "invalidated"}:
        ap = args.get("approval", "")
        if not ap or not ctx.approved(ap):
            raise Reject("revoked/invalidated 复活须 --approval 指向 approved 行（人工复活）")
    row = list(cur)
    row[ctx.idx("creds.tsv", "status")] = st
    row[ctx.idx("creds.tsv", "note")] = _clean(args.get("note", ""))
    row[ctx.idx("creds.tsv", "created")] = args["timestamp"]
    ctx.append("creds.tsv", row)
    ctx.event(args["timestamp"], "set-cred-status %s:%s" % (args["id"], st), phase=args.get("phase", ""))
    ctx.commit({"creds.tsv", "timeline.tsv"})
    _ok_line(args["id"] + "(追加新行)", "creds.tsv", [row])
    return 0


# ---------------------------------------------------------------- 注册

_IMPL = {
    "add-goal": _add_goal,
    "add-scope": _add_scope,
    "add-intent": _add_intent,
    "set-intent-status": _set_intent_status,
    "add-fact": _add_fact,
    "add-finding": _add_finding,
    "supersede-finding": _supersede_finding,
    "add-asset": _add_asset,
    "add-edge": _add_edge,
    "add-evidence": _add_evidence,
    "approve": _approve,
    "matrix-set": _matrix_set,
    "checkpoint": _checkpoint,
    "append-timeline": _append_timeline,
    "matrix-freeze": _matrix_freeze,
    "budget-log": _budget_log,
    "add-cred": _add_cred,
    "amend-scope": _amend_scope,
    "set-cred-status": _set_cred_status,
}


def _wrap(name, fn):
    def h(goal_dir, rest):
        try:
            return fn(goal_dir, rest)
        except Reject as e:
            sys.stderr.write("REJECT" + TAB + name + TAB + str(e) + chr(10))
            return 1
        except Usage as e:
            sys.stderr.write("用法错误 " + name + ": " + str(e) + chr(10))
            return 2
    return h


HANDLERS = {n: _wrap(n, f) for n, f in _IMPL.items()}
for _n, _f in _IMPL.items():
    HANDLERS["ledger-" + _n] = _wrap("ledger-" + _n, _f)


# ---------------------------------------------------------------- 探知注记（实现侧起草点，随报告上报）
# 1. --timestamp 必填：02a 载 created/updated/timestamp 为「命令铸造」，批次 1 统一改为必填参数取值（确定性）。
# 2. 通用可选 --phase：写命令自动 timeline 事件的 phase 列契约未载→默认空，可选传入。
# 3. add-intent：--asset/--actions 为起草参数（§9.2 负向用例与 §4.10 硬门的可判载体，02a 签名未载）；
#    intents.score 公式（§8.7）未载→统一留空=未评估（与 03 终审「不打分留空」一致）。
# 4. redact 检出/匹配器语法/定长截断(200)/vuln_ref 编号形态/budget 整数段允许 K/M/G 后缀
#    （01 示例 2M;50000;40 vs 02a「三段整数」）均为高精确度起草规则。
# 5. assets.in_scope 落 in_scope/out_of_scope 字面量（夹具旧样本 1/0 兼容读）。
# 6. checkpoint（批次 3 T4 升级）：state.md v2 行结构已冻结（10 固定键+handoff 段，cli/ledger/state_md.py
#    单一实现）；新参数 --session/--release/--round/--note/--spawn 为 02a 终审补全 5 授权追加（沿
#    批次 1 探知注记 1 --timestamp 同型先例；契约 02a §13 回注=探知项 G-10，T13 收口统一回注）。
#    revision ≡ 落账后 timeline 行数（state-rebuild 对账基准，撕裂态=timeline 领先 state）。
# 7. append-timeline：request-ticket 前置机制未载→未实现；irreversible 的 approvals 绑定
#    经 --approval 参数化（同 set-intent-status/amend-scope 范式）。
# 8. matrix-set：VOCAB 校验由「行键须已存在」承载（shared/VOCAB.md 未在仓库）；新置格行
#    frozen_at=空（锚点行=冻结时在场的行，由 matrix-freeze 盖戳）。
# 9. amend-scope「P0 后」判定=timeline 出现 P1-P6 事件（阶段推进的可机械判据）。
# 10. add-cred：role 合法集合无法从既有账本机械闭合（八问⑧不落表）→仅强制非空；
#     permitted_actions 覆盖=对照全部生效 account-grant 行并集。
# 11. add-finding C2 条件可达性证据=以 evidence_ids 非空近似（证据行无条件性标记列）。
# 12. set-intent-status 状态机仅允许 02a 载明箭头+blocked 复活；deferred 复活转移未载→不允许。
# 13. EV/FD 卡片为骨架生成（front-matter 同值标量+契约正文段标题）；嵌套段留 LLM/引擎填充。
