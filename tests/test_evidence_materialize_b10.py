# -*- coding: utf-8 -*-
"""批次 10 T2：add-evidence 工件真身回填（缝⑧收口）。

八专家评审（渗透/swe P1）：G-r4 34/34 工件哈希=sha256(空串)——简报把 touch 空
文件定为 SOP，哈希链 attest 不到任何内容。修：artifact 文件缺失或零字节时，
用 raw-excerpt 落真身再算哈希（既有非空工件不受影响）。"""
import hashlib, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, '..', 'cli', 'tanyin-ledger')
FIX = os.path.join(HERE, 'fixtures', 'G-g1')
TS = '2026-09-30T09:20:00Z'
EMPTY = hashlib.sha256(b'').hexdigest()


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], '--goal-dir', gd] + list(args[1:]),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


class TestArtifactMaterialize(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_missing_artifact_backfilled_from_excerpt(self):
        out = run(self.d, 'add-evidence', '--title=T2 回填', '--source-type=command',
                  '--observed-at=' + TS, '--network-position=intranet',
                  '--repro-command=GET /probe', '--repro-kind=single',
                  '--artifact=evidence/m1.raw', '--raw-excerpt=BODY-MARKER-77',
                  '--timestamp=' + TS).stdout
        ev = out.split()[1]
        p = os.path.join(self.d, 'evidence', 'm1.raw')
        self.assertTrue(os.path.isfile(p), '工件须落真身')
        body = open(p, encoding='utf-8').read()
        self.assertIn('BODY-MARKER-77', body)
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        self.assertNotEqual(h, EMPTY, '哈希不得再是空串指纹')
        idx = open(os.path.join(self.d, 'E-index.tsv'), encoding='utf-8').read()
        self.assertIn(h[:16], idx or '', 'E-index 须载真哈希')

    def test_prealoaded_artifact_untouched(self):
        os.makedirs(os.path.join(self.d, 'art'), exist_ok=True)
        with open(os.path.join(self.d, 'art', 'pre.txt'), 'w', encoding='utf-8') as f:
            f.write('PRE-EXISTING')
        out = run(self.d, 'add-evidence', '--title=T2 保留', '--source-type=command',
                  '--observed-at=' + TS, '--network-position=intranet',
                  '--repro-command=GET /probe', '--repro-kind=single',
                  '--artifact=art/pre.txt', '--raw-excerpt=OTHER',
                  '--timestamp=' + TS).stdout
        body = open(os.path.join(self.d, 'art', 'pre.txt'), encoding='utf-8').read()
        self.assertEqual(body, 'PRE-EXISTING', '既有非空工件不得覆写')


if __name__ == '__main__':
    unittest.main()