#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-admin——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网+127.0.0.1 映射）。
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

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        if self.path.startswith("/login") and "user=admin" in body and "pass=admin123" in body:
            self._send(200, "token " + TOKEN)
        else:
            self._send(403, "denied")

    def do_GET(self):
        if not self._authed():
            self._send(401, "auth required")
        elif self.path.startswith("/admin/orders"):        # 订单路由（对象级越权·他人数据回显）
            self._send(200, "<html>GTIDOR-01 synthetic orders of user 101 (not caller)</html>")
        elif self.path.startswith("/admin/invoices"):      # 发票路由（对象级越权·他人数据回显）
            self._send(200, "<html>GTIDOR-02 synthetic invoices of user 202 (not caller)</html>")
        elif self.path.startswith("/admin/api/roles"):     # 角色管理 API（低权会话可达=角色混淆）
            self._send(200, "<html>GTROLE-01 synthetic role list exposed to low-priv session</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
