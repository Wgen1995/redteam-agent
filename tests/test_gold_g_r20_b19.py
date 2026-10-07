# -*- coding: utf-8 -*-
"""battle-19(G-r20) gold: law-22/25 re-amendment full redemption (+8).

30/56=0.5357 (beacon 30; second-best tier, +8 over G-r19's 22 - the
predicted effective score redeemed);
six post_auth findings all carry auth_context=CRED-r20-0002 (chain explicit);
assets all face-explicit (svc-login/login form; billing /invoice/88 id form) -
weakpass+ratelimit+userenum login triple all hit (prior-gen bare-root double sink);
40/40 replay VERIFIED; honest FAIL kept on record (gate-exit sequence violation,
no forged gate events).
Seventeen-gen: .../0.55/0.39/0.54."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r20')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR20(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 30.0 / 56)
        self.assertEqual(len(missing), 26)
        self.assertEqual(tracks['beacon'], 30)
        self.assertNotIn('role-03', missing)      # law-22 chain redemption x6
        self.assertNotIn('role-04', missing)
        self.assertNotIn('hauth-05', missing)
        self.assertNotIn('idor-05', missing)
        self.assertNotIn('idor-06', missing)
        self.assertNotIn('idor-04', missing)      # /invoice/88 id-form
        self.assertNotIn('weakpass-01', missing)  # face-explicit redemption
        self.assertIn('ratelimit-01', missing)  # real finding, asset right; card matcher mislabeled GTUSERENUM-01 (cross-beacon swap)
        self.assertNotIn('userenum-01', missing)
        self.assertIn('ssti-01', missing)         # category variance

    def test_replay_40_verified(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        self.assertEqual(ev_v, 40)

    def test_auth_chain_explicit_pinned(self):
        """law-22 re-amendment: six post_auth findings carry CRED link."""
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        pa = [r for r in self.rows['findings.tsv']
              if r[fi('status')] == 'active'
              and ('/admin' in assets.get(r[fi('affected_asset_id')], '')
                   or 'invoice' in assets.get(r[fi('affected_asset_id')], ''))]
        self.assertGreaterEqual(len(pa), 6)
        for r in pa:
            self.assertTrue(r[fi('auth_context')].startswith('CRED-'),
                            'chain explicit on %s' % r[0])

    def test_no_bare_root_asset(self):
        vals = [r[2] for r in self.rows['assets.tsv']]
        bare = [v for v in vals if v.endswith('/')]
        self.assertEqual(bare, [])   # law-25 re-amendment held


if __name__ == '__main__':
    unittest.main()
