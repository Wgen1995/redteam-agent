# -*- coding: utf-8 -*-
"""battle-18(G-r19) gold: law-29 beacon-in-card redemption; two booking-form
regressions pinned (auth_context chain-break x7; bare-root asset).

22/56=0.3929 (beacon 22; effective ~29 lost to booking form);
GTRATE-01 counter beacon redeemed (law-29 debut);
post_auth seven findings booked with EMPTY auth_context -> authz gate blocks
(role-03/04, hauth-05, idor-05/06, idor-04 - all real, chain unlinked);
weakpass-01 asset booked as bare-root 'svc-login/' (trailing slash, no face).
Sixteen-gen: .../0.34/0.46/0.45/0.55/0.39."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r19')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 22.0 / 56)
        self.assertEqual(len(missing), 34)
        self.assertEqual(tracks['beacon'], 22)
        self.assertIn('ratelimit-01', missing)   # card HAS GTRATE-01 word; bare-root asset sinks it
        self.assertNotIn('redir-03', missing)
        self.assertIn('role-03', missing)           # auth_context chain-break x7
        self.assertIn('idor-04', missing)
        self.assertIn('hauth-05', missing)
        self.assertIn('weakpass-01', missing)       # bare-root asset form
        self.assertIn('userenum-01', missing)       # gen-variance face

    def test_replay_42_verified(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        self.assertEqual(ev_v, 42)   # 42/42 all verified

    def test_auth_context_chain_break_pinned(self):
        """post_auth findings booked with empty auth_context - pinned for record."""
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        pa = [r for r in self.rows['findings.tsv']
              if r[fi('status')] == 'active'
              and ('/admin' in assets.get(r[fi('affected_asset_id')], '')
                   or 'invoice' in assets.get(r[fi('affected_asset_id')], ''))]
        self.assertGreaterEqual(len(pa), 7)
        for r in pa:
            self.assertEqual(r[fi('auth_context')], '',
                             'chain-break: auth_context empty on %s' % r[0])

    def test_bare_root_asset_pinned(self):
        vals = [r[2] for r in self.rows['assets.tsv']]
        self.assertIn('svc-login/', vals)   # form variant #5, pinned


if __name__ == '__main__':
    unittest.main()
