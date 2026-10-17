# -*- coding: utf-8 -*-
"""W6 控制台批——六页真页（总览/实时动态/攻击链路/发现/审批+导航壳）路由与 API 钉。

施工图=panorama/graphled-console-prototype.html（23 页满数据版，用户过目认可风格）；
真身=cli/webui/（server.py 路由 + static/console_* 页 + console 投影 API）。
文案律=docs/design/ui-copy-standard-v1.md：界面只说人话——导航名词（总览/实时动态/
攻击链路/发现/审批/设置）、战士→智能体、八问→新建任务、琥珀线→预算预警线、
P0-P6→执行阶段名（授权确认→范围检查→预算→执行→复测→报告→签发→清理→沉淀）、
三态→验证状态（已验证/待验证/已失效）；内部代号（E-index/账本/九门/投影…）不上屏。

python3 -m unittest tests.test_console_ui
法律：纯 stdlib、3.9 兼容、观察面只读投影零写入；测试动态取口（绝不 bind 8900 等）。
"""
import http.client
import json
import os
import re
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
STATIC = os.path.join(CLI, "webui", "static")
sys.path.insert(0, CLI)

from ledger import core                    # noqa: E402
from webui import server as srv_mod        # noqa: E402

T = core.TABLES
OP_KEY = "op-key-w6-console"
AP_KEY = "ap-key-w6-console"
COOKIE_RE = re.compile(r"tanyin_sess=([^;]+)")
TS = ["2026-11-01T0%d:00:00Z" % i for i in range(1, 9)]
PAGES = ("/console", "/console/live", "/console/graph",
         "/console/findings", "/console/approval")
PAGE_FILES = {"console": "console_dash.html", "console/live": "console_live.html",
              "console/graph": "console_graph.html",
              "console/findings": "console_findings.html",
              "console/approval": "console_approval.html"}
APIS = ("/api/console/overview.json", "/api/console/live.json",
        "/api/console/graph.json", "/api/console/findings.json")


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    """(ts, actor, phase, event, revert) 铸链式 timeline 行（core.row_hash 同链法）。"""
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event, revert in specs:
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        prev = h
    return rows


CVSS_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"


