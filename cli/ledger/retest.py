# -*- coding: utf-8 -*-
"""功能13补件二·定时复验器（设计档 2026-10-20-sentinel-retest-design.md §补二）——三命令。

① retest-pending（查）：过期清单。last_verified ≡ findings 事件溯源最新行 created
   （入库时落=add-finding created；复验时刷新=沿 set-replay-state/set-cred-status
   「追加行刷新 created」既有形——13 表列集冻结禁新增物理列，探知注记13 同律）。
   过期 ⇔ age=now-last_verified ≥ window_days（默认 7 天；<goal-dir>/retest.json
   可配 {"window_days": N}，planner.json 同型先例；--window-days 覆盖通道 G-3 同型）。
   口径=active 且 exploitation_status=verified（复验池=已验真发现）；created 空/
   不可解析=fail-closed 按过期收（宁可多复验不漏验）。
② retest-scan（写编排）：过期发现→自动生成复验卡走既有 add-intent 通道
   （registry.lookup=goal 写锁既有执法链，planner_loop._run 同型 stdout 捕获；
   本命令不持锁——禁嵌套取锁，filelock 死锁论证同款纪律）。卡：kind=nday-verify
   （既有六值，设计档「nday-verify 同型」）/origin=entity/engine=replay/
   budget_share=1;1;1/detail 带 [retest:FD-…] 标记（[prereq:] 标记同型承载）+
   原EV引用+重放命令+原 dedup_key；priority 留空给规划者五因子（不自算分）。
   幂等：活卡在途（标记卡最新态非终态）跳过；终态后下一轮铸 #N+1 轮新卡
   （dedup_key=asset+kind+title 铸造形天然防同轮重复）。
③ retest-settle（写）：复验完成事件→三态回写钩子。判定单源=tanyin-replay 三态
   （reproduced/not-reproduced/env-diff，timeline replay-probe 行；S4 四门+
   REPLAY_CAP=3 复验纪律在重放侧，本命令只消费判定——别重造）：
   - reproduced→仍真：经既有 set-replay-state VERIFIED 门（reproduced 实证）+
     last_verified 刷新（created=ts 既有形）+ retest:FD:still-true 审计事件；
   - env-diff→已修复：经既有 REPAIRED 语义（env-diff 实证过门；末值 REPAIRED
     →report_artifacts lifecycle tri=env-diff→repair-candidate 桶——对齐三桶
     语义，不另造桶）+ retest:FD:fixed 审计事件；
   - not-reproduced→环境变更（参数变了）：关旧开新沿既有 supersedes 机制——
     新发现经 add-finding --supersede=<旧FD> 铸链后，--new-finding 指认；
     settle 只验链（同 dedup_key/旧行 superseded/supersedes 边在册）+落
     retest:FD:env-changed superseded-by=<新FD> 审计事件（零新写回机制）。
   聚合偏置=任一挂接 EV 最新 not-reproduced 即 env-changed（与 set-replay-state
   G-52 门「not-reproduced 拦 VERIFIED/REPAIRED」同款 fail-closed 偏置——
   reproduced>env-diff 让位 blocked）。幂等：末次 retest:FD 事件晚于末次
   replay-probe 行=已回写拒收。回写后顺带收口 [retest:FD] 标记卡（沿状态机
   走合法箭头至终态；blocked 复活须审批→留人工并留痕）。
时间纪律：G-23 墙钟退役——一切时刻取 --timestamp 必填参数，零 datetime.now。
挂接（④最小改动）：registry._MODULES 一行注册（本模块 HANDLERS 自动入
dispatch_face/KNOWN_COMMANDS 白名单）；set-replay-state 同型锁纪律=用法校验
先行于 goal_lock，锁内只调不带锁的内部体（check_cmds._set_replay_state_locked
/write_cmds._intent_status_body），无嵌套取锁。
Ruling（verdict→三态映射）：webui 复测页语言（not-reproduced=疑似已修复）与
tanyin-replay SUGGEST（env-diff→REPAIRED）存在字面张力；取后者为机械映射，
因 G-52 门已立法「not-reproduced 后 VERIFIED/REPAIRED 须补 reproduced 探针
（--manual 不能翻案）」——env-diff→REPAIRED 是唯一零门禁矛盾、零新证据规则
的既有通路；not-reproduced→supersede 链同为既有机制（关旧开新重定性，若实为
已修复则新卡定性落空即诚实收敛）。
"""
import contextlib
import io
import json
import os
import re
import sys

