# -*- coding: utf-8 -*-
"""battle-6（G-r7）金样锚：新面首战 56 分母（端口异构+认证加权+摩擦面）。

v4.1 两遍法后钉：recall 16/56≈0.2857（beacon 16/diff 0）；missing 40；
21 EV 全 VERIFIED（零强改）；post_auth 16 靶全 miss（凭据 0——键名族缺口）。
四代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29。"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r7')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 16.0 / 56)   # 新面首战（56 分母）
        self.assertEqual(len(missing), 40)
        self.assertEqual(tracks['beacon'], 16)
        self.assertEqual(tracks['diff'], 0)

    def test_replay_all_verified(self):
        tl = [r for r in self.rows['timeline.tsv'][1:]]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 21)   # 21 EV 全 VERIFIED
        self.assertEqual(forced, 0)      # 零强改


if __name__ == '__main__':
    unittest.main()
