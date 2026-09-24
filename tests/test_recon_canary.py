# -*- coding: utf-8 -*-
"""批次4 T12：侦察金丝雀（G-13）——recon-deploy/recon-recall+denominator ④。

Ruling（argv 契约，R-T1-1 同型）：计划 run() 把 --goal-dir 尾置——CLI 单入口冻结
argv[2]=="--goal-dir"（tanyin-canary/tanyin-phases/tanyin-ledger main 同律），
修正=--goal-dir 紧随子命令/命令名。语义断言逐字保持计划原文。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CANARY = os.path.join(ROOT, "cli", "tanyin-canary")
PHASES = os.path.join(ROOT, "cli", "tanyin-phases")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:00:00Z"


def run(cli, gd, sub, *args):
    return subprocess.run([sys.executable, cli, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestReconCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_deploy_and_recall_miss_then_hit(self):
        r = run(CANARY, self.gd, "recon-deploy", "--value=decoy1.shop.example",
                "--type=subdomain", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(CANARY, self.gd, "recon-deploy", "--value=decoy1.shop.example",
                "--type=subdomain", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, "重复诱饵=REJECT")
        r = run(CANARY, self.gd, "recon-recall")
        self.assertEqual(r.returncode, 0)
        self.assertIn("0/1", r.stdout)
        # 诱饵被发现（测绘落账）→召回满
        r = subprocess.run([sys.executable, LEDGER, "add-asset", "--goal-dir", self.gd,
                            "--type=subdomain", "--value=decoy1.shop.example",
                            "--timestamp=" + TS],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(CANARY, self.gd, "recon-recall")
        self.assertIn("1/1", r.stdout)

    def test_denominator_gate4_paths(self):
        # 路径一：未部署且未披露→FAIL
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertEqual(r.returncode, 1)
        self.assertIn("④", r.stdout + r.stderr)
        # 路径二：未部署但披露 fact→④过（其余断言若挂不影响本例判断——只查④行不在 FAIL 清单）
        subprocess.run([sys.executable, LEDGER, "add-fact", "--goal-dir", self.gd,
                        "--intent-id=INT-g1-0001", "--kind=info", "--target=canary:recon",
                        "--detail=客户暂不配合植入（披露）", "--confidence=0.9",
                        "--timestamp=" + TS],
                       capture_output=True, text=True)
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertNotIn("④召回", r.stdout)
        # 路径三：部署 1 未发现→FAIL 列缺失诱饵
        run(CANARY, self.gd, "recon-deploy", "--value=decoy2.shop.example",
            "--type=subdomain", "--timestamp=" + TS)
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertIn("decoy2", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
