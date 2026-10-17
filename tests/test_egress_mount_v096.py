# -*- coding: utf-8 -*-
"""SEC-2 舰 S2（v0.9.6 执法面升权批）：egress 实挂 TDD——runner 内嵌代理+env 强制
+request-ticket 机械记账（覆盖率 0%→机械强制）。

评审依据：docs/reviews/2026-10-15-direction-review/02-security-enforcement.md S2 节
（「Tier3 egress 代理全仓唯一消费者是 tests/」；修正方向：runner 内嵌起 EgressProxy，
强制子进程 env HTTP_PROXY/HTTPS_PROXY+NO_PROXY，随战斗生命周期开关）+
docs/superpowers/plans/2026-10-15-v096-enforcement.md SEC-2 舰条目 4。

红=ledger.egress_mount 模块不存在 + tanyin-egress selfcheck 不存在 + runner 无挂载接线。
机械性实证：客户端（外联工具替身 urllib）零配合——仅凭 runner 侧注入的代理 env，
allow 域放行、界外域 403，且每次判决自动铸 request-ticket 入 timeline（增量不重复）。
"""
import http.server, os, shutil, socketserver, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
EGRESS = os.path.join(CLI, "tanyin-egress")
LEDGER = os.path.join(CLI, "tanyin-ledger")
RUNNER = os.path.join(CLI, "tanyin-runner")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"

sys.path.insert(0, CLI)

FETCH = "import sys, urllib.request; urllib.request.urlopen(sys.argv[1], timeout=10)"


def run(*args, **kw):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", **kw)


class _Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.gd = os.path.join(self.tmp, "G-g1")
        shutil.copytree(FIX, self.gd)
        # 授权 loopback（mock 目标域；CIDR 语义等价 Ruling 同 test_replay_gate）
        r = run(LEDGER, "add-scope", "--goal-dir", self.gd, "--kind=include",
                "--matcher=127.0.0.0/8", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # compile 出真实 egress.acl（执法策略源=账本，非手写 ACL）
        r = run(EGRESS, "compile", "--goal-dir", self.gd, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def timeline(self):
        return open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()


class TestMount(Base):
    def test_mount_boots_and_forces_proxy_env(self):
        from ledger import egress_mount
        m = egress_mount.mount(self.gd)
        self.assertIsNotNone(m, "有 egress.acl 须挂载")
        self.addCleanup(m.shutdown)
        self.assertGreater(m.port, 0)
        env = m.env(no_proxy="::1,localhost")
        url = "http://127.0.0.1:%d/" % m.port
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            self.assertEqual(env[k], url, "子进程 env 须强制代理: " + k)
        self.assertEqual(env["NO_PROXY"], "::1,localhost")

    def test_no_acl_means_unmounted(self):
        from ledger import egress_mount
        os.remove(os.path.join(self.gd, "egress.acl"))
        self.assertIsNone(egress_mount.mount(self.gd), "无 compile 产物=不挂载（如实披露非静默拒）")

    def test_corrupt_acl_fails_closed(self):
        from ledger import egress_mount
        with open(os.path.join(self.gd, "egress.acl"), "w", encoding="utf-8") as f:
            f.write("wibble nonsense\n")
        with self.assertRaises(ValueError):
            egress_mount.mount(self.gd)


class TestMechanicalEnforcement(Base):
    """机械实证：env 强制的客户端零配合过 decide 四态；判决自动记 request-ticket。"""

    def setUp(self):
        super().setUp()
        self.srv = socketserver.TCPServer(("127.0.0.1", 0), _Ok)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(self.srv.server_close)

    def test_allow_deny_and_automatic_tickets(self):
        from ledger import egress_mount
        m = egress_mount.mount(self.gd)
        self.assertIsNotNone(m)
        self.addCleanup(m.shutdown)
        env = dict(os.environ, **m.env(no_proxy="::1,localhost"))
        # allow：授权域（127.0.0.0/8 include → allow）经代理实达 mock
        r1 = run("-c", FETCH, "http://127.0.0.1:%d/ok" % self.port, env=env)
        self.assertEqual(r1.returncode, 0, "allow 域须放行: %s%s" % (r1.stdout, r1.stderr))
        # deny：界外域默认拒（decide 先行，零 DNS 依赖）
        r2 = run("-c", FETCH, "http://evil.outside/x", env=env)
        self.assertNotEqual(r2.returncode, 0, "界外域须被代理拒")
        self.assertIn("403", r2.stderr, "代理判决=403: " + r2.stderr)
        # 自动记账：egress-log 增量 → timeline request-ticket（机械，不经战士手）
        n = m.poll_tickets(self.gd)
        self.assertEqual(n, 2, "两笔判决各铸一票: %d" % n)
        tl = self.timeline()
        self.assertIn("request-ticket egress verdict=allow kind=forward host=127.0.0.1", tl)
        self.assertIn("request-ticket egress verdict=deny kind=forward host=evil.outside", tl)
        # 增量不重复
        self.assertEqual(m.poll_tickets(self.gd), 0)
        # 记账入链（链完整——机械记账不破账本）
        self.assertEqual(run(LEDGER, "verify-chain", "--goal-dir", self.gd).returncode, 0)


class TestSelfcheck(Base):
    """安装/自检文档化（计划条目：文档化但不动 ZhuLong——8900 常驻不在作业面）。"""

    def test_selfcheck_ok_and_bad_acl(self):
        r = run(EGRESS, "selfcheck", "--acl", os.path.join(self.gd, "egress.acl"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)
        bad = os.path.join(self.tmp, "bad.acl")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("not-an-acl-line\n")
        r2 = run(EGRESS, "selfcheck", "--acl", bad)
        self.assertEqual(r2.returncode, 2, "坏 ACL 自检须 fail-closed: %s%s" % (r2.stdout, r2.stderr))


class TestRunnerWiring(Base):
    """runner 执行路径接线钉子（opencode 无法在测试面拉起——源级钉位同
    test_replay_timestamp.py::test_no_wallclock_in_replay_path 先例）。"""

    def test_runner_mounts_polls_and_shuts_down(self):
        src = open(RUNNER, encoding="utf-8").read()
        self.assertIn("egress_mount.mount(", src, "runner 须内嵌挂载 egress 代理")
        self.assertIn("poll_tickets", src, "runner 须轮询 egress-log 自动记 request-ticket")
        self.assertIn("EGRESS-MOUNT", src, "挂载状态须入 runner 日志（含 off 披露）")


if __name__ == "__main__":
    unittest.main()
