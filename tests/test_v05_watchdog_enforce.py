# -*- coding: utf-8 -*-
"""v0.5a F3/F4/F5：budget 执法化 + LOGONLY-ALIVE + ask:human 纯函数面（SRE/AI agent 项）。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import watchdog as wd  # noqa: E402

BUDGET_JSON = ('{"goal":{"budget":"2M;50000;40","limit":{"token":2000000,"requests":50000,'
               '"hours":40.0,"dollars":0.0},"used":{"token":20000,"requests":65,'
               '"hours":0.3,"dollars":0.0},"left":{"token":1980000.0}}}')


class TestBudgetEnforce(unittest.TestCase):
    def test_parse_usage(self):
        used, limit = wd.budget_usage(BUDGET_JSON)
        self.assertEqual(used["token"], 20000)
        self.assertEqual(limit["hours"], 40.0)

    def test_parse_bad_json_returns_none(self):
        self.assertIsNone(wd.budget_usage("not json"))

    def test_states(self):
        used = {"token": 100, "requests": 10, "hours": 1.0, "dollars": 0.0}
        limit = {"token": 1000, "requests": 100, "hours": 10.0, "dollars": 0.0}
        self.assertEqual(wd.budget_state(used, limit), "ok")
        used["token"] = 850
        self.assertEqual(wd.budget_state(used, limit), "warn")     # >80% 单维即 warn
        used["token"] = 1001
        self.assertEqual(wd.budget_state(used, limit), "over")     # 任一维超限=over
        used["token"] = 100
        used["hours"] = 10.5
        self.assertEqual(wd.budget_state(used, limit), "over")


class TestLogonlyAlive(unittest.TestCase):
    def test_is_logonly(self):
        self.assertTrue(wd.is_logonly(log_grew=True, tl_grew=False))
        self.assertFalse(wd.is_logonly(log_grew=True, tl_grew=True))
        self.assertFalse(wd.is_logonly(log_grew=False, tl_grew=False))

    def test_should_emit_once_per_round(self):
        self.assertTrue(wd.logonly_should_emit(already=False, logonly_sec=200, soft=180))
        self.assertFalse(wd.logonly_should_emit(already=True, logonly_sec=500, soft=180))
        self.assertFalse(wd.logonly_should_emit(already=False, logonly_sec=100, soft=180))


class TestAskHuman(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.d)

    def test_ask_detected(self):
        self.assertIsNone(wd.ask_question(os.path.join(self.d, "ask.md")))  # 缺文件
        p = os.path.join(self.d, "ask.md")
        open(p, "w", encoding="utf-8").write("凭据发放面在哪个服务？")
        self.assertEqual(wd.ask_question(p), "凭据发放面在哪个服务？")

    def test_wait_state(self):
        self.assertEqual(wd.wait_state(ask_pending=True, answered=False), "WAIT")
        self.assertEqual(wd.wait_state(ask_pending=True, answered=True), "RUN")
        self.assertEqual(wd.wait_state(ask_pending=False, answered=False), "RUN")


if __name__ == "__main__":
    unittest.main()
