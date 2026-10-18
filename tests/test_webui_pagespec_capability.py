# -*- coding: utf-8 -*-
"""演进飞轮②能力曲线钉测（api_v2_capability·/api/v2/capability.json）。

python3 -m unittest tests.test_webui_pagespec_capability
律：只读投影零写入、纯 stdlib、3.9 兼容、输出确定性（禁 datetime.now）、
动态口真服禁碰 8900（127.0.0.1:0）。

三层钉：
  ①投影层  capability_view——每仗评测聚合投影（仗序号×召回/误报/每美元
           发现/覆盖率，时间序=仗编号升序）；数据单源=battle 家目录
           （settle-report.txt 召回行+G-* 会话账本表 timeline/budget/matrix/
           findings——metrics.py 同源勘定，跨舰零 import 自洽）；曲线下降段=
           告警旗（召回/覆盖/每美元回落+误报率上升，相邻对逐段旗）。
  ②挂载层  ROUTES 单源表+dispatch 同形（api_v2_techniques 舰间契约同款）；
           会话门 401+登录后 200 真服过 HTTP。
  ③知识位  knowledge 存量块（技法卡/避坑卡计数——飞轮知识 stock 可视锚）。
"""
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
REPO = os.path.join(HERE, "..")
sys.path.insert(0, CLI)

from webui import api_v2_capability as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402  测试侧表头单源

from tests import webui_login  # noqa: E402


def _tsv(path, table, rows):
    cols = TABLES[table]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")


def make_battle(battles_dir, n, *, recall_line=None, missing=0, dollars=0.0,
                active=1, fp_events=(), matrix=(), directive=None,
                settled=True):
    """曲线夹具战：settle 报告（召回行）+会话四表+directive 臂标。"""
    gen = "G-c%d" % n
    home = os.path.join(battles_dir, "battle-%d" % n)
    sess = os.path.join(home, gen)
    os.makedirs(sess, exist_ok=True)
    if settled:
        hit, tot = recall_line
        rep = ("verify-chain: PASS\n\nrecall=%.2f (%d/%d)\n"
               "track_beacon=%d track_diff=0\n"
               % (hit / tot if tot else 0.0, hit, tot, hit))
        rep += "".join("MISSING\tGT-%02d\n" % (i + 1) for i in range(missing))
        with open(os.path.join(home, "settle-report.txt"), "w",
                  encoding="utf-8") as f:
            f.write(rep)
    frows = []
    for i in range(active):
        frows.append({"id": "FD-c%04d" % (i + 1), "intent_id": "INT-1",
                      "title": "发现%d" % (i + 1), "confidence": "C1",
                      "impact": "中", "exploitation_status": "verified",
                      "vuln_ref": "CWE-79", "scope_check": "in_scope",
                      "description_brief": "b", "reproducible_steps": "s",
                      "affected_asset_id": "AST-1",
                      "evidence_ids": "EV-c%d-%d" % (n, i + 1),
                      "status": "active",
                      "schema_version": 1, "created": "2026-10-19T00:00:00Z"})
    _tsv(os.path.join(sess, "findings.tsv"), "findings.tsv", frows)
    tl = [{"timestamp": "2026-10-19T00:00:00Z", "actor": "w", "phase": "P4",
           "event": "replay:EV-c%d-1:VERIFIED" % n, "prev_hash": "GENESIS",
           "hash": "h1", "schema_version": 1}]
    for ev_text in fp_events:
        tl.append({"timestamp": "2026-10-19T00:01:00Z", "actor": "w",
                   "phase": "P4", "event": ev_text, "prev_hash": "h1",
                   "hash": "h2", "schema_version": 1})
    _tsv(os.path.join(sess, "timeline.tsv"), "timeline.tsv", tl)
    _tsv(os.path.join(sess, "budget.tsv"), "budget.tsv",
         [{"timestamp": "2026-10-19T00:00:00Z", "token_delta": 1000,
           "requests_delta": 10, "hours_delta": 0, "dollars_delta": dollars,
           "scope": "goal", "note": "夹具", "schema_version": 2}])
    _tsv(os.path.join(sess, "matrix.tsv"), "matrix.tsv",
         [{"attack_surface": s, "vuln_class": v, "state": st, "reason": "",
           "intent_id": "", "schema_version": 1,
           "updated": "2026-10-19T00:00:00Z"} for s, v, st in matrix])
    if directive is not None:
        with open(os.path.join(home, "directive.txt"), "w", encoding="utf-8") as f:
            f.write(directive)
    return home


