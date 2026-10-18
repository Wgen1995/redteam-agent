# -*- coding: utf-8 -*-
"""api_v2_llm_status（T7·模型状态页）——多通道模型池只读面，路由
GET /api/v2/llm-status.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now——剩余秒按调用方注入的 now 计算，view 本体给定 now 输出确定；
route 适配层=time.time() 单点注入）；本页无写路径——POST_ROUTES 恒空。
挂载=ROUTES 单源表由 include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_llm_status.py（_V2MountHandler）：GET 过会话门。

数据单源（spec §P8-P18 模型状态页）：
  通道配置 = 任务目录 channels.json（战士 --channels 同形
             [{"name","model","base_url","api_key"}…]；密钥永不上屏——只出
             「是否已配」布尔，SEC 钥不落页面律；文件缺席=诚实空态说明：
             通道由智能体启动参数注入，不入账本）；
  各道健康/熔断态/冷却剩时 = goal 目录 llmpool_state.json（llmpool_wire.attach
             钉根路径，读面不迁移 env 改投）：hard=熔断（无自动恢复）、
             cooldown_end>now=冷却（剩余秒向上取整）、否则健康——判定式与
             llmpool._snap_of 同律（读侧零改动零落盘，不触发惰性恢复写）；
  故障转移事件 = timeline llmpool_wire 行（actor=llmpool，event=
             "llm_failover k=v…"——trip/recover 负载逐键解析，lane/cooldown_s
             的 None 字面还原为 None）；
  判定参数 = ledger.llmpool 常量 import 单源（软熔阈值/429 短档/服务端长档
             1/5/30min/±20% 抖动——不复制第二份）。
"""
import json
import math
import os
import sys
import time

_CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CLI_DIR not in sys.path:                     # server/测试同款兜底：cli/ 上 path
    sys.path.insert(0, _CLI_DIR)

from ledger import core                          # noqa: E402
from ledger import llmpool as _pool              # noqa: E402  (判定参数单源)
from ledger.session_view import list_battles     # noqa: E402

ROUTE_LLM = "/api/v2/llm-status.json"
ROUTES = {ROUTE_LLM: None}                       # 尾部赋真身（前向引用）
POST_ROUTES = {}                                 # 只读页：零写路由

EVENTS_LIMIT = 200                               # 事件线有界（诚实截断）
CHANNELS_FILENAME = "channels.json"              # 战士 --channels 同形文件名
_TL = core.TABLES["timeline.tsv"]
_KV_NONE = ("lane", "cooldown_s")                # 字面 None 还原为 None 的负载键


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_json(path):
    text = _read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:                            # corrupt=按缺席（池 _load 同律）
        return None


def _read_tsv_rows(path, nfields):
    text = _read_text(path)
    if text is None:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        out.append((cols + [""] * nfields)[:nfields] if len(cols) < nfields else cols)
    return out


