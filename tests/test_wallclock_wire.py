# -*- coding: utf-8 -*-
"""WC · wall_clock battle 接线（scripts/battle.py 三铸点）——外环墙钟轨测试。

契约（docs/superpowers/plans/2026-10-14-opsec-wallclock.md Task WC；审计
docs/reviews/2026-10-10-nine-expert-review/02-opsec.md 关键缺口1「授权窗
只在 P5 lint 查、guard exec 不查墙钟」——v0.7b 墙钟轨接进战斗外环）：

- battle.mint_wall(goal_dir, phase, note="")：payload=ledger.wallclock.
  event_text（detect_gaps 解析的单源格式），行写=ledger.timeline.
  append_tl_locked 单源写方（v0.8 Task W llmpool_wire 先例——goal 锁内
  读表→算链→写回）；actor="battle"（外环工具名，llmpool 先例），
  phase="P-lifecycle"（跨阶段基础设施轨，wallclock 先例），行 ts=负载
  wall= 值（行与负载墙钟严格同源）。已知偏差：wallclock.mint_wall_sync
  经 phases_engine._append_event 旧路因签名漂移（ts 必填化）现调即
  TypeError，且 wallclock.py 不在本任务白名单——接线不经它。
- fail-open 观测轨语义：账本未生（agent 模式 init/launch 正常态）跳过
  返回 None 不建文件；账本损坏铸造失败返回 None 零半写、不外抛——
  墙钟轨不炸战斗主流程。
- battle.wall_gaps(goal_dir)：timeline 行过 wallclock.detect_gaps——
  settle 侧断连窗口检出的接线面。
- 三铸点源码钉（v08w TestSingleSourceWriterPin 先例）：cmd_init→
  phase=init；cmd_launch→phase=launch；cmd_settle→phase=settle 且铸点
  在 verify-chain 之前（clock-sync 自身入结算链断言覆盖）。
"""
import datetime
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
import battle                   # noqa: E402 （scripts/battle.py，模块级零副作用）
from ledger import core         # noqa: E402
from ledger import timeline     # noqa: E402
from ledger import wallclock    # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
BATTLE_SRC = os.path.join(HERE, "..", "scripts", "battle.py")


