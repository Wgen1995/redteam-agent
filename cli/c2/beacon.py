# -*- coding: utf-8 -*-
"""beacon 管理——每 beacon=账本行，心跳超时=状态投影翻转。

行律（beacons.tsv）：register 行立 beacon（id/上线时刻/来源意图/凭据引用），
heartbeat 行续命（同 id 追加，不改历史）；投影=同 id 行族：
  first_seen   = 首行 ts（register 时刻，心跳不改）
  last_hb      = 最新行 ts（心跳推进）
  status       = 投影推导：online（lag<=T）/ stale（T<lag<=2T）/
                 offline（lag>2T）——心跳超时=状态翻转，账本零行改动。

执法（gate.py 族审批在 cli 层统一过门，本模块只管账本律）：
- register：intent_ref 引用闭合（intents.tsv 在册）；cred_ref 非空时
  须=creds.tsv 在册 id 或 {{vault:cred-N}} 占位符（凭据四条：真值只进 vault）。
- heartbeat：未登记 beacon 的心跳=拒收（fail-closed——匿名心跳不入账）。
"""
import re

from ..ledger import core as ledger_core
from ..ledger.schemas import TABLES
from .store import C2Error, C2Store
from .tables import HEARTBEAT_TIMEOUT

_VAULT_RE = re.compile(r"^\{\{vault:cred-\d+\}\}$")


def _session(goal_dir):
    return ledger_core.Session(goal_dir)


def register(goal_dir, ts, intent_ref, cred_ref="", host_tag="", note=""):
    """登记 beacon（register 行）；返回 (beacon_id, row)。

    引用闭合 fail-closed：intent_ref 不在 intents.tsv / cred_ref 非法
    形 = C2Error（怎么走：先 add-intent / 凭据引用用 CRED id 或 vault 占位符）。
    L3 族门：c2-beacon 预授权族须放行（gates-speed 预授权档——批一次放一族）。
    """
    from . import families
    families.require(goal_dir, "c2-beacon", ts)
    s = _session(goal_dir)
    int_ids = {r[0] for r in s.rows("intents.tsv")}
    if intent_ref not in int_ids:
        raise C2Error(
            "intent_ref 引用闭合失败: %s 不在 intents.tsv（怎么走: 先 add-intent 登记来源意图）" % intent_ref)
    if cred_ref:
        cred_ids = {r[0] for r in s.rows("creds.tsv")}
        if cred_ref not in cred_ids and not _VAULT_RE.match(cred_ref):
            raise C2Error(
                "cred_ref 非法: %r（怎么走: creds.tsv 在册 CRED id 或 {{vault:cred-N}} 占位符，"
                "凭据真值只进 vault）" % cred_ref)
    store = C2Store(goal_dir)
    bid = store.next_id("beacons.tsv", "BCN")
    row = store.append("beacons.tsv", {
        "id": bid, "kind": "register", "ts": ts, "intent_ref": intent_ref,
        "cred_ref": cred_ref, "host_tag": host_tag, "note": note})
    return bid, row


def heartbeat(goal_dir, beacon_id, ts):
    """beacon 心跳（同 id 追加行，投影取最新）；未登记=拒收。"""
    store = C2Store(goal_dir)
    fam = store.latest_by_key("beacons.tsv")
    if beacon_id not in fam:
        raise C2Error(
            "未知 beacon: %s（怎么走: 先 register 登记，匿名心跳不入账——fail-closed）" % beacon_id)
    latest = fam[beacon_id]
    ci = _cols_index()
    row = store.append("beacons.tsv", {
        "id": beacon_id, "kind": "heartbeat", "ts": ts,
        "intent_ref": latest[ci["intent_ref"]],
        "cred_ref": latest[ci["cred_ref"]],
        "host_tag": latest[ci["host_tag"]], "note": ""})
    return row


def _cols_index():
    from .tables import cols
    return {k: i for i, k in enumerate(cols("beacons.tsv"))}


def _parse_ts(ts):
    """ISO8601 Z 形 -> epoch 秒（账本 ts 字符串域=机械可投影）。"""
    import datetime
    return datetime.datetime.strptime(ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z").timestamp()


def projection(goal_dir, now_ts, timeout=HEARTBEAT_TIMEOUT):
    """beacon 状态投影（读面零写入）：[{id,first_seen,last_hb,status,...}]。

    状态翻转律：lag=now-last_hb；online<=T / stale<=2T / offline>2T。
    """
    store = C2Store(goal_dir)
    ci = _cols_index()
    now = _parse_ts(now_ts)
    out = []
    for bid in sorted(store.latest_by_key("beacons.tsv")):
        rows = [r for r in store.read("beacons.tsv") if r[0] == bid]
        first, last = rows[0], rows[-1]
        lag = now - _parse_ts(last[ci["ts"]])
        if lag <= timeout:
            status = "online"
        elif lag <= 2 * timeout:
            status = "stale"
        else:
            status = "offline"
        out.append({
            "id": bid, "first_seen": first[ci["ts"]], "last_hb": last[ci["ts"]],
            "intent_ref": last[ci["intent_ref"]], "cred_ref": last[ci["cred_ref"]],
            "host_tag": last[ci["host_tag"]], "status": status,
            "heartbeats": len(rows) - 1})
    return out


def beacon_exists(goal_dir, beacon_id):
    return beacon_id in C2Store(goal_dir).latest_by_key("beacons.tsv")
