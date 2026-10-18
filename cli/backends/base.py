# -*- coding: utf-8 -*-
"""外部执行后端·统一接口（功能24a F24a，设计定稿 2026-10-20 唯一正文）。

把外部 AI harness（dsh/claude/codex…）当编外士兵的肌肉：我们的军官（意图/
任务包）派活定规矩，外部 harness 出力执行，成果一律回我们的账本、过我们
的质量门（归一见 ingest.py，零豁免）。本模块只定「接口+协议」：

- JSONL stdio v1 帧协议（Multica/dsh 已商品化的形状，不发明新协议）：帧
  ready/session/text/thinking/tool_call/tool_result/usage/result/error，
  全帧带 v=1；不认识的 type/字段=降级不崩（灰度安全，Multica 模式）。
- Backend 接口字段=Multica 26 后端 checklist 全集（§7.1/§8-2，缺一块就是
  对标缺口）：resume 三语义（resume_session_id 期望续/resume_expected 被
  感知/resume_continuity_notice 通知文案）/supplement（中途改目标，渗透
  刚需）/tool_activity+interrupt（工具级看门狗，长扫描必备）/
  terminal_observed（防「完成」被误判挂起）/usage 四 token 维+成本 ticks
  （1e-10 USD）。
- capability 协商：常量缺省=安全失败——未声明即不支持，调用方协商缺口
  （negotiate）后自决降级，绝不静默假装支持。

测试铁律（tests/test_backends_*.py）：零真子进程/零真外呼——dsh/claude
adapter 全用注入 transport+假帧流，local adapter 全链真跑（进程内自有
warrior）。
"""
import json

PROTOCOL_VERSION = 1

#: v1 出站/入站帧类型全集（task_id/request_id 关联由调用方承载在帧外层）
FRAME_TYPES = frozenset({
    "ready",          # 后端就绪：{runtime}
    "session",        # 会话指针：{session_id}（rerun resume 的锚）
    "text",           # 可见文本增量：{text}
    "thinking",       # 推理增量：{text}
    "tool_call",      # 工具调用开始：{call_id, name, arguments(JSON 字符串)}
    "tool_result",    # 工具调用结束：{call_id, output, is_error}
    "usage",          # 用量：{provider, model, 四 token 维, cost_usd_ticks}
    "result",         # 终态：{status, output, error{code,message},
                      #           session_id, resume_rejected}
    "error",          # 协议/通道错误：{code, message}（dsh protocol_error 同位）
})

# ---------------------------------------------------------------- 能力协商

CAP_RESUME = "resume"                      # 会话续跑（resume 三语义）
CAP_SUPPLEMENT = "supplement"              # 活跃 turn 中途追加指令
CAP_TOOL_ACTIVITY = "tool_activity"        # 工具级活动可视
CAP_INTERRUPT = "interrupt"                # 打断后台工具（长扫描看门狗）
CAP_TERMINAL_OBSERVED = "terminal_observed"  # 终态可观测（防假挂起）
CAP_USAGE_TOKENS = "usage_tokens"          # 四 token 维用量
CAP_COST_TICKS = "cost_ticks"              # 成本 ticks（1e-10 USD）
CAP_MODELS = "models"                      # 模型枚举（--list-models 面）
CAP_CANCEL = "cancel"                      # 任务取消
CAP_MCP = "mcp"                            # MCP server 注入

CAPABILITY_NAMES = frozenset({
    CAP_RESUME, CAP_SUPPLEMENT, CAP_TOOL_ACTIVITY, CAP_INTERRUPT,
    CAP_TERMINAL_OBSERVED, CAP_USAGE_TOKENS, CAP_COST_TICKS, CAP_MODELS,
    CAP_CANCEL, CAP_MCP,
})


class CapabilityDenied(Exception):
    """能力未声明即调用（缺省=安全失败的执法面）。"""


class Capabilities(object):
    """能力集：supports 未声明即 False（默认拒绝，绝不静默放行）。"""

    __slots__ = ("_offered",)

    def __init__(self, offered=frozenset()):
        unknown = set(offered) - CAPABILITY_NAMES
        if unknown:
            raise ValueError("未知能力常量: %s" % sorted(unknown))
        self._offered = frozenset(offered)

    def supports(self, name):
        return name in CAPABILITY_NAMES and name in self._offered

    def offered(self):
        return self._offered

    def __contains__(self, name):
        return self.supports(name)

    def __eq__(self, other):
        return isinstance(other, Capabilities) and \
            self._offered == other._offered

    def __hash__(self):
        return hash(self._offered)


def negotiate(required, offered):
    """需求 ∩ 缺口：返回 required 中 offered 不支持的子集（调用方降级依据）。"""
    return frozenset(
        c for c in required if not offered.supports(c))


