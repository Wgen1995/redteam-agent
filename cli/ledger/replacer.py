# -*- coding: utf-8 -*-
"""重派四分类器（功能5/8·补件三，设计 docs/design/2026-10-20-priority-planner-design.md）。

意图终态时纯机械判（trace 行数+终态标记+产出计数，不 LLM——ARTEX 活体解剖⑧
纪律落地）：
  纯故障重派 fault-redispatch ：trace 零执行+传输故障标记 → 原卡重入池
  接续收口   continue-closeout：跑了部分断（有产出有终态未达）→ 续接卡带
                                 已得结论+剩余步骤
  边界固化   boundary-solidify：否定收口（此路不通）→ 写收口事实，不重派
  完成       complete          ：正常终态，零写入

Ruling：
- R-REP-1 「trace 零执行」账本口径=产出计数（facts+findings 按 intent_id 归因）
  与矩阵置格归因皆零——timeline 生命周期行（add-intent/状态迁移）不算执行：纯
  故障卡也有领卡行。传输故障标记=blocked 行 reason 前缀 transport-fault（先例=
  lease-expired 理由词承载，13 表列集冻结→自由文本唯一承载位）。
- R-REP-2 纯故障重派动作=先经既有 approve 通道铸机械审批行（approver=
  planner:replacer，timeline 全审计）再 set-intent-status blocked→active
  （--owner=planner:replacer --lease-min=1）：原卡内容零改动重入在途集
  （{candidate,pending,active} 口径）；短租约到期后任意战士经既有 takeover
  路径重授。不冒充 lease-expired 复活（不诚实复活禁）。
- R-REP-3 blocked 其余情形（有产出/非传输故障停摆）=接续收口：续接卡经既有
  add-intent 通道铸（dedup_key 机械判重=幂等）；detail 承载已得结论+剩余
  步骤；原 blocked 卡不动（事件溯源全审计）。
- R-REP-4 边界固化=经既有 add-fact 写收口事实（kind=info，detail 前缀
  收口事实:，同 intent 判重=幂等）；不重派。
- R-REP-5 lease-expired 回收行=既有自动复活律管辖（W2·01P0-2），重派器
  不越权（classify=None）。
- R-REP-6 完成=done，零写入。

写通道纪律：全部经 ledger.registry.lookup（goal 写锁包装的既有执法链），
不直接改 write_cmds（哨兵舰在改），不私铸 TSV 行。

评审修（docs/reviews/2026-10-20-review-sentinel-planner.md §二）：
- I-2 持钥部署（TANYIN_APPROVAL_KEY 在场）机械审批走 --sig 签名通道。
- I-4 线性扫面：sweep 头部一趟聚合 intent_id→机械信号映射，Session 全
  sweep 复用一只（旧 O(I×N) 三全表扫×逐动作重读盘已除）。
"""
import contextlib
import hashlib
import io
import re

from . import core, registry
from .query_cmds import _cell
from .write_cmds import (LEASE_EXPIRED_REASON, _INTENT_KINDS, INTENT_ORIGINS,
                          _OWNER_MARK_RE, _approval_key, _approval_sig,
                          _seg_num)

TRANSPORT_MARKER = "transport-fault"
OWNER = "planner:replacer"

VERDICT_FAULT = "fault-redispatch"
VERDICT_CONTINUE = "continue-closeout"
VERDICT_BOUNDARY = "boundary-solidify"
VERDICT_COMPLETE = "complete"

_CLOSEOUT_MARK = "收口事实:"
_EV_IDX = core.TABLES["timeline.tsv"].index("event")


# ---------------------------------------------------------------- 机械信号（账本可查）

def _latest_intents(s):
    """intents 事件溯源最新行映射（文件序后者覆盖前者）。"""
    out = {}
    for r in s.rows("intents.tsv"):
        out[r[0]] = r
    return out


def trace_lines(s, iid):
    """生命周期 trace 行数：timeline 事件文本含该意图 id 的行数。"""
    return sum(1 for r in s.rows("timeline.tsv") if iid in r[_EV_IDX])


def output_count(s, iid):
    """产出计数：facts+findings 按 intent_id 归因行数。"""
    n = sum(1 for r in s.rows("facts.tsv")
            if _cell(r, "facts.tsv", "intent_id") == iid)
    n += sum(1 for r in s.rows("findings.tsv")
             if _cell(r, "findings.tsv", "intent_id") == iid)
    return n


def matrix_marks(s, iid):
    """矩阵置格归因：matrix 行 intent_id==iid 且 state 非空的行数。"""
    return sum(1 for r in s.rows("matrix.tsv")
               if _cell(r, "matrix.tsv", "intent_id") == iid
               and _cell(r, "matrix.tsv", "state").strip())


