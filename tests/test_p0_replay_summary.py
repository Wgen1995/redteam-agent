# -*- coding: utf-8 -*-
"""P0 诚实性加固批（会诊④/RT-0023 32/54 洞）：replay-summary 全 EV 终态。

旧语义：C1/C2 finding 任一 EV 已重放 ⇒ PASS（54 findings 仅 32 重放照样
出 P4）。新语义：全部 evidence_ids∪linked 须终态；PASS 行附
c12_findings 与 ev_coverage 披露。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestReplaySummaryTightened(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        # 直铸 C1 finding（两枚挂接 EV；E-index/findings 非链式表可直写）
        for i, fid in ((1, "EV-x-0001"), (2, "EV-x-0002")):
            with open(os.path.join(self.d, "E-index.tsv"), "a", encoding="utf-8") as f:
                f.write("\t".join([fid, "证据", "command", TS, "internet",
                                    "curl -s http://x/", "single", "a" * 64, "b" * 64,
                                    "", "", "FD-x-0001", "", "ex", "2", TS]) + "\n")
        with open(os.path.join(self.d, "findings.tsv"), "a", encoding="utf-8") as f:
            f.write("\t".join(["FD-x-0001", "INT-x", "双证据越权", "C1", "高",
                               "suspected", "", "x-key", "", "in_scope", "双EV",
                               "步骤", "", "", "", "", "", "2", TS]) + "\n")

    def tearDown(self):
        shutil.rmtree(self.d)

    def _probe(self, rid, verdict="reproduced"):
        r = run(self.d, "append-timeline", "--actor=子代理", "--phase=P4",
                "--event=replay-probe %s verdict=%s" % (rid, verdict),
                "--revert-cmd=none", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)

    def _sign(self, rid):
        r = run(self.d, "set-replay-state", "--id=" + rid, "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_partial_coverage_fails(self):
        self._probe("EV-x-0001")
        self._sign("EV-x-0001")
        r = run(self.d, "ledger-replay-summary")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EV未终态:EV-x-0002", r.stdout)

    def test_full_coverage_passes_with_disclosure(self):
        for rid in ("EV-x-0001", "EV-x-0002"):
            self._probe(rid)
            self._sign(rid)
        r = run(self.d, "ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("c12_findings=1", r.stdout)
        self.assertIn("ev_coverage=100%", r.stdout)

    def test_c3_finding_still_exempt(self):
        # G-g1 自带 FD-g1-0001=C3：不产生重放义务
        for rid in ("EV-x-0001", "EV-x-0002"):
            self._probe(rid)
            self._sign(rid)
        r = run(self.d, "ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
