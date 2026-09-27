# -*- coding: utf-8 -*-
"""批次 7 T2：写命令并发安全（C1 并发半边）。红=专家 16 并发 add-fact 存活 5 行且双 PASS——
无锁下 Ctx.commit 全表重写=last-writer-wins 丢行。16 个独立子进程（真进程级并发）。

R-T2-1（夹具裁决）：反例夹具用 test_write_cmds 同款 tests/fixtures/G-g1 拷贝——计划片段的
fresh_drydir 空目无 goals/intents 行，add-fact 将因 Tier0/引用闭合=用法性失败（假红）；
台账反例需要 16 条全部合法的 add-fact 竞速才复现「存活 5 行」。argv 形=tests/test_write_cmds.py
现存 add-fact 正例原样（禁自造参数名）。"""
import os, shutil, subprocess, sys, tempfile, unittest
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import core

FIX = os.path.join(HERE, "fixtures", "G-g1")
CLI = os.path.join(ROOT, "cli", "tanyin-ledger")
NCOL = len(core.TABLES["facts.tsv"])

class TestGoalLock(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_sixteen_concurrent_add_fact_all_survive(self):
        gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        n0 = len(core.read_tsv(os.path.join(gd, "facts.tsv"), NCOL))
        def one(i):
            r = subprocess.run(
                [sys.executable, CLI, "add-fact", "--goal-dir", gd,
                 "--intent-id=INT-g1-0001", "--kind=port",
                 "--target=10.10.1.5", "--detail=443/tcp open",
                 "--confidence=0.9", "--timestamp=2026-09-27T00:%02d:00Z" % i],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
            return r.returncode, (r.stdout + r.stderr)[:200]
        with ThreadPoolExecutor(max_workers=16) as ex:
            results = list(ex.map(one, range(16)))
        bad = [(rc, o) for rc, o in results if rc != 0]
        self.assertEqual(bad, [], "16 并发全 rc=0（REJECT/崩溃都算失败）：%s" % bad[:3])
        facts = core.read_tsv(os.path.join(gd, "facts.tsv"), NCOL)
        self.assertEqual(len(facts), n0 + 16, "16 行一个不能少（专家反例：存活 5 行）")
        new_ids = [r[0] for r in facts[n0:]]
        self.assertEqual(len(set(new_ids)), 16, "新行 id 不得碰撞（last-writer-wins 特征）")
        r = subprocess.run([sys.executable, CLI, "verify-chain", "--goal-dir", gd],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0,
                         "并发后链完整（专家反例：双 PASS 假绿）: " + r.stdout + r.stderr)

    def test_lock_file_not_in_tables(self):
        self.assertNotIn(".lock", core.TABLES, "锁文件不进 13 表（fingerprint/金样零干扰）")
        from ledger import filelock
        with filelock.goal_lock(self.td.name):
            self.assertTrue(os.path.isfile(os.path.join(self.td.name, ".lock")))
