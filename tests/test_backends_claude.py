# -*- coding: utf-8 -*-
"""功能24a·外部执行后端②b：claude adapter=stream-json 族最小面（TDD 红先行）。

对齐 Multica 清点 §7.3 claude 形（codex/qwen 同族 stream-json 最小面）：
- 启动：claude -p --output-format stream-json --input-format stream-json
  --verbose --permission-mode <mode> --disallowedTools AskUserQuestion
  [--model] [--effort] [--max-turns] [--resume] [--mcp-config <0600 临时文件>
  --strict-mcp-config]；协议旗全部列入 extra_args 黑名单（防破坏）。
- 差异化：permission_mode 缺省=default（受控权限）——Multica 全线
  bypassPermissions 是它的洞，恰是我们的卖点（设计 §4 权限分级）。
- 原生事件 → 本包 v1 帧翻译（纯函数可单测）：system/init→session；
  assistant content 块 text|thinking|tool_use→text|thinking|tool_call；
  user tool_result 块→tool_result；result→usage(四 token 维+成本)+
  result(status/output/session_id)。
- usage 映射：cache_creation_input_tokens→cache_write 维；
  total_cost_usd→cost_usd_ticks（×1e10 取整）。

零真子进程律：launcher 注入（FakeTransport 假帧流，与 dsh 测试同款）。

跑法：python3 -m unittest tests.test_backends_claude -v
"""
import json
import os
import stat
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from backends import base  # noqa: E402
from backends import claude  # noqa: E402
from tests.test_backends_dsh import FakeTransport  # noqa: E402


def _native(**kw):
    return json.dumps(dict(kw), ensure_ascii=False)


INIT = _native(type="system", subtype="init", session_id="cl-s1")
ASSIST = _native(type="assistant", message={"content": [
    {"type": "thinking", "thinking": "先看子域"},
    {"type": "text", "text": "开扫"},
    {"type": "tool_use", "id": "toolu_1", "name": "Bash",
     "input": {"command": "nmap -sV t"}}]})
TOOLRES = _native(type="user", message={"content": [
    {"type": "tool_result", "tool_use_id": "toolu_1", "content": "22/open",
     "is_error": False}]})
RESULT = _native(type="result", subtype="success", is_error=False,
                 result="完成扫描", session_id="cl-s1",
                 usage={"input_tokens": 100, "output_tokens": 40,
                        "cache_creation_input_tokens": 3,
                        "cache_read_input_tokens": 7,
                        "total_cost_usd": 0.0000000007})


class TranslateCase(unittest.TestCase):
    """原生 stream-json → v1 帧纯函数翻译面。"""

    def test_init_maps_to_session(self):
        frames = claude.translate_line(json.loads(INIT))
        self.assertEqual(frames[0]["type"], "session")
        self.assertEqual(frames[0]["session_id"], "cl-s1")

    def test_assistant_blocks_map_in_order(self):
        frames = claude.translate_line(json.loads(ASSIST))
        types = [f["type"] for f in frames]
        self.assertEqual(types, ["thinking", "text", "tool_call"])
        self.assertEqual(frames[0]["text"], "先看子域")
        self.assertEqual(frames[2]["call_id"], "toolu_1")
        self.assertEqual(frames[2]["name"], "Bash")
        # input 对象 → JSON 字符串（§7.2 tool_call.arguments 同形）
        argv = json.loads(frames[2]["arguments"])
        self.assertEqual(argv["command"], "nmap -sV t")

    def test_tool_result_maps(self):
        frames = claude.translate_line(json.loads(TOOLRES))
        self.assertEqual(frames[0]["type"], "tool_result")
        self.assertEqual(frames[0]["call_id"], "toolu_1")
        self.assertEqual(frames[0]["output"], "22/open")
        self.assertFalse(frames[0]["is_error"])

    def test_result_maps_usage_and_terminal(self):
        frames = claude.translate_line(json.loads(RESULT))
        kinds = {f["type"] for f in frames}
        self.assertIn("usage", kinds)
        self.assertIn("result", kinds)
        u = [f for f in frames if f["type"] == "usage"][0]
        self.assertEqual(u["input_tokens"], 100)
        self.assertEqual(u["output_tokens"], 40)
        self.assertEqual(u["cache_read_tokens"], 7)      # cache_read 同名
        self.assertEqual(u["cache_write_tokens"], 3)     # creation→write 维
        self.assertEqual(u["cost_usd_ticks"], 7)         # ×1e10 取整
        r = [f for f in frames if f["type"] == "result"][0]
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["output"], "完成扫描")
        self.assertEqual(r["session_id"], "cl-s1")

    def test_error_result_maps_to_error_status(self):
        bad = _native(type="result", subtype="error_during_execution",
                      is_error=True, result="", session_id="cl-s1",
                      usage={"input_tokens": 1, "output_tokens": 1})
        frames = claude.translate_line(json.loads(bad))
        r = [f for f in frames if f["type"] == "result"][0]
        self.assertEqual(r["status"], "error")

    def test_unknown_native_type_returns_empty(self):
        frames = claude.translate_line({"type": "stream_event", "x": 1})
        self.assertEqual(frames, [])


