# -*- coding: utf-8 -*-
"""battle-20(G-r21) gold: law-30 honored (five gates, zero skips);
two new miss-forms pinned (family face-drift render/report; asset mis-attach).

29/56=0.5179 (beacon 29);
SSTI booked with real computation (${7*7}->49) on /render face - GT anchors
/report face (GTSSTI-01): family face-drift pinned;
weakpass card word GTWEAKPASS-01 correct but finding attached to
svc-files/unserialize asset (merged into deser row): asset mis-attach pinned;
xss family: GT four faces (search/comment/reply/feedback), warrior hit two.
Eighteen-gen: .../0.39/0.54/0.52."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r21')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 29.0 / 56)
        self.assertEqual(len(missing), 27)
        self.assertEqual(tracks['beacon'], 29)
        self.assertNotIn('cmdi-01', missing)      # cmdi landed this gen
        self.assertNotIn('ratelimit-01', missing)
        self.assertNotIn('role-03', missing)      # chain explicit held
        self.assertNotIn('idor-04', missing)
        self.assertIn('ssti-01', missing)         # family face-drift (render vs report)
        self.assertIn('weakpass-01', missing)     # asset mis-attach (deser row)
        self.assertIn('xss-03', missing)          # family under-enumeration
        self.assertIn('xss-04', missing)
        self.assertIn('userenum-01', missing)     # gen-variance face

    def test_gates_ordered_zero_skip(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])   # law-30 held

    def test_ssti_real_computation_pinned(self):
        """/render SSTI finding carries real eval evidence (GTSSTI-02 word);
        GT anchors /report face - the face-drift record."""
        from tests.eval_range_recall import _word_markers
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        hit = []
        for r in self.rows['findings.tsv']:
            if r[fi('status')] != 'active':
                continue
            evs = [x for x in (r[fi('evidence_ids')] or '').split(';') if x]
            if 'GTSSTI-02' in _word_markers(self.cards, evs):
                hit.append(assets.get(r[fi('affected_asset_id')], ''))
        self.assertEqual(len(hit), 1)
        self.assertIn('render', hit[0])       # real eval on render face
        self.assertNotIn('report', hit[0])    # GT face not reached

    def test_weakpass_asset_misattach_pinned(self):
        from tests.eval_range_recall import _word_markers
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index
        assets = {r[0]: r[2] for r in self.rows['assets.tsv']}
        for r in self.rows['findings.tsv']:
            if r[fi('status')] != 'active':
                continue
            evs = [x for x in (r[fi('evidence_ids')] or '').split(';') if x]
            if 'GTWEAKPASS-01' in _word_markers(self.cards, evs):
                av = assets.get(r[fi('affected_asset_id')], '')
                self.assertNotIn('svc-login/login', av)   # mis-attached (deser row)


if __name__ == '__main__':
    unittest.main()
