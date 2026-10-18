# -*- coding: utf-8 -*-
"""发现总览（R64 对齐）：原「能力并集审计修①」钉的严重度分布条/sevRank 排序/
openDetail 跳转从未在任何页面落地——该规格被 GL-DS v1 新漏洞面
（static/pages/findings.html，ef3abfb）取代：五档严重度徽章+筛选组+行内
detail_url 详情链+技法库入口。本文件旧断言已按三处置式收编：
仍存在的功能→改钉新面；已移除的规格→退休（R64: 随49b1619 IA v2移除）。
python3 -m unittest tests.test_console_findings_overview
法律：纯 stdlib、3.9 兼容、只读投影零写入；测试动态取口（绝不 bind 8900）。
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
OP_KEY = "op-key-findings-ov"
COOKIE_RE = re.compile(r"tanyin_sess=([^;]+)")
TS = ["2026-11-01T0%d:00:00Z" % i for i in range(1, 9)]
CVSS_HI = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in specs:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def build_goal(gd):
    """四档严重度+三态验证状态：高×2（一验一待）/中×1（验）/低×1（失效）
    +空 impact×1（未分级）——分布条与排序的完整输入域。"""
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-f1-0001", target="shop.example",
        objective="发现总览夹具", budget="1000;100;10",
        signer="王安全（CISO）", valid_from="2026-11-01T00:00:00Z",
        valid_until="2026-11-08T00:00:00Z", emergency_contact="138-0000-0000",
        schema_version="2", created=TS[0])])
    core.write_tsv(os.path.join(gd, "scope.tsv"), [
        row("scope.tsv", id="S-f1-0001", kind="include", matcher="shop.example",
            note="夹具白名单", created=TS[0], schema_version="2")])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-f1-0001", title="低危已失效项",
            confidence="C3", impact="低", exploitation_status="ruled_out",
            vuln_ref="CWE-538", description_brief="复测未复现",
            affected_asset_id="", evidence_ids="", status="active",
            created=TS[4], schema_version="2"),
        row("findings.tsv", id="FD-f1-0002", title="中危已验证带向量",
            confidence="C1", impact="中", exploitation_status="verified",
            vuln_ref="CWE-307", description_brief="已实证 %s" % CVSS_HI,
            affected_asset_id="", evidence_ids="", status="active",
            created=TS[5], schema_version="2"),
        row("findings.tsv", id="FD-f1-0003", title="高危待验证甲",
            confidence="C2", impact="高", exploitation_status="suspected",
            vuln_ref="CWE-204", description_brief="响应差异待复测",
            affected_asset_id="", evidence_ids="", status="active",
            created=TS[6], schema_version="2"),
        row("findings.tsv", id="FD-f1-0004", title="高危已验证乙",
            confidence="C1", impact="高", exploitation_status="verified",
            vuln_ref="CWE-89", description_brief="注入实证",
            affected_asset_id="", evidence_ids="", status="active",
            created=TS[6], schema_version="2"),
        row("findings.tsv", id="FD-f1-0005", title="未分级疑似项",
            confidence="C2", impact="", exploitation_status="suspected",
            vuln_ref="", description_brief="影响未定级",
            affected_asset_id="", evidence_ids="", status="active",
            created=TS[7], schema_version="2")])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS[0], "总控", "P0", "add-goal G-f1-0001"),
        (TS[4], "CLI", "P3", "add-finding FD-f1-0001"),
        (TS[5], "CLI", "P3", "add-finding FD-f1-0002"),
        (TS[6], "CLI", "P3", "add-finding FD-f1-0003"),
        (TS[6], "CLI", "P3", "add-finding FD-f1-0004"),
        (TS[7], "CLI", "P3", "add-finding FD-f1-0005")]))
    return gd


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = os.path.join(self.td.name, "battles")
        self.goal = build_goal(
            os.path.join(self.battles, "battle-1", "G-f1x"))
        self.srv = srv_mod.make_server(
            "127.0.0.1", 0, self.goal, battles_dir=self.battles,
            operator_key=OP_KEY, approval_key="ap-key")
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

    def login(self):
        r = self.req("POST", "/login", body={"password": OP_KEY},
                     headers={"X-Requested-With": "XMLHttpRequest",
                              "Origin": "http://127.0.0.1:%d" % self.port})
        m = COOKIE_RE.search(r["headers"].get("set-cookie", ""))
        if m:
            self.cookie = m.group(1)

    def api(self, path):
        r = self.req("GET", path)
        self.assertEqual(r["status"], 200,
                         path + " 须 200: " + r["body"][:300].decode("utf-8", "ignore"))
        return json.loads(r["body"].decode("utf-8"))


# ═══════════════════════════ ① API 层 ═══════════════════════════

class TestFindingsOverviewApi(Base):
    """R64: 随49b1619 IA v2移除 goal/severities 两键钉——旧控制台发现页深链
    （?id&goal 拼参）与分布条口径随旧规格退役，新漏洞面计数在客户端
    五档徽章+筛选组渲染（见 TestFindingsOverviewPage 新钉）。"""

    # test_payload_has_goal_for_detail_deep_link —— R64: 随49b1619 IA v2移除
    # test_severity_distribution_real_counts —— R64: 随49b1619 IA v2移除

    def test_states_counts_unchanged(self):
        d = self.api("/api/console/findings.json")
        self.assertEqual(d["states"], {"已验证": 2, "待验证": 2, "已失效": 1})
        self.assertEqual(d["total"], 5)

    def test_readonly_deterministic_two_runs(self):
        a = self.api("/api/console/findings.json")
        b = self.api("/api/console/findings.json")
        self.assertEqual(a, b, "只读投影两跑逐字节一致")


# ═══════════════════════════ ② 页面层 ═══════════════════════════

def _src():
    with open(os.path.join(STATIC, "pages", "findings.html"), encoding="utf-8") as f:
        return f.read()


def _old_console_src():
    with open(os.path.join(STATIC, "console_findings.html"), encoding="utf-8") as f:
        return f.read()


class TestFindingsOverviewPage(unittest.TestCase):
    """R64 对齐（①新现实）：新漏洞面（GL-DS v1 pages/findings.html）——
    五档严重度徽章（危急/高/中/低/未知）+状态/严重度两组筛选+行内
    detail_url 详情链+技法库入口。"""

    def test_severity_bands_and_filters(self):
        # R64: 随49b1619 IA v2移除 分布条(sev-bar/sev-legend)规格——
        # 新现实=五档徽章 sevCls + 严重度筛选组 data-s
        src = _src()
        self.assertIn("sevCls", src, "缺五档严重度映射")
        for cls in ("sev-c", "sev-h", "sev-m", "sev-l", "sev-i"):
            self.assertIn(cls, src, "缺严重度档 " + cls)
        self.assertIn('id="filters"', src, "缺筛选组容器")
        self.assertIn("data-s", src, "缺严重度筛选钮")

    def test_row_click_navigates_to_detail_page(self):
        # R64: 随49b1619 IA v2移除 openDetail/“/p/finding-detail” 钉形——
        # 新现实=行内 detail_url 详情链（详情与重放史）
        src = _src()
        self.assertIn("detail_url", src, "行须带 detail_url 详情链")
        self.assertIn("详情与重放史", src, "详情链人话文案")

    def test_severity_sort_default(self):
        # R64: 随49b1619 IA v2移除 sevRank/cvss 决胜排序规格——
        # 新现实=服务端序+客户端筛选组（无本地排序键）
        src = _src()
        self.assertIn("ITEMS.filter", src, "筛选在客户端数据面生效")

    def test_evidence_quick_view_drawer_kept(self):
        src = _old_console_src()
        self.assertIn("GL.drawer", src, "既有钉：快览抽屉须保留")

    def test_knowledge_entry_front(self):
        src = _src()
        self.assertIn("/p/techniques", src, "知识库（技法库）入口须前置在发现页")
        # R64: 随49b1619 IA v2移除 q= 深链搜索参数（技法库面换 id 直达）


if __name__ == "__main__":
    unittest.main()
