# -*- coding: utf-8 -*-
"""SEC-2 舰 S4（v0.9.6 执法面升权批）：replay 治理四门 TDD。

评审依据：docs/reviews/2026-10-15-direction-review/02-security-enforcement.md S4 节
（replay 无速率/无窗口/无危害分类；自带第二套 scope 实现）+
docs/superpowers/plans/2026-10-15-v096-enforcement.md SEC-2 舰条目 5：
授权时间窗检查+危险方法分类（非 GET 默认拒，--allow-method 显式开）+次数帽+
scope 判定吃 enforce.load_scope 单源（删第二套实现）。

红=四门皆缺：现状 replay 对超窗/非 GET/超帽全放行，且 scope 用 amendment_of
跳行的私有读法（与 enforce 同 matcher 后行覆盖语义在「修订行改 matcher」场景分歧）。
冒烟三实证（舰命）：非 GET 默认拒 / 超窗拒 / 超次数帽拒。
"""
import http.server, json, os, shutil, socketserver, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
REPLAY = os.path.join(CLI, "tanyin-replay")
LEDGER = os.path.join(CLI, "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"   # G-g1 授权窗 2026-09-01..2026-09-30 内
sys.path.insert(0, CLI)
from ledger.schemas import TABLES  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class _Postable(http.server.BaseHTTPRequestHandler):
    """mock 目标：GET/POST 皆 200 ok（POST 面为方法分类实证）。"""
    hits = []

    def _ok(self):
        _Postable.hits.append(self.command)
        body = "ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        self._ok()

    def do_POST(self):
        self._ok()

    def log_message(self, *a):
        pass


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.gd = os.path.join(self.tmp, "G-g1")
        shutil.copytree(FIX, self.gd)

    def first_ev(self):
        p = os.path.join(self.gd, "E-index.tsv")
        return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l][0][0]

    def mint_card(self, host, method="GET", path="/x"):
        ev = self.first_ev()
        card = os.path.join(self.gd, "evidence", ev + ".md")
        os.makedirs(os.path.dirname(card), exist_ok=True)
        open(card, "w", encoding="utf-8", newline="\n").write(
            "---\nid: %s\nnetwork_position: internet\nraw_request: |\n  %s %s HTTP/1.1\n"
            "  Host: %s\nexpected: {}\npair_group: \n---\n## 摘\n" % (ev, method, path, host))
        return ev

    def replay(self, ev, *extra):
        return run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                   "--scheme=http", "--timeout=2", "--timestamp=" + TS, *extra)

    def timeline(self):
        return open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()

    def _set_goal_bound(self, col, value):
        gi = TABLES["goals.tsv"].index(col)
        p = os.path.join(self.gd, "goals.tsv")
        rows = [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l]
        rows[0][gi] = value
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join("\t".join(r) for r in rows) + "\n")


class TestNonGetDefaultDeny(Base):
    """冒烟实证一：非 GET 默认拒；--allow-method 显式开。"""

    def setUp(self):
        super().setUp()
        # 授权 127.0.0.1（语义等价 CIDR，test_op2_ua 同款 Ruling）——方法门实证不与 scope 门混淆
        r = run(LEDGER, "add-scope", "--goal-dir", self.gd, "--kind=include",
                "--matcher=127.0.0.0/8", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _Postable.hits = []
        self.srv = socketserver.TCPServer(("127.0.0.1", 0), _Postable)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(self.srv.server_close)

    def test_post_default_deny_then_flag_opens(self):
        ev = self.mint_card("127.0.0.1", method="POST", path="/ok")
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                "--scheme=http", "--port=%d" % self.port, "--timeout=3",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, "非 GET 须默认拒: %s%s" % (r.stdout, r.stderr))
        self.assertIn("REJECT", r.stdout + r.stderr)
        self.assertIn("method", (r.stdout + r.stderr).lower())
        self.assertIn("REJECT=method", self.timeline())
        self.assertFalse(_Postable.hits, "拒绝后不得发包")
        self.assertFalse(os.path.exists(os.path.join(self.gd, "replay", ev)),
                         "拒绝不得落判定产物")
        # --allow-method=POST 显式开 → 放行且请求实达 mock
        r2 = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                 "--scheme=http", "--port=%d" % self.port, "--timeout=3",
                 "--timestamp=" + TS, "--allow-method=POST")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertIn("POST", _Postable.hits, "--allow-method=POST 须放行真实 POST")
        j = json.loads(r2.stdout.strip().splitlines()[-1])
        self.assertEqual(j["verdict"], "manual")   # expected 空 → manual（放行非判真）


