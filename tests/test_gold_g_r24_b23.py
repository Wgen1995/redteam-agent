# -*- coding: utf-8 -*-
"""battle-23(G-r24) gold: 0.66 (37/56) — first FULLY-ENGINE battle
(battle.py init+launch, runner gate-exit:P4 completion criterion,
zero manual intervention, restarts=0); BRIEF-33 + dict-v3.13 first combat.

Cross-runtime A/B (same opencode+GLM-5.3 warrior):
  op-1  bare-skill  wide-matrix(264): 0.70 (39/56), 39 findings
  b-23  BRIEF-33    matrix 144:       0.66 (37/56), 41 active+11 superseded
  -> wide-matrix beats narrow-BRIEF on recall (+3 GT) at 2x recon faces;
     BRIEF wins precision-material discipline (supersede chains, honest P5 FAIL).
55/55 EV VERIFIED after one honest EV-r24-0035 fix+re-replay;
five gates zero skips; P5 FAIL at human signoff (designed, honest);
verify-chain PASS; GT zero-read attested via probe-output correspondence.
Twenty-three datapoints: .../0.59/0.70(op-1 cross-runtime)/0.66."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r24')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR24(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 37.0 / 56)
        self.assertEqual(len(missing), 19)
        self.assertEqual(tracks['beacon'], 37)
        self.assertEqual(tracks.get('diff', 0), 0)
        # dict v3.13 parallel redirect family: all three redirect GT hit
        for gt_id in ('redir-01', 'redir-02', 'redir-03'):
            self.assertNotIn(gt_id, missing)   # jump?u=/logout?next=/redirect 双参
        # structural-unreachable annotation holds: admin-token faces still miss
        for gt_id in ('hauth-01', 'role-01', 'role-02'):
            self.assertIn(gt_id, missing)
        # engine-battle variance faces (BRIEF narrow-matrix cost vs op-1)
        self.assertIn('cors-01', missing)
        self.assertIn('lfi-01', missing)
        self.assertIn('cmdi-02', missing)

    def test_gates_and_replay_clean(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])
        ev_v = {r[3].split(':')[1] for r in tl
                if 'replay:EV-' in r[3] and ':VERIFIED' in r[3]}
        self.assertEqual(len(ev_v), 55)          # all cards verified post-fix
        self.assertFalse([r for r in tl
                          if 'replay:EV-' in r[3] and ':REJECTED' in r[3]])

    def test_active_findings_shape(self):
        fd = self.rows['findings.tsv']
        self.assertEqual(len(fd), 68)             # 67 booked, no header row
        sup = set()
        with open(os.path.join(GD, 'edges.tsv'), encoding='utf-8') as f:
            for line in f:
                c = line.rstrip('\n').split('\t')
                if len(c) > 3 and c[1] == 'supersedes':
                    sup.add(c[3].strip())
        active_ids = {r[0] for r in fd} - sup
        self.assertEqual(len(active_ids), 56 - 15)  # 41 active after 11 supersedes
        # one-vuln-one-row (law 31): weakpass holds own face rows
        wp = [r for r in fd if 'GTWEAKPASS-01' in r[2]]
        self.assertTrue(wp)

    def test_engine_provenance(self):
        tl = self.rows['timeline.tsv']
        # scenario clock battle-23 = 2026-10-20 (engine battle.py init)
        self.assertTrue(any(r[0].startswith('2026-10-20') for r in tl[1:]))


if __name__ == '__main__':
    unittest.main()