from . import core
from .enforce import parse_ts
from .query_cmds import TAB, UsageError, parse_kv, usage_guard, latest_by, _cell

DEFAULT_WINDOW_DAYS = 7
_CARD_KIND = "nday-verify"      # 既有六值之一（设计档补件二「nday-verify 同型」）
_CARD_ORIGIN = "entity"         # INTENT_ORIGINS 既有值：卡源自发现/资产实体
_CARD_ENGINE = "replay"         # 复验=非 LLM 盲重放（tanyin-replay 驱动）
_CARD_BUDGET = "1;1;1"          # planner assess 同形（token;requests;hours）
_IN_SCOPE_OK = {"1", "in_scope", "true"}   # add-intent 界外资产禁派生同款口径
_RETEST_MARK_RE = re.compile(r"\[retest:(FD-[^\[\]\s]+)\]")
_PROBE_RE = re.compile(r"replay-probe (\S+) verdict=(\S+)")   # tanyin-replay 同形
_RETEST_EV_RE = re.compile(r"^retest:(FD-[^:\s]+):(still-true|fixed|env-changed)")
# 三态聚合偏置（blocked> reproduced > env-diff；manual/未知=无三态机判实证）
_AGG_ORDER = (("not-reproduced", "env-changed"), ("reproduced", "still-true"),
              ("env-diff", "fixed"))


def _ts_check(v):
    try:
        return parse_ts(v)
    except (ValueError, TypeError):
        raise UsageError("--timestamp 非法 ISO8601（形如 2026-10-20T09:00:00Z）: " + str(v))


def _load_cfg(goal_dir):
    p = os.path.join(goal_dir, "retest.json")
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except ValueError as e:
        raise UsageError("retest.json 不可解析（fail-closed）: %s" % e)
    if not isinstance(d, dict):
        raise UsageError("retest.json 须为对象（如 {\"window_days\": 3}）")
    return d


def window_days(goal_dir, override=None):
    raw = override if override is not None else _load_cfg(goal_dir).get(
        "window_days", DEFAULT_WINDOW_DAYS)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        raise UsageError("window_days 须正整数: %r" % (raw,))
    if n <= 0:
        raise UsageError("window_days 须正整数: %r" % (raw,))
    return n


# ---------------------------------------------------------------- ① 过期清单

