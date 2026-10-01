# -*- coding: utf-8 -*-
"""battle-5 金样 G-r6 收编钉（双轨首证锚）。

G-r6 = battle-5 独立战士会话（2026-10-02）：门控 0.38（beacon 18+diff 1=史上首枚差分轨命中）；
P4 27/27 VERIFIED 零强改；九门 P0-P4 全 PASS。钉住双轨分解与 v4 键形行为。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r6')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.gt = json.load(open(GT, encoding='utf-8'))
        cls.rows, cls.cards = load_session(GD)

    def test_dual_track_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 19.0 / 56)   # battle-6 认证加权：19/56
        self.assertEqual(len(missing), 37)
        self.assertEqual(tracks['beacon'], 19)   # v4.1 归因归真：ratelimit-01 词证归位
        self.assertEqual(tracks['diff'], 0)   # v4.1 两遍法：词证先耗用——FD-r6-0021 归 ratelimit-01（GTRATE-01 在卡），weakpass-01 移 miss

    def test_replay_all_verified(self):
        n = 0
        for r in self.rows['timeline.tsv'][1:]:
            ev = r[3]
            if ev.startswith('replay:') and ':VERIFIED' in ev:
                n += 1
        self.assertEqual(n, 27)   # 27/27 零强改


if __name__ == '__main__':
    unittest.main()
