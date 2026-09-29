# -*- coding: utf-8 -*-
"""批次 10 T8（P2#14）：飞轮归因抽样核验步——retro 页 lint 契约。

八专家渗透 P2+RT-0001 writeback②：战记 honest_misses 自述归因未核即入册
（PR-0005 带错喂养实锤）。修=kind=retro 且 missed 非空时，front-matter 必带
attribution_check ∈ {verified,sampled,pending-human}（pending-human=人工复核项）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
KN = os.path.join(ROOT, 'cli', 'tanyin-knowledge')


def kn(kdir, *args):
    return subprocess.run([sys.executable, KN, args[0], '--knowledge-dir', kdir,
                           '--timestamp=2026-09-30T12:00:00Z'] + list(args[1:]),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


BASE_FM_HEAD = ('---\nid: RT-9001\nkind: retro\nclient: CLIENT-03\n'
                 'window: 2026-09-30..2026-09-30\nmissed: ')
BASE_FM_TAIL = ('\ntrigger_gap: x\nweak_channel: x\nwriteback: x\n'
                 'vocab_version: WSTG-v4.2\nstatus: learned\nlast_verified: 2026-09-30\n---\n\n## 摘要\nt\n')


class TestRetroAttributionGate(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        r = kn(self.d, 'init')
        assert r.returncode == 0, r.stdout + r.stderr   # format_version=kn-v1 铸造
        os.makedirs(os.path.join(self.d, 'retros'), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _page(self, missed, extra=''):
        p = os.path.join(self.d, 'retros', 'RT-9001.md')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(BASE_FM_HEAD + missed + (('\n' + extra) if extra else '') + BASE_FM_TAIL)
        return p

    def test_missed_nonempty_requires_attribution_check(self):
        self._page('某靶漏检')
        r = kn(self.d, 'lint')
        self.assertNotEqual(r.returncode, 0, 'missed 非空而缺 attribution_check 须红')
        self.assertIn('attribution_check', r.stdout + r.stderr)

    def test_attribution_check_enum_enforced(self):
        self._page('某靶漏检', 'attribution_check: 瞎写\n')
        r = kn(self.d, 'lint')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('verified/sampled/pending-human', r.stdout + r.stderr)

    def test_verified_attribution_passes_gate(self):
        # schema 本就必填 missed——正当路径=missed 非空+attribution_check 合法值
        self._page('某靶漏检（种子复核：tests/range/seed/svc-login/app.py do_GET）',
                   'attribution_check: sampled\n')
        r = kn(self.d, 'lint')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()