# -*- coding: utf-8 -*-
"""llmpool 战场接线（v0.8 Task W）——Registry 钉根 goal 账本 + failover 事件入 timeline。

attach(goal_dir, env=None, now=None, rng=None) 把纯离线判定核（ledger.llmpool）
接进 goal 交战区，两条接线：

1. 状态钉根：state_path=<goal_dir>/llmpool_state.json（重启恢复走 goal 目录内
   自包含状态文件）。
2. 事件入账：emit 包装 ledger.timeline.append_tl_locked——goal 锁内「读表→
   算链→写回」的 timeline 单源写方（批次 10 P2#9 单源钉），不绕锁、不私铸
   链行——把池的 kind=llm_failover 事件 dict 铸成 timeline 事件行。

选定语义（本 docstring 钉死，测试 tests/test_v08w_wire.py 同步钉）：
- 事件行负载："llm_failover" 起头，后接 event/model/reason/lane/cooldown_s
  逐键 k=v（键在场才进；硬熔 lane=None cooldown_s=None 照印，recover 事件
  无此二键自然省略）——沿账本既有 key=value 事件词惯例（guard/replay 同款）。
- 行定位：actor="llmpool"（工具名先例），phase="P-lifecycle"（跨阶段基础
  设施事件轨，wallclock mint_wall_sync 同款），revert 空。
- ts 换算：池事件 ts 为注入时钟数值（epoch 秒）→ UTC ISO8601 Z 字符串；
  已是字符串则原样透传（ts 必填律由 append_tl_locked 执法，本层不缺省）。
- env（默认 os.environ）：仅认 TANYIN_LLMPOOL_STATE（llmpool.ENV_STATE 同名
  先例）整体改投 state 文件位置——只移 state，事件仍入 goal_dir/timeline.tsv；
  传空映射 {} 即与进程环境隔离。
- attach 幂等：每次调用返回新建等价 Registry（无隐藏进程缓存——进程级单例
  需求由 llmpool.get_registry 承担）；等价性由同一 state 文件承载，多实例
  并发写亦只做原子整文件替换，无半写。
- fail-open 双保险：emit 任何异常由 llmpool._fire 吞、state 落盘失败由
  llmpool._persist 静默——接线层不新增炸点，timeline 写失败不阻断池判定。
"""
import datetime
import os

from . import llmpool
from . import timeline

ACTOR = "llmpool"
PHASE = "P-lifecycle"          # 跨阶段基础设施事件轨（wallclock 先例）
EVENT_KIND = "llm_failover"
_PAYLOAD_FIELDS = ("event", "model", "reason", "lane", "cooldown_s")
_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso_ts(ts):
    """池事件 ts → timeline ts 列：数值（epoch 秒）转 UTC ISO8601 Z；字符串透传。"""
    if isinstance(ts, str) and ts:
        return ts
    return datetime.datetime.fromtimestamp(
        float(ts), datetime.timezone.utc).strftime(_TS_FMT)


def _event_line(ev):
    """事件 dict → 事件行词：llm_failover + 逐键 k=v（键在场才进）。"""
    parts = [EVENT_KIND]
    for key in _PAYLOAD_FIELDS:
        if key in ev:
            parts.append("%s=%s" % (key, ev[key]))
    return " ".join(parts)


def _make_emit(goal_dir):
    """emit 包装：单源写方 append_tl_locked（goal 锁内路径），无本地链铸造。"""
    def emit(ev):
        timeline.append_tl_locked(goal_dir, _iso_ts(ev.get("ts")),
                                  _event_line(ev), ACTOR, PHASE)
    return emit


def attach(goal_dir, env=None, now=None, rng=None):
    """把 llmpool.Registry 接进 goal 账本（战场接线单点）。

    state_path=<goal_dir>/llmpool_state.json（env[TANYIN_LLMPOOL_STATE] 可整体
    改投）；emit=append_tl_locked 包装发 llm_failover 事件行；now/rng 原样
    注入池（None 走池缺省）。幂等语义：每次调用新建等价 Registry——详见
    模块 docstring「选定语义」节。
    """
    env = os.environ if env is None else env
    state_path = env.get(llmpool.ENV_STATE) or os.path.join(
        goal_dir, llmpool.STATE_FILENAME)
    return llmpool.LLMPoolRegistry(
        state_path=state_path, now=now, rng=rng, emit=_make_emit(goal_dir))
