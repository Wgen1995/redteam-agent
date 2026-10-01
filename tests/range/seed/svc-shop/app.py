#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-shop——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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
        # battle-6 认证加权（post_auth 靶）：低权会话可达面——token 门后。
        if self.path.startswith("/admin/reports"):
            if not self._authed():
                self._send(401, "auth required")
            else:
                self._send(200, "<html>GTIDOR-06 synthetic idor-06 他人报表</html>")
            return
        # battle-5 T3a（P3 蓝军）：诱饵面——常见扫描器首发路径的拟真 200 噪声
        # （无 marker、无漏洞行为；惩罚无验证的广撒=信噪摩擦）。正身路由不受影响。
        if self.path.startswith("/wp-admin") or self.path.startswith("/admin.php"):
            self._send(200, "<html><title>WordPress &#8250; Setup Configuration</title>"
                          "decoy wp installer noise</html>")
            return
        if self.path.startswith("/.git"):
            self._send(200, "[core] decoy git config noise\nrepositoryformatversion = 0")
            return
        if self.path.startswith("/item"):              # 商品详情路由（注入类·合成回显）
            self._send(200, "<html>product page GTSQLI-01 synthetic SQL error near ''1''</html>")
        elif self.path.startswith("/order"):           # 订单路由（注入类·合成回显）
            self._send(200, "<html>order page GTSQLI-02 synthetic SQL syntax error</html>")
        elif self.path.startswith("/search"):          # 搜索路由（反射回显）
            q = self.path.split("q=", 1)[-1].split("&")[0]
            self._send(200, "<html>search results %s GTXSS-01 synthetic reflected xss</html>" % q)
        elif self.path.startswith("/comment"):         # 评论路由（存储回显）
            self._send(200, "<html>comment GTXSS-02 synthetic stored xss echo</html>")
        elif self.path.startswith("/include"):           # 本地包含路由（LFI·合成回显）
            self._send(200, "<html>include GTLFI-01 synthetic local file: root:x:0:0</html>")
        elif self.path.startswith("/logout"):            # 登出跳转（开放重定向·参数可控）
            nxt = self.path.split("next=", 1)[-1].split("&")[0]
            self._send(302, "<html>GTREDIR-02 synthetic redirect to %s</html>",
                       extra=[("Location", nxt)])
        elif self.path.startswith("/account/transfer"):   # 转账路由（CSRF·无 token 的状态变更 GET）
            self._send(200, "<html>transfer done GTCSRF-01 synthetic no csrf token required</html>")
        elif self.path.startswith("/reply"):             # 回复路由（二级路径·反射回显）
            t2 = self.path.split("text=", 1)[-1].split("&")[0]
            self._send(200, "<html>reply %s GTXSS-03 synthetic reflected xss</html>" % t2)
        elif self.path.startswith("/feedback"):          # 反馈路由（二级路径·反射回显）
            m = self.path.split("msg=", 1)[-1].split("&")[0]
            self._send(200, "<html>feedback %s GTXSS-04 synthetic reflected xss</html>" % m)
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), H).serve_forever()   # battle-6 端口异构：PORT env（compose 8001-8008）
