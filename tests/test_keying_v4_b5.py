# -*- coding: utf-8 -*-
"""battle-5 T1（P2#6）：scorer 键形 v4——尾段数字归一+同键多 GT 单计。

dict §四勘误 v4：①路径尾段纯数字归一 {n}（idor 资源 id 探测同值差不再卡分）
②同键多 GT 条目一枚 finding 至多计一（检出膨胀封口）。KEYING_VERSION=4。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import _canon_endpoint, KEYING_VERSION   # noqa: E402
from cli.ledger.core import TABLES   # noqa: E402

TS = '2026-10-02T00:00:00Z'


class TestCanonV4(unittest.TestCase):
    def test_keying_version_bumped(self):
        self.assertEqual(KEYING_VERSION, 5)   # battle-8：v4→v4.1→v5（alt-form 孪生键）

    def test_digit_tail_normalized(self):
        self.assertEqual(_canon_endpoint('svc-admin/admin/users/102', {}),
                         _canon_endpoint('svc-admin/admin/users/1', {}))
        self.assertIn('{n}', _canon_endpoint('svc-admin/admin/users/102', {}))

    def test_non_digit_tail_untouched(self):
        self.assertNotIn('{n}', _canon_endpoint('svc-files/.env', {}))
        self.assertNotEqual(_canon_endpoint('svc-a/orders', {}),
                            _canon_endpoint('svc-a/orders/1', {}))

    def test_query_stripped_no_false_tail(self):
        self.assertEqual(_canon_endpoint('svc-shop/product?id=1', {}),
                         _canon_endpoint('svc-shop/product?id=2', {}))
        self.assertNotIn('{n}', _canon_endpoint('svc-shop/product?id=1', {}))


def _mk(endpoints_gt, finding_eps):
    """用 core.TABLES 真表头铸最小合成会话：每 finding 一条+VERIFIED 重放行。
    EV raw_excerpt 含全部 marker（word-matcher 面）；timeline 含 replay:<EV>:VERIFIED。"""
    rows = {t: [list(TABLES[t])] for t in ('findings.tsv', 'assets.tsv', 'E-index.tsv',
                                           'creds.tsv', 'intents.tsv', 'facts.tsv',
                                           'timeline.tsv')}

    def put(t, **kw):
        r = [''] * len(TABLES[t])
        for k, v in kw.items():
            r[TABLES[t].index(k)] = str(v)
        rows[t].append(r)

    gt = [{'id': 'GT-%02d' % (i + 1), 'endpoint': ep, 'marker': 'MK%02d' % (i + 1),
           'post_auth': False, 'authz_role': ''} for i, ep in enumerate(endpoints_gt)]
    all_mk = ' '.join(g['marker'] for g in gt)
    for j, ep in enumerate(finding_eps):
        aid, evid, fid = 'AST-%d' % j, 'EV-%02d' % j, 'FD-%02d' % j
        put('assets.tsv', id=aid, type='endpoint', value=ep, in_scope='in_scope',
            schema_version=2, created=TS)
        put('E-index.tsv', id=evid, title=ep, source_type='http',
            observed_at=TS, repro_command='curl %s' % ep, repro_kind='curl',
            content_hash_raw='x' * 64, content_hash_norm='x' * 64,
            raw_excerpt=all_mk,
            linked_finding=fid, schema_version=2, created=TS)
        put('findings.tsv', id=fid, title='t', confidence='high', impact='high',
            status='active', exploitation_status='verified', scope_check='in_scope',
            affected_asset_id=aid, evidence_ids=evid, vuln_ref='CWE-0', created=TS)
        put('timeline.tsv', timestamp=TS, actor='CLI', phase='P4',
            event='replay:%s:VERIFIED' % evid, hash='h')
    cards = {}
    for j in range(len(finding_eps)):
        evid = 'EV-%02d' % j
        cards[evid] = {'expected': {'matchers': [
            {'type': 'word', 'words': [g['marker'] for g in gt]}]}}
    return rows, cards, gt


class TestSameKeySingleCount(unittest.TestCase):
    def test_one_finding_one_gt(self):
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(['svc-a/x', 'svc-a/x'], ['svc-a/x'])
        rec, missing = score(rows, cards, gt)
        self.assertEqual(rec, 0.5, '同键双 GT 单 finding 只计一')
        self.assertEqual(len(missing), 1)

    def test_two_findings_two_gts(self):
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(['svc-a/x', 'svc-a/x'], ['svc-a/x', 'svc-a/x'])
        rec, _m = score(rows, cards, gt)
        self.assertEqual(rec, 1.0, '两 finding 双 GT 各计一')

    def test_digit_tail_hit_via_v4(self):
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(['svc-admin/admin/users/102'], ['svc-admin/admin/users/1'])
        rec, _m = score(rows, cards, gt)
        self.assertEqual(rec, 1.0, '尾段数字归一后命中')


if __name__ == '__main__':
    unittest.main()