def build_console_goal(gd):
    """控制台夹具账本：三态发现+CVSS 向量+证据原文+usage 行+待审行+预算三笔。"""
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-c1-0001", target="shop.example",
        objective="授权渗透：控制台夹具", budget="1000;100;10",
        signer="王安全（CISO）", valid_from="2026-11-01T00:00:00Z",
        valid_until="2026-11-08T00:00:00Z", emergency_contact="138-0000-0000",
        schema_version="2", created=TS[0])])
    core.write_tsv(os.path.join(gd, "scope.tsv"), [
        row("scope.tsv", id="S-c1-0001", kind="include", matcher="shop.example",
            note="夹具白名单", created=TS[0], schema_version="2"),
        row("scope.tsv", id="S-c1-0002", kind="oob", matcher="138-0000-0000",
            note="OOB 联系人", created=TS[0], schema_version="2")])
    core.write_tsv(os.path.join(gd, "budget.tsv"), [
        row("budget.tsv", timestamp=TS[0], token_delta="100", requests_delta="10",
            hours_delta="0.5", scope="goal", note="侦察", schema_version="2"),
        row("budget.tsv", timestamp=TS[1], token_delta="200", requests_delta="20",
            hours_delta="0.2", scope="goal", note="枚举", schema_version="2"),
        row("budget.tsv", timestamp=TS[2], token_delta="300", requests_delta="30",
            hours_delta="0.1", scope="goal", note="利用", schema_version="2")])
    core.write_tsv(os.path.join(gd, "assets.tsv"), [
        row("assets.tsv", id="AST-c1-0001", type="endpoint",
            value="shop.example/api", in_scope="in_scope", created=TS[3],
            schema_version="2")])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-c1-0001",
            title="验证登录面", detail="对登录接口做受限测试", status="done",
            created=TS[3], schema_version="2")])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-c1-0001", intent_id="INT-c1-0001",
            title="登录接口无速率限制", confidence="C1", impact="中",
            exploitation_status="verified", vuln_ref="CWE-307",
            description_brief="已实证 %s（夹具向量）" % CVSS_VECTOR,
            reproducible_steps="curl -s http://shop.example/api/login",
            affected_asset_id="AST-c1-0001", evidence_ids="EV-c1-0001",
            status="active", created=TS[4], schema_version="2"),
        row("findings.tsv", id="FD-c1-0002", intent_id="INT-c1-0001",
            title="旧接口用户枚举（疑似）", confidence="C2", impact="高",
            exploitation_status="suspected", vuln_ref="CWE-204",
            description_brief="响应差异待复测", affected_asset_id="AST-c1-0001",
            evidence_ids="", status="active", created=TS[5], schema_version="2"),
        row("findings.tsv", id="FD-c1-0003", intent_id="INT-c1-0001",
            title="备份文件可读（已失效）", confidence="C3", impact="低",
            exploitation_status="ruled_out", vuln_ref="CWE-538",
            description_brief="复测未复现，判失效", affected_asset_id="AST-c1-0001",
            evidence_ids="", status="active", created=TS[6], schema_version="2")])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id="EV-c1-0001", title="登录无速率限制原始报文",
            source_type="command", observed_at=TS[4], network_position="internet",
            repro_command="curl -s -w '%{http_code}' http://shop.example/api/login",
            repro_kind="single", content_hash_raw="a" * 64, content_hash_norm="b" * 64,
            artifact_path="evidence/login.raw", card_path="evidence/EV-c1-0001.md",
            linked_finding="FD-c1-0001", raw_excerpt='HTTP/1.1 200 OK\n{"code":0}',
            created=TS[4], schema_version="2")])
    core.write_tsv(os.path.join(gd, "edges.tsv"), [
        row("edges.tsv", id="E-c1-0001", kind="parent",
            source_id="AST-c1-0001", target_id="G-c1-0001", created=TS[3],
            schema_version="2"),
        row("edges.tsv", id="E-c1-0002", kind="proves",
            source_id="EV-c1-0001", target_id="FD-c1-0001", created=TS[4],
            schema_version="2")])
    core.write_tsv(os.path.join(gd, "approvals.tsv"), [])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS[0], "总控", "P0", "add-goal G-c1-0001", ""),
        (TS[0], "总控", "P0", "add-scope S-c1-0001", ""),
        (TS[0], "总控", "P0", "gate-exit:P0 asserts=3 result=PASS", ""),
        (TS[3], "CLI", "P3", "add-asset AST-c1-0001(in_scope)", ""),
        (TS[3], "CLI", "P3", "add-intent INT-c1-0001", ""),
        (TS[4], "CLI", "P3", "add-finding FD-c1-0001", ""),
        (TS[5], "CLI", "P3", "add-finding FD-c1-0002", ""),
        (TS[6], "CLI", "P3", "add-finding FD-c1-0003", ""),
        (TS[4], "CLI", "P3", "add-evidence EV-c1-0001", ""),
        (TS[7], "总控", "P3", "usage: run=G-c1-0001-r1 tokens=450000 est_tokens=448000", ""),
        (TS[7], "replay", "P4", "replay-probe EV-c1-0001 verdict=reproduced", ""),
        (TS[7], "CLI", "P3", "request: sqlmap -u ... --level=3", "rm -f /tmp/sqlmap-marker"),
        (TS[7], "CLI", "P3", "request: ffuf -w dict.txt -u http://shop.example/FUZZ", "rm -f /tmp/ffuf.lock"),
    ]))
    return gd


