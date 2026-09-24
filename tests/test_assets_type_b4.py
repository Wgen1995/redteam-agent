# -*- coding: utf-8 -*-
"""批次4 T1：assets.type 十一值枚举（G-12 裁决+pivot/foothold 启用）。"""
import os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T08:00:00Z"


def call(gd, *args):
    # Ruling（T1）：CLI 单入口冻结 argv[2]=="--goal-dir"（cli/tanyin-ledger main）——
    # --goal-dir 须紧随命令名（test_negative_matrix.py 先例），计划原稿尾置恒 exit 2。
    import subprocess
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestAssetTypeEnum(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_pivot_foothold_now_accepted(self):
        for t, v in (("pivot", "10.10.9.9"), ("foothold", "web-01.intranet")):
            r = call(self.gd, "add-asset", "--type=" + t, "--value=" + v, "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("OK", r.stdout)

    def test_new_g12_types_accepted_with_meta_sub(self):
        r = call(self.gd, "add-asset", "--type=cloud-storage", "--value=bucket-acme.s3.example.com",
                 "--meta=sub:object-bucket", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = call(self.gd, "add-asset", "--type=human-factor", "--value=cso@acme.example",
                 "--meta=sub:email", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unknown_type_still_rejected(self):
        r = call(self.gd, "add-asset", "--type=botnet", "--value=x.example", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
