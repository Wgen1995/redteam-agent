# -*- coding: utf-8 -*-
"""批次 10 T6（P2#10）：契约链悬空引用收口。

八专家架构 P2：shared/LEDGER.md 名存实亡（12 处悬空引用）。修=实体化指针页，
升格 02a 为正式稿留人工终审（人工项）。"""
import glob, os, re, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


class TestContractChain(unittest.TestCase):
    def test_shared_ledger_materialized(self):
        p = os.path.join(ROOT, 'shared', 'LEDGER.md')
        self.assertTrue(os.path.isfile(p), 'shared/LEDGER.md 须实体化（12 处引用）')
        body = open(p, encoding='utf-8').read()
        self.assertIn('02a-command-signatures-draft.md', body, '须指明附录 A 底稿位置')
        self.assertIn('registry', body, '须指明 KNOWN_COMMANDS 派生单源')

    def test_no_dangling_shared_ledger_refs(self):
        hits = []
        for f in glob.glob(os.path.join(ROOT, 'contracts', '*.md')):
            if 'shared/LEDGER.md' in open(f, encoding='utf-8').read():
                hits.append(f)
        self.assertTrue(hits, '契约引用面存在（前提自检）')
        self.assertTrue(os.path.isfile(os.path.join(ROOT, 'shared', 'LEDGER.md')),
                        '所有 shared/LEDGER.md 引用须可解析')


if __name__ == '__main__':
    unittest.main()