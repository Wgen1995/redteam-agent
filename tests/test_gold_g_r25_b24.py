# -*- coding: utf-8 -*-
"""battle-24(G-r25) gold: 0.62 (35/56) — AMENDMENT-A NEGATIVE RESULT.

Controlled verdict (RT-0022): wide-matrix 60-face tier ROLLED BACK.
  b23 BRIEF-30face+dict3.13: 0.66 (37/56)
  b24 BRIEF-60face+dict3.14: 0.62 (35/56)  net -2
  gains: cors-01 (dict v3.14 origin-quartet — DICT credit, not matrix)
  losses: userenum-01/xxe-01/traversal-02 (spray diluted dict-family depth)
Third datapoint vs op-1 bare 264-face 0.70: unconstrained spray + dict family
both needed; 60-face tier got neither discipline nor breadth.
46/46 EV VERIFIED; five gates; engine interruptions survived (NameError fix,
network-stall kill, three relaunches, ledger continuity 285->495).
Twenty-five datapoints: .../0.59/0.70(op-1)/0.66(b23)/0.62(b24-A/B)."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r25')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR25(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 35.0 / 56)
        self.assertEqual(len(missing), 21)
        self.assertEqual(tracks['beacon'], 35)
        # v3.14 cors origin quartet landed (DICT credit — the one keeper)
        self.assertNotIn('cors-01', missing)
        # spray-dilution regressions vs b23 (amendment-A cost — rollback basis)
        for gt_id in ('userenum-01', 'xxe-01', 'traversal-02'):
            self.assertIn(gt_id, missing)
        # lfi dual-form dict addition did NOT land (kept as annotated miss)
        self.assertIn('lfi-01', missing)
        # structural admin-wall faces still unreachable (range-v2 domain)
        for gt_id in ('role-01', 'hauth-01', 'hauth-04'):
            self.assertIn(gt_id, missing)

    def test_gates_and_replay_clean(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])
        ev_v = {r[3].split(':')[1] for r in tl
                if 'replay:EV-' in r[3] and ':VERIFIED' in r[3]}
        self.assertEqual(len(ev_v), 46)
        self.assertFalse([r for r in tl
                          if 'replay:EV-' in r[3] and ':REJECTED' in r[3]])

    def test_findings_shape(self):
        fd = self.rows['findings.tsv']
        self.assertEqual(len(fd), 47)
        sup = set()
        with open(os.path.join(GD, 'edges.tsv'), encoding='utf-8') as f:
            for line in f:
                c = line.rstrip('\n').split('\t')
                if len(c) > 3 and c[1] == 'supersedes':
                    sup.add(c[3].strip())
        self.assertEqual(len(sup), 2)
        ids = [r[0] for r in fd]
        self.assertEqual(len(ids), 47)              # rows incl. supersede-flow re-adds
        self.assertEqual(len(set(ids)), 45)        # 2 ids re-booked via supersede
        self.assertEqual(len(set(ids) - sup), 43)  # active after edge removal

    def test_engine_survival_provenance(self):
        tl = self.rows['timeline.tsv']
        # scenario clock battle-24 = 2026-10-21 (engine battle.py init)
        self.assertTrue(any(r[0].startswith('2026-10-21') for r in tl[1:]))
        # cors landed via dict quartet: GTCORS token anywhere in its rows (EV summary col)
        fd = self.rows['findings.tsv']
        self.assertTrue([r for r in fd if any('GTCORS-01' in c for c in r)])


if __name__ == '__main__':
    unittest.main()
