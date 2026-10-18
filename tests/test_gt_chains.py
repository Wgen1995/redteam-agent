# -*- coding: utf-8 -*-
"""tests/test_gt_chains.py — GT L3 链式扩容测（≥12 测；宪法#43 评测棘轮的链式面）。

被测件：evals/gt/battlefields/zl-chain-v1.json + range-chain-v1.json（链=有序步骤组，
环环 verify_cmd）+ gt-index.tsv 链式口径（chains/steps 步骤组字段）+ gt_verify.py
（chain-gt 校验面）+ gt_eval.py（链级两档判分：整链全对=1.0/部分对=0.5——口径写死不漂）
+ baselines/gt-chain-baseline-v1.tsv（三既有战链式召回对照）。
靶场仓只读律：--live 例只读 ZhuLong 仓（缺仓 env-skip rc=2 容错）。
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
ZL_CHAIN = os.path.join(GT_DIR, "battlefields", "zl-chain-v1.json")
RANGE_CHAIN = os.path.join(GT_DIR, "battlefields", "range-chain-v1.json")
CHAIN_BASELINE = os.path.join(GT_DIR, "baselines", "gt-chain-baseline-v1.tsv")
SESSION_GT = os.path.join(REPO, "tests", "range", "ground-truth.json")

REQUIRED_CHAIN_FIELDS = ("id", "battlefield", "polarity", "status", "class", "cwe",
                         "severity", "title", "impact", "steps", "provenance", "entered_at")
REQUIRED_STEP_FIELDS = ("order", "id", "title", "location", "finding", "verify_cmd", "provenance")

sys.path.insert(0, GT_DIR)
import gt_verify  # noqa: E402


def _index_rows():
    return gt_verify.load_index(INDEX)


def _chain_bfs():
    out = {}
    for r in _index_rows():
        if r["kind"] == "chain-gt":
            with open(os.path.join(REPO, r["gt_file"]), encoding="utf-8") as f:
                out[r["battlefield"]] = json.load(f)
    return out


def _chains():
    return [c for doc in _chain_bfs().values() for c in doc["chains"]]


class TestChainIndex(unittest.TestCase):
    def test_index_chain_rows_and_step_group_columns(self):
        """② gt-index 链式口径：11 列（chains/steps 步骤组字段）+ ≥2 链式战场行。"""
        rows = _index_rows()
        chain_rows = [r for r in rows if r["kind"] == "chain-gt"]
        self.assertGreaterEqual(len(chain_rows), 2, "至少 2 个 chain-gt 战场行")
        for r in rows:
            for col in ("battlefield", "kind", "gt_file", "true_findings", "decoys",
                        "chains", "steps", "caliber", "status", "entered_at", "note"):
                self.assertTrue(r.get(col), r["battlefield"] + " 缺 " + col)
            if r["kind"] == "chain-gt":
                self.assertGreaterEqual(int(r["chains"]), 1)
                self.assertGreaterEqual(int(r["steps"]), int(r["chains"]))

    def test_index_chain_counts_match_json(self):
        for r in _index_rows():
            if r["kind"] != "chain-gt":
                self.assertIn(int(r["chains"]), (0,), r["battlefield"] + " 非链行 chains 应为 0")
                continue
            with open(os.path.join(REPO, r["gt_file"]), encoding="utf-8") as f:
                doc = json.load(f)
            pos = [c for c in doc["chains"] if c["polarity"] == "pos"]
            self.assertEqual(int(r["true_findings"]), len(pos), r["battlefield"])
            self.assertEqual(int(r["decoys"]), len(doc["chains"]) - len(pos), r["battlefield"])
            self.assertEqual(int(r["chains"]), len(doc["chains"]), r["battlefield"])
            self.assertEqual(int(r["steps"]), sum(len(c["steps"]) for c in doc["chains"]),
                             r["battlefield"])


class TestChainSchema(unittest.TestCase):
    def test_min_two_verified_chains_each_source(self):
        """① ≥2 条已验证攻击链：源码锚（ZhuLong）与会话锚（24 夹具）各成链。"""
        bfs = _chain_bfs()
        self.assertIn("zl-chain-v1", bfs)
        self.assertIn("range-chain-v1", bfs)
        zl = [c for c in bfs["zl-chain-v1"]["chains"]]
        rc = [c for c in bfs["range-chain-v1"]["chains"]]
        self.assertGreaterEqual(len(zl), 2, "ZhuLong 源码链 ≥2")
        self.assertGreaterEqual(len(rc), 2, "会话链 ≥2")
        for c in zl + rc:
            self.assertGreaterEqual(len(c["steps"]), 2, c["id"] + " 链至少 2 环")

    def test_chain_schema_complete(self):
        for c in _chains():
            miss = [k for k in REQUIRED_CHAIN_FIELDS if not c.get(k)]
            self.assertEqual(miss, [], c.get("id") + " 缺 " + str(miss))
            self.assertIn(c["polarity"], ("pos", "neg"))
            self.assertIn(c["status"], ("open", "fixed-anchor", "decoy"))
            self.assertIn(c["severity"], ("Critical", "High", "Medium", "Low", "Info"))
            self.assertEqual(c["battlefield"].startswith("zl-chain") or
                             c["battlefield"].startswith("range-chain"), True)

    def test_steps_ordered_contiguous_with_fields(self):
        for c in _chains():
            orders = [s["order"] for s in c["steps"]]
            self.assertEqual(orders, list(range(1, len(c["steps"]) + 1)),
                             c["id"] + " 环序须 1..N 连续")
            for s in c["steps"]:
                miss = [k for k in REQUIRED_STEP_FIELDS if not s.get(k)]
                self.assertEqual(miss, [], c["id"] + "/" + str(s.get("id")) + " 缺 " + str(miss))

    def test_chain_and_step_ids_unique_global(self):
        seen = set()
        for doc in _chain_bfs().values():
            for c in doc["chains"]:
                self.assertNotIn(c["id"], seen, c["id"])
                seen.add(c["id"])
                for s in c["steps"]:
                    self.assertNotIn(s["id"], seen, s["id"])
                    seen.add(s["id"])
        for r in _index_rows():
            if r["kind"] == "source-gt":
                with open(os.path.join(REPO, r["gt_file"]), encoding="utf-8") as f:
                    for row in json.load(f)["rows"]:
                        self.assertNotIn(row["id"], seen, row["id"] + " 与链/环撞号")
                        seen.add(row["id"])

    def test_session_chain_gt_refs_resolve_no_dup(self):
        """会话链 gt_ref 逐一落在 session-GT 在册条目上；链内不重复引用（反膨胀）。"""
        with open(SESSION_GT, encoding="utf-8") as f:
            planted = {e["id"]: e for e in json.load(f)["planted"]}
        doc = _chain_bfs()["range-chain-v1"]
        for c in doc["chains"]:
            refs = [s["gt_ref"] for s in c["steps"]]
            self.assertEqual(len(refs), len(set(refs)), c["id"] + " 链内 gt_ref 重复")
            for ref in refs:
                self.assertIn(ref, planted, c["id"] + " 引用未知条目 " + str(ref))
            # 语义钉：凭据链以认证前面收尾（末环 post_auth）——链终点=认证后利用
            self.assertTrue(planted[refs[-1]].get("post_auth"), c["id"] + " 末环须认证后条目")

    def test_step_verify_cmds_guard_safe(self):
        for c in _chains():
            for s in c["steps"]:
                ok, why = gt_verify.check_verify_cmd(s["verify_cmd"])
                self.assertTrue(ok, c["id"] + "/" + s["id"] + " verify_cmd 不安全: " + why)


class TestChainVerifyRun(unittest.TestCase):
    def test_verify_includes_chain_steps_snapshot(self):
        """gt_verify 收链：快照根全行（含链环）rc=0。"""
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_verify.py"),
                            "--root", SNAP_ROOT], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("fail=0", p.stdout)

    def test_verify_chain_steps_live_or_envskip(self):
        if not os.path.isdir(ZL_REPO):
            self.skipTest("ZhuLong 靶场仓不在本机（env-skip）")
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_verify.py"),
                            "--live"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("fail=0", p.stdout)

    def test_new_snapshot_files_carry_header(self):
        for rel in ("apps/server/src/routes/runner.ts",):
            p = os.path.join(SNAP_ROOT, rel)
            self.assertTrue(os.path.isfile(p), p + " 快照缺件")
            with open(p, encoding="utf-8") as f:
                head = f.read(400)
            self.assertIn("GT-ANCHOR-SNAPSHOT", head)
            self.assertIn("source-of-truth", head)
            self.assertIn("runner.ts", head)
        with open(os.path.join(SNAP_ROOT, "apps/server/src/services/runner-auth.ts"),
                  encoding="utf-8") as f:
            body = f.read()
        for anchor in ("'master.key'", "sealedMasterKey", "crypto_box_seal"):
            self.assertIn(anchor, body, "runner-auth 快照缺锚 " + anchor)


class TestChainScoring(unittest.TestCase):
    def test_chain_tiers_written_in_stone(self):
        """③ 链级两档判分口径写死：整链全对=1.0/部分对=0.5/零=0——常量钉死禁漂移。"""
        import gt_eval
        self.assertEqual(gt_eval.CHAIN_TIERS, {"full": 1.0, "partial": 0.5, "zero": 0.0})

    def test_score_chain_tier_math(self):
        import gt_eval
        chain = {"id": "t", "steps": [{"gt_ref": "a"}, {"gt_ref": "b"}, {"gt_ref": "c"}]}
        r = gt_eval.score_chain(chain, {"a", "b", "c"})
        self.assertEqual((r["tier"], r["score"]), ("full", 1.0))
        r = gt_eval.score_chain(chain, {"a"})
        self.assertEqual((r["tier"], r["score"]), ("partial", 0.5))
        self.assertEqual(r["missed_steps"], ["b", "c"])
        r = gt_eval.score_chain(chain, set())
        self.assertEqual((r["tier"], r["score"]), ("zero", 0.0))
        self.assertEqual(gt_eval.chain_recall([{"score": 1.0}, {"score": 0.5}]), 0.75)
        self.assertEqual(gt_eval.chain_recall([]), 0.0)

    def test_gt_eval_chain_mode_on_fixture(self):
        """CLI 链式面：G-r26（battle-25）——链1 全对/链2 部分对 → chain_recall=0.75。"""
        p = subprocess.run([sys.executable, os.path.join(GT_DIR, "gt_eval.py"),
                            "--session", os.path.join(REPO, "tests", "fixtures", "G-r26"),
                            "--label", "ut-G-r26", "--chain", RANGE_CHAIN],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("chain_recall=0.75 (1.5/2)", p.stdout)
        self.assertIn("full=1", p.stdout)
        self.assertIn("partial=1", p.stdout)
        self.assertIn("step_recall=0.80 (4/5)", p.stdout)
        self.assertIn("flat_recall=0.57", p.stdout)
        self.assertIn("range-chain-01	full", p.stdout)
        self.assertIn("range-chain-02	partial", p.stdout)
        self.assertIn("missed=idor-02", p.stdout)

    def test_three_battles_chain_baseline_recorded(self):
        """④ 三既有战链式召回对照入册；数值与复算一致（防尺子漂移）。"""
        self.assertTrue(os.path.isfile(CHAIN_BASELINE))
        import gt_eval
        with open(CHAIN_BASELINE, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln and not ln.startswith("#")]
        header = lines[0].split("\t")
        self.assertIn("chain_recall", header)
        self.assertIn("flat_recall", header)
        rows = {}
        for ln in lines[1:]:
            cols = ln.split("\t")
            self.assertEqual(len(cols), len(header), ln)
            rows[cols[0]] = dict(zip(header, cols))
        for lbl, sess, flat in (("b24-G-r25", "G-r25", "0.62"),
                                ("b25-G-r26", "G-r26", "0.57"),
                                ("b26-G-r27", "G-r27", "0.41")):
            self.assertIn(lbl, rows, lbl + " 缺链式基线行")
            r = gt_eval.eval_session_chains(os.path.join(REPO, "tests", "fixtures", sess),
                                            RANGE_CHAIN, SESSION_GT)
            self.assertEqual(rows[lbl]["chain_recall"], "%.2f" % r["chain_recall"], lbl)
            self.assertEqual(rows[lbl]["flat_recall"], flat, lbl)
            self.assertEqual(rows[lbl]["zero"], "0", lbl + " 三战均有链命中（零档空）")


if __name__ == "__main__":
    unittest.main()