class ConsoleBase(unittest.TestCase):
    """起服（动态口+临时账本）+HTTP 小助手+登录。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = os.path.join(self.td.name, "battles")
        self.goal = build_console_goal(
            os.path.join(self.battles, "battle-1", "G-c1"))
        self.srv = srv_mod.make_server(
            "127.0.0.1", 0, self.goal, battles_dir=self.battles,
            operator_key=OP_KEY, approval_key=AP_KEY)
        self.port = self.srv.server_address[1]
        th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        th.start()
        self.addCleanup(self.srv.shutdown)
        self.cookie = ""
        self.login()

    def req(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        hdrs = dict(headers or {})
        if self.cookie:
            hdrs["Cookie"] = "tanyin_sess=" + self.cookie
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=data, headers=hdrs)
        r = conn.getresponse()
        out = {"status": r.status,
               "headers": {k.lower(): v for k, v in r.getheaders()},
               "body": r.read()}
        conn.close()
        return out

    def write_req(self, path, body=None, xrw=True, origin=None):
        h = {"Origin": origin or ("http://127.0.0.1:%d" % self.port)}
        if xrw:
            h["X-Requested-With"] = "XMLHttpRequest"
        return self.req("POST", path, body=body, headers=h)

    def login(self, password=OP_KEY):
        r = self.write_req("/login", {"password": password})
        if r["status"] == 200:
            m = COOKIE_RE.search(r["headers"].get("set-cookie", ""))
            if m:
                self.cookie = m.group(1)
        return r

    def jbody(self, r):
        return json.loads(r["body"].decode("utf-8"))

    def api(self, path):
        r = self.req("GET", path)
        self.assertEqual(r["status"], 200, path + " 须 200: " + r["body"][:200].decode("utf-8", "ignore"))
        return self.jbody(r)


# ===========================================================================
# 一、路由与登录门（读面铁律：新页/新 API 一律过会话，除 /login）
# ===========================================================================

class TestConsoleRoutesAndGate(ConsoleBase):

    def test_five_pages_200_after_login(self):
        for p in PAGES:
            r = self.req("GET", p)
            self.assertEqual(r["status"], 200, p + " 登录后须 200")
            self.assertIn("text/html", r["headers"].get("content-type", ""), p)
            body = r["body"].decode("utf-8")
            self.assertIn("<!DOCTYPE html>", body, p + " 须完整 HTML 页")

    def test_pages_redirect_to_login_when_anonymous(self):
        self.cookie = ""
        for p in PAGES:
            r = self.req("GET", p)
            self.assertEqual(r["status"], 302, p + " 未登录读页须 302")
            self.assertEqual(r["headers"].get("location"), "/login",
                             p + " 须 302 到 /login")

    def test_console_apis_401_json_when_anonymous(self):
        self.cookie = ""
        for p in APIS:
            r = self.req("GET", p)
            self.assertEqual(r["status"], 401, p + " 未登录读 API 须 401")
            self.assertIn("error", self.jbody(r), p)



# ===========================================================================
# 二、总览 API（token 经济学=usage 真行 + 活动流=timeline 尾 + 门灯卡片真数）
# ===========================================================================

class TestOverviewApi(ConsoleBase):

    def test_contract_and_real_values(self):
        d = self.api('/api/console/overview.json')
        for k in ('goal', 'cards', 'token_usage', 'activity', 'battles'):
            self.assertIn(k, d, 'overview 缺键 ' + k)
        self.assertEqual(d['goal']['id'], 'G-c1-0001')
        self.assertEqual(d['goal']['target'], 'shop.example')
        self.assertEqual(d['cards']['verified_findings'], 1)
        self.assertEqual(d['cards']['findings_total'], 3)
        self.assertEqual(d['cards']['graph_nodes'], 7)  # G1+INT1+AST1+FD3+EV1
        self.assertEqual(d['cards']['evidence_cards'], 1)
        self.assertEqual(d['cards']['budget']['token']['limit'], 1000.0)
        self.assertEqual(d['cards']['budget']['token']['used'], 600.0)
        self.assertEqual(d['cards']['budget']['token']['left'], 400.0)
        tu = d['token_usage']
        self.assertEqual(tu['total_tokens'], 450000)
        self.assertEqual(tu['total_est_tokens'], 448000)
        self.assertEqual(tu['runs'][0]['run'], 'G-c1-0001-r1')
        self.assertEqual(tu['runs'][0]['tokens'], 450000)
        self.assertIn('口径', tu['note'])
        acts = d['activity']
        self.assertTrue(acts, '活动流非空')
        self.assertEqual(acts[-1]['actor'], 'CLI')
        self.assertIn('ffuf', acts[-1]['event'])
        for a in acts:
            for f in ('ts', 'actor', 'phase', 'event'):
                self.assertIn(f, a)
        self.assertEqual(d['battles'][0]['id'], 'battle-1')
        self.assertEqual(d['battles'][0]['target'], 'shop.example')

    def test_battle_param_selects_and_404(self):
        d = self.api('/api/console/overview.json?battle=1')
        self.assertEqual(d['goal']['id'], 'G-c1-0001')
        r = self.req('GET', '/api/console/overview.json?battle=99')
        self.assertEqual(r['status'], 404, '不存在的任务须 404')
        self.assertIn('error', self.jbody(r))



# ===========================================================================
# 三、实时动态 API（九阶段灯=执行阶段名 + 预算烧速真曲线 + 收敛四条件 + 事件流）
# ===========================================================================

class TestLiveApi(ConsoleBase):

    def test_phases_nine_with_standard_names(self):
        d = self.api('/api/console/live.json')
        self.assertIn('phases', d)
        ph = d['phases']
        self.assertEqual(len(ph), 9, '九个执行阶段')
        names = [p['name'] for p in ph]
        self.assertEqual(names, ['授权确认', '范围检查', '预算', '执行', '复测',
                                 '报告', '签发', '清理', '沉淀'])
        self.assertEqual([p['id'] for p in ph],
                         ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P5.5', 'P6.0', 'P6'])
        self.assertEqual(ph[0]['result'], 'PASS', 'P0 过门=真 timeline 行推导')
        self.assertEqual(ph[1]['result'], 'PENDING')
        for p in ph:
            self.assertIn(p['result'], ('PASS', 'FAIL', 'PENDING'))

    def test_budget_burn_series_real_cumulative(self):
        d = self.api('/api/console/live.json')
        b = d['budget']
        self.assertEqual(b['token']['limit'], 1000.0)
        self.assertEqual(b['token']['used'], 600.0)
        series = b['series']
        self.assertEqual([p['cum_tokens'] for p in series], [100, 300, 600],
                         '烧速=预算流水累计（错行=没接真数）')
        self.assertEqual([p['token_delta'] for p in series], [100, 200, 300],
                         '单笔增量也随行携带')
        self.assertEqual([p['cum_requests'] for p in series], [10, 30, 60])
        self.assertEqual(series[0]['ts'], TS[0])

    def test_convergence_four_conditions(self):
        d = self.api('/api/console/live.json')
        cv = d['convergence']
        self.assertEqual(cv['state'], 'converged',
                         '空矩阵+无未消费事实+无阻塞意图+预算未穿=收敛')
        cond = {c['key']: c for c in cv['conditions']}
        self.assertEqual(sorted(cond), ['blocked_intents', 'budget_exhausted',
                                        'matrix_gaps', 'unconsumed_facts'])
        self.assertEqual(cond['matrix_gaps']['count'], 0)
        self.assertFalse(cond['matrix_gaps']['ok'] is None)
        for c in cv['conditions']:
            self.assertIn('name', c, '条件须有人话名')
            self.assertIn('ok', c)

    def test_events_tail_real_rows(self):
        d = self.api('/api/console/live.json')
        evs = d['events']
        self.assertTrue(evs)
        self.assertIn('ffuf', evs[-1]['event'])
        self.assertEqual(evs[-1]['actor'], 'CLI')



# ===========================================================================
# 四、攻击链路 API（节点入场帧=timeline 行号；回放条帧数=timeline 真行数钉）
# ===========================================================================

class TestGraphApi(ConsoleBase):

    def test_frames_equal_timeline_rows(self):
        d = self.api('/api/console/graph.json')
        self.assertIn('replay', d)
        self.assertEqual(d['replay']['frames'], 13,
                         '回放条帧数=timeline 真实行数（13 行夹具）')
        self.assertEqual(d['timeline_rows'], 13)
        with open(os.path.join(self.goal, 'timeline.tsv'), encoding='utf-8') as f:
            real_rows = sum(1 for _ in f)
        self.assertEqual(d['replay']['frames'], real_rows,
                         '帧数钉与磁盘实况一致')

    def test_node_born_row_from_real_timeline(self):
        d = self.api('/api/console/graph.json')
        born = {n['id']: n.get('born_row') for n in d['nodes']}
        self.assertEqual(born.get('G-c1-0001'), 1, '目标=add-goal 行 1')
        self.assertEqual(born.get('AST-c1-0001'), 4, '资产=add-asset 行 4')
        self.assertEqual(born.get('INT-c1-0001'), 5, '意图=add-intent 行 5')
        self.assertEqual(born.get('FD-c1-0001'), 6, '发现=add-finding 行 6')
        self.assertEqual(born.get('EV-c1-0001'), 9, '证据=add-evidence 行 9')
        for n in d['nodes']:
            self.assertIn('born_row', n, '每节点都带入场帧')
            self.assertIn(n['kind'], ('G', 'INT', 'AST', 'CRED', 'F', 'FD', 'EV'))

    def test_legend_kinds_real_seven_plus_ten(self):
        d = self.api('/api/console/graph.json')
        nk = {k['kind']: k['name'] for k in d['node_kinds']}
        self.assertEqual(nk, {'G': '目标', 'INT': '意图', 'AST': '资产',
                              'CRED': '凭据', 'F': '事实', 'FD': '发现',
                              'EV': '证据'}, '节点型=真实 7 型（不虚构 11 型）')
        ek = {k['kind']: k['name'] for k in d['edge_kinds']}
        self.assertEqual(len(ek), 10, '边型=真实 10 型')
        self.assertEqual(ek.get('proves'), '证明')
        self.assertEqual(ek.get('parent'), '隶属于')
        for k in d['node_kinds'] + d['edge_kinds']:
            self.assertIn('color', k, '图例须带色标')

    def test_edges_carry_kind_and_born(self):
        d = self.api('/api/console/graph.json')
        edges = {e['id']: e for e in d['edges']}
        self.assertIn('E-c1-0002', edges)
        self.assertEqual(edges['E-c1-0002']['kind'], 'proves')
        self.assertEqual(edges['E-c1-0002']['born_row'], 9,
                         '边入场=两端都到场（EV 行 9）')



# ===========================================================================
# 五、发现 API（验证状态三态=已验证/待验证/已失效 + CVSS 实算 + 证据原文抽屉）
# ===========================================================================

class TestFindingsApi(ConsoleBase):

    def test_states_three_way_real_counts(self):
        d = self.api('/api/console/findings.json')
        self.assertEqual(d['total'], 3)
        self.assertEqual(d['states'], {'已验证': 1, '待验证': 1, '已失效': 1},
                         '验证状态三态=exploitation_status 事件溯源最新')
        st = {f['id']: f['verify_state'] for f in d['findings']}
        self.assertEqual(st, {'FD-c1-0001': '已验证',
                              'FD-c1-0002': '待验证',
                              'FD-c1-0003': '已失效'})

    def test_finding_fields_and_impact(self):
        d = self.api('/api/console/findings.json')
        f1 = [f for f in d['findings'] if f['id'] == 'FD-c1-0001'][0]
        for k in ('id', 'title', 'verify_state', 'impact', 'confidence',
                  'vuln_ref', 'asset', 'created', 'cvss', 'evidence'):
            self.assertIn(k, f1, '发现缺字段 ' + k)
        self.assertEqual(f1['impact'], '中')
        self.assertEqual(f1['vuln_ref'], 'CWE-307')
        self.assertEqual(f1['asset'], 'AST-c1-0001')

    def test_cvss_computed_from_real_vector(self):
        d = self.api('/api/console/findings.json')
        f1 = [f for f in d['findings'] if f['id'] == 'FD-c1-0001'][0]
        self.assertAlmostEqual(f1['cvss']['score'], 9.8,
                               places=1, msg='向量在场=ledger.cvss 实算')
        self.assertEqual(f1['cvss']['severity'], '严重')
        self.assertIn('CVSS:3.1/AV:N', f1['cvss']['vector'])
        f2 = [f for f in d['findings'] if f['id'] == 'FD-c1-0002'][0]
        self.assertIsNone(f2['cvss'], '无向量=未评定（不虚构分数）')

    def test_evidence_raw_request_response(self):
        d = self.api('/api/console/findings.json')
        f1 = [f for f in d['findings'] if f['id'] == 'FD-c1-0001'][0]
        ev = f1['evidence']
        self.assertEqual(ev[0]['id'], 'EV-c1-0001')
        self.assertIn('curl', ev[0]['request'],
                      '原始请求=证据卡复现命令真转抄')
        self.assertIn('HTTP/1.1 200 OK', ev[0]['response'],
                      '响应节选=证据卡原文真转抄')
        f2 = [f for f in d['findings'] if f['id'] == 'FD-c1-0002'][0]
        self.assertEqual(f2['evidence'], [], '无证据挂接=空表不虚构')



# ===========================================================================
# 六、审批真提交（过 TANYIN_APPROVAL_KEY 持钥通道）+ 四层拦截只读表
# ===========================================================================

class TestApprovalE2E(ConsoleBase):

    def test_get_pending_queue_with_sig(self):
        d = self.api('/api/approval')
        self.assertEqual(d['pending_count'], 2, '两条待审（sqlmap+ffuf）')
        self.assertTrue(d['key_configured'])
        p0 = d['pending'][0]
        for k in ('row', 'ts', 'event', 'revert_cmd', 'command_hash',
                  '_approval_sig'):
            self.assertIn(k, p0)
        self.assertIn('sqlmap', p0['event'])

    def test_approve_real_ledger_write(self):
        d = self.api('/api/approval')
        p0 = d['pending'][0]
        r = self.write_req('/api/approval', {
            'decision': 'approved', 'row': p0['row'],
            '_approval_sig': p0['_approval_sig']})
        self.assertEqual(r['status'], 200, r['body'][:200].decode('utf-8', 'ignore'))
        out = self.jbody(r)
        self.assertTrue(out['ok'])
        self.assertEqual(out['decision'], 'approved')
        with open(os.path.join(self.goal, 'approvals.tsv'), encoding='utf-8') as f:
            ap = f.read()
        self.assertIn('approved', ap, '审批决定真落表')

    def test_reject_real_ledger_write(self):
        d = self.api('/api/approval')
        p1 = [p for p in d['pending'] if 'ffuf' in p['event']][0]
        r = self.write_req('/api/approval', {
            'decision': 'rejected', 'row': p1['row'],
            '_approval_sig': p1['_approval_sig']})
        self.assertEqual(r['status'], 200)
        self.assertEqual(self.jbody(r)['decision'], 'rejected')
        with open(os.path.join(self.goal, 'approvals.tsv'), encoding='utf-8') as f:
            self.assertIn('rejected', f.read(), '拒绝决定真落表')
        d2 = self.api('/api/approval')
        got = [p for p in d2['pending'] if 'ffuf' in p['event']][0]
        self.assertEqual(got.get('decided'), 'rejected',
                         '已决项带决定标记（页面据此移出队列）')
        sqlmap = [p for p in d2['pending'] if 'sqlmap' in p['event']][0]
        self.assertNotIn('decided', sqlmap, '未决项不带决定标记')

    def test_submit_without_sig_403(self):
        r = self.write_req('/api/approval', {'decision': 'approved', 'row': 12})
        self.assertEqual(r['status'], 403, '缺持钥签名=拒')


class TestInterceptApi(ConsoleBase):

    def test_four_layers_real_projection(self):
        d = self.api('/api/console/intercept.json')
        layers = {L['level']: L for L in d['layers']}
        self.assertEqual(sorted(layers), ['L0', 'L1', 'L2', 'L3'],
                         '四层拦截=法/范围/副作用/资源')
        self.assertEqual(layers['L0']['name'], '授权窗口')
        self.assertIn('2026-11-01T00:00:00Z', layers['L0']['window'])
        self.assertTrue(layers['L0']['in_window'],
                        '按记录尾行时刻判定（禁 datetime.now）')
        self.assertEqual(layers['L1']['name'], '范围与蜜签')
        self.assertEqual(layers['L1']['scope_includes'], 1,
                         '范围层=scope include 真行数')
        self.assertEqual(layers['L2']['name'], '副作用黑名单')
        self.assertFalse(layers['L2']['acl_present'], '无 egress.acl=如实披露')
        self.assertEqual(layers['L3']['name'], '资源护栏')
        for L in d['layers']:
            self.assertIn('rule', L, '每层须有人话规则句')



# ===========================================================================
# 七、静态资产与页面结构钉（壳=侧栏+顶栏+Ctrl+K；数据全 JS fetch 真接）
# ===========================================================================

NEW_PAGES = ('console_dash.html', 'console_live.html', 'console_graph.html',
             'console_findings.html', 'console_approval.html')


def _static_src(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as f:
        return f.read()


class TestShellAssets(ConsoleBase):

    def test_console_css_js_routes_gated(self):
        r = self.req('GET', '/console.css')
        self.assertEqual(r['status'], 200)
        self.assertIn('text/css', r['headers'].get('content-type', ''))
        r = self.req('GET', '/console.js')
        self.assertEqual(r['status'], 200)
        self.assertIn('javascript', r['headers'].get('content-type', ''))
        self.cookie = ''
        for p in ('/console.css', '/console.js'):
            self.assertEqual(self.req('GET', p)['status'], 302,
                             p + ' 未登录须 302（读面铁律）')

    def test_pages_link_shell_and_api(self):
        for name, api in (('console_dash.html', '/api/console/overview.json'),
                          ('console_live.html', '/api/console/live.json'),
                          ('console_graph.html', '/api/console/graph.json'),
                          ('console_findings.html', '/api/console/findings.json')):
            src = _static_src(name)
            self.assertIn('/console.css', src, name + ' 缺壳样式')
            self.assertIn('/console.js', src, name + ' 缺壳脚本')
            self.assertIn(api, src, name + ' 缺真数据 API 接线')
        src = _static_src('console_approval.html')
        self.assertIn('/api/approval', src, '审批页须接既有审批 API')
        self.assertIn('/api/console/intercept.json', src)


class TestPageStructure(unittest.TestCase):

    def test_dash_structure(self):
        src = _static_src('console_dash.html')
        for hook in ('id="ov-cards"', 'id="token-table"',
                     'id="activity-feed"', 'id="side"', 'id="top"'):
            self.assertIn(hook, src, '总览缺 ' + hook)

    def test_live_structure(self):
        src = _static_src('console_live.html')
        for hook in ('id="phase-lamps"', 'id="budget-burn"',
                     'id="converge-box"', 'id="event-feed"'):
            self.assertIn(hook, src, '实时动态缺 ' + hook)
        self.assertIn('/api/stream', src, '事件流须接 SSE 真流')
        self.assertIn('执行阶段', src, '阶段灯区须有「执行阶段」人话标题')
        self.assertIn('预算预警线', src, '预算区须用「预算预警线」规范词')

    def test_graph_structure(self):
        src = _static_src('console_graph.html')
        for hook in ('id="graphsvg"', 'id="graph-legend"',
                     'id="replay-range"', 'id="replay-pos"'):
            self.assertIn(hook, src, '攻击链路缺 ' + hook)
        self.assertIn('演变回放', src, '回放条须自解释（回到任意历史时刻）')

    def test_findings_structure(self):
        src = _static_src('console_findings.html')
        for hook in ('id="state-seg"', 'id="findings-table"'):
            self.assertIn(hook, src, '发现缺 ' + hook)
        self.assertIn('GL.drawer', src, '发现页须挂详情抽屉')
        self.assertIn('d.id = "drawer"', _static_src('console.js'),
                      '抽屉容器由壳统一创建')
        for st in ('已验证', '待验证', '已失效'):
            self.assertIn('data-state="%s"' % st, src, '筛选缺状态 ' + st)
        self.assertIn('验证状态', src, '筛选项须名「验证状态」')

    def test_approval_structure(self):
        src = _static_src('console_approval.html')
        for hook in ('id="ap-queue"', 'id="intercept-table"',
                     'data-decision="approved"', 'data-decision="rejected"'):
            self.assertIn(hook, src, '审批缺 ' + hook)
        self.assertIn('X-Requested-With', _static_src('console.js'),
                      '写请求须带 CSRF 自定义头')


class TestNavShell(unittest.TestCase):

    def test_nav_23_items_with_standard_names(self):
        src = _static_src('console.js')
        m = re.search(r'NAV\s*=\s*\[(.*?)\];', src, re.S)
        self.assertIsNotNone(m, 'console.js 缺 NAV 常量')
        items = re.findall(r'\[\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"[^"]*"[^\]]*\]', m.group(1))
        self.assertEqual(len(items), 23, '导航=23 项（未建页占位不许假数据）')
        for name in ('总览', '新建任务', '实时动态', '攻击链路', '发现',
                     '任务详情', '审批', '证据', '基准评测', '资产覆盖',
                     '实时日志', '设置', '用户与角色'):
            self.assertIn(name, src, '导航缺规范名 ' + name)

    def test_placeholder_badge_and_selector_and_cmdk(self):
        src = _static_src('console.js')
        self.assertIn('建设中·排期W6', src, '未建页须显示建设中占位')
        self.assertIn('battle-select', src, '顶栏须有任务选择器')
        self.assertTrue('(e.metaKey || e.ctrlKey)' in src and '"k"' in src,
                        'Ctrl+K 全局搜索钩子')
        self.assertIn('cmdk', src)


class TestUiCopyStandard(unittest.TestCase):
    """ui-copy-standard-v1：界面只说人话——禁词不上屏，规范词在场。"""

    BANNED = re.compile('看战况|看战果|管战场|战士|八问|琥珀线|三态|九门|十边|'
                        '账本|验链|投影|E-index|开战|作战|战况|战果|战场|战报|战役')

    def test_no_banned_words_in_label_zone(self):
        import html.parser

        class Vis(html.parser.HTMLParser):
            SKIP = ('script', 'style', 'pre', 'code', 'textarea', 'template')

            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.chunks = []
                self.depth = 0

            def handle_starttag(self, tag, attrs):
                if tag in self.SKIP:
                    self.depth += 1

            def handle_endtag(self, tag):
                if tag in self.SKIP and self.depth:
                    self.depth -= 1

            def handle_data(self, data):
                if not self.depth:
                    self.chunks.append(data)

        for name in NEW_PAGES + ('console.js',):
            src = _static_src(name)
            if name.endswith('.js'):
                src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
                src = re.sub(r'(^|[^:])//[^\n]*', r'\1', src)
                text = src
            else:
                p = Vis()
                p.feed(src)
                p.close()
                text = '\n'.join(p.chunks)
            hit = self.BANNED.search(text)
            self.assertIsNone(hit, '%s 标签区禁词: %r' % (name, hit and hit.group(0)))

    def test_page_titles_standard_names(self):
        want = {'console_dash.html': '总览', 'console_live.html': '实时动态',
                'console_graph.html': '攻击链路', 'console_findings.html': '发现',
                'console_approval.html': '审批'}
        for name, word in want.items():
            self.assertIn('<title>GraphLed · %s</title>' % word,
                          _static_src(name), name + ' 标题须规范名')


if __name__ == '__main__':
    unittest.main()






