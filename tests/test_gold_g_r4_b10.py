# -*- coding: utf-8 -*-
"""批次 10 T3：G-r4 战果金样回归钉（automation 专家 P2）。

三轮战完整会话（精度门勘误后快照）入 fixtures——CI 对 scorer 演进做端到端
锁定：v3 键形+精度门+post_auth 链全链路 recall=0.56（28/50）；missing=22；
重放验证计数=32（34-2 勘误 REJECTED）；任何 scorer 回归即红。"""
import json, os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval_range_recall as E

GD = os.path.join(HERE, 'fixtures', 'G-r4')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.cards = E.load_session(GD)
        cls.gt = json.load(open(GT, encoding='utf-8'))

    def test_gold_recall_pinned(self):
        recall, missing = E.score(self.rows, self.cards, self.gt)
        self.assertAlmostEqual(recall, 0.50)   # battle-6 认证加权 50→56 分母扩
        self.assertEqual(len(missing), 28)   # battle-6：+6 新靶均未检出（分子不变）

    def test_gold_replay_verified_count(self):
        verified, blocked = E._replay_state(self.rows)
        self.assertEqual(len(verified & {r[0] for r in self.rows['E-index.tsv']}), 32)
        self.assertIn('EV-r4-0020', blocked)
        self.assertIn('EV-r4-0029', blocked)


if __name__ == '__main__':
    unittest.main()