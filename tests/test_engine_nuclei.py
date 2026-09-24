# -*- coding: utf-8 -*-
"""批次4 T10：nuclei adopt——验签先于归一化（不过=blocked）+canned JSONL 归一化。"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ADAPTER = os.path.join(ROOT, "engines", "nuclei", "adapter.py")
JSONL = os.path.join(HERE, "fixtures", "engine", "nuclei-jsonl", "sample.jsonl")
LOCK = os.path.join(ROOT, "tools.lock")
HAVE_OPENSSL = shutil.which("openssl") is not None


class TestNucleiAdapter(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def run_adapter(self, *extra):
        return subprocess.run([sys.executable, ADAPTER, "--intent-id", "INT-g1-0100",
                               "--out-dir", self.out] + list(extra),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_tampered_lock_blocks_before_normalize(self):
        """验签先于归一化：lock 副本篡改 nuclei 行 sha256→--jsonl-file 仍 blocked（exit 0）。"""
        tmp_lock = os.path.join(self.out, "tools.lock")
        rows = []
        for l in open(LOCK, encoding="utf-8").read().splitlines():
            p = l.split("\t")
            if len(p) == 5 and p[0] == "nuclei":
                p[2] = "0" * 64
                l = "\t".join(p)
            rows.append(l)
        with open(tmp_lock, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(rows) + "\n")
        r = self.run_adapter("--lock", tmp_lock, "--jsonl-file", JSONL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        self.assertEqual(sub["status"], "blocked", "验签不过=blocked 提交（环境受阻）")
        self.assertEqual(sub["findings"], [])
        log = open(os.path.join(self.out, "operations.log"), encoding="utf-8").read()
        self.assertIn("验签失败", log, "log 落 blocked 缘由")

    @unittest.skipUnless(HAVE_OPENSSL, "openssl 缺失=ENV——验签先于归一化，canned 路径不可达")
    def test_canned_normalize(self):
        r = self.run_adapter("--jsonl-file", JSONL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        self.assertEqual(sub["engine"], "nuclei")
        self.assertEqual(sub["status"], "done")
        by_dedup = {f["dedup_key_proposed"]: f for f in sub["findings"]}
        med = by_dedup["tanyin-exposed-panel+nuclei"]
        self.assertEqual(med["impact"], "中", "severity medium→中")
        self.assertEqual(med["expected_matcher"]["matchers"][0]["words"], ["word-0"],
                         "matcher-name→expected_matcher word")
        high = by_dedup["tanyin-actuator-leak+nuclei"]
        self.assertEqual(high["impact"], "高", "severity high→高")
        self.assertEqual(high["confidence"], "C3")
        self.assertEqual(high["network_position"], "internet")

    def test_golden_face_registered(self):
        """金样面 engine-nuclei-adopt 在 run_golden 登记（openssl 门控=ENV SKIP 口径）。"""
        src = open(os.path.join(HERE, "run_golden.py"), encoding="utf-8").read()
        self.assertIn("engine-nuclei-adopt", src)
        self.assertIn("NUCLEI_CMDS", src)


if __name__ == "__main__":
    unittest.main()
