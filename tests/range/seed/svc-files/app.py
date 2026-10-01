#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# svc-files——授权靶场漏洞服务（批次6 T16 种20；全部合成 payload，仅 compose 内网（M-3 internal:true 宿主零映射——探针经 attack-noop 跳板）。
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

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        if self.path.startswith("/upload") and "filename=" in body:
            # 上传路由（类型无校验·任意文件接受回显）
            self._send(200, "<html>GTUPLOAD-01 synthetic file accepted no type check</html>")
        else:
            self._send(400, "bad request")

    def do_GET(self):
        # battle-6 认证加权（post_auth 靶）：低权会话可达面——token 门后。
        if self.path.startswith("/admin/logs"):
            if not self._authed():
                self._send(401, "auth required")
            else:
                self._send(200, "<html>GTROLE-04 synthetic role-04 低权可达日志</html>")
            return
        if self.path.startswith("/unserialize"):       # 反序列化入口 A（合成对象回显）
            self._send(200, "<html>GTDESER-01 synthetic pickle object inflated</html>")
        elif self.path.startswith("/import"):          # 反序列化入口 B（合成序列化块接受）
            self._send(200, "<html>GTDESER-02 synthetic java serialized blob accepted</html>")
        elif self.path.startswith("/download"):        # 下载路由（目录遍历·合成文件回显）
            self._send(200, "<html>GTTRAVERSAL-01 synthetic file: root:x:0:0:root</html>")
        elif self.path.startswith("/static"):            # 静态资源路由（二级路径·目录遍历）
            self._send(200, "<html>GTTRAVERSAL-02 synthetic file: shadow file content</html>")
        elif self.path.startswith("/decode"):            # 解码路由（二级路径·反序列化）
            self._send(200, "<html>GTDESER-03 synthetic base64 payload object inflated</html>")
        elif self.path.startswith("/.env"):              # 环境文件路由（信息泄露）
            self._send(200, "<html>GTINFOLEAK-03 synthetic env file: SECRET_KEY=&lt;redacted&gt;</html>")
        else:
            self._send(404, "not found")

    def log_message(self, *_a):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), H).serve_forever()   # battle-6 端口异构：PORT env（compose 8001-8008）
