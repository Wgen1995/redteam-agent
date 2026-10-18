# -*- coding: utf-8 -*-
"""api_v2_command——功能17补件·对话指挥闭环（command-converse-v1）。

舰间契约：本文件=本舰独写；挂载=GET ROUTES/POST POST_ROUTES 单源表由
include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_command_converse.py（_V2MountHandler）：POST 过会话门+CSRF 双检，
GET 过会话门。设计权威 docs/design/2026-10-20-command-approval-design.md。

三面（确定性词表推导——审批中心 AI 预审同先例，不上模型不编事实）：
  ①对话建任务  POST /api/v2/battle/propose——聊天框「打 xxx」→ 解析目标+
    弹任务卡（目标/范围预览/红线/预算帽/字典版 form=battle/new 表单直映射）。
    **只产卡不建仗**：本路由零写（goal 目录逐字节不变）；确认走既有
    POST /api/battle/new（授权八问仍归 new-task 表单，本模块不代办）。
  ②@引用  GET /api/v2/at-search——fuzzy 搜账本四表（目标/漏洞/事实/任务），
    命中=api_v2_ask 同形锚（选中即钉上下文，可直接喂 /api/v2/ask）；
    POST /api/v2/at-dispatch——「@X 再测一次」经 registry.lookup("add-intent")
    既有通道生成任务卡进活池（origin=recon-event 直达 pending；dedup 机械
    判重=幂等——planner_loop 同先例，写全经 registry 不碰 write_cmds）。
  ③回复四分类  POST /api/v2/steer-reply——解析回复 → 批准/拒绝/改方向/给情报：
    批准/拒绝→路由既有 /api/approval HMAC 面（action 包带 row+decision+签，
    本模块零写 approvals——guard 页三钮同律）；改方向→steer 管道
    （cli/warrior/steer.py 既有写者 warrior-steer 行）；给情报→注入士兵简报
    （steer 扫描每轮并入模型上下文=简报面，loop.process_intent 同源）；
    未识别→保守落「给情报」（原文必达士兵，绝不自动批准）。

词表律（62律）：本模块一切屏上文本过 scripts/vocab_lint.BANNED 单源
（KIND_WORDS/SCREEN_TEXTS 供 tests.test_command_converse.TestVocabLaw 钉）。
纯 stdlib、3.9 兼容；propose 零钟零写（确定性投影）。
"""
import datetime
import os
import re

from ledger import core, registry
from warrior import steer
from . import api_v2_ask

ROUTE_PROPOSE = "/api/v2/battle/propose"
ROUTE_AT_SEARCH = "/api/v2/at-search"
ROUTE_AT_DISPATCH = "/api/v2/at-dispatch"
ROUTE_STEER_REPLY = "/api/v2/steer-reply"
ROUTES = {ROUTE_AT_SEARCH: None}                       # GET 面（尾部赋真身）
POST_ROUTES = {ROUTE_PROPOSE: None, ROUTE_AT_DISPATCH: None,
               ROUTE_STEER_REPLY: None}

# 表→人话类词（62律单源：asset=目标 finding=漏洞 fact=事实 intent=任务）
KIND_WORDS = {"assets.tsv": "目标", "findings.tsv": "漏洞",
              "facts.tsv": "事实", "intents.tsv": "任务"}
# 各表标题列（@搜索与派活卡标题用）
_TITLE_COL = {"assets.tsv": "value", "findings.tsv": "title",
              "facts.tsv": "detail", "intents.tsv": "title"}
SEARCH_CAP = 20
CARD_VERSION = "propose-v1"
CONFIRM_ROUTE = "/api/battle/new"
ENV_BUDGET = "TANYIN_BATTLE_BUDGET_CAP_USD"

# 目标形：域名 / IPv4 / CIDR 网段（new.html 范围白名单同形）
_DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$", re.I)
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_CIDR_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}$")
_LEAD_VERB_RE = re.compile(r"^(?:打|攻击|测|测试|干|搞|扫)\s*")
_SEP_RE = re.compile(r"[，,；;：:、\s]+")

