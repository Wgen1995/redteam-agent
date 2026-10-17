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
import subprocess  # noqa: E402
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


TAB = chr(9)
FIX = os.path.join(HERE, "fixtures", "G-g1")
FINDINGS_COLS = 19


def _finding(fid, exploit, status="active"):
    row = [""] * FINDINGS_COLS
    row[0], row[1], row[2] = fid, "INT-g1-0001", "矩阵用发现"
    row[3], row[4], row[5] = "C2", "中", exploit
    row[15] = "findings-cards/%s.md" % fid
    row[16] = status
    row[17] = "2"
    row[18] = "2026-10-17T00:00:00Z"
    return TAB.join(row)


def _goal_with_findings(td, exploits):
    import shutil
    gd = os.path.join(td, "g-" + "-".join(e or "empty" for e in exploits))
    shutil.copytree(FIX, gd)
    rows = [_finding("FD-m-%02d" % i, e) for i, e in enumerate(exploits, 1)]
    with open(os.path.join(gd, "findings.tsv"), "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("".join(r + chr(10) for r in rows))
    return gd


class TestFindingCandidatesRunner(unittest.TestCase):
    """rc3 数据源：finding-candidates runner——账本 active 发现但零 verified（G4 原文）。

    findings.tsv 单源：live=status 非 superseded；verified=exploitation_status
    =="verified"（projections 同口径）；候选=live 且非 verified/ruled_out。
    verified>0 → 候选不报（「仅候选」态不成立；pending 重放义务归 M02 硬门）。"""

    def _ctx(self, goal_dir):
        return {"goal_dir": goal_dir, "args": [], "ts": "2026-10-17T00:00:00Z", "metric": {}}

    def test_only_unverified_reports_candidates(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gd = _goal_with_findings(td, ["suspected", ""])
            out = evals_metrics._RUNNERS["finding-candidates"](self._ctx(gd))
            self.assertEqual(out["status"], "PASS")
            self.assertEqual(out["candidates"], 2, "active 且零 verified=候选全报: %s" % out["actual"])

    def test_verified_present_zero_candidates(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gd = _goal_with_findings(td, ["verified", "suspected"])
            out = evals_metrics._RUNNERS["finding-candidates"](self._ctx(gd))
            self.assertEqual(out["candidates"], 0,
                             "verified 在档→非「仅候选」态: %s" % out["actual"])
            self.assertIn("verified=1", out["actual"])

    def test_superseded_not_candidate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gd = _goal_with_findings(td, ["suspected"])
            with open(os.path.join(gd, "findings.tsv"), "a", encoding="utf-8") as f:
                pass
            out = evals_metrics._RUNNERS["finding-candidates"](self._ctx(gd))
            self.assertEqual(out["candidates"], 1)
            # 全 superseded→零 live→零候选（vacuous 绿不在此 runner 面：空账本归 ENV 面）
            gd2 = _goal_with_findings(td, [])
            with open(os.path.join(gd2, "findings.tsv"), "a", encoding="utf-8") as f:
                f.write(_finding("FD-m-99", "verified", status="superseded") + chr(10))
            out2 = evals_metrics._RUNNERS["finding-candidates"](self._ctx(gd2))
            self.assertEqual(out2["candidates"], 0)

    def test_missing_ledger_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            empty = os.path.join(td, "no-ledger")
            os.makedirs(empty)
            with self.assertRaises(OSError):
                evals_metrics._RUNNERS["finding-candidates"](self._ctx(empty))

    def test_e2e_suite_rc3_then_rc0(self):
        import tempfile
        self._saved2 = dict(evals_metrics._RUNNERS)
        evals_metrics._RUNNERS.clear()
        evals_metrics._RUNNERS.update(self._saved2)  # 真 runner 面上叠 synthetic
        @evals_metrics.register("syn-matrix-pass")
        def _p(ctx):
            return {"status": "PASS", "actual": 1}
        with tempfile.TemporaryDirectory() as td:
            ms = _suite(_metric("A", "syn-matrix-pass"),
                        _metric("B", "finding-candidates"))
            code3, rep3 = evals_metrics.run_suite(ms, "s", _goal_with_findings(td, ["suspected"]), None)
            self.assertEqual(code3, 3, "端到端：仅未验证候选→rc3 黄灯")
            self.assertEqual(rep3["counts"]["candidates"], 1)
            code0, _ = evals_metrics.run_suite(ms, "s", _goal_with_findings(td, ["verified"]), None)
            self.assertEqual(code0, 0, "端到端：verified 在册→rc0")


if __name__ == "__main__":
    unittest.main()


def _cli(*args):
    return subprocess.run([sys.executable] + list(args), cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _run_evals(metrics_path, goal_dir):
    return _cli(os.path.join("cli", "tanyin-evals"), "run",
                "--metrics", metrics_path, "--suite", "s", "--goal-dir", goal_dir)


class TestFaceExitMatrix(unittest.TestCase):
    """CLI 面级退出码矩阵（W2 退出码分离验收面）：rc0/1/2/3 全格在册。

    rc0=门过；rc1=门禁 FAIL（含 vacuous 反绿 T17）；rc2=环境/用法（goal 缺/
    指标文件缺——b7/b8 env 分型先例全墙面钉）；rc3=仅未验证候选（evals 面，
    temp 指标集真跑子进程）。载体=[sys.executable, path] 纪律。"""

    def test_rc0_pass_faces(self):
        for args in ((os.path.join("cli", "tanyin-ledger"), "validate", "--goal-dir", FIX),
                     (os.path.join("cli", "tanyin-phases"), "status", "--goal-dir", FIX)):
            r = _cli(*args)
            self.assertEqual(r.returncode, 0, "%s→rc0: %s%s" % (args[0], r.stdout, r.stderr))

    def test_rc1_gate_fail_faces(self):
        g = _cli(os.path.join("cli", "tanyin-phases"), "gate", "--goal-dir", FIX,
                 "--phase=P5", "--timestamp=2026-09-24T10:00:00Z")
        self.assertEqual(g.returncode, 1, "P5 夹具断言不过=门禁 FAIL 非 env: %s" % g.stdout)
        v = _run_evals(os.path.join(ROOT, "no-such-metrics.json"), ROOT)
        self.assertEqual(v.returncode, 1, "指标文件缺=vacuous FAIL rc=1（T17 反绿口径）: %s" % v.stdout)

    def test_rc2_env_faces(self):
        miss = "/nonexistent-goal-matrix"
        faces = (os.path.join("cli", "tanyin-ledger"), os.path.join("cli", "tanyin-phases"),
                 os.path.join("cli", "tanyin-replay"), os.path.join("cli", "tanyin-viz"),
                 os.path.join("cli", "tanyin-budgetctl"), os.path.join("cli", "tanyin-guard"))
        for entry in faces:
            r = _cli(entry, "validate" if entry.endswith("tanyin-ledger") else "status",
                     "--goal-dir", miss)
            self.assertEqual(r.returncode, 2, "%s 缺 goal=env rc=2: %s%s" % (entry, r.stdout, r.stderr))
        r = _cli(os.path.join("cli", "tanyin-evals"), "list",
                 "--metrics", os.path.join(ROOT, "no-such-metrics.json"))
        self.assertEqual(r.returncode, 2, "evals list 指标缺=env rc=2")

    def test_rc3_only_candidates_and_rc0_after_verified(self):
        import json as _json
        import shutil
        import tempfile
        metric = {"id": "M-matrix-cand", "layer": "L2", "gate": "hard", "kind": "threshold",
                  "title": "矩阵 rc3 面", "baseline": {"value": "collect-first", "frozen_at": None},
                  "source": {"runner": "finding-candidates", "args": []}, "desc": "matrix"}
        with tempfile.TemporaryDirectory() as td:
            mp = os.path.join(td, "m.json")
            with open(mp, "w", encoding="utf-8") as f:
                _json.dump({"format_version": 1, "metrics": [metric], "suites": {"s": ["M-matrix-cand"]}}, f)
            r3 = _run_evals(mp, _goal_with_findings(td, ["suspected"]))
            self.assertEqual(r3.returncode, 3, "仅未验证候选→rc3 黄灯: %s%s" % (r3.stdout, r3.stderr))
            r0 = _run_evals(mp, _goal_with_findings(td, ["verified"]))
            self.assertEqual(r0.returncode, 0, "verified 在册→rc0: %s%s" % (r0.stdout, r0.stderr))


if __name__ == "__main__":
    unittest.main()
