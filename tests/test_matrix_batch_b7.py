# -*- coding: utf-8 -*-
"""批次 7 T14：矩阵批量置格（High：220 资产=2640 格单格单命令）+资产类词表裁剪
（High：缺席资产类全量出行=矩阵爆炸）。

裁决（R-T14，详见 HANDOFF）：
- _validate_cell 单源抽出（单格/批量共用，禁第二份校验）；批量=先全校验后一次
  写入（全成全败），恰一条 matrix-set-batch n=<k> 事件；batch 行自载 state/reason
  （空单元格回落命令行参）。
- --from-assets 行集裁剪=在册 in_scope 资产类型映射的词表类（TYPE_VOCAB_CLASSES
  单源新建于 matrix_init——仓库此前无 type→class 映射）；缺席资产类型（A5 存储与云/
  A7 人的因素等）不出行；缺省不带开关=现行全量行为零变更（金样保护）。
- 计划示例断言字面 "A5" 在 matrix.tsv 无对应实形（词表键=wstg-*，shared/VOCAB），
  按实形断言缺席类型独涉类不出行。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, TS

LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
A64 = "a" * 64
TAB = chr(9)


def _batch(gd, rows):
    p = os.path.join(gd, "batch.tsv")
    with open(p, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("".join(TAB.join(r) + chr(10) for r in rows))
    return p


def _batch_set(gd, p):
    return subprocess.run([sys.executable, LEDGER, "matrix-set", "--goal-dir", gd,
                           "--batch-file=" + p, "--timestamp=" + TS, "--phase=P3"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _mk_goal(td, name):
    """最小 in_scope 夹具：八问落账+scope include+两 root-domain 资产（命中 matcher）。"""
    gd = fresh_drydir(td, name)
    rc, out, err = ledger(gd, "add-goal", [
        "--target=prune.example", "--objective=x", "--auth-doc=auth/dry.pdf",
        "--auth-sha256=" + A64, "--signer=self", "--valid-from=2026-09-01",
        "--valid-until=2026-09-30", "--budget=2M;50000;40", "--model-tier=strong",
        "--guard-tier=T3", "--timestamp=" + TS])
    assert rc == 0, out + err
    rc, out, err = ledger(gd, "add-scope", ["--kind=include", "--matcher=*.prune.example",
                                            "--note=y", "--timestamp=" + TS])
    assert rc == 0, out + err
    for v in ("a.prune.example", "b.prune.example"):
        rc, out, err = ledger(gd, "add-asset", ["--type=root-domain", "--value=" + v,
                                                "--meta=", "--timestamp=" + TS])
        assert rc == 0, out + err
    return gd


def _matrix_classes(gd):
    with open(os.path.join(gd, "matrix.tsv"), encoding="utf-8") as f:
        rows = [l.rstrip(chr(10)).split(TAB) for l in f if l.strip()]
    return rows, sorted({r[1] for r in rows})


class TestBatch(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-mb"))
        # G-g1 基线已冻结（frozen_at 在场——make_fixtures 模拟 P2 冻结，test_trigger_audit 同律）

    def test_batch_all_valid_single_event(self):
        rows = [["batch-s1.shop.example", "wstg-authz", "x", "submatrix:批量证据-1"],
                ["batch-s1.shop.example", "wstg-conf", "?", "submatrix:批量证据-2"],
                ["web.admin-panel", "authn.missing", "x", "批量证据-3"]]
        p = _batch(self.gd, rows)
        r = _batch_set(self.gd, p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("matrix-set-batch", r.stdout)
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertEqual(tl.count("matrix-set-batch n=3"), 1, "恰一条批量事件")
        with open(os.path.join(self.gd, "matrix.tsv"), encoding="utf-8") as f:
            mx = f.read()
        for surf, vc, _st, _rs in rows:
            self.assertIn(surf + TAB + vc, mx, "逐行落格: %s×%s" % (surf, vc))

    def test_batch_all_or_nothing(self):
        rows = [["batch-x.shop.example", "wstg-authz", "x", "submatrix:ok"],
                ["batch-y.shop.example", "wstg-notexist", "x", "submatrix:词表外键"]]
        with open(os.path.join(self.gd, "matrix.tsv"), encoding="utf-8") as f:
            before = f.read()
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            n0 = f.read().count(chr(10))
        p = _batch(self.gd, rows)
        r = _batch_set(self.gd, p)
        self.assertEqual(r.returncode, 1, "整批 REJECT（红现状：--batch-file 未知参数 rc=2）: "
                         + r.stdout + r.stderr)
        with open(os.path.join(self.gd, "matrix.tsv"), encoding="utf-8") as f:
            self.assertEqual(f.read(), before, "零部分写入（fail-closed）")
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            self.assertEqual(f.read().count(chr(10)), n0, "零事件落账")

    def test_batch_rejects_empty_and_malformed(self):
        p = _batch(self.gd, [])
        r = _batch_set(self.gd, p)
        self.assertEqual(r.returncode, 1, "空 batch=REJECT")
        p = _batch(self.gd, [["web.admin-panel", "authn.missing", "x", "五列", "多列"]])
        r = _batch_set(self.gd, p)
        self.assertEqual(r.returncode, 1, "非四列行=REJECT")
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            self.assertNotIn("matrix-set-batch", f.read(), "拒收零事件")


class TestFromAssets(unittest.TestCase):
    def test_absent_classes_pruned_only_with_flag(self):
        """夹具仅 root-domain（A1 标识层）在册：缺省=2 面×12 类全量出行；
        --from-assets=映射类（info/conf/idnt）出行，缺席类型独涉类不出行。"""
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        gd1 = _mk_goal(self.td.name, "G-mf1")
        rc, out, err = ledger(gd1, "matrix-init", ["--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        full, full_classes = _matrix_classes(gd1)
        self.assertEqual(len(full), 24, "缺省行为零变更（2 面×12 类）")
        self.assertEqual(len(full_classes), 12, "缺省=词表全集出行")
        gd2 = _mk_goal(self.td.name, "G-mf2")
        rc, out, err = ledger(gd2, "matrix-init", ["--from-assets", "--timestamp=" + TS])
        self.assertEqual(rc, 0, "红现状：--from-assets 未知参数 usage rc=2: " + out + err)
        pruned, pruned_classes = _matrix_classes(gd2)
        self.assertLess(len(pruned), len(full), "缺席类裁剪后行数严格更少")
        self.assertEqual(pruned_classes, ["wstg-conf", "wstg-idnt", "wstg-info"],
                         "root-domain 映射类恰三项（A1 标识层）")
        self.assertNotIn("wstg-sess", pruned_classes, "缺席类型独涉类不出行")
        self.assertNotIn("wstg-busl", pruned_classes, "A7 人的因素独涉类不出行")


if __name__ == "__main__":
    unittest.main()
