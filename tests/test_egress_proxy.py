# -*- coding: utf-8 -*-
"""批次 6 T10：Tier3 egress 代理本体（tanyin-egress serve；裁决 H，TDD 红→绿）。

断言面：
- parse_acl 绑定 compile 真实产物格式（egress.acl v2：[acl]/[dns-pinning]/[oob]/[infra]，
  default deny、allow 通配/CIDR、pin 无 ip 声明、allow-oob/allow-infra）——未知行
  ValueError fail-closed；
- 判定单源 decide：host:port 精确/端口通配/通配后缀/CIDR/默认拒绝；
- 端到端（upstream+proxy 全 127.0.0.1 ephemeral）：allow 转发（log kind=forward）、
  deny 403（log verdict=deny）、CONNECT 无 ACL 拒 403（隧道不建立）、canary 触碰
  告警行（kind=canary）、OOB 落账行（kind=oob）、dns-pin 地址不符拒绝（pin_ok=False）；
- 代理绝不写 13 表：egress-log.jsonl 是唯一运行时工件（单写者纪律）。
TLS 限制披露（裁决 H）：CONNECT 按 CONNECT 目标主机名判定，不解析 TLS 内容（无中间人）。
"""
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import egress_proxy  # noqa: E402

TS = "2026-09-24T00:00:00Z"
UP_BODY = b"up-ok"


class _Up(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(UP_BODY)))
        self.end_headers()
        self.wfile.write(UP_BODY)

    def log_message(self, *a):
        pass


def _start(srv):
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def _compile_real_acl():
    """compile 真实产物（G-g1 拷贝上编译——共享夹具零触碰纪律：compile 落 timeline
    事件，直编共享夹具=夹具漂移事故源，本测试在 tempfile 拷贝内锚定格式）。"""
    import shutil
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        gd = os.path.join(d, "g")
        shutil.copytree(os.path.join(HERE, "fixtures", "G-g1"), gd)
        subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-egress"),
                        "compile", "--goal-dir", gd],
                       capture_output=True, text=True, timeout=120,
                       env={**os.environ, "PYTHONUTF8": "1"}, check=True)
        with open(os.path.join(gd, "egress.acl"), encoding="utf-8") as f:
            return f.read()


class TestAcl(unittest.TestCase):
    def test_parse_real_compile_product(self):
        """解析器与 compile 真实产物绑定（egress.acl v2 格式锚定）。"""
        acl = egress_proxy.parse_acl(_compile_real_acl())
        self.assertTrue(acl["default_deny"])
        self.assertIn(("*.shop.example", "*"), acl["allow"])
        self.assertIn("*.shop.example", acl["dns_pin"])
        self.assertEqual(sorted(acl["oob"]), [])
        # 通配后缀与 CIDR 判定走 decide 单源
        self.assertEqual(egress_proxy.decide(acl, "a.shop.example", 443), "allow")
        self.assertEqual(egress_proxy.decide(acl, "10.10.9.9", 80), "allow")
        self.assertEqual(egress_proxy.decide(acl, "evil.example", 443), "deny")
        # 基础设施白名单=allow 面（端口通配）
        self.assertEqual(egress_proxy.decide(acl, "api.github.com", 443), "allow")

    def test_parse_plan_forms(self):
        """计划行约定形态（host:port 精确/dns-pin 带 ip/oob/canary）并存可解析。"""
        acl = egress_proxy.parse_acl(
            "allow api.example.com:443\n"
            "allow wide.example:*\n"
            "dns-pin api.example.com 203.0.113.9\n"
            "oob oob.example.com\n"
            "canary canary.invalid\n")
        self.assertEqual(acl["allow"], {("api.example.com", 443), ("wide.example", "*")})
        self.assertEqual(acl["dns_pin"], {"api.example.com": "203.0.113.9"})
        self.assertEqual(acl["oob"], {"oob.example.com"})
        self.assertEqual(acl["canary"], {"canary.invalid"})

    def test_unknown_line_fails_closed(self):
        with self.assertRaises(ValueError):
            egress_proxy.parse_acl("mystery-line x\n")


class TestDecide(unittest.TestCase):
    def setUp(self):
        self.acl = egress_proxy.parse_acl(
            "[acl]\ndefault deny\nallow web.example:8080\nallow any.example:*\n"
            "allow *.suf.example\nallow 10.10.0.0/16\n")

    def test_port_exact_and_wildcard(self):
        self.assertEqual(egress_proxy.decide(self.acl, "web.example", 8080), "allow")
        self.assertEqual(egress_proxy.decide(self.acl, "web.example", 81), "deny")
        self.assertEqual(egress_proxy.decide(self.acl, "any.example", 9999), "allow")

    def test_wildcard_suffix_strict(self):
        self.assertEqual(egress_proxy.decide(self.acl, "a.suf.example", 443), "allow")
        self.assertEqual(egress_proxy.decide(self.acl, "suf.example", 443), "deny",
                         "通配 *.suf 不含裸域（apex 由独立 allow 行声明）")
        self.assertEqual(egress_proxy.decide(self.acl, "a.b.suf.example", 443), "allow")

    def test_default_deny(self):
        self.assertEqual(egress_proxy.decide(self.acl, "other.example", 80), "deny")


