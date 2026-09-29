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

    # 批次 10（P2#3，渗透专家）：类级全局计数器跨端点串扰（一端连击另一端出 marker，
    # 且重放非自包含=残留计数器假象）——改 per-(route,method) 计数。
    _rate = {}   # {("/login","POST"): n, ("/api/otp","GET"): n}

    def _bump(self, route):
        key = (route, self.command)
        H._rate[key] = H._rate.get(key, 0) + 1
        return H._rate[key]

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        attempts = self._bump("/login")
        # 弱口令路由：admin/admin123 合成凭据放行（成功=marker+X-Auth-Token 发放=认证态通道）
        if "user=admin" in body and "pass=admin123" in body:
            self._send(200, "<html>welcome admin GTWEAKPASS-01 synthetic weak credential accepted</html>",
                       extra=[("X-Auth-Token", TOKEN)])
        elif attempts > 10:
            # 11 连击仍受理=无限流（行为差分观测面，dict §二）
            self._send(403, "<html>denied GTRATE-01 synthetic no rate limit after %d attempts</html>" % attempts)
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
            # OTP 路由（限流缺失通道二：连击观测；per-route 计数=批次 10 P2#3）
            tries = self._bump("/api/otp")
            if tries > 10:
                self._send(200, "<html>GTRATE-02 synthetic otp no rate limit after %d tries</html>" % tries)
            else:
                self._send(200, "<html>otp checked</html>")
        else:
            self._send(200, "<html>login form</html>")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
