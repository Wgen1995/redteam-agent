#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-api-gw——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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
        elif self.path.startswith("/api/user"):          # 用户 API（JWT 弱验·alg=none 接受）
            tok = (self.headers.get("Authorization") or "").replace("Bearer ", "")
            if tok.count(".") == 1 and tok.split(".")[1] == "":
                self._send(200, "<html>GTJWT-01 synthetic jwt alg none accepted</html>")
            else:
                self._send(401, "auth required")
        elif self.path.startswith("/graphql"):           # GraphQL 路由（内省开放）
            self._send(200, "<html>GTGRAPHQL-01 synthetic introspection enabled: __schema types</html>")
        elif self.path.startswith("/proxy"):             # 代理路由（二级路径·SSRF）
            self._send(200, "<html>proxy GTSSRF-03 synthetic internal fetch done</html>")
        elif self.path.startswith("/origin"):            # Origin 回显路由（CORS 反射）
            o = self.headers.get("Origin") or "none"
            self._send(200, "<html>origin GTCORS-02 reflected %s allow-credentials true</html>" % o,
                       extra=[("Access-Control-Allow-Origin", o),
                              ("Access-Control-Allow-Credentials", "true")])
        elif self.path.startswith("/jump"):              # 跳转路由（二级路径·开放重定向）
            u = self.path.split("u=", 1)[-1].split("&")[0]
            self._send(302, "<html>GTREDIR-03 synthetic redirect to %s</html>",
                       extra=[("Location", u)])
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


HTTPServer(("0.0.0.0", 8000), H).serve_forever()
