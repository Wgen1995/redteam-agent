# -*- coding: utf-8 -*-
"""外部执行后端·local adapter（功能24a）——本地回环=直接调我们自己的 warrior。

为什么要有它（设计 §2）：证明抽象不漏——同一 Backend 接口、同一 v1 帧协议、
同一归一入账通道，内部肌肉（自有 warrior）与外部肌肉（dsh/claude）同形；
同时是测试主力（全链真跑：假模型服务+注入 spawn+假钟=零真子进程）。

不新发明机制律：
- supplement → warrior 原生 steer 轨（write_steer：timeline 定向行，战士
  每回合模型调用前增量消费）——中途改目标走的是自家既有轨道；
- interrupt → steer.write_stop（stop 信号轨，R5 优雅停）；
- 工具帧 → spawn 包夹（gate.execute 的注入位——真工具执行的唯一咽喉）：
  call 前发 tool_call(name=卡命令, arguments=参数表)，call 后发
  tool_result(output 截断 2000+truncated 标记=is_error)；
- usage → transcript 聚合（R4 留痕单源：assistant 行 usage 逐回合记账，
  四维中 cache 两维战士无账=诚实置 0）；
- Result 状态映射：no-intents/max-intents→ok；stop-signal→cancelled；
  budget-cap/time-window/stalled→error(code=状态名)。

prompt 不消费（回环律）：本地执行以账本意图卡为纲，任务包仅为协议形状
完整（外部 adapter 才以 prompt 为公文）。
"""
import itertools
import json
import os

from . import base
from .base import (CAP_INTERRUPT, CAP_SUPPLEMENT, CAP_TERMINAL_OBSERVED,
                   CAP_TOOL_ACTIVITY, CAP_USAGE_TOKENS, Capabilities, Result,
                   Session)

RUNTIME = "graphled-warrior"
TOOL_OUTPUT_LIMIT = 2000


def _split_tool(guard_argv):
    """guard argv → (卡命令, 参数表)：以独立 -- 分隔位切（gate.execute 形）。"""
    argv = list(guard_argv)
    try:
        idx = argv.index("--")
    except ValueError:
        return (argv[-1] if argv else "", [])
    rest = argv[idx + 1:]
    return (rest[0] if rest else "", rest[1:])


