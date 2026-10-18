# -*- coding: utf-8 -*-
"""功能24a·外部执行后端①：Backend 统一接口+JSONL stdio v1 帧协议（TDD 红测试先行）。

设计源：docs/design/2026-10-20-external-backend-design.md（唯一正文）+
Multica 全量清点 §7.1/§7.2/§8——接口字段=竞品护城河清单，缺一块即对标缺口。

本文件咬住的契约：
- 协议=版本化 JSONL stdio v1：帧 ready/session/text/thinking/tool_call/
  tool_result/usage/result/error，task_id 关联；新字段/新类型不认识=降级
  不崩（Multica 灰度安全模式），坏行不炸。
- capability 协商：常量集缺省=安全失败（supports 未声明即 False）。
- ExecOptions 全字段面：resume 三语义（resume_session_id/resume_expected/
  resume_continuity_notice）/supplement 载体 prompt/cwd/model{provider,id,
  reasoning_effort}/max_turns/timeout/mcp_servers/extra_args。
- Usage 四 token 维（input/output/cache_read/cache_write）+成本 ticks
  （int64 1e-10 USD）；Result 带 status/output/error{code,message}/
  session_id/resume_rejected/terminal_observed。
- Session 基类：frames 流/drain 增量/tool_activity 看门狗面/
  interrupt_background_tools 与 supplement 的能力门（未声明=CapabilityDenied）。

跑法：python3 -m unittest tests.test_backends_base -v
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from backends import base  # noqa: E402


class FrameCodecCase(unittest.TestCase):
    """JSONL stdio v1 帧编解码：确定性/版本钉死/坏行降级。"""

    def test_protocol_version_is_1(self):
        self.assertEqual(base.PROTOCOL_VERSION, 1)

    def test_frame_types_exact_nine(self):
        self.assertEqual(base.FRAME_TYPES, frozenset({
            "ready", "session", "text", "thinking", "tool_call",
            "tool_result", "usage", "result", "error"}))

    def test_encode_injects_version_and_is_deterministic(self):
        line1 = base.encode_frame({"type": "text", "text": "甲"})
        line2 = base.encode_frame({"type": "text", "text": "甲"})
        self.assertEqual(line1, line2)
        doc = json.loads(line1)
        self.assertEqual(doc["v"], 1)
        self.assertEqual(doc["type"], "text")
        self.assertEqual(doc["text"], "甲")

    def test_encode_rejects_frame_without_type(self):
        with self.assertRaises(ValueError):
            base.encode_frame({"text": "x"})

    def test_encode_line_is_single_line(self):
        line = base.encode_frame({"type": "text", "text": "a\nb"})
        self.assertNotIn("\n", line.replace("\\n", ""))
        decoded = base.decode_line(line)
        self.assertEqual(decoded["text"], "a\nb")

    def test_decode_roundtrip(self):
        for frame in ({"type": "ready", "runtime": "dsh"},
                      {"type": "session", "session_id": "s-1"},
                      {"type": "tool_call", "call_id": "c1", "name": "dig",
                       "arguments": "{}"},
                      {"type": "result", "status": "ok", "session_id": "s-1",
                       "resume_rejected": False}):
            back = base.decode_line(base.encode_frame(frame))
            self.assertEqual(back["type"], frame["type"])

    def test_decode_malformed_line_returns_none_not_raise(self):
        self.assertIsNone(base.decode_line("not-json{{{"))
        self.assertIsNone(base.decode_line(""))

    def test_decode_unknown_type_degrades_not_crash(self):
        frame = base.decode_line(json.dumps(
            {"v": 1, "type": "hologram", "x": 1}))
        self.assertIsNotNone(frame)                    # 降级不崩：帧仍返回
        self.assertEqual(base.classify_frame(frame), "unknown-type")

    def test_decode_newer_version_flagged_but_returned(self):
        frame = base.decode_line(json.dumps(
            {"v": 2, "type": "text", "text": "hi"}))
        self.assertIsNotNone(frame)                    # 不认识=降级不崩
        self.assertEqual(base.classify_frame(frame), "unknown-version")

    def test_decode_unknown_extra_field_kept_silently(self):
        frame = base.decode_line(json.dumps(
            {"v": 1, "type": "usage", "input_tokens": 3, "zzz": 9}))
        self.assertEqual(base.classify_frame(frame), "ok")
        self.assertEqual(frame["zzz"], 9)              # 新字段透传不丢


class CapabilityCase(unittest.TestCase):
    """能力协商：缺省=安全失败（Multica DaemonCapability 模式）。"""

    def test_capability_constants_exist(self):
        for name in ("resume", "supplement", "tool_activity", "interrupt",
                     "terminal_observed", "usage_tokens", "cost_ticks",
                     "models", "cancel", "mcp"):
            self.assertIn(name, base.CAPABILITY_NAMES)

    def test_supports_default_deny(self):
        caps = base.Capabilities(frozenset({base.CAP_RESUME}))
        self.assertTrue(caps.supports(base.CAP_RESUME))
        self.assertFalse(caps.supports(base.CAP_SUPPLEMENT))   # 未声明即拒

    def test_supports_unknown_name_denies(self):
        caps = base.Capabilities(frozenset({base.CAP_RESUME}))
        self.assertFalse(caps.supports("teleport"))

    def test_negotiate_reports_missing(self):
        need = {base.CAP_RESUME, base.CAP_SUPPLEMENT}
        offered = base.Capabilities(frozenset({base.CAP_RESUME}))
        self.assertEqual(base.negotiate(need, offered),
                         frozenset({base.CAP_SUPPLEMENT}))


class ExecOptionsCase(unittest.TestCase):
    """ExecOptions 字段面：resume 三语义缺省值+必填校验。"""

    def test_minimal_options_defaults(self):
        opt = base.ExecOptions(task_id="T-1", cwd="/w", prompt="干掉它")
        self.assertEqual(opt.resume_session_id, "")
        self.assertFalse(opt.resume_expected)
        self.assertEqual(opt.resume_continuity_notice, "")
        self.assertEqual(opt.model, {})
        self.assertEqual(opt.mcp_servers, [])
        self.assertEqual(opt.extra_args, [])
        self.assertIsNone(opt.max_turns)
        self.assertIsNone(opt.timeout_s)

    def test_task_id_required(self):
        with self.assertRaises(ValueError):
            base.ExecOptions(task_id="", cwd="/w", prompt="p")

    def test_resume_three_semantics_fields(self):
        opt = base.ExecOptions(
            task_id="T-2", cwd="/w", prompt="p",
            resume_session_id="s-9", resume_expected=True,
            resume_continuity_notice="会话曾被回收，续作时注意")
        self.assertEqual(opt.resume_session_id, "s-9")
        self.assertTrue(opt.resume_expected)
        self.assertEqual(opt.resume_continuity_notice,
                         "会话曾被回收，续作时注意")

    def test_model_shape(self):
        opt = base.ExecOptions(
            task_id="T-3", cwd="/w", prompt="p",
            model={"provider": "deepseek", "id": "r1",
                   "reasoning_effort": "high"})
        self.assertEqual(opt.model["provider"], "deepseek")
        self.assertEqual(opt.model["reasoning_effort"], "high")


class UsageCase(unittest.TestCase):
    """usage 四 token 维+成本 ticks（§7.1 Result.Usage 形）。"""

    def test_four_token_dimensions_and_total(self):
        u = base.Usage(input_tokens=10, output_tokens=5,
                       cache_read_tokens=1, cache_write_tokens=2)
        self.assertEqual(u.total_tokens(), 18)

    def test_cost_ticks_int_and_dollars(self):
        u = base.Usage(cost_usd_ticks=7)
        self.assertAlmostEqual(u.dollars(), 7e-10)   # 1e-10 USD/tick

    def test_defaults_zero(self):
        u = base.Usage()
        self.assertEqual(
            (u.input_tokens, u.output_tokens, u.cache_read_tokens,
             u.cache_write_tokens, u.cost_usd_ticks), (0, 0, 0, 0, 0))
        self.assertEqual(u.provider, "")
        self.assertEqual(u.model, "")

    def test_from_frame_reads_all_four_dims(self):
        u = base.Usage.from_frame({
            "type": "usage", "provider": "p", "model": "m",
            "input_tokens": 100, "output_tokens": 40,
            "cache_read_tokens": 7, "cache_write_tokens": 3,
            "cost_usd_ticks": 11})
        self.assertEqual(u.input_tokens, 100)
        self.assertEqual(u.cache_write_tokens, 3)
        self.assertEqual(u.model, "m")
        self.assertEqual(u.total_tokens(), 150)


class ResultCase(unittest.TestCase):
    """Result 字段面：status/output/error{code,message}/resume_rejected/
    terminal_observed。"""

    def test_defaults(self):
        r = base.Result(status="ok", output="完了")
        self.assertEqual(r.error, {})
        self.assertEqual(r.session_id, "")
        self.assertFalse(r.resume_rejected)
        self.assertFalse(r.terminal_observed)

    def test_error_shape(self):
        r = base.Result(status="error",
                        error={"code": "backend-died", "message": "eof"})
        self.assertEqual(r.error["code"], "backend-died")

    def test_ok_alias(self):
        self.assertTrue(base.Result(status="ok").is_ok())
        self.assertFalse(base.Result(status="error").is_ok())
        self.assertFalse(base.Result(status="cancelled").is_ok())


class SessionContractCase(unittest.TestCase):
    """Session 基类：frames/drain/tool_activity/能力门方法。"""

    def _session(self, caps=frozenset()):
        s = base.Session(base.Capabilities(caps))
        return s

    def test_frames_append_and_drain_incremental(self):
        s = self._session()
        s.emit({"type": "ready", "runtime": "x"})
        s.emit({"type": "session", "session_id": "s1"})
        first = s.drain()
        self.assertEqual([f["type"] for f in first],
                         ["ready", "session"])
        self.assertEqual(s.drain(), [])               # 增量：二次抽干
        s.emit({"type": "text", "text": "hi"})
        self.assertEqual(len(s.drain()), 1)

    def test_tool_activity_watchdog_view(self):
        s = self._session()
        self.assertEqual(s.tool_activity(),
                         {"calls": 0, "results": 0, "last_seq": None})
        s.emit({"type": "tool_call", "call_id": "c1", "name": "nmap",
                "arguments": "[]"})
        s.emit({"type": "tool_call", "call_id": "c2", "name": "nuclei",
                "arguments": "[]"})
        s.emit({"type": "tool_result", "call_id": "c1", "output": "",
                "is_error": False})
        act = s.tool_activity()
        self.assertEqual(act["calls"], 2)             # 长扫描看门狗面
        self.assertEqual(act["results"], 1)
        self.assertEqual(act["last_seq"], 2)          # 0 基序号

    def test_terminal_observed_follows_result_frame(self):
        s = self._session()
        self.assertFalse(s.terminal_observed())       # 防「完成」被误判挂起
        s.emit({"type": "result", "status": "ok", "session_id": "s"})
        self.assertTrue(s.terminal_observed())

    def test_supplement_gated_by_capability(self):
        s = self._session()
        with self.assertRaises(base.CapabilityDenied):
            s.supplement("改打 vpn 入口")
        s2 = self._session({base.CAP_SUPPLEMENT})
        self.assertTrue(s2.supplement("改打 vpn 入口"))

    def test_interrupt_gated_by_capability(self):
        s = self._session()
        with self.assertRaises(base.CapabilityDenied):
            s.interrupt_background_tools()
        s2 = self._session({base.CAP_INTERRUPT})
        self.assertTrue(s2.interrupt_background_tools())

    def test_usage_accumulates_from_frames(self):
        s = self._session()
        s.emit({"type": "usage", "input_tokens": 10, "output_tokens": 1,
                "cache_read_tokens": 0, "cache_write_tokens": 2})
        s.emit({"type": "usage", "input_tokens": 5, "output_tokens": 5,
                "cache_read_tokens": 1, "cache_write_tokens": 0})
        u = s.usage()                                 # 多帧累计（末帧语义）
        self.assertEqual(u.total_tokens(), 24)

    def test_unknown_frames_counted_not_crash(self):
        s = self._session()
        s.emit({"type": "hologram"})
        s.emit({"type": "text", "text": "x"})
        self.assertEqual(s.unknown_frames, 1)
        self.assertEqual(len(s.frames), 2)


if __name__ == "__main__":
    unittest.main()