def _gens(battle_dir):
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in _digits(name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


def _digits(name):
    out, cur = [], ""
    for ch in name:
        if ch.isdigit():
            cur += ch
        elif cur:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def _read_int(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None，布尔无语义：%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数：%r" % (name, value))


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir) —— 有战用战，无战回落主账本。"""
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return [], None, str(ledger_dir or "")
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return battles, None, None
    return battles, picked, os.path.join(root, picked["id"])


def _goal_dir_of(battle_dir):
    gens = _gens(battle_dir)
    if gens:
        return os.path.join(battle_dir, gens[-1]), gens[-1]
    return str(battle_dir or ""), os.path.basename(os.path.normpath(str(battle_dir or "")))


# ---------------------------------------------------------------- 通道池 --

def _load_channels(battle_dir, goal_dir):
    """候选位实勘（任务根→代目录）→ (channels|None, found_path|None)。
    只出脱敏投影位（api_key_set），原始密钥不出本函数。"""
    for base in (battle_dir, goal_dir):
        path = os.path.join(str(base or ""), CHANNELS_FILENAME)
        data = _read_json(path)
        if isinstance(data, list) and data and all(isinstance(c, dict) for c in data):
            return data, path
    return None, None


def _health_of(st, now):
    """状态行 → (state, remaining_s)——llmpool._snap_of 同律（读侧零改动）。"""
    if st.get("hard"):
        return "tripped", None
    end = st.get("cooldown_end") or 0
    if end > 0:
        remain = end - now
        if remain > 0:
            return "cooling", int(math.ceil(remain))
    return "healthy", 0


def _channels_face(battle_dir, goal_dir, states, now):
    """通道池投影：配置序在前+状态在册而配置未见者在后（字典序）。"""
    raw, found = _load_channels(battle_dir, goal_dir)
    out = []
    seen = set()
    if raw:
        for c in raw:
            name = str(c.get("name") or "")
            if not name or name in seen:
                continue
            seen.add(name)
            st = states.get(name) or {}
            state, remaining = _health_of(st, now)
            out.append({
                "name": name, "model": str(c.get("model") or ""),
                "base_url": str(c.get("base_url") or ""),
                "api_key_set": bool(c.get("api_key")),
                "configured": True, "state": state, "remaining_s": remaining,
                "soft_streak": st.get("soft_streak", 0),
                "rate_trips": st.get("rate_trips", 0),
                "server_trips": st.get("server_trips", 0),
            })
    for name in sorted(k for k in states if k not in seen):
        st = states[name] or {}
        state, remaining = _health_of(st, now)
        out.append({
            "name": name, "model": "", "base_url": "", "api_key_set": False,
            "configured": False, "state": state, "remaining_s": remaining,
            "soft_streak": st.get("soft_streak", 0),
            "rate_trips": st.get("rate_trips", 0),
            "server_trips": st.get("server_trips", 0),
        })
    return out, bool(raw), found


def _pool_states(goal_dir):
    """llmpool_state.json → {model: state行}（缺席/corrupt=空——池 _load 同律）。"""
    data = _read_json(os.path.join(goal_dir, _pool.STATE_FILENAME))
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, dict):
        return {}
    return {str(k): (v if isinstance(v, dict) else {}) for k, v in models.items()}


# ---------------------------------------------------------------- 事件线 --

def _parse_failover(event):
    """llm_failover k=v 负载 → dict|None（非本域形=None；None 字面还原）。"""
    if not event.startswith("llm_failover"):
        return None
    payload = {}
    for part in event.split()[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            payload[k] = None if (k in _KV_NONE and v == "None") else v
    if "cooldown_s" in payload and payload["cooldown_s"] is not None:
        try:
            payload["cooldown_s"] = int(payload["cooldown_s"])
        except (TypeError, ValueError):
            pass
    return payload


def _failover_events(battle_dir, limit=EVENTS_LIMIT):
    """timeline llmpool 行 → 新者在前有界事件线 + truncated 旗。"""
    gens = _gens(battle_dir)
    dirs = [os.path.join(battle_dir, g) for g in gens] if gens else [battle_dir]
    picked, truncated = [], False
    for d in dirs:
        if not d:
            continue
        for no, cols in enumerate(_read_tsv_rows(os.path.join(d, "timeline.tsv"),
                                                 len(_TL)), 1):
            if (cols[1] or "").strip() != "llmpool":
                continue
            payload = _parse_failover((cols[3] or "").strip())
            if payload is None:
                continue
            picked.append({"row": no, "ts": cols[0], "phase": cols[2],
                           "payload": payload})
    picked.reverse()                               # 新者在前
    if len(picked) > limit:
        picked, truncated = picked[:limit], True
    return picked, truncated


# ---------------------------------------------------------------- 读投影 --

def llm_status_view(battles_dir=None, battle=None, ledger_dir=None, now=None):
    """模型状态页读投影 → {battle, battles, channels, counts, events,
    events_truncated, params, notes}。只读零写入；now=剩余秒基准（缺省墙钟
    ——route 适配层单点注入，测试注入定值）。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    if now is None:                                # 最后兜底（route 层已注入）
        now = time.time()
    goal_dir, goal = _goal_dir_of(battle_dir)

    states = _pool_states(goal_dir)
    channels, configured, found = _channels_face(battle_dir, goal_dir, states, now)
    events, truncated = _failover_events(battle_dir)

    counts = {
        "channels_configured": sum(1 for c in channels if c["configured"]),
        "healthy": sum(1 for c in channels if c["state"] == "healthy"),
        "cooling": sum(1 for c in channels if c["state"] == "cooling"),
        "tripped": sum(1 for c in channels if c["state"] == "tripped"),
        "events": len(events),
    }
    notes = {
        "channels": (
            ("通道配置=%s（任务目录实勘，战士 --channels 同形；密钥只显示"
             "「是否已配」，原文永不上屏）" % found if configured
             else "未发现通道配置文件（%s）——通道由智能体启动参数注入"
             "（--channels），不入账本；下方仅展示状态文件在册的通道"
             % CHANNELS_FILENAME)),
        "state": ("健康/熔断/冷却剩时=任务代目录 %s（llmpool 钉根状态文件，"
                  "重启恢复同源）；剩余秒按读取时刻计算" % _pool.STATE_FILENAME),
        "events": ("故障转移事件=时间线 llmpool 行（熔断 trip/恢复 recover，"
                   "新者在前，最近 %d 条%s）"
                   % (EVENTS_LIMIT, "；记录较长已截断" if truncated else "")),
    }
    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles,
        "goal": goal,
        "channels": channels,
        "counts": counts,
        "events": events,
        "events_truncated": truncated,
        "params": {                                # 判定参数=ledger.llmpool 单源
            "soft_trip_threshold": _pool.SOFT_TRIP_THRESHOLD,
            "rate_cooldown_s": _pool.RATE_COOLDOWN_S,
            "server_ladder_s": list(_pool.LADDER_S),
            "jitter": _pool.JITTER,
            "hard_status": list(_pool.HARD_STATUS),
        },
        "notes": notes,
    }


# ---------------------------------------------------------------- 路由 --

def _llm_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = llm_status_view(battles_dir=battles_dir, battle=query.get("battle"),
                                  ledger_dir=ledger_dir, now=time.time())
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "模型状态参数无效: %s" % e}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_LLM] = _llm_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
