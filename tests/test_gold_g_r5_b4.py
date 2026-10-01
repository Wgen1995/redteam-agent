# -*- coding: utf-8 -*-
"""battle-4 金样 G-r5 收编钉（负样本锚）。

G-r5 = battle-4 独立战士会话（2026-10-01）：门控 0.24 / 行为面 23 / P4 重放 30 VERIFIED 零强改。
钉住：scorer 键形/门控行为变化时此锚漂移须显式重定标（如 v4 键形落地）。
对照 G-r4（0.56）：两代战士策略差异（广撒 vs 深挖）+wave1 dedup 陷阱=教学缺口实证。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r5')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.gt = json.load(open(GT, encoding='utf-8'))
        cls.rows, cls.cards = load_session(GD)

    def test_gated_recall_pinned(self):
        rec, missing = score(self.rows, self.cards, self.gt)
        self.assertAlmostEqual(rec, 12.0 / 56)   # battle-6 认证加权：12/56
        self.assertEqual(len(missing), 44)

    def test_replay_all_verified_no_forcing(self):
        verified, blocked = set(), set()
        for ln in self.rows['timeline.tsv'][1:]:
            f = ln.split('\t') if isinstance(ln, str) else ln
            ev = f[3] if len(f) > 3 else ''
            if ev.startswith('replay:') and ':VERIFIED' in ev:
                verified.add(ev.split(':')[1])
        self.assertEqual(len(verified), 30)   # 30/30 零强改


if __name__ == '__main__':
    unittest.main()
