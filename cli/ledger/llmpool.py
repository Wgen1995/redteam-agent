# -*- coding: utf-8 -*-
"""llmpool 故障转移（v0.8 Task A，借 ARTEX 错误分类表 + 两处声明改进）。

纯离线判定核心：不接真 API，一切时间/随机/事件/落盘路径皆可注入。

错误分类表（classify 纯函数）：
  ok           2xx——成功：清软计数/连续熔断计数，治愈任何熔断态
  no_failover  400、ctx取消(asyncio.CancelledError/KeyboardInterrupt)、
               表外 4xx 与未知异常——保守不转移、不动计数
  hard         401/402/403/404——硬熔断：1 次即熔，无自动冷却，仅成功可治愈
  soft         408/429/网络(URLError/timeout/OSError)——软计数；5xx 同
改进①（分道）：429 固定短冷却 1min；408/网络/5xx 走 server 长档
               1min/5min/30min（按各自 lane 连续熔断次数选档，封顶 30min）。
改进②（抖动）：冷却时长 ±20% 抖动（factor = 1 ± JITTER*(2*rng()-1)），
               随机源注入可测。
软计数连续 3 次软失败 → 熔断进冷却；冷却窗过 → 惰性自动恢复（保留
连续熔断计数，防抖动复活；成功 report 才全量清零）。

状态落盘：state_path（默认 env TANYIN_LLMPOOL_STATE，否则 cwd 下
llmpool_state.json；目标 dir 由调用方指向 ledger 旁）原子写 JSON，
重启恢复未过期冷却窗与硬熔断；corrupt 文件按全新启动处理。
事件：每次 trip/recover 经注入 emit 回调发 kind=llm_failover 事件；
默认 emit=None 不发不炸；emit 抛异常亦不阻断池判定。
"""
import asyncio
import json
import math
import os
import random
import socket
import threading
import time
import urllib.error

ENV_STATE = "TANYIN_LLMPOOL_STATE"
STATE_FILENAME = "llmpool_state.json"

HARD_STATUS = (401, 402, 403, 404)   # 硬熔断：1 次即熔
SOFT_TRIP_THRESHOLD = 3              # 软计数连续 N 次熔断
LADDER_S = (60.0, 300.0, 1800.0)     # server 长档 1/5/30 分钟
RATE_COOLDOWN_S = 60.0               # 改进①：429 固定短冷却 1min
JITTER = 0.2                         # 改进②：±20% 抖动

BUCKET_OK = "ok"
BUCKET_NONE = "no_failover"
BUCKET_HARD = "hard"
BUCKET_SOFT = "soft"
LANE_RATE = "rate"
LANE_SERVER = "server"


def classify(err):
    """错误分类纯函数 → (bucket, lane, reason)。

    bucket ∈ ok/no_failover/hard/soft；lane 仅 soft 时为 rate|server。
    HTTPError 按 code 归类（优先于 URLError/OSError 父类）。
    """
    if isinstance(err, int):
        code = err
        if 200 <= code < 300:
            return (BUCKET_OK, None, "http:%d" % code)
        if code in HARD_STATUS:
            return (BUCKET_HARD, None, "http:%d" % code)
        if code == 429:
            return (BUCKET_SOFT, LANE_RATE, "http:429")
        if code == 408 or 500 <= code < 600:
            return (BUCKET_SOFT, LANE_SERVER, "http:%d" % code)
        # 400 及表外状态：保守不转移
        return (BUCKET_NONE, None, "http:%d" % code)
    if isinstance(err, (asyncio.CancelledError, KeyboardInterrupt)):
        return (BUCKET_NONE, None, "exc:%s" % type(err).__name__)
    if isinstance(err, urllib.error.HTTPError):
        return classify(err.code)
    if isinstance(err, (urllib.error.URLError, TimeoutError, socket.timeout,
                        OSError)):
        return (BUCKET_SOFT, LANE_SERVER, "exc:%s" % type(err).__name__)
    return (BUCKET_NONE, None, "exc:%s" % type(err).__name__)


def _new_state():
    """单模型可落盘状态（全 JSON 原生类型）。"""
    return {"soft_streak": 0, "rate_trips": 0, "server_trips": 0,
            "cooldown_end": 0.0, "hard": False}


def _model_id(entry):
    """链元素 dict → 模型 id：优先 model 键，回退 name。"""
    mid = entry.get("model") or entry.get("name")
    if not mid:
        raise ValueError("模型条目缺 model/name 键: %r" % (entry,))
    return str(mid)


