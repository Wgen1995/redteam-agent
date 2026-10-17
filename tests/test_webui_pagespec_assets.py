# -*- coding: utf-8 -*-
"""T3·P5.6 测试资产页签钉测（界面线施工计划 2026-10-18 T3）。

python3 -m unittest tests.test_webui_pagespec_assets
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P5.6；文案宪法#41（界面人话律）。
数据源=assets+scope 复判；已测请求数=timeline request: 行按资产值口径归并。

三层钉：
  ①投影层  api_v2_assets.assets_view——资产表(资产/类型/授权复判✓绿·范围外黄标/
           已测请求数/关联发现链接)+scope 汇总(include/exclude/oob/修订)；
           多代合并同 id 后代胜（复判可翻案）。
  ②挂载层  /api/v2/assets.json 过会话门（无 cookie=401 JSON）；battle 选战；
           坏战号=422、不存在=404；动态取口禁碰 8900。
  ③页面层  static/pages/assets.html 结构钉（资产表+DSL 搜索框[AND/OR/NOT]+四态+
           nav.push 自注册+零 CDN）。
"""
import json
import os
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from ledger import core  # noqa: E402
from webui import api_v2_assets as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-21T02:00:00Z"
TS2 = "2026-10-21T02:01:00Z"
TS3 = "2026-10-21T02:02:00Z"
TS4 = "2026-10-21T02:03:00Z"
TS5 = "2026-10-21T02:04:00Z"
TS6 = "2026-10-21T02:10:00Z"
TS7 = "2026-10-21T02:20:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in rows_spec:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def build_fixture(td):
    """battle-8 两代目：4 资产（2 授权 2 范围外）+scope 四态+修订行+请求归并。"""
    bdir = os.path.join(td, "battles", "battle-8")
    g1 = os.path.join(bdir, "G-r1")
    os.makedirs(g1)
    core.write_tsv(os.path.join(g1, "assets.tsv"), [
        row("assets.tsv", id="AST-8001", type="service", value="svc-shop",
            in_scope="in_scope", created=TS2),
        row("assets.tsv", id="AST-8002", type="app", value="shop.example",
            in_scope="in_scope", created=TS3),
        row("assets.tsv", id="AST-8003", type="root-domain", value="evil.example",
            in_scope="out_of_scope", created=TS4),
        row("assets.tsv", id="AST-8004", type="ip", value="10.0.0.0/8",
            in_scope="out_of_scope", created=TS5),
    ])
    core.write_tsv(os.path.join(g1, "scope.tsv"), [
        row("scope.tsv", id="S-8001", kind="include", matcher="*.shop.example",
            created=TS2),
        row("scope.tsv", id="S-8002", kind="include", matcher="svc-shop",
            created=TS2),
        row("scope.tsv", id="S-8003", kind="exclude", matcher="evil.example",
            created=TS2),
        row("scope.tsv", id="S-8004", kind="oob", matcher="oob.example",
            created=TS2),
        row("scope.tsv", id="S-8005", kind="include", matcher="new.example",
            amendment_of="S-8001", note="扩展审批通过后接入", created=TS6),
    ])
    core.write_tsv(os.path.join(g1, "findings.tsv"), [
        row("findings.tsv", id="FD-8001", title="管理面板匿名可读", impact="高",
            exploitation_status="verified", affected_asset_id="AST-8001",
            status="active", created=TS4),
        row("findings.tsv", id="FD-8002", title="登录接口无速率限制", impact="中",
            exploitation_status="suspected", affected_asset_id="AST-8001",
            status="active", created=TS5),
        row("findings.tsv", id="FD-8003", title="订单接口越权", impact="高",
            exploitation_status="verified", affected_asset_id="AST-8002",
            status="active", created=TS5),
    ])
    core.write_tsv(os.path.join(g1, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-r1"),
        (TS2, "CLI", "P1", "add-asset AST-8001"),
        (TS3, "CLI", "P1", "add-asset AST-8002"),
        (TS4, "CLI", "P2", "add-finding FD-8001"),
        (TS4, "replay", "P4", "request: svc-shop/login via=replay"),
        (TS4, "replay", "P4", "request: svc-shop/admin via=replay"),
        (TS5, "CLI", "P2", "add-finding FD-8002"),
        (TS5, "replay", "P4", "request: svc-shop/login via=replay"),
        (TS5, "replay", "P4", "request: shop.example/api/orders via=replay"),
        (TS6, "总控", "P1", "amend-scope S-8005->S-8001"),
    ]))
    g2 = os.path.join(bdir, "G-r2")
    os.makedirs(g2)
    core.write_tsv(os.path.join(g2, "assets.tsv"), [
        row("assets.tsv", id="AST-8003", type="root-domain", value="evil.example",
            in_scope="in_scope", created=TS4),          # 后代翻案：范围外→授权
        row("assets.tsv", id="AST-8005", type="service", value="svc-login",
            in_scope="in_scope", created=TS7),
    ])
    core.write_tsv(os.path.join(g2, "timeline.tsv"), chained_tl([
        (TS7, "CLI", "P1", "add-asset AST-8005"),
        (TS7, "replay", "P4", "request: evil.example/www via=replay"),
    ]))
    return bdir