def classify(s, iid, agg=None):
    """意图终态四分类（纯机械：终态标记+产出计数+矩阵置格；不 LLM）。

    非终态（candidate/pending/active/deferred）与 lease-expired 回收行 → None
    （R-REP-5：自动复活律管辖）。返回含全部机械信号的裁决 dict（审计面）。
    agg=sweep 头部 _aggregate 的预聚合映射（评审 I-4：免逐意图三全表扫，
    同判同果）；缺省=逐意图现算（独立调用面行为不变）。
    """
    if agg is not None:
        entry = agg.get(iid)
        row = entry["latest"] if entry is not None else None
    else:
        row = _latest_intents(s).get(iid)
    if row is None:
        return None
    status = _cell(row, "intents.tsv", "status")
    reason = _cell(row, "intents.tsv", "reason").strip()
    if agg is not None:
        trace_n, outputs, marks = (entry["trace_lines"], entry["outputs"],
                                   entry["matrix_marks"])
    else:
        trace_n = trace_lines(s, iid)
        outputs = output_count(s, iid)
        marks = matrix_marks(s, iid)
    base = {"intent_id": iid, "status": status, "reason": reason,
            "trace_lines": trace_n, "outputs": outputs,
            "matrix_marks": marks}
    if status == "done":
        return dict(base, verdict=VERDICT_COMPLETE)
    if status == "rejected":
        return dict(base, verdict=VERDICT_BOUNDARY)
    if status == "blocked":
        if reason == LEASE_EXPIRED_REASON:
            return None
        if (reason.startswith(TRANSPORT_MARKER) and base["outputs"] == 0
                and base["matrix_marks"] == 0):
            return dict(base, verdict=VERDICT_FAULT)
        return dict(base, verdict=VERDICT_CONTINUE)
    return None


# ---------------------------------------------------------------- 一趟聚合（评审 I-4）

_TRACE_SEP = frozenset(" \t\r\n,;:()[]{}\"'<>|")   # 事件文本 id 词元边界
_INT_AT = re.compile("(?=INT-)")


def _count_trace(ev, agg, lens, seen):
    """单事件行 trace 计数：行内每个 INT- 起点取最大 id 形词元，已知 iid
    （=词元前缀，逐前缀长度试）计数一次——与旧「iid 子串出现于该行」在
    账本真实形态（write_cmds 事件以空白/标点分隔嵌 id）逐行等价；对抗性
    把 id 嵌进更长非法 id 字面量的文本不计（trace_lines 是审计面非判据）。"""
    n = len(ev)
    for m in _INT_AT.finditer(ev):
        j = m.start()
        k = j
        while k < n and ev[k] not in _TRACE_SEP:
            k += 1
        run = ev[j:k]
        for ln in lens:
            x = run[:ln]
            hit = agg.get(x)
            if hit is not None and x not in seen:
                seen.add(x)
                hit["trace_lines"] += 1


def _aggregate(s):
    """sweep 头部一趟聚合（评审 I-4）→ {iid: 机械信号}。

    单趟扫 intents/timeline/facts/findings/matrix 建
    {iid: {"latest","trace_lines","outputs","matrix_marks","concl"}}；
    sweep 分类与动作读面（续接结论/收口幂等判重）全程复用——旧路径每意图
    三全表扫 O(I×N)（万格实测 8.32s/轮）+逐动作重开 Session 全量重读盘，
    均除。concl=facts.detail[:200]+findings.title[:200]（_conclusions 同序
    同截）。"""
    agg = {}
    for iid, row in _latest_intents(s).items():
        agg[iid] = {"latest": row, "trace_lines": 0, "outputs": 0,
                    "matrix_marks": 0, "concl": []}
    if not agg:
        return agg
    lens = sorted({len(iid) for iid in agg})
    for r in s.rows("timeline.tsv"):
        seen = set()                     # 每行每 iid 至多计一次（同旧口径）
        _count_trace(r[_EV_IDX], agg, lens, seen)
    for r in s.rows("facts.tsv"):
        hit = agg.get(_cell(r, "facts.tsv", "intent_id"))
        if hit is not None:
            hit["outputs"] += 1
            hit["concl"].append(_cell(r, "facts.tsv", "detail")[:200])
    for r in s.rows("findings.tsv"):
        hit = agg.get(_cell(r, "findings.tsv", "intent_id"))
        if hit is not None:
            hit["outputs"] += 1
            hit["concl"].append(_cell(r, "findings.tsv", "title")[:200])
    for r in s.rows("matrix.tsv"):
        if _cell(r, "matrix.tsv", "state").strip():
            hit = agg.get(_cell(r, "matrix.tsv", "intent_id"))
            if hit is not None:
                hit["matrix_marks"] += 1
    return agg


