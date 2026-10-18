# -*- coding: utf-8 -*-
"""外部执行后端·claude adapter（功能24a）——codex/qwen 同族 stream-json 最小面。

对齐 Multica 清点 §7.3 claude.go 启动形（协议旗黑名单防破坏同律），两点
有意差异（设计 §4 权限分级=差异化卖点）：
- --permission-mode 缺省 default（受控权限）——Multica 全线
  bypassPermissions 是它的洞，恰是我们的「受控渗透」卖点；
- 能力诚实最小面：resume/tool_activity/terminal_observed/usage 四维+
  成本 ticks/mcp 声明；supplement/interrupt/cancel 未做=不声明
  （capability 缺省=安全失败）。

原生事件 → 本包 v1 帧（translate_line 纯函数）：
  system/init → session；assistant content 块 text|thinking|tool_use →
  text|thinking|tool_call(arguments=JSON 字符串)；user tool_result 块 →
  tool_result；result → usage(cache_creation→cache_write 维，
  total_cost_usd→cost_usd_ticks ×1e10 取整)+result(status/output/
  session_id)。

stdin 面：单条 user 消息 JSON 行（stream-json 输入）后关流。
mcp_servers → 0600 临时 JSON 文件 + --mcp-config + --strict-mcp-config
（会话收尾 cleanup_mcp() 即清——配置不留盘面）。

零真子进程律：launcher 注入（FakeTransport 假帧流）。
"""
import json
import os
import stat
import tempfile

from . import base
from .base import (CAP_COST_TICKS, CAP_MCP, CAP_RESUME, CAP_TERMINAL_OBSERVED,
                   CAP_TOOL_ACTIVITY, CAP_USAGE_TOKENS, Capabilities, Result,
                   Session, decode_line, encode_frame)

#: 协议关键字黑名单（§7.3 claude.go:1065-1068）——extra_args 携带即拒
BANNED_EXTRA = frozenset({
    "-p", "--print", "--output-format", "--input-format", "--verbose",
    "--permission-mode", "--resume", "--model", "--max-turns", "--effort",
    "--disallowedTools", "--mcp-config", "--strict-mcp-config",
})

READY_RUNTIME = "claude-stream-json"


def _cost_ticks(usd):
    try:
        return int(round(float(usd) * 1e10))
    except (TypeError, ValueError):
        return 0


def translate_line(doc):
    """原生 stream-json 事件 dict → v1 帧列表（不认识=空列表，降级不崩）。"""
    if not isinstance(doc, dict):
        return []
    t = doc.get("type")
    out = []
    if t == "system" and doc.get("subtype") == "init":
        out.append({"v": 1, "type": "session",
                    "session_id": doc.get("session_id", "")})
    elif t == "assistant":
        msg = doc.get("message") or {}
        for blk in (msg.get("content") or []):
            if not isinstance(blk, dict):
                continue
            bt = blk.get("type")
            if bt == "text":
                out.append({"v": 1, "type": "text",
                            "text": blk.get("text", "")})
            elif bt == "thinking":
                out.append({"v": 1, "type": "thinking",
                            "text": blk.get("thinking", "")})
            elif bt == "tool_use":
                out.append({"v": 1, "type": "tool_call",
                            "call_id": blk.get("id", ""),
                            "name": blk.get("name", ""),
                            "arguments": json.dumps(
                                blk.get("input") or {},
                                ensure_ascii=False, sort_keys=True)})
    elif t == "user":
        msg = doc.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            for blk in content:
                if isinstance(blk, dict) and blk.get("type") == "tool_result":
                    body = blk.get("content", "")
                    if not isinstance(body, str):
                        body = json.dumps(body, ensure_ascii=False)
                    out.append({"v": 1, "type": "tool_result",
                                "call_id": blk.get("tool_use_id", ""),
                                "output": body,
                                "is_error": bool(blk.get("is_error",
                                                         False))})
    elif t == "result":
        u = doc.get("usage") or {}
        out.append({"v": 1, "type": "usage",
                    "provider": "anthropic",
                    "model": (doc.get("model") or ""),
                    "input_tokens": u.get("input_tokens", 0),
                    "output_tokens": u.get("output_tokens", 0),
                    "cache_read_tokens": u.get("cache_read_input_tokens", 0),
                    "cache_write_tokens":
                        u.get("cache_creation_input_tokens", 0),
                    "cost_usd_ticks": _cost_ticks(u.get("total_cost_usd"))})
        status = "ok" if (doc.get("subtype") == "success"
                          and not doc.get("is_error")) else "error"
        out.append({"v": 1, "type": "result", "status": status,
                    "output": doc.get("result", "") or "",
                    "session_id": doc.get("session_id", ""),
                    "resume_rejected": False})
    return out