class LLMPoolRegistry(object):
    """进程内注册表：pick/report/snapshot 三面 + 状态落盘/恢复。"""

    def __init__(self, state_path=None, now=None, rng=None, emit=None):
        self.state_path = (state_path
                           or os.environ.get(ENV_STATE)
                           or os.path.join(os.getcwd(), STATE_FILENAME))
        self._now = now if now is not None else time.time
        self._rng = rng if rng is not None else random.random
        self._emit = emit
        self._states = {}
        self._load()

    # ---- 接口三面 ----

    def pick(self, models):
        """健康链序首个：按入参顺序返回首个健康模型条目（原 dict 引用）。

        全不健康或空链 → None。判定途中惰性处理到期冷却窗（发 recover）。
        """
        for entry in models:
            mid = _model_id(entry)
            st = self._states.get(mid)
            if st is None:
                return entry
            self._refresh(mid, st)
            if self._snap_of(st)["state"] == "healthy":
                return entry
        return None

    def report(self, model, err):
        """上报单次调用结果（HTTP 状态码 int 或异常实例）→ 该模型快照。"""
        bucket, lane, reason = classify(err)
        mid = str(model)
        if bucket == BUCKET_NONE:
            return self.snapshot(mid)   # 不转移：状态零改动
        st = self._states.get(mid)
        if st is None:
            st = _new_state()
            self._states[mid] = st
        self._refresh(mid, st)          # 冷却窗若已过，先惰性恢复
        if bucket == BUCKET_OK:
            if st["hard"] or st["cooldown_end"] > 0:
                self._fire({"kind": "llm_failover", "event": "recover",
                            "model": mid, "reason": "success",
                            "ts": self._now()})
            st.update(_new_state())     # 成功：计数/熔断全量清零
            self._persist()
        elif bucket == BUCKET_HARD:
            if not st["hard"]:          # 硬熔幂等：重复上报不重复发事件
                st["hard"] = True
                st["cooldown_end"] = 0.0
                st["soft_streak"] = 0
                self._persist()
                self._fire({"kind": "llm_failover", "event": "trip",
                            "model": mid, "reason": reason, "lane": None,
                            "cooldown_s": None, "ts": self._now()})
        else:  # soft
            if not st["hard"]:          # 硬熔 sticky：仅成功可治愈
                st["soft_streak"] += 1
                if st["soft_streak"] >= SOFT_TRIP_THRESHOLD:
                    self._trip(mid, st, lane, reason)
                self._persist()
        return self.snapshot(mid)

    def snapshot(self, model=None):
        """三态快照：healthy/cooling/tripped + 剩余秒。

        单模型 → {"state", "remaining_s"}；全量（model=None）→ {mid: 同构}。
        cooling 剩余秒向上取整（冷却中恒 ≥1）；hard tripped 无自动恢复
        remaining_s=None；healthy 剩余 0。
        """
        if model is not None:
            mid = str(model)
            st = self._states.get(mid)
            if st is None:
                return {"state": "healthy", "remaining_s": 0}
            self._refresh(mid, st)
            return self._snap_of(st)
        return {mid: self._refresh_snap(mid, st)
                for mid, st in sorted(self._states.items())}

    # ---- 内部 ----

    def _trip(self, mid, st, lane, reason):
        st["soft_streak"] = 0
        if lane == LANE_RATE:
            st["rate_trips"] += 1
            base = RATE_COOLDOWN_S                     # 改进①：固定短档
        else:
            st["server_trips"] += 1
            base = LADDER_S[min(st["server_trips"], len(LADDER_S)) - 1]
        cooldown = base * (1.0 + JITTER * (2.0 * self._rng() - 1.0))
        st["cooldown_end"] = self._now() + cooldown
        self._fire({"kind": "llm_failover", "event": "trip", "model": mid,
                    "reason": reason, "lane": lane,
                    "cooldown_s": int(round(cooldown)), "ts": self._now()})

    def _refresh(self, mid, st):
        """惰性到期：软熔冷却窗已过 → 就地恢复（保留连续熔断计数）。"""
        if (not st["hard"] and st["cooldown_end"] > 0
                and self._now() >= st["cooldown_end"]):
            st["cooldown_end"] = 0.0
            st["soft_streak"] = 0
            self._persist()
            self._fire({"kind": "llm_failover", "event": "recover",
                        "model": mid, "reason": "cooldown-expired",
                        "ts": self._now()})

    def _refresh_snap(self, mid, st):
        self._refresh(mid, st)
        return self._snap_of(st)

    def _snap_of(self, st):
        if st["hard"]:
            return {"state": "tripped", "remaining_s": None}
        if st["cooldown_end"] > 0:
            remain = st["cooldown_end"] - self._now()
            if remain > 0:
                return {"state": "cooling",
                        "remaining_s": int(math.ceil(remain))}
        return {"state": "healthy", "remaining_s": 0}

    def _fire(self, event):
        if self._emit is None:
            return
        try:
            self._emit(event)
        except Exception:
            pass  # 事件入账失败不阻断池判定（记账 fail-open）

    def _persist(self):
        """原子落盘（tmp+replace）；失败静默——池判定优先于记账。"""
        try:
            d = os.path.dirname(self.state_path)
            if d:
                os.makedirs(d, exist_ok=True)
            tmp = self.state_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "models": self._states}, f,
                          ensure_ascii=False, sort_keys=True)
            os.replace(tmp, self.state_path)
        except OSError:
            pass

    def _load(self):
        """重启恢复：未过期冷却窗与硬熔断逐模型还原；corrupt → 全新。"""
        try:
            with open(self.state_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, dict):
            return
        for mid, raw in models.items():
            if not isinstance(raw, dict):
                continue
            st = _new_state()
            for key in ("soft_streak", "rate_trips", "server_trips"):
                val = raw.get(key)
                if isinstance(val, int) and not isinstance(val, bool):
                    st[key] = val
            end = raw.get("cooldown_end")
            if isinstance(end, (int, float)) and not isinstance(end, bool):
                st["cooldown_end"] = float(end)
            hard = raw.get("hard")
            if isinstance(hard, bool):
                st["hard"] = hard
            self._states[str(mid)] = st


_REGISTRY = None
_REGISTRY_LOCK = threading.Lock()


def get_registry(**kwargs):
    """进程级单例取用（参数仅首次创建时生效；测试可用 reset_registry）。"""
    global _REGISTRY
    with _REGISTRY_LOCK:
        if _REGISTRY is None:
            _REGISTRY = LLMPoolRegistry(**kwargs)
        return _REGISTRY


def reset_registry():
    """清进程级单例（测试/运维重建入口）。"""
    global _REGISTRY
    with _REGISTRY_LOCK:
        _REGISTRY = None
