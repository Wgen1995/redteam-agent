# -*- coding: utf-8 -*-
"""battle-25(G-r26) gold: 0.57 (32/56) — op-1 REPRODUCTION NEGATIVE RESULT.

Four-cell matrix COMPLETE (RT-0023):
  op-1  bare+manual:   0.70 (single sample, outlier)
  b25   bare+engine:   0.57 (54 findings, only 32 EV replay-verified)
  b23   brief30+eng:   0.66
  b24   brief60+eng:   0.62 (amendment A rolled back)
  -> 0.70 did NOT reproduce under engine custody; BRIEF-30 is the best
     stable config. Bare mode = high variance, low verified-replay floor.
KEYING v7 born here: bare warrior books service-level assets (docker
IP:port) -> GT alias table + service-asset fallback via EV raw_request/
E-index desc URLs (pseudo-zero 0.00 -> true 0.57).
32/32 replay VERIFIED; five gates; restarts=0; timeline=930."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score, KEYING_VERSION  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r26')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR26(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        self.assertEqual(KEYING_VERSION, 7)
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 32.0 / 56)
        self.assertEqual(len(missing), 24)
        self.assertEqual(tracks['beacon'], 32)
        self.assertIn('sqli-01', missing)          # bare-mode spray cost
        self.assertIn('ssrf-02', missing)          # dict-family depth lost
        self.assertIn('deser-02', missing)

    def test_gates_and_replay_clean(self):
        tl = self.rows['timeline.tsv']
        gates = [r[3] for r in tl if r[3].startswith('gate-exit:')]
        self.assertEqual(len(gates), 5)
        seq = [g.split(':')[1].split()[0] for g in gates]
        self.assertEqual(seq, ['P0', 'P1', 'P2', 'P3', 'P4'])
        ev_v = {r[3].split(':')[1] for r in tl
                if 'replay:EV-' in r[3] and ':VERIFIED' in r[3]}
        self.assertEqual(len(ev_v), 32)           # honest: only 32 of 54 replayed
        self.assertFalse([r for r in tl
                          if 'replay:EV-' in r[3] and ':REJECTED' in r[3]])

    def test_v7_keying_service_asset_fallback(self):
        # bare warrior books docker IP service assets; GT aliases carry them now
        al = self.gt['host_aliases']
        self.assertIn('172.28.0.9:8001', al['svc-shop'])
        self.assertIn('172.28.0.7:8004', al['svc-login'])
        # service-level assets present (the v7 trigger condition)
        kinds = {r[1] for r in self.rows['assets.tsv']}
        self.assertIn('service', kinds)

    def test_findings_shape(self):
        fd = self.rows['findings.tsv']
        self.assertGreaterEqual(len(fd), 54)
        sup = set()
        with open(os.path.join(GD, 'edges.tsv'), encoding='utf-8') as f:
            for line in f:
                c = line.rstrip('\n').split('\t')
                if len(c) > 3 and c[1] == 'supersedes':
                    sup.add(c[3].strip())
        self.assertGreaterEqual(len(sup), 32)


if __name__ == '__main__':
    unittest.main()