# 红线（任务卡固定列——范围必须人确认律的平台面）
RED_LINES = (
    "范围外的目标一律不碰——开仗前须人工确认范围预览",
    "不可逆或高危操作一律逐条审批，不走预授权",
    "平台保留端口（8900/3000/8787/8443）不碰（battle_registry 同表）",
    "测试节奏遵守授权文件窗口与预算帽",
)

# 四分类词表（确定性；顺序=判定优先级：拒绝>批准>改方向>情报）
_REJECT_WORDS = ("拒绝", "驳回", "不行", "不准", "别执行", "不要执行", "reject")
_APPROVE_WORDS = ("批准", "同意", "准了", "准许", "放行", "可以执行", "approve")
_REDIRECT_WORDS = ("改打", "改方向", "转向", "改成", "换成", "先测", "先打",
                   "别管", "优先", "改测", "转去", "去测")
_INTEL_WORDS = ("情报", "线索", "钥匙", "账号", "密码", "入口", "提示",
                "token", "试试", "告诉")

# 屏上文本全集（tests.TestVocabLaw 逐条过 vocab_lint.BANNED）
SCREEN_TEXTS = (
    "没认出要打的目标——请带上域名或网段（如：打 xxx.com）",
    "缺任务内容——请先输入要说的任务（如：打 xxx.com，找尽可能多漏洞）",
    "任务卡只起草不开仗——确认后走既有开仗表单（授权件仍须人工上传）",
    "缺搜索内容——@ 后跟关键词（如 @管理面板）",
    "没有命中的对象——换个关键词试试",
    "暂只支持「再测一次」这类复测指令——其余请走对话问询",
    "批准/拒绝须指定待审行（context.row）——先在审批中心选中那一条",
    "走既有审批通道（持钥签名）——页面代发 /api/approval",
    "已注入士兵转向指令——下一轮即带令续跑",
    "情报已注入士兵简报——士兵下一轮即带上",
) + RED_LINES + tuple(KIND_WORDS.values())

_UTC_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utc_now():
    return datetime.datetime.utcnow().strftime(_UTC_FMT)


def _goal_dir(base, goal):
    return api_v2_ask._goal_dir(base, goal)          # ask 同源（读复用）


# ---------------------------------------------------------------- ① 对话建任务 --

def _parse_target(text):
    """「打 xxx.com,找尽可能多漏洞」→ (target, objective) | (None, text)。"""
    body = _LEAD_VERB_RE.sub("", text.strip())
    parts = [p for p in _SEP_RE.split(body) if p]
    for i, tok in enumerate(parts):
        cand = tok.strip("。，,；;：:()（）")
        if (_DOMAIN_RE.match(cand) or _IPV4_RE.match(cand)
                or _CIDR_RE.match(cand)):
            rest = "，".join(x for x in parts[i + 1:] if x)
            return cand, rest
    return None, text


def _scope_preview(target):
    """目标 → 范围预览行（域名=本域+同根泛域；IP/网段=自身——new.html 同形）。"""
    if _CIDR_RE.match(target) or _IPV4_RE.match(target):
        return [target]
    labels = target.split(".")
    root = ".".join(labels[-2:]) if len(labels) >= 3 else target
    return [target, "*." + root]


def propose(body, ledger_dir):
    """POST /api/v2/battle/propose {text} → 任务卡（只产卡不建仗，零写）。"""
    if not isinstance(body, dict):
        return 400, {"error": "请求体须 JSON 对象"}
    text = str(body.get("text") or "").strip()
    if not text:
        return 400, {"error": SCREEN_TEXTS[1]}
    target, objective = _parse_target(text)
    if target is None:
        return 422, {"error": SCREEN_TEXTS[0]}
    scope = _scope_preview(target)
    budget_cap = (os.environ.get(ENV_BUDGET) or "").strip()
    return 200, {
        "card_version": CARD_VERSION,
        "target": target,
        "objective": objective,
        "scope_preview": scope,
        "red_lines": list(RED_LINES),
        "budget_cap": budget_cap,
        "form": {"name": target, "note": objective,
                 "budget": budget_cap, "scope": scope},
        "needs_confirm": True,
        "confirm_route": CONFIRM_ROUTE,
        "note": SCREEN_TEXTS[2],
    }


