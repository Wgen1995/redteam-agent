# -*- coding: utf-8 -*-
"""battle-10(G-r11) gold: role semantics unlock gen.

v5: 21/56=0.3750 (beacon 21, diff 0); missing 35; 32 EV VERIFIED;
first post_auth gate hits: role-03/role-04/hauth-05.
Eight-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r11')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding="utf-8") as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 22.0 / 56)  # v7 键控上修（IP 形资产键找回）
        self.assertEqual(len(missing), 34)
        self.assertEqual(tracks['beacon'], 22)
        self.assertEqual(tracks['diff'], 0)
        self.assertNotIn('role-03', missing)   # law-22 unlock: first role-class hit
        self.assertNotIn('role-04', missing)   # law-22 unlock
        self.assertNotIn('hauth-05', missing)  # law-22 unlock: first hauth-class hit
        self.assertIn('idor-03', missing)      # svc-admin face 401->404: admin-level token needed
        self.assertIn('idor-05', missing)      # coverage gap: 3-service rescan only

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 32)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
