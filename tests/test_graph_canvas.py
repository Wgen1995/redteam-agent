# -*- coding: utf-8 -*-
"""画布段——graph.html 战场画布钉（pan/zoom/全图/小地图/节点卡/详情侧板）。

python3 -m unittest tests.test_graph_canvas
结构钉=零执行环境的静态源断言（容器/控件/类钩子/常量）；
活体钉=playwright DOM 冒烟（缩放后 transform 变化/点卡侧板出现/全图复位/
小地图跳转/缩放低于阈值隐藏边名）——本模型无图不截屏，一律 DOM 断言，
零 pageerror 是每条活体钉的收尾断言。
律：Python 3.9 纯 stdlib（playwright 可缺席→活体类整体跳过不红）、只读、
工艺令与文案令由 test_ui_craft/test_ui_copy/test_v09d_* 同页共管。
"""
import os
import re
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

STATIC = os.path.join(CLI, "webui", "static")
GRAPH_HTML = os.path.join(STATIC, "graph.html")

TS1 = "2026-10-16T01:00:00Z"
TS2 = "2026-10-16T02:00:00Z"

KIND_CN_ALL = ("生成", "得出", "推导自", "证明", "隶属于", "攻击路径",
               "交叉引用", "证据支撑", "取代", "范围关系")


def _src():
    with open(GRAPH_HTML, encoding="utf-8") as f:
        return f.read()


class TestGraphCanvasStructure(unittest.TestCase):
    """静态结构钉：画布=地图、节点=卡、点卡=侧板、边名常显的全部 DOM 钩子。"""

    def test_canvas_containers_present(self):
        src = _src()
        for hook in ('id="graph"', 'id="world"', 'id="canvas-tools"',
                     'id="minimap"', 'id="mini-view"'):
            self.assertIn(hook, src, "画布缺容器 " + hook)
        self.assertIn("edge-layer", src, "画布缺边线层 edge-layer")

    def test_zoom_controls_present(self):
        src = _src()
        for hook in ('id="zoom-in"', 'id="zoom-out"', 'id="zoom-fit"',
                     'id="zoom-level"'):
            self.assertIn(hook, src, "缩放控件缺 " + hook)
        self.assertIn("全图", src, "全图按钮缺中文文案")

    def test_node_card_class_hooks(self):
        src = _src()
        for cls in ("node-card", "nc-badge", "nc-num", "nc-title",
                    "nc-dot", "nc-impact"):
            self.assertIn(cls, src, "节点卡缺类钩子 " + cls)

    def test_unverified_fade_hook(self):
        """未证实=整体 45% 淡显（类钩子+透明度档）。"""
        src = _src()
        self.assertIn(".node-card.unverified", src, "缺未证实淡显类钩子")
        self.assertRegex(src, r"unverified[^}]*opacity:\s*\.45",
                         "未证实淡显须 45% 透明度")

    def test_status_dot_hooks(self):
        src = _src()
        for st in ("已完成", "进行中", "未证实"):
            self.assertIn('[data-status="%s"]' % st, src,
                          "状态色点缺钩子 " + st)

    def test_impact_badge_hooks(self):
        src = _src()
        for lv in ("高", "中", "低"):
            self.assertIn('[data-impact="%s"]' % lv, src,
                          "危级徽章缺钩子 " + lv)

    def test_zoom_discipline_constants(self):
        """缩放域 0.1~2 倍写成命名常量（禁散落魔数）。"""
        src = _src()
        self.assertIn("ZOOM_MIN = 0.1", src)
        self.assertIn("ZOOM_MAX = 2", src)

    def test_edge_label_threshold_and_ten_kind_names(self):
        """边名常显+低于 0.4 隐藏；十型中文名单源在页。"""
        src = _src()
        self.assertIn("LABEL_MIN = 0.4", src)
        self.assertIn("labels-off", src)
        for name in KIND_CN_ALL:
            self.assertIn(name, src, "边型中文名缺 " + name)

    def test_detail_panel_hooks(self):
        src = _src()
        for hook in ('id="detail"', 'id="detail-close"', "d-edge",
                     "data-node"):
            self.assertIn(hook, src, "详情侧板缺钩子 " + hook)

    def test_minimap_jump_hook(self):
        src = _src()
        self.assertIn("minimapJump", src, "小地图点击跳转函数缺")
        self.assertIn("mdot", src, "小地图节点缩影缺类钩子")

    def test_layer_columns_kept(self):
        """分层列序=目标→意图→资产/凭据→事实→发现→证据（沿用六层）。"""
        src = _src()
        m = re.search(r"LAYER_NAMES\s*=\s*\{(.*?)\}", src, re.S)
        self.assertIsNotNone(m, "缺 LAYER_NAMES 分层表")
        for name in ("目标", "意图", "资产/凭据", "事实", "发现", "证据"):
            self.assertIn(name, m.group(1), "分层名缺 " + name)

    def test_fetch_still_graph_api(self):
        self.assertIn("/api/graph.json", _src())


