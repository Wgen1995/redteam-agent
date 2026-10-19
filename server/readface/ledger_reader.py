# -*- coding: utf-8 -*-
"""GraphLed 账本读投影层(P0 T2)——纯读,零 side effect。

铁律对齐(docs/superpowers/plans/2026-10-20-p0-command-deck.md):
- 引擎零改: 本文件不写任何账本文件;只 import cli/ 侧既有读函数。
- 进程内读: 导入即把仓根 cli/ 目录前上 sys.path(PYTHONPATH=cli 同效),
  复用 ledger.core.Session / ledger.timeline.read_rows / ledger.query_cmds /
  ledger.preauth / warrior.corps 读面——列义/词表/路由零第二份。
- 宁缺毋假: 夹具缺的列/事件,投影字段返回 None,不造数。

四个投影(数据源: tests/fixtures/G-r18 夹具账本):
1. timeline_tail(goal_dir, before_key=None, limit=50)
   → [{key,ts,kind,detail}...] 新→旧;key=行链哈希(唯一);before_key=
   上一页最旧 key,返回更早的 limit 行(游标反向分页)。
2. findings_list(goal_dir, status=None)
   → [{id,sev,where,title,verified,replay_state,ts}...] 事件溯源取最新行;
   verified=机器复放验真(终态 VERIFIED/REPAIRED);replay_state 人话三态:
   已验/待验(灰卡,复放未过)/复验中(replay-probe 在途未落终态)。
3. soldiers_now(goal_dir)
   → [{corps,intent,status,heartbeat_ts,tokens}...] 意图行=战士行;
   corps=兵种位[corps:X]直读>kind 缺省路由;heartbeat_ts=timeline
   warrior-heartbeat 行最新值(缺=None);tokens=budget_share 首段。
4. approvals_pending(goal_dir)
   → [{id,event,risk_line,timeout_policy,ts}...] 待审=引擎
   cleanup-checklist 同源 pending(revert_cmd 非空且未 revert/未豁免);
   id=sha256(revert_cmd)(approve 通道 --command-hash 同键);
   risk_line=preauth 确定性词表判读(判不了=None);timeout_policy=
   approval.json timeout_min(缺省 30 分钟)超时保守。
"""
import hashlib
import os
import re
import sys

# 仓根 cli/ 前上 sys.path(server/readface/ → 上三级=仓根;warrior/__init__
# 与 report_agg 同款先例)。已在不重插,零污染调用方路径序。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_CLI_DIR = os.path.join(_REPO_ROOT, "cli")
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

from ledger import core as ledger_core            # noqa: E402
from ledger import preauth as ledger_preauth       # noqa: E402
from ledger import query_cmds as ledger_query      # noqa: E402
from ledger import timeline as ledger_timeline     # noqa: E402
from ledger.check_cmds import REPLAY_EVENT         # noqa: E402  重放事件形态单源
from ledger.schemas import TABLES                  # noqa: E402  列义单源
from warrior import corps as warrior_corps         # noqa: E402  兵种路由单源

_TL = TABLES["timeline.tsv"]
_TS_I = _TL.index("timestamp")
_EV_I = _TL.index("event")
_RV_I = _TL.index("revert_cmd")
_HASH_I = _TL.index("hash")

# replay-probe 在途形态(check_cmds 内联同式——引擎未导出,此处为投影自用)
_PROBE_RE = re.compile(r"^replay-probe (\S+) verdict=(\S+)")
# warrior-heartbeat 行 intent= 抽取(warrior/heartbeat.py beat() 落行同形)
_HB_INTENT_RE = re.compile(r"\bintent=(\S+)")

# 机器复放验真终态(通过档)——check_cmds REPLAY_STATES 同源枚举
_VERDICT_PASS = ("VERIFIED", "REPAIRED")


def _nz(value):
    """空串→None(宁缺毋假:夹具缺列不造数)。"""
    s = str(value).strip()
    return s if s else None


def _event_kind(event):
    """事件头词: 首空白 token 再截首个冒号前段。

    add-goal G-..→add-goal;replay:EV-x:VERIFIED→replay;gate-exit:P4→
    gate-exit;request: path via=replay→request。
    """
    head = str(event).split(" ", 1)[0]
    return head.split(":", 1)[0] or head