def dir_bytes(root):
    out = {}
    for base, _dirs, files in os.walk(root):
        for n in sorted(files):
            p = os.path.join(base, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.bdir = build_fixture(self.td.name)
        self.battles_root = os.path.join(self.td.name, "battles")
        self.ledger_dir = os.path.join(self.bdir, "G-r2")


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestAssetsProjection(Base):
    """资产表投影：assets+scope 复判+请求归并+关联发现。"""

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles_root)
        kw.setdefault("ledger_dir", self.ledger_dir)
        return api.assets_view(**kw)

    def test_table_columns(self):
        p = self.view()
        a = {x["id"]: x for x in p["assets"]}
        s1 = a["AST-8001"]
        self.assertEqual(s1["type"], "service")
        self.assertEqual(s1["value"], "svc-shop")
        self.assertEqual(s1["in_scope"], "in_scope")
        self.assertEqual(s1["auth_zh"], "复判✓")             # 授权复判绿标
        self.assertEqual(s1["requests"], 3)                   # svc-shop 3 次请求
        self.assertEqual(s1["findings"], ["FD-8001", "FD-8002"])
        s2 = a["AST-8002"]
        self.assertEqual(s2["requests"], 1)                   # shop.example/… 前缀口径
        self.assertEqual(s2["findings"], ["FD-8003"])
        s4 = a["AST-8004"]
        self.assertEqual(s4["requests"], 0)                   # 网段无请求=诚实 0
        self.assertEqual(s4["auth_zh"], "范围外")

    def test_later_gen_overrides_verdict(self):
        p = self.view()
        a = {x["id"]: x for x in p["assets"]}
        self.assertEqual(a["AST-8003"]["in_scope"], "in_scope")   # G-r2 翻案
        self.assertEqual(a["AST-8003"]["auth_zh"], "复判✓")
        self.assertEqual(a["AST-8003"]["requests"], 1)            # G-r2 请求计入
        self.assertIn("AST-8005", a)                               # 新资产并入

    def test_request_counting_token_boundary(self):
        p = self.view()
        a = {x["id"]: x for x in p["assets"]}
        # svc-shop-admin 若在库不应把 svc-shop 的请求计入（无此资产=只验 svc-shop 精确 3）
        self.assertEqual(a["AST-8001"]["requests"], 3)

    def test_counts_and_scope_summary(self):
        p = self.view()
        c = p["counts"]
        self.assertEqual(c["total"], 5)
        self.assertEqual(c["in_scope"], 4)
        self.assertEqual(c["out_of_scope"], 1)
        self.assertEqual(c["tested"], 3)
        self.assertEqual(c["with_findings"], 2)
        sc = p["scope"]
        self.assertEqual(sc["include"], 3)
        self.assertEqual(sc["exclude"], 1)
        self.assertEqual(sc["oob"], 1)
        self.assertEqual(sc["amendments"], 1)

    def test_ordering_deterministic(self):
        p = self.view()
        ids = [x["id"] for x in p["assets"]]
        self.assertEqual(ids, ["AST-8001", "AST-8002", "AST-8003", "AST-8004",
                               "AST-8005"])                      # 首现序

    def test_battle_pick_and_goal(self):
        p = self.view()
        self.assertEqual(p["battle"]["id"], "battle-8")
        self.assertEqual(p["goal"], "G-r2")
        self.assertEqual(p["battles"][0]["n"], 8)
        p1 = self.view(battle="8")
        self.assertEqual(p1["battle"]["n"], 8)

    def test_unknown_battle_and_bad(self):
        p = self.view(battle=9)
        self.assertIn("error", p)
        with self.assertRaises(ValueError):
            self.view(battle="x!")

    def test_single_goal_fallback(self):
        gd = os.path.join(self.td.name, "G-solo")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "assets.tsv"), [row(
            "assets.tsv", id="AST-s1", type="service", value="svc-x",
            in_scope="in_scope", created=TS1)])
        p = api.assets_view(battles_dir=os.path.join(self.td.name, "none"),
                            ledger_dir=gd)
        self.assertIsNone(p["battle"])
        self.assertEqual(p["assets"][0]["id"], "AST-s1")

    def test_empty_ledger_tolerant(self):
        gd = os.path.join(self.td.name, "G-bare")
        os.makedirs(gd)
        p = api.assets_view(battles_dir=os.path.join(self.td.name, "none"),
                            ledger_dir=gd)
        self.assertEqual(p["assets"], [])
        self.assertEqual(p["counts"]["total"], 0)
        self.assertEqual(p["scope"]["include"], 0)

    def test_readonly_deterministic(self):
        before = dir_bytes(self.bdir)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.bdir), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)