def pending_rows(s, now_epoch, wd):
    """复验池：active+verified 发现，age≥wd 天列过期（age 不可算=fail-closed 收）。"""
    out = []
    for key, r in sorted(latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"]).items()):
        if _cell(r, "findings.tsv", "status") not in ("", "active"):
            continue
        if _cell(r, "findings.tsv", "exploitation_status") != "verified":
            continue
        lv = _cell(r, "findings.tsv", "created").strip()
        try:
            age_d = int((now_epoch - parse_ts(lv)) // 86400)
        except (ValueError, TypeError):
            age_d = None   # created 空/坏形：按过期收，age 留空
        if age_d is not None and age_d < wd:
            continue
        out.append((_cell(r, "findings.tsv", "id"), _cell(r, "findings.tsv", "title"),
                    _cell(r, "findings.tsv", "affected_asset_id"), lv,
                    "" if age_d is None else str(age_d),
                    _cell(r, "findings.tsv", "evidence_ids")))
    return out


def h_retest_pending(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"timestamp", "window-days"} or not args.get("timestamp"):
        raise UsageError("retest-pending --timestamp=ISO8601 [--window-days=N]"
                         "（窗口默认 7 天，<goal-dir>/retest.json 可配）")
    now = _ts_check(args["timestamp"])
    wd = window_days(goal_dir, args.get("window-days"))
    s = core.Session(goal_dir)
    rows = pending_rows(s, now, wd)
    print("#pending=%d%swindow_days=%d" % (len(rows), TAB, wd))
    for r in rows:
        print(TAB.join(r))
    return 0


# ---------------------------------------------------------------- ② 复验意图卡

def _card_state(s):
    """[retest:FD] 标记卡盘点：{fd: (在途卡最新态非终态?, 曾铸卡数)}。"""
    out = {}
    for r in latest_by(s.rows("intents.tsv"), "intents.tsv", ["id"]).values():
        m = _RETEST_MARK_RE.search(_cell(r, "intents.tsv", "detail") or "")
        if not m:
            continue
        fd = m.group(1)
        live, n = out.get(fd, (False, 0))
        out[fd] = (live or _cell(r, "intents.tsv", "status") not in ("done", "rejected"), n + 1)
    return out


def _run_add_intent(goal_dir, s_args):
    """CLI 级既有入口（registry.lookup=goal 写锁执法链），stdout 捕获（planner 同型）。"""
    from . import registry
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup("add-intent")(goal_dir, s_args)
    return rc, buf.getvalue()


def h_retest_scan(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"timestamp", "window-days"} or not args.get("timestamp"):
        raise UsageError("retest-scan --timestamp=ISO8601 [--window-days=N]"
                         "（过期发现→自动铸复验卡走 add-intent 通道）")
    now = _ts_check(args["timestamp"])
    ts = args["timestamp"]
    wd = window_days(goal_dir, args.get("window-days"))
    s = core.Session(goal_dir)
    expired = pending_rows(s, now, wd)
    cards = _card_state(s)
    scope = {r[0]: _cell(r, "assets.tsv", "in_scope")
             for r in latest_by(s.rows("assets.tsv"), "assets.tsv", ["id"]).values()}
    queued = skipped = hard = 0
    lines = []
    for fid, _title, asset, _lv, _age, ev_ids in expired:
        if scope.get(asset, "") not in _IN_SCOPE_OK:
            skipped += 1
            lines.append("SKIP%s%s%sasset 界外（界外资产禁派生 intent）" % (TAB, fid, TAB))
            continue
        live, rounds = cards.get(fid, (False, 0))
        if live:
            skipped += 1
            lines.append("SKIP%s%s%scard-in-flight" % (TAB, fid, TAB))
            continue
        evs = [x for x in ev_ids.split(";") if x]
        title = "retest %s #%d" % (fid, rounds + 1)
        detail = ("[retest:%s] 原EV=%s 原 dedup_key=%s 重放命令=tanyin-replay replay"
                  " --goal-dir %s --id=%s --timestamp=<T>（S4 四门+REPLAY_CAP=3"
                  " 三态判定单源=tanyin-replay）"
                  % (fid, ";".join(evs) or "-",
                     _cell(latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])[(fid,)],
                           "findings.tsv", "dedup_key"),
                     goal_dir, evs[0] if evs else "-"))
        rc, out = _run_add_intent(goal_dir, [
            "--title=" + title, "--detail=" + detail, "--engine=" + _CARD_ENGINE,
            "--kind=" + _CARD_KIND, "--origin=" + _CARD_ORIGIN,
            "--budget-share=" + _CARD_BUDGET, "--asset=" + asset, "--timestamp=" + ts])
        if rc == 0:
            queued += 1
            ol = out.splitlines()
            iid = ol[1].split(TAB)[0] if len(ol) > 1 else "-"   # OK 行次行=铸卡行首列
            lines.append("QUEUED%s%s%s%s" % (TAB, fid, TAB, iid))
        elif "dedup_key" in out:
            skipped += 1   # 并发竞速已派=合并（回放特例律）
            lines.append("SKIP%s%s%sdedup-race" % (TAB, fid, TAB))
        else:
            hard += 1
            lines.append("REJECT%s%s%s%s" % (TAB, fid, TAB,
                         out.strip().splitlines()[0] if out.strip() else "add-intent 拒收"))
    print("#expired=%d%s#queued=%d%s#skipped=%d" % (len(expired), TAB, queued, TAB, skipped))
    for ln in lines:
        print(ln)
    return 1 if hard else 0


