# -*- coding: utf-8 -*-
"""battle-26(G-r27) gold: 0.41 (23/56) — b11 gateloop arm-B NEGATIVE RESULT.

Three-metric adjudication vs arm A (b23 0.66) — RT-0024:
  score   A 0.66 (37/56)  vs  B 0.41 (23/56, all beacon track)
  restarts A 0            vs  B bright-period 0 / blind-period 5 (driver bug)
  token   A 380,548 bytes vs  B 561,066 bytes (1.47x)
  sessions A 1 long       vs  B >=4 per-gate fresh (resume-kit rebuild)
Verdict (single battle, confounds documented): per-gate session reset
loses ~0.25 recall vs continuous session; gateloop's real value is
observability (per-gate SLI P2 9.0m / P3 57.7m / P4 19.5m), not score.
Architectural outcome: advancement policy modelled as pluggable
(ai-self default | python-gate-loop ops/experiment harness).
Also pinned here: gateloop poll write-amplifier — 623 of 1422 timeline
rows are mechanical gate-fail noise (44%), expert-review P0 throttle fix.
KEYING v7; 28 findings; blind P0+P1 + bright P2/P3/P4; 86.3m bright total."""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score, KEYING_VERSION  # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r27')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR27(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        self.assertEqual(KEYING_VERSION, 7)
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 23.0 / 56)
        self.assertEqual(len(missing), 33)
        self.assertEqual(tracks.get('beacon'), 23)
        self.assertEqual(tracks.get('diff'), 0)
        # arm-B breadth losses (session-reset cost, RT-0024)
        self.assertIn('idor-04', missing)
        self.assertIn('jwt-02', missing)
        self.assertIn('csrf-02', missing)

    def test_gate_noise_pinned(self):
        # write-amplifier evidence for the P0 throttle fix: mechanical
        # gate-fail rows minted by the per-tick polling driver.
        # NOTE final composition 596/1422 = 42% (mid-battle peak observed
        # 623/1273 = 49%; rows grew while gate-fail count FELL — some
        # rewrite touched the timeline during P4; open question, see
        # RT-0024 §5).
        tl = os.path.join(GD, 'timeline.tsv')
        with open(tl, encoding='utf-8') as f:
            rows = [ln for ln in f if ln.strip()]
        self.assertEqual(len(rows), 1422)
        fails = sum(1 for ln in rows if 'gate-fail' in ln)
        self.assertEqual(fails, 596)
        self.assertGreater(fails / len(rows), 0.40)  # noise floor documented
        self.assertLess(fails / len(rows), 0.5)


if __name__ == '__main__':
    unittest.main()
