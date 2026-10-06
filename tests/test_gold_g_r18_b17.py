# -*- coding: utf-8 -*-
"""battle-17(G-r18) gold: dict v3.8 second-face redemption at scale.

31/56=0.5536 (beacon 31, second-best; record 0.5893 at G-r13).
Second faces redeemed: xss-02/04, cors-02, traversal-02, infoleak-03;
redir-03 four-gen streak broken (jump?u= full external URL form);
userenum-01 redeemed (forgot?user=).
ratelimit-01 booked-real but card matcher lacked GT beacon string (GTRATE-01);
cmdi-01/02 + ssti-01 honestly suspected (scorer correctly excludes suspected).
Fifteen-gen: .../0.34/0.46/0.45/0.55."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r18')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR18(unittest.TestCase):
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
        self.assertNotIn('redir-03', missing)     # four-gen streak broken
        self.assertNotIn('xss-02', missing)       # second-face redemptions
        self.assertNotIn('cors-02', missing)
        self.assertNotIn('traversal-02', missing)
        self.assertNotIn('infoleak-03', missing)
        self.assertNotIn('userenum-01', missing)
        self.assertNotIn('idor-05', missing)      # five-peat holds
        self.assertIn('ratelimit-01', missing)    # card matcher gap: no GTRATE-01 string
        self.assertIn('ssti-01', missing)         # honest suspected excluded

    def test_replay_63_verified_ev_key(self):
        tl = self.rows['timeline.tsv']
        ev_v = sum(1 for r in tl if 'replay:EV-' in r[3] and ':VERIFIED' in r[3])
        fd_v = sum(1 for r in tl if 'replay:FD-' in r[3])
        self.assertGreaterEqual(ev_v, 63)   # 63 cited EVs verified, standard form
        self.assertEqual(fd_v, 0)

    def test_ratelimit_card_gap_pinned(self):
        """FD-r18-0041 real finding, EV verified, endpoint right - but card
        matchers lack the GT beacon string (only 'denied'). Pinned for the record."""
        words = set()
        for r in self.rows['findings.tsv']:
            if r[0] == 'FD-r18-0041':
                evs = [x for x in (r[10] or '').split(';') if x]
                words = {w for w in self._words(evs)}
        self.assertNotIn('GTRATE-01', words)   # the gap, pinned

    def _words(self, ev_ids):
        from tests.eval_range_recall import _word_markers
        return _word_markers(self.cards, ev_ids)


if __name__ == '__main__':
    unittest.main()