# ---------------------------------------------------------------- 帧编解码

def encode_frame(frame):
    """帧 dict → 单行 JSONL（v 强制=1；type 必填；键序确定=可回放）。"""
    if not isinstance(frame, dict) or not frame.get("type"):
        raise ValueError("帧缺 type: %r" % (frame,))
    out = dict(frame)
    out["v"] = PROTOCOL_VERSION
    return json.dumps(out, ensure_ascii=False, sort_keys=True)


def decode_line(line):
    """单行 JSONL → 帧 dict；坏行 None（不外抛——通道降级优先于崩）。"""
    try:
        doc = json.loads(line)
    except (ValueError, TypeError):
        return None
    return doc if isinstance(doc, dict) else None


def classify_frame(frame):
    """帧分级：ok / unknown-type / unknown-version / malformed。"""
    if not isinstance(frame, dict):
        return "malformed"
    v = frame.get("v")
    if v is not None and v != PROTOCOL_VERSION:
        return "unknown-version"
    if frame.get("type") not in FRAME_TYPES:
        return "unknown-type"
    return "ok"


# ---------------------------------------------------------------- 数据面

class Usage(object):
    """用量四 token 维+成本 ticks（§7.1：CostUSDTicks int64，1e-10 USD）。

    cache_read/cache_write=外账（对 Multica/dsh 族入账维度对齐）；本地
    warrior 无缓存维=诚实置 0。
    """

    __slots__ = ("input_tokens", "output_tokens", "cache_read_tokens",
                 "cache_write_tokens", "cost_usd_ticks", "provider", "model")

    def __init__(self, input_tokens=0, output_tokens=0, cache_read_tokens=0,
                 cache_write_tokens=0, cost_usd_ticks=0, provider="",
                 model=""):
        self.input_tokens = int(input_tokens or 0)
        self.output_tokens = int(output_tokens or 0)
        self.cache_read_tokens = int(cache_read_tokens or 0)
        self.cache_write_tokens = int(cache_write_tokens or 0)
        self.cost_usd_ticks = int(cost_usd_ticks or 0)
        self.provider = provider or ""
        self.model = model or ""

    def total_tokens(self):
        return (self.input_tokens + self.output_tokens
                + self.cache_read_tokens + self.cache_write_tokens)

    def dollars(self):
        return self.cost_usd_ticks * 1e-10

    @staticmethod
    def from_frame(frame):
        return Usage(
            input_tokens=frame.get("input_tokens", 0),
            output_tokens=frame.get("output_tokens", 0),
            cache_read_tokens=frame.get("cache_read_tokens", 0),
            cache_write_tokens=frame.get("cache_write_tokens", 0),
            cost_usd_ticks=frame.get("cost_usd_ticks", 0),
            provider=frame.get("provider", ""),
            model=frame.get("model", ""))


class Result(object):
    """终态（§7.1 Result 形）：status/output/session_id/error{code,message}/
    resume_rejected/usage/terminal_observed。"""

    __slots__ = ("status", "output", "session_id", "error", "resume_rejected",
                 "usage", "terminal_observed")

    def __init__(self, status, output="", session_id="", error=None,
                 resume_rejected=False, usage=None, terminal_observed=False):
        self.status = status
        self.output = output or ""
        self.session_id = session_id or ""
        self.error = dict(error or {})
        self.resume_rejected = bool(resume_rejected)
        self.usage = usage if usage is not None else Usage()
        self.terminal_observed = bool(terminal_observed)

    def is_ok(self):
        return self.status == "ok"

    @staticmethod
    def from_frame(frame):
        """result 帧 → Result（error{code,message}/resume_rejected 透传）。"""
        err = frame.get("error") or {}
        return Result(
            status=frame.get("status") or "error",
            output=frame.get("output", ""),
            session_id=frame.get("session_id", ""),
            error={"code": err.get("code", ""), "message": err.get("message", "")}
            if err else {},
            resume_rejected=bool(frame.get("resume_rejected", False)),
            terminal_observed=True)


