# -*- coding: utf-8 -*-
"""任务列表+详情·会话签读面(P0 T11)——GET /api/tasks 三端点。

读法自释(零假数,纯读零 side effect;快照见 tests/readface/test_tasks.py):
- 仗枚举单源=引擎 webui.api_v2_tasks.tasks_view(与 overview/指挥流
  同源;overview 只数执行中,本面收全部仗不分态——已完跑/复测/草稿
  照列,「执行中/已完跑」口径即 tasks_view 界面七态标签,零第二份
  状态机);name/goal(当代 G-x)/objective=goals 行透传;
  running=标签==执行中(overview._RUNNING_LABEL 同词)。
- 计数如实: soldiers_n/findings_n=ledger_reader soldiers_now/
  findings_list 长度(意图行=战士行;不筛态不折算);latest_ts=当代
  goal timeline 全量最大 ts(账本文件序偶有时钟倒挂,以 ts 为准);
  无代 goal 的草稿仗零计数+None,不造假。
- 会话分组(详情): 该仗 timeline 按战士/意图归组,线索序(先匹配
  先赢,零猜):
    ① actor 列 warrior:X 前缀(战士自落行——工具调用/心跳原文);
    ② 事件 warrior=X(warrior-start/-heartbeat/-stop 生命周期行);
    ③ warrior-steer 行 target=X(插话留痕归目标战士的会话);
    ④ 事件 intent=INT-x(无战士线索时按意图归);
    ⑤ add-intent INT-x(立项行归该意图组);
    ⑥ 其余归 deck(战役本级: add-goal/add-scope/发现/重放等)。
  每组 {session_key,label,rows_n,first_ts,last_ts};label: 战士 X /
  意图 INT-x · 标题(intents latest 行,缺=只显号)/战役本级;组序
  last_ts 新→旧(同 ts 以 session_key 升序稳定)。
- 组流: GET /api/tasks/{id}/sessions/{key}——组内行形状同 T5 stream
  ({key,ts,kind,detail,battle,badge};badge=sha256 派生色相同源),
  组内 (ts,key) 新→旧;before_key=上一页末行 key(单链游标,无需
  T5 的跨仗 base64 映射);翻页无重无漏;未知仗/未知组 404,坏/跨组
  游标 400(auth 同款错误面),limit 走 FastAPI 校验(ge=1 le=200)。
"""
import os
import re
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

# 导入序: ledger_reader 导入即把仓根 cli/ 前上 sys.path,webui 随后可导;
# chat._badge/_battle_goals 与 overview._RUNNING_LABEL=徽标/执行中口径
# 单源复用,零第二份。
from .. import ledger_reader
from .chat import _badge
from .overview import _RUNNING_LABEL
from ledger.session_view import default_battles_dir
from webui import api_v2_tasks

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_MAX_LIMIT = 200            # 单页上限(防滥用;缺省 50 同 T5 stream)

# timeline 列位(TABLES 列义单源;timeline_tail 不带 actor 列,组归组
# 需战士位,故经 ledger_reader.ledger_timeline.read_rows 直读——
# epoch 一致性读同律,chat._evidence_refs 引用 Session/TABLES 同先例)。
_TL = ledger_reader.TABLES["timeline.tsv"]
_TS_I = _TL.index("timestamp")
_ACTOR_I = _TL.index("actor")
_EV_I = _TL.index("event")
_HASH_I = _TL.index("hash")

_WARRIOR_EVENT_RE = re.compile(r"\bwarrior=(\S+)")     # 生命周期行
_STEER_TARGET_RE = re.compile(r"\btarget=(\S+)")       # 插话行目标战士
_INTENT_EQ_RE = re.compile(r"\bintent=(INT-\S+)")      # 心带意图线索
_INTENT_TOKEN_RE = re.compile(r"(?:^|\s)(INT-[A-Za-z0-9-]+)")  # 立项行


def _session_of(actor, event):
    """(actor,事件原文) → session_key(先匹配先赢;无线索=deck)。"""
    if actor.startswith("warrior:"):
        wid = actor.split(":", 1)[1].strip()
        if wid:
            return "w:" + wid
    m = _WARRIOR_EVENT_RE.search(event)
    if m:
        return "w:" + m.group(1)
    if event.startswith("warrior-steer"):
        m = _STEER_TARGET_RE.search(event)
        if m:
            return "w:" + m.group(1)
    m = _INTENT_EQ_RE.search(event)
    if m:
        return "i:" + m.group(1)
    if event.startswith("add-intent"):
        m = _INTENT_TOKEN_RE.search(event)
        if m:
            return "i:" + m.group(1)
    return "deck"


def _tl_rows(goal_dir):
    """timeline 全量(文件序)→ [{key,ts,actor,kind,detail}](纯读)。"""
    if not os.path.isfile(os.path.join(goal_dir, "timeline.tsv")):
        return []                     # 无账本=空,不造假
    return [{"key": r[_HASH_I], "ts": r[_TS_I], "actor": r[_ACTOR_I],
             "kind": ledger_reader._event_kind(r[_EV_I]),
             "detail": r[_EV_I]}
            for r in ledger_reader.ledger_timeline.read_rows(goal_dir)]


def _intent_titles(goal_dir):
    """意图号 → 标题(intents latest_by 事件溯源,ledger_reader 单源)。"""
    s = ledger_reader.ledger_core.Session(goal_dir)
    i_title = ledger_reader.TABLES["intents.tsv"].index("title")
    latest = ledger_reader.ledger_query.latest_intents(s)
    return {r[0]: r[i_title] for r in latest.values()}


