# -*- coding: utf-8 -*-
"""battle-8（G-r9）金样锚：头名族/method 族缺口代+vault 链路首通。

v5 alt-form 双遍法钉：recall 18/56≈0.3214（beacon 18/diff 0）；missing 38；
21 EV 全 VERIFIED（含 vault 占位符 EV fail-closed 链路）；creds 1。
六代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29 / G-r8 0.38 / G-r9 0.32。"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r9')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 18.0 / 56)   # 头名族缺口代（token 携带形态未采）
        self.assertEqual(len(missing), 38)
        self.assertEqual(tracks['beacon'], 18)
        self.assertEqual(tracks['diff'], 0)
        self.assertNotIn('weakpass-01', missing)   # 键名族律保持兑现
        self.assertNotIn('redir-01', missing)      # redirect 参数族三代际最全收割
        self.assertIn('role-03', missing)          # 携带形态缺口→post_auth 再封（RT-0006）
        self.assertIn('deser-01', missing)         # 方法族缺口（GET 直取面 POST 脑补）

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 21)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