# ---------------------------------------------------------------- ③ 三态回写

def _ev_set(s, fd):
    """复验 EV 证据集=linked_finding 挂接 ∪ finding 行自书 evidence_ids/control_evidence_ids
    （set-replay-state 探针面与 report_artifacts._replay_tri 三方同源——evidence-first
    流水里 EV 先落账 finding 后引，linked_finding 常空，finding 行自书引用才是主链）。"""
    evs = {r[0] for r in s.rows("E-index.tsv")
           if (_cell(r, "E-index.tsv", "linked_finding") or "") == fd}
    frow = latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"]).get((fd,))
    if frow is not None:
        for col in ("evidence_ids", "control_evidence_ids"):
            evs |= {x for x in (_cell(frow, "findings.tsv", col) or "").split(";")
                    if x and x.startswith("EV-")}
    return evs


def _probe_verdicts(s, fd):
    """复验 EV 集 → 每 EV 最新判定（timeline replay-probe 行，tanyin-replay 单源）。"""
    evs = _ev_set(s, fd)
    last = {}
    for r in s.rows("timeline.tsv"):
        m = _PROBE_RE.search(_cell(r, "timeline.tsv", "event"))
        if m and m.group(1) in evs:
            last[m.group(1)] = m.group(2)
    return last


def _aggregate(verdicts):
    vals = set(verdicts.values())
    for hit, state in _AGG_ORDER:
        if hit in vals:
            return state
    return None


def _last_idx(s, pred):
    for i in range(len(s.rows("timeline.tsv")) - 1, -1, -1):
        if pred(_cell(s.rows("timeline.tsv")[i], "timeline.tsv", "event")):
            return i
    return -1