class TestProxyEndToEnd(unittest.TestCase):
    """线程内起 upstream http.server（127.0.0.1 ephemeral）+proxy（ephemeral）；
    http.client 挂代理发绝对 URI 请求（代理形态）；Windows CI 兼容——只连 127.0.0.1。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        d = self.td.name
        self.log_path = os.path.join(d, "egress-log.jsonl")
        self.up = _start(ThreadingHTTPServer(("127.0.0.1", 0), _Up))
        self.up_port = self.up.server_address[1]

    def tearDown(self):
        self.up.shutdown()
        self.up.server_close()
        self.td.cleanup()

    def _proxy(self, acl_text):
        p = egress_proxy.serve_text(acl_text, port=0, egress_log=self.log_path, now=TS)
        return _start(p)

    def _get_via_proxy(self, proxy_port, url, host_header=None):
        conn = http.client.HTTPConnection("127.0.0.1", proxy_port, timeout=10)
        conn.request("GET", url, headers={"Host": host_header or url})
        r = conn.getresponse()
        body = r.read()
        conn.close()
        return r, body

    def _log_rows(self):
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f if ln.strip()]

    def test_allow_forward(self):
        p = self._proxy("[acl]\ndefault deny\nallow 127.0.0.1:%d\n" % self.up_port)
        r, body = self._get_via_proxy(
            p.server_address[1], "http://127.0.0.1:%d/hello" % self.up_port)
        self.assertEqual(r.status, 200)
        self.assertEqual(body, UP_BODY)
        rows = self._log_rows()
        self.assertEqual([x["kind"] for x in rows], ["forward"])
        self.assertEqual(rows[0]["verdict"], "allow")
        self.assertEqual(rows[0]["host"], "127.0.0.1")
        self.assertEqual(rows[0]["port"], self.up_port)
        self.assertEqual(rows[0]["ts"], TS)

    def test_deny_403(self):
        p = self._proxy("[acl]\ndefault deny\nallow other.example:80\n")
        r, _ = self._get_via_proxy(
            p.server_address[1], "http://127.0.0.1:%d/hello" % self.up_port)
        self.assertEqual(r.status, 403)
        rows = self._log_rows()
        self.assertEqual(rows[0]["kind"], "forward")
        self.assertEqual(rows[0]["verdict"], "deny")

    def test_connect_denied_without_acl(self):
        p = self._proxy("[acl]\ndefault deny\nallow other.example:443\n")
        conn = http.client.HTTPConnection("127.0.0.1", p.server_address[1], timeout=10)
        conn.set_debuglevel(0)
        conn.connect()
        conn.sock.sendall(b"CONNECT evil.example.com:443 HTTP/1.1\r\n"
                          b"Host: evil.example.com:443\r\n\r\n")
        status = conn.sock.recv(1024).decode("utf-8", "replace")
        conn.close()
        self.assertTrue(status.startswith("HTTP/1.1 403"), status)
        rows = self._log_rows()
        self.assertEqual(rows[0]["kind"], "connect")
        self.assertEqual(rows[0]["verdict"], "deny")

    def test_canary_alert_line(self):
        """canary 域 allow 后经代理触碰 → log 出 kind=canary 告警行（零容忍证据源）。"""
        acl = ("[acl]\ndefault deny\nallow canary.invalid:%d\n" % self.up_port
               + "[dns-pinning]\ndns-pin canary.invalid 127.0.0.1\n"
               + "[canary]\ncanary canary.invalid\n")
        p = self._proxy(acl)
        r, body = self._get_via_proxy(
            p.server_address[1],
            "http://canary.invalid:%d/touch" % self.up_port)
        self.assertEqual(r.status, 200, "pin 直连 127.0.0.1 → 上游可达")
        self.assertEqual(body, UP_BODY)
        kinds = [x["kind"] for x in self._log_rows()]
        self.assertIn("canary", kinds)
        self.assertIn("forward", kinds)

    def test_oob_logged(self):
        acl = ("[acl]\ndefault deny\nallow oob.invalid:%d\n" % self.up_port
               + "[dns-pinning]\ndns-pin oob.invalid 127.0.0.1\n"
               + "[oob]\noob oob.invalid\n")
        p = self._proxy(acl)
        r, _ = self._get_via_proxy(
            p.server_address[1], "http://oob.invalid:%d/cb" % self.up_port)
        self.assertEqual(r.status, 200)
        kinds = [x["kind"] for x in self._log_rows()]
        self.assertIn("oob", kinds)

    def test_dns_pin_mismatch_denied(self):
        """目标地址（IP 字面量）≠ pin 期望 → 拒绝 + pin_ok=False（DNS pin 执法面）。"""
        acl = ("[acl]\ndefault deny\nallow 127.0.0.1:%d\n" % self.up_port
               + "[dns-pinning]\ndns-pin 127.0.0.1 203.0.113.9\n")
        p = self._proxy(acl)
        r, _ = self._get_via_proxy(
            p.server_address[1], "http://127.0.0.1:%d/hello" % self.up_port)
        self.assertEqual(r.status, 403)
        rows = self._log_rows()
        self.assertEqual(rows[0]["verdict"], "deny")
        self.assertFalse(rows[0]["pin_ok"])

    def test_proxy_never_writes_tables(self):
        """代理运行时工件=egress-log.jsonl 一个文件（单写者纪律：13 表零触碰）。"""
        p = self._proxy("[acl]\ndefault deny\nallow 127.0.0.1:%d\n" % self.up_port)
        self._get_via_proxy(p.server_address[1],
                            "http://127.0.0.1:%d/hello" % self.up_port)
        d = self.td.name
        produced = sorted(os.listdir(d))
        self.assertEqual(produced, ["egress-log.jsonl"], produced)


if __name__ == "__main__":
    unittest.main()