class ArgvCase(unittest.TestCase):
    def _opts(self, **kw):
        args = dict(task_id="T-1", cwd="/w", prompt="p")
        args.update(kw)
        return base.ExecOptions(**args)

    def test_minimal_argv(self):
        b = claude.ClaudeBackend(claude_path="/usr/local/bin/claude")
        argv = b.build_argv(self._opts())
        self.assertEqual(
            argv[:9],
            ["/usr/local/bin/claude", "-p", "--output-format", "stream-json",
             "--input-format", "stream-json", "--verbose",
             "--permission-mode", "default"])
        self.assertIn("--disallowedTools", argv)

    def test_permission_mode_default_not_bypass(self):
        """差异化：缺省受控权限，不抄 Multica 全线 bypassPermissions。"""
        b = claude.ClaudeBackend()
        argv = b.build_argv(self._opts())
        i = argv.index("--permission-mode")
        self.assertEqual(argv[i + 1], "default")

    def test_optional_flags_when_given(self):
        b = claude.ClaudeBackend()
        argv = b.build_argv(self._opts(
            model={"provider": "anthropic", "id": "sonnet"},
            max_turns=8, resume_session_id="cl-s9"))
        self.assertIn("sonnet", argv)
        self.assertIn("--max-turns", argv)
        i = argv.index("--resume")
        self.assertEqual(argv[i + 1], "cl-s9")

    def test_reasoning_effort_maps_to_effort_flag(self):
        b = claude.ClaudeBackend()
        argv = b.build_argv(self._opts(
            model={"provider": "anthropic", "id": "sonnet",
                   "reasoning_effort": "high"}))
        i = argv.index("--effort")
        self.assertEqual(argv[i + 1], "high")

    def test_protocol_flags_in_extra_args_rejected(self):
        """协议关键字黑名单（§7.3 claude.go:1065-1068 同律）——防破坏。"""
        b = claude.ClaudeBackend()
        with self.assertRaises(ValueError) as ctx:
            b.build_argv(self._opts(extra_args=["--output-format", "text"]))
        self.assertIn("--output-format", str(ctx.exception))

    def test_allowed_extra_args_appended(self):
        b = claude.ClaudeBackend()
        argv = b.build_argv(self._opts(extra_args=["--settings", "/s.json"]))
        self.assertEqual(argv[-2:], ["--settings", "/s.json"])


class ExecuteCase(unittest.TestCase):
    def _backend(self, script):
        self.tr = FakeTransport(script)
        return claude.ClaudeBackend(launcher=lambda argv: self.tr)

    def _opts(self, **kw):
        args = dict(task_id="T-1", cwd="/w", prompt="任务包正文")
        args.update(kw)
        return base.ExecOptions(**args)

    def test_full_stream_and_stdin_shape(self):
        b = self._backend([INIT, ASSIST, TOOLRES, RESULT])
        s = b.execute(self._opts())
        kinds = [f["type"] for f in s.frames]
        # ready 合成帧打头（本包 v1 面），随后原生翻译帧
        self.assertEqual(kinds[0], "ready")
        self.assertEqual(kinds[1], "session")
        self.assertEqual(kinds[-2], "usage")
        self.assertEqual(kinds[-1], "result")
        r = s.result()
        self.assertTrue(r.is_ok())
        self.assertEqual(r.output, "完成扫描")
        self.assertEqual(s.usage().total_tokens(), 150)
        self.assertTrue(s.terminal_observed())
        # stdin：单条 user 消息 JSON 行后关流（stream-json 输入面）
        first = json.loads(self.tr.written[0])
        self.assertEqual(first["type"], "user")
        self.assertEqual(first["message"]["role"], "user")
        self.assertEqual(first["message"]["content"], "任务包正文")
        self.assertIn("<stdin-closed>", self.tr.written)

    def test_tool_activity_from_translated_frames(self):
        b = self._backend([INIT, ASSIST, TOOLRES, RESULT])
        s = b.execute(self._opts())
        self.assertEqual(s.tool_activity(),
                         {"calls": 1, "results": 1, "last_seq": 5})

    def test_garbage_line_degrades(self):
        b = self._backend(["{oops", INIT, RESULT])
        s = b.execute(self._opts())
        self.assertTrue(s.result().is_ok())
        self.assertEqual(s.unknown_frames, 1)

    def test_eof_without_result_is_error(self):
        b = self._backend([INIT])
        s = b.execute(self._opts())
        self.assertEqual(s.result().status, "error")
        self.assertEqual(s.result().error["code"], "backend-died")

    def test_capabilities_honest_minimal(self):
        b = claude.ClaudeBackend()
        for cap in (base.CAP_RESUME, base.CAP_TOOL_ACTIVITY,
                    base.CAP_TERMINAL_OBSERVED, base.CAP_USAGE_TOKENS,
                    base.CAP_COST_TICKS, base.CAP_MCP):
            self.assertTrue(b.capabilities.supports(cap), cap)
        # 最小面未做：中途补指令/打断/取消——诚实不声明（缺省=安全失败）
        for cap in (base.CAP_SUPPLEMENT, base.CAP_INTERRUPT, base.CAP_CANCEL):
            self.assertFalse(b.capabilities.supports(cap), cap)

    def test_mcp_config_written_0600_and_flagged(self):
        self.tr = FakeTransport([RESULT])
        b = claude.ClaudeBackend(launcher=lambda argv: self.tr)
        s = b.execute(self._opts(mcp_servers=[{"name": "m1"}]))
        i = b.last_argv.index("--mcp-config")
        path = b.last_argv[i + 1]
        self.assertIn("--strict-mcp-config", b.last_argv)
        mode = stat.S_IMODE(os.stat(path).st_mode)
        self.assertEqual(mode, 0o600)          # §7.3：0600 临时文件
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        self.assertEqual(doc["mcpServers"]["m1"]["name"], "m1")
        s.cleanup_mcp()                         # 会话收尾即清（不留配置面）
        self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
