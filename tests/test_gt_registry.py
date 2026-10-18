# -*- coding: utf-8 -*-
"""evals/gt 数据件校验测（宪法#43 评测棘轮地基；≥10 测：GT 行完整性/索引一致/评测可跑）。

被测件：evals/gt/gt-index.tsv + battlefields/*.json + snapshots/zl-repo/**
+ gt_verify.py（CLI 面）+ gt_eval.py（会话评测面）+ baselines/gt-baseline-v1.tsv。
靶场仓只读律：测试只读 ZhuLong 仓（--live 例 env-skip rc=2 容错）。
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GT_DIR = os.path.join(REPO, "evals", "gt")
INDEX = os.path.join(GT_DIR, "gt-index.tsv")
SNAP_ROOT = os.path.join(GT_DIR, "snapshots", "zl-repo")
ZL_REPO = os.path.expanduser(
    "~/Documents/AI For Security & Compliance/ai-assisted-security-verification-platform")
REQUIRED_FIELDS = ("id", "battlefield", "polarity", "status", "class", "cwe", "severity",
                   "title", "location", "finding", "verify_cmd", "provenance", "entered_at")

sys.path.insert(0, GT_DIR)
import gt_verify  # noqa: E402


def _index_rows():
    return gt_verify.load_index(INDEX)


def _battlefields():
    out = {}
    for r in _index_rows():
        if r["kind"] == "source-gt":
            with open(os.path.join(REPO, r["gt_file"]), encoding="utf-8") as f:
                out[r["battlefield"]] = json.load(f)
    return out


class TestGtIndex(unittest.TestCase):
    def test_index_header_and_kinds(self):
        rows = _index_rows()
        kinds = {r["kind"] for r in rows}
        self.assertIn("session-gt", kinds)
        self.assertIn("source-gt", kinds)
        self.assertIn("replay-fixture", kinds)
        for r in rows:
            self.assertEqual(len([c for c in [r["battlefield"], r["kind"], r["gt_file"],
                                              r["true_findings"], r["decoys"], r["caliber"],
                                              r["status"], r["entered_at"], r["note"]] if c]), 9)

    def test_index_files_exist(self):
        for r in _index_rows():
            p = r["gt_file"] if os.path.isabs(r["gt_file"]) else os.path.join(REPO, r["gt_file"])
            self.assertTrue(os.path.exists(p), r["battlefield"] + " -> " + p)

    def test_index_counts_match_rows(self):
        bfs = _battlefields()
        for r in _index_rows():
            if r["kind"] == "source-gt":
                pos = [x for x in bfs[r["battlefield"]]["rows"] if x["polarity"] == "pos"]
                neg = [x for x in bfs[r["battlefield"]]["rows"] if x["polarity"] == "neg"]
                self.assertEqual(int(r["true_findings"]), len(pos), r["battlefield"])
                self.assertEqual(int(r["decoys"]), len(neg), r["battlefield"])
            if r["kind"] == "session-gt":
                with open(os.path.join(REPO, r["gt_file"]), encoding="utf-8") as f:
                    self.assertEqual(int(r["true_findings"]), len(json.load(f)["planted"]))


class TestGtRows(unittest.TestCase):
    def test_row_schema_complete(self):
        for bf, doc in _battlefields().items():
            for row in doc["rows"]:
                miss = [k for k in REQUIRED_FIELDS if not row.get(k)]
                self.assertEqual(miss, [], bf + "/" + str(row.get("id")))
                self.assertIn(row["polarity"], ("pos", "neg"))
                self.assertIn(row["status"], ("open", "fixed-anchor", "decoy"))
                self.assertIn(row["severity"], ("Critical", "High", "Medium", "Low", "Info"))
                self.assertEqual(row["battlefield"], bf)

    def test_row_ids_unique_global(self):
        seen = set()
        for doc in _battlefields().values():
            for row in doc["rows"]:
                self.assertNotIn(row["id"], seen, row["id"])
                seen.add(row["id"])
        self.assertGreaterEqual(len(seen), 15)

    def test_new_battlefields_minimum(self):
        bfs = _battlefields()
        self.assertGreaterEqual(len(bfs), 2, "至少 2 个新 GT 战场")
        pos_total = sum(1 for d in bfs.values() for r in d["rows"] if r["polarity"] == "pos")
        self.assertGreaterEqual(pos_total, 10, "新真发现行 ≥10")

    def test_open_rows_on_record_provenance(self):
        for doc in _battlefields().values():
            for row in doc["rows"]:
                if row["status"] == "open":
                    self.assertRegex(row["provenance"], r"(ARTEX|Z:2|BO\d|walk-zhulong|runner-auth|artifact)",
                                     row["id"] + " 须在册出处")
                    self.assertIn(row["severity"], ("Critical", "High", "Medium"))

    def test_fixed_anchor_rows_marked(self):
        n = 0
        for doc in _battlefields().values():
            for row in doc["rows"]:
                if row["status"] == "fixed-anchor":
                    self.assertIn("修复回归锚", row["title"], row["id"])
                    n += 1
        self.assertGreaterEqual(n, 3)

    def test_decoys_negative_polarity(self):
        for doc in _battlefields().values():
            for row in doc["rows"]:
                if row["polarity"] == "neg":
                    self.assertEqual(row["status"], "decoy", row["id"])
                    self.assertIn("FP 诱饵", row["title"], row["id"])


class TestVerifyGuard(unittest.TestCase):
    def test_unsafe_commands_rejected(self):
        for bad in ("rm -rf apps", "grep -q x f && curl http://e",
                    "python3 -c 'print(1)'", "grep -q x f | wc -l",
                    "grep -q x f > out", "node -e '1'", ""):
            ok, why = gt_verify.check_verify_cmd(bad)
            self.assertFalse(ok, bad)

    def test_safe_commands_accepted(self):
        for good in ("grep -q 'x' a.ts",
                     "grep -q a f && ! grep -q b f",
                     "grep -q x f || test -f g"):
            ok, why = gt_verify.check_verify_cmd(good)
            self.assertTrue(ok, good + " " + why)


class TestVerifyRun(unittest.TestCase):
    def test_all_rows_verify_on_snapshots(self):
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_verify.py"),
                            "--root", SNAP_ROOT], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("fail=0", p.stdout)

    def test_live_verification_passes_or_envskip(self):
        if not os.path.isdir(ZL_REPO):
            self.skipTest("ZhuLong 靶场仓不在本机（env-skip）")
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_verify.py"),
                            "--live"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("fail=0", p.stdout)

    def test_snapshots_carry_provenance_header(self):
        n = 0
        for dirpath, _dirs, files in os.walk(SNAP_ROOT):
            for fn in files:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    head = f.read(200)
                self.assertIn("GT-ANCHOR-SNAPSHOT", head, fn)
                self.assertIn("source-of-truth", head, fn)
                n += 1
        self.assertGreaterEqual(n, 10)


class TestEvalRunnable(unittest.TestCase):
    def test_gt_eval_on_promoted_fixture(self):
        sess = os.path.join(REPO, "tests", "fixtures", "G-r27")
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_eval.py"),
                            "--session", sess, "--label", "ut-G-r27"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("recall=0.41 (23/56)", p.stdout)

    def test_baseline_table_three_battles(self):
        p = os.path.join(GT_DIR, "baselines", "gt-baseline-v1.tsv")
        with open(p, encoding="utf-8") as f:
            body = f.read()
        for lbl in ("b40-G-r41", "b41-G-r42", "b42-G-r43"):
            self.assertIn(lbl, body)
        self.assertIn("gt_total", body.splitlines()[1])
        for ln in body.splitlines():
            if ln.startswith("b4"):
                cols = ln.split("\t")
                self.assertEqual(len(cols), 11, ln)
                self.assertGreater(float(cols[7]), -1)   # fp 列在位
                self.assertGreater(float(cols[5]), 0.5)  # recall 列在位


if __name__ == "__main__":
    unittest.main()