class TestAuthzWindow(Base):
    """冒烟实证二：超窗拒（申报钟 --timestamp 出 [valid_from,valid_until] 即 REJECT）。"""

    def test_expired_window_rejects(self):
        self._set_goal_bound("valid_until", "2026-08-31")
        ev = self.mint_card("10.10.9.9")
        r = self.replay(ev, "--port=1")
        self.assertEqual(r.returncode, 1, "授权窗已过须拒: %s%s" % (r.stdout, r.stderr))
        self.assertIn("授权窗", r.stdout + r.stderr)
        self.assertIn("REJECT=authz-window", self.timeline())
        self.assertNotIn("replay-probe", self.timeline(), "超窗不得产探针事件")

    def test_not_started_window_rejects(self):
        self._set_goal_bound("valid_from", "2026-10-01")
        ev = self.mint_card("10.10.9.9")
        r = self.replay(ev, "--port=1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("授权窗", r.stdout + r.stderr)
        self.assertIn("REJECT=authz-window", self.timeline())

    def test_in_window_still_replays(self):
        ev = self.mint_card("10.10.9.9")
        r = self.replay(ev, "--port=1")
        self.assertEqual(r.returncode, 0, "窗内（date-only 止日含当日）不得误拒: %s%s"
                         % (r.stdout, r.stderr))

    def test_bad_bound_fail_closed(self):
        self._set_goal_bound("valid_until", "not-a-date")
        ev = self.mint_card("10.10.9.9")
        r = self.replay(ev, "--port=1")
        self.assertEqual(r.returncode, 1, "坏边界须 fail-closed 拒")
        self.assertIn("REJECT=authz-window", self.timeline())


class TestReplayCap(Base):
    """冒烟实证三：超次数帽拒——单 EV 判定产物满 3 份后第 4 次机械拒。"""

    def test_fourth_replay_rejected(self):
        ev = self.mint_card("10.10.9.9")
        for i in (1, 2, 3):
            r = self.replay(ev, "--port=1")
            self.assertEqual(r.returncode, 0, "第 %d 次须放行: %s%s" % (i, r.stdout, r.stderr))
            self.assertTrue(os.path.exists(os.path.join(self.gd, "replay", ev, "%d.json" % i)))
        r4 = self.replay(ev, "--port=1")
        self.assertEqual(r4.returncode, 1, "第 4 次须拒（次数帽）: %s%s" % (r4.stdout, r4.stderr))
        self.assertIn("次数帽", r4.stdout + r4.stderr)
        self.assertIn("REJECT=replay-cap", self.timeline())
        self.assertFalse(os.path.exists(os.path.join(self.gd, "replay", ev, "4.json")),
                         "超帽不得再落判定产物")


class TestScopeSingleSource(Base):
    """scope 单源：判定吃 enforce.load_scope（同 matcher 后行覆盖），
    第二套 amendment_of 跳行读法退役——修订行新增 matcher 不撤销原行。"""

    def test_amendment_with_new_matcher_keeps_original(self):
        # 追加修订行：include 10.99.0.0/16 amendment_of=S-g1-0002（原 include 10.10.0.0/16）
        # 旧私有读法：S-g1-0002 被跳行 → 10.10.9.9 界外 REJECT；
        # enforce 单源：两 matcher 并存生效 → 10.10.9.9 界内放行。
        p = os.path.join(self.gd, "scope.tsv")
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(["S-g1-9001", "include", "10.99.0.0/16", "", "",
                                "S-g1-0002", "修订扩段（单源钉子）", "2",
                                "2026-09-24T00:00:00Z"]) + "\n")
        ev = self.mint_card("10.10.9.9")
        r = self.replay(ev, "--port=1")
        self.assertEqual(r.returncode, 0, "enforce 单源语义下原 matcher 行仍生效: %s%s"
                         % (r.stdout, r.stderr))
        tl = self.timeline()
        self.assertIn("request: 10.10.9.9/x via=replay", tl)
        self.assertNotIn("REJECT=out-of-scope", tl)


if __name__ == "__main__":
    unittest.main()