# ---------------------------------------------------------------- ① timeline --

def timeline_tail(goal_dir, before_key=None, limit=50):
    """timeline 尾窗反向分页(新→旧),key=行链哈希游标。

    - 缺省末 50 行倒序;before_key=链上某行哈希,返回其前(更旧)limit 行;
    - 游标=上一页末项(页内最旧)key,走到链底返回空页;
    - before_key 不在链上=ValueError(fail-loud,引擎同律)。
    读面=ledger.timeline.read_rows(epoch 一致性读,撕裂快照拒绝返回)。
    """
    try:
        n = int(limit)
    except (TypeError, ValueError):
        raise ValueError("limit 须为正整数: %r" % (limit,))
    if n <= 0:
        raise ValueError("limit 须为正整数: %r" % (limit,))
    rows = ledger_timeline.read_rows(goal_dir)
    if before_key is None:
        lo = max(0, len(rows) - n)
        window = rows[lo:]
    else:
        keys = [r[_HASH_I] for r in rows]
        if before_key not in keys:
            raise ValueError("before_key 不在 timeline 链上: %r" % (before_key,))
        idx = keys.index(before_key)
        lo = max(0, idx - n)
        window = rows[lo:idx]
    return [{"key": r[_HASH_I], "ts": r[_TS_I],
             "kind": _event_kind(r[_EV_I]), "detail": r[_EV_I]}
            for r in reversed(window)]


# ---------------------------------------------------------------- ② findings --

def _replay_tracks(s):
    """timeline 单遍扫描: 重放终态(按序末值)+probe 在途位置。

    终态语义=report_agg._replay_states 同源(replay:<ref>:<state> 按序
    末值);在途=同 ref 有更晚(或尚无终态的)replay-probe 行。
    """
    verd, vpos, ppos = {}, {}, {}
    for i, r in enumerate(s.rows("timeline.tsv")):
        ev = r[_EV_I]
        m = REPLAY_EVENT.match(ev)
        if m:
            verd[m.group(1)] = m.group(2)
            vpos[m.group(1)] = i
            continue
        m2 = _PROBE_RE.match(ev)
        if m2:
            ppos[m2.group(1)] = i
    return verd, vpos, ppos


def findings_list(goal_dir, status=None):
    """发现清单投影(事件溯源取最新行,按 id 排序)。

    - status=None 全量;否则按最新行 status 列过滤(active/superseded...)。
    - refs 链=[FD id]+evidence_ids+control_evidence_ids(引擎 rids 同序),
      终态取链上首个有终态的 ref(report_agg 同源优先序);
    - verified=终态通过(VERIFIED/REPAIRED);replay_state 三态:
      复验中(任一 ref probe 在途)>已验(终态通过)>待验(灰卡:无终态或
      REJECTED 复放未过)。
    """
    s = ledger_core.Session(goal_dir)
    verd, vpos, ppos = _replay_tracks(s)
    f = TABLES["findings.tsv"]
    i_status = f.index("status")
    i_evid = f.index("evidence_ids")
    i_ctrl = f.index("control_evidence_ids")
    i_sev = f.index("confidence")
    i_where = f.index("affected_asset_id")
    i_title = f.index("title")
    i_created = f.index("created")
    latest = ledger_query.latest_by(s.rows("findings.tsv"), "findings.tsv", ["id"])
    out = []
    for key in sorted(latest):
        r = latest[key]
        if status is not None and r[i_status] != status:
            continue
        refs = [r[0]] + [x for x in (r[i_evid] + ";" + r[i_ctrl]).split(";") if x]
        verdict = next((verd[x] for x in refs if x in verd), None)
        inflight = any(x in ppos and (x not in vpos or ppos[x] > vpos[x])
                       for x in refs)
        verified = verdict in _VERDICT_PASS
        if inflight:
            state = "复验中"
        elif verified:
            state = "已验"
        else:
            state = "待验"
        out.append({
            "id": r[0],
            "sev": r[i_sev],
            "where": _nz(r[i_where]),
            "title": r[i_title],
            "verified": verified,
            "replay_state": state,
            "ts": _nz(r[i_created]),
        })
    return out


# ---------------------------------------------------------------- ③ soldiers --