# ---------------------------------------------------------------- ② @引用 --

def at_search(query, ledger_dir):
    """GET /api/v2/at-search?q=关键词[&goal=G] → 账本四表 fuzzy 命中（只读）。"""
    q = str((query or {}).get("q") or "").strip()
    if not q:
        return 400, {"error": SCREEN_TEXTS[3]}
    gd = _goal_dir(ledger_dir, str((query or {}).get("goal") or "").strip())
    needle = q.lower()
    hits = []
    s = core.Session(gd)
    for tname, kind in KIND_WORDS.items():
        tcol = core.TABLES[tname].index(_TITLE_COL[tname])
        for i, r in enumerate(s.rows(tname)):
            ident = r[0].strip()
            if not ident:
                continue
            title = r[tcol] if tcol < len(r) else ""
            hay = " ".join([ident, title] + [c for c in r if str(c).strip()])
            if needle not in hay.lower():
                continue
            row_no = i + 1
            hits.append({
                "table": tname, "row": row_no, "id": ident,
                "kind": kind,
                "label": " ".join(x for x in (kind, ident, title) if x),
                "ref": "[%s#%d]" % (tname, row_no),
                "anchor": {"table": tname, "id": ident, "row": row_no},
                "_rank": (0 if needle in ident.lower() else 1, row_no),
            })
    hits.sort(key=lambda h: (h["_rank"], h["table"], h["row"]))
    for h in hits:
        del h["_rank"]
    hits = hits[:SEARCH_CAP]
    if not hits:
        return 200, {"q": q, "hits": [], "hint": SCREEN_TEXTS[4]}
    return 200, {"q": q, "hits": hits}


_RETEST_WORDS = ("再测一次", "再测一遍", "再测", "重测", "复测", "重新测")


def at_dispatch(body, ledger_dir):
    """POST /api/v2/at-dispatch {anchor, command} → @引用派活进活池（复测类）。"""
    import contextlib, io
    if not isinstance(body, dict):
        return 400, {"error": "请求体须 JSON 对象"}
    command = str(body.get("command") or "").strip()
    if not command:
        return 400, {"error": "缺派活指令——请说明要它做什么（如：再测一次）"}
    if not any(w in command for w in _RETEST_WORDS):
        return 422, {"error": SCREEN_TEXTS[5]}
    gd = _goal_dir(ledger_dir, str(body.get("goal") or "").strip())
    st, anchor = api_v2_ask.resolve_anchor(gd, body.get("anchor"))
    if st != 200:
        return st, anchor
    tname = anchor["table"]
    if tname not in KIND_WORDS:
        return 422, {"error": "该对象不支持派活（支持：目标/漏洞/事实/任务）"}
    kind = KIND_WORDS[tname]
    s = core.Session(gd)
    rows = s.rows(tname)
    row = rows[anchor["row"] - 1]
    title = row[core.TABLES[tname].index(_TITLE_COL[tname])] if rows else ""
    label = " ".join(x for x in (kind, anchor["id"], title) if x)
    title = "复测" + label
    detail = "@引用派活 %s（源 %s 行指纹 %s）" % (command, anchor["ref"],
                                                  anchor["line_hash"])
    argv = ["--title=" + title, "--detail=" + detail,
            "--engine=web-blackbox", "--kind=nday-verify",
            "--origin=recon-event", "--budget-share=1;1;1",
            "--timestamp=" + _utc_now()]
    if tname == "assets.tsv":
        argv.append("--asset=" + anchor["id"])      # 界内闭合（账本级校验）
    buf, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = registry.lookup("add-intent")(gd, argv)
    except Exception as e:                     # 通道兜底拒收（非 Reject 形）
        rc, out = 1, str(e)
    else:
        out = buf.getvalue() + err.getvalue()   # Reject=stderr REJECT 行（_wrap）
    if rc != 0:
        if "dedup_key" in out:
            exist = [r for r in s.rows("intents.tsv")
                     if r[core.TABLES["intents.tsv"].index("dedup_key")]
                     .endswith("+" + title)]
            return 200, {"ok": True, "dedup": True,
                         "intent_id": exist[0][0] if exist else "",
                         "note": "同对象同指令已派过——不重复入池（机械判重）"}
        return 422, {"ok": False, "error": "派活被拒：" + out.strip()[:200]}
    first = out.splitlines()[0] if out.splitlines() else ""
    rid = first.split("\t")[1] if first.startswith("OK\t") else ""
    return 200, {"ok": True, "dedup": False, "intent_id": rid,
                 "ref": anchor["ref"],
                 "note": "复测任务卡已入活池——士兵领到即开工"}


