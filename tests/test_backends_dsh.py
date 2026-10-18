# -*- coding: utf-8 -*-
"""功能24a·外部执行后端②a：dsh adapter（TDD 红测试先行）。

对齐 Multica 清点 §7.2（pkg/agent/dsh.go 479 行全读的直接对照）：
- 启动：dsh --profile <p> --stdio；模型 ID=provider/model URL 转义。
- 入站帧：execute{v,request_id,cwd,prompt,resume_session_id,model{provider,
  id,reasoning_effort},mcp_servers[]} 与 cancel{request_id}；出站帧序
  ready/runtime → session(session_id) → text|thinking → tool_call(call_id,
  name,arguments JSON 字符串) → tool_result(output,is_error) → usage(
  provider,model,四类 token) → result(status,output,error{code,message},
  session_id,resume_rejected) → protocol_error。
- 进程治理：cancel 帧→宽限→SIGTERM→再宽限→SIGKILL（独立进程组）；
  stderr 尾部留存于错误。
- resume 三语义：resume_session_id/resume_expected/resume_continuity_
  notice 全字段贯通；期望续被拒=上浮错误，不静默重开。

零真子进程律：全部用 FakeTransport 假帧流，launcher 注入。

跑法：python3 -m unittest tests.test_backends_dsh -v
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from backends import base  # noqa: E402
from backends import dsh  # noqa: E402


class FakeTransport(object):
    """假 dsh 进程：脚本化出站帧流+记录入站帧/信号。"""

    def __init__(self, script_lines, stderr=""):
        self._lines = list(script_lines)
        self.written = []
        self.signals = []
        self.stderr = stderr
        self.alive = True

    def write_line(self, line):
        self.written.append(line)

    def close_stdin(self):
        self.written.append("<stdin-closed>")

    def readline(self):
        return self._lines.pop(0) if self._lines else None

    def terminate(self):
        self.signals.append("TERM")

    def kill(self):
        self.signals.append("KILL")
        self.alive = False

    def wait(self, timeout=None):
        return None if self.alive else 0

    def stderr_tail(self):
        return self.stderr


class FakeSleeper(object):
    def __init__(self):
        self.slept = []

    def __call__(self, s):
        self.slept.append(s)


def _frame(**kw):
    return json.dumps(dict(kw, v=1), ensure_ascii=False)


READY = _frame(type="ready", runtime="dsh")
SESSION = _frame(type="session", session_id="dsh-s1")
TEXT = _frame(type="text", text="扫描中")
THINK = _frame(type="thinking", text="先查子域")
TCALL = _frame(type="tool_call", call_id="c1", name="nmap",
               arguments='["-sV","target"]')
TRES = _frame(type="tool_result", call_id="c1", output="22/open",
              is_error=False)
USAGE = _frame(type="usage", provider="deepseek", model="r1",
               input_tokens=100, output_tokens=40, cache_read_tokens=7,
               cache_write_tokens=3, cost_usd_ticks=11)
RESULT_OK = _frame(type="result", status="ok", output="完成",
                   session_id="dsh-s1", resume_rejected=False)


class DshArgvCase(unittest.TestCase):
    def test_argv_shape_profile_stdio(self):
        b = dsh.DshBackend(dsh_path="/opt/bin/dsh", profile="graphled")
        self.assertEqual(b.build_argv(),
                         ["/opt/bin/dsh", "--profile", "graphled", "--stdio"])

    def test_model_id_url_escaped(self):
        # §7.2：模型 ID=provider/model URL 转义（斜杠不入分隔位歧义）
        self.assertEqual(dsh.encode_model_id("deepseek", "r1"),
                         "deepseek/r1")
        self.assertEqual(dsh.encode_model_id("deepseek", "a/b"),
                         "deepseek/a%2Fb")
        self.assertEqual(dsh.encode_model_id("pro v", "m"),
                         "pro%20v/m")

    def test_capabilities_declared(self):
        b = dsh.DshBackend()
        for cap in (base.CAP_RESUME, base.CAP_SUPPLEMENT, base.CAP_INTERRUPT,
                    base.CAP_TOOL_ACTIVITY, base.CAP_TERMINAL_OBSERVED,
                    base.CAP_USAGE_TOKENS, base.CAP_COST_TICKS, base.CAP_MCP):
            self.assertTrue(b.capabilities.supports(cap), cap)


class DshExecuteCase(unittest.TestCase):
    def _backend(self, script, stderr=""):
        self.tr = FakeTransport(script, stderr=stderr)
        self.sleeper = FakeSleeper()
        b = dsh.DshBackend(launcher=lambda argv: self.tr,
                           sleep=self.sleeper)
        return b

    def _opts(self, **kw):
        args = dict(task_id="T-1", cwd="/w", prompt="任务包正文")
        args.update(kw)
        return base.ExecOptions(**args)

    def _first_written(self):
        return json.loads(self.tr.written[0])

    def test_full_frame_sequence_streamed(self):
        b = self._backend([READY, SESSION, TEXT, THINK, TCALL, TRES, USAGE,
                           RESULT_OK])
        seen = []
        s = b.execute(self._opts(), on_event=lambda f, ss: seen.append(f))
        self.assertEqual([f["type"] for f in seen],
                         ["ready", "session", "text", "thinking",
                          "tool_call", "tool_result", "usage", "result"])
        r = s.result()
        self.assertTrue(r.is_ok())
        self.assertEqual(r.output, "完成")
        self.assertEqual(r.session_id, "dsh-s1")
        self.assertTrue(s.terminal_observed())
        u = s.usage()
        self.assertEqual(u.input_tokens, 100)
        self.assertEqual(u.cache_read_tokens, 7)
        self.assertEqual(u.total_tokens(), 150)
        self.assertEqual(u.cost_usd_ticks, 11)

    def test_execute_frame_shape(self):
        b = self._backend([RESULT_OK])
        b.execute(self._opts(model={"provider": "deepseek", "id": "r1",
                                    "reasoning_effort": "high"},
                             mcp_servers=[{"name": "m1"}]))
        ef = self._first_written()
        self.assertEqual(ef["type"], "execute")
        self.assertEqual(ef["v"], 1)
        self.assertEqual(ef["request_id"], "T-1")
        self.assertEqual(ef["cwd"], "/w")
        self.assertEqual(ef["prompt"], "任务包正文")
        self.assertEqual(ef["model"]["provider"], "deepseek")
        self.assertEqual(ef["model"]["id"], "deepseek/r1")
        self.assertEqual(ef["model"]["reasoning_effort"], "high")
        self.assertEqual(ef["mcp_servers"], [{"name": "m1"}])

    def test_minimal_execute_frame_omits_empty_optionals(self):
        b = self._backend([RESULT_OK])
        b.execute(self._opts())
        ef = self._first_written()
        self.assertNotIn("model", ef)
        self.assertNotIn("mcp_servers", ef)
        self.assertNotIn("resume_session_id", ef)

    def test_eof_without_result_is_error_with_stderr_tail(self):
        b = self._backend([READY], stderr="boom\ntrace-x")
        s = b.execute(self._opts())
        r = s.result()
        self.assertEqual(r.status, "error")
        self.assertEqual(r.error["code"], "backend-died")
        self.assertIn("trace-x", r.error["message"])   # stderr 尾部留存
        self.assertFalse(s.terminal_observed())

    def test_malformed_line_degrades_not_crash(self):
        b = self._backend(["garbage{{{", READY, RESULT_OK])
        s = b.execute(self._opts())
        self.assertTrue(s.result().is_ok())
        self.assertEqual(s.unknown_frames, 1)

    def test_protocol_error_frame_mapped_to_error(self):
        b = self._backend([_frame(type="protocol_error",
                                  error={"code": "bad-frame",
                                         "message": "x"})])
        s = b.execute(self._opts())
        self.assertEqual(s.result().status, "error")
        self.assertEqual(s.result().error["code"], "bad-frame")

    def test_unknown_frame_type_counted_and_stream_continues(self):
        future = json.dumps({"v": 1, "type": "hologram"})
        b = self._backend([READY, future, RESULT_OK])
        s = b.execute(self._opts())
        self.assertTrue(s.result().is_ok())
        self.assertEqual(s.unknown_frames, 1)


class DshResumeCase(unittest.TestCase):
    """resume 三语义：期望续/被拒上浮/通知文案随帧。"""

    def _backend(self, script):
        self.tr = FakeTransport(script)
        return dsh.DshBackend(launcher=lambda argv: self.tr)

    def _opts(self, **kw):
        args = dict(task_id="T-r", cwd="/w", prompt="p")
        args.update(kw)
        return base.ExecOptions(**args)

    def test_resume_session_id_sent(self):
        b = self._backend([RESULT_OK])
        b.execute(self._opts(resume_session_id="dsh-s9",
                             resume_continuity_notice="会话曾被回收"))
        ef = json.loads(self.tr.written[0])
        self.assertEqual(ef["resume_session_id"], "dsh-s9")
        self.assertEqual(ef["resume_continuity_notice"], "会话曾被回收")

    def test_resume_rejected_surfaced(self):
        rej = _frame(type="result", status="error", output="",
                     session_id="dsh-s9", resume_rejected=True,
                     error={"code": "session-gone", "message": "没了"})
        b = self._backend([rej])
        s = b.execute(self._opts(resume_session_id="dsh-s9"))
        r = s.result()
        self.assertTrue(r.resume_rejected)          # 被拒语义透传
        self.assertEqual(r.error["code"], "session-gone")

    def test_resume_expected_and_rejected_becomes_hard_error(self):
        rej = _frame(type="result", status="ok", output="重开新会话干了",
                     session_id="dsh-new", resume_rejected=True)
        b = self._backend([rej])
        s = b.execute(self._opts(resume_session_id="dsh-s9",
                                 resume_expected=True))
        r = s.result()
        # 期望续（resume_expected）被拒：不静默接受重开——上浮 resume-rejected
        self.assertEqual(r.status, "error")
        self.assertEqual(r.error["code"], "resume-rejected")

    def test_resume_expected_and_accepted_stays_ok(self):
        b = self._backend([_frame(type="result", status="ok",
                                  output="续作完成", session_id="dsh-s9",
                                  resume_rejected=False)])
        s = b.execute(self._opts(resume_session_id="dsh-s9",
                                 resume_expected=True))
        self.assertTrue(s.result().is_ok())


class DshControlCase(unittest.TestCase):
    """cancel/打断阶梯（宽限→TERM→宽限→KILL）+ supplement 帧。"""

    def _setup(self, script):
        self.tr = FakeTransport(script)
        self.sleeper = FakeSleeper()
        b = dsh.DshBackend(launcher=lambda argv: self.tr,
                           sleep=self.sleeper,
                           grace_s=3.0, term_wait_s=2.0)
        return b

    def _opts(self):
        return base.ExecOptions(task_id="T-c", cwd="/w", prompt="p")

    def test_interrupt_writes_cancel_then_ladder(self):
        b = self._setup([READY, SESSION, TCALL, RESULT_OK])

        def on_ev(frame, session):
            if frame["type"] == "tool_call":
                session.interrupt_background_tools()
        s = b.execute(self._opts(), on_event=on_ev)
        cancels = [json.loads(w) for w in self.tr.written
                   if w != "<stdin-closed>"]
        self.assertEqual(cancels[1]["type"], "cancel")
        self.assertEqual(cancels[1]["request_id"], "T-c")
        self.assertEqual(self.tr.signals, ["TERM", "KILL"])   # 3s+2s 注入零等待
        self.assertEqual(self.sleeper.slept, [3.0, 2.0])

    def test_interrupt_ladder_stops_at_term_if_proc_exits(self):
        class ExitsOnTerm(FakeTransport):
            def terminate(self):          # 收 TERM 即退（wait 有返回值）
                FakeTransport.terminate(self)
                self.alive = False
        self.tr = ExitsOnTerm([READY, TCALL, RESULT_OK])
        self.sleeper = FakeSleeper()
        b = dsh.DshBackend(launcher=lambda argv: self.tr,
                           sleep=self.sleeper,
                           grace_s=3.0, term_wait_s=2.0)

        def on_ev(frame, session):
            if frame["type"] == "tool_call":
                session.interrupt_background_tools()
        s = b.execute(self._opts(), on_event=on_ev)
        self.assertEqual(self.tr.signals, ["TERM"])           # 不必 KILL
        self.assertEqual(self.sleeper.slept, [3.0, 2.0])      # 两段宽限照走

    def test_supplement_writes_frame_midstream(self):
        b = self._setup([READY, SESSION, TEXT, RESULT_OK])

        def on_ev(frame, session):
            if frame["type"] == "text":
                session.supplement("改打 vpn 入口")
        s = b.execute(self._opts(), on_event=on_ev)
        sups = [json.loads(w) for w in self.tr.written
                if w != "<stdin-closed>"]
        self.assertEqual(sups[1]["type"], "supplement")
        self.assertEqual(sups[1]["request_id"], "T-c")
        self.assertEqual(sups[1]["text"], "改打 vpn 入口")

    def test_tool_activity_visible_midstream(self):
        b = self._setup([READY, TCALL, TRES, RESULT_OK])
        snaps = []

        def on_ev(frame, session):
            snaps.append(dict(session.tool_activity()))
        b.execute(self._opts(), on_event=on_ev)
        self.assertEqual(snaps[-1]["calls"], 1)
        self.assertEqual(snaps[-1]["results"], 1)


if __name__ == "__main__":
    unittest.main()