def _transcript_offsets(goal_dir):
    """跑前快照：transcripts/<intent>.jsonl → 行数（跑后只读增量）。"""
    d = os.path.join(goal_dir, "transcripts")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if fn.endswith(".jsonl"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                out[fn] = sum(1 for _ in f)
    return out


def _transcript_usage(goal_dir, offsets):
    """跑后聚合：新 assistant 行 usage → 四维 Usage（cache 维=0 诚实）。"""
    d = os.path.join(goal_dir, "transcripts")
    pt = ct = 0
    if not os.path.isdir(d):
        return base.Usage()
    for fn in os.listdir(d):
        if not fn.endswith(".jsonl"):
            continue
        start = offsets.get(fn, 0)
        try:
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i < start:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if row.get("role") != "assistant":
                        continue
                    u = row.get("usage") or {}
                    pt += int(u.get("prompt_tokens", 0) or 0)
                    ct += int(u.get("completion_tokens", 0) or 0)
        except OSError:
            continue
    return base.Usage(input_tokens=pt, output_tokens=ct)


class LocalSession(Session):
    """回环会话：supplement/interrupt 落 steer 真通道。"""

    def __init__(self, capabilities, goal_dir, warrior_id, ts_fn):
        Session.__init__(self, capabilities)
        self.goal_dir = goal_dir
        self.warrior_id = warrior_id
        self._ts_fn = ts_fn
        self._result = None

    def result(self):
        return self._result

    def set_result(self, result):
        self._result = result

    def _do_supplement(self, text):
        from warrior import steer
        steer.write_steer(self.goal_dir, self.warrior_id, text,
                          self._ts_fn())
        return True

    def _do_interrupt(self):
        from warrior import steer
        steer.write_stop(self.goal_dir, self.warrior_id,
                         "backend-interrupt 打断后台工具", self._ts_fn())
        return True


_STATUS_MAP = {
    "no-intents": "ok", "max-intents": "ok", "stop-signal": "cancelled",
    "yielded": "cancelled", "budget-cap": "error", "time-window": "error",
    "stalled": "error",
}


class LocalBackend(base.Backend):
    """本地回环后端：进程内真跑 WarriorLoop（全注入=测试确定性）。"""

    name = "local"
    capabilities = Capabilities(frozenset({
        CAP_SUPPLEMENT, CAP_INTERRUPT, CAP_TOOL_ACTIVITY,
        CAP_TERMINAL_OBSERVED, CAP_USAGE_TOKENS}))

    def __init__(self, goal_dir, battle_name, channels, pool=None,
                 warrior_id="warrior:LB-1", max_intents=1, max_turns=6,
                 lease_min=30, token_cap=100000, clock=None,
                 tool_spawn=None, tool_state_path=None, env=None,
                 skill_path=None, heartbeat_min=5.0, stall_min=15.0,
                 ctx_tokens=24000, guardrail=None):
        self.goal_dir = goal_dir
        self.battle_name = battle_name
        self.channels = list(channels)
        self.pool = pool
        self.warrior_id = warrior_id
        self.max_intents = max_intents
        self.max_turns = max_turns
        self.lease_min = lease_min
        self.token_cap = token_cap
        self.clock = clock
        self.tool_spawn = tool_spawn
        self.tool_state_path = tool_state_path
        self.env = env
        self.skill_path = skill_path
        self.heartbeat_min = heartbeat_min
        self.stall_min = stall_min
        self.ctx_tokens = ctx_tokens
        self.guardrail = guardrail

    def _pool(self):
        if self.pool is not None:
            return self.pool
        from ledger import llmpool_wire
        import os as _os
        env = self.env if self.env is not None else dict(_os.environ)
        return llmpool_wire.attach(self.goal_dir, env=env)

    def _wrap_spawn(self, session, on_event=None):
        """spawn 包夹：真工具执行前后发 tool_call/tool_result 帧（回调
        同步触发——supplement/interrupt 在真执行窗口内可达）。"""
        from tools import gate as tool_gate
        inner = self.tool_spawn or tool_gate._guard_spawn   # 单源引用
        counter = itertools.count(1)

        def _emit(frame):
            session.emit(frame)
            if on_event is not None:
                on_event(frame, session)

        def spawn(guard_argv):
            name, args = _split_tool(guard_argv)
            call_id = "t%d" % next(counter)
            _emit({"v": 1, "type": "tool_call",
                   "call_id": call_id, "name": name,
                   "arguments": json.dumps(
                       [str(a) for a in args], ensure_ascii=False)})
            rc, out, err = inner(guard_argv)
            output = (out if out else (err or ""))
            truncated = len(output) > TOOL_OUTPUT_LIMIT
            _emit({"v": 1, "type": "tool_result",
                   "call_id": call_id,
                   "output": output[:TOOL_OUTPUT_LIMIT],
                   "is_error": rc != 0,
                   "truncated": truncated})
            return rc, out, err
        return spawn

    def execute(self, options, on_event=None):
        from warrior import loop as wloop
        from warrior.heartbeat import iso_of

        clock = self.clock
        ts_fn = (lambda: iso_of(clock())) if clock is not None \
            else (lambda: iso_of(_now()))

        session = LocalSession(self.capabilities, self.goal_dir,
                               self.warrior_id, ts_fn)
        session.emit({"v": 1, "type": "ready", "runtime": RUNTIME})
        session.emit({"v": 1, "type": "session",
                      "session_id": "local:%s:%s" % (self.warrior_id,
                                                     options.task_id)})
        if on_event is not None:
            for f in session.frames:
                on_event(f, session)
        offsets = _transcript_offsets(self.goal_dir)
        loop = wloop.WarriorLoop(
            self.goal_dir, self.battle_name, self.channels, self._pool(),
            warrior_id=self.warrior_id, max_intents=self.max_intents,
            max_turns=self.max_turns, lease_min=self.lease_min,
            token_cap=self.token_cap, clock=clock,
            tool_spawn=self._wrap_spawn(session, on_event),
            tool_state_path=self.tool_state_path,
            skill_path=self.skill_path,
            heartbeat_min=self.heartbeat_min, stall_min=self.stall_min,
            ctx_tokens=self.ctx_tokens, guardrail=self.guardrail)
        report = loop.run()
        usage = _transcript_usage(self.goal_dir, offsets)
        session.emit({"v": 1, "type": "usage",
                      "provider": "graphled-warrior",
                      "model": (self.channels[0].get("model")
                                or self.channels[0].get("name", "")),
                      "input_tokens": usage.input_tokens,
                      "output_tokens": usage.output_tokens,
                      "cache_read_tokens": usage.cache_read_tokens,
                      "cache_write_tokens": usage.cache_write_tokens,
                      "cost_usd_ticks": 0})
        summary = ("status=%s processed=%d done=%d tokens=%d %s"
                   % (report.status, report.processed, report.done_count,
                      usage.total_tokens(), report.stop_detail))
        session.emit({"v": 1, "type": "text", "text": summary})
        status = _STATUS_MAP.get(report.status, "error")
        result = Result(
            status=status, output=summary,
            session_id=session.session_id(),
            error={"code": report.status, "message": report.stop_detail}
            if status == "error" else {},
            usage=usage, terminal_observed=True)
        session.emit({"v": 1, "type": "result", "status": result.status,
                      "output": result.output,
                      "session_id": result.session_id,
                      "resume_rejected": False})
        session.set_result(result)
        if on_event is not None:
            for f in session.drain():
                on_event(f, session)
        return session


def _now():
    import time
    return time.time()
