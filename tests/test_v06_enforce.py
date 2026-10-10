# -*- coding: utf-8 -*-
"""v0.6 H1/H2/H3：预算门禁红线/多 EV 危害行/精确 McNemar。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import report_render  # noqa: E402

_spec = importlib_util = None
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "rerun", os.path.join(ROOT, "scripts", "rerun.py"))
rerun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerun)

FIX = os.path.join(ROOT, "tests", "fixtures", "G-g1")


def run_gate(d, phase="P4"):
    # 夹具已焙进 P0-P3 门事件（不可剥：断链）；P4=未过门，真跑断言链
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli", "tanyin-phases"), "gate",
         "--goal-dir", d, "--phase=" + phase,
         "--timestamp=2026-10-24T09:00:00Z"],
        capture_output=True, text=True, timeout=60)


def _fresh(d):
    """占位（历史：曾剥门事件——断哈希链，弃）；夹具门事件不可动。"""
    return d


class TestH1BudgetGateLine(unittest.TestCase):
    def test_gate_pass_with_budget_rows(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(FIX, d, dirs_exist_ok=True)
            _fresh(d)
            r = run_gate(d)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_gate_fail_budget_not_minted(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(FIX, d, dirs_exist_ok=True)
            _fresh(d)
            with open(os.path.join(d, "budget.tsv"), "w", encoding="utf-8") as f:
                f.write("")   # b27 实锤场景：全程不铸
            r = run_gate(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("budget-not-minted", r.stdout)
            tl = open(os.path.join(d, "timeline.tsv"), encoding="utf-8").read()
            self.assertIn("gate-fail:P4 assert=budget", tl)


class TestH2MultiEvHarmLines(unittest.TestCase):
    def test_all_ev_excerpts_listed(self):
        lines = report_render._harm_lines([
            ("EV-1", "echo x"), ("EV-2", ""), ("EV-3", "syntax error")])
        self.assertEqual(len(lines), 2)
        self.assertIn("EV-1", lines[0])
        self.assertIn("EV-3", lines[1])

    def test_none_returns_empty(self):
        self.assertEqual(report_render._harm_lines([("EV-1", "")]), [])


class TestH3Mcnemar(unittest.TestCase):
    def test_no_discordant(self):
        self.assertEqual(rerun.mcnemar_exact(0, 0), 1.0)

    def test_strong_signal(self):
        self.assertLess(rerun.mcnemar_exact(8, 0), 0.01)

    def test_weak_signal(self):
        self.assertGreater(rerun.mcnemar_exact(3, 4), 0.5)


if __name__ == "__main__":
    unittest.main()
