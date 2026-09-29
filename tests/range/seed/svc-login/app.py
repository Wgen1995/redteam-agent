#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-login——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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

    attempts = 0   # 登录尝试计数（限流缺失观测面）

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        H.attempts += 1
        # 弱口令路由：admin/admin123 合成凭据放行（成功=marker+X-Auth-Token 发放=认证态通道）
        if "user=admin" in body and "pass=admin123" in body:
            self._send(200, "<html>welcome admin GTWEAKPASS-01 synthetic weak credential accepted</html>",
                       extra=[("X-Auth-Token", TOKEN)])
        elif H.attempts > 10:
            # 11 连击仍受理=无限流（行为差分观测面，dict §二）
            self._send(403, "<html>denied GTRATE-01 synthetic no rate limit after %d attempts</html>" % H.attempts)
        else:
            self._send(403, "<html>denied</html>")

    def do_GET(self):
        if self.path.startswith("/forgot"):
            # 忘记口令路由（用户枚举差分：存在用户 200/不存在 404）
            if "user=admin" in self.path:
                self._send(200, "<html>reset sent GTUSERENUM-01 synthetic user exists disclosure</html>")
            else:
                self._send(404, "not found")
        elif self.path.startswith("/api/otp"):
            # OTP 路由（限流缺失通道二：连击观测）
            H.attempts += 1
            if H.attempts > 10:
                self._send(200, "<html>GTRATE-02 synthetic otp no rate limit after %d tries</html>" % H.attempts)
            else:
                self._send(200, "<html>otp checked</html>")
        else:
            self._send(200, "<html>login form</html>")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
