# -*- coding: utf-8 -*-
"""批次 7 T12：restart 阈值接线（High：≥0.75/≥10 轮全仓零代码消费）。
红=缺参/低用量照常重启。"""
import os, shutil, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from tests.test_dryrun_p0p2 import ledger, phases

FIX = os.path.join(HERE, "fixtures", "G-g1")

class TestRestartThreshold(unittest.TestCase):
    def _ready(self, td, name):
        """R-T12-1（夹具裁决）：fresh_drydir 无 goals 行——checkpoint/add-scope 撞
        Tier0 硬门（REJECT 先立项，实测 rc=1）→ 按既有 test_kill9/test_managed_restart
        先例改 G-g1 夹具拷贝+checkpoint；断言面与计划一致。"""
        gd = os.path.join(td, name)
        shutil.copytree(FIX, gd)
        rc, out, err = ledger(gd, "checkpoint", ["--session=s0", "--phase=P1", "--note=init",
                                                 "--timestamp=2026-09-27T00:00:00Z"])
        self.assertEqual(rc, 0, out + err + "（夹具 checkpoint 失败=夹具无效）")
        # R-T12-2：restart 调用统一带 --session=s0（与夹具 checkpoint 同会话=auto 延续
        # 自身血统，非接管——③单活跃会话护栏与本任务断言正交，不因夹具态误伤）。
        return gd

    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_missing_usage_round_exit_2(self):
        gd = self._ready(self.td.name, "G-r1")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--session=s0", "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 2, "红现状：缺 --usage/--round 照常受理: " + out + err)

    def test_auto_below_threshold_rejected(self):
        gd = self._ready(self.td.name, "G-r2")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.30", "--round=3", "--session=s0",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 1, "红现状：0.30/3 轮照样重启（阈值零消费）: " + out + err)
        self.assertIn("restart-threshold", out)

    def test_auto_at_context_threshold_passes(self):
        gd = self._ready(self.td.name, "G-r3")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.80", "--round=3", "--session=s0",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)

    def test_auto_every_n_rounds_passes(self):
        gd = self._ready(self.td.name, "G-r4")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.10", "--round=10", "--session=s0",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)

    def test_manual_records_without_threshold(self):
        gd = self._ready(self.td.name, "G-r5")
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--usage=0.10", "--round=3", "--session=s0",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("usage=0.1", tl.replace("usage=0.10", "usage=0.1"), "事件词带 usage/round 审计")

    def test_invalid_values_exit_2(self):
        gd = self._ready(self.td.name, "G-r6")
        for extra in (["--usage=1.5", "--round=3"], ["--usage=abc", "--round=3"],
                      ["--usage=0.5", "--round=0"], ["--usage=0.5", "--round=x"]):
            rc, out, err = phases(gd, "restart",
                                  ["--spawn=auto", "--session=s0", "--timestamp=2026-09-27T01:00:00Z"] + extra)
            self.assertEqual(rc, 2, "非法值=usage 错: %r -> %s%s" % (extra, out, err))

    def test_manual_missing_params_exit_2(self):
        """manual 不设阈值但必须带参（审计语义）——缺参同为 usage exit 2。"""
        gd = self._ready(self.td.name, "G-r7")
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--session=s0", "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 2, "manual 缺 --usage/--round=usage 错: " + out + err)


if __name__ == "__main__":
    unittest.main()