# ---------------------------------------------------------------------------
# 活体 DOM 冒烟（playwright；浏览器缺席整类跳过不红）
# ---------------------------------------------------------------------------

def _row(tname, **kw):
    from ledger import core
    r = [""] * len(core.TABLES[tname])
    for k, v in kw.items():
        r[core.TABLES[tname].index(k)] = str(v)
    return r


def build_canvas_fixture(td):
    """11 节点跨六层（含 1 未证实意图 + 1 高危发现）+7 边的 mini 记录。"""
    from ledger import core
    gd = os.path.join(td, "G-cv")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [_row(
        "goals.tsv", id="G-cv-0001", target="shop.example",
        objective="授权渗透：画布验证", budget="1000;100;10",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        _row("intents.tsv", id="INT-cv-0001", title="面板测绘",
             status="done", kind="recon", origin="entity",
             schema_version="2", created=TS1),
        _row("intents.tsv", id="INT-cv-0002", title="越权试探",
             status="candidate", kind="authz-diff", origin="llm",
             schema_version="2", created=TS2)])
    core.write_tsv(os.path.join(gd, "assets.tsv"), [
        _row("assets.tsv", id="AST-cv-0001", type="app",
             value="web.admin-panel", in_scope="1",
             schema_version="2", created=TS1),
        _row("assets.tsv", id="AST-cv-0002", type="endpoint",
             value="web.api", in_scope="1",
             schema_version="2", created=TS1),
        _row("assets.tsv", id="AST-cv-0003", type="endpoint",
             value="web.static", in_scope="1",
             schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "facts.tsv"), [_row(
        "facts.tsv", id="F-cv-0001", intent_id="INT-cv-0001", kind="port",
        target="AST-cv-0002", detail="443 开放", confidence="C1",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [_row(
        "findings.tsv", id="FD-cv-0001", intent_id="INT-cv-0001",
        title="admin 面板匿名可读", confidence="C2", impact="高",
        exploitation_status="suspected", dedup_key="admin-anon-read",
        scope_check="in_scope", description_brief="未登录可读订单列表",
        affected_asset_id="AST-cv-0002", evidence_ids="EV-cv-0001",
        status="open", schema_version="2", created=TS2)])
    core.write_tsv(os.path.join(gd, "creds.tsv"), [_row(
        "creds.tsv", id="CRED-cv-0001", kind="session", role="admin",
        scope_asset="AST-cv-0002", obtained_via_intent="INT-cv-0001",
        status="active", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        _row("E-index.tsv", id="EV-cv-0001", title="子域清单",
             source_type="command", observed_at=TS1,
             network_position="internet", repro_kind="single",
             repro_command="curl -s https://crt.example/q?d=shop.example",
             content_hash_raw="a" * 64, content_hash_norm="b" * 64,
             card_path="evidence/EV-cv-0001.md", linked_finding="FD-cv-0001",
             pair_group="PG-cv-0001", raw_excerpt="12 subdomains",
             schema_version="2", created=TS1),
        _row("E-index.tsv", id="EV-cv-0002", title="登录响应",
             source_type="http", observed_at=TS2,
             network_position="dmz", repro_kind="single",
             repro_command="curl -i http://shop.example/login",
             content_hash_raw="c" * 64, content_hash_norm="d" * 64,
             artifact_path="artifacts/EV-cv-0002.raw",
             raw_excerpt="Set-Cookie: sid=...",
             schema_version="2", created=TS2)])
    edges = [
        ("spawns", "G-cv-0001", "INT-cv-0001"),
        ("spawns", "G-cv-0001", "INT-cv-0002"),
        ("yields", "INT-cv-0001", "F-cv-0001"),
        ("proves", "INT-cv-0001", "FD-cv-0001"),
        ("evidences", "EV-cv-0001", "FD-cv-0001"),
        ("parent", "AST-cv-0002", "AST-cv-0001"),
        ("attack", "FD-cv-0001", "AST-cv-0002"),
    ]
    core.write_tsv(os.path.join(gd, "edges.tsv"), [
        _row("edges.tsv", id="E-cv-%04d" % (i + 1), kind=k,
             source_id=sr, target_id=ds, provenance="P2",
             schema_version="2", created=TS1)
        for i, (k, sr, ds) in enumerate(edges)])
    return gd


def _parse_scale(transform):
    m = re.search(r"scale\(([0-9.]+)\)", transform or "")
    return float(m.group(1)) if m else None


class TestGraphCanvasSmoke(unittest.TestCase):
    """活体 DOM 冒烟：真 server + 真 Chrome，零截屏零截图断言。"""

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:                       # noqa: BLE001
            raise unittest.SkipTest("playwright 不可用: %s" % e)
        # R64 环境守卫（③）：同进程 asyncio loop 在跑时 Playwright Sync API
        # 不可用——浏览器不可用即环境性跳过（不许假绿不许裸红）
        import asyncio
        try:
            _loop = asyncio.get_event_loop()
        except RuntimeError:
            _loop = None
        if _loop is not None and _loop.is_running():
            raise unittest.SkipTest(
                "asyncio loop 在跑: Playwright Sync API 不可用 ENV-SKIP")
        from webui import server as srv_mod
        from tests import webui_login
        cls.td = tempfile.TemporaryDirectory()
        cls.gd = build_canvas_fixture(cls.td.name)
        cls.srv = srv_mod.make_server("127.0.0.1", 0, cls.gd,
                                      tail=3, poll_s=0.05, keepalive_s=1.0,
                                      operator_key=webui_login.OP_KEY)
        cls.port = cls.srv.server_address[1]
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()
        cls.sid = webui_login.login(cls.port)     # B舰 P0 后：读面须会话
        cls.pw = sync_playwright().start()
        try:
            try:
                cls.browser = cls.pw.chromium.launch()
            except Exception:                        # 缺内置二进制→系统 Chrome
                cls.browser = cls.pw.chromium.launch(channel="chrome")
        except Exception as e:                       # noqa: BLE001
            cls._teardown_all()
            raise unittest.SkipTest("浏览器不可用: %s" % e)
        cls.context = cls.browser.new_context()
        cls.context.add_cookies([{"name": "tanyin_sess", "value": cls.sid,
                                  "url": "http://127.0.0.1:%d" % cls.port}])

    @classmethod
    def _teardown_all(cls):
        if hasattr(cls, "srv"):
            cls.srv.stopping = True
            cls.srv.shutdown()
            cls.srv.server_close()
        if hasattr(cls, "td"):
            cls.td.cleanup()
        if hasattr(cls, "pw"):
            cls.pw.stop()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "context"):
            cls.context.close()
        if hasattr(cls, "browser"):
            cls.browser.close()
        cls._teardown_all()

    def setUp(self):
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.goto("http://127.0.0.1:%d/graph" % self.port)
        self.page.wait_for_selector("#graph-box[data-state=ready] .node-card",
                                    timeout=10000)

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [],
                         "活体冒烟须零 pageerror: %s" % self.errors)

    def _scale(self):
        t = self.page.eval_on_selector("#world", "el => el.style.transform")
        s = _parse_scale(t)
        self.assertIsNotNone(s, "world transform 缺 scale: %r" % t)
        return s

    def _zoom_level_text(self):
        return self.page.text_content("#zoom-level").strip()

    def test_node_cards_render_with_hooks(self):
        n = self.page.locator(".node-card").count()
        self.assertEqual(n, 11, "节点卡数应=11")
        self.assertGreater(self.page.locator(".node-card.unverified").count(),
                           0, "未证实卡应淡显存在")
        impact = self.page.locator('.nc-impact[data-impact="高"]')
        self.assertEqual(impact.count(), 1, "高危发现卡应带危级徽章")
        dots = self.page.locator(".nc-dot[data-status]")
        self.assertEqual(dots.count(), 11, "每卡一个状态色点")

    def test_zoom_buttons_change_transform(self):
        s0 = self._scale()
        self.page.click("#zoom-in")
        s1 = self._scale()
        self.assertGreater(s1, s0, "放大后 scale 须变大")
        self.assertEqual(self._zoom_level_text(),
                         "%d%%" % round(s1 * 100), "缩放读数须同步")
        self.page.click("#zoom-out")
        self.page.click("#zoom-out")
        s2 = self._scale()
        self.assertLess(s2, s1, "缩小后 scale 须变小")

    def test_zoom_clamped_between_min_and_max(self):
        for _ in range(40):
            self.page.click("#zoom-out")
        self.assertGreaterEqual(self._scale(), 0.1, "下限 0.1")
        for _ in range(60):
            self.page.click("#zoom-in")
        self.assertLessEqual(self._scale(), 2.0, "上限 2")

    def test_click_card_opens_detail(self):
        card = self.page.locator(".node-card").first
        num = card.locator(".nc-num").text_content().strip()
        card.click()
        self.page.wait_for_selector("#detail.open", timeout=3000)
        node_id = self.page.get_attribute("#detail", "data-node")
        self.assertEqual(node_id, card.get_attribute("data-id"))
        body = self.page.text_content("#detail")
        self.assertIn(num, body, "侧板须显示编号角标全文")
        self.page.click("#detail-close")
        self.assertEqual(self.page.locator("#detail.open").count(), 0,
                         "关闭后侧板应收起")

    def test_detail_edge_row_jumps_to_opposite_node(self):
        cards = self.page.locator(".node-card")
        for i in range(cards.count()):
            if cards.nth(i).get_attribute("data-id") == "INT-cv-0001":
                cards.nth(i).click()
                break
        self.page.wait_for_selector("#detail.open .d-edge", timeout=3000)
        before = self.page.get_attribute("#detail", "data-node")
        self.page.locator("#detail .d-edge").first.click()
        self.page.wait_for_timeout(50)
        after = self.page.get_attribute("#detail", "data-node")
        self.assertNotEqual(after, before, "点关联行须跳到对面节点")
        self.assertEqual(self.page.locator("#detail.open").count(), 1)

    def test_fit_restores_panorama(self):
        s0 = self._scale()
        for _ in range(3):
            self.page.click("#zoom-in")
        self.assertGreater(self._scale(), s0)
        self.page.click("#zoom-fit")
        s1 = self._scale()
        self.assertAlmostEqual(s1, s0, delta=0.02,
                               msg="全图按钮须复位到整战场一览缩放")

    def test_minimap_click_jumps(self):
        dots = self.page.locator("#minimap .mdot").count()
        self.assertEqual(dots, 11, "小地图须含全节点缩影")
        t0 = self.page.eval_on_selector("#world", "el => el.style.transform")
        box = self.page.locator("#minimap").bounding_box()
        self.page.click("#minimap", position={
            "x": box["width"] * 0.75, "y": box["height"] * 0.25})
        t1 = self.page.eval_on_selector("#world", "el => el.style.transform")
        self.assertNotEqual(t0, t1, "点小地图须平移视口")

    def test_edge_labels_hidden_below_threshold(self):
        for _ in range(12):
            self.page.click("#zoom-out")
            if "labels-off" in (self.page.get_attribute("#world", "class")
                                or ""):
                break
        self.assertIn("labels-off",
                      self.page.get_attribute("#world", "class") or "",
                      "缩放低于 0.4 须隐藏边名避免糊")
        self.assertLess(self._scale(), 0.4)


if __name__ == "__main__":
    unittest.main()
