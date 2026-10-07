# -*- coding: utf-8 -*-
"""battle-21(G-r22) gold: law-31 + dict-v3.11 redemption; docker-cp incident
with deterministic rebuild; honest SSTI replay-drift downgrade.

31/56=0.5536 ties second-best (beacon 31);
weakpass redeemed on its own row (asset=svc-login/login - law-31);
xss-03/xss-04 landed (four-face enumeration - dict v3.11);
SSTI downgraded to C3/suspected after replay drift (2 EV REJECTED - honest
cost correctly paid); rebuilt chain verify PASS 548 rows 5 gates 0 skips.
Nineteen-gen: .../0.39/0.54/0.52/0.55."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r22')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR22(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 31.0 / 56)
        self.assertEqual(len(missing), 25)
        self.assertEqual(tracks['beacon'], 31)
        self.assertNotIn('weakpass-01', missing)   # law-31 redemption (own row)
        self.assertNotIn('xss-03', missing)        # dict v3.11 four faces
        self.assertNotIn('xss-04', missing)
        self.assertNotIn('role-03', missing)       # chain explicit held
        self.assertIn('ssti-01', missing)          # honest replay-drift downgrade
        self.assertIn('cmdi-01', missing)
        self.assertIn('hauth-04', missing)         # admin wall structural

    def test_gates_ordered_after_rebuild(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])

    def test_ssti_honest_downgrade_pinned(self):
        """2 EV REJECTED (replay drift) + findings downgraded to suspected -
        honesty must cost score, and here it did."""
        tl = self.rows['timeline.tsv']
        rej = {r[3].split(':')[1] for r in tl
               if 'replay:EV-' in r[3] and ':REJECTED' in r[3]}
        self.assertEqual(len(rej), 2)   # 2 distinct EVs (retried once each)
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        suspected = [r for r in self.rows['findings.tsv']
                     if r[fi('status')] == 'active'
                     and (r[fi('confidence')] or '') == 'C3']
        self.assertGreaterEqual(len(suspected), 2)   # redir + ssti pair

    def test_weakpass_own_row_pinned(self):
        from tests.eval_range_recall import _word_markers
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        for r in self.rows['findings.tsv']:
            if r[fi('status')] != 'active':
                continue
            evs = [x for x in (r[fi('evidence_ids')] or '').split(';') if x]
            if 'GTWEAKPASS-01' in _word_markers(self.cards, evs):
                self.assertEqual(assets.get(r[fi('affected_asset_id')]),
                                 'svc-login/login')   # law-31: own row, own face


if __name__ == '__main__':
    unittest.main()
