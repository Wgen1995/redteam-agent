# -*- coding: utf-8 -*-
"""v0.9b 观察面三页——覆盖热图/十边图/证据卡（计划 Task B1-B3）。

python3 -m unittest tests.test_v09b_pages
律（docs/design/tanyin-target-form.md §1/§3 + 计划共同律）：只读投影零写入、
纯 stdlib、3.9 兼容、前端零框架零 CDN、每页 JS<2000 行。
"""
import json, os, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from ledger import core, viz_render  # noqa: E402
from ledger.write_cmds import EDGE_KINDS  # noqa: E402

from webui import projections as proj_mod  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-14T01:00:00Z"
TS2 = "2026-10-14T02:00:00Z"
TS3 = "2026-10-14T03:00:00Z"
TS4 = "2026-10-14T04:00:00Z"
TS5 = "2026-10-14T05:00:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    """按 (ts, actor, phase, event) 铸链式 timeline 行（core.row_hash 同链法）。"""
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in rows_spec:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def build_mini_ledger(td):
    """mini 夹具：matrix 4 行（含 1 行过时重复键）/edges 10 kind 全覆盖/EV 三卡。"""
    gd = os.path.join(td, "G-w9")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-w9-0001", target="shop.example", objective="授权渗透：分区验证",
        budget="1000;100;10", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-w9-0001", title="面板测绘", status="done",
            kind="recon", origin="entity", schema_version="2", created=TS1),
        row("intents.tsv", id="INT-w9-0002", title="越权试探", status="candidate",
            kind="authz-diff", origin="llm", schema_version="2", created=TS2)])
    core.write_tsv(os.path.join(gd, "assets.tsv"), [
        row("assets.tsv", id="AST-w9-0001", type="app", value="web.admin-panel",
            in_scope="1", schema_version="2", created=TS1),
        row("assets.tsv", id="AST-w9-0002", type="endpoint", value="web.api",
            in_scope="1", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "facts.tsv"), [row(
        "facts.tsv", id="F-w9-0001", intent_id="INT-w9-0001", kind="port",
        target="AST-w9-0002", detail="443 开放", confidence="C1",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [row(
        "findings.tsv", id="FD-w9-0001", intent_id="INT-w9-0001", title="admin 面板匿名可读",
        confidence="C2", impact="高", exploitation_status="suspected",
        dedup_key="admin-anon-read", vuln_ref="CVE-2026-1337", scope_check="in_scope",
        description_brief="未登录可读订单列表", affected_asset_id="AST-w9-0002",
        evidence_ids="EV-w9-0001", status="open", schema_version="2", created=TS2)])
    core.write_tsv(os.path.join(gd, "creds.tsv"), [row(
        "creds.tsv", id="CRED-w9-0001", kind="session", role="admin",
        scope_asset="AST-w9-0002", obtained_via_intent="INT-w9-0001", status="active",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id="EV-w9-0001", title="子域清单", source_type="command",
            observed_at=TS1, network_position="internet",
            repro_command="curl -s https://crt.example/q?d=shop.example", repro_kind="single",
            content_hash_raw="a" * 64, content_hash_norm="b" * 64,
            card_path="evidence/EV-w9-0001.md", linked_finding="FD-w9-0001",
            pair_group="PG-w9-0001", raw_excerpt="12 subdomains",
            schema_version="2", created=TS1),
        row("E-index.tsv", id="EV-w9-0002", title="登录响应", source_type="http",
            observed_at=TS2, network_position="dmz",
            repro_command="curl -i http://shop.example/login", repro_kind="single",
            content_hash_raw="c" * 64, content_hash_norm="d" * 64,
            artifact_path="artifacts/EV-w9-0002.raw", raw_excerpt="Set-Cookie: sid=...",
            schema_version="2", created=TS2),
        row("E-index.tsv", id="EV-w9-0003", title="管理面板截图", source_type="manual",
            observed_at=TS3, network_position="intranet", repro_kind="manual",
            content_hash_raw="e" * 64, content_hash_norm="f" * 64,
            linked_finding="FD-w9-0001", raw_excerpt="匿名可读订单",
            schema_version="2", created=TS3)])
    edge_rows = [
        ("spawns", "G-w9-0001", "INT-w9-0001"),
        ("yields", "INT-w9-0001", "F-w9-0001"),
        ("derived_from", "F-w9-0001", "INT-w9-0002"),
        ("proves", "INT-w9-0001", "FD-w9-0001"),
        ("parent", "AST-w9-0001", "AST-w9-0002"),
        ("attack", "FD-w9-0001", "AST-w9-0002"),
        ("cross_ref", "F-w9-0001", "FD-w9-0001"),
        ("evidences", "EV-w9-0001", "FD-w9-0001"),
        ("supersedes", "EV-w9-0002", "EV-w9-0001"),
        ("scope-rel", "AST-w9-0001", "AST-w9-0002"),
    ]
    core.write_tsv(os.path.join(gd, "edges.tsv"), [
        row("edges.tsv", id="E-w9-%04d" % (i + 1), kind=k, source_id=sr,
            target_id=ds, provenance="P2", schema_version="2", created=TS1)
        for i, (k, sr, ds) in enumerate(edge_rows)])
    core.write_tsv(os.path.join(gd, "matrix.tsv"), [
        row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authn.missing",
            state="", updated=TS1, schema_version="2"),                      # 过时行（事件溯源被盖）
        row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authn.missing",
            state="?", reason="存疑：需复验", intent_id="INT-w9-0001",
            updated=TS2, schema_version="2"),
        row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authz.diff",
            state="x", reason="FD-w9-0001", intent_id="INT-w9-0001",
            updated=TS3, schema_version="2", frozen_at=TS3),                 # 冻结锚点格
        row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql",
            state="", updated=TS1, schema_version="2"),                      # 空格=欠账
    ])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-w9-0001"),
        (TS2, "CLI", "P2", "replay-probe EV-w9-0001 verdict=not-reproduced"),
        (TS3, "CLI", "P2", "replay-probe EV-w9-0001 verdict=reproduced"),
        (TS4, "CLI", "P2", "replay-probe EV-w9-0002 verdict=manual"),
        (TS5, "总控", "P3", "add-fact F-w9-0001")]))
    return gd


def dir_bytes(gd):
    out = {}
    for n in sorted(os.listdir(gd)):
        p = os.path.join(gd, n)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                out[n] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_mini_ledger(self.td.name)

    def _empty(self):
        empty = os.path.join(self.td.name, "G-empty")
        os.makedirs(empty)
        return empty


class TestMatrixViewV09b(Base):
    """B1 /api/matrix.json 投影：matrix 行+状态（frozen_at 有无）+热图轴+统计。"""

    def test_shape_axes_and_rows(self):
        mv = proj_mod.matrix_view(self.gd)
        for k in ("surfaces", "vuln_classes", "rows", "stats"):
            self.assertIn(k, mv)
        self.assertEqual(mv["surfaces"], ["web.admin-panel", "web.api"])
        self.assertEqual(mv["vuln_classes"], ["authn.missing", "authz.diff", "inj.sql"])
        by_key = {(r["attack_surface"], r["vuln_class"]): r for r in mv["rows"]}
        self.assertEqual(len(mv["rows"]), 3)                       # 事件溯源：同键取最新
        self.assertEqual(by_key[("web.admin-panel", "authn.missing")]["state"], "?")
        self.assertFalse(by_key[("web.admin-panel", "authn.missing")]["frozen"])
        fr = by_key[("web.admin-panel", "authz.diff")]
        self.assertEqual(fr["state"], "x")
        self.assertTrue(fr["frozen"])
        self.assertEqual(fr["frozen_at"], TS3)
        empty = by_key[("web.api", "inj.sql")]
        self.assertEqual(empty["state"], "")
        self.assertFalse(empty["frozen"])

    def test_stats_counts(self):
        st = proj_mod.matrix_view(self.gd)["stats"]
        self.assertEqual(st["cells"], 3)
        self.assertEqual(st["set"], 2)
        self.assertEqual(st["empty"], 1)
        self.assertEqual(st["frozen"], 1)

    def test_readonly_projection(self):
        before = dir_bytes(self.gd)
        proj_mod.matrix_view(self.gd)
        self.assertEqual(dir_bytes(self.gd), before)

    def test_deterministic_and_json_serializable(self):
        a, b = proj_mod.matrix_view(self.gd), proj_mod.matrix_view(self.gd)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_empty_dir_tolerant(self):
        mv = proj_mod.matrix_view(self._empty())
        self.assertEqual(mv["surfaces"], [])
        self.assertEqual(mv["vuln_classes"], [])
        self.assertEqual(mv["rows"], [])
        self.assertEqual(mv["stats"]["cells"], 0)


class TestGraphViewV09b(Base):
    """B2 /api/graph.json 投影：节点（id+kind+层）+edges 10 kind+着色语义。"""

    def test_nodes_kinds_layers_candidate(self):
        gv = proj_mod.graph_view(self.gd)
        by_id = {n["id"]: n for n in gv["nodes"]}
        self.assertEqual(len(gv["nodes"]), 11)
        expect_kind = {"G-w9-0001": "G", "INT-w9-0001": "INT", "INT-w9-0002": "INT",
                       "AST-w9-0001": "AST", "AST-w9-0002": "AST", "CRED-w9-0001": "CRED",
                       "F-w9-0001": "F", "FD-w9-0001": "FD", "EV-w9-0001": "EV",
                       "EV-w9-0002": "EV", "EV-w9-0003": "EV"}
        self.assertEqual(by_id.keys() ^ expect_kind.keys(), set())
        for nid, kind in expect_kind.items():
            self.assertEqual(by_id[nid]["kind"], kind, nid)
            self.assertEqual(by_id[nid]["layer"], viz_render.LAYER[kind], nid)  # 层语义同源
        self.assertFalse(by_id["INT-w9-0001"]["candidate"])
        self.assertTrue(by_id["INT-w9-0002"]["candidate"])        # candidate 半透明同语义

    def test_edges_cover_all_ten_kinds(self):
        gv = proj_mod.graph_view(self.gd)
        self.assertEqual(len(gv["edges"]), 10)
        self.assertEqual({e["kind"] for e in gv["edges"]}, EDGE_KINDS)
        for e in gv["edges"]:
            for f in ("id", "kind", "src", "dst"):
                self.assertIn(f, e)

    def test_edge_style_ten_distinct_with_viz_semantics(self):
        """10 kind 全区分 + viz_render 语义锚（attack 金/cross_ref 虚/supersedes 点/scope-rel 灰）。"""
        es = proj_mod.graph_view(self.gd)["edge_style"]
        self.assertEqual(set(es), EDGE_KINDS)
        pairs = {(v["color"], v["dash"]) for v in es.values()}
        self.assertEqual(len(pairs), 10, "10 kind 着色须两两可区分")
        for v in es.values():
            self.assertRegex(v["color"], "^#[0-9a-f]{6}$")
        self.assertEqual(es["attack"]["color"], "#d4a017")        # viz_render 金渲染值
        self.assertEqual(es["cross_ref"]["dash"], "6 4")          # 虚线
        self.assertEqual(es["supersedes"]["dash"], "2 3")         # 点线
        self.assertEqual(es["scope-rel"]["color"], "#555c66")     # viz_render 灰渲染值

    def test_readonly_deterministic_json(self):
        before = dir_bytes(self.gd)
        a = proj_mod.graph_view(self.gd)
        self.assertEqual(dir_bytes(self.gd), before)
        self.assertEqual(a, proj_mod.graph_view(self.gd))
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_empty_dir_tolerant(self):
        gv = proj_mod.graph_view(self._empty())
        self.assertEqual(gv["nodes"], [])
        self.assertEqual(gv["edges"], [])
        self.assertEqual(gv["stats"]["nodes"], 0)
        self.assertEqual(gv["stats"]["edges"], 0)


class TestEvidenceViewV09b(Base):
    """B3 /api/evidence.json 投影：E-index 卡（id/vuln_ref/verdict/请求响应哈希）。"""

    def test_cards_fields_and_verdict_latest_wins(self):
        ev = proj_mod.evidence_view(self.gd)
        ids = [c["id"] for c in ev["cards"]]
        self.assertEqual(ids, ["EV-w9-0001", "EV-w9-0002", "EV-w9-0003"])
        c1 = ev["cards"][0]
        self.assertEqual(c1["verdict"], "reproduced")              # 两条 probe 取最新
        self.assertEqual(c1["vuln_ref"], "CVE-2026-1337")          # linked_finding → findings.vuln_ref
        self.assertEqual(c1["content_hash_raw"], "a" * 64)         # 请求响应哈希
        self.assertEqual(c1["content_hash_norm"], "b" * 64)
        self.assertEqual(c1["linked_finding"], "FD-w9-0001")
        self.assertEqual(c1["title"], "子域清单")
        self.assertEqual(c1["repro_command"], "curl -s https://crt.example/q?d=shop.example")
        self.assertEqual(c1["network_position"], "internet")
        self.assertEqual(ev["cards"][1]["verdict"], "manual")
        self.assertEqual(ev["cards"][1]["vuln_ref"], "")           # 无挂接 finding
        self.assertEqual(ev["cards"][2]["verdict"], "")            # 未重放

    def test_stats_verdict_buckets(self):
        st = proj_mod.evidence_view(self.gd)["stats"]
        self.assertEqual(st, {"cards": 3, "reproduced": 1, "not_reproduced": 0,
                              "manual": 1, "env_diff": 0, "unprobed": 1})

    def test_readonly_deterministic_json(self):
        before = dir_bytes(self.gd)
        a = proj_mod.evidence_view(self.gd)
        self.assertEqual(dir_bytes(self.gd), before)
        self.assertEqual(a, proj_mod.evidence_view(self.gd))
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_empty_dir_tolerant(self):
        ev = proj_mod.evidence_view(self._empty())
        self.assertEqual(ev["cards"], [])
        self.assertEqual(ev["stats"]["cards"], 0)


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.gd,
                                       tail=3, poll_s=0.05, keepalive_s=1.0)
        self.port = self.srv.server_address[1]
        import threading
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop_server)

    def _stop_server(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _get(self, path, timeout=5):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path)
        return conn, conn.getresponse()


class TestServerRoutesV09b(ServerBase):
    """server 三新路由挂既有三分支旁：三页 HTML+三 API JSON。"""

    def test_coverage_page(self):
        conn, resp = self._get("/coverage")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        body = resp.read().decode("utf-8")
        self.assertIn('id="heatmap"', body)
        conn.close()

    def test_graph_page(self):
        conn, resp = self._get("/graph")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        self.assertIn('id="graph"', resp.read().decode("utf-8"))
        conn.close()

    def test_evidence_page(self):
        conn, resp = self._get("/evidence")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        self.assertIn('id="cards"', resp.read().decode("utf-8"))
        conn.close()

    def _get_json(self, path):
        conn, resp = self._get(path)
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        return data

    def test_api_matrix_json(self):
        data = self._get_json("/api/matrix.json")
        self.assertEqual(data["stats"]["cells"], 3)
        self.assertEqual(data["surfaces"], ["web.admin-panel", "web.api"])

    def test_api_graph_json(self):
        data = self._get_json("/api/graph.json")
        self.assertEqual(len(data["nodes"]), 11)
        self.assertEqual(len(data["edges"]), 10)
        self.assertEqual(set(data["edge_style"]), EDGE_KINDS)

    def test_api_evidence_json(self):
        data = self._get_json("/api/evidence.json")
        self.assertEqual(data["stats"]["cards"], 3)
        c1 = data["cards"][0]
        self.assertEqual(c1["id"], "EV-w9-0001")
        self.assertEqual(c1["verdict"], "reproduced")

    def test_api_hits_are_readonly(self):
        """投影律（服务端）：三 API 各打一轮，goal 目录字节不变。"""
        before = dir_bytes(self.gd)
        for p in ("/api/matrix.json", "/api/graph.json", "/api/evidence.json"):
            conn, resp = self._get(p)
            self.assertEqual(resp.status, 200, p)
            resp.read()
            conn.close()
        self.assertEqual(dir_bytes(self.gd), before)

    def test_404_unknown_still(self):
        conn, resp = self._get("/nope")
        self.assertEqual(resp.status, 404)
        conn.close()


STATIC = os.path.join(CLI, "webui", "static")
PAGES = {
    "coverage.html": ("/api/matrix.json",
                      ('id="heatmap"', 'id="legend"', 'id="stats"',
                       "c-empty", "c-frozen", "c-cold")),
    "graph.html": ("/api/graph.json",
                   ('id="graph"', 'id="edge-legend"', 'id="detail"',
                    "createElementNS",
                    # 画布段升级批追加钩子：缩放控件/小地图/节点卡
                    'id="zoom-fit"', 'id="minimap"', "node-card")),
    "evidence.html": ("/api/evidence.json",
                      ('id="cards"', "classList", "open")),
}


class TestPagesV09b(Base):
    """三静态页语言律：零框架零 CDN、单页 JS<2000 行、关键节点在。"""

    @staticmethod
    def _src(name):
        with open(os.path.join(STATIC, name), encoding="utf-8") as f:
            return f.read()

    def test_containers_and_fetch(self):
        for name, (api, marks) in PAGES.items():
            src = self._src(name)
            self.assertIn(api, src, name + " 须拉取 " + api)
            for m in marks:
                self.assertIn(m, src, name + " 缺 " + m)

    def test_zero_framework_zero_cdn(self):
        for name in PAGES:
            src = self._src(name)
            # v0.9d 收口批（E3 F2）：唯一外链=/status.js（server 字节级伺服）
            self.assertEqual(src.count('<script src="/status.js"></script>'),
                             1, name)
            self.assertEqual(src.count("<script src="), 1,
                             name + " 只许 status.js 一支外链")
            self.assertNotIn("https://", src, name)           # 无 CDN/外域
            # W3C SVG 命名空间是合法内联常量（test_viz 同款豁免）
            self.assertNotIn("http://", src.replace("http://www.w3.org", ""), name)

    def test_js_under_2000_lines(self):
        for name in PAGES:
            src = self._src(name)
            blocks = src.split("<script>")[1:]
            self.assertGreaterEqual(len(blocks), 1, name)
            nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
            self.assertLess(nlines, 2000, name)


if __name__ == "__main__":
    unittest.main()
