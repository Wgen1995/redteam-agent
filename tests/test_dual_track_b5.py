# -*- coding: utf-8 -*-
"""battle-5 T2（P2#1）：双轨 recall——beacon 轨 vs 行为差分轨分列。

蓝军专家律：marker 回显=「答案在响应里」的 beacon 依赖；真实世界的 ior 检出主通道
=匿名/持证对照差分。v5 双轨：GT 命中可经 beacon 轨（marker 词证）或差分轨
（finding.authz_diff 非空或 EV pair_group 控制对+键合+重放实证——无 marker 亦可）。
recall=并集；tracks 字典回填分轨计数（beacon/diff）。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from tests.eval_range_recall import score   # noqa: E402
from tests.test_keying_v4_b5 import _mk, TS   # noqa: E402


class TestDualTrack(unittest.TestCase):
    def _mk_diff(self, ep):
        """差分轨最小会话：finding.authz_diff 非空+EV 带 pair_group，卡片无 marker。"""
        from cli.ledger.core import TABLES
        rows = {t: [list(TABLES[t])] for t in ('findings.tsv', 'assets.tsv', 'E-index.tsv',
                                               'creds.tsv', 'intents.tsv', 'facts.tsv',
                                               'timeline.tsv')}

        def put(t, **kw):
            r = [''] * len(TABLES[t])
            for k, v in kw.items():
                r[TABLES[t].index(k)] = str(v)
            rows[t].append(r)

        put('assets.tsv', id='AST-0', type='endpoint', value=ep, in_scope='in_scope',
            schema_version=2, created=TS)
        put('creds.tsv', id='CRED-0', kind='static-cred', role='user',
            scope_asset='AST-0', permitted_actions='read', schema_version=2, created=TS)
        put('E-index.tsv', id='EV-00', title=ep, source_type='http', observed_at=TS,
            repro_command='curl %s' % ep, repro_kind='curl',
            content_hash_raw='x' * 64, content_hash_norm='x' * 64,
            raw_excerpt='no marker here', pair_group='PAIR-0',
            linked_finding='FD-00', schema_version=2, created=TS)
        put('findings.tsv', id='FD-00', title='diff', confidence='high', impact='high',
            status='active', exploitation_status='verified', scope_check='in_scope',
            auth_context='CRED-0', control_evidence_ids='EV-00',
            affected_asset_id='AST-0', evidence_ids='EV-00', vuln_ref='CWE-639', created=TS)
        put('timeline.tsv', timestamp=TS, actor='CLI', phase='P4',
            event='replay:EV-00:VERIFIED', hash='h')
        cards = {'EV-00': {'expected': {'matchers': [{'type': 'word', 'words': ['irrelevant']}]}}}
        return rows, cards

    def test_diff_track_hits_without_marker(self):
        rows, cards = self._mk_diff('svc-admin/admin/invoices')
        gt = [{'id': 'GT-01', 'endpoint': 'svc-admin/admin/invoices', 'marker': 'GTIDOR-02',
               'post_auth': False, 'authz_role': ''}]
        tracks = {}
        rec, missing = score(rows, cards, gt, tracks=tracks)
        self.assertEqual(rec, 1.0, '差分实证（pair+authz_diff+键合+VERIFIED）无 marker 亦命中')
        self.assertEqual(tracks.get('beacon'), 0)
        self.assertEqual(tracks.get('diff'), 1)

    def test_beacon_track_primary(self):
        rows, cards, gt = _mk(['svc-a/x'], ['svc-a/x'])   # 有 marker 词证
        tracks = {}
        rec, _m = score(rows, cards, gt, tracks=tracks)
        self.assertEqual(rec, 1.0)
        self.assertEqual(tracks.get('beacon'), 1)
        self.assertEqual(tracks.get('diff'), 0)

    def test_diff_requires_provenance(self):
        # 无 authz_diff 且无 pair_group 的无 marker 卡 → 两轨皆不收
        rows, cards = self._mk_diff('svc-admin/admin/invoices')
        from cli.ledger.core import TABLES
        fi = TABLES['findings.tsv'].index('control_evidence_ids')
        rows['findings.tsv'][1][fi] = ''
        ei = TABLES['E-index.tsv'].index('pair_group')
        rows['E-index.tsv'][1][ei] = ''
        gt = [{'id': 'GT-01', 'endpoint': 'svc-admin/admin/invoices', 'marker': 'GTIDOR-02',
               'post_auth': False, 'authz_role': ''}]
        rec, _m = score(rows, cards, gt)
        self.assertEqual(rec, 0.0, '无词证无差分源=幻觉面零分')


if __name__ == '__main__':
    unittest.main()
