# -*- coding: utf-8 -*-
"""battle-16(G-r17) gold: law-23 dual-form + dict v3.7 redemption, REPAIRED-rail debut.

25/56=0.4464 (beacon 25); idor-04 redeemed (invoice/{1,2,88} dual-form);
graphql-01 + ratelimit-01 redeemed via dict v3.7; 31/31 replay VERIFIED
with 2 first-attempt not-reproduced fixed via card repair (REPAIRED rail);
xss-02/cors-02/traversal-02 second-face-of-family misses (four families
booked only their first face).
Fourteen-gen: .../0.43/0.34/0.46/0.45."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r17')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 25.0 / 56)
        self.assertEqual(len(missing), 31)
        self.assertEqual(tracks['beacon'], 25)
        self.assertNotIn('idor-04', missing)     # law-23 dual-form redemption
        self.assertNotIn('graphql-01', missing)  # dict v3.7 redemption
        self.assertNotIn('ratelimit-01', missing)
        self.assertNotIn('ssrf-01', missing)     # fourth straight triple
        self.assertIn('xss-02', missing)         # second-face-of-family miss
        self.assertIn('cors-02', missing)
        self.assertIn('redir-03', missing)       # fourth straight gen
        self.assertIn('userenum-01', missing)    # honest negative

    def test_replay_31_verified(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        ev_r = sum(1 for r in tl if 'replay:EV-' in r[3] and ':REJECTED' in r[3])
        self.assertEqual(ev_v, 31)   # 31/31 all verified
        self.assertEqual(ev_r, 0)

    def test_resource_dual_form_asset(self):
        vals = [r[2] for r in self.rows['assets.tsv']]
        import re as _re
        self.assertTrue(any(_re.search(r'/invoice/\d+$', v) for v in vals),
                        'law-25/23: invoice face booked with concrete id tail')


if __name__ == '__main__':
    unittest.main()
