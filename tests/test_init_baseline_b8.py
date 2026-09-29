# -*- coding: utf-8 -*-
"""批次 8 T10a（G-45）：init 运行时库缺省带方法学基线——k1-baseline.tsv 等
methodology/ TSV 随 init 拷入（缺基线=K1 exit 2 反例的根因面收口）。
"""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")


class TestInitBaseline(unittest.TestCase):
    def test_init_carries_methodology_baselines(self):
        with tempfile.TemporaryDirectory() as td:
            kd = os.path.join(td, "kn")
            r = subprocess.run([sys.executable, KN, "init", "--knowledge-dir", kd],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            self.assertEqual(r.returncode, 0, r.stderr)
            base = os.path.join(kd, "methodology", "k1-baseline.tsv")
            self.assertTrue(os.path.isfile(base),
                            "红现状：init 后 k1-baseline.tsv 缺（K1 缺基线=exit 2 根因）")
            head = open(base, encoding="utf-8").readline()
            self.assertIn("vuln_class", head)
            wstg = os.path.join(kd, "methodology", "k1-wstg-map.tsv")
            self.assertTrue(os.path.isfile(wstg))

    def test_init_idempotent_preserves_existing(self):
        with tempfile.TemporaryDirectory() as td:
            kd = os.path.join(td, "kn")
            subprocess.run([sys.executable, KN, "init", "--knowledge-dir", kd],
                           capture_output=True)
            p = os.path.join(kd, "methodology", "k1-baseline.tsv")
            with open(p, "a", encoding="utf-8") as f:
                f.write("custom-row	0.5	2\t本地覆写\tLOCAL\n")
            subprocess.run([sys.executable, KN, "init", "--knowledge-dir", kd],
                           capture_output=True)
            self.assertIn("custom-row", open(p, encoding="utf-8").read(),
                          "幂等：不覆盖既有本地基线")


if __name__ == "__main__":
    unittest.main()
