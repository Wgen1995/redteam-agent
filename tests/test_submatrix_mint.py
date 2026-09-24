# -*- coding: utf-8 -*-
"""批次4 T2：G-2 子矩阵行铸造+前缀首次归类修正（裁决 A）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T08:10:00Z"


def call(gd, *args):
    # Ruling（T2，同 T1）：CLI 单入口冻结 argv[2]=="--goal-dir"——须紧随命令名
    # （计划原稿尾置恒 exit 2）；test_negative_matrix.py 同款先例。
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def prep_matrix(gd, freeze=True):
    """Ruling（T2）：夹具 matrix.tsv 自带 frozen_at 盖戳行（make_fixtures 模拟 P2
    冻结事件）且 web.api 行 state=" "（伪空态）——计划原稿 setUp 对夹具直接
    matrix-freeze 必 REJECT「不可重复冻结」，且无 state=="" 行致 fresh 选择器
    StopIteration。按金样 autodrive 先例（run_golden.py matrix-freeze 预解冻）
    做文件级预处理：清全部 frozen_at+归一空态，再走 CLI matrix-freeze 冻结基线。"""
    p = os.path.join(gd, "matrix.tsv")
    rows = [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l]
    for r in rows:
        if len(r) >= 8:
            r[7] = ""            # frozen_at 清空（金样预解冻同款）
            if r[2] == " ":
                r[2] = ""        # 伪空态归一为 matrix-init 语义空态
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join("\t".join(r) for r in rows) + "\n")
    if freeze:
        r = call(gd, "matrix-freeze", "--timestamp=" + TS)
        assert r.returncode == 0, r.stdout + r.stderr


class TestSubmatrixMint(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        # 夹具矩阵已初始化；先冻结基线（submatrix 语义前置）——预处理见 prep_matrix
        prep_matrix(self.gd, freeze=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def matrix_keys(self):
        p = os.path.join(self.gd, "matrix.tsv")
        rows = [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l]
        return {(r[0], r[1]): r for r in rows}

    def test_mint_new_surface_full_vocab(self):
        r = call(self.gd, "matrix-set", "--attack-surface=api2.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: 新资产子矩阵",
                 "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        keys = self.matrix_keys()
        surf = [k for k in keys if k[0] == "api2.shop.example"]
        self.assertEqual(len(surf), 12, "新表面应铸造 VOCAB 全集 12 行，实际 %d" % len(surf))
        tgt = keys[("api2.shop.example", "wstg-authz")]
        self.assertEqual(tgt[2], "?")
        self.assertTrue(tgt[3].startswith("submatrix:"))
        other = [k for k in surf if k[1] != "wstg-authz"]
        self.assertTrue(all(keys[k][2] == "" and keys[k][3] == "submatrix:" for k in other),
                        "非目标行 state 空+reason 裸前缀")

    def test_mint_rejected_without_submatrix_prefix(self):
        r = call(self.gd, "matrix-set", "--attack-surface=api3.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=普通理由", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("submatrix:", r.stdout + r.stderr)

    def test_mint_rejected_before_freeze(self):
        gd2 = shutil.copytree(FIX, os.path.join(self.tmp, "G-nofreeze"))
        prep_matrix(gd2, freeze=False)   # 只预处理不冻结（Ruling：夹具自带盖戳行）
        r = call(gd2, "matrix-set", "--attack-surface=api4.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("冻结", r.stdout + r.stderr)

    def test_existing_surface_new_key_rejected(self):
        surf0 = next(iter(self.matrix_keys()))[0]
        r = call(self.gd, "matrix-set", "--attack-surface=" + surf0,
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("新表面", r.stdout + r.stderr)

    def test_first_categorization_authz_diff_allowed(self):
        """前缀首次归类修正：init 行 reason 空→authz-diff: 前缀放行（修潜伏阻塞）。"""
        keys = self.matrix_keys()
        fresh = next(k for k in keys if keys[k][3] == "" and keys[k][2] == "")
        r = call(self.gd, "matrix-set", "--attack-surface=" + fresh[0],
                 "--vuln-class=" + fresh[1], "--state=x",
                 "--reason=authz-diff: 各角色 403 一致", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_category_flip_rejected(self):
        keys = self.matrix_keys()
        fresh = next(k for k in keys if keys[k][3] == "" and keys[k][2] == "")
        call(self.gd, "matrix-set", "--attack-surface=" + fresh[0], "--vuln-class=" + fresh[1],
             "--state=x", "--reason=authz-diff: a", "--timestamp=" + TS)
        r = call(self.gd, "matrix-set", "--attack-surface=" + fresh[0],
                 "--vuln-class=" + fresh[1], "--state=x", "--reason=submatrix: b", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("前缀", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