def _tokens_of(share):
    """budget_share 首段(tokens;requests;hours)→数值;缺/坏=None。

    解析=ledger_query.parse_num 单源(2M→2000000);整数收 int。
    """
    first = str(share or "").split(";", 1)[0].strip()
    if not first:
        return None
    try:
        n = ledger_query.parse_num(first)
    except (ValueError, TypeError):
        return None
    return int(n) if float(n).is_integer() else n


def soldiers_now(goal_dir):
    """战士在编投影: 意图行=战士行,按意图 id 稳定排序。

    - corps: 兵种位 [corps:X](detail 虚拟列)直读优先,须在五兵种卡面
      (warrior_corps.SKILL_CORPS)内;否则 kind 缺省路由
      (DEFAULT_KIND_ROUTES,commander 卡纪律 2 单源);authz-diff 无缺省
      兵种=None(宁缺毋假)。
    - heartbeat_ts: timeline warrior-heartbeat 行 intent=<id> 最新值
      (文件序末值);夹具无心跳行=None 不造假。
    - tokens: budget_share 首段;status: 意图状态原样透传。
    """
    s = ledger_core.Session(goal_dir)
    hb = {}
    for r in s.rows("timeline.tsv"):
        ev = r[_EV_I]
        if ev.startswith("warrior-heartbeat"):
            m = _HB_INTENT_RE.search(ev)
            if m:
                hb[m.group(1)] = r[_TS_I]
    itbl = TABLES["intents.tsv"]
    i_detail, i_kind = itbl.index("detail"), itbl.index("kind")
    i_title, i_status = itbl.index("title"), itbl.index("status")
    i_share = itbl.index("budget_share")
    out = []
    latest = ledger_query.latest_intents(s)
    for key in sorted(latest):
        r = latest[key]
        mark = warrior_corps.marker_of(r[i_detail])
        corps = mark if mark in warrior_corps.SKILL_CORPS else None
        if corps is None:
            corps = warrior_corps.DEFAULT_KIND_ROUTES.get(r[i_kind])
        out.append({
            "corps": corps,
            "intent": r[i_title],
            "status": r[i_status],
            "heartbeat_ts": hb.get(r[0]),
            "tokens": _tokens_of(r[i_share]),
        })
    return out


# --------------------------------------------------------------- ④ approvals --

def _risk_line(event, revert_cmd):
    """风险一句: preauth 确定性词表单源判读(不上模型)。

    高危记号→必须人工审;只读动词→界内可预授权豁免;两者皆无=判不了,
    返回 None(宁缺毋假)。词表=ledger_preauth._READ_VERBS/_DANGER_MARKS
    引擎单源,本文件零第二份。
    """
    text = (str(event) + " " + str(revert_cmd)).lower()
    if any(m in text for m in ledger_preauth._DANGER_MARKS):
        return "含高危/不可逆动作记号——必须人工审"
    if any(v in text for v in ledger_preauth._READ_VERBS):
        return "只读探测动作——界内可走预授权豁免"
    return None


def approvals_pending(goal_dir):
    """待审清单投影: 引擎 cleanup-checklist 同源 pending 项。

    - 数据面=ledger_query._replay_status(preauth 同源引用先例):
      timeline revert_cmd 非空行,reverted(后续 revert:<原事件>行)/
      exempted(approvals 行 decision=exempted 且 note 含原事件)出队;
    - id=sha256(revert_cmd)=approve 通道 --command-hash 同键(写转发即用);
    - timeout_policy=preauth.load_timeout(approval.json timeout_min,
      缺省 30 分钟)超时保守跳过;顺序=timeline 文件序(挂起先后)。
    """
    s = ledger_core.Session(goal_dir)
    tmo = ledger_preauth.load_timeout(goal_dir)
    policy = "待审挂起超 %d 分钟→保守跳过(超时保守策略)" % tmo
    out = []
    for it in ledger_query._replay_status(s):
        if it["status"] != "pending":
            continue
        r = it["row"]
        revert = r[_RV_I]
        out.append({
            "id": hashlib.sha256(revert.encode("utf-8")).hexdigest(),
            "event": r[_EV_I],
            "risk_line": _risk_line(r[_EV_I], revert),
            "timeout_policy": policy,
            "ts": r[_TS_I],
        })
    return out
