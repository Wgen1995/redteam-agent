# -*- coding: utf-8 -*-
"""批次 10 T1（缝⑩收口）：scope 执法面与键形 v3 对齐。

八专家评审 arch P1：G-r4 全部 41 目标资产被误判 out_of_scope——根因双层：
①add-scope 校验器强制点分域名/CIDR，单标签服务名（svc-shop 形）被拒；
②add-asset 匹配只对全值（endpoint 值带路径）做后缀匹配，主机段永不触达。
修：校验器收单标签名；匹配=全值或主机段双试。
负向：未声明服务名仍 out_of_scope（禁猜测式放大）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, '..', 'cli', 'tanyin-ledger')
FIX = os.path.join(HERE, 'fixtures', 'G-g1')
TS = '2026-09-30T09:00:00Z'


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], '--goal-dir', gd] + list(args[1:]),
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


class TestScopeBareHostname(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _tl(self):
        return open(os.path.join(self.d, 'timeline.tsv'), encoding='utf-8').read()

    def test_bare_hostname_include_accepted(self):
        r = run(self.d, 'add-scope', '--kind=include', '--matcher=svc-shop',
                '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_service_asset_in_scope_by_bare_name(self):
        run(self.d, 'add-scope', '--kind=include', '--matcher=svc-shop',
            '--timestamp=' + TS)
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-shop',
                '--meta=b10', '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('(in_scope)', self._tl())

    def test_endpoint_asset_in_scope_via_host_part(self):
        run(self.d, 'add-scope', '--kind=include', '--matcher=svc-shop',
            '--timestamp=' + TS)
        r = run(self.d, 'add-asset', '--type=endpoint',
                '--value=svc-shop/item?id=1', '--meta=b10', '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('(in_scope)', self._tl())

    def test_undeclared_service_stays_out(self):
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-billing',
                '--meta=b10', '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('(out_of_scope)', self._tl())

    def test_exclude_still_wins_for_bare_name(self):
        run(self.d, 'add-scope', '--kind=include', '--matcher=svc-shop',
            '--timestamp=' + TS)
        run(self.d, 'add-scope', '--kind=exclude', '--matcher=svc-shop',
            '--timestamp=' + TS)
        r = run(self.d, 'add-asset', '--type=service', '--value=svc-shop',
                '--meta=b10', '--timestamp=' + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('(out_of_scope)', self._tl())


if __name__ == '__main__':
    unittest.main()