# ---------------------------------------------------------------- ③ 回复四分类 --

def classify_reply(text):
    """一句话回复 → approve|reject|redirect|intel（确定性词表；缺省=情报）。"""
    low = str(text or "").lower()
    for w in _REJECT_WORDS:
        if w in low:
            return "reject"
    for w in _APPROVE_WORDS:
        if w in low:
            return "approve"
    for w in _REDIRECT_WORDS:
        if w in low:
            return "redirect"
    return "intel"          # 保守缺省：原文必达士兵，绝不自动批准


def steer_reply(body, ledger_dir):
    """POST /api/v2/steer-reply {warrior, reply[, context]} → 四分类+路由/注入。"""
    if not isinstance(body, dict):
        return 400, {"error": "请求体须 JSON 对象"}
    reply = str(body.get("reply") or "").strip()
    if not reply:
        return 400, {"error": "缺回复内容——请先输入要回给士兵的话"}
    warrior = str(body.get("warrior") or "").strip() or "w1"
    gd = _goal_dir(ledger_dir, str(body.get("goal") or "").strip())
    category = classify_reply(reply)
    if category in ("approve", "reject"):
        ctx = body.get("context")
        if not isinstance(ctx, dict) or not ctx.get("row"):
            return 422, {"error": SCREEN_TEXTS[6]}
        decision = "approved" if category == "approve" else "rejected"
        return 200, {
            "category": category,
            "action": {"route": "/api/approval",
                       "body": {"row": ctx.get("row"),
                                "decision": decision,
                                "_approval_sig": str(
                                    ctx.get("_approval_sig") or "")}},
            "note": SCREEN_TEXTS[7],
        }
    text = ("【转向】" if category == "redirect" else "【情报】") + reply
    ts = _utc_now()
    steer.write_steer(gd, warrior, text, ts)
    try:
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl_row = sum(1 for _ in f)
    except OSError:
        tl_row = 0
    note = SCREEN_TEXTS[8] if category == "redirect" else SCREEN_TEXTS[9]
    return 200, {"category": category, "warrior": warrior,
                 "timeline_row": tl_row, "note": note}


# ---------------------------------------------------------------- include 挂载口 --

def _at_search_route(query, ledger_dir=None, battles_dir=None):
    return at_search(query, ledger_dir)


ROUTES[ROUTE_AT_SEARCH] = _at_search_route
POST_ROUTES[ROUTE_PROPOSE] = propose
POST_ROUTES[ROUTE_AT_DISPATCH] = at_dispatch
POST_ROUTES[ROUTE_STEER_REPLY] = steer_reply


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口（GET）→ (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)


def dispatch_post(path, body, ledger_dir):
    """include 机制分发口（POST）→ (status, payload) | None(非本域路由)。"""
    fn = POST_ROUTES.get(path)
    if fn is None:
        return None
    return fn(body, ledger_dir)
