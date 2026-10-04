# -*- coding: utf-8 -*-
"""battle-15(G-r16) gold: law-22 bare-word redemption + law-27 debut.

26/56=0.4643 (beacon 26, second-best ever); creds roles bare-word
admin/user -> six post_auth redeemed (role-03/04, hauth-05, idor-05/06);
36/36 replay VERIFIED zero REJECTED (no self-collapse);
xss-01/02 redeemed via dict v3.6 (xss-03/04 still missing).
Thirteen-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43/0.59/0.43/0.34/0.46."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r16')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 26.0 / 56)
        self.assertEqual(len(missing), 30)
        self.assertEqual(tracks['beacon'], 26)
        self.assertNotIn('role-03', missing)    # law-22 bare-word redemption
        self.assertNotIn('role-04', missing)
        self.assertNotIn('hauth-05', missing)
        self.assertNotIn('idor-05', missing)
        self.assertNotIn('idor-06', missing)
        self.assertNotIn('weakpass-01', missing)  # double hit, evidence-first
        self.assertNotIn('xss-01', missing)     # dict v3.6 half-redemption
        self.assertNotIn('xss-02', missing)
        self.assertNotIn('ssrf-01', missing)    # third straight gen triple
        self.assertIn('idor-04', missing)       # face variance: billing 403 wall
        self.assertIn('graphql-01', missing)    # gen-variance case three

    def test_replay_all_verified_ev_key(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        ev_r = sum(1 for r in tl if 'replay:EV-' in r[3] and ':REJECTED' in r[3])
        fd_v = sum(1 for r in tl if 'replay:FD-' in r[3])
        self.assertEqual(ev_v, 36)   # 36/36 all verified, zero REJECTED
        self.assertEqual(ev_r, 0)    # no self-collapse this gen (law-27 debut)
        self.assertEqual(fd_v, 0)    # law-26 standard form held

    def test_creds_roles_bare_word(self):
        roles = {r[2] for r in self.rows['creds.tsv']}
        self.assertEqual(roles, {'admin', 'user'})   # law-22 strict enum


if __name__ == '__main__':
    unittest.main()
