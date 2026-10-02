# -*- coding: utf-8 -*-
"""battle-7（G-r8）金样锚：键名族首破凭据墙+post_auth 首命中。

GT v5 钉：recall 21/56≈0.375（beacon 21/diff 0；idor-01/02 alt-form 孪生键归位）；missing 35；
26 EV 全 VERIFIED；creds 2（admin/admin123→tok-usr-001 跨服务信任链）；
idor-03=史上首枚 post_auth GT 命中（authz-diff intent 链）。
五代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29 / G-r8 0.34。"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import load_session, score   # noqa: E402

GD = os.path.join(HERE, 'fixtures', 'G-r8')
GT = os.path.join(HERE, 'range', 'ground-truth.json')


class TestGoldGR8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GT, encoding='utf-8') as f:
            cls.gt = json.load(f)
        cls.rows, cls.cards = load_session(GD)

    def test_recall_pinned(self):
        tracks = {}
        rec, missing = score(self.rows, self.cards, self.gt, tracks=tracks)
        self.assertAlmostEqual(rec, 21.0 / 56)   # GT v5 重算：idor-01/02 alt-form 归位（实已找到）
        self.assertEqual(len(missing), 35)
        self.assertEqual(tracks['beacon'], 21)
        self.assertEqual(tracks['diff'], 0)
        self.assertNotIn('weakpass-01', missing)   # 凭据墙破（键名族叉乘律）
        self.assertNotIn('redir-01', missing)      # redirect 族字典兑现
        self.assertNotIn('idor-01', missing)      # v5 alt-form：path 形记账经孪生键命中
        self.assertNotIn('idor-02', missing)
        self.assertNotIn('idor-03', missing)       # 史上首枚 post_auth 命中
        self.assertIn('role-03', missing)          # /admin/<noun> 两段式族盲区（RT-0005）

    def test_replay_all_verified(self):
        tl = self.rows['timeline.tsv'][1:]
        verified = sum(1 for r in tl if 'replay:' in r[3] and ':VERIFIED' in r[3])
        forced = sum(1 for r in tl if ':REPAIRED' in r[3] or ':REJECTED' in r[3])
        self.assertEqual(verified, 26)
        self.assertEqual(forced, 0)


if __name__ == '__main__':
    unittest.main()