def _settle_locked(goal_dir, args):
    from . import check_cmds
    from .write_cmds import Ctx as _WCtx, _intent_status_body, Reject as _WReject

    def reject(why):
        sys.stderr.write("REJECT" + TAB + "retest-settle" + TAB + why + chr(10))
        return 1

    fd, ts = args["id"], args["timestamp"]
    _ts_check(ts)
    s = core.Session(goal_dir)
    frow = latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"]).get((fd,))
    if frow is None:
        return reject("id 引用闭合失败（findings 无此行）: " + fd)
    verdicts = _probe_verdicts(s, fd)
    state = _aggregate(verdicts)
    if state is None:
        return reject("无三态机判实证（挂接 EV 无 replay-probe 判定或 verdict=manual"
                      "——先 tanyin-replay replay --id=<EV> 实放）")
    # 已关护栏只拦仍真/已修复两臂；环境变更臂的关旧开新本就以 superseded 收口
    if state != "env-changed" and _cell(frow, "findings.tsv", "status") not in ("", "active"):
        return reject("复验对象已关（status=%s，superseded 不再复验）"
                      % _cell(frow, "findings.tsv", "status"))
    # 幂等门：末次 retest:FD 回写事件晚于末次 replay-probe 行=该实证已回写
    evs = _ev_set(s, fd)
    p_last = _last_idx(s, lambda e: bool(_PROBE_RE.search(e))
                       and _PROBE_RE.search(e).group(1) in evs)
    r_last = _last_idx(s, lambda e: bool(_RETEST_EV_RE.match(e)) and _RETEST_EV_RE.match(e).group(1) == fd)
    if r_last > p_last:
        return reject("该复验实证已回写（幂等）——补新 replay-probe 后再 settle")
    # ---- 三态分发（复用既有单源，零新桶零新证据规则）----
    if state in ("still-true", "fixed"):
        rs_state = "VERIFIED" if state == "still-true" else "REPAIRED"
        rc = check_cmds._set_replay_state_locked(
            goal_dir, {"id": fd, "state": rs_state, "timestamp": ts,
                       "note": "retest-" + state})
        if rc != 0:
            return 1   # 上游已落 REJECT 单行（证据门 fail-closed 透传）
        ev = ("retest:%s:still-true last_verified=%s" % (fd, ts) if state == "still-true"
              else "retest:%s:fixed repair-candidate" % fd)
        s2 = core.Session(goal_dir)
        check_cmds._append_timeline(s2, goal_dir, ev, ts)
    else:   # env-changed：关旧开新沿既有 supersedes 链（add-finding --supersede 已铸）
        new_fd = args.get("new-finding", "")
        if not new_fd:
            return reject("环境变更回写须 --new-finding=<新FD>（先 add-finding"
                          " --supersede=%s 同 dedup_key 关旧开新）" % fd)
        nrow = latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"]).get((new_fd,))
        if nrow is None:
            return reject("new-finding 引用闭合失败: " + new_fd)
        if _cell(nrow, "findings.tsv", "dedup_key") != _cell(frow, "findings.tsv", "dedup_key"):
            return reject("新旧 dedup_key 不同键——supersede 链须同键关旧开新")
        if _cell(frow, "findings.tsv", "status") != "superseded" or not any(
                _cell(r, "edges.tsv", "kind") == "supersedes"
                and _cell(r, "edges.tsv", "source_id") == fd
                and _cell(r, "edges.tsv", "target_id") == new_fd
                for r in s.rows("edges.tsv")):
            return reject("supersedes 链未铸（先 add-finding --supersede=%s 关旧开新）" % fd)
        check_cmds._append_timeline(core.Session(goal_dir), goal_dir,
                                    "retest:%s:env-changed superseded-by=%s" % (fd, new_fd), ts)
    # ---- 收口 [retest:FD] 标记卡（沿状态机合法箭头至终态）----
    ctx = _WCtx(goal_dir)
    reason = "retest-settled:" + state
    closed, blocked_cards = [], []
    for iid in {r[0] for r in ctx.rows("intents.tsv")
                if (_RETEST_MARK_RE.search(ctx.val("intents.tsv", r, "detail") or "")
                    and _RETEST_MARK_RE.search(ctx.val("intents.tsv", r, "detail")).group(1) == fd)}:
        st = ctx.val("intents.tsv", ctx.latest("intents.tsv", iid), "status")
        walk = {"active": ["done"], "candidate": ["rejected"], "pending": ["active", "done"],
                "deferred": ["pending", "active", "done"]}.get(st)
        if walk is None:
            if st not in ("done", "rejected"):
                blocked_cards.append(iid)   # blocked 复活须审批→留人工
            continue
        try:
            for j, nxt in enumerate(walk):
                a = {"id": iid, "status": nxt, "timestamp": ts}
                if nxt in ("rejected", "deferred") or j == len(walk) - 1:
                    a["reason"] = reason
                _intent_status_body(ctx, a, "set-intent-status")
            closed.append(iid)
        except _WReject:
            blocked_cards.append(iid)
    print("OK%sretest-settle%s%s%sstate=%s" % (TAB, TAB, fd, TAB, state)
          + ("" if not closed else "%scard-closed=%s" % (TAB, ",".join(sorted(closed))))
          + ("" if not blocked_cards else "%scard-manual=%s（blocked 复活须审批）"
             % (TAB, ",".join(sorted(blocked_cards)))))
    return 0


def h_retest_settle(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"id", "timestamp", "new-finding"} \
            or not args.get("id") or not args.get("timestamp"):
        raise UsageError("retest-settle --id=<FD-id> --timestamp=ISO8601"
                         " [--new-finding=FD-id]（环境变更臂须指认 supersedes 新行）")
    # set-replay-state 同型锁纪律：用法校验先行于锁，锁包读账→回写→收口全程
    from .filelock import goal_lock
    with goal_lock(goal_dir):
        return _settle_locked(goal_dir, args)


HANDLERS = {name: usage_guard(fn) for name, fn in {
    "retest-pending": h_retest_pending,
    "retest-scan": h_retest_scan,
    "retest-settle": h_retest_settle,
}.items()}
