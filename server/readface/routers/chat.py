# -*- coding: utf-8 -*-
"""指挥流读面(P0 T5)——GET /api/chat/stream + GET /api/chat/warboard。

读法自释(零假数,纯读零 side effect;快照见 tests/readface/test_chat_stream.py):
- battles 根发现与 routers/overview.py 同法,复用勿抄第二份: TANYIN_HOME
  (缺省 ~/.tanyin)/battles=ledger.session_view.default_battles_dir 单源;
  仗枚举+当代 goal(battle-N/G-* 末代)=引擎 webui.api_v2_tasks.tasks_view
  行 battle/goal 字段。与 overview 的差别只有选择策略: 指挥台时间线收
  全部仗(不分执行态),overview 只数执行中——发现原语同一份。
- stream 合并: 每仗当代 goal 全量调 ledger_reader.timeline_tail(单源
  读,与 tasks_view 同量级),按 (ts,key) 确定全序(账本文件序偶有时钟
  倒挂,时间线视图以 ts 为准)后开窗。注: 计划「每仗取 limit 再归并」
  简化法在倒挂处会产生重复(G-r18 实测),故取全量+确定全序,翻页才
  无重无漏。before_key=base64(JSON 映射 {仗: 该仗已示最旧 key}): 各仗
  在各自全序上取更早 limit 行再按同一全序归并截断;未出战之仗位置跨页
  携带(丢了会从尾重取而重复);首次入图的仗无条目=从尾取(行未示过,
  仍是候选);页短于 limit=链尽,next_cursor=None。
- 徽标色 badge=hsl(H,70%,60%),H=sha256(battle 目录名)前 8 hex mod 360
  ——从目录名派生的稳定色相,同仗恒同色,stream/warboard 同源。
- warboard: soldiers_now/findings_list(各仗取前 5)/approvals_pending
  合并,皆注 battle+badge;无数据=空列表,不造假。
- findings(T9): ledger_reader.findings_list 各仗全量合并,行
  {id,title,severity,where,verified,replay_state,evidence,battle,badge,
  ts}——severity/verified/replay_state/title/where=T2 投影单源透传
  (severity=引擎 confidence 词表 C1/C2/C3/➖🛑 原样,不翻译不造假);
  evidence=证据袋引用(findings.tsv evidence_ids+control_evidence_ids,
  latest_by 事件溯源同律;无引用=空列表);battle 参数可空=全仗,
  未知仗/空根零行不造假;全局 ts 新→旧(同 ts 以 id 定序,缺 ts 殿后)。
- 坏游标(非 base64/非映射 JSON/悬空 key)→400 {"error":...}(auth 同款
  错误面);limit 走 FastAPI 校验(ge=1 le=200,坏值 422)。
"""
import base64
import binascii
import hashlib
import json
import os
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

# 导入序: ledger_reader 导入即把仓根 cli/ 前上 sys.path,webui 随后可导。
from .. import ledger_reader
from ledger.session_view import default_battles_dir
from webui import api_v2_tasks

router = APIRouter(prefix="/api/chat", tags=["chat"])

_MAX_LIMIT = 200            # 单页上限(防滥用;缺省 50 同 timeline_tail)
_FULL_WINDOW = 10 ** 6      # 每仗全量读窗口(P0 仗级账本量级,同 tasks_view)
_BADGE_SAT = 70             # 徽标色饱和度(GL-DS 暗底上的色相点)
_BADGE_LIGHT = 60


def _badge(battle):
    """徽标色: battle 目录名 sha256 前 8 hex → 色相(稳定派生)。"""
    hue = int(hashlib.sha256(battle.encode("utf-8")).hexdigest()[:8], 16) % 360
    return "hsl(%d, %d%%, %d%%)" % (hue, _BADGE_SAT, _BADGE_LIGHT)


