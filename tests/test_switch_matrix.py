# -*- coding: utf-8 -*-
"""M11 强/弱档开关矩阵（批次 6 T2）——铁律 6 不可裁剪三项在 T1/T3 两档同行为。

a) tanyin-guard exec 对 deny-list 命令恒 REJECT（rc!=0，两档一致）；
b) tanyin-egress compile 两档均产出 egress.acl（弱档不消失只降披露）；
c) 金丝雀零容忍不可裁剪：deploy 后 probe --tier=1/--tier=3 全拦（rc=0=拦截在位、
   allowed=0），且底层界外触碰（guard exec 对诱饵）恒非零 rc（R-T2-1）。

档位载体=goal 的 guard-tier（guard exec 无 --tier 旗标，R-T2-2）；
公开 CLI 面驱动，不触内部（铁律 7）。"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
GUARD = os.path.join(HERE, "..", "cli", "tanyin-guard")
EGRESS = os.path.join(HERE, "..", "cli", "tanyin-egress")
CANARY = os.path.join(HERE, "..", "cli", "tanyin-canary")
PY = sys.executable
TS = "2026-09-24T00:00:00Z"
NOOP = [PY, "-c", "pass"]


def _cli(entry, gd, *args):
    a = list(args)
    if not any(str(x).startswith("--timestamp") for x in a):   # 批次 10 T5：EPOCH 退役
        ts = "--timestamp=2026-09-30T12:00:00Z"
        a = ([a[0], ts] + a[1:]) if "--" in a else (a + [ts])   # 前置参位（-- 之前）
    return subprocess.run([PY, entry, a[0], "--goal-dir", gd] + a[1:],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class SwitchMatrix(unittest.TestCase):
    def setUp(self):
        if shutil.which("openssl") is None:
            self.skipTest("openssl 缺席（ENV 披露）")
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.gds = {}
        for tier in ("T1", "T3"):
            gd = os.path.join(self._td.name, "g" + tier)
            os.makedirs(gd)  # goal 目录须先在（core 纪律：不代建）
            r = _cli(LEDGER, gd, "add-goal", "--target=shop.example", "--objective=开关矩阵",
                     "--auth-doc=auth/m11.md", "--auth-sha256=" + "a" * 64, "--signer=evals",
                     "--allow-missing-auth=1",  # P0 加固：虚拟授权书走显式豁免
                     "--valid-from=2026-09-01", "--valid-until=2026-09-30",
                     "--budget=1M;1000;10", "--model-tier=strong", "--guard-tier=" + tier,
                     "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            r = _cli(LEDGER, gd, "add-scope", "--kind=include", "--matcher=shop.example",
                     "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.gds[tier] = gd

    def test_a_deny_list_reject_both_tiers(self):
        for tier, gd in sorted(self.gds.items()):
            r = _cli(GUARD, gd, "exec", "--", *(NOOP + ["shutdown"]))
            self.assertNotEqual(r.returncode, 0, tier + ": deny-list 恒 REJECT 被裁剪")
            self.assertIn("deny-list", r.stdout)

    def test_b_egress_acl_both_tiers(self):
        for tier, gd in sorted(self.gds.items()):
            r = _cli(EGRESS, gd, "compile")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(os.path.isfile(os.path.join(gd, "egress.acl")),
                            tier + ": egress.acl 未产出（弱档消失=裁剪）")

    def test_c_canary_zero_tolerance_both_probe_tiers(self):
        gd = self.gds["T3"]
        r = _cli(CANARY, gd, "deploy", "--seed=m11", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = _cli(EGRESS, gd, "compile")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        decoy = None
        for ptier in ("1", "3"):
            r = _cli(CANARY, gd, "probe", "--tier=" + ptier, "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, ptier + ": probe rc!=0（放行诱饵=零容忍破）")
            res = json.loads(r.stdout)
            self.assertEqual(res["status"], "pass")
            self.assertEqual(res["allowed"], 0, ptier + ": allowed!=0（零容忍破）")
            decoy = res["detail"][0]["value"]
        # 底层界外触碰恒非零 rc（「恒非零」探测面本体，R-T2-1）
        r = subprocess.run([PY, GUARD, "exec", "--goal-dir", gd, '--timestamp=2026-09-30T12:00:00Z', "--", *(NOOP + [decoy])],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertNotEqual(r.returncode, 0, "界外诱饵触碰未被拒绝")
        self.assertIn("REJECT", r.stdout)


if __name__ == "__main__":
    unittest.main()
