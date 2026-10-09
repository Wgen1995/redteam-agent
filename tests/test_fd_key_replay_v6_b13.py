# -*- coding: utf-8 -*-
"""battle-13 T3（v6 FD 键别名）TDD：G-r14 实证——重放行键 FD 形（replay:FD-xxx:VERIFIED）
语义等价（账本真值 verified），评分门须可消费。

红：FD 键行不解锁 EV→0 分（G-r14 实况）。绿：FD 键行按 findings 链展开为其全部 EV。
前代（EV 键）零漂移；FD 键 REJECTED 阻断同展开。"""
import json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score, KEYING_VERSION   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r14')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestFDKeyReplayV6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_version_bumped(self):
        self.assertEqual(KEYING_VERSION, 7)   # battle-25：v6→v7（服务级资产回退）；本钉随键控演进而移（battle-13 v5→v6 先例）

    def test_fd_keyed_replay_unlocks(self):
        """G-r14 全账 FD 键重放行（24 VERIFIED）——须按 findings 链展开为 EV。"""
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertGreater(rec, 0.30)   # 实况 ~0.5+；0 分=红
        self.assertNotIn('weakpass-01', missing)
        self.assertNotIn('idor-04', missing)   # 律 25 兑现：invoice/88 尾段

    def test_prior_gens_zero_drift(self):
        """v6 对 EV 键代（G-r4..G-r13）零漂移。"""
        expect = {'G-r4': 28, 'G-r5': 21, 'G-r6': 19, 'G-r7': 16, 'G-r8': 22,
                  'G-r9': 18, 'G-r10': 19, 'G-r11': 22,
                  'G-r12': 24, 'G-r13': 35}
        for g, n in expect.items():
            rows, cards = load_session(os.path.join(HERE, 'fixtures', g))
            t = {}
            rec, miss = score(rows, cards, self.gt, tracks=t)
            self.assertAlmostEqual(rec, n / 56, msg=g)


if __name__ == '__main__':
    unittest.main()
