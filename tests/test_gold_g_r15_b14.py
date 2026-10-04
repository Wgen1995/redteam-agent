# -*- coding: utf-8 -*-
"""battle-14(G-r15) gold: law-26 EV-key standard + dict v3.5 SSRF sweep.

19/56=0.3393 (beacon 19); role enum drift blocked 7 accounted findings
(six post_auth + idor-04) - effective 0.46 lost to booking form;
weakpass honest self-collapse (EV REJECTED -> suspected).
Twelve-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43/0.59/0.43/0.34."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r15')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 19.0 / 56)
        self.assertEqual(len(missing), 37)
        self.assertEqual(tracks['beacon'], 19)
        self.assertNotIn('ssrf-01', missing)    # dict v3.5 redemption: SSRF triple
        self.assertNotIn('ssrf-02', missing)
        self.assertNotIn('ssrf-03', missing)
        self.assertNotIn('trav', missing)       # every-gen sweep held
        self.assertIn('role-03', missing)       # role enum drift: 7 accounted blocked
        self.assertIn('idor-04', missing)       # user-ji vs user drift
        self.assertIn('weakpass-01', missing)   # honest self-collapse C3

    def test_replay_ev_key_standard(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        fd_v = sum(1 for r in tl if 'replay:FD-' in r[3])
        self.assertEqual(ev_v, 45)   # law-26: raw EV-key VERIFIED lines (42 EV + 3 drill; latest-state 40)
        self.assertEqual(fd_v, 0)    # no FD-key lines this gen

    def test_role_enum_drift_evidence(self):
        roles = {r[2] for r in self.rows['creds.tsv']}
        self.assertIn('user \u7ea7', roles)   # the drift, pinned for the record


if __name__ == '__main__':
    unittest.main()
