# -*- coding: utf-8 -*-
"""批次4 T6：重放门 eval——localhost mock 三态全链路（replay→set-replay-state→summary→P4 门）。

mock 目标（127.0.0.1 随机端口，授权内：scope include=127.0.0.0/8）：
  /ok      200 errorCode:00000 "total":42   → reproduced（VERIFIED 维持 C1）
  /drift   403                              → not-reproduced（REJECTED 降 C3）
  （第三个 EV 指向未监听端口）              → env-diff（REPAIRED 候选）

跨平台：socketserver/http.server+127.0.0.1 套接字非 POSIX-only（Windows 等价），
无诚实 skip 必要；测试入口一律 [sys.executable, <脚本路径>]（Windows 纪律）。

Ruling（计划↔实况裁决，详见 docs/HANDOFF.md 批次4 T6 节）：
- 计划 setUp 用 --matcher=127.0.0.1 授权 loopback——add-scope 的 _matcher_ok 冻结校验
  只认 CIDR/域名后缀/通配（裸 IP 字面量不是域名），改用语义等价的 CIDR 127.0.0.0/8
  （host_in_scope 经 _match_value CIDR 命中，授权意图不变）。
"""
import http.server, json, os, shutil, socketserver, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T09:30:00Z"


def call(cli, *args):
    return subprocess.run([sys.executable, cli] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/ok"):
            body = 'errorCode:00000 "total":42'
            self.send_response(200)
        else:
            body = "forbidden"
            self.send_response(403)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class TestReplayGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        # 授权 127.0.0.1（scope include 追加；Ruling：裸 IP 非 _matcher_ok 合法形，用等价 CIDR）+三张 EV 卡片
        self.call("add-scope", "--kind=include", "--matcher=127.0.0.0/8", "--timestamp=" + TS)
        self.evs = []
        for i, (path, m) in enumerate((("/ok", "word+status"), ("/drift", "status"), ("/gone", "word"))):
            r = self.call("add-evidence", "--title=重放%d" % i, "--source-type=command",
                          "--observed-at=" + TS, "--network-position=same-host",
                          "--repro-command=curl http://127.0.0.1:%d%s" % (self.port, path),
                          "--repro-kind=single", "--artifact=replay-art/%d.txt" % i,
                          "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            ev = r.stdout.splitlines()[0].split("\t")[1]
            card = os.path.join(self.gd, "evidence", ev + ".md")
            exp = ('---\nid: %s\nnetwork_position: same-host\nraw_request: |\n'
                   "  GET %s HTTP/1.1\n  Host: 127.0.0.1\nexpected:\n"
                   "  matchers:\n    - {type: word, words: [errorCode:00000]}\n"
                   "    - {type: status, status: [200]}\npair_group: \n---\n## 摘\n" % (ev, path))
            open(card, "w", encoding="utf-8", newline="\n").write(exp)
            self.evs.append(ev)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def call(self, cmd, *args):
        # argv 契约：--goal-dir 紧随命令名（tanyin-ledger main 冻结形态；T1/T2 同款 Ruling）
        return call(LEDGER, cmd, "--goal-dir", self.gd, *args)

    def replay(self, ev, port):
        return call(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                    "--scheme=http", "--port=%d" % port, "--timeout=3", "--timestamp=" + TS)

    def test_three_states_and_summary_green(self):
        v1 = json.loads(self.replay(self.evs[0], self.port).stdout.strip().splitlines()[-1])
        self.assertEqual(v1["verdict"], "reproduced")
        v2 = json.loads(self.replay(self.evs[1], self.port).stdout.strip().splitlines()[-1])
        self.assertEqual(v2["verdict"], "not-reproduced")
        v3 = json.loads(self.replay(self.evs[2], 1).stdout.strip().splitlines()[-1])
        self.assertEqual(v3["verdict"], "env-diff")
        # 三态落账（P4 子代理据此调用；本测试直接执行建议命令）
        for ev, st in ((self.evs[0], "VERIFIED"), (self.evs[1], "REJECTED"), (self.evs[2], "REPAIRED")):
            r = self.call("set-replay-state", "--id=" + ev, "--state=" + st)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.call("ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        # 链一致（request:/replay-probe 事件照常入链）
        self.assertEqual(self.call("verify-chain").returncode, 0)


if __name__ == "__main__":
    unittest.main()
