# -*- coding: utf-8 -*-
"""批次5 T3：intents 15→17 双列（G-24 priority/G-27 cred）物理落地。

钉子四面：schemas 17 字段序（priority/cred 插 reason 后、schema_version 前）；
夹具重铸全行 17 列；add-intent --priority/--cred 落物理列（0-1 校验+任意 kind
cred 引用闭合）；set-intent-status 事件溯源追加行携带两列值。
R-T3-2：状态转移用例改 INT-g1-0002（pending→active 合法转移）——计划原文
INT-g1-0001 在夹具中 status=done 终态不可复活（_INTENT_ARROWS["done"]=∅）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger.schemas import TABLES  # noqa: E402

INTENT_FIELDS = TABLES["intents.tsv"]
TS = "2026-09-24T08:00:00Z"


def run(gd, *args):
    # R-T3-1：入口约束 argv[2]=="--goal-dir"（tanyin-ledger main）——--goal-dir 紧随命令，
    # 同 run_golden.run_cli / make_diff_fixture.call 在册形态（计划测试片段后置形态不可用）。
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def intent_rows(gd):
    p = os.path.join(gd, "intents.tsv")
    return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]


class TestIntents17Columns(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        # 夹具重铸后 intents 行应已 17 列——本测试同时钉死夹具

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_schema_has_17_fields_with_priority_cred(self):
        self.assertEqual(len(INTENT_FIELDS), 17)
        self.assertEqual(INTENT_FIELDS[-4], "priority")
        self.assertEqual(INTENT_FIELDS[-3], "cred")
        self.assertEqual(INTENT_FIELDS[-2], "schema_version")
        self.assertEqual(INTENT_FIELDS[-1], "created")
        self.assertEqual(INTENT_FIELDS[INTENT_FIELDS.index("reason") + 1], "priority")

    def test_fixture_rows_all_17(self):
        for row in intent_rows(self.d):
            self.assertEqual(len(row), 17, "非 17 列行: " + row[0])

    def test_add_intent_priority_cred_land_in_columns(self):
        r = run(self.d, "add-intent", "--title=带凭据意图", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=100;10;1",
                "--priority=0.72", "--cred=CRED-g1-0001",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = intent_rows(self.d)
        new = [x for x in rows if x[INTENT_FIELDS.index("title")] == "带凭据意图"][-1]
        self.assertEqual(new[INTENT_FIELDS.index("priority")], "0.72")
        self.assertEqual(new[INTENT_FIELDS.index("cred")], "CRED-g1-0001")

    def test_priority_out_of_range_rejected(self):
        r = run(self.d, "add-intent", "--title=坏分", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--priority=1.5", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    def test_priority_non_numeric_rejected(self):
        r = run(self.d, "add-intent", "--title=非数", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--priority=abc", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    def test_cred_reference_must_close(self):
        r = run(self.d, "add-intent", "--title=坏引用", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--cred=CRED-g1-9999", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("cred 引用闭合失败", r.stderr)

    def test_status_change_row_carries_columns(self):
        # 事件溯源：set-intent-status 追加行须携带 priority/cred 值（R-T3-2：INT-g1-0002）
        r = run(self.d, "add-intent", "--title=携带检查", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--priority=0.4", "--cred=CRED-g1-0001", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(self.d, "set-intent-status", "--id=INT-g1-0002", "--status=active",
                "--timestamp=2026-09-24T08:30:00Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [x for x in intent_rows(self.d) if x[0] == "INT-g1-0002"]
        self.assertGreaterEqual(len(rows), 2)
        pi = INTENT_FIELDS.index("priority")
        ci = INTENT_FIELDS.index("cred")
        self.assertEqual(rows[-1][pi], rows[0][pi])
        self.assertEqual(rows[-1][ci], rows[0][ci])


if __name__ == "__main__":
    unittest.main()
