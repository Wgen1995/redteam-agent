# -*- coding: utf-8 -*-
"""外部执行后端·dsh adapter（功能24a）——dsh=DeepSeek Harness 一等后端。

形状全对齐 Multica 清点 §7.2（pkg/agent/dsh.go 直接对照，不发明协议）：
- 启动 dsh --profile <p> --stdio（profile=协议载体，未装=runtime 降级，
  归 F24b profile 分发自愈舰管）；
- 入站帧 execute{v,request_id,cwd,prompt,resume_session_id[,
  resume_continuity_notice],model{provider,id,reasoning_effort},
  mcp_servers[]} / cancel{request_id} / supplement{request_id,text}（本舰
  扩展帧，对端不识=忽略，降级安全）；模型 ID=provider/model URL 转义；
- 出站帧 ready/runtime → session → text|thinking → tool_call →
  tool_result → usage(四类 token) → result(status,output,error,
  session_id,resume_rejected) → protocol_error（映射本包 error 帧）；
- 进程治理：cancel → 宽限 → SIGTERM → 再宽限 → SIGKILL；stderr 尾部
  留存于 backend-died 错误。

resume 三语义：resume_session_id=期望续；result.resume_rejected=被拒透传；
resume_expected=True 时被拒=上浮 resume-rejected 硬错（不静默重开）；
resume_continuity_notice=续作通知文案随 execute 帧下发。

零真子进程律：launcher/sleep 全注入——测试全走假帧流。
"""
import time

from . import base
from .base import (CAP_CANCEL, CAP_COST_TICKS, CAP_INTERRUPT, CAP_MCP,
                   CAP_RESUME, CAP_SUPPLEMENT, CAP_TERMINAL_OBSERVED,
                   CAP_TOOL_ACTIVITY, CAP_USAGE_TOKENS, Capabilities,
                   Result, Session, decode_line, encode_frame)

GRACE_S = 3.0        # cancel 后宽限（§7.2：3s）
TERM_WAIT_S = 2.0    # SIGTERM 后宽限（§7.2：2s）


def encode_model_id(provider, model_id):
    """provider/model 两段各自 URL 转义后拼接（§7.2:123-147 形）。"""
    import urllib.parse
    q = urllib.parse.quote
    return "%s/%s" % (q(str(provider or ""), safe=""),
                      q(str(model_id or ""), safe=""))


