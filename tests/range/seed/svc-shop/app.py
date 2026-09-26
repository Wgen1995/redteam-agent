#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-shop——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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
        if self.path.startswith("/item"):              # 商品详情路由（注入类·合成回显）
            self._send(200, "<html>product page GTSQLI-01 synthetic SQL error near ''1''</html>")
        elif self.path.startswith("/order"):           # 订单路由（注入类·合成回显）
            self._send(200, "<html>order page GTSQLI-02 synthetic SQL syntax error</html>")
        elif self.path.startswith("/search"):          # 搜索路由（反射回显）
            q = self.path.split("q=", 1)[-1].split("&")[0]
            self._send(200, "<html>search results %s GTXSS-01 synthetic reflected xss</html>" % q)
        elif self.path.startswith("/comment"):         # 评论路由（存储回显）
            self._send(200, "<html>comment GTXSS-02 synthetic stored xss echo</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