def _battle_goals(battles_dir=None):
    """全部仗 → [(battle, 当代 goal 目录)](根发现=overview 同法单源复用)。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    out = []
    for b in api_v2_tasks.tasks_view(battles_dir=root)["battles"]:
        if not b["goal"]:
            continue                      # 无代目录的仗无时间线,跳过
        out.append((b["battle"], os.path.join(root, b["battle"], b["goal"])))
    return out


def _decode_cursor(raw):
    """base64(JSON {仗: key}) → 映射;None=尾取;坏形返回 None(面=400)。"""
    if raw is None:
        return {}
    try:
        data = base64.b64decode(raw.encode("ascii"), validate=True)
        mapping = json.loads(data.decode("utf-8"))
    except (ValueError, TypeError, UnicodeError, binascii.Error):
        return None
    if not isinstance(mapping, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in mapping.items()):
        return None
    return mapping


def stream_doc(battles_dir=None, before_key=None, limit=50):
    """跨仗合并时间线投影 → {rows:[{key,ts,kind,detail,battle,badge}],
    next_cursor};坏/悬空游标 → 400 JSONResponse(auth 同款错误面)。"""
    cursors = _decode_cursor(before_key)
    if cursors is None:
        return JSONResponse(status_code=400, content={
            "error": "游标不合法:须为服务端签发的 base64 仗→key 映射"})
    merged = []
    for battle, goal_dir in _battle_goals(battles_dir):
        rows = ledger_reader.timeline_tail(goal_dir, limit=_FULL_WINDOW)
        # 确定全序: (ts,key) 双倒——账本文件序偶有时钟倒挂(G-r18 夹具实存
        # 4 处),时间线视图以 ts 为准;同 ts 以 key 定序。游标按此全序开窗。
        rows.sort(key=lambda r: (r["ts"], r["key"]), reverse=True)
        if battle in cursors:
            keys = [r["key"] for r in rows]
            want = cursors[battle]
            if want not in keys:
                return JSONResponse(status_code=400, content={
                    "error": "游标失效(该仗链上找不到 key,可能已换代):%s"
                             % want})
            rows = rows[keys.index(want) + 1:]
        for r in rows[:limit]:
            merged.append((r["ts"], r["key"], battle, r))
    merged.sort(key=lambda t: (t[0], t[1]), reverse=True)
    page = merged[:limit]
    next_cursor = None
    if len(page) == limit:
        last = dict(cursors)    # 未出战之仗沿用入参位置(否则从尾重取→重复)
        for _ts, key, battle, _r in page:
            last[battle] = key  # 出战之仗: 全序页内该仗最旧行
        next_cursor = base64.b64encode(
            json.dumps(last, sort_keys=True).encode("utf-8")).decode("ascii")
    return {
        "rows": [{"key": key, "ts": ts, "kind": r["kind"],
                  "detail": r["detail"], "battle": battle,
                  "badge": _badge(battle)}
                 for ts, key, battle, r in page],
        "next_cursor": next_cursor,
    }


@router.get("/stream")
def chat_stream(before_key: Optional[str] = None,
                limit: int = Query(50, ge=1, le=_MAX_LIMIT)):
    """指挥台中央流尾窗: 跨仗合并时间线(1s 尾轮询客户端,见 web chat.tsx)。"""
    return stream_doc(before_key=before_key, limit=limit)


@router.get("/warboard")
def chat_warboard():
    """右侧战况板三格: 在跑士兵/最新发现(各仗前 5)/待审批,皆注 battle。"""
    soldiers, findings, approvals = [], [], []
    for battle, goal_dir in _battle_goals(None):
        color = _badge(battle)
        for s in ledger_reader.soldiers_now(goal_dir):
            soldiers.append(dict(s, battle=battle, badge=color))
        for f in ledger_reader.findings_list(goal_dir)[:5]:
            findings.append(dict(f, battle=battle, badge=color))
        for a in ledger_reader.approvals_pending(goal_dir):
            approvals.append(dict(a, battle=battle, badge=color))
    return {"soldiers": soldiers,
            "findings_latest": findings,
            "approvals": approvals}


def _evidence_refs(goal_dir):
    """发现号 → 证据袋引用链(EV 号列表)。

    findings.tsv evidence_ids+control_evidence_ids 引用列(latest_by
    事件溯源取最新行,与 findings_list 同律;Session/latest_by/TABLES
    皆 ledger_reader 单源转引,列义零第二份)。无引用=空列表。
    """
    s = ledger_reader.ledger_core.Session(goal_dir)
    f = ledger_reader.TABLES["findings.tsv"]
    i_evid = f.index("evidence_ids")
    i_ctrl = f.index("control_evidence_ids")
    latest = ledger_reader.ledger_query.latest_by(
        s.rows("findings.tsv"), "findings.tsv", ["id"])
    out = {}
    for key in latest:
        r = latest[key]
        out[r[0]] = [x for x in (r[i_evid] + ";" + r[i_ctrl]).split(";") if x]
    return out


def findings_doc(battles_dir=None, battle=None):
    """发现清单跨仗合并 → [{id,title,severity,where,verified,
    replay_state,evidence,battle,badge,ts}]。

    - battle 缺省/空串=全仗;未知仗/空根零行,不造假;
    - severity/verified/replay_state/title/where/ts=T2 findings_list
      单源透传(severity=引擎 confidence 词表原样,前端词表才译色);
    - evidence=证据袋引用(有则显,无则空列表);
    - 全局 ts 新→旧,同 ts 以 id 定序;缺 created 的行 ts=None 殿后
      (不造假不弃行)。
    """
    want = battle or None
    out = []
    for b, goal_dir in _battle_goals(battles_dir):
        if want is not None and b != want:
            continue
        color = _badge(b)
        ev = _evidence_refs(goal_dir)
        for fd in ledger_reader.findings_list(goal_dir):
            out.append({
                "id": fd["id"],
                "title": fd["title"],
                "severity": fd["sev"],
                "where": fd["where"],
                "verified": fd["verified"],
                "replay_state": fd["replay_state"],
                "evidence": ev.get(fd["id"], []),
                "ts": fd["ts"],
                "battle": b,
                "badge": color,
            })
    out.sort(key=lambda r: (r["ts"] or "", r["id"]), reverse=True)
    return out


@router.get("/findings")
def chat_findings(battle: Optional[str] = Query(None)):
    """T9 发现时刻配对面: 各仗发现清单(battle 可空=全仗),纯读。"""
    return findings_doc(battle=battle)