# ═══════════════════════════════ ② 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 未落地）：/api/v2/* 过会话门后分发 ROUTES。"""

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            status, payload = api.dispatch(u.path, q, ledger_dir=self.server.ledger_dir,
                                           battles_dir=self.server.battles_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.ledger_dir,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=self.battles_root)
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)
        self.sid = webui_login.login(self.port)

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _get(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()


class TestV2MountContract(ServerBase):
    """/api/v2/assets.json 会话门+分发（动态口=server_address[1]，禁碰 8900）。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/assets.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_over_http(self):
        conn, resp = self._get("/api/v2/assets.json?battle=8")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["total"], 5)
        conn.close()

    def test_unknown_battle_404_over_http(self):
        conn, resp = self._get("/api/v2/assets.json?battle=99")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_bad_battle_422_over_http(self):
        conn, resp = self._get("/api/v2/assets.json?battle=zz")
        self.assertEqual(resp.status, 422)
        conn.close()

    def test_http_hits_readonly(self):
        before = dir_bytes(self.bdir)
        conn, resp = self._get("/api/v2/assets.json")
        self.assertEqual(resp.status, 200)
        resp.read()
        conn.close()
        self.assertEqual(dir_bytes(self.bdir), before)


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "assets.html")
ZONE_MARKS = (
    'id="battle-pick"', 'id="as-counts"',
    # 资产表：资产/类型/授权复判✓/范围外黄标/已测请求数/关联发现链接
    'id="as-table"', 'id="as-body"', "授权复判", "范围外", "已测请求数", "关联发现",
    "复判✓",
    # DSL 搜索框（AND/OR/NOT 三连词）
    'id="dsl-input"', 'id="dsl-go"', 'id="dsl-hits"', "AND", "OR", "NOT", "type:",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 跳转漏洞详情
    "finding-detail.html",
    # 宿主壳接入
    "AssetsTab", "mode-tab",
)
FETCH_MARKS = ("'/api/v2/assets.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "复测岗")


class TestPageStructure(Base):
    def _src(self):
        with open(PAGE, encoding="utf-8") as f:
            return f.read()

    def test_zones_and_states_present(self):
        src = self._src()
        for m in ZONE_MARKS:
            self.assertIn(m, src, "缺 " + m)
        for m in FETCH_MARKS:
            self.assertIn(m, src, "须拉取 " + m)
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src, "宪法#41 禁词上屏: " + bad)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'assets'", src)
        self.assertIn("label: '测试资产'", src)
        self.assertIn("group: '任务详情'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_250(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 250, "P5.6 页 ~280 行量纲")


if __name__ == "__main__":
    unittest.main()
