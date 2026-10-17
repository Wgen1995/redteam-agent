# -*- coding: utf-8 -*-
"""战士运行时·入口（W5 战士 MVP）。

python3 -m cli.warrior --goal-dir D --battle-name X --max-intents N
  [--dry-run] [--channels PATH.json] [--warrior-id W-1] [--lease-min 30]
  [--token-cap N] [--time-window-min N] [--heartbeat-min 5]
  [--stall-min 15] [--ctx-tokens 24000] [--max-turns 6]
  [--respawn-max 2] [--skill PATH] [--tools-state PATH]

退出码：0=优雅停（含 no-intents/budget-cap/time-window/stop-signal/
max-intents）；2=用法/环境；3=停滞重生耗尽；1=异常。
模型面测试=本地假模型服务（动态口），绝不真调外部 API。

跑法：python3 -m unittest tests.test_warrior_main -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cli"))

from warrior import __main__ as wmain  # noqa: E402
from tests.test_warrior_fake_model import FakeModelServer  # noqa: E402

class _FakeLoop(object):
    """重生单测假循环：run() 返回预设战报。"""

    def __init__(self, status):
        self.status = status

    def run(self):
        rep = wmain.loop_mod.RunReport()
        rep.status = self.status
        rep.stop_detail = "fake"
        return rep


FACT = ('{"op":"ledger","cmd":"add-fact","args":{"intent-id":"INT-g1-0002",'
        '"kind":"info","target":"shop.example",'
        '"detail":"入口 E2E 观察","confidence":"0.6"}}')
DONE = '{"op":"done","reason":"入口链路通"}'


class TestMainUnit(unittest.TestCase):
    def test_parse_args_minimal(self):
        a = wmain.parse_args(["--goal-dir", "/g", "--battle-name", "B",
                              "--max-intents", "3", "--channels", "/c.json"])
        self.assertEqual(a["goal_dir"], "/g")
        self.assertEqual(a["battle_name"], "B")
        self.assertEqual(a["max_intents"], 3)
        self.assertFalse(a["dry_run"])
        self.assertEqual(a["respawn_max"], 2)

    def test_parse_args_usage_errors(self):
        for argv in ([], ["--goal-dir", "/g"], ["--goal-dir", "/g",
                                                "--battle-name", "B"]):
            with self.assertRaises(SystemExit) as cm:
                wmain.parse_args(argv)
            self.assertEqual(cm.exception.code, 2)

    def test_respawn_rebuilds_loop_until_graceful(self):
        made = []

        def factory(i):
            made.append(i)
            return _FakeLoop("stalled" if i < 3 else "no-intents")
        rc = wmain.run_with_respawn(factory, respawn_max=5)
        self.assertEqual(rc, 0)
        self.assertEqual(len(made), 4, "3 次停滞重生后第 4 脑收敛")

    def test_respawn_exhausted_exits_three(self):
        rc = wmain.run_with_respawn(lambda i: _FakeLoop("stalled"),
                                    respawn_max=2)
        self.assertEqual(rc, 3, "停滞重生耗尽=退出码 3")


class TestMainSubprocess(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, "-m", "cli.warrior",
             "--goal-dir", self.gd, "--battle-name", "B-x",
             "--max-intents", "1"] + list(extra),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=ROOT, timeout=60)

    def test_usage_error_exit_two(self):
        r = subprocess.run([sys.executable, "-m", "cli.warrior"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT, timeout=60)
        self.assertEqual(r.returncode, 2)
        self.assertIn("用法", r.stderr)

    def test_missing_goal_dir_exit_two(self):
        r = self._run("--channels", "/nonexistent.json")
        self.assertEqual(r.returncode, 2)

    def test_dry_run_prints_context_without_writes(self):
        before = open(os.path.join(self.gd, "timeline.tsv"),
                      encoding="utf-8").read()
        r = self._run("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("admin 面板", r.stdout)
        after = open(os.path.join(self.gd, "timeline.tsv"),
                     encoding="utf-8").read()
        self.assertEqual(before, after, "dry-run 零账本写")

    def test_full_run_via_entry_with_fake_model(self):
        srv = FakeModelServer()
        self.addCleanup(srv.stop)
        srv.set_scripts({"m1": [{"content": FACT}, {"content": DONE}]})
        cpath = os.path.join(self.gd, "..",
                             os.path.basename(self.gd) + "-ch.json")
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump([{"name": "m1", "model": "m1",
                        "base_url": srv.base, "api_key": "k"}], f)
        r = self._run("--channels", cpath, "--token-cap", "100000")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        rows = [l.split("\t") for l in open(
            os.path.join(self.gd, "intents.tsv"), encoding="utf-8")
            if l.strip()]
        self.assertEqual(rows[-1][3], "done")
        facts = [l for l in open(os.path.join(self.gd, "facts.tsv"),
                                 encoding="utf-8") if "入口 E2E" in l]
        self.assertEqual(len(facts), 1, "模型 add-fact 指令经入口落账")


if __name__ == "__main__":
    unittest.main()