class PopenTransport(object):
    """真子进程 transport（生产面；测试用假实现注入替换）。

    start_new_session=True=独立进程组（§7.2 进程治理律——组信号不外溢）。
    """

    def __init__(self, proc):
        import subprocess
        self.proc = proc
        self._subprocess = subprocess

    def write_line(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def close_stdin(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass

    def readline(self):
        return self.proc.stdout.readline() or None

    def terminate(self):
        self.proc.terminate()

    def kill(self):
        self.proc.kill()

    def wait(self, timeout=None):
        return self.proc.wait(timeout=timeout)

    def stderr_tail(self, limit=2000):
        try:
            err = self.proc.stderr.read() or ""
        except (OSError, ValueError):
            err = ""
        return err[-limit:]


def default_launcher(argv):
    import subprocess
    proc = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, start_new_session=True)
    return PopenTransport(proc)


class DshSession(Session):
    """dsh 会话：transport 持有=supplement/cancel 真通道。"""

    def __init__(self, transport, task_id, capabilities, sleep, grace_s,
                 term_wait_s):
        Session.__init__(self, capabilities)
        self.transport = transport
        self.task_id = task_id
        self._sleep = sleep
        self._grace_s = grace_s
        self._term_wait_s = term_wait_s
        self._result = None

    def result(self):
        return self._result

    def set_result(self, result):
        self._result = result

    # ---- 真通道 ----

    def _do_supplement(self, text):
        """中途改目标：supplement 帧下发（对端不识=忽略，降级安全）。"""
        self.transport.write_line(encode_frame({
            "type": "supplement", "request_id": self.task_id,
            "text": text}))
        return True

    def _do_interrupt(self):
        """打断后台工具：cancel 帧 → 宽限 → TERM → 宽限 → KILL。"""
        self.transport.write_line(encode_frame({
            "type": "cancel", "request_id": self.task_id}))
        self._sleep(self._grace_s)
        if self.transport.wait(self._grace_s) is None:
            self.transport.terminate()
            self._sleep(self._term_wait_s)
            if self.transport.wait(self._term_wait_s) is None:
                self.transport.kill()
        return True


class DshBackend(base.Backend):
    """dsh --stdio 后端（F24a 面：execute/cancel/supplement/usage）。"""

    name = "dsh"
    capabilities = Capabilities(frozenset({
        CAP_RESUME, CAP_SUPPLEMENT, CAP_TOOL_ACTIVITY, CAP_INTERRUPT,
        CAP_TERMINAL_OBSERVED, CAP_USAGE_TOKENS, CAP_COST_TICKS, CAP_CANCEL,
        CAP_MCP}))

    def __init__(self, dsh_path="dsh", profile="graphled", launcher=None,
                 sleep=None, grace_s=GRACE_S, term_wait_s=TERM_WAIT_S):
        self.dsh_path = dsh_path
        self.profile = profile
        self.launcher = launcher or default_launcher
        self.sleep = sleep if sleep is not None else time.sleep
        self.grace_s = grace_s
        self.term_wait_s = term_wait_s

    def build_argv(self):
        return [self.dsh_path, "--profile", self.profile, "--stdio"]

    # ---- 帧组装 ----

    @staticmethod
    def _execute_frame(options):
        frame = {"type": "execute", "request_id": options.task_id,
                 "cwd": options.cwd, "prompt": options.prompt}
        if options.resume_session_id:
            frame["resume_session_id"] = options.resume_session_id
            if options.resume_continuity_notice:
                frame["resume_continuity_notice"] = \
                    options.resume_continuity_notice
        if options.model:
            frame["model"] = dict(options.model)
            if frame["model"].get("provider") and frame["model"].get("id"):
                frame["model"]["id"] = encode_model_id(
                    frame["model"]["provider"], frame["model"]["id"])
        if options.mcp_servers:
            frame["mcp_servers"] = list(options.mcp_servers)
        return frame

    def execute(self, options, on_event=None):
        transport = self.launcher(self.build_argv())
        session = DshSession(transport, options.task_id, self.capabilities,
                             self.sleep, self.grace_s, self.term_wait_s)
        transport.write_line(encode_frame(self._execute_frame(options)))
        result = None
        while True:
            line = transport.readline()
            if line is None:
                break
            raw = decode_line(line.rstrip("\n"))
            if raw is None:
                session.unknown_frames += 1
                continue
            frame = self._normalize(raw)
            session.emit(frame)
            if on_event is not None:
                on_event(frame, session)      # 回调带会话句柄（看门狗面）
            if frame.get("type") == "result":
                result = Result.from_frame(frame)
                break
            if frame.get("type") == "error":
                # protocol_error 同位：会话已坏=终态，不再等 result
                result = Result(status="error", error={
                    "code": frame.get("code", ""),
                    "message": frame.get("message", "")})
                break
        if result is None:
            tail = (transport.stderr_tail() or "").strip()
            result = Result(status="error", error={
                "code": "backend-died",
                "message": "无 result 帧即断流" + (": " + tail if tail else "")})
        elif options.resume_expected and result.resume_rejected:
            # 期望续被拒：不静默接受重开——上浮硬错（resume 三语义执法位）
            result = Result(
                status="error", output=result.output,
                session_id=result.session_id,
                error={"code": "resume-rejected",
                       "message": options.resume_continuity_notice
                       or "后端拒绝续作（resume_expected）"},
                resume_rejected=True,
                usage=result.usage, terminal_observed=True)
        session.set_result(result)
        transport.close_stdin()
        return session

    @staticmethod
    def _normalize(frame):
        """dsh 出站帧归一：protocol_error→error（同位映射）；其余透传。"""
        if frame.get("type") == "protocol_error":
            err = frame.get("error") or {}
            return {"v": base.PROTOCOL_VERSION, "type": "error",
                    "code": err.get("code", frame.get("code", "")),
                    "message": err.get("message", frame.get("message", ""))}
        return frame
