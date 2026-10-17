# -*- coding: utf-8 -*-
"""战士测试共用件：本地假模型服务（fixture HTTP，动态口）+假钟。

铁律：绝不真调外部 API——一切模型面测试指向本文件起的 127.0.0.1 动态口
stub；stub 按 payload.model 路由剧本（status/content/usage/sleep），
openai chat 信封兼容。无 TestCase（discovery 空载不炸）。
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def envelope(content, prompt_tokens=100, completion_tokens=20,
             finish_reason="stop", with_usage=True):
    msg = {"role": "assistant", "content": content}
    choice = {"message": msg, "finish_reason": finish_reason}
    body = {"id": "chatcmpl-stub", "object": "chat.completion",
            "choices": [choice]}
    if with_usage:
        body["usage"] = {"prompt_tokens": prompt_tokens,
                         "completion_tokens": completion_tokens}
    return body


class _Handler(BaseHTTPRequestHandler):
    server_version = "FakeModel/1"

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            payload = {}
        self.server.requests.append(payload)
        script = self.server.script_for(payload.get("model", "?"))
        if script.get("sleep_s"):
            time.sleep(script["sleep_s"])
        status = script.get("status", 200)
        if status != 200:
            data = json.dumps({"error": {"message": "boom",
                                         "type": "stub"}}).encode("utf-8")
            self.send_response(status)
        else:
            raw = script.get("raw_body")
            if raw is not None:
                data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            else:
                data = json.dumps(
                    envelope(script.get("content", ""),
                             prompt_tokens=script.get("prompt_tokens", 100),
                             completion_tokens=script.get(
                                 "completion_tokens", 20),
                             with_usage=script.get("with_usage", True)),
                    ensure_ascii=False).encode("utf-8")
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class FakeModelServer(object):
    """按 model 名路由的剧本化假模型服务（动态口，threading）。"""

    def __init__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.requests = []
        self.httpd.script_for = lambda model: {}
        self.port = self.httpd.server_address[1]
        self._t = threading.Thread(target=self.httpd.serve_forever,
                                   daemon=True)
        self._t.start()

    @property
    def base(self):
        return "http://127.0.0.1:%d/v1" % self.port

    def set_scripts(self, scripts):
        """scripts: {model_name: [剧本, ...]}——按到达次序逐个消费，尽后停末个。"""
        queues = {m: list(seq) for m, seq in scripts.items()}
        last = {m: (seq[-1] if seq else {}) for m, seq in scripts.items()}

        def route(model):
            q = queues.get(model)
            if q:
                if len(q) > 1:
                    return q.pop(0)
                return q[0]
            return last.get(model, {})
        self.httpd.script_for = route

    @property
    def requests(self):
        return list(self.httpd.requests)

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class FakeClock(object):
    """可拨假钟：advance(s) 前进；() 取当前 epoch。"""

    def __init__(self, start=1770000000.0):
        self.t = float(start)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += float(seconds)