class TestCapabilityView(unittest.TestCase):

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.bdir = os.path.join(self.td.name, "battles")
        os.makedirs(self.bdir)

    def tearDown(self):
        self.td.cleanup()

    def test_series_shape_and_time_order(self):
        make_battle(self.bdir, 2, recall_line=(1, 2), dollars=2.0,
                    matrix=[("a", "xss", "x")], directive="")
        make_battle(self.bdir, 10, recall_line=(2, 2), dollars=4.0,
                    matrix=[("a", "xss", "x")], directive="d")
        v = api.capability_view(battles_dir=self.bdir)
        self.assertEqual([b["n"] for b in v["series"]], [2, 10])  # 数字序
        b0 = v["series"][0]
        for k in ("n", "id", "arm", "recall", "hits", "total", "missing_n",
                  "fp", "active", "fp_rate", "dollars", "per_dollar",
                  "coverage"):
            self.assertIn(k, b0)
        self.assertEqual(b0["id"], "battle-2")
        self.assertEqual(b0["arm"], "对照")
        self.assertEqual(v["series"][1]["arm"], "处置")

    def test_recall_and_missing_from_settle_report(self):
        make_battle(self.bdir, 1, recall_line=(1, 2), missing=1)
        v = api.capability_view(battles_dir=self.bdir)
        self.assertEqual(v["series"][0]["recall"], 0.5)
        self.assertEqual(v["series"][0]["hits"], 1)
        self.assertEqual(v["series"][0]["total"], 2)
        self.assertEqual(v["series"][0]["missing_n"], 1)

    def test_false_positive_rate_from_timeline(self):
        make_battle(self.bdir, 1, recall_line=(1, 1), active=2,
                    fp_events=("replay-probe EV-c1-1 verdict=not-reproduced",))
        v = api.capability_view(battles_dir=self.bdir)
        b = v["series"][0]
        self.assertEqual(b["active"], 2)
        self.assertEqual(b["fp"], 1)
        self.assertEqual(b["fp_rate"], 0.5)

    def test_per_dollar_honest(self):
        make_battle(self.bdir, 1, recall_line=(2, 2), dollars=0.0)
        make_battle(self.bdir, 2, recall_line=(2, 2), dollars=4.0)
        v = api.capability_view(battles_dir=self.bdir)
        self.assertIsNone(v["series"][0]["per_dollar"])   # 零美元=未计量不虚造
        self.assertEqual(v["series"][1]["per_dollar"], 0.5)

    def test_coverage_fraction_latest_wins(self):
        make_battle(self.bdir, 1, recall_line=(1, 1),
                    matrix=[("a", "xss", "x"), ("a", "xss", "-"),
                            ("b", "sqli", "x"), ("c", "ssrf", "?")])
        v = api.capability_view(battles_dir=self.bdir)
        self.assertAlmostEqual(v["series"][0]["coverage"], 1 / 3, places=4)
        make_battle(self.bdir, 2, recall_line=(1, 1), matrix=[])
        v2 = api.capability_view(battles_dir=self.bdir)
        self.assertIsNone(v2["series"][1]["coverage"])       # 无矩阵=未测面

    def test_decline_warnings(self):
        make_battle(self.bdir, 1, recall_line=(2, 2), dollars=2.0,
                    matrix=[("a", "xss", "x")])
        make_battle(self.bdir, 2, recall_line=(1, 2), dollars=4.0,
                    matrix=[("a", "xss", "?")])
        v = api.capability_view(battles_dir=self.bdir)
        metrics = {w["metric"] for w in v["warnings"]}
        self.assertIn("recall", metrics)
        self.assertIn("coverage", metrics)
        rec = [w for w in v["warnings"] if w["metric"] == "recall"][0]
        self.assertEqual(rec["from_n"], 1)
        self.assertEqual(rec["to_n"], 2)
        self.assertEqual(rec["from_v"], 1.0)
        self.assertEqual(rec["to_v"], 0.5)
        self.assertIn("召回", rec["metric_zh"])                 # 宪法#41 人话

    def test_fp_rise_flagged(self):
        make_battle(self.bdir, 1, recall_line=(1, 1), active=2,
                    matrix=[("a", "xss", "x")])
        make_battle(self.bdir, 2, recall_line=(1, 1), active=2,
                    fp_events=("replay-probe EV-c2-1 verdict=not-reproduced",),
                    matrix=[("a", "xss", "x")])
        v = api.capability_view(battles_dir=self.bdir)
        fpw = [w for w in v["warnings"] if w["metric"] == "fp_rate"]
        self.assertEqual(len(fpw), 1)
        self.assertIn("误报", fpw[0]["metric_zh"])

    def test_no_warnings_when_improving_or_flat(self):
        make_battle(self.bdir, 1, recall_line=(1, 2), dollars=4.0,
                    matrix=[("a", "xss", "?")])
        make_battle(self.bdir, 2, recall_line=(2, 2), dollars=2.0,
                    matrix=[("a", "xss", "x")])
        v = api.capability_view(battles_dir=self.bdir)
        self.assertEqual(v["warnings"], [])

    def test_unsettled_battle_excluded_but_counted(self):
        make_battle(self.bdir, 1, recall_line=(1, 1))
        make_battle(self.bdir, 2, settled=False)     # 未结算：不入曲线只入计数
        v = api.capability_view(battles_dir=self.bdir)
        self.assertEqual([b["n"] for b in v["series"]], [1])
        self.assertEqual(v["counts"]["battles_seen"], 2)
        self.assertEqual(v["counts"]["battles_settled"], 1)

    def test_determinism_and_zero_writes(self):
        make_battle(self.bdir, 1, recall_line=(2, 2), dollars=2.0,
                    matrix=[("a", "xss", "x")])
        make_battle(self.bdir, 2, recall_line=(1, 2), dollars=2.0,
                    matrix=[("a", "xss", "?")])
        before = {}
        for root, _dirs, files in os.walk(self.td.name):
            for fn in files:
                p = os.path.join(root, fn)
                with open(p, "rb") as f:
                    before[p] = f.read()
        a = api.capability_view(battles_dir=self.bdir)
        b = api.capability_view(battles_dir=self.bdir)
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))
        after = {}
        for root, _dirs, files in os.walk(self.td.name):
            for fn in files:
                p = os.path.join(root, fn)
                with open(p, "rb") as f:
                    after[p] = f.read()
        self.assertEqual(before, after)

    def test_knowledge_stock_real_repo(self):
        v = api.capability_view(battles_dir=self.bdir,
                                knowledge_dir=os.path.join(REPO, "knowledge"))
        self.assertEqual(v["knowledge"]["technique_cards"], 50)
        self.assertEqual(v["knowledge"]["negative_cards"], 0)  # 蒸馏未开工如实 0

    def test_headerless_real_battle_shape(self):
        # 真实 battle 会话=无表头冻结列序（schemas.py TABLES 单源；裸写钉）+
        # .bak 备份族在场主代优先
        home = os.path.join(self.bdir, "battle-7")
        for g in ("G-real.bak-preReplay", "G-real"):
            os.makedirs(os.path.join(home, g))
        sess = os.path.join(home, "G-real")
        with open(os.path.join(sess, "findings.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("FD-1\tINT-1\tt\tC1\t中\tverified\t\t\tCWE-79\tin_scope"
                    "\tb\ts\tAST-1\tEV-a\t\t\tactive\t1"
                    "\t2026-10-19T00:00:00Z\n")
        with open(os.path.join(sess, "timeline.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("ts\tw\tP4\treplay-probe EV-a verdict=not-reproduced\t"
                    "\t\t\t1\n")
        with open(os.path.join(sess, "budget.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("ts\t100\t10\t0\t2.5\tgoal\tn\t2\n")
        with open(os.path.join(sess, "matrix.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("a\txss\tx\t\t\t1\tts\t\n")
            f.write("b\tsqli\t?\t\t\t1\tts\t\n")
        with open(os.path.join(home, "settle-report.txt"), "w",
                  encoding="utf-8") as f:
            f.write("verify-chain: PASS\n\nrecall=0.50 (1/2)\nMISSING\tGT-2\n")
        v = api.capability_view(battles_dir=self.bdir)
        b = v["series"][0]
        self.assertEqual(b["n"], 7)
        self.assertEqual((b["fp"], b["active"]), (1, 1))
        self.assertEqual(b["fp_rate"], 1.0)
        self.assertEqual(b["dollars"], 2.5)
        self.assertEqual(b["per_dollar"], 0.4)
        self.assertEqual(b["coverage"], 0.5)

    def test_frozen_column_indices_match_tables(self):
        # 列位漂移钉：冻结列位须与 schemas.py TABLES 逐位一致（schema bump=红）
        self.assertEqual(TABLES["findings.tsv"].index("id"), api._FI_ID)
        self.assertEqual(TABLES["findings.tsv"].index("status"), api._FI_STATUS)
        self.assertEqual(TABLES["timeline.tsv"].index("event"), api._TI_EVENT)
        self.assertEqual(TABLES["budget.tsv"].index("dollars_delta"), api._BI_DOLLARS)
        self.assertEqual(TABLES["matrix.tsv"].index("attack_surface"), api._MI_SURF)
        self.assertEqual(TABLES["matrix.tsv"].index("vuln_class"), api._MI_VULN)
        self.assertEqual(TABLES["matrix.tsv"].index("state"), api._MI_STATE)

    def test_default_battles_dir_tanyin_home(self):
        os.environ["TANYIN_HOME"] = self.td.name
        try:
            self.assertEqual(api.default_battles_dir(),
                             os.path.join(self.td.name, "battles"))
        finally:
            os.environ.pop("TANYIN_HOME", None)


class TestRouteContract(unittest.TestCase):

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.bdir = os.path.join(self.td.name, "battles")
        os.makedirs(self.bdir)
        make_battle(self.bdir, 1, recall_line=(1, 1), dollars=2.0)

    def tearDown(self):
        self.td.cleanup()

    def test_route_registered_and_dispatch_shape(self):
        self.assertIn(api.ROUTE_CAP, api.ROUTES)
        self.assertIsNotNone(api.ROUTES[api.ROUTE_CAP])
        self.assertIsNone(api.dispatch("/api/v2/nope.json", {}))
        status, payload = api.dispatch(api.ROUTE_CAP, {}, ledger_dir="x",
                                       battles_dir=self.bdir)
        self.assertEqual(status, 200)
        self.assertIn("series", payload)
        self.assertEqual(payload["series"][0]["n"], 1)


class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 由 UI-1 舰分发）：/api/v2/* 过会话门。"""

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            status, payload = api.dispatch(u.path, q,
                                           ledger_dir=self.server.ledger_dir,
                                           battles_dir=self.server.battles_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class TestV2MountContract(unittest.TestCase):
    """动态口真服（禁碰 8900 系）：会话门+真数据过 HTTP。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.bdir = os.path.join(cls.td.name, "battles")
        os.makedirs(cls.bdir)
        make_battle(cls.bdir, 1, recall_line=(2, 2), dollars=2.0,
                    matrix=[("a", "xss", "x")])
        make_battle(cls.bdir, 2, recall_line=(1, 2), dollars=2.0,
                    matrix=[("a", "xss", "?")])
        ledger = os.path.join(cls.td.name, "G-bare")
        os.makedirs(ledger, exist_ok=True)
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=ledger,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=cls.bdir)
        cls.port = cls.srv.server_address[1]
        assert cls.port not in (8900, 3000, 8787, 8443)
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()
        cls.sid = webui_login.login(cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stopping = True
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.td.cleanup()

    def _get(self, path, cookie=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, json.loads(body.decode("utf-8"))

    def test_session_gate_401_without_cookie(self):
        status, payload = self._get(api.ROUTE_CAP, cookie=False)
        self.assertEqual(status, 401)
        self.assertIn("error", payload)

    def test_logged_in_serves_series_over_http(self):
        status, payload = self._get(api.ROUTE_CAP)
        self.assertEqual(status, 200)
        self.assertEqual([b["n"] for b in payload["series"]], [1, 2])
        self.assertTrue(payload["warnings"])          # 下降段告警旗过 HTTP 在案


if __name__ == "__main__":
    unittest.main()
