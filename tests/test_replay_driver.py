# -*- coding: utf-8 -*-
"""批次4 T5：tanyin-replay 驱动——三态判定（R2/R3）+scope 门链+request 记账。

Ruling（计划↔实况裁决，详见 docs/HANDOFF.md 批次4 T5 节）：
- 夹具 G-g1 无 evidence/ 目录（计划注释称首行卡片在场）——测试内预铸卡片
  （Host=10.10.9.9 命中夹具 scope include 10.10.0.0/16：免 DNS、连接层失败确定）。
- 未知 EV id=退出 2（计划测试与骨架冲突，按「2=用法问题可重跑」口径取测试侧）。
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T09:00:00Z"


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def first_ev(self):
        p = os.path.join(self.gd, "E-index.tsv")
        return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l][0][0]

    def mint_card(self, host, path="/x"):
        """预铸 E-index 首行卡片（add-evidence 模板同构，network_position 与行同值）。"""
        ev = self.first_ev()
        card = os.path.join(self.gd, "evidence", ev + ".md")
        os.makedirs(os.path.dirname(card), exist_ok=True)
        open(card, "w", encoding="utf-8", newline="\n").write(
            "---\nid: %s\nnetwork_position: internet\nraw_request: |\n  GET %s HTTP/1.1\n"
            "  Host: %s\nexpected: {}\npair_group: \n---\n## 摘\n" % (ev, path, host))
        return ev


class TestReplayDriver(Base):
    def test_env_diff_on_connection_refused(self):
        ev = self.mint_card("10.10.9.9")
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                "--scheme=http", "--port=1", "--timeout=2", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(j["verdict"], "env-diff")
        self.assertIn("REPAIRED", j["suggest"])
        # 判定产物只增不覆盖（T6/T14 消费）+ timeline request: 记账（§4.10）
        self.assertTrue(os.path.exists(os.path.join(self.gd, "replay", ev, "1.json")))
        tl = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("request: 10.10.9.9/x via=replay", tl)
        self.assertIn("replay-probe %s verdict=env-diff" % ev, tl)

    def test_reject_out_of_scope_host(self):
        ev = self.mint_card("evil.outside")
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                "--scheme=http", "--timeout=2", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("scope", (r.stdout + r.stderr).lower())

    def test_unknown_id_exit_two(self):
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=EV-g1-9999")
        self.assertEqual(r.returncode, 2)

    def test_matcher_test_offline(self):
        exp = os.path.join(self.tmp, "exp.json")
        resp = os.path.join(self.tmp, "resp.txt")
        open(exp, "w", encoding="utf-8").write(json.dumps(
            {"matchers": [{"type": "status", "status": [200]}]}))
        open(resp, "w", encoding="utf-8").write("HTTP/1.1 200 OK\r\n\r\nok")
        r = run(REPLAY, "matcher-test", "--expected-file", exp, "--response-file", resp)
        self.assertEqual(r.returncode, 0)
        self.assertIn('"matched": true', r.stdout)


if __name__ == "__main__":
    unittest.main()
