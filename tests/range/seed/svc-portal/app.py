#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-portal——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
# 漏洞 marker 只内嵌于漏洞路由响应体（可观测面），注释不带 marker 字面量。
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

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
        elif self.path.startswith("/jwt/verify"):        # JWT 校验路由（过期/none 接受——须真实呈 token 且 alg=none 或 exp 过期）
            # 批次 9 评审修复（蓝军专家 P1）：旧实现对裸 GET 直发 marker（token 零读）语义不成立。
            import base64, json as _json, time as _time
            from urllib.parse import parse_qs, urlsplit as _us
            tok = (self.headers.get("Authorization") or "").replace("Bearer ", "") \
                or (parse_qs(_us(self.path).query).get("token") or [""])[0]
            ok = False
            if tok.count(".") >= 1:
                try:
                    h = tok.split(".")[0]
                    p = tok.split(".")[1] if tok.count(".") > 1 else ""
                    hdr = _json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
                    ok = str(hdr.get("alg", "")).lower() == "none"
                    if not ok and p:
                        pl = _json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
                        ok = float(pl.get("exp", 0)) < _time.time()
                except Exception:
                    ok = False
            if ok:
                self._send(200, "<html>GTJWT-02 synthetic expired token accepted</html>")
            else:
                self._send(401, "auth required")
        elif self.path.startswith("/page"):              # 页面路由（二级路径·本地包含）
            self._send(200, "<html>GTLFI-02 synthetic local file: /etc/hostname content</html>")
        elif self.path.startswith("/widget"):            # 挂件路由（远程包含·RFI 合成回显）
            self._send(200, "<html>GTRFI-01 synthetic remote include executed</html>")
        elif self.path.startswith("/api/graphql"):       # GraphQL 内部路由（二级路径·内省开放）
            self._send(200, "<html>GTGRAPHQL-02 synthetic introspection enabled: __schema</html>")
        elif self.path.startswith("/account/close"):     # 销户路由（CSRF·无 token 状态变更）
            self._send(200, "<html>account closed GTCSRF-02 synthetic no csrf token required</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), H).serve_forever()   # battle-6 端口异构：PORT env（compose 8001-8008）
