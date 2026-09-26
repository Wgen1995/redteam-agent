#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-portal——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网+127.0.0.1 映射）。
# 漏洞 marker 只内嵌于漏洞路由响应体（可观测面），注释不带 marker 字面量。
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "tok-usr-001"   # post-auth 服务会话令牌（合成，登录发放）


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, extra=None):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        for k, v in (extra or []):
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _authed(self):
        return self.headers.get("X-Auth-Token") == TOKEN

    def do_GET(self):
        if self.path.startswith("/redirect"):          # 跳转路由（开放重定向）
            to = self.path.split("to=", 1)[-1].split("&")[0]
            self._send(302, "<html>GTREDIR-01 synthetic redirect to %s</html>",
                       extra=[("Location", to)])
        elif self.path.startswith("/debug/env"):       # 调试路由（环境信息泄露·合成脱敏值）
            self._send(200, "<html>GTINFOLEAK-01 synthetic env: DB_PASS=&lt;redacted&gt; AWS_KEY=&lt;redacted&gt;</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
