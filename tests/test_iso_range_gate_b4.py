# -*- coding: utf-8 -*-
"""批次 battle-4 T9（缝⑬）：ISO8601 范围校验——形状检查不够。

战创：G-r5 战士早期时间戳 2026-10-01T09:155:00Z（分钟=155）被 CLI rc=0 收账
（G-g1 复测确认）；字典序在该形下破坏时间序（09:100<09:59）。修=timestamp
单一咽喉点（_parse/_req 后统一校验）严格范围：月 1-12/日 1-31/时 0-23/分秒 0-59。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, '..', 'cli', 'tanyin-ledger')
FIX = os.path.join(HERE, 'fixtures', 'G-g1')
TS_OK = '2026-10-01T10:00:00Z'


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], '--goal-dir', gd] + list(args[1:]),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


class TestIsoRangeGate(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_minute_155_rejected(self):
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-ts1', '--meta=x',
                '--timestamp=2026-10-01T09:155:00Z')
        self.assertEqual(r.returncode, 1)
        self.assertIn('ISO8601', r.stdout + r.stderr)

    def test_hour_25_rejected(self):
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-ts2', '--meta=x',
                '--timestamp=2026-10-01T25:00:00Z')
        self.assertEqual(r.returncode, 1)

    def test_valid_still_passes(self):
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-ts3', '--meta=x',
                '--timestamp=' + TS_OK)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
