# -*- coding: utf-8 -*-
"""api_v2_ask（全域锚定对话 MVP·anchored-chat-v1）——页内只读 AI 问答面。

舰间契约：本文件=本舰独写；挂载=POST_ROUTES 单源表由 include 机制
（api_pages.py，UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_anchored_chat.py
（_V2MountHandler）：POST 过会话门+CSRF 双检（Handler._guard_csrf），缺会话
=401 JSON。设计权威 docs/design/contextual-chat-v1.md（MVP 裁剪见下）。

只读律（MVP 边界，测试钉死）：
- AI 只回答、不执行任何动作——本模块零账本写（不铸 timeline 行、不改表、
  不派意图）；成功路径唯一落盘=llmpool_state.json（模型道健康运行态，与
  智能体运行时同位同律——llmpool_wire.attach 钉根 goal 目录）。
- 对话不落账（timeline 线程/审批门=后续舰接入）；历史仅页内会话态。

机制（同 warrior 通道链）：
- 模型道=channels JSON 文件（[{"name","model","base_url","api_key"}…]，
  与 cli/warrior --channels 同格式），位置=env TANYIN_ASK_CHANNELS——缺/
  坏=503 人话；调用=warrior.model_client.ModelClient（llmpool 选道+故障
  转移+用量入 Reply），全道失败=502。
- 锚=账本行址（表+行号+行内容指纹 sha256 前 12）：发现锚富化=本行+关联
  证据行（linked_finding 反指 ∪ evidence_ids）+所属意图行——零手工粘贴。
- 引用核验：答案里的 [table.tsv#N] 标签逐个对回真实行——存在=ok:true 带
  指纹+标签；不存在=ok:false（页端亮「未命中」），不信模型自报。
"""
import hashlib
import json
import os
import re

from ledger import core
from ledger import llmpool_wire
from warrior import model_client

ROUTE_ASK = "/api/v2/ask"
ROUTES: dict = {}                                 # GET 面：本模块无（纯 POST）
POST_ROUTES = {ROUTE_ASK: None}                    # 尾部赋真身（前向引用）
# （ROUTES/POST_ROUTES 前向引用形=舰队单源表惯例，同 api_v2_findings）

ENV_CHANNELS = "TANYIN_ASK_CHANNELS"

# 可锚表白名单：（id 列, 标题列, 界面词）——表外锚=400（不开放任意文件读）
_ANCHORABLE = {
    "findings.tsv": ("id", "title", "发现"),
    "intents.tsv": ("id", "title", "意图"),
    "E-index.tsv": ("id", "title", "证据"),
    "assets.tsv": ("id", "value", "资产"),
    "goals.tsv": ("id", "target", "任务"),
}
_CITE_RE = re.compile(r"\[([A-Za-z][\w-]*\.tsv)#(\d+)\]")
_HASH_LEN = 12

SYSTEM_PROMPT = (
    "你是安全测试平台 GraphLed 的只读助手。只依据用户给出的账本行上下文回答；"
    "引用事实时必须带上行址标签（如 [findings.tsv#1]）；上下文里没有的信息"
    "就说不知道，不要编造。你只能回答问题，不能执行任何操作，也不要给出"
    "需要平台代为执行的指令。"
)


def _goal_dir(base, goal):
    """goal= 同名目录优先（本 goal 内子目录，次选同辈）——多战宿主可定位。"""
    if not goal:
        return base
    for cand in (os.path.join(base, goal), os.path.join(os.path.dirname(base), goal)):
        if os.path.isdir(cand):
            return cand
    return base


