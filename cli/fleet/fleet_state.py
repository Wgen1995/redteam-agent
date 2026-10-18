# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）·件②：仗注册表 fleet_state——TSV 单源+追加审计。

来源：docs/design/2026-10-20-build-master-plan.md R14（多任务治理舰）+
裁决书 §十八（supervisor 舰队化缺三件）+审计实证
docs/research/2026-10-20-assets-inventory-audit.md :75（十并发/排队原=纯设计）。
与 battle_registry 的分界：battle_registry=battles 根运行态仲裁（registry.json：
预算/端口/pid 收尸——进程点火执法面）；本模块=舰队治理注册表（fleet.tsv：
状态机/士兵分配/心跳超时/舰队旗——supervisor 的账面单源）。两册并存互不代写。

Ruling（tests/test_fleet_state.py 同源钉）：
- R-FLS-1 TSV 单源：fleet.tsv（11 列）+fleet-meta.tsv（舰队旗：halted 落此，
  不塞仗行）+fleet-audit.tsv（追加审计，只追加不改写）。写入=core.write_tsv
  原子写（tmp+fsync+rename——半写无第三态）。
- R-FLS-2 状态机：queued→{active,paused,failed}；active→{paused,done,failed}；
  paused→{active,queued,done,failed}（paused→queued=续仗遇帽排队）；
  done/failed 终态冻结。非法转移/未知状态/未注册仗=ValueError（fail-loud）；
  同态转移=幂等 no-op（changed=False 零审计）。
- R-FLS-3 幂等律：register 重复/soldiers 无变化/meta 同值=零写入零审计。
- R-FLS-4 心跳超时=纯读：active 行 heartbeat_at 缺失或龄>timeout→stale；
  非 active 不执法（停摆的仗不误判）。
- R-FLS-5 损坏 fleet.tsv=fail-closed ValueError（core.read_tsv 列数执法——
  battle_registry 同律零静默重置）；battle 名须 battle-N 形。
- R-FLS-6 钟全注入：写入口收 now_iso（ISO Z 形），stale 检测收 now_epoch——
  本模块零取钟（判决确定性可测）。priority 列=supervisor 的投影回填
  （set_priority 无审计——排序快照非治理动作）。