class ExecOptions(object):
    """派活参数（§7.1 ExecOptions 全字段面，缺省=最保守）。

    resume 三语义：resume_session_id=期望续的会话指针；resume_expected=
    调用方断言续作必然成立（被拒要上浮成错误，不静默重开）；
    resume_continuity_notice=续作通知文案（会话曾被回收/换机等连续性说明）。
    """

    __slots__ = ("task_id", "cwd", "prompt", "model", "max_turns", "timeout_s",
                 "resume_session_id", "resume_expected",
                 "resume_continuity_notice", "mcp_servers", "extra_args")

    def __init__(self, task_id, cwd, prompt, model=None, max_turns=None,
                 timeout_s=None, resume_session_id="", resume_expected=False,
                 resume_continuity_notice="", mcp_servers=None,
                 extra_args=None):
        if not task_id:
            raise ValueError("task_id 必填（帧 request_id 关联律）")
        self.task_id = task_id
        self.cwd = cwd
        self.prompt = prompt
        self.model = dict(model or {})
        self.max_turns = max_turns
        self.timeout_s = timeout_s
        self.resume_session_id = resume_session_id or ""
        self.resume_expected = bool(resume_expected)
        self.resume_continuity_notice = resume_continuity_notice or ""
        self.mcp_servers = list(mcp_servers or [])
        self.extra_args = list(extra_args or [])

    def resume_wanted(self):
        return bool(self.resume_session_id)


# ---------------------------------------------------------------- Session

class Session(object):
    """后端会话句柄基类：帧流累积+看门狗面+能力门方法。

    适配器职责：emit() 喂帧（execute 运行期即流式累积，on_event 回调同步
    可观——工具看门狗/中途打断都在同线程回调里做决定）；基类负责 drain
    增量、tool_activity 视图、terminal_observed、supplement/interrupt 的
    能力门。子类覆写 _do_supplement/_do_interrupt 落真通道。
    """

    def __init__(self, capabilities):
        self.capabilities = (capabilities if isinstance(capabilities,
                                                        Capabilities)
                             else Capabilities(capabilities))
        self.frames = []
        self.unknown_frames = 0
        self._drained = 0
        self._usage = Usage()
        self._session_id = ""

    # ---- 帧面 ----

    def emit(self, frame):
        """喂一帧：unknown 计数不崩；usage/session/result 顺手归位。"""
        kind = classify_frame(frame)
        if kind == "unknown-type" or kind == "unknown-version":
            self.unknown_frames += 1
        elif kind == "malformed":
            self.unknown_frames += 1
            return
        self.frames.append(frame)
        t = frame.get("type")
        if t == "session":
            self._session_id = frame.get("session_id", "") or self._session_id
        elif t == "usage":
            self._merge_usage(Usage.from_frame(frame))
        return frame

    def _merge_usage(self, u):
        """多 usage 帧=分段累计（四维各自相加，元信息末帧胜）。"""
        self._usage = Usage(
            input_tokens=self._usage.input_tokens + u.input_tokens,
            output_tokens=self._usage.output_tokens + u.output_tokens,
            cache_read_tokens=self._usage.cache_read_tokens + u.cache_read_tokens,
            cache_write_tokens=self._usage.cache_write_tokens + u.cache_write_tokens,
            cost_usd_ticks=self._usage.cost_usd_ticks + u.cost_usd_ticks,
            provider=u.provider or self._usage.provider,
            model=u.model or self._usage.model)

    def drain(self):
        """增量取帧：上次 drain 之后的新帧（流式消费面）。"""
        new = self.frames[self._drained:]
        self._drained = len(self.frames)
        return new

    def session_id(self):
        return self._session_id

    def usage(self):
        return self._usage

    # ---- 看门狗面（§7.1 Session 同形） ----

    def tool_activity(self):
        """工具级活动视图：调用数/结果数/最后工具帧序（0 基）。"""
        calls = results = 0
        last = None
        for i, f in enumerate(self.frames):
            t = f.get("type")
            if t == "tool_call":
                calls += 1
                last = i
            elif t == "tool_result":
                results += 1
                last = i
        return {"calls": calls, "results": results, "last_seq": last}

    def terminal_observed(self):
        """终态可观测：见过 result 帧（防「完成」被误判挂起）。"""
        return any(f.get("type") == "result" for f in self.frames)

    # ---- 能力门方法 ----

    def supplement(self, text):
        """中途改目标（渗透刚需）——能力门后落子类真通道。"""
        if not self.capabilities.supports(CAP_SUPPLEMENT):
            raise CapabilityDenied("backend 不支持 supplement")
        return self._do_supplement(text)

    def interrupt_background_tools(self):
        """打断后台工具（长 nmap/nuclei 必备）——能力门后落真通道。"""
        if not self.capabilities.supports(CAP_INTERRUPT):
            raise CapabilityDenied("backend 不支持 interrupt")
        return self._do_interrupt()

    def _do_supplement(self, text):
        return True

    def _do_interrupt(self):
        return True


class Backend(object):
    """后端统一接口：execute(options, on_event) → Session（同步执至终态）。

    实现舰：dsh.py（子进程 dsh --stdio）/claude.py（stream-json 族最小面）/
    local.py（进程内自有 warrior 回环）。能力协商经 self.capabilities。
    """

    name = "backend"
    capabilities = Capabilities()

    def execute(self, options, on_event=None):
        raise NotImplementedError
