# -*- coding: utf-8 -*-
"""battle-22(G-r23) gold: TIES ALL-TIME RECORD 0.5893; dict-v3.12 double
redemption; law-32 ops three-checks zero-incident; raw_request executable-message
lesson (45 cards first-round replay wipe -> fixed -> 100%).

33/56=0.5893 (beacon 33 - ties G-r13);
cmdi-01/02 landed (host-type tool faces /ping?host= /diag?host= after
cmd/exec/run/eval all 404 - deformation family breakthrough);
ssti-01/02 landed (three-shot differential adjudicated pre-card, zero replay drift);
45/45 EV VERIFIED, five gates zero skips, verify-chain 429 PASS.
Twenty-gen: .../0.39/0.54/0.52/0.55/0.59."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r23')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR23(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 33.0 / 56)
        self.assertEqual(len(missing), 23)
        self.assertEqual(tracks['beacon'], 33)
        self.assertNotIn('cmdi-01', missing)      # deformation family breakthrough
        self.assertNotIn('cmdi-02', missing)
        self.assertNotIn('ssti-01', missing)      # pre-card adjudication, no drift
        self.assertNotIn('ssti-02', missing)
        self.assertNotIn('weakpass-01', missing)  # held (own row)
        self.assertNotIn('ratelimit-01', missing)
        self.assertIn('idor-01', missing)         # admin wall structural
        self.assertIn('hauth-04', missing)
        self.assertIn('redir-03', missing)        # gen-variance (jump?u=)

    def test_gates_and_replay_clean(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])
        ev_v = {r[3].split(':')[1] for r in tl
                if 'replay:EV-' in r[3] and ':VERIFIED' in r[3]}
        self.assertEqual(len(ev_v), 45)
        rej = {r[3].split(':')[1] for r in tl
               if 'replay:EV-' in r[3] and ':REJECTED' in r[3]}
        self.assertEqual(rej, set())   # zero rejected final

    def test_cmdi_host_type_face_pinned(self):
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        faces = set()
        for r in self.rows['findings.tsv']:
            if r[fi('status')] != 'active':
                continue
            av = assets.get(r[fi('affected_asset_id')], '')
            if 'ping?host=' in av or 'diag?host=' in av:
                faces.add(av.split('?')[0])
        self.assertTrue({'svc-dashboard/ping', 'svc-dashboard/diag'} <= faces)

    def test_post_auth_chain_held(self):
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        pa = [r for r in self.rows['findings.tsv']
              if r[fi('status')] == 'active'
              and ('/admin' in assets.get(r[fi('affected_asset_id')], '')
                   or 'invoice' in assets.get(r[fi('affected_asset_id')], ''))]
        self.assertGreaterEqual(len(pa), 6)
        for r in pa:
            self.assertTrue(r[fi('auth_context')].startswith('CRED-'))


if __name__ == '__main__':
    unittest.main()