class WireBase(unittest.TestCase):
    """夹具 G-g1 副本（timeline 8 行链有效）——v08w WireBase 同款。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp(prefix="wc-wire-")
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        with open(BATTLE_SRC, encoding="utf-8") as f:
            self.src = f.read()

    def tearDown(self):
        shutil.rmtree(self.gd, ignore_errors=True)

    def tl_rows(self):
        return core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)

    def tl_bytes(self):
        with open(os.path.join(self.gd, "timeline.tsv"), "rb") as f:
            return f.read()

    def assert_chain_ok(self):
        ok, bad = core.Session(self.gd).verify_chain()
        self.assertTrue(ok, "timeline 链断于第 %d 行" % bad)

    def body(self, fn):
        """源码钉辅助：截取 battle.py 某 cmd_* 函数体（到下一个 def 为止）。"""
        self.assertIn("def %s(" % fn, self.src, "battle.py 缺 %s" % fn)
        return self.src.split("def %s(" % fn)[1].split("\ndef ")[0]


class TestMintWall(WireBase):
    """铸造行为：clock-sync 行入链+格式单源+fail-open 双态。"""

    def test_mint_appends_clock_sync_row_and_chain_verifies(self):
        ev = battle.mint_wall(self.gd, "launch", "battle-1,runner-pid=42")
        self.assertTrue(ev.startswith("clock-sync wall="))   # detect_gaps 可解析格式
        self.assertIn("phase=launch", ev)
        self.assertIn("note=battle-1,runner-pid=42", ev)
        rows = self.tl_rows()
        self.assertEqual(len(rows), 9)                       # 夹具 8 行 + 铸点 1 行
        last = rows[-1]
        wall = ev.split("wall=")[1].split()[0]
        self.assertEqual(last[0], wall)                      # 行 ts=负载 wall= 值
        self.assertEqual(last[1], "battle")                  # actor=外环工具名
        self.assertEqual(last[2], "P-lifecycle")             # 跨阶段基础设施轨
        self.assertEqual(last[3], ev)
        self.assertEqual(last[4], "")                        # revert 空
        self.assertEqual(last[7], "2")                       # schema_version
        self.assert_chain_ok()

    def test_three_phases_init_launch_settle_dense_no_gap(self):
        for ph in ("init", "launch", "settle"):
            self.assertTrue(battle.mint_wall(self.gd, ph, "battle-2"))
        rows = self.tl_rows()
        self.assertEqual(len(rows), 11)                      # 夹具 8 + 三铸点
        self.assertEqual(
            [r[3].split("phase=")[1].split()[0] for r in rows[-3:]],
            ["init", "launch", "settle"])
        self.assert_chain_ok()
        # 与 v0.7b 纯函数面互通：秒级间隔不构成断连窗口
        self.assertEqual(wallclock.detect_gaps(rows), [])

    def test_unborn_ledger_skips_fail_open(self):
        gd2 = tempfile.mkdtemp(prefix="wc-unborn-")          # 空目录：agent 模式 init 态
        self.addCleanup(lambda: shutil.rmtree(gd2, ignore_errors=True))
        self.assertIsNone(battle.mint_wall(gd2, "init", "battle-3"))
        self.assertFalse(os.path.exists(os.path.join(gd2, "timeline.tsv")))

    def test_corrupt_ledger_fail_open_zero_halfwrite(self):
        # 真实失败注入（非 mock）：timeline.tsv 追加列数坏行 → 单源写方读表即炸
        with open(os.path.join(self.gd, "timeline.tsv"), "a", encoding="utf-8") as f:
            f.write("坏行\t两列" + chr(10))
        before = self.tl_bytes()
        self.assertIsNone(battle.mint_wall(self.gd, "settle", "battle-4"))
        self.assertEqual(self.tl_bytes(), before)            # 零半写：坏账本未被动过


class TestWallGaps(WireBase):
    """settle 侧断连窗口检出接线：timeline 行过 wallclock.detect_gaps。"""

    def test_stale_window_between_clock_syncs_reported(self):
        old = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        timeline.append_tl_locked(                           # 种一枚 2h 前的 clock-sync
            self.gd, old, "clock-sync wall=%s phase=P3" % old,
            "battle", "P-lifecycle")
        self.assertTrue(battle.mint_wall(self.gd, "settle", "battle-5"))
        gaps = battle.wall_gaps(self.gd)
        self.assertEqual(len(gaps), 1)
        self.assertIn("phase=settle", gaps[0][0])            # 嫌疑窗指向后一枚
        self.assertGreater(gaps[0][1], 7100)                 # ≈2h（留执行余量）
        self.assertLess(gaps[0][1], 7300)
        self.assert_chain_ok()

    def test_dense_track_no_gap(self):
        battle.mint_wall(self.gd, "init", "battle-6")
        battle.mint_wall(self.gd, "settle", "battle-6")
        self.assertEqual(battle.wall_gaps(self.gd), [])


class TestBattleWiringPin(WireBase):
    """源码钉（v08w TestSingleSourceWriterPin 先例）：三铸点在位+顺序+单源写方。"""

    def test_init_launch_settle_mint_points_wired(self):
        for fn, ph in (("cmd_init", "init"), ("cmd_launch", "launch"),
                       ("cmd_settle", "settle")):
            self.assertIn('mint_wall(p["goal"], "%s"' % ph, self.body(fn),
                          "%s 缺 phase=%s 铸点" % (fn, ph))

    def test_settle_mints_before_verify_chain(self):
        body = self.body("cmd_settle")
        # 针取真实调用 ledger("verify-chain" 而非裸词——注释提及 verify-chain
        # 不应误判（首版裸词针命中自家注释的实证修正）
        self.assertLess(body.index("mint_wall("), body.index('ledger("verify-chain"'),
                        "settle 铸点须在 verify-chain 前——clock-sync 自身入链断言覆盖")

    def test_single_source_writer_no_private_mint(self):
        self.assertIn("append_tl_locked", self.src)          # 单源写方在位
        self.assertIn("event_text", self.src)                # payload 格式单源（wallclock）
        self.assertNotIn("row_hash(", self.src)              # 不私铸链行
        self.assertNotRegex(self.src, r"(?m)^def (chained_row|append_tl)\b")


if __name__ == "__main__":
    unittest.main()