"""
import os
import re

from ledger import core
from ledger.enforce import parse_ts

FLEET_TSV = "fleet.tsv"
AUDIT_TSV = "fleet-audit.tsv"
META_TSV = "fleet-meta.tsv"
ACTOR = "fleet"

STATES = ("queued", "active", "paused", "done", "failed")
COLUMNS = ("battle", "goal_dir", "state", "soldiers", "priority",
           "budget_usd", "budget_cap_usd", "deadline", "heartbeat_at",
           "queued_at", "updated_at")
AUDIT_COLUMNS = ("ts", "actor", "action", "battle", "detail")
META_COLUMNS = ("key", "value", "updated_at")

_BATTLE = re.compile(r"^battle-(\d+)$")

_TRANSITIONS = {
    "queued": frozenset(("active", "paused", "failed")),
    "active": frozenset(("paused", "done", "failed")),
    "paused": frozenset(("active", "queued", "done", "failed")),
    "done": frozenset(),
    "failed": frozenset(),
}


def battle_key(name):
    """battle-N 自然序键（battle-2<battle-10，字典序误排防）。"""
    m = _BATTLE.match(name or "")
    return (int(m.group(1)) if m else 1 << 30, name or "")


def _read_dicts(root, name, columns):
    """TSV→dict 行；缺件=空；损坏/列数错=ValueError（fail-closed，R-FLS-5）。"""
    path = os.path.join(root, name)
    if not os.path.isfile(path):
        return []
    return [dict(zip(columns, r)) for r in core.read_tsv(path, len(columns))]


def _write_dicts(root, name, columns, rows):
    os.makedirs(root, exist_ok=True)
    core.write_tsv(os.path.join(root, name),
                   [[r[c] for c in columns] for r in rows])


def _audit(root, ts, action, battle, detail):
    """追加审计行（只追加；esc 单源=core.esc——列安全律）。"""
    os.makedirs(root, exist_ok=True)
    line = chr(9).join(core.esc(x) for x in (ts, ACTOR, action, battle, detail))
    with open(os.path.join(root, AUDIT_TSV), "a", encoding="utf-8",
              newline="\n") as f:
        f.write(line + chr(10))


def audit_rows(root):
    """审计全量（读侧=dict 行）。"""
    return _read_dicts(root, AUDIT_TSV, AUDIT_COLUMNS)


def register(root, battle, goal_dir, *, soldiers=0, budget_usd="",
             budget_cap_usd="", deadline="", now_iso=""):
    """注册新仗（初始 queued）。幂等：在册=already-registered 零写入零审计。"""
    if not _BATTLE.match(battle or ""):
        raise ValueError("battle 须 battle-N 形: %r" % (battle,))
    n = int(soldiers)
    if n < 0:
        raise ValueError("soldiers 须非负整数: %r" % (soldiers,))
    rows = _read_dicts(root, FLEET_TSV, COLUMNS)
    for r in rows:
        if r["battle"] == battle:
            return {"battle": battle, "registered": False,
                    "reason": "already-registered", "row": r}
    new = dict((c, "") for c in COLUMNS)
    new.update({"battle": battle, "goal_dir": str(goal_dir),
                "state": "queued", "soldiers": str(n),
                "budget_usd": str(budget_usd),
                "budget_cap_usd": str(budget_cap_usd),
                "deadline": str(deadline),
                "queued_at": now_iso, "updated_at": now_iso})
    rows.append(new)
    rows.sort(key=lambda r: battle_key(r["battle"]))
    _write_dicts(root, FLEET_TSV, COLUMNS, rows)
    _audit(root, now_iso, "register", battle,
           "state=queued soldiers=%d goal_dir=%s" % (n, goal_dir))
    return {"battle": battle, "registered": True, "row": new}


def row_of(root, battle):
    """单仗行；未注册=None。"""
    for r in _read_dicts(root, FLEET_TSV, COLUMNS):
        if r["battle"] == battle:
            return r
    return None


def rows(root):
    """全部仗行（自然序）。损坏册=ValueError（fail-closed）。"""
    out = _read_dicts(root, FLEET_TSV, COLUMNS)
    out.sort(key=lambda r: battle_key(r["battle"]))
    return out


def transition(root, battle, to_state, *, now_iso, reason=""):
    """状态机转移（R-FLS-2）：同态=幂等 no-op；非法/未知=ValueError。"""
    if to_state not in STATES:
        raise ValueError("未知状态 %r（合法集=%s）" % (to_state, list(STATES)))
    rows_ = _read_dicts(root, FLEET_TSV, COLUMNS)
    row = None
    for r in rows_:
        if r["battle"] == battle:
            row = r
            break
    if row is None:
        raise ValueError("未注册的仗: %r" % (battle,))
    cur = row["state"]
    if cur == to_state:
        return {"battle": battle, "changed": False, "from": cur, "to": to_state}
    if to_state not in _TRANSITIONS[cur]:
        raise ValueError("非法转移 %s→%s（%s 态可达集=%s）"
                         % (cur, to_state, cur,
                            sorted(_TRANSITIONS[cur])))
    row["state"] = to_state
    row["updated_at"] = now_iso
    _write_dicts(root, FLEET_TSV, COLUMNS, rows_)
    _audit(root, now_iso, "transition", battle,
           "%s→%s reason=%s" % (cur, to_state, reason))
    return {"battle": battle, "changed": True, "from": cur, "to": to_state}


def set_soldiers(root, battle, soldiers, *, now_iso):
    """士兵分配回写；无变化=零审计（幂等）。"""
    n = int(soldiers)
    if n < 0:
        raise ValueError("soldiers 须非负整数: %r" % (soldiers,))
    rows_ = _read_dicts(root, FLEET_TSV, COLUMNS)
    row = _find(rows_, battle)
    if row["soldiers"] == str(n):
        return {"battle": battle, "soldiers": n, "changed": False}
    row["soldiers"] = str(n)
    row["updated_at"] = now_iso
    _write_dicts(root, FLEET_TSV, COLUMNS, rows_)
    _audit(root, now_iso, "set-soldiers", battle, "soldiers=%d" % n)
    return {"battle": battle, "soldiers": n, "changed": True}


def set_priority(root, battle, priority, *, now_iso):
    """priority 投影回填（排序快照，无审计——R-FLS-6）。"""
    rows_ = _read_dicts(root, FLEET_TSV, COLUMNS)
    row = _find(rows_, battle)
    row["priority"] = str(priority)
    row["updated_at"] = now_iso
    _write_dicts(root, FLEET_TSV, COLUMNS, rows_)


def heartbeat(root, battle, *, now_iso):
    """心跳行回写（事实更新，无审计——心跳频次不入审计流）。"""
    rows_ = _read_dicts(root, FLEET_TSV, COLUMNS)
    row = _find(rows_, battle)
    row["heartbeat_at"] = now_iso
    row["updated_at"] = now_iso
    _write_dicts(root, FLEET_TSV, COLUMNS, rows_)
    return {"battle": battle, "heartbeat_at": now_iso}


def stale_battles(root, now_epoch, timeout_s):
    """心跳超时检测（R-FLS-4 纯读）：active 且心跳缺失/龄>窗 →[battle]。

    心跳缺失的 active 行回退 updated_at（开打宽限窗——刚升格还没来得及跳的仗
    不误杀）；两级都缺=stale。
    """
    out = []
    for r in _read_dicts(root, FLEET_TSV, COLUMNS):
        if r["state"] != "active":
            continue
        hb = r["heartbeat_at"] or r["updated_at"]
        if not hb:
            out.append(r["battle"])
            continue
        try:
            age = now_epoch - parse_ts(hb)
        except (ValueError, TypeError):
            age = None
        if age is None or age > timeout_s:
            out.append(r["battle"])
    return sorted(out, key=battle_key)


def set_meta(root, key, value, *, now_iso, reason=""):
    """舰队级旗 upsert（halted 等）；同值=幂等零审计（R-FLS-3）。"""
    rows_ = _read_dicts(root, META_TSV, META_COLUMNS)
    value = str(value)
    for r in rows_:
        if r["key"] == key:
            if r["value"] == value:
                return {"key": key, "value": value, "changed": False}
            r["value"] = value
            r["updated_at"] = now_iso
            _write_dicts(root, META_TSV, META_COLUMNS, rows_)
            _audit(root, now_iso, "set-meta", "-", "%s=%s reason=%s"
                   % (key, value, reason))
            return {"key": key, "value": value, "changed": True}
    rows_.append({"key": key, "value": value, "updated_at": now_iso})
    _write_dicts(root, META_TSV, META_COLUMNS, rows_)
    _audit(root, now_iso, "set-meta", "-", "%s=%s reason=%s" % (key, value,
                                                                reason))
    return {"key": key, "value": value, "changed": True}


def meta(root):
    """舰队旗 {key: value}。"""
    return {r["key"]: r["value"] for r in _read_dicts(root, META_TSV,
                                                      META_COLUMNS)}


def snapshot(root):
    """盘点视图：battles（自然序）+meta+totals（仪表盘/查仗数据面）。"""
    battles = rows(root)
    by_state = dict((s, 0) for s in STATES)
    active_soldiers = 0
    for r in battles:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1
        if r["state"] == "active":
            active_soldiers += _int0(r["soldiers"])
    return {"battles": battles, "meta": meta(root),
            "totals": {"active_soldiers": active_soldiers,
                       "by_state": by_state}}


def _find(rows_, battle):
    for r in rows_:
        if r["battle"] == battle:
            return r
    raise ValueError("未注册的仗: %r" % (battle,))


def _int0(s):
    try:
        return int(str(s).strip() or 0)
    except (TypeError, ValueError):
        return 0
