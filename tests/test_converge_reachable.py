# -*- coding: utf-8 -*-
"""批次5 T7：converge-check 可达未测格结构性停机判据（G-28 前半）。

#reachable-gaps/#unreachable-gaps 双计数=graph_cmds.reachable_gap_cells 单源
（horizon 同函数——起点集参数化，R-T7-1：计划片段固定 scope-root 起点与
「horizon 改调它行为零变」冲突，按行为零变优先参数化，converge 传 scope-root 资产集）。
结构性停机=不可达空格经 unreachable: 前缀置态（-）后计入清零——图依据显式置格，
非静默豁免（matrix-set 零改动：批4 裁决 A「旧前缀为空→任意前缀放行」）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T13:00:00Z"


def run(gd, sub, *args):
    return subprocess.run([sys.executable, CLI, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestConvergeReachable(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _close_unconsumed_facts(self):
        """G-g1 两 fact 无 derived_from 出边——先闭合该条件，隔离出空格维度。"""
        for fid in ("F-g1-0001", "F-g1-0002"):
            r = run(self.d, "add-edge", "--kind=derived_from", "--source-id=" + fid,
                    "--target-id=INT-g1-0002", "--provenance=风暴消费",
                    "--timestamp=" + TS)
            assert r.returncode == 0, r.stdout + r.stderr

    def test_counts_split_output(self):
        r = run(self.d, "converge-check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("#reachable-gaps=", r.stdout, "缺可达空格计数行")
        self.assertIn("#unreachable-gaps=", r.stdout, "缺不可达空格计数行")
        # 判定行仍居首（gate 断言读首行，PROTOCOL §1）
        self.assertIn(r.stdout.splitlines()[0].split("（")[0],
                      ("running", "converged", "budget-exhausted"))

    def test_structural_channel_closes_to_converged(self):
        """G-g1 唯一空格 web.api/inj.sql=不可达空格 → running+structural；
        unreachable: 通道置态后 → converged 且双计数清零。"""
        self._close_unconsumed_facts()
        r = run(self.d, "converge-check")
        self.assertIn("#reachable-gaps=0", r.stdout)
        self.assertIn("#unreachable-gaps=1", r.stdout)
        self.assertIn("structural", r.stdout, "可达清零而不可达>0 须附 structural 提示")
        first = r.stdout.splitlines()[0]
        self.assertTrue(first.startswith("running（structural"), first)
        r2 = run(self.d, "matrix-set", "--attack-surface=web.api", "--vuln-class=inj.sql",
                 "--state=-", "--reason=unreachable:AST-g1-0003", "--timestamp=" + TS)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        r3 = run(self.d, "converge-check")
        self.assertTrue(r3.stdout.startswith("converged"), r3.stdout)
        self.assertIn("#reachable-gaps=0", r3.stdout)
        self.assertIn("#unreachable-gaps=0", r3.stdout)
        self.assertNotIn("structural", r3.stdout)

    def test_reachable_gap_blocks_converged(self):
        """可达资产上留空格 → 不得 converged（即使不可达空格全清）且无 structural 提示。"""
        self._close_unconsumed_facts()
        # 织边：root→admin 子域（parent）——admin-internal.shop.example 自此可达
        r = run(self.d, "add-edge", "--kind=parent", "--source-id=AST-g1-0001",
                "--target-id=AST-g1-0002", "--provenance=可达性织边", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 清掉不可达空格（web.api 置态）
        r = run(self.d, "matrix-set", "--attack-surface=web.api", "--vuln-class=inj.sql",
                "--state=-", "--reason=unreachable:AST-g1-0003", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 可达面铸子矩阵行（目标类 x、其余 11 类空格）→ 可达空格=11
        r = run(self.d, "matrix-set", "--attack-surface=admin-internal.shop.example",
                "--vuln-class=wstg-inpv", "--state=x", "--reason=submatrix: 可达性测试",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = run(self.d, "converge-check")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotEqual(out.stdout.splitlines()[0].strip(), "converged",
                            "可达空格未清不得 converged")
        self.assertIn("#reachable-gaps=11", out.stdout)
        self.assertIn("#unreachable-gaps=0", out.stdout)
        self.assertNotIn("structural", out.stdout, "可达空格>0 不属 structural 通道")

    def test_horizon_behavior_unchanged_by_extraction(self):
        """单源抽取回归钉：graph-horizon 输出与抽取前逐字节一致（prep_graph 等价场景）。"""
        r = run(self.d, "add-edge", "--kind=parent", "--source-id=AST-g1-0001",
                "--target-id=AST-g1-0002", "--provenance=golden-graph", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(self.d, "matrix.tsv"), "a", encoding="utf-8", newline="\n") as f:
            f.write("admin-internal.shop.example\tinj.sql\t\t\t\t2\t\t\n")
        h = run(self.d, "graph-horizon", "--from=AST-g1-0001")
        self.assertEqual(h.returncode, 0, h.stderr)
        self.assertEqual(
            h.stdout,
            "#reachable=2\nAST-g1-0001\tasset\nAST-g1-0002\tasset\n"
            "#gaps=1\nadmin-internal.shop.example\tinj.sql\n",
            "horizon 行为因抽取漂移")


if __name__ == "__main__":
    unittest.main()
