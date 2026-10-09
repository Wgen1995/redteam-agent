# -*- coding: utf-8 -*-
"""battle-12(G-r13) gold: all-time record gen + asset-key form variants.

v5: 33/56=0.5893 (beacon 33); record 0.50 -> 0.59; 37 EV VERIFIED;
post_auth five-peat + traversal x2 + rail-switch double exemplar.
Ten-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43/0.59."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r13')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding="utf-8") as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 35.0 / 56)  # v7 键控上修（IP 形资产键找回）
        self.assertEqual(len(missing), 21)
        self.assertEqual(tracks['beacon'], 35)
        self.assertEqual(tracks['diff'], 0)
        self.assertNotIn('traversal-01', missing)   # dict v3.4 every-gen rule
        self.assertNotIn('idor-05', missing)        # post_auth five-peat
        self.assertNotIn('idor-06', missing)
        self.assertNotIn('ratelimit-01', missing)  # v7 键控上修：IP 形资产键找回（原 asset-key drift 面修复）
        self.assertNotIn('idor-04', missing)      # v7 键控上修：{n} 尾段归一面找回

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 38)   # 37 EV + drill EV re-verified (warrior report)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
