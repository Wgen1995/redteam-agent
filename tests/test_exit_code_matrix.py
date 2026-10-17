# -*- coding: utf-8 -*-
"""W2 退出码分离：evals 裁决引擎第 4 态 rc3=仅未验证候选（D 舰 G4 缺口）。

矩阵（裁决优先级：硬门 FAIL > 全 ENV-SKIP > 仅候选黄灯 > 干净绿）：
  rc1=任一硬门 FAIL（候选并存不改判）
  rc2=零 PASS 全 ENV-SKIP（候选并存不改判——环境前置缺不得伪装黄灯）
  rc3=硬门全过+有 PASS+存在未验证候选（CI 黄灯：跑了但有候选没实证，不静默绿）
  rc0=硬门全过+有 PASS+零候选
warn 门 FAIL 不影响退出码（既有口径）；evals_metrics.py 契约行（docstring）同步
0/1/2/3。runners 注册表逐用例隔离（test_evals_schema R-T1-5 同律）。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import evals_metrics  # noqa: E402


def _metric(mid, runner):
    return {"id": mid, "layer": "L2", "gate": "hard", "kind": "threshold",
            "title": mid, "baseline": {"value": "collect-first", "frozen_at": None},
            "source": {"runner": runner, "args": []}, "desc": "matrix"}


def _suite(*metrics):
    return {"format_version": 1, "suites": {"s": [m["id"] for m in metrics]},
            "metrics": list(metrics)}


class TestSuiteExitMatrix(unittest.TestCase):
    def setUp(self):
        self._saved = dict(evals_metrics._RUNNERS)
        evals_metrics._RUNNERS.clear()

    def tearDown(self):
        evals_metrics._RUNNERS.clear()
        evals_metrics._RUNNERS.update(self._saved)

    def _reg(self, name, status, candidates=None):
        @evals_metrics.register(name)
        def _r(ctx):
            out = {"status": status, "actual": name}
            if candidates is not None:
                out["candidates"] = candidates
            return out

    def test_hard_fail_beats_candidates_and_env(self):
        self._reg("m-pass", "PASS")
        self._reg("m-cand", "PASS", candidates=3)
        self._reg("m-env", "ENV-SKIP")
        self._reg("m-fail", "FAIL")
        code, rep = evals_metrics.run_suite(_suite(_metric("A", "m-pass"),
                                                   _metric("B", "m-cand"),
                                                   _metric("C", "m-env"),
                                                   _metric("D", "m-fail")), "s", ".", None)
        self.assertEqual(code, 1)
        self.assertEqual(rep["exit"], 1)

    def test_all_env_skip_is_rc2_even_with_candidates(self):
        self._reg("m-env", "ENV-SKIP", candidates=2)
        code, _ = evals_metrics.run_suite(_suite(_metric("A", "m-env")), "s", ".", None)
        self.assertEqual(code, 2)

    def test_pass_with_only_unverified_candidates_is_rc3(self):
        self._reg("m-pass", "PASS")
        self._reg("m-cand", "PASS", candidates=2)
        code, rep = evals_metrics.run_suite(_suite(_metric("A", "m-pass"),
                                                   _metric("B", "m-cand")), "s", ".", None)
        self.assertEqual(code, 3, "仅未验证候选=CI 黄灯 rc3（G4：不静默绿）")
        self.assertEqual(rep["counts"]["candidates"], 2)
        self.assertEqual(rep["exit"], 3)

    def test_clean_pass_stays_rc0(self):
        self._reg("m-pass", "PASS")
        self._reg("m-zero", "PASS", candidates=0)
        code, rep = evals_metrics.run_suite(_suite(_metric("A", "m-pass"),
                                                   _metric("B", "m-zero")), "s", ".", None)
        self.assertEqual(code, 0)

    def test_warn_fail_with_candidates_is_rc3(self):
        ms = _metric("W", "m-wfail")
        ms["gate"] = "warn"
        self._reg("m-wfail", "FAIL")
        self._reg("m-cand", "PASS", candidates=1)
        code, rep = evals_metrics.run_suite(_suite(ms, _metric("B", "m-cand")), "s", ".", None)
        self.assertEqual(code, 3, "warn 门 FAIL 不升 rc1（既有口径），候选黄灯照报")
        self.assertEqual(rep["counts"]["warn_fail"], 1)

    def test_contract_line_synced_to_four_states(self):
        doc = evals_metrics.__doc__ or ""
        self.assertIn("0/1/2/3", doc, "契约行（docstring）须载 0/1/2/3 四态")
        self.assertIn("仅未验证候选", doc, "rc3 语义须在契约行在册（D 舰 G4：evals_metrics.py:2 同步）")


if __name__ == "__main__":
    unittest.main()
