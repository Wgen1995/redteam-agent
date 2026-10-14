# -*- coding: utf-8 -*-
"""judge 窄调用客户端单测（v0.8 Task D）。

本地 http.server stub 模拟三态（合法 JSON / 畸形响应 / 超时），
真实 API 绝不进测试；URL 通过 base_url 参数注入。
"""
import json
import os
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'cli'))
from ledger import judge_client as jc  # noqa: E402


GOOD = json.dumps({"verdict": "allow", "comment": "实际操作/后果/规则三段",
                   "reason": "命中规则 R3"}, ensure_ascii=False)


class _StubHandler(BaseHTTPRequestHandler):
    """可编程 stub：mode=ok(openai 信封) / raw(原样字节)；另支持 sleep_s/status。"""
    mode = "ok"
    content = None
    finish_reason = "stop"
    status = 200
    sleep_s = 0.0
    seen = {}

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        _StubHandler.seen = {
            "path": self.path,
            "auth": self.headers.get("Authorization"),
            "ctype": self.headers.get("Content-Type"),
            "body": json.loads(self.rfile.read(n).decode("utf-8")),
        }
        if _StubHandler.sleep_s:
            time.sleep(_StubHandler.sleep_s)
        if _StubHandler.status != 200:
            data = b'{"error": "boom"}'
            self.send_response(_StubHandler.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if _StubHandler.mode == "raw":
            data = _StubHandler.content
            data = data.encode("utf-8") if isinstance(data, str) else data
        else:
            inner = GOOD if _StubHandler.content is None else _StubHandler.content
            data = json.dumps({"choices": [
                {"message": {"content": inner},
                 "finish_reason": _StubHandler.finish_reason},
            ]}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class StubServer:
    def __init__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def base(self):
        return "http://127.0.0.1:%d/v1" % self.port

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class JudgeBase(unittest.TestCase):
    def setUp(self):
        _StubHandler.seen = {}
        _StubHandler.mode = "ok"
        _StubHandler.content = None
        _StubHandler.finish_reason = "stop"
        _StubHandler.status = 200
        _StubHandler.sleep_s = 0.0
        self.stub = StubServer()

    def tearDown(self):
        self.stub.stop()

    def client(self, **kw):
        kw.setdefault("base_url", self.stub.base)
        kw.setdefault("model", "m-test")
        kw.setdefault("api_key", "k-test")
        kw.setdefault("env", {})
        return jc.JudgeClient(**kw)


class TestNotConfigured(JudgeBase):
    def test_all_missing(self):
        v, r = jc.ask("判一下", env={})
        self.assertIsNone(v)
        self.assertEqual(r, "not-configured")

    def test_any_single_piece_missing(self):
        for drop in ("base_url", "model", "api_key"):
            kw = {"base_url": self.stub.base, "model": "m",
                  "api_key": "k", "env": {}}
            kw.pop(drop)
            v, r = jc.ask("判一下", **kw)
            self.assertIsNone(v, drop)
            self.assertEqual(r, "not-configured", drop)
        # 全程零请求：未配置时绝不出网
        self.assertEqual(_StubHandler.seen, {})

    def test_env_fallback_configures(self):
        v, r = jc.ask(
            "判一下",
            env={"TANYIN_JUDGE_BASE_URL": self.stub.base,
                 "TANYIN_JUDGE_MODEL": "m-env",
                 "TANYIN_JUDGE_API_KEY": "k-env"})
        self.assertEqual(v, {"verdict": "allow",
                             "comment": "实际操作/后果/规则三段",
                             "reason": "命中规则 R3"})
        self.assertIsNone(r)
        self.assertEqual(_StubHandler.seen["body"]["model"], "m-env")
        self.assertEqual(_StubHandler.seen["auth"], "Bearer k-env")

    def test_param_overrides_env(self):
        v, r = jc.ask(
            "判一下", model="m-param",
            env={"TANYIN_JUDGE_BASE_URL": self.stub.base,
                 "TANYIN_JUDGE_MODEL": "m-env",
                 "TANYIN_JUDGE_API_KEY": "k-env"})
        self.assertIsNone(r)
        self.assertEqual(_StubHandler.seen["body"]["model"], "m-param")


class TestLegalFlow(JudgeBase):
    def test_full_object(self):
        v, r = self.client().ask("判一下")
        self.assertEqual(v, {"verdict": "allow",
                             "comment": "实际操作/后果/规则三段",
                             "reason": "命中规则 R3"})
        self.assertIsNone(r)

    def test_subset_object_ok(self):
        _StubHandler.content = '{"verdict": "deny"}'
        v, r = self.client().ask("判一下")
        self.assertEqual(v, {"verdict": "deny"})
        self.assertIsNone(r)

    def test_whitespace_padded_json_ok(self):
        _StubHandler.content = '  \n{"verdict": "allow"}\n  '
        v, r = self.client().ask("判一下")
        self.assertEqual(v, {"verdict": "allow"})
        self.assertIsNone(r)

    def test_deterministic_code_fence_stripped(self):
        _StubHandler.content = "```json\n" + GOOD + "\n```"
        v, r = self.client().ask("判一下")
        self.assertEqual(v["verdict"], "allow")
        self.assertIsNone(r)

    def test_request_contract(self):
        self.client().ask("任务书正文一句话")
        seen = _StubHandler.seen
        self.assertEqual(seen["path"], "/v1/chat/completions")
        self.assertEqual(seen["auth"], "Bearer k-test")
        self.assertTrue((seen["ctype"] or "").startswith("application/json"))
        body = seen["body"]
        self.assertEqual(body["model"], "m-test")
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["max_tokens"], 512)
        # 单轮：仅一条 user 消息，无 system、无历史
        self.assertEqual(body["messages"], [{"role": "user",
                                             "content": "任务书正文一句话"}])


class TestMalformed(JudgeBase):
    def assert_fail(self, reason):
        v, r = self.client().ask("判一下")
        self.assertIsNone(v)
        self.assertEqual(r, reason)
        return r

    def test_prose_rejected(self):
        _StubHandler.content = "我认为这个操作可以放行。"
        self.assert_fail("prose")

    def test_duplicate_key_rejected(self):
        _StubHandler.content = '{"verdict": "allow", "verdict": "deny"}'
        self.assert_fail("duplicate-key")

    def test_extra_field_rejected(self):
        _StubHandler.content = ('{"verdict": "allow", "comment": "c",'
                                ' "reason": "r", "confidence": 0.9}')
        self.assert_fail("extra-keys")

    def test_array_rejected(self):
        _StubHandler.content = '["verdict"]'
        self.assert_fail("not-single-object")

    def test_two_objects_rejected(self):
        _StubHandler.content = '{"verdict": "allow"} {"verdict": "deny"}'
        self.assert_fail("not-single-object")

    def test_missing_verdict_rejected(self):
        _StubHandler.content = '{"comment": "只说不判"}'
        self.assert_fail("missing-verdict")

    def test_truncation_by_finish_reason(self):
        # finish_reason=length：即使内容恰好完整也判截断，绝不补全
        _StubHandler.content = '{"verdict": "allow"'
        _StubHandler.finish_reason = "length"
        self.assert_fail("truncated")

    def test_truncated_fence_never_repaired(self):
        # 栅栏开了没关（典型截断）：去栅栏只做确定性剥离，绝不修复
        _StubHandler.content = "```json\n" + '{"verdict": "all'
        self.assert_fail("prose")

    def test_envelope_without_choices(self):
        _StubHandler.mode = "raw"
        _StubHandler.content = '{"object": "chat.completion"}'
        self.assert_fail("bad-response")

    def test_envelope_garbage_body(self):
        _StubHandler.mode = "raw"
        _StubHandler.content = "502 Bad Gateway"
        self.assert_fail("bad-response")

    def test_content_not_string(self):
        _StubHandler.mode = "raw"
        _StubHandler.content = json.dumps(
            {"choices": [{"message": {"content": 123},
                          "finish_reason": "stop"}]})
        self.assert_fail("bad-response")

    def test_http_error_fail_closed(self):
        _StubHandler.status = 500
        r = self.assert_fail("http-error:500")
        self.assertTrue(r.startswith("http-error"))

    def test_connection_refused_fail_closed(self):
        self.stub.stop()  # 端口即死
        c = jc.JudgeClient(base_url=self.stub.base, model="m",
                           api_key="k", env={})
        v, r = c.ask("判一下")
        self.assertIsNone(v)
        self.assertEqual(r, "network-error")


class TestTimeout(JudgeBase):
    def test_slow_endpoint_times_out(self):
        _StubHandler.sleep_s = 1.5
        c = self.client(timeout=0.3)
        v, r = c.ask("判一下")
        self.assertIsNone(v)
        self.assertEqual(r, "timeout")


if __name__ == '__main__':
    unittest.main()
