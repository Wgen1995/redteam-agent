# -*- coding: utf-8 -*-
"""battle-6 收战：scorer v4.1 两遍法 TDD——词证先耗用、差分补余（总分不变、归因归真）。

G-r7 实证：GT 序 weakpass-01(先) ratelimit-01(后) 同键 svc-login/login；单 finding
带控制对（差分可计）且卡含 GTRATE-01（词证可计）。一遍法按 GT 序：weakpass 差分
先耗用→ratelimit 词证落空=证据强度倒挂。v4.1：第一遍全 GT 只走词证，第二遍
余 GT 走差分——词证永远优先于差分。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from cli.ledger.core import TABLES   # noqa: E402

TS = '2026-10-03T00:00:00Z'


def _mk(gt_list, finding_specs):
    """gt_list=[(id,marker)]；finding_specs=[{ev:词表, ctrl:[EV], ep}]——真表头合成。"""
    rows = {t: [list(TABLES[t])] for t in ('findings.tsv', 'assets.tsv', 'E-index.tsv',
                                           'creds.tsv', 'intents.tsv', 'facts.tsv',
                                           'timeline.tsv')}

    def put(t, **kw):
        r = [''] * len(TABLES[t])
        for k, v in kw.items():
            r[TABLES[t].index(k)] = str(v)
        rows[t].append(r)

    gt = [{'id': gid, 'endpoint': 'svc-login/login', 'marker': mk,
           'post_auth': False, 'authz_role': ''} for gid, mk in gt_list]
    cards = {}
    for j, spec in enumerate(finding_specs):
        aid, fid, evid, ctrle = 'AST-%d' % j, 'FD-%02d' % j, 'EV-%02d' % j, spec.get('ctrl', [])
        put('assets.tsv', id=aid, type='endpoint', value=spec.get('ep', 'svc-login/login'),
            in_scope='in_scope', schema_version=2, created=TS)
        put('E-index.tsv', id=evid, linked_finding=fid, schema_version=2, created=TS)
        for c in ctrle:
            put('E-index.tsv', id=c, linked_finding=fid, pair_group='PG-%d' % j,
                schema_version=2, created=TS)
        put('findings.tsv', id=fid, title='t', confidence='high', impact='high',
            status='active', exploitation_status='verified', scope_check='in_scope',
            affected_asset_id=aid, evidence_ids=evid + (' ' + ' '.join(ctrle) if ctrle else ''),
            control_evidence_ids=' '.join(ctrle), vuln_ref='CWE-0', created=TS)
        put('timeline.tsv', timestamp=TS, actor='CLI', phase='P4',
            event='replay:%s:VERIFIED' % evid, hash='h')
        cards[evid] = {'expected': {'matchers': [
            {'type': 'word', 'words': spec.get('words', [])}]}}
    return rows, cards, gt


class V41BeaconFirst(unittest.TestCase):
    def test_beacon_preferred_over_earlier_gt_diff(self):
        """G-r7 实形：weakpass(先,无词证) vs ratelimit(后,词证在卡)。v4.1 归 ratelimit。"""
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [('weakpass-01', 'GTWEAKPASS-01'), ('ratelimit-01', 'GTRATE-01')],
            [{'words': ['denied', 'GTRATE-01'], 'ctrl': ['EV-C0']}])
        t = {}
        rec, missing = score(rows, cards, gt, tracks=t)
        self.assertEqual(rec, 0.5)
        self.assertEqual(t['beacon'], 1)
        self.assertEqual(t['diff'], 0, '词证在卡：差分让位')
        self.assertIn('weakpass-01', missing)
        self.assertNotIn('ratelimit-01', missing)

    def test_diff_still_counts_without_beacon(self):
        from tests.eval_range_recall import score
        rows, cards, gt = _mk(
            [('weakpass-01', 'GTWEAKPASS-01')],
            [{'words': ['denied'], 'ctrl': ['EV-C0']}])
        t = {}
        rec, missing = score(rows, cards, gt, tracks=t)
        self.assertEqual(rec, 1.0)
        self.assertEqual(t['diff'], 1)


if __name__ == '__main__':
    unittest.main()