def _label_of(session_key, titles):
    """session_key → 人话标签(宁缺毋假: 意图缺标题只显号)。"""
    if session_key == "deck":
        return "战役本级"
    kind, _, ident = session_key.partition(":")
    if kind == "w":
        return "战士 " + ident
    title = titles.get(ident)
    return "意图 " + ident + ((" · " + title) if title else "")


def _battle_row(battles_root, battle):
    """仗名 → tasks_view 行|None(approvals._known_battle 同律: 未知 404)。"""
    for b in api_v2_tasks.tasks_view(battles_dir=battles_root)["battles"]:
        if b["battle"] == battle:
            return b
    return None


def _battle_doc(b, battles_root, with_sessions=False):
    """tasks_view 行 → 列表/详情字典(纯读,缺件如实为零/None)。"""
    battle = b["battle"]
    goal = b["goal"] or ""
    goal_dir = os.path.join(battles_root, battle, goal) if goal else None
    doc = {
        "id": battle,
        "name": b["name"],
        "status": b["state"]["label"],
        "status_detail": b["state"].get("detail", ""),
        "running": b["state"]["label"] == _RUNNING_LABEL,
        "badge": _badge(battle),
        "goal": goal,
        "soldiers_n": 0,
        "findings_n": 0,
        "latest_ts": None,
    }
    if goal_dir is None:
        if with_sessions:
            doc["objective"] = b["objective"]
            doc["sessions"] = []
        return doc
    doc["soldiers_n"] = len(ledger_reader.soldiers_now(goal_dir))
    doc["findings_n"] = len(ledger_reader.findings_list(goal_dir))
    rows = _tl_rows(goal_dir)
    if rows:
        doc["latest_ts"] = max(r["ts"] for r in rows)
    if with_sessions:
        doc["objective"] = b["objective"]
        groups = {}
        for r in rows:
            groups.setdefault(_session_of(r["actor"], r["detail"]), []).append(r)
        titles = _intent_titles(goal_dir)
        sessions = []
        for key, grows in groups.items():
            tss = [r["ts"] for r in grows]
            sessions.append({
                "session_key": key,
                "label": _label_of(key, titles),
                "rows_n": len(grows),
                "first_ts": min(tss),
                "last_ts": max(tss),
            })
        # 组序: last_ts 新→旧;两段稳定排序保同 ts 以 session_key 升序。
        sessions.sort(key=lambda s: s["session_key"])
        sessions.sort(key=lambda s: (s["last_ts"] or ""), reverse=True)
        doc["sessions"] = sessions
    return doc


def tasks_doc(battles_dir=None):
    """仗列表投影 → {battles:[…]}(根缺/空=空列表诚实态)。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    view = api_v2_tasks.tasks_view(battles_dir=root)
    return {"battles": [_battle_doc(b, root) for b in view["battles"]]}


def task_detail_doc(battle, battles_dir=None):
    """仗详情投影 → 字典|404(未知仗/无目录不造假)。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    b = _battle_row(root, battle)
    if b is None:
        return JSONResponse(status_code=404, content={
            "error": "battle 不存在: %r" % battle})
    return _battle_doc(b, root, with_sessions=True)


def session_stream_doc(battle, session_key, before_key=None, limit=50):
    """组内时刻流 → {rows:[T5 形状+badge],next_cursor}|404/400。"""
    root = default_battles_dir()
    b = _battle_row(root, battle)
    if b is None:
        return JSONResponse(status_code=404, content={
            "error": "battle 不存在: %r" % battle})
    if not b["goal"]:
        return JSONResponse(status_code=404, content={
            "error": "该仗无代 goal(无时间线): %r" % battle})
    goal_dir = os.path.join(root, battle, b["goal"])
    rows = [r for r in _tl_rows(goal_dir)
            if _session_of(r["actor"], r["detail"]) == session_key]
    if not rows:
        return JSONResponse(status_code=404, content={
            "error": "会话组不存在(该仗链上无此战士/意图线索): %r"
                     % session_key})
    rows.sort(key=lambda r: (r["ts"], r["key"]), reverse=True)
    if before_key is not None:
        keys = [r["key"] for r in rows]
        if before_key not in keys:
            return JSONResponse(status_code=400, content={
                "error": "游标失效(不在该会话组内,可能跨组或已换代): %s"
                         % before_key})
        rows = rows[keys.index(before_key) + 1:]
    page = rows[:limit]
    next_cursor = page[-1]["key"] if len(page) == limit else None
    badge = _badge(battle)
    return {
        "rows": [{"key": r["key"], "ts": r["ts"], "kind": r["kind"],
                  "detail": r["detail"], "battle": battle, "badge": badge}
                 for r in page],
        "next_cursor": next_cursor,
    }


@router.get("")
def tasks_list():
    """任务列表: battles 根枚举全部仗(含已完跑/复测/草稿),纯读。"""
    return tasks_doc()


@router.get("/{battle_id}")
def task_detail(battle_id: str):
    """任务详情: 列表字段+goals 简述+会话分组(战士/意图线索归组)。"""
    return task_detail_doc(battle_id)


@router.get("/{battle_id}/sessions/{session_key}")
def task_session_stream(battle_id: str, session_key: str,
                        before_key: Optional[str] = None,
                        limit: int = Query(50, ge=1, le=_MAX_LIMIT)):
    """会话签组内时刻流: T5 行形状+badge,key 游标反向分页(10s 尾轮询
    客户端,见 web task-detail.tsx)。"""
    return session_stream_doc(battle_id, session_key,
                              before_key=before_key, limit=limit)
