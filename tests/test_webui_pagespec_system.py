# -*- coding: utf-8 -*-
"""T7·系统配置页钉测（界面线施工计划 2026-10-18 续程④：读面+写面留位）。

python3 -m unittest tests.test_webui_pagespec_system
律：投影只读零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN；读面=全局配置
（不随任务换源）；写面=留位不开（W7 权限门后开——POST_ROUTES 恒空）。
文案宪法#41（界面人话律）。

数据单源（spec §P8-P18 系统配置页）：
  门禁三速度 = docs/design/gates-speed-v1.md §三速度（疾速/预授权/严审——
              设计档单源，投影只转述不另立）；
  守卫档     = goals 强度档枚举（model_tier strong|weak / guard_tier T1|T2|T3
              ——server/api_v2_tasks 同域枚举）；
  预算默认   = contracts/01 预算三元组形+示例+第四维默认关+预警线 80%
              （api_v2_tasks._WARN_PCT 同域）；
  版本信息   = 代码常量单源 import（server.Handler.server_version /
              ledger.schemas.SCHEMA_VERSION / warrior.WARRIOR_VERSION /
              tools.cards 卡册版本）——不复制第二份。

四层钉：
  ①投影层  system_view——三速度/守卫档/预算默认/版本四块（+来源注）。
  ③挂载层  GET 过会话门；POST 无面（写面留位：带会话+守卫头也=404 未知
            路由——诚实反映「写面未开」）；动态口真服过 HTTP 各一例。
  ④页面层  static/pages/system.html——四读块+写面留位卡（W7 权限门后开）
            +四态+nav.push 自注册+零 CDN。
"""
import json
import os
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402  (同款先例：cli/ 上 path)

sys.path.insert(0, CLI)
from ledger import schemas as schemas_mod            # noqa: E402
from tools import cards as tool_cards                # noqa: E402
from warrior import WARRIOR_VERSION                  # noqa: E402
from webui import api_v2_system as api               # noqa: E402
from webui import server as srv_mod                  # noqa: E402


class TestSystemProjection(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.ledger = os.path.join(self.td.name, "G-bare")
        os.makedirs(self.ledger, exist_ok=True)
        self.battles = os.path.join(self.td.name, "battles")
        os.makedirs(self.battles, exist_ok=True)

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles)
        kw.setdefault("ledger_dir", self.ledger)
        return api.system_view(**kw)

    def test_gates_three_speeds(self):
        g = self.view()["gates"]
        self.assertEqual([s["id"] for s in g], ["fast", "pre", "strict"])
        by = {s["id"]: s for s in g}
        self.assertEqual(by["fast"]["name"], "疾速档")
        self.assertIn("只读", by["fast"]["rule"])
        self.assertIn("零审批", by["fast"]["decision"])
        self.assertIn("批一次放一族", by["pre"]["rule"])
        self.assertIn("出界即停", by["pre"]["rule"])
        self.assertIn("人工", by["strict"]["decision"])

    def test_gates_plain_language(self):
        flat = json.dumps(self.view()["gates"], ensure_ascii=False)
        for bad in ("开战", "战士", "九门"):
            self.assertNotIn(bad, flat)                     # 宪法#41
        self.assertIn("gates-speed-v1.md", flat)            # 来源注=设计档单源

    def test_guard_tiers(self):
        t = self.view()["tiers"]
        self.assertEqual(t["model_tier"]["enum"], ["strong", "weak"])
        self.assertEqual(t["model_tier"]["zh"], {"strong": "完整", "weak": "仅取证"})
        self.assertEqual(t["guard_tier"]["enum"], ["T1", "T2", "T3"])

    def test_budget_defaults(self):
        b = self.view()["budget_defaults"]
        self.assertEqual(b["triple_format"], "token;requests;hours")
        self.assertEqual(b["example"], "2M;50000;40")       # contracts/01 示例
        self.assertIn("默认关", b["dollar_dimension"])       # 第四维默认关
        self.assertEqual(b["warn_line_pct"], 80)            # 预算预警线 80%

    def test_versions_single_source(self):
        v = self.view()["versions"]
        self.assertEqual(v["server"], srv_mod.Handler.server_version)
        self.assertEqual(v["ledger_schema"], schemas_mod.SCHEMA_VERSION)
        self.assertEqual(v["warrior"], WARRIOR_VERSION)
        self.assertEqual(v["tool_cards"],
                         "/".join(sorted({c.version
                                          for c in tool_cards.all_cards()})))
        # 单源=投影从注册表派生（多批次卡版本并集，W3 f22 两批共存）

    def test_write_face_reserved(self):
        w = self.view()["write"]
        self.assertEqual(w["status"], "reserved")           # 写面=留位不开
        self.assertIn("W7", w["gate"])
        self.assertIn("只读", w["note"])

    def test_readonly_deterministic_no_battle_source(self):
        a = self.view()
        b = self.view()
        self.assertEqual(a, b)                              # 读面全局：零任务态
        self.assertNotIn("battle", a)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_readonly_zero_writes(self):
        before = {}
        for base, _d, files in os.walk(self.td.name):
            for n in files:
                p = os.path.join(base, n)
                with open(p, "rb") as f:
                    before[p] = f.read()
        self.view()
        after = {}
        for base, _d, files in os.walk(self.td.name):
            for n in files:
                p = os.path.join(base, n)
                with open(p, "rb") as f:
                    after[p] = f.read()
        self.assertEqual(before, after)                     # 零写入（含零新文件）


