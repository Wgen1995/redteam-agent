# tests/test_evals_dynamic.py
# -*- coding: utf-8 -*-
"""T3 动态指标：token 效率实采（G-11）/重放三态裁决/动态 runner 注册面（批次 6）。"""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_metrics, evals_token_eff  # noqa: E402


class TestTokenEff(unittest.TestCase):
    ROWS = [  # timeline usage 行样本——列序=TABLES["timeline.tsv"] 实形（R-T3-1：event=index 3）
        ["2026-09-24T00:00:00Z", "总控", "P3", "usage: run=r1 tokens=1000 est_tokens=1250",
         "", "0" * 64, "a" * 64, "2"],
        ["2026-09-24T00:01:00Z", "总控", "P3", "usage: run=r2 tokens=900 est_tokens=1250",
         "", "a" * 64, "b" * 64, "2"],
    ]

    def test_ratio_rows(self):
        ratios = evals_token_eff.extract_ratios(self.ROWS)
        self.assertEqual(ratios, [1000 / 1250, 900 / 1250])

    def test_no_rows_is_env(self):
        with self.assertRaises(EnvironmentError):
            evals_token_eff.extract_ratios([])

    def test_cmd_idx_pinned_to_schema(self):
        # R-T3-1：cmd_idx 以 schemas 单源钉死；schema 错位=本断言红（计划「错位=断言红」兑现）
        from ledger.schemas import TABLES
        self.assertEqual(evals_token_eff._CMD_IDX, TABLES["timeline.tsv"].index("event"))
        self.assertEqual(evals_token_eff._CMD_IDX, 3)

    def test_calibration_report_written(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "calib.json")
            rep = evals_token_eff.write_calibration([0.8, 0.72], out)
            self.assertEqual(rep["n"], 2)
            self.assertTrue(0.7 < rep["median"] < 0.8)
            self.assertIn("proposal", rep)  # 契约 v3 系数候选文本在
            self.assertTrue(os.path.exists(out))


class TestDynamicRunners(unittest.TestCase):
    def test_registered(self):
        for name in ("canary-zero", "replay-rate", "token-usage", "manual"):
            self.assertIn(name, evals_metrics._RUNNERS)

    def test_manual_env_skip(self):
        r = evals_metrics._RUNNERS["manual"]({"goal_dir": ".", "args": [], "ts": "t", "metric": {}})
        self.assertEqual(r["status"], "ENV-SKIP")

    def test_canary_zero_all_tiers(self):
        # 夹具 G-g1 复制到临时目录后逐档 probe；docker/网络不敏感（probe=诱饵触探，本地落账）
        import shutil
        src = os.path.join(HERE, "fixtures", "G-g1")
        if not os.path.isdir(src):
            self.skipTest("G-g1 夹具缺")
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(src, os.path.join(d, "g"))
            r = evals_metrics._RUNNERS["canary-zero"]({
                "goal_dir": os.path.join(d, "g"), "args": [], "ts": "2026-09-24T00:00:00Z", "metric": {}})
            self.assertIn(r["status"], ("PASS", "ENV-SKIP"))  # 依赖 canary 组件在位（R-T3-3：未部署=ENV-SKIP）

    def test_replay_rate_parse(self):
        states = ["reproduced", "reproduced", "env-diff"]
        self.assertEqual(evals_token_eff.replay_verdict(states),
                         ("PASS", {"reproduced": 2, "env-diff": 1, "unhandled": 0}))
        self.assertEqual(evals_token_eff.replay_verdict(["not-reproduced"])[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