def default_launcher(argv):
    from .dsh import default_launcher as _dl   # Popen 同形复用（stdio 族）
    return _dl(argv)


class ClaudeSession(Session):
    """claude 会话：持有 mcp 临时文件（cleanup_mcp 收尾清盘）。"""

    def __init__(self, capabilities, mcp_path=""):
        Session.__init__(self, capabilities)
        self._mcp_path = mcp_path
        self._result = None

    def result(self):
        return self._result

    def set_result(self, result):
        self._result = result

    def cleanup_mcp(self):
        if self._mcp_path:
            try:
                os.unlink(self._mcp_path)
            except OSError:
                pass


class ClaudeBackend(base.Backend):
    """claude -p stream-json 后端（最小面）。"""

    name = "claude"
    capabilities = Capabilities(frozenset({
        CAP_RESUME, CAP_TOOL_ACTIVITY, CAP_TERMINAL_OBSERVED,
        CAP_USAGE_TOKENS, CAP_COST_TICKS, CAP_MCP}))

    def __init__(self, claude_path="claude", launcher=None,
                 permission_mode="default"):
        self.claude_path = claude_path
        self.launcher = launcher or default_launcher
        self.permission_mode = permission_mode
        self.last_argv = None

    # ---- argv 组装 ----

    def _write_mcp_config(self, servers):
        fd, path = tempfile.mkstemp(prefix="mcp-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {s.get("name", "s%d" % i): s
                                      for i, s in enumerate(servers)}},
                      f, ensure_ascii=False)
        os.chmod(path, 0o600)
        return path

    def build_launch(self, options):
        argv = [self.claude_path, "-p",
                "--output-format", "stream-json",
                "--input-format", "stream-json",
                "--verbose",
                "--permission-mode", self.permission_mode,
                "--disallowedTools", "AskUserQuestion"]
        mcp_path = ""
        if options.model:
            if options.model.get("id"):
                argv += ["--model", options.model["id"]]
            if options.model.get("reasoning_effort"):
                argv += ["--effort", options.model["reasoning_effort"]]
        if options.max_turns:
            argv += ["--max-turns", str(options.max_turns)]
        if options.resume_session_id:
            argv += ["--resume", options.resume_session_id]
        if options.mcp_servers:
            mcp_path = self._write_mcp_config(options.mcp_servers)
            argv += ["--mcp-config", mcp_path, "--strict-mcp-config"]
        for i in range(0, len(options.extra_args) - 1, 2):
            flag = options.extra_args[i]
            if flag in BANNED_EXTRA:      # 协议关键字黑名单：防破坏拒启
                raise ValueError(
                    "extra_args 含协议旗（黑名单拒绝）: %s" % flag)
            argv += [flag, options.extra_args[i + 1]]
        return argv, mcp_path

    def build_argv(self, options):
        return self.build_launch(options)[0]

    # ---- 执行 ----

    def execute(self, options, on_event=None):
        argv, mcp_path = self.build_launch(options)
        self.last_argv = argv
        transport = self.launcher(argv)
        session = ClaudeSession(self.capabilities, mcp_path=mcp_path)
        session.emit({"v": 1, "type": "ready", "runtime": READY_RUNTIME})
        if on_event is not None:
            on_event(session.frames[-1], session)
        transport.write_line(json.dumps(
            {"type": "user",
             "message": {"role": "user", "content": options.prompt}},
            ensure_ascii=False))
        transport.close_stdin()
        result = None
        while True:
            line = transport.readline()
            if line is None:
                break
            doc = decode_line(line.rstrip("\n"))
            if doc is None:
                session.unknown_frames += 1
                continue
            frames = translate_line(doc)
            if not frames and doc.get("type") not in (
                    "system", "assistant", "user", "result"):
                session.unknown_frames += 1
                continue
            for frame in frames:
                session.emit(frame)
                if on_event is not None:
                    on_event(frame, session)
                if frame.get("type") == "result":
                    result = Result.from_frame(frame)
        if result is None:
            tail = (transport.stderr_tail() or "").strip()
            result = Result(status="error", error={
                "code": "backend-died",
                "message": "无 result 帧即断流" + (": " + tail if tail else "")})
        session.set_result(result)
        return session