# ---------------------------------------------------------------- 既有写入通道

def _run(gd, cmd, args):
    """CLI 级既有入口（registry.lookup=goal 写锁包装执法链）。

    stdout+stderr 合并捕获（评审 I-1）：REJECT 走 stderr——合并文本带回
    拒绝原因并供 "dedup_key" 竞速合并判定（planner_loop._run 同型修法）。
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    return rc, buf.getvalue()


def _redispatch(gd, iid, ts):
    """纯故障重派（R-REP-2）：机械审批→原卡 blocked→active 重入在途集。

    持钥通道（评审 I-2）：TANYIN_APPROVAL_KEY 在场（生产姿态，HANDOFF
    B2「AI 写者再不能自铸 approvals 行」）时 approve 强制
    --sig=HMAC-SHA256(sha256(key), command_hash)——机械审批与人工同律
    走签名通道：密钥来源=环境（部署面注入，同律），HMAC 式复用既有单源
    write_cmds._approval_sig（不自铸第二份签名式）。
    """
    chash = hashlib.sha256(
        ("set-intent-status --id=%s --status=active" % iid).encode("utf-8")
    ).hexdigest()
    ap_args = [
        "--command-hash=" + chash, "--decision=approved", "--approver=" + OWNER,
        "--note=R-REP-2 replacer 纯故障重派预授权（transport-fault，零执行零产出）",
        "--timestamp=" + ts]
    akey = _approval_key()
    if akey:
        ap_args.append("--sig=" + _approval_sig(chash, akey))
    rc, out = _run(gd, "approve", ap_args)
    if rc != 0:
        raise RuntimeError("重派预授权被拒: " + out)
    ap = _approval_id_of(out)
    if ap is None:
        # OK 回执行不可解析 → 回退读己之写（新鲜 Session 扫描；评审 I-4 正常
        # 路径零 Session——审批行 id 取自执法链自己的 OK 回执行）
        s = core.Session(gd)
        ap = None
        for r in s.rows("approvals.tsv"):
            if (_cell(r, "approvals.tsv", "command_hash") == chash
                    and _cell(r, "approvals.tsv", "approver") == OWNER):
                ap = r[0]
        if ap is None:
            raise RuntimeError("重派预授权行铸后不可见（读己之写破）")
    rc, out = _run(gd, "set-intent-status", [
        "--id=" + iid, "--status=active", "--approval=" + ap,
        "--reason=transport-fault 纯故障重派（R-REP-1 判据成立）",
        "--owner=" + OWNER, "--lease-min=1", "--timestamp=" + ts])
    if rc != 0:
        raise RuntimeError("原卡重入池被拒: " + out)


def _approval_id_of(out):
    """approve 的 OK 回执行首行=「OK<TAB>AP-xxx<TAB>approvals.tsv」（_ok_line
    金样钉死面）——取新铸审批行 id，免重开 Session 全量重读盘（评审 I-4）。"""
    first = out.splitlines()[0] if out else ""
    parts = first.split(chr(9))
    if len(parts) >= 2 and parts[0] == "OK" and parts[1].startswith("AP"):
        return parts[1]
    return None


def _conclusions(s, iid):
    """已得结论：facts.detail + findings.title 按 intent_id 归因（截 200 字/条）。"""
    out = [_cell(r, "facts.tsv", "detail")[:200]
           for r in s.rows("facts.tsv")
           if _cell(r, "facts.tsv", "intent_id") == iid]
    out += [_cell(r, "findings.tsv", "title")[:200]
            for r in s.rows("findings.tsv")
            if _cell(r, "findings.tsv", "intent_id") == iid]
    return out


def _continue_card(gd, iid, row, ts, s=None, agg=None):
    """接续收口（R-REP-3）：续接卡带已得结论+剩余步骤；dedup 判重=幂等。

    s/agg=sweep 传入的复用 Session 与头部聚合映射（评审 I-4；缺省=自开
    Session 现算，独立调用面行为不变）。共享 Session 对本轮 sweep 内新铸
    续接卡不可见——同轮同 dedup 撞卡由 add-intent 执法链 dedup_key 拒收
    兜住（I-1 修后=合并不 raise），账面仍恰一张。"""
    if s is None:
        s = core.Session(gd)
    title = "续接: " + _cell(row, "intents.tsv", "title")
    kind = _cell(row, "intents.tsv", "kind")
    if kind not in _INTENT_KINDS:
        kind = "matrix-test"        # 旧数据 kind 空时缺省（枚举硬门兜底）
    origin = _cell(row, "intents.tsv", "origin")
    if origin not in INTENT_ORIGINS:
        origin = "adjacency"
    budget = _cell(row, "intents.tsv", "budget_share")
    seg = budget.split(";")
    if len(seg) not in (3, 4) or not all(_seg_num(x) for x in seg):
        budget = "1;1;1"
    priority = _cell(row, "intents.tsv", "priority")
    try:
        if not (0.0 <= float(priority) <= 1.0):
            raise ValueError
    except ValueError:
        priority = ""
    dedup = "-+" + kind + "+" + title
    if dedup in {_cell(r, "intents.tsv", "dedup_key")
                 for r in s.rows("intents.tsv")}:
        return None                      # 幂等：续接卡已在池
    rest = _OWNER_MARK_RE.sub("", _cell(row, "intents.tsv", "detail")).strip()
    concl = (agg[iid]["concl"]
             if agg is not None and iid in agg else _conclusions(s, iid))
    detail = "续接 %s；已得结论: %s；剩余步骤: %s" % (
        iid, "；".join(concl) if concl else "无", rest or "无")
    args = ["--title=" + title, "--detail=" + detail,
            "--engine=" + (_cell(row, "intents.tsv", "engine") or "web-blackbox"),
            "--kind=" + kind, "--origin=" + origin, "--budget-share=" + budget,
            "--timestamp=" + ts]
    if priority:
        args.append("--priority=" + priority)
    rc, out = _run(gd, "add-intent", args)
    if rc != 0 and "dedup_key" not in out:
        raise RuntimeError("续接卡铸造被拒: " + out)
    return title


def _solidify(gd, iid, row, ts, s=None, sig=None):
    """边界固化（R-REP-4）：写收口事实，不重派；同 intent 判重=幂等。

    s/sig=sweep 传入的复用 Session 与分类裁决机械信号（评审 I-4；缺省=
    自开 Session 现算，独立调用面行为不变）。"""
    if s is None:
        s = core.Session(gd)
    for r in s.rows("facts.tsv"):
        if (_cell(r, "facts.tsv", "intent_id") == iid
                and _cell(r, "facts.tsv", "detail").startswith(_CLOSEOUT_MARK)):
            return None                  # 幂等：收口事实已在账
    if sig is not None:
        trace_n, outputs = sig["trace_lines"], sig["outputs"]
    else:
        trace_n, outputs = trace_lines(s, iid), output_count(s, iid)
    detail = "%s 此路不通（rejected; reason=%s；trace=%d 行/产出=%d）" % (
        _CLOSEOUT_MARK, _cell(row, "intents.tsv", "reason").strip(),
        trace_n, outputs)
    rc, out = _run(gd, "add-fact", [
        "--intent-id=" + iid, "--kind=info",
        "--target=" + (_cell(row, "intents.tsv", "title") or iid)[:200],
        "--detail=" + detail, "--confidence=1.0", "--timestamp=" + ts])
    if rc != 0:
        raise RuntimeError("收口事实被拒: " + out)
    return detail


# ---------------------------------------------------------------- 扫面入口

def sweep(goal_dir, ts, only=None):
    """全部终态意图四分类+执行对应动作（只扫 only 集则限域）。

    返回裁决 dict 列表（含机械信号，审计/报告面）；非终态与 lease-expired
    跳过；动作幂等（dedup/收口判重），重复 sweep 零重复写入。

    线性扫面（评审 I-4）：头部 _aggregate 一趟聚合 intent_id→(latest/trace/
    产出/置格/结论) 映射，Session 全 sweep 复用一只——旧路径每意图三全表
    扫+classify 重建 latest 映射+逐动作重开 Session 全量重读盘（O(I×N)，
    评审实测万格 8.32s/轮）已除；写路径（registry→Ctx）自身的加载=既有
    执法链成本，不在本面。"""
    out = []
    s = core.Session(goal_dir)
    agg = _aggregate(s)
    for iid, entry in sorted(agg.items()):
        if only is not None and iid not in only:
            continue
        row = entry["latest"]
        v = classify(s, iid, agg=agg)
        if v is None:
            continue
        if v["verdict"] == VERDICT_FAULT:
            _redispatch(goal_dir, iid, ts)
        elif v["verdict"] == VERDICT_CONTINUE:
            _continue_card(goal_dir, iid, row, ts, s=s, agg=agg)
        elif v["verdict"] == VERDICT_BOUNDARY:
            _solidify(goal_dir, iid, row, ts, s=s, sig=v)
        # complete：零写入（R-REP-6）
        out.append(v)
    return out
