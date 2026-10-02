# -*- coding: utf-8 -*-
"""battle-9（G-r10）金样锚：响应头采集兑现+role 语义拦代。

v5 双遍法钉：recall 19/56≈0.3393（beacon 18+diff 1——v4.1 后首枚差分）；
missing 37；42 EV 全 VERIFIED；creds 2；deser GET 直取三面首中。
七代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29 / G-r8 0.38 / G-r9 0.32 / G-r10 0.34。"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r10')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 19.0 / 56)   # role 语义拦代（11 枚 post_auth 在账被拦）
        self.assertEqual(len(missing), 37)
        self.assertEqual(tracks['beacon'], 18)
        self.assertEqual(tracks['diff'], 1)      # v4.1 后首枚差分轨命中
        self.assertNotIn('deser-01', missing)    # GET 直取律首验三中
        self.assertNotIn('sqli-01', missing)     # 参数面族首中
        self.assertIn('weakpass-01', missing)    # 卡词行为串无 marker（RT-0007 归因 2）
        self.assertIn('role-03', missing)        # role=admin≠user 语义拦（RT-0007 归因 1）

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 42)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
