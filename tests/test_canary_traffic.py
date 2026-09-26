# -*- coding: utf-8 -*-
"""批次 6 T11：canary 流量级验证链（egress-log 双源+R10 误报校准口径，TDD 红→绿）。

断言面：
- 经代理触 canary 域 → egress-log kind=canary 行 → probe --tier 3 --egress-log 判触碰
  （rc!=0，输出含诱饵域+流量证据）——流量级证据源并入零容忍判定；
- R10 反例（误报校准）：不经代理的同域裸连接（无 log 行）不触发——判定只认
  egress-log kind=canary 行；未部署诱饵的外来 canary 行（他进程共享环境）不误报；
- 回归：不给 --egress-log → 行为与现状逐字节一致（既有 canary 测试面零漂移）。
触碰绑定口径（R10）：host 命中本交战已部署诱饵表 ∧ 行 ts ≥ 最近 canary-deploy 事件 ts
（两侧皆 ISO 形态才比对；不可比=不过滤并如实计数）。
"""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import egress_proxy  # noqa: E402

CANARY_CLI = os.path.join(REPO, "cli", "tanyin-canary")
TS_DEPLOY = "2026-09-26T00:00:00Z"
TS_TOUCH = "2026-09-26T01:00:00Z"
TS_PROBE = "2026-09-26T02:00:00Z"
ENV = {**os.environ, "PYTHONUTF8": "1"}
UP_BODY = b"up-ok"


class _Up(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(UP_BODY)))
        self.end_headers()
        self.wfile.write(UP_BODY)

    def log_message(self, *a):
        pass


def _goal_with_deploy():
    """G-g1 拷贝（共享夹具零触碰）+确定性 deploy；返回 (gd, 首个域名诱饵, 日志路径)。"""
    gd = tempfile.mkdtemp(prefix="t11-")
    shutil.copytree(os.path.join(HERE, "fixtures", "G-g1"), gd,
                    dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    r = subprocess.run([sys.executable, CANARY_CLI, "deploy", "--goal-dir", gd,
                        "--seed=t11traffic", "--timestamp=" + TS_DEPLOY],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENV, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    with open(os.path.join(gd, "canary", "targets.tsv"), encoding="utf-8") as f:
        rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    decoy = next(v for k, v in ((r[0], r[1]) for r in rows) if v.endswith(".tanyin-test"))
    return gd, decoy, os.path.join(gd, "egress-log.jsonl")


def _probe(gd, extra):
    # canary 既有参数面=--key=value 形态（cmd_probe kv 字典解析）
    r = subprocess.run([sys.executable, CANARY_CLI, "probe", "--goal-dir", gd,
                        "--tier=3", "--timestamp=" + TS_PROBE] + extra,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENV, timeout=300)
    return r


class TestTrafficLevel(unittest.TestCase):
    def setUp(self):
        self._tmp = []
        self.up = ThreadingHTTPServer(("127.0.0.1", 0), _Up)
        threading.Thread(target=self.up.serve_forever, daemon=True).start()
        self.up_port = self.up.server_address[1]

    def tearDown(self):
        self.up.shutdown()
        self.up.server_close()
        for s in getattr(self, "_servers", []):
            try:
                s.server_close()
            except OSError:
                pass
        for p in self._tmp:
            shutil.rmtree(p, ignore_errors=True)

    def _proxy_touch(self, decoy, log_path):
        """起代理（canary 域 allow+pin 直连）→ 经代理触诱饵 → 返回代理端口。"""
        acl = ("[acl]\ndefault deny\nallow %s:%d\n" % (decoy, self.up_port)
               + "[dns-pinning]\ndns-pin %s 127.0.0.1\n" % decoy
               + "[canary]\ncanary %s\n" % decoy)
        httpd = egress_proxy.serve_text(acl, port=0, egress_log=log_path, now=TS_TOUCH)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self._servers = getattr(self, "_servers", []) + [httpd]
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1],
                                          timeout=10)
        conn.request("GET", "http://%s:%d/touch" % (decoy, self.up_port))
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 200, "pin 直连可达上游（触碰成立前提）")
        return httpd

    def test_touch_via_proxy_detected(self):
        gd, decoy, log_path = _goal_with_deploy()
        self._proxy_touch(decoy, log_path)
        for s in getattr(self, "_servers", []):
            s.shutdown()
            s.server_close()
        self.up.shutdown()
        self.up.server_close()
        r = _probe(gd, ["--egress-log=" + log_path])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["status"], "fail")
        self.assertGreaterEqual(out.get("traffic_touches", 0), 1)
        hit = [d for d in out["detail"] if d["value"] == decoy]
        self.assertTrue(hit and hit[0]["verdict"] == "allowed" and hit[0].get("traffic"),
                        out["detail"])
        self.assertIn(decoy, r.stdout)

    def test_non_proxy_connection_not_flagged(self):
        """R10 反例：同域裸 socket 连接不经代理（零 log 行）→ probe 不误报 rc==0。"""
        gd, decoy, log_path = _goal_with_deploy()
        s = socket.create_connection(("127.0.0.1", self.up_port), timeout=5)
        s.sendall(b"GET / HTTP/1.0\r\n\r\n")
        s.recv(1024)
        s.close()
        self.assertFalse(os.path.exists(log_path), "裸连接绝不产生 egress-log 行")
        # acl 静态面在场（诱饵不在白名单=blocked），log 缺=无流量触碰 → pass
        with open(os.path.join(gd, "egress.acl"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("[acl]\ndefault deny\nallow other.example\n")
        r = _probe(gd, ["--egress-log=" + log_path])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "pass")

    def test_foreign_canary_rows_ignored(self):
        """R10 绑定：log 中他进程的外来 canary 行（host 不在诱饵表）不并入判定。"""
        gd, decoy, log_path = _goal_with_deploy()
        with open(log_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"ts": TS_TOUCH, "verdict": "allow",
                                "host": "canary.evil.example", "port": 443,
                                "kind": "canary", "pin_ok": None}) + "\n")
        r = _probe(gd, ["--egress-log=" + log_path])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["traffic_touches"], 0)

    def test_touch_before_deploy_window_ignored(self):
        """R10 时间窗：deploy 之前的 canary 行（不可归因本次交战触碰）不并入判定。"""
        gd, decoy, log_path = _goal_with_deploy()
        with open(log_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"ts": "2026-09-25T00:00:00Z", "verdict": "allow",
                                "host": decoy, "port": 443,
                                "kind": "canary", "pin_ok": None}) + "\n")
        r = _probe(gd, ["--egress-log=" + log_path])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_probe_without_log_backcompat(self):
        """回归：不给 --egress-log → 现状行为（缺 acl=not-deployed exit 0；零漂移）。"""
        gd, _decoy, _log = _goal_with_deploy()
        self._tmp.append(gd)
        r = _probe(gd, [])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "not-deployed")


if __name__ == "__main__":
    unittest.main()
