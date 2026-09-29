# -*- coding: utf-8 -*-
"""批次 10 T5（P2#9）：timeline 铸造单源 ledger.timeline。

八专家架构 P2：五工具各自复制 append_tl+EPOCH 缺省（guard:32/canary:63/
budgetctl:35/replay:80/egress:25）——单源化+墙钟/EPOCH 缺省退役。"""
import os, re, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'cli'))
from ledger import timeline as TL
from ledger import core

FIX = os.path.join(HERE, 'fixtures', 'G-g1')


class TestTimelineSingleSource(unittest.TestCase):
    def test_chained_row_genesis(self):
        row, prev = TL.chained_row([], '2026-09-30T12:00:00Z', 't', 'e', 'P4')
        self.assertEqual(prev, core.GENESIS)
        self.assertEqual(row[0], '2026-09-30T12:00:00Z')
        self.assertEqual(core.row_hash(prev, row[:6] + [row[7]]), row[6])

    def test_chained_row_chains(self):
        r0, p0 = TL.chained_row([], '2026-09-30T12:00:00Z', 't', 'e1', 'P4')
        r1, p1 = TL.chained_row([r0], '2026-09-30T12:00:01Z', 't', 'e2', 'P3', revert='x')
        self.assertEqual(p1, r0[6])

    def test_append_tl_locked_writes_and_ts_required(self):
        d = tempfile.mkdtemp()
        try:
            for f in os.listdir(FIX):
                shutil.copy(os.path.join(FIX, f), d)
            TL.append_tl_locked(d, '2026-09-30T12:00:00Z', '单源写入测试', '总控', 'P4')
            rows = open(os.path.join(d, 'timeline.tsv'), encoding='utf-8').read().splitlines()
            last = rows[-1].split(chr(9))
            self.assertEqual(last[2], 'P4')
            self.assertIn('单源写入测试', last[3])
            with self.assertRaises(TypeError):
                TL.append_tl_locked(d)   # ts 无缺省——EPOCH/墙钟缺省退役
        finally:
            shutil.rmtree(d)

    def test_no_local_copies_in_tools(self):
        """五工具不得再各自定义 append_tl/EPOCH（单源钉）。"""
        for tool in ('tanyin-guard', 'tanyin-canary', 'tanyin-budgetctl',
                     'tanyin-replay', 'tanyin-egress'):
            src = open(os.path.join(ROOT, 'cli', tool), encoding='utf-8').read()
            self.assertNotRegex(src, r'(?m)^def append_tl', tool + ' 仍有本地 append_tl')
            self.assertNotIn('EPOCH = ', src, tool + ' 仍有 EPOCH 缺省')


if __name__ == '__main__':
    unittest.main()