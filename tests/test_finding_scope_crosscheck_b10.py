# -*- coding: utf-8 -*-
"""批次 10 T1b：add-finding scope_check↔assets.in_scope 联查（缝⑩后半）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, '..', 'cli', 'tanyin-ledger')
FIX = os.path.join(HERE, 'fixtures', 'G-g1')
TS = '2026-09-30T09:10:00Z'


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], '--goal-dir', gd] + list(args[1:]),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


class TestFindingScopeCrosscheck(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_out_of_scope_asset_rejects_in_scope_claim(self):
        ast = run(self.d, 'add-asset', '--type=service', '--value=svc-billing',
                  '--meta=b10', '--timestamp=' + TS).stdout.split()[1]
        ev = run(self.d, 'add-evidence', '--title=b10 夹具证据', '--source-type=command',
                 '--observed-at=' + TS, '--network-position=intranet',
                 '--repro-command=GET /x', '--repro-kind=single',
                 '--artifact=evidence/x.raw', '--raw-excerpt=probe',
                 '--timestamp=' + TS).stdout.split()[1]
        r = run(self.d, 'add-finding', '--intent-id=INT-g1-0002',
                '--title=越界自书', '--confidence=C2', '--impact=中',
                '--exploitation-status=suspected', '--scope-check=in_scope',
                '--description-brief=联查负向', '--reproducible-steps=GET /x',
                '--affected-asset-id=' + ast, '--evidence-ids=' + ev,
                '--timestamp=' + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn('联查', r.stdout + r.stderr)

    def test_boundary_verified_channel_still_open(self):
        ast = run(self.d, 'add-asset', '--type=service', '--value=svc-billing',
                  '--meta=b10', '--timestamp=' + TS).stdout.split()[1]
        ev = run(self.d, 'add-evidence', '--title=b10 夹具证据', '--source-type=command',
                 '--observed-at=' + TS, '--network-position=intranet',
                 '--repro-command=GET /x', '--repro-kind=single',
                 '--artifact=evidence/x.raw', '--raw-excerpt=probe',
                 '--timestamp=' + TS).stdout.split()[1]
        r = run(self.d, 'add-finding', '--intent-id=INT-g1-0002',
                '--title=边界人工核验通道', '--confidence=C3', '--impact=低',
                '--exploitation-status=suspected', '--scope-check=boundary-verified',
                '--description-brief=联查放行面', '--reproducible-steps=GET /x',
                '--affected-asset-id=' + ast, '--evidence-ids=' + ev,
                '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()