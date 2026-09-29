# -*- coding: utf-8 -*-
"""批次 7 T11：egress OOB/canary 接线（High：decide() 只查 allow 集、compile 不产
[canary] 段——两声明面默认失效）+墙钟注入+日志轮转+socket 超时。"""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import egress_proxy as ep

# 名对齐 Step 0（以实文件为准）：骨架 load_acl/build_acl 为示意名——实名
# parse_acl（判定结构单源）/build_acl（cli/tanyin-egress 编译器内）；本测试经
# compile 子进程锚定产物，decide/format_log_line/append_log_line 为实名直测。


class TestDecide(unittest.TestCase):
    def _acl(self, text):
        return ep.parse_acl(text)

    def test_oob_classified_allow(self):
        acl = self._acl("[acl]\nallow in.example\n[oob]\noob oob.example\n")
        v, why = ep.decide(acl, "oob.example", 443)
        self.assertEqual(v, "oob", "红现状：只查 allow 集→oob 落默认拒")
        self.assertTrue(why)

    def test_canary_classified_allow(self):
        acl = self._acl("[acl]\nallow in.example\n[canary]\ncanary can.example\n")
        v, why = ep.decide(acl, "can.example", 80)
        self.assertEqual(v, "canary", "canary 命中=告警类放行（探测点语义）")
        self.assertTrue(why)

    def test_default_deny_unchanged(self):
        acl = self._acl("[acl]\nallow in.example\n")
        v, why = ep.decide(acl, "evil.example", 443)
        self.assertEqual(v, "deny")
        self.assertTrue(why)

    def test_explicit_deny_beats_allow(self):
        """exclude 优先纪律不回退（洞 1）：deny 命中恒先于 allow/canary/oob。"""
        acl = self._acl("[acl]\nallow in.example\ndeny in.example\n[canary]\ncanary can.example\n")
        v, _ = ep.decide(acl, "in.example", 443)
        self.assertEqual(v, "deny")


class TestCompile(unittest.TestCase):
    def test_compile_emits_oob_and_canary_sections(self):
        import shutil
        import subprocess
        ROOT = os.path.join(HERE, "..")
        FIX = os.path.join(HERE, "fixtures", "G-g1")
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-eg")
        shutil.copytree(FIX, gd)
        # scope kind=oob 行（argv 以契约附录 A add-scope 为准；R-T11-1 夹具对齐）
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "add-scope", "--goal-dir", gd, "--kind=oob",
                            "--matcher=oob.example",
                            "--timestamp=2026-09-27T00:00:00Z"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        os.makedirs(os.path.join(gd, "canary"))
        with open(os.path.join(gd, "canary", "recon-decoys.tsv"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("host\tcan-decoy.example\n")
        out = os.path.join(td.name, "egress.acl")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-egress"),
                            "compile", "--goal-dir", gd, "--out=" + out, '--timestamp=2026-09-30T12:00:00Z'],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            acl = f.read()
        self.assertIn("[oob]", acl)
        self.assertIn("oob.example", acl)
        self.assertIn("[canary]", acl, "红现状：compile v2 不产 canary 段（模块注释自认）")
        self.assertIn("can-decoy.example", acl)


class TestLogOps(unittest.TestCase):
    def test_wall_clock_default_not_constant(self):
        import re
        line = ep.format_log_line(None, "allow", "h.example", 443, "in")   # now=None→真墙钟
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}T", line), "缺省=真墙钟（红：EPOCH 常量）")
        line2 = ep.format_log_line("2026-09-27T00:00:00Z", "allow", "h.example", 443, "in")
        self.assertTrue(line2.startswith("2026-09-27T00:00:00Z"), "显式注入固定 now=测试确定性")

    def test_log_rotation(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        p = os.path.join(td.name, "egress.log")
        with open(p, "w") as f:
            f.write("x" * (ep.MAX_LOG_BYTES + 1))
        ep.append_log_line(p, "2026-09-27T00:00:00Z allow h 443 in")
        self.assertTrue(os.path.isfile(p + ".1"), "超限轮转 .1 代")
        self.assertLess(os.path.getsize(p), ep.MAX_LOG_BYTES)

    def test_handler_timeout_wired(self):
        self.assertEqual(ep._Handler.timeout, ep.HANDLER_TIMEOUT_S,
                         "handler socket 超时 30s（红：常量与接线俱缺）")


if __name__ == "__main__":
    unittest.main()