# ═══════════════════════════════ ③ 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 落地中）：GET 过会话门分发 ROUTES；
    POST 不拦——写面留位（基面 /api/v2/ 未知写路由=404 如实）。"""

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
    """动态口真服（禁碰 8900）：会话门+读一例+写面留位（POST=404 未知路由）。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.gd = os.path.join(cls.td.name, "G-live")
        os.makedirs(cls.gd, exist_ok=True)
        from tests import webui_login
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=cls.gd,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=os.path.join(cls.td.name, "battles"))
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

    def _req(self, method, path, cookie=True, xhr=True, body=None):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        hdrs = {}
        if cookie:
            hdrs.update(webui_login.cookie(self.sid))
        if xhr:
            hdrs["X-Requested-With"] = "XMLHttpRequest"
        if body is not None:
            hdrs["Content-Type"] = "application/json"
            body = json.dumps(body).encode("utf-8")
        conn.request(method, path, body=body, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._req("GET", "/api/v2/system.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_get_over_http(self):
        conn, resp = self._req("GET", "/api/v2/system.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["gates"]), 3)
        conn.close()

    def test_write_face_not_open_over_http(self):
        """写面留位：POST（过守卫）也=404 未知路由——如实反映「写面未开」。"""
        conn, resp = self._req("POST", "/api/v2/system.json",
                               body={"action": "set-gate"})
        self.assertEqual(resp.status, 404)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertIn("未知路由", p["error"])
        conn.close()

    def test_no_post_surface(self):
        self.assertEqual(api.POST_ROUTES, {})                # 只读+留位：零写路由


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "system.html")
ZONE_MARKS = (
    # 读面四块（门禁三速度/守卫档/预算默认/版本信息）
    'id="sy-gates"', "疾速档", "预授权档", "严审档",
    'id="sy-tiers"', 'id="sy-budget"', 'id="sy-version"',
    # 写面留位（W7 权限门后开）
    'id="sy-write"', "W7", "权限门",
    # 四态
    'id="st-loading"', 'id="st-error"', 'id="btn-retry"', 'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/system.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场", "战士", "开战")


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

    def test_write_placeholder_disabled(self):
        src = self._src()
        self.assertIn("写面预留", src)                        # 留位卡明示
        self.assertIn("disabled", src)                       # 控件禁用态
        self.assertIn("后开放", src)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'system'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_readonly_page_no_post(self):
        src = self._src()
        self.assertNotIn("method: 'POST'", src)              # 只读页零 POST
        self.assertNotIn("method=\"POST\"", src)

    def test_js_under_2000_lines_page_over_200(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 200, "系统配置页量纲")


if __name__ == "__main__":
    unittest.main()