def _raw_lines(gd, tname):
    """表文件原文行（1-based=数据行号，账本表无表头——read_tsv 同律，
    空行跳过两端对齐）——指纹与行号的单源。"""
    try:
        with open(os.path.join(gd, tname), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    return [ln for ln in text.split("\n") if ln.strip()]


def _line_hash(raw_line):
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()[:_HASH_LEN]


def _keyvals(tname, vals):
    cols = core.TABLES[tname]
    return " | ".join("%s=%s" % (c, v) for c, v in zip(cols, vals)
                      if str(v).strip())


def _label(tname, vals):
    id_col, title_col, kind = _ANCHORABLE[tname]
    try:
        ident = vals[core.TABLES[tname].index(id_col)] or ""
        title = vals[core.TABLES[tname].index(title_col)] or ""
    except (ValueError, IndexError):
        ident, title = "", ""
    out = " ".join(x for x in (ident, title) if x)
    return (kind + " " + out).strip()


def _ctx_entry(gd, tname, rown, rows, raws):
    return {"ref": "[%s#%d]" % (tname, rown), "table": tname, "row": rown,
            "label": _label(tname, rows[rown - 1]),
            "keyvals": _keyvals(tname, rows[rown - 1]),
            "line_hash": _line_hash(raws[rown - 1])}


# ---------------------------------------------------------------- 锚解析 --

def resolve_anchor(gd, anchor):
    """锚 → (200, {table,row,id,label,ref,line_hash,context[]}) |
    (400|404, {error})。行号=数据行 1-based（去表头）。"""
    if not isinstance(anchor, dict):
        return 400, {"error": "缺锚定对象——先选中一行账本（如一个发现）再提问"}
    tname = str(anchor.get("table") or "").strip()
    if tname not in _ANCHORABLE:
        return 400, {"error": "该表不支持锚定提问（支持：发现/意图/证据/资产/任务）"}
    rows = core.Session(gd).rows(tname)
    raws = _raw_lines(gd, tname)
    id_col = _ANCHORABLE[tname][0]
    idx = None
    ident = str(anchor.get("id") or "").strip()
    if ident:
        for i in range(len(rows) - 1, -1, -1):      # 后行覆盖=最新态
            if rows[i][core.TABLES[tname].index(id_col)] == ident:
                idx = i
                break
        if idx is None:
            return 404, {"error": "锚定的%s不存在: %s" % (_ANCHORABLE[tname][2],
                                                          ident)}
    else:
        try:
            n = int(anchor.get("row") or 0)
        except (TypeError, ValueError):
            return 400, {"error": "缺锚定对象——须给 id 或行号(row)"}
        if not 1 <= n <= len(rows):
            return 404, {"error": "行号越界: %s#%d（共 %d 行）"
                                   % (tname, n, len(rows))}
        idx = n - 1
        ident = rows[idx][core.TABLES[tname].index(id_col)]
    rown = idx + 1
    context = [_ctx_entry(gd, tname, rown, rows, raws)]
    # —— 发现锚富化：关联证据行 + 所属意图行 ——
    if tname == "findings.tsv":
        frow = rows[idx]
        tf = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
        want = set(x.strip() for x in
                   (frow[tf["evidence_ids"]] or "").split(",") if x.strip())
        ev_rows = core.Session(gd).rows("E-index.tsv")
        ev_raws = _raw_lines(gd, "E-index.tsv")
        te = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
        for i, er in enumerate(ev_rows):
            if er[te["linked_finding"]] == ident or er[te["id"]] in want:
                context.append(_ctx_entry(gd, "E-index.tsv", i + 1,
                                          ev_rows, ev_raws))
        iid = frow[tf["intent_id"]]
        if iid:
            in_rows = core.Session(gd).rows("intents.tsv")
            in_raws = _raw_lines(gd, "intents.tsv")
            ti = {f: i for i, f in enumerate(core.TABLES["intents.tsv"])}
            for i, ir in enumerate(in_rows):
                if ir[ti["id"]] == iid:
                    context.append(_ctx_entry(gd, "intents.tsv", i + 1,
                                              in_rows, in_raws))
                    break
    return 200, {"table": tname, "row": rown, "id": ident,
                 "label": _label(tname, rows[idx]),
                 "ref": "[%s#%d]" % (tname, rown),
                 "line_hash": _line_hash(raws[idx]) if idx < len(raws) else "",
                 "context": context}


# ---------------------------------------------------------------- 模型道 --

def _load_channels():
    """env TANYIN_ASK_CHANNELS → (0, channels) | (503, {error})。"""
    path = (os.environ.get(ENV_CHANNELS) or "").strip()
    if not path:
        return 503, {"error": "模型通道未配置——请设 %s 指向通道文件"
                              "（与智能体运行时 --channels 同格式）" % ENV_CHANNELS}
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return 503, {"error": "模型通道文件不可读或不是合法 JSON: %s" % path}
    if (not isinstance(doc, list) or not doc or
            any(not isinstance(c, dict) or not c.get("name")
                or not c.get("base_url") for c in doc)):
        return 503, {"error": "模型通道格式不对——须 JSON 数组且每条含 "
                              "name/base_url"}
    return 0, doc


def _user_prompt(anchor, message):
    lines = ["【提问对象】%s（%s 第 %d 行）" % (anchor["label"], anchor["table"],
                                               anchor["row"]),
             "", "【账本行上下文】（引用事实请使用行址标签，如 %s）"
             % anchor["ref"]]
    for c in anchor["context"]:
        lines.append("%s %s" % (c["ref"], c["keyvals"]))
    lines.append("")
    lines.append("【问题】")
    lines.append(message)
    return "\n".join(lines)


def _verify_citations(text, gd):
    """答案内 [table.tsv#N] → 逐个对回真实行；不存在=ok:false（不信自报）。"""
    out, seen = [], set()
    for m in _CITE_RE.finditer(text):
        ref = m.group(0)
        if ref in seen:
            continue
        seen.add(ref)
        tname, rown = m.group(1), int(m.group(2))
        entry = {"ref": ref, "table": tname, "row": rown, "ok": False,
                 "line_hash": "", "label": ""}
        if tname in _ANCHORABLE:
            rows = core.Session(gd).rows(tname)
            raws = _raw_lines(gd, tname)
            if 1 <= rown <= len(rows) and rown <= len(raws):
                entry.update(ok=True, line_hash=_line_hash(raws[rown - 1]),
                             label=_label(tname, rows[rown - 1]))
        out.append(entry)
    return out


# ---------------------------------------------------------------- 主入口 --

def ask(body, ledger_dir):
    """POST /api/v2/ask {goal, anchor{table,id|row}, message} → 只读问答。"""
    if not isinstance(body, dict):
        return 400, {"error": "请求体须 JSON 对象"}
    gd = _goal_dir(ledger_dir, str(body.get("goal") or "").strip())
    st, anchor = resolve_anchor(gd, body.get("anchor"))
    if st != 200:
        return st, anchor
    message = str(body.get("message") or "").strip()
    if not message:
        return 400, {"error": "缺问题内容——请先输入要问的问题"}
    st, channels = _load_channels()
    if st:
        return st, channels
    pool = llmpool_wire.attach(gd)          # 池态钉根 goal（同智能体运行时）
    client = model_client.ModelClient(channels, pool)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(anchor, message)}]
    reply = client.chat(messages)
    if not reply.ok:
        return 502, {"error": "模型通道暂时不可用，请稍后再试",
                     "reason": reply.reason}
    return 200, {
        "answer": reply.content,
        "model": reply.model,
        "usage": {"prompt_tokens": reply.prompt_tokens,
                  "completion_tokens": reply.completion_tokens},
        "citations": _verify_citations(reply.content, gd),
        "anchor": {"table": anchor["table"], "row": anchor["row"],
                   "id": anchor["id"], "label": anchor["label"],
                   "ref": anchor["ref"], "line_hash": anchor["line_hash"]},
        "attempts": reply.attempts,
        "read_only": True,
    }


POST_ROUTES[ROUTE_ASK] = ask


def dispatch_post(path, body, ledger_dir):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = POST_ROUTES.get(path)
    if fn is None:
        return None
    return fn(body, ledger_dir)
