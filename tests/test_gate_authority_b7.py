# -*- coding: utf-8 -*-
"""批次 7 T6：九门权威（C3）。红=专家反例复现：append-timeline 零白名单——
连发 gate-exit:P0..P6（补 P5.5/P6.0 即 verify-chain 跳门=0）→ tanyin-phases
gate P6 already-passed exit 0，九门断言零执行即终局。绿=保留事件词拒收
（REJECT=零落账），门事件唯一铸造点=phases_engine 引擎侧直写（R-T6-1）。"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))

from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, dry_run_p0_p2, TS


class TestGateAuthority(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def _prep(self, name):
        """立项+scope 三行（tier0 硬门放行）；止步 gate P0 前——红绿两态共用前置。"""
        gd = fresh_drydir(self.td.name, name)
        code, done = dry_run_p0_p2(gd, upto=7)
        self.assertEqual(code, 0, "prep 序列自伤 rc=%d" % code)
        return gd

    def _tl(self, gd):
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            return f.read()

    # --- 红测：保留词拒收（绿态语义；红现状=rc=0 直通落账）---

    def test_append_timeline_rejects_gate_exit(self):
        gd = self._prep("G-ga")
        rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
                                    "--event=gate-exit:P0", "--timestamp=" + TS])
        self.assertEqual(rc, 1, "红现状 rc=0（零白名单直通——专家反例通道）: " + out + err)
        self.assertIn("REJECT", out + err)
        self.assertNotIn("gate-exit:", self._tl(gd), "REJECT=零落账")

    def test_append_timeline_rejects_gate_fail_and_variant(self):
        gd = self._prep("G-ga2")
        for ev in ("gate-fail:P0", "gate-exit:P5.5", "gate-exit:P6 asserts=0 result=PASS"):
            rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
                                        "--event=" + ev, "--timestamp=" + TS])
            self.assertEqual(rc, 1, "保留词拒收: " + ev + " -> " + out + err)

    def test_forged_fast_forward_sequence_broken(self):
        """专家复现序列：连发 gate-exit:P0..P6——修复后第一步即断。"""
        gd = self._prep("G-ga3")
        for g in ("P0", "P1", "P2", "P3", "P4", "P5", "P6"):
            rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=" + g,
                                        "--event=gate-exit:" + g, "--timestamp=" + TS])
            self.assertEqual(rc, 1, "第 %s 门伪造必须被拒（红现状 rc=0 落账）: %s"
                             % (g, out + err))

    # --- 对照组：合法铸造路径与合法事件词不受扰 ---

    def test_legit_gate_mint_unaffected(self):
        """合法铸造路径（dry_run P0-P2 三门真跑）照常：白名单只堵 append-timeline 注入侧。"""
        gd = fresh_drydir(self.td.name, "G-ga4")
        code, done = dry_run_p0_p2(gd)
        self.assertEqual(code, 0, "干跑 P0-P2 全序列 rc=%d（合法铸造通道受扰）" % code)
        tl = self._tl(gd)
        for g in ("P0", "P1", "P2"):
            self.assertIn("gate-exit:%s asserts=" % g, tl, "引擎铸造的门事件在链上: " + g)
        rc, out, err = ledger(gd, "verify-chain")
        self.assertEqual(rc, 0, out + err)

    def test_managed_restart_word_still_allowed(self):
        gd = self._prep("G-ga5")
        rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P1",
                                    "--event=managed-restart spawn=auto", "--timestamp=" + TS])
        self.assertEqual(rc, 0, "managed-restart 不进保留表（T6 裁决）: " + out + err)


if __name__ == "__main__":
    unittest.main()
