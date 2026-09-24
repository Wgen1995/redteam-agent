# -*- coding: utf-8 -*-
"""批次4 T7 前置（图谱驱动设计增补 71d3b7c）：图查询三命令——只读确定性图运算。

graph-neighbors（邻接展开）/graph-paths（可达路径枚举）/graph-horizon（可达集×矩阵空格 join）。
41 面增补走微版本勘误（同 G-1 先例）；铁律 7 允许类=确定性账本运算，无攻击决策。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:00:00Z"


def call(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def add_edge(gd, kind, src, dst):
    r = call(gd, "add-edge", "--kind=" + kind, "--source-id=" + src, "--target-id=" + dst,
             "--provenance=graph-test", "--timestamp=" + TS)
    assert r.returncode == 0, r.stdout + r.stderr


class TestGraphNeighbors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        # 预织图：parent 边（资产层级）+ attack 边（finding→资产）；CRED→scope_asset 链自带于 creds 行
        add_edge(self.gd, "parent", "AST-g1-0001", "AST-g1-0002")
        add_edge(self.gd, "attack", "FD-g1-0001", "AST-g1-0002")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_depth_one_mixed_via(self):
        r = call(self.gd, "graph-neighbors", "--asset=AST-g1-0002")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#count=", r.stdout)
        self.assertIn("CRED-g1-0001", r.stdout)   # 凭据链出边（cred:unlock）
        self.assertIn("FD-g1-0001", r.stdout)     # attack 入边
        self.assertIn("AST-g1-0001", r.stdout)    # parent 入边

    def test_edge_class_filter(self):
        r = call(self.gd, "graph-neighbors", "--asset=AST-g1-0002", "--edge-class=cred")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CRED-g1-0001", r.stdout)
        self.assertNotIn("FD-g1-0001", r.stdout)
        r = call(self.gd, "graph-neighbors", "--asset=AST-g1-0002", "--edge-class=attack")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("FD-g1-0001", r.stdout)
        self.assertNotIn("CRED-g1-0001", r.stdout)

    def test_depth_two_and_unknown(self):
        r = call(self.gd, "graph-neighbors", "--asset=FD-g1-0001", "--depth=2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CRED-g1-0001", r.stdout)   # FD→AST(1)→CRED(2)
        r = call(self.gd, "graph-neighbors", "--asset=AST-g1-9999")
        self.assertEqual(r.returncode, 0)
        self.assertIn("#count=0", r.stdout)

    def test_usage_errors(self):
        self.assertEqual(call(self.gd, "graph-neighbors").returncode, 2)
        self.assertEqual(call(self.gd, "graph-neighbors", "--asset=AST-g1-0002",
                              "--depth=abc").returncode, 2)
        self.assertEqual(call(self.gd, "graph-neighbors", "--asset=AST-g1-0002",
                              "--edge-class=nope").returncode, 2)


class TestGraphPaths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        add_edge(self.gd, "parent", "AST-g1-0001", "AST-g1-0002")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_cred_to_asset_path(self):
        r = call(self.gd, "graph-paths", "--from=CRED-g1-0001", "--to=AST-g1-0002")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#paths=1", r.stdout)
        self.assertIn("CRED-g1-0001->AST-g1-0002", r.stdout)

    def test_scope_root_and_unreachable(self):
        r = call(self.gd, "graph-paths", "--from=AST-g1-0001", "--to=scope-root")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("AST-g1-0001", r.stdout)     # 起点即 root-domain（0 跳平凡路径）
        r = call(self.gd, "graph-paths", "--from=CRED-g1-0001", "--to=AST-g1-0001")
        self.assertEqual(r.returncode, 0)
        self.assertIn("#paths=0", r.stdout)        # 凭据可达资产不可达根域（parent 边单向）

    def test_max_hops_and_usage(self):
        r = call(self.gd, "graph-paths", "--from=CRED-g1-0001", "--to=AST-g1-0002",
                 "--max-hops=1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#paths=1", r.stdout)
        self.assertEqual(call(self.gd, "graph-paths", "--to=AST-g1-0002").returncode, 2)
        self.assertEqual(call(self.gd, "graph-paths", "--from=CRED-g1-0001", "--to=AST-g1-0002",
                              "--max-hops=x").returncode, 2)


class TestGraphHorizon(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        add_edge(self.gd, "parent", "AST-g1-0001", "AST-g1-0002")
        # 预置可达表面上的空格行（state 空=未检查）：admin-internal.shop.example=in_scope 资产值
        with open(os.path.join(self.gd, "matrix.tsv"), "a", encoding="utf-8", newline="\n") as f:
            f.write("admin-internal.shop.example\tinj.sql\t\t\t\t2\t\t\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_reachable_and_gap_join(self):
        r = call(self.gd, "graph-horizon", "--from=AST-g1-0001")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#reachable=2", r.stdout)   # AST-1 + AST-2（parent 出边；CRED→AST 为入边不计）
        self.assertIn("#gaps=1", r.stdout)
        self.assertIn("admin-internal.shop.example\tinj.sql", r.stdout)

    def test_no_gap_off_reachable_surface(self):
        r = call(self.gd, "graph-horizon", "--from=AST-g1-0003")   # vpn 子域：无边可达
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#reachable=1", r.stdout)
        self.assertIn("#gaps=0", r.stdout)        # web.api 空格在不可达表面——不进地平线

    def test_deterministic_output(self):
        a = call(self.gd, "graph-horizon", "--from=AST-g1-0001")
        b = call(self.gd, "graph-horizon", "--from=AST-g1-0001")
        self.assertEqual(a.stdout, b.stdout)
        self.assertEqual(call(self.gd, "graph-horizon").returncode, 2)


if __name__ == "__main__":
    unittest.main()
