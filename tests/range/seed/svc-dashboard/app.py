#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-dashboard——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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
        if self.path.startswith("/api/xml") and ("<!ENTITY" in body or "SYSTEM" in body):
            # XML API（外部实体接受·XXE 合成回显）
            self._send(200, "<html>GTXXE-01 synthetic external entity resolved: file content</html>")
        else:
            self._send(400, "bad request")

    def do_GET(self):
        if self.path.startswith("/report"):            # 报表路由（模板渲染回显）
            name = self.path.split("name=", 1)[-1].split("&")[0]
            self._send(200, "<html>report GTSSTI-01 synthetic ssti render %s</html>" % name)
        elif self.path.startswith("/ping"):            # 探活路由（命令执行·合成输出）
            self._send(200, "<html>ping GTCMDI-01 synthetic cmd output: 64 bytes from 127.0.0.1</html>")
        elif self.path.startswith("/render"):            # 渲染路由（二级路径·模板注入）
            tp = self.path.split("tpl=", 1)[-1].split("&")[0]
            self._send(200, "<html>render GTSSTI-02 synthetic ssti render %s</html>" % tp)
        elif self.path.startswith("/diag"):              # 诊断路由（命令执行·合成输出）
            self._send(200, "<html>diag GTCMDI-02 synthetic cmd output: uptime 3 days</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
