# -*- coding: utf-8 -*-
"""battle-11(G-r12) gold: law-23 full cross-product gen.

v5: 24/56=0.4286 (beacon 24); ceiling 0.38 -> 0.43; 31 EV VERIFIED;
five post_auth via 64/64 admin-noun cross-product.
Nine-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r12')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding="utf-8") as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 24.0 / 56)
        self.assertEqual(len(missing), 32)
        self.assertEqual(tracks['beacon'], 24)
        self.assertEqual(tracks['diff'], 0)
        self.assertNotIn('idor-05', missing)   # law-23 cross-product hit
        self.assertNotIn('idor-06', missing)   # law-23 cross-product hit
        self.assertNotIn('role-03', missing)   # repeat hit
        self.assertNotIn('role-04', missing)   # repeat hit
        self.assertNotIn('hauth-05', missing)  # repeat hit
        self.assertIn('idor-01', missing)      # admin-level wall (no tok-adm channel)
        self.assertIn('traversal-01', missing)  # generational face variance

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 31)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
