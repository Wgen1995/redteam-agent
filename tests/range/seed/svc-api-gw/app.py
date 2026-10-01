#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-api-gw——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
# 漏洞 marker 只内嵌于漏洞路由响应体（可观测面），注释不带 marker 字面量。
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

TOKEN = "tok-usr-001"   # post-auth 服务会话令牌（合成，登录发放）

# battle-5 T3a（P3 蓝军）：全局速率摩擦——真 IPS 的诚实最小形。跨路由源 IP 计数
# （per-route 限流之上的面级预算），超阈 429+Retry-After+入窗拒收（退避可解）。
# 阈值宽松（30req/10s 滚动窗）不影响重放与正常探测节奏，只罚无退避连喷。
_GL_RATE = {}          # ip -> [timestamps]
_GL_LIMIT, _GL_WINDOW = 30, 10.0


def _gl_throttled(ip):
    now = time.time()
    w = [t for t in _GL_RATE.get(ip, []) if now - t < _GL_WINDOW]
    w.append(now)
    _GL_RATE[ip] = w
    return len(w) > _GL_LIMIT



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
        if _gl_throttled(self.client_address[0]):      # battle-5：面级限流门（先于路由）
            self._send(429, "rate limited: back off (Retry-After)",
                       extra=[("Retry-After", "3")])
            return
        if self.path.startswith("/fetch"):             # 抓取路由（服务端请求伪造·合成内网文档）
            self._send(200, "<html>fetch GTSSRF-01 synthetic internal doc: internal-secret-doc</html>")
        elif self.path.startswith("/preview"):         # 预览路由（服务端请求伪造·合成元数据）
            self._send(200, "<html>preview GTSSRF-02 synthetic webhook meta: internal-metadata</html>")
        elif self.path.startswith("/cors-debug"):      # CORS 调试路由（宽松策略；通配源不带凭据头——浏览器拒收组合不冒充可利用）
            self._send(200, "<html>cors debug GTCORS-01 wildcard allow-origin</html>",
                       extra=[("Access-Control-Allow-Origin", "*")])
        elif self.path.startswith("/api/user"):          # 用户 API（JWT 弱验·alg=none 接受）
            tok = (self.headers.get("Authorization") or "").replace("Bearer ", "")
            # 批次 9 评审修复（蓝军专家 P1）：真 alg=none 形=三段 header.payload.（空签名），
            # 旧判据只收两段退化形致教科书伪造必被拒（诚实探不中）；双收两形。
            ok_none = False
            if tok.count(".") == 1 and tok.split(".")[1] == "":
                ok_none = True                     # 退化两段形（历史兼容）
            elif tok.count(".") == 2 and tok.split(".")[2] == "":
                import base64, json as _json
                try:
                    pad = tok.split(".")[0] + "=" * (-len(tok.split(".")[0]) % 4)
                    hdr = _json.loads(base64.urlsafe_b64decode(pad))
                    ok_none = str(hdr.get("alg", "")).lower() == "none"
                except Exception:
                    ok_none = False
            if ok_none:
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


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), H).serve_forever()
