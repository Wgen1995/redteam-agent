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
"""
import contextlib
import hashlib
import io

from . import core, registry
from .query_cmds import _cell
from .write_cmds import (LEASE_EXPIRED_REASON, _INTENT_KINDS, INTENT_ORIGINS,
                         _OWNER_MARK_RE, _seg_num)

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


def classify(s, iid):
    """意图终态四分类（纯机械：终态标记+产出计数+矩阵置格；不 LLM）。

    非终态（candidate/pending/active/deferred）与 lease-expired 回收行 → None
    （R-REP-5：自动复活律管辖）。返回含全部机械信号的裁决 dict（审计面）。
    """
    row = _latest_intents(s).get(iid)
    if row is None:
        return None
    status = _cell(row, "intents.tsv", "status")
    reason = _cell(row, "intents.tsv", "reason").strip()
    base = {"intent_id": iid, "status": status, "reason": reason,
            "trace_lines": trace_lines(s, iid),
            "outputs": output_count(s, iid),
            "matrix_marks": matrix_marks(s, iid)}
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


# ---------------------------------------------------------------- 既有写入通道

def _run(gd, cmd, args):
    """CLI 级既有入口（registry.lookup=goal 写锁包装执法链），stdout 捕获。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    return rc, buf.getvalue()


def _redispatch(gd, iid, ts):
    """纯故障重派（R-REP-2）：机械审批→原卡 blocked→active 重入在途集。"""
    chash = hashlib.sha256(
        ("set-intent-status --id=%s --status=active" % iid).encode("utf-8")
    ).hexdigest()
    rc, out = _run(gd, "approve", [
        "--command-hash=" + chash, "--decision=approved", "--approver=" + OWNER,
        "--note=R-REP-2 replacer 纯故障重派预授权（transport-fault，零执行零产出）",
        "--timestamp=" + ts])
    if rc != 0:
        raise RuntimeError("重派预授权被拒: " + out)
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


def _conclusions(s, iid):
    """已得结论：facts.detail + findings.title 按 intent_id 归因（截 200 字/条）。"""
    out = [_cell(r, "facts.tsv", "detail")[:200]
           for r in s.rows("facts.tsv")
           if _cell(r, "facts.tsv", "intent_id") == iid]
    out += [_cell(r, "findings.tsv", "title")[:200]
            for r in s.rows("findings.tsv")
            if _cell(r, "findings.tsv", "intent_id") == iid]
    return out


def _continue_card(gd, iid, row, ts):
    """接续收口（R-REP-3）：续接卡带已得结论+剩余步骤；dedup 判重=幂等。"""
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
    concl = _conclusions(s, iid)
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


def _solidify(gd, iid, row, ts):
    """边界固化（R-REP-4）：写收口事实，不重派；同 intent 判重=幂等。"""
    s = core.Session(gd)
    for r in s.rows("facts.tsv"):
        if (_cell(r, "facts.tsv", "intent_id") == iid
                and _cell(r, "facts.tsv", "detail").startswith(_CLOSEOUT_MARK)):
            return None                  # 幂等：收口事实已在账
    detail = "%s 此路不通（rejected; reason=%s；trace=%d 行/产出=%d）" % (
        _CLOSEOUT_MARK, _cell(row, "intents.tsv", "reason").strip(),
        trace_lines(s, iid), output_count(s, iid))
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
    """
    out = []
    s = core.Session(goal_dir)
    for iid, row in sorted(_latest_intents(s).items()):
        if only is not None and iid not in only:
            continue
        v = classify(s, iid)
        if v is None:
            continue
        if v["verdict"] == VERDICT_FAULT:
            _redispatch(goal_dir, iid, ts)
        elif v["verdict"] == VERDICT_CONTINUE:
            _continue_card(goal_dir, iid, row, ts)
        elif v["verdict"] == VERDICT_BOUNDARY:
            _solidify(goal_dir, iid, row, ts)
        # complete：零写入（R-REP-6）
        out.append(v)
    return out
