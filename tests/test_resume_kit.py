# -*- coding: utf-8 -*-
"""批次 3 T7：resume-kit 生成——白名单注入清单/先对账/幂等字节一致。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:00:00Z"


class TestResumeKit(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def gen(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("resume-kit", self.gd, list(args) or ["--timestamp=" + TS])
        return code, buf.getvalue()

    def read_kit(self):
        p = os.path.join(self.gd, "resume-kit.md")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None

    def test_generates_whitelist_content(self):
        code, out = self.gen()
        self.assertEqual(code, 0, out)
        kit = self.read_kit()
        self.assertIn("先对账再干活", kit)
        self.assertIn("current_gate: P4", kit)   # 夹具已过 P0-P3 → 下一门 P4
        self.assertIn("verify-chain", kit)
        self.assertIn("state-rebuild", kit)
        self.assertIn("phases/P4.md", kit)
        self.assertIn("pending-intents", kit)
        self.assertIn("禁注入", kit)
        self.assertIn("INT-g1-0001", kit)   # 夹具 done intent 进幂等表

    def test_idempotent_byte_identical(self):
        self.gen()
        first = self.read_kit()
        self.gen()
        self.assertEqual(self.read_kit(), first)   # 同账本+同 ts=字节一致（确定性投影）

    def test_broken_chain_refuses(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"
        core.write_tsv(p, rows)
        code, out = self.gen()
        self.assertEqual(code, 1)
        self.assertIsNone(self.read_kit())

    def test_atomic_no_tmp(self):
        self.gen()
        self.assertFalse(os.path.exists(os.path.join(self.gd, "resume-kit.md.tmp")))

    def test_skip_table_reflects_submissions(self):
        os.makedirs(os.path.join(self.gd, "submissions", "INT-g1-0001"), exist_ok=True)
        with open(os.path.join(self.gd, "submissions", "INT-g1-0001", "submission.json"),
                  "w", encoding="utf-8") as f:
            f.write("{}")
        self.gen()
        kit = self.read_kit()
        self.assertRegex(kit, r"INT-g1-0001\s+SKIP")

    # ---- 自加钉死例（计划未列；T3/T6 同型先例，HANDOFF 记账）----

    def test_default_timestamp_from_timeline_tail(self):
        # --timestamp 缺省=timeline 最后一行时间戳（确定性；禁 datetime.now 进产物）
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("resume-kit", self.gd, [])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("updated: 2026-09-23T03:05:00Z", self.read_kit())   # 夹具末行

    def test_usage_error_exit_2(self):
        # 退出码纪律：用法/参数非法=2（非裸异常）
        code, _ = self.gen("--bogus=1")
        self.assertEqual(code, 2)

    def test_cli_golden_baseline_lock(self):
        """CLI 面（[sys.executable, 入口]）+ 双目录字节一致 + 金样基线锁定（T3 裁决同型）。"""
        import subprocess
        cli = os.path.join(ROOT, "cli", "tanyin-phases")
        r = subprocess.run([sys.executable, cli, "resume-kit", "--goal-dir", self.gd,
                            "--timestamp=" + TS], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK" + chr(9) + "resume-kit" + chr(9) + "gate=P4" + chr(9) + "cached=1",
                      r.stdout)
        gd2 = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1b"))
        r2 = subprocess.run([sys.executable, cli, "resume-kit", "--goal-dir", gd2,
                             "--timestamp=" + TS], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        kit1 = self.read_kit()
        with open(os.path.join(gd2, "resume-kit.md"), encoding="utf-8") as f:
            kit2 = f.read()
        self.assertEqual(kit1, kit2)   # 双目录字节一致（确定性投影）
        gp = os.path.join(HERE, "golden", "phases-resume-kit.norm")
        self.assertTrue(os.path.isfile(gp), "金样缺失: " + gp)
        with open(gp, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), kit1.strip())


if __name__ == "__main__":
    unittest.main()
