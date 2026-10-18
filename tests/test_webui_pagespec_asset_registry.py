# -*- coding: utf-8 -*-
"""T7·资产库页钉测（界面线施工计划 2026-10-18 续程①：跨任务资产登记处读面）。

python3 -m unittest tests.test_webui_pagespec_asset_registry
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18（资产库跨任务）；
文案宪法#41（界面人话律）——「任务」上屏（battle 不上屏），资产=登记处口径。

数据单源：battles/*/G-*/assets.tsv 跨代合并（同 id 后代胜）→ 按资产值归并
跨任务登记；findings.tsv affected_asset_id 反指（活跃行口径）+ timeline
request: 行按资产值 token 边界归并（已测请求数）——与 P5.6 任务内资产页同
口径、跨任务聚合（单源口径不另造）。

三层钉：
  ①投影层  api_v2_asset_registry.asset_registry_view——按值归并(id 册/类型/
           出现任务清单+复判/关联发现/已测请求)；跨代同 id 后代胜；搜索 q；
           空目录降级空表。
  ②挂载层  /api/v2/asset-registry.json 过会话门（无 cookie=401 JSON）；
           动态口真服过 HTTP 返夹具登记（跨任务聚合真数据）。
  ③页面层  static/pages/asset-registry.html——搜索+计数+资产表+任务展开+
           四态+nav.push 自注册+零 CDN。
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
from webui import api_v2_asset_registry as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

# 夹具=core.TABLES 列序的行式 TSV（账本表无表头——core.Session.rows 同口径）


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_fixture(root):
    """两战夹具 + 一战跨代翻案夹具（同 id 后代胜）。"""
    b1 = os.path.join(root, "battle-1", "G-r2")
    _write(os.path.join(b1, "assets.tsv"), [
        "AST-1\thost\tapi.example.com\t-\t1\t1\t2026-10-01T00:00:00Z",
        "AST-2\thost\told.example.com\t-\t0\t1\t2026-10-01T00:00:00Z",
    ])
    _write(os.path.join(b1, "findings.tsv"), [
        "F-1\tINT-1\t反射 XSS\t0.9\thigh\tverified\t-\tdk1\t-\tok\t简\t步\tAST-1\tEV-1\t\t\t\t1\t2026-10-01T01:00:00Z",
    ])
    _write(os.path.join(b1, "timeline.tsv"), [
        "2026-10-01T01:00:00Z\tplanner\tP2\trequest: api.example.com/search\t-\t-\t-\t1",
        "2026-10-01T02:00:00Z\tplanner\tP2\trequest: api.example.com/search\t-\t-\t-\t1",
        "2026-10-01T03:00:00Z\tplanner\tP2\trequest: other.host/x\t-\t-\t-\t1",
    ])
    b2 = os.path.join(root, "battle-2", "G-r5")
    _write(os.path.join(b2, "assets.tsv"), [
        "AST-9\thost\tapi.example.com\t-\t1\t1\t2026-10-02T00:00:00Z",
        "AST-3\tdomain\tsub.example.com\t-\tin_scope\t1\t2026-10-02T00:00:00Z",
    ])
    _write(os.path.join(b2, "findings.tsv"), [
        "F-2\tINT-2\tSQL 注入\t0.8\thigh\tverified\t-\tdk2\t-\tok\t简\t步\tAST-9\tEV-2\t\t\t\t1\t2026-10-02T01:00:00Z",
        "F-3\tINT-3\t已被取代\t0.5\tlow\tsuspected\t-\tdk3\t-\tok\t简\t步\tAST-9\tEV-3\t\t\tsuperseded\t1\t2026-10-02T02:00:00Z",
    ])
    _write(os.path.join(b2, "timeline.tsv"), [
        "2026-10-02T01:00:00Z\tplanner\tP2\trequest: api.example.com/api/users\t-\t-\t-\t1",
        "2026-10-02T01:30:00Z\tplanner\tP2\trequest: api.example.com/api/users\t-\t-\t-\t1",
        "2026-10-02T02:00:00Z\tplanner\tP2\trequest: api.example.com/api/users\t-\t-\t-\t1",
    ])
    # battle-3：跨代翻案（AST-5 在 G-r10 改判范围外——后代胜）
    _write(os.path.join(root, "battle-3", "G-r2", "assets.tsv"), [
        "AST-5\thost\tv.example.com\t-\t1\t1\t2026-10-03T00:00:00Z",
    ])
    _write(os.path.join(root, "battle-3", "G-r10", "assets.tsv"), [
        "AST-5\thost\tv.example.com\t-\t0\t1\t2026-10-03T06:00:00Z",
    ])
    return root


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
        self.root = build_fixture(os.path.join(self.td.name, "battles"))

    def view(self, **kw):
        kw.setdefault("battles_dir", self.root)
        return api.asset_registry_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestRegistryProjection(Base):
    def test_group_by_value_across_battles(self):
        p = self.view()
        row = [a for a in p["assets"] if a["value"] == "api.example.com"][0]
        self.assertEqual(row["type"], "host")
        self.assertEqual(row["battle_count"], 2)
        self.assertEqual([b["id"] for b in row["battles"]], ["battle-1", "battle-2"])
        self.assertEqual(row["requests"], 5)                 # 2+3 跨任务合计
        self.assertEqual(row["findings_count"], 2)           # 活跃行口径
        self.assertEqual(row["first_battle"], "battle-1")

    def test_per_battle_verdicts(self):
        p = self.view()
        row = [a for a in p["assets"] if a["value"] == "api.example.com"][0]
        verdicts = {b["id"]: b["auth_zh"] for b in row["battles"]}
        self.assertEqual(verdicts["battle-1"], "复判✓")
        self.assertEqual(verdicts["battle-2"], "复判✓")
        old = [a for a in p["assets"] if a["value"] == "old.example.com"][0]
        self.assertEqual(old["battles"][0]["auth_zh"], "范围外")
        self.assertEqual(old["findings_count"], 0)

    def test_multigen_later_gen_wins(self):
        p = self.view()
        row = [a for a in p["assets"] if a["value"] == "v.example.com"][0]
        self.assertEqual(row["battle_count"], 1)
        self.assertEqual(row["battles"][0]["auth_zh"], "范围外")   # G-r10 后代胜

    def test_counts(self):
        p = self.view()
        self.assertEqual(p["counts"]["battles"], 3)
        self.assertEqual(p["counts"]["assets"], 4)           # 唯一资产值
        self.assertEqual(p["counts"]["cross_battle"], 1)
        self.assertEqual(p["counts"]["requests_total"], 5)
        self.assertEqual(p["counts"]["findings_total"], 2)

    def test_search_q(self):
        p = self.view(q="old.")
        self.assertEqual([a["value"] for a in p["assets"]], ["old.example.com"])
        p2 = self.view(q="EXAMPLE")                          # 大小写不敏感
        self.assertEqual(len(p2["assets"]), 4)
        p3 = self.view(q="domain")                           # 类型命中
        self.assertEqual([a["value"] for a in p3["assets"]], ["sub.example.com"])
        p4 = self.view(q="不存在")
        self.assertEqual(p4["assets"], [])
        self.assertTrue(p4["q"])

    def test_sort_deterministic(self):
        p = self.view()
        self.assertEqual([a["value"] for a in p["assets"]],
                         sorted(a["value"] for a in p["assets"]))

    def test_empty_dir_tolerant(self):
        empty = os.path.join(self.td.name, "none")
        p = api.asset_registry_view(battles_dir=empty)
        self.assertEqual(p["assets"], [])
        self.assertEqual(p["counts"]["assets"], 0)
        self.assertEqual(p["counts"]["battles"], 0)

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.td.name), before)
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


class TestV2MountContract(unittest.TestCase):
    """动态口真服（禁碰 8900）：会话门+夹具登记过 HTTP。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.ledger = os.path.join(cls.td.name, "G-bare")
        os.makedirs(cls.ledger, exist_ok=True)
        cls.root = build_fixture(os.path.join(cls.td.name, "battles"))
        from tests import webui_login
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=cls.ledger,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=cls.root)
        cls.port = cls.srv.server_address[1]
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
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/asset-registry.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_registry_over_http(self):
        conn, resp = self._get("/api/v2/asset-registry.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["battles"], 3)
        row = [a for a in p["assets"] if a["value"] == "api.example.com"][0]
        self.assertEqual(row["battle_count"], 2)
        conn.close()

    def test_q_over_http(self):
        conn, resp = self._get("/api/v2/asset-registry.json?q=sub.example")
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual([a["value"] for a in p["assets"]], ["sub.example.com"])
        conn.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "asset-registry.html")
ZONE_MARKS = (
    # 顶条：搜索 + 计数
    'id="reg-search"', 'id="reg-counts"',
    # 资产表（资产/类型/出现任务/复判/关联发现/已测请求）
    'id="reg-table"', "出现任务", "复判", "关联发现", "已测请求",
    # 跨任务登记说明
    "跨任务",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/asset-registry.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场")


class TestPageStructure(unittest.TestCase):
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
        self.assertIn("id: 'asset-registry'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_230(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 230, "资产库页量纲")


if __name__ == "__main__":
    unittest.main()
