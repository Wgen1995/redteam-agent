# -*- coding: utf-8 -*-
"""battle-13(G-r14) gold: law-25 asset-key gen + scorer v6 FD-alias.

v6: 24/56=0.4286 (beacon 24) after FD-key replay expansion (was 0.00);
prior ten gens zero drift; honest REJECTED propagates via FD chain.
Eleven-gen: 0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43/0.59/0.43."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r14')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding="utf-8") as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 24.0 / 56)
        self.assertEqual(len(missing), 32)
        self.assertEqual(tracks['beacon'], 24)
        self.assertNotIn('idor-04', missing)    # law-25 debut: /invoice/88 tail
        self.assertNotIn('idor-05', missing)     # law-23 five-peat
        self.assertIn('ratelimit-01', missing)   # honest REJECTED -> v6 blocks chain
        self.assertIn('ssrf-01', missing)        # SSRF family skipped this gen

    def test_replay_fd_keyed(self):
        tl = self.rows['timeline.tsv']
        fd_v = sum(1 for r in tl if 'replay:FD-' in r[3] and ':VERIFIED' in r[3])
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        self.assertEqual(fd_v, 24)   # FD-keyed lines (v6 consumes)
        self.assertEqual(ev_v, 0)


if __name__ == '__main__':
    unittest.main()
