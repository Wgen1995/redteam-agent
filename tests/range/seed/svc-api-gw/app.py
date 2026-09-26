#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-api-gw——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网+127.0.0.1 映射）。
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
        if self.path.startswith("/fetch"):             # 抓取路由（服务端请求伪造·合成内网文档）
            self._send(200, "<html>fetch GTSSRF-01 synthetic internal doc: internal-secret-doc</html>")
        elif self.path.startswith("/preview"):         # 预览路由（服务端请求伪造·合成元数据）
            self._send(200, "<html>preview GTSSRF-02 synthetic webhook meta: internal-metadata</html>")
        elif self.path.startswith("/cors-debug"):      # CORS 调试路由（宽松策略+调试回显）
            self._send(200, "<html>cors debug GTCORS-01 wildcard allow-origin</html>",
                       extra=[("Access-Control-Allow-Origin", "*"),
                              ("Access-Control-Allow-Credentials", "true")])
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
