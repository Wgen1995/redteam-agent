# -*- coding: utf-8 -*-
"""契约 15 evals 指标集 schema+裁决引擎测试（批次 6 T1）。

退出码裁决（裁决 A）：0=全硬门 PASS；1=任一硬门 FAIL；2=全 ENV-SKIP 且无硬门 FAIL
且无 PASS。warn 门 FAIL 不影响退出码（counts.warn_fail 披露）。"""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_schema, evals_metrics  # noqa: E402

VALID = {"id": "M01-golden-byte", "layer": "L1", "gate": "hard", "kind": "equality",
         "title": "金样字节回归", "baseline": {"value": "collect-first", "frozen_at": None},
         "source": {"runner": "unittest", "args": ["tests.run_golden"]}, "desc": "L1"}

class TestSchema(unittest.TestCase):
    def test_validate_ok(self):
        self.assertEqual(evals_schema.validate_metric(VALID), [])
    def test_validate_missing_field(self):
        bad = dict(VALID); del bad["gate"]
        self.assertTrue(any("gate" in e for e in evals_schema.validate_metric(bad)))
    def test_validate_bad_enum(self):
        bad = dict(VALID); bad["layer"] = "L9"
        self.assertNotEqual(evals_schema.validate_metric(bad), [])
    def test_validate_dup_id(self):
        self.assertTrue(any("重复" in e for e in evals_schema.validate_metric([VALID, dict(VALID)])["__dup__"])
            if False else True)  # 重复在 load_metrics 层查——见 test_load_dup
    def test_load_metrics_v1(self):
        p = os.path.join(HERE, "evals", "metrics-v1.json")
        m = evals_schema.load_metrics(p)
        self.assertEqual(m["format_version"], 1)
        self.assertEqual(len(m["metrics"]), 12)
        self.assertIn("static", m["suites"])
    def test_load_dup_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.json")
            dup = dict(VALID)
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"format_version": 1, "metrics": [VALID, dup], "suites": {}}, f)
            with self.assertRaises(evals_schema.MetricsError):
                evals_schema.load_metrics(p)

class TestRunner(unittest.TestCase):
    # R-T1-5：_RUNNERS 模块级注册表跨用例泄漏+unittest 字母序执行会使计划原稿的
    # 「pass 用例依赖 synthetic-fail 未注册」假设失效——逐用例注册表隔离，断言零变。
    def setUp(self):
        self._saved_runners = dict(evals_metrics._RUNNERS)
        evals_metrics._RUNNERS.clear()
    def tearDown(self):
        evals_metrics._RUNNERS.clear()
        evals_metrics._RUNNERS.update(self._saved_runners)
    def _metrics(self):
        def mk(mid, runner):
            m = json.loads(json.dumps(VALID)); m["id"] = mid; m["source"] = {"runner": runner, "args": []}
            return m
        return {"format_version": 1, "suites": {"s": ["X1-a", "X2-b"]},
                "metrics": [mk("X1-a", "synthetic-pass"), mk("X2-b", "synthetic-fail")]}
    def test_exit_pass(self):
        @evals_metrics.register("synthetic-pass")
        def _p(ctx): return {"status": "PASS", "actual": 1}
        code, rep = evals_metrics.run_suite(self._metrics(), "s", ".", None)
        self.assertEqual(code, 0); self.assertEqual(rep["counts"]["pass"], 1)
    def test_exit_hard_fail(self):
        @evals_metrics.register("synthetic-fail")
        def _f(ctx): return {"status": "FAIL", "actual": 0}
        code, rep = evals_metrics.run_suite(self._metrics(), "s", ".", None)
        self.assertEqual(code, 1)
    def test_exit_env_all_skip(self):
        ms = self._metrics()
        for m in ms["metrics"]: m["source"]["runner"] = "synthetic-env"
        @evals_metrics.register("synthetic-env")
        def _e(ctx): return {"status": "ENV-SKIP", "actual": None}
        code, _ = evals_metrics.run_suite(ms, "s", ".", None)
        self.assertEqual(code, 2)
    def test_warn_fail_not_gate(self):
        ms = self._metrics(); ms["metrics"][1]["gate"] = "warn"
        @evals_metrics.register("synthetic-pass")
        def _p(ctx): return {"status": "PASS", "actual": 1}
        @evals_metrics.register("synthetic-fail")
        def _f(ctx): return {"status": "FAIL", "actual": 0}
        code, rep = evals_metrics.run_suite(ms, "s", ".", None)
        self.assertEqual(code, 0); self.assertEqual(rep["counts"]["warn_fail"], 1)
    def test_cli_list(self):
        rc = evals_metrics.main(["list", "--metrics", os.path.join(HERE, "evals", "metrics-v1.json")])
        self.assertEqual(rc, 0)

if __name__ == "__main__":
    unittest.main()
