# -*- coding: utf-8 -*-
"""battle-8 T3：GT v5 alt-form 孪生键 TDD——语义等价显式声明（idor-01/02/03 证据基最小集）。

battle-7 实证：idor-01/02 漏洞实已找到（种子 startswith 双形都收），战士记账 path 形
/admin/orders/1，GT 键 query 形 /admin/orders?user_id=101（query 剥离+无尾段）→键不等。
v5：GT 条目可声明 alt_forms（孪生键清单，canon 后并集匹配）；语义等价必须显式。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from cli.ledger.core import TABLES   # noqa: E402

TS = '2026-10-05T00:00:00Z'


def _mk(gt_list, finding_eps):
    rows = {t: [list(TABLES[t])] for t in ('findings.tsv', 'assets.tsv', 'E-index.tsv',
                                           'creds.tsv', 'intents.tsv', 'facts.tsv',
                                           'timeline.tsv')}

    def put(t, **kw):
        r = [''] * len(TABLES[t])
        for k, v in kw.items():
            r[TABLES[t].index(k)] = str(v)
        rows[t].append(r)

    gt = gt_list   # 直接给完整条目 dict
    cards = {}
    for j, ep in enumerate(finding_eps):
        aid, fid, evid = 'AST-%d' % j, 'FD-%02d' % j, 'EV-%02d' % j
        put('assets.tsv', id=aid, type='endpoint', value=ep,
            in_scope='in_scope', schema_version=2, created=TS)
        put('E-index.tsv', id=evid, linked_finding=fid, schema_version=2, created=TS)
        put('findings.tsv', id=fid, title='t', confidence='high', impact='high',
            status='active', exploitation_status='verified', scope_check='in_scope',
            affected_asset_id=aid, evidence_ids=evid, vuln_ref='CWE-0', created=TS)
        put('timeline.tsv', timestamp=TS, actor='CLI', phase='P4',
            event='replay:%s:VERIFIED' % evid, hash='h')
        cards[evid] = {'expected': {'matchers': [
            {'type': 'word', 'words': ['GTIDOR-01']}]}}
    return rows, cards, gt


class V5AltForm(unittest.TestCase):
    def test_path_form_hits_query_gt_via_alt_form(self):
        """G-r8 实形：GT query 形+alt_forms path 孪生；战士记 path 形 → 命中。"""
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [{'id': 'idor-01', 'endpoint': 'svc-admin/admin/orders?user_id=101',
              'marker': 'GTIDOR-01', 'post_auth': False, 'authz_role': '',
              'alt_forms': ['svc-admin/admin/orders/1']}],
            ['svc-admin/admin/orders/1'])
        rec, missing = score(rows, cards, gt)
        self.assertEqual(rec, 1.0, 'path 形经 alt_forms 命中 query 形 GT')

    def test_primary_form_still_matches(self):
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [{'id': 'idor-01', 'endpoint': 'svc-admin/admin/orders?user_id=101',
              'marker': 'GTIDOR-01', 'post_auth': False, 'authz_role': '',
              'alt_forms': ['svc-admin/admin/orders/1']}],
            ['svc-admin/admin/orders?user_id=102'])
        rec, _m = score(rows, cards, gt)
        self.assertEqual(rec, 1.0, '主形照常命中（query 剥离同键）')

    def test_no_alt_form_no_twin_hit(self):
        """无声明=不识别孪生（语义等价必须显式——铁律）。"""
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [{'id': 'idor-01', 'endpoint': 'svc-admin/admin/orders?user_id=101',
              'marker': 'GTIDOR-01', 'post_auth': False, 'authz_role': ''}],
            ['svc-admin/admin/orders/1'])
        rec, _m = score(rows, cards, gt)
        self.assertEqual(rec, 0.0, '未声明 alt_forms：path 形不命中（显式律）')

    def test_alt_form_single_count_preserved(self):
        """孪生键不破单计律：同 GT 双形 finding 只计一。"""
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [{'id': 'idor-01', 'endpoint': 'svc-admin/admin/orders?user_id=101',
              'marker': 'GTIDOR-01', 'post_auth': False, 'authz_role': '',
              'alt_forms': ['svc-admin/admin/orders/1']}],
            ['svc-admin/admin/orders/1', 'svc-admin/admin/orders?user_id=9'])
        rec, missing = score(rows, cards, gt)
        self.assertEqual(rec, 1.0, '单 GT 双形 finding 仍只计一')


if __name__ == '__main__':
    unittest.main()
