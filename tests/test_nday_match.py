# -*- coding: utf-8 -*-
"""批次5 T14：K3 本地 CVE 快照（cve-snapshot.tsv 七列精选+README 更新纪律/联网
仅核验边界 R11）+ nday-match 离线 CPE 匹配（前缀+版本区间元组比较 [start,end)；
零联网 import 断言；输出附快照日期 G-32）。"""
import os, re, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")
SNAP = os.path.join(SEED, "cve", "cve-snapshot.tsv")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestNdayMatch(unittest.TestCase):
    def test_hit_log4shell_range(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED,
               "--cpe=cpe:apache:log4j", "--version=2.14.1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CVE-2021-44228", r.stdout)
        self.assertIn("critical", r.stdout)
        self.assertIn("2.0..2.15", r.stdout, "版本区间回显")
        self.assertIn("2021-12-10", r.stdout, "published 回显")
        self.assertIn("#candidates=1", r.stdout)

    def test_version_out_of_range_miss(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED,
               "--cpe=cpe:apache:log4j", "--version=2.17.1")
        self.assertEqual(r.returncode, 0)
        self.assertIn("#candidates=0", r.stdout)

    def test_range_boundary_start_inclusive_end_exclusive(self):
        # version∈[start,end)：2.0 命中（含端点），2.15 不命中（开区间端）
        r1 = kn("nday-match", "--knowledge-dir=" + SEED,
                "--cpe=cpe:apache:log4j", "--version=2.0")
        self.assertIn("#candidates=1", r1.stdout)
        r2 = kn("nday-match", "--knowledge-dir=" + SEED,
                "--cpe=cpe:apache:log4j", "--version=2.15")
        self.assertIn("#candidates=0", r2.stdout)

    def test_unknown_prefix_zero(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED,
               "--cpe=cpe:x:y", "--version=1.0")
        self.assertEqual(r.returncode, 0)
        self.assertIn("#candidates=0", r.stdout)

    def test_snapshot_date_in_output(self):
        # G-32：nday 输出必附快照日期供审计
        r = kn("nday-match", "--knowledge-dir=" + SEED,
               "--cpe=cpe:apache:log4j", "--version=2.14.1")
        self.assertRegex(r.stdout, r"#snapshot-date=\d{4}-\d{2}-\d{2}")

    def test_args_required(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED, "--cpe=cpe:x:y")
        self.assertEqual(r.returncode, 2)

    def test_no_network_imports(self):
        # R11 离线边界：knowledge.py 零联网库（模块级 import 白名单断言）
        with open(os.path.join(ROOT, "cli", "ledger", "knowledge.py"),
                  encoding="utf-8") as f:
            src = f.read()
        for banned in ("urllib", "socket", "http.client", "requests"):
            self.assertNotIn(banned, src, "联网库进 knowledge.py 违反离线边界")


class TestSnapshotFile(unittest.TestCase):
    def test_shape_seven_cols_fourteen_rows(self):
        with open(SNAP, encoding="utf-8") as f:
            lines = f.read().splitlines()
        header = [l for l in lines if l.startswith("#")][0]
        self.assertIn("snapshot-date", header)
        data = [l.split("\t") for l in lines
                if l and not l.startswith("#") and not l.startswith("cve_id\t")]
        self.assertEqual(len(data), 14, "精选 14 行快照")
        for r in data:
            self.assertEqual(len(r), 7, "七列: %r" % (r,))
            self.assertRegex(r[0], r"^CVE-\d{4}-\d{4,}$")
            self.assertIn(r[4], ("critical", "high", "medium", "low"),
                          "severity 枚举: %r" % (r,))
            self.assertRegex(r[5], r"^\d{4}-\d{2}-\d{2}$", "published 日期")
            self.assertIn(r[6], ("NVD", "KEV", "PSIRT", "vendor"), "source 枚举")

    def test_readme_documents_boundaries(self):
        with open(os.path.join(SEED, "cve", "README.md"), encoding="utf-8") as f:
            t = f.read()
        for kw in ("NVD", "KEV", "联网仅核验", "G-32", "七列"):
            self.assertIn(kw, t, "README 缺: " + kw)


if __name__ == "__main__":
    unittest.main()
