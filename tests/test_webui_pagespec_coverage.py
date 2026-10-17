# -*- coding: utf-8 -*-
"""T3·P5.7 资产覆盖页签钉测（界面线施工计划 2026-10-18 T3）。

python3 -m unittest tests.test_webui_pagespec_coverage
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P5.7（覆盖诚实法条的可视化）；
文案宪法#41。数据源=matrix 表（终态门禁分母）+assets 复判+timeline request: 深度。

三层钉：
  ①投影层  api_v2_coverage.coverage_view——资产×意图族热图（格=状态 x/?/-/!/空
           +深度=请求数对数色阶）+未测清单（资产/未测意图/原因[范围外/无凭据/
           预算止/待测/存疑]）；同格后代行胜（事件溯源）。
  ②挂载层  /api/v2/coverage.json 过会话门；battle 选战；坏战号=422、不存在=404。
  ③页面层  static/pages/coverage.html 结构钉（热图+对数色阶+未测斜纹+图例+
           未测清单表+四态+nav.push 自注册+零 CDN）。
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
from webui import api_v2_coverage as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-22T03:00:00Z"
TS2 = "2026-10-22T03:10:00Z"
TS3 = "2026-10-22T03:20:00Z"
TS4 = "2026-10-22T03:30:00Z"
TS5 = "2026-10-22T03:40:00Z"


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


def mrow(surface, vclass, state="", reason="", iid="", updated=TS4, frozen=""):
    return row("matrix.tsv", attack_surface=surface, vuln_class=vclass,
               state=state, reason=reason, intent_id=iid,
               schema_version="2", updated=updated, frozen_at=frozen)


def build_fixture(td):
    """battle-9 两代目：3 表面×6 类=11 格（x4/?1/-2/!2/空2）+请求深度。"""
    bdir = os.path.join(td, "battles", "battle-9")
    g1 = os.path.join(bdir, "G-r1")
    os.makedirs(g1)
    core.write_tsv(os.path.join(g1, "assets.tsv"), [
        row("assets.tsv", id="AST-9001", type="service", value="svc-shop",
            in_scope="in_scope", created=TS2),
        row("assets.tsv", id="AST-9002", type="service", value="svc-admin",
            in_scope="in_scope", created=TS2),
        row("assets.tsv", id="AST-9003", type="root-domain", value="evil.example",
            in_scope="out_of_scope", created=TS3),
    ])
    core.write_tsv(os.path.join(g1, "intents.tsv"), [
        row("intents.tsv", id="INT-9001", title="管理面信息收集", kind="recon",
            status="done", created=TS2),
        row("intents.tsv", id="INT-9002", title="会话机制核验", kind="matrix-test",
            status="done", created=TS2),
    ])
    core.write_tsv(os.path.join(g1, "matrix.tsv"), [
        mrow("svc-shop", "wstg-info", "x", "submatrix:tested:face 探测", "INT-9001"),
        mrow("svc-shop", "wstg-authn", "x", "submatrix:tested:JWT 核验", "INT-9001"),
        mrow("svc-shop", "wstg-inpv", "?", "首轮载荷未定论"),
        mrow("svc-shop", "wstg-cryp", "-", "not-applicable:无密码学面"),
        mrow("svc-shop", "wstg-sess", "!", "401 墙未破+凭据缺（无凭据）", "INT-9002"),
        mrow("svc-shop", "wstg-busl", ""),                       # 空=未检查
        mrow("svc-admin", "wstg-info", "x", "submatrix:tested:枚举", "INT-9001"),
        mrow("svc-admin", "wstg-authn", "?", "登录面两轮未定"),
        mrow("svc-admin", "wstg-cryp", "!", "budget-exhausted 挂起"),
        mrow("svc-admin", "wstg-busl", "-", "not-applicable:单面无业务流"),
        mrow("evil.example", "wstg-info", ""),
    ])
    core.write_tsv(os.path.join(g1, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-r1"),
        (TS2, "CLI", "P1", "add-asset AST-9001"),
        (TS3, "CLI", "P1", "add-asset AST-9003"),
        (TS4, "CLI", "P3", "request: svc-shop/login via=probe"),
        (TS4, "CLI", "P3", "request: svc-shop/admin via=probe"),
        (TS4, "CLI", "P3", "request: svc-shop/orders via=probe"),
        (TS4, "CLI", "P3", "request: svc-shop/api via=probe"),
        (TS4, "CLI", "P3", "request: svc-shop/search via=probe"),
        (TS4, "CLI", "P3", "request: svc-admin/admin via=probe"),
        (TS5, "总控", "P4", "matrix-freeze 锚点冻结"),
    ]))
    g2 = os.path.join(bdir, "G-r2")
    os.makedirs(g2)
    core.write_tsv(os.path.join(g2, "matrix.tsv"), [
        mrow("svc-shop", "wstg-busl", "x", "submatrix:tested:补测完成", "INT-9002",
             updated=TS5),                                       # 后代行翻案 空→x
        mrow("svc-shop", "wstg-inpv", "x", "submatrix:tested:载荷族补测",
             updated=TS5),                                       # ? → x
    ])
    core.write_tsv(os.path.join(g2, "timeline.tsv"), chained_tl([
        (TS5, "CLI", "P3", "matrix-set svc-shop×wstg-busl=x"),
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

class TestCoverageProjection(Base):
    """资产×意图族热图+未测清单投影：matrix 同格后代行胜。"""

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles_root)
        kw.setdefault("ledger_dir", self.ledger_dir)
        return api.coverage_view(**kw)

    def test_grid_shape_and_order(self):
        p = self.view()
        self.assertEqual(p["classes"], ["wstg-info", "wstg-authn", "wstg-inpv",
                                        "wstg-cryp", "wstg-sess", "wstg-busl"])
        self.assertEqual([s["name"] for s in p["surfaces"]],
                         ["svc-shop", "svc-admin", "evil.example"])

    def test_cell_states_and_override(self):
        p = self.view()
        shop = p["surfaces"][0]["cells"]
        self.assertEqual(shop["wstg-info"]["state"], "x")
        self.assertEqual(shop["wstg-info"]["state_zh"], "已覆盖")
        self.assertEqual(shop["wstg-inpv"]["state"], "x")       # G-r2 翻案 ?→x
        self.assertEqual(shop["wstg-cryp"]["state"], "-")
        self.assertEqual(shop["wstg-cryp"]["state_zh"], "不适用")
        self.assertEqual(shop["wstg-sess"]["state"], "!")
        self.assertEqual(shop["wstg-sess"]["state_zh"], "受阻")
        self.assertEqual(shop["wstg-busl"]["state"], "x")       # G-r2 翻案 空→x
        admin = p["surfaces"][1]["cells"]
        self.assertEqual(admin["wstg-authn"]["state"], "?")
        self.assertEqual(admin["wstg-authn"]["state_zh"], "存疑")
        self.assertNotIn("wstg-sess", admin)                    # 未建格=不虚造

    def test_depth_log_scale(self):
        p = self.view()
        shop = p["surfaces"][0]
        self.assertEqual(shop["requests"], 5)
        self.assertAlmostEqual(shop["depth"], 2.58, places=2)   # log2(5+1)
        admin = p["surfaces"][1]
        self.assertEqual(admin["requests"], 1)
        self.assertAlmostEqual(admin["depth"], 1.0, places=2)   # log2(1+1)
        evil = p["surfaces"][2]
        self.assertEqual(evil["requests"], 0)
        self.assertEqual(evil["depth"], 0.0)

    def test_cell_depth_inherited_from_surface(self):
        p = self.view()
        c = p["surfaces"][0]["cells"]["wstg-info"]
        self.assertEqual(c["requests"], 5)
        self.assertEqual(c["depth"], p["surfaces"][0]["depth"])
        self.assertEqual(c["intent_id"], "INT-9001")
        self.assertTrue(c["updated"])

    def test_untested_list_reason_taxonomy(self):
        p = self.view()
        ut = p["untested"]
        keys = [(u["surface"], u["vclass"]) for u in ut]
        # 未测 = state ∉ {x,-}：受阻/存疑/空/范围外四类各一（shop 两格已翻案）
        self.assertEqual(keys, [("svc-shop", "wstg-sess"),
                                ("svc-admin", "wstg-authn"),
                                ("svc-admin", "wstg-cryp"),
                                ("evil.example", "wstg-info")])
        by = {(u["surface"], u["vclass"]): u for u in ut}
        self.assertEqual(by[("svc-shop", "wstg-sess")]["reason_code"], "no_cred")
        self.assertEqual(by[("svc-shop", "wstg-sess")]["reason_zh"], "无凭据")
        self.assertEqual(by[("svc-admin", "wstg-cryp")]["reason_code"], "budget_stop")
        self.assertEqual(by[("svc-admin", "wstg-cryp")]["reason_zh"], "预算止")
        self.assertEqual(by[("svc-admin", "wstg-authn")]["reason_code"], "inconclusive")
        self.assertEqual(by[("evil.example", "wstg-info")]["reason_code"],
                         "out_of_scope")
        self.assertEqual(by[("evil.example", "wstg-info")]["reason_zh"], "范围外")

    def test_no_cred_reason(self):
        p = self.view()
        codes = [u["reason_code"] for u in p["untested"]]
        self.assertIn("no_cred", codes)             # wstg-sess 受阻=凭据缺

    def test_no_cred_derivation(self):
        gd = os.path.join(self.td.name, "G-cred")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "matrix.tsv"), [
            mrow("svc-x", "wstg-sess", "!", "认证墙未破 token 全拒（无凭据）"),
        ])
        p = api.coverage_view(battles_dir=os.path.join(self.td.name, "none"),
                              ledger_dir=gd)
        self.assertEqual(p["untested"][0]["reason_code"], "no_cred")
        self.assertEqual(p["untested"][0]["reason_zh"], "无凭据")

    def test_counts_and_coverage_pct(self):
        p = self.view()
        c = p["counts"]
        self.assertEqual(c["cells"], 11)
        self.assertEqual(c["covered"], 5)           # x：shop×4 + admin-info
        self.assertEqual(c["negative"], 2)
        self.assertEqual(c["blocked"], 2)
        self.assertEqual(c["inconclusive"], 1)
        self.assertEqual(c["untested"], 1)          # evil.example（空态）
        self.assertAlmostEqual(c["coverage_pct"], round((5 + 2) / 11 * 100, 1))

    def test_matrix_frozen_flag(self):
        p = self.view()
        self.assertTrue(p["matrix_frozen"])          # timeline matrix-freeze 行

    def test_battle_pick(self):
        p = self.view()
        self.assertEqual(p["battle"]["id"], "battle-9")
        self.assertEqual(p["goal"], "G-r2")
        p1 = self.view(battle="9")
        self.assertEqual(p1["battle"]["n"], 9)
        p2 = self.view(battle=10)
        self.assertIn("error", p2)
        with self.assertRaises(ValueError):
            self.view(battle="bad")

    def test_single_goal_fallback_and_empty(self):
        gd = os.path.join(self.td.name, "G-solo")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "matrix.tsv"), [
            mrow("svc-x", "wstg-info", "x", "tested"),
        ])
        p = api.coverage_view(battles_dir=os.path.join(self.td.name, "none"),
                              ledger_dir=gd)
        self.assertIsNone(p["battle"])
        self.assertEqual(p["counts"]["cells"], 1)
        gd2 = os.path.join(self.td.name, "G-bare")
        os.makedirs(gd2)
        p2 = api.coverage_view(battles_dir=os.path.join(self.td.name, "none"),
                               ledger_dir=gd2)
        self.assertEqual(p2["surfaces"], [])
        self.assertEqual(p2["untested"], [])
        self.assertEqual(p2["counts"]["cells"], 0)

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
    """/api/v2/coverage.json 会话门+分发（动态口=server_address[1]，禁碰 8900）。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/coverage.json", cookie=False)
        self.assertEqual(resp.status, 401)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertIn("会话", body["error"])
        conn.close()

    def test_over_http(self):
        conn, resp = self._get("/api/v2/coverage.json?battle=9")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["cells"], 11)
        self.assertEqual(len(p["classes"]), 6)
        conn.close()

    def test_unknown_battle_404_and_bad_422(self):
        conn, resp = self._get("/api/v2/coverage.json?battle=11")
        self.assertEqual(resp.status, 404)
        conn.close()
        conn, resp = self._get("/api/v2/coverage.json?battle=xx")
        self.assertEqual(resp.status, 422)
        conn.close()

    def test_http_hits_readonly(self):
        before = dir_bytes(self.bdir)
        conn, resp = self._get("/api/v2/coverage.json")
        self.assertEqual(resp.status, 200)
        resp.read()
        conn.close()
        self.assertEqual(dir_bytes(self.bdir), before)


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "coverage.html")
ZONE_MARKS = (
    'id="battle-pick"', 'id="cv-counts"',
    # 热图：格=对数色阶深度 + 未测斜纹 + 图例
    'id="heat-grid"', "heat-cell", 'id="cv-legend"', "Math.log2",
    "repeating-linear-gradient", "未测",
    # 未测清单表：资产/未测意图/原因[范围外/无凭据/预算止]
    'id="ut-table"', 'id="ut-body"', "未测意图", "范围外", "无凭据", "预算止",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 覆盖诚实法条披露
    "覆盖",
    # 宿主壳接入
    "CoverageTab", "mode-tab",
)
FETCH_MARKS = ("'/api/v2/coverage.json",)
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
        self.assertIn("id: 'coverage'", src)
        self.assertIn("label: '资产覆盖'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 250, "P5.7 页 ~300 行量纲")


if __name__ == "__main__":
    unittest.main()
