# -*- coding: utf-8 -*-
"""T7·设置页钉测（界面线施工计划 2026-10-18 续程③：账本参数读写面）。

python3 -m unittest tests.test_webui_pagespec_settings
律：投影只读零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN；写路径=窄门
subprocess 调既有 tanyin-ledger amend-scope（唯一写入路径，与 server._run_cli
同法——本模块不自己写表）。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18 + A 舰 B62 落法
「设置页=账本参数的读写面（amendment 语义，改动=行+因）」；文案宪法#41。

数据单源：goals.tsv（档位/预算三元组/速率窗/语言——读面）+ scope.tsv（范围
参数，修订链 amendment_of 后行覆盖先行）+ approvals.tsv（豁免与 P0 后审批）
+ timeline（amend-scope 修订史+P0 后判定）。

三层钉：
  ①投影层  settings_view——参数读面+范围行修订链+豁免清单+修订史+P0 后旗标。
  ②写路径  settings_apply——amendment 带因（note 空=422）；kind 枚举；P0 后
           须 approval；窄门 CLI 落账（真 CLI 集成 1 例：修订行真入表）。
  ③挂载层  GET 过会话门；POST 过会话门+CSRF 双检（X-Requested-With）；
           动态口真服过 HTTP 读写各一例。
  ④页面层  static/pages/settings.html——参数卡+修订表单(行+因)+修订史+四态
           +nav.push 自注册+零 CDN。
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
from webui import api_v2_settings as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def goal_row():
    """goals 行（19 列，core.TABLES 序）：档位 strong/T2+预算三元组+速率窗。"""
    return ("G-r2\trange.example.com\t全量测试\tauth.pdf\t" + "a" * 64 +
            "\t签名官\t2026-10-01T00:00:00Z\t2026-10-31T00:00:00Z\t"
            "600/10m\t08:00-20:00\t值班人\t100000;5000;40\t0\tzh\t"
            "业务背景\tstrong\tT2\t1\t2026-10-01T00:00:00Z")


def build_fixture(root):
    """battle-1=P0 未过（修订免审批）；battle-2=P2 已过（修订须审批）。"""
    b1 = os.path.join(root, "battle-1", "G-r2")
    _write(os.path.join(b1, "goals.tsv"), [goal_row()])
    _write(os.path.join(b1, "scope.tsv"), [
        "S-1\tinclude\t*.example.com\t\t\t\t范围基线\t1\t2026-10-01T00:00:00Z",
        "S-2\texclude\told.example.com\t\t\tS-1\t下线域名移出范围\t1\t2026-10-02T00:00:00Z",
    ])
    _write(os.path.join(b1, "timeline.tsv"), [
        "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r2\t\t\t\t1",
        "2026-10-02T00:00:00Z\tCLI\tP0\tamend-scope S-2->S-1\t\t\t\t1",
    ])
    _write(os.path.join(b1, "approvals.tsv"), [
        "AP-1\t1111\texempted\t操作员\t2026-10-02T01:00:00Z\t历史豁免（夹具）\t1",
        "AP-2\t2222\tapproved\t操作员\t2026-10-02T02:00:00Z\t范围修订批准（夹具）\t1",
    ])
    _write(os.path.join(b1, "budget.tsv"), [
        "2026-10-01T01:00:00Z\t1000\t10\t0\t0\troot\t起步\t1",
        "2026-10-01T02:00:00Z\t500\t5\t0\t0\troot\t续跑\t1",
    ])
    b2 = os.path.join(root, "battle-2", "G-r3")
    _write(os.path.join(b2, "goals.tsv"), [goal_row().replace("G-r2", "G-r3")])
    _write(os.path.join(b2, "scope.tsv"), [
        "S-1\tinclude\t*.example.com\t\t\t\t范围基线\t1\t2026-10-01T00:00:00Z",
    ])
    _write(os.path.join(b2, "timeline.tsv"), [
        "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r3\t\t\t\t1",
        "2026-10-01T01:00:00Z\tCLI\tP2\tadd-intent INT-1\t\t\t\t1",
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
        self.ledger = os.path.join(self.td.name, "G-bare")
        os.makedirs(self.ledger, exist_ok=True)

    def view(self, **kw):
        kw.setdefault("battles_dir", self.root)
        kw.setdefault("ledger_dir", self.ledger)
        return api.settings_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestSettingsProjection(Base):
    def test_params_read_face(self):
        p = self.view(battle=1)
        pr = p["params"]
        self.assertEqual(pr["model_tier"], "strong")
        self.assertEqual(pr["model_tier_zh"], "强")
        self.assertEqual(pr["guard_tier"], "T2")
        self.assertEqual(pr["budget"], "100000;5000;40")
        self.assertEqual(pr["budget_limits"], {"tokens": 100000, "requests": 5000,
                                               "hours": 40})
        self.assertEqual(pr["rate_limit"], "600/10m")
        self.assertEqual(pr["window"], "08:00-20:00")
        self.assertEqual(pr["language"], "zh")

    def test_budget_used(self):
        p = self.view(battle=1)
        self.assertEqual(p["budget"]["used"]["tokens"], 1500)
        self.assertEqual(p["budget"]["used"]["requests"], 15)

    def test_scope_amendment_chain(self):
        p = self.view(battle=1)
        rows = {r["id"]: r for r in p["scope"]}
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows["S-1"]["superseded"])       # 被 S-2 修订覆盖
        self.assertFalse(rows["S-2"]["superseded"])
        self.assertEqual(rows["S-2"]["amendment_of"], "S-1")
        self.assertEqual(rows["S-2"]["note"], "下线域名移出范围")
        self.assertEqual(p["counts"]["scope_heads"], 1)  # 生效行=链头

    def test_exemptions_listed(self):
        p = self.view(battle=1)
        self.assertEqual([e["id"] for e in p["exemptions"]], ["AP-1"])

    def test_amendment_history(self):
        p = self.view(battle=1)
        self.assertEqual(len(p["amendment_history"]), 1)
        self.assertIn("amend-scope S-2->S-1", p["amendment_history"][0]["event"])

    def test_p0_over_flag(self):
        self.assertEqual(self.view(battle=1)["p0_over"], False)
        self.assertEqual(self.view(battle=2)["p0_over"], True)

    def test_writable_manifest(self):
        p = self.view(battle=1)
        self.assertEqual(p["writable"]["action"], "amend-scope")
        self.assertIn("note", p["writable"]["requires"])
        self.assertIn("include", p["writable"]["kinds"])

    def test_bad_battle_valueerror(self):
        with self.assertRaises(ValueError):
            self.view(battle="x")

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view(battle=1)
        b = self.view(battle=1)
        self.assertEqual(dir_bytes(self.td.name), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)


# ═══════════════════════════════ ② 写路径 ═══════════════════════════════

class FakeRunner(object):
    """假窄门：记录 argv，回 preset 回执（returncode/stdout 形同 subprocess）。"""

    def __init__(self, returncode=0, out="OK\tS-3(修订行)\tamendment_of=S-1"):
        self.returncode = returncode
        self.stdout = out
        self.stderr = ""
        self.argv = None

    def __call__(self, argv, env=None):
        self.argv = argv
        return self


class TestSettingsApply(Base):
    def gd(self, battle=1):
        return os.path.join(self.root, "battle-%d" % battle,
                            "G-r2" if battle == 1 else "G-r3")

    def test_amendment_requires_reason(self):
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-1", "kind": "exclude",
             "matcher": "old.example.com", "note": "  "}, self.gd())
        self.assertEqual(st, 422)
        self.assertIn("带因", p["error"])                 # 因空=拒（账本同律）

    def test_amendment_validates_fields(self):
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-1", "kind": "hack",
             "matcher": "x", "note": "因"}, self.gd())
        self.assertEqual(st, 422)
        st2, p2 = api.settings_apply(
            {"action": "set-model-tier"}, self.gd())      # 档位无修订命令=拒
        self.assertEqual(st2, 422)
        self.assertIn("只支持", p2["error"])

    def test_p0_over_requires_approval(self):
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-1", "kind": "exclude",
             "matcher": "x.example.com", "note": "因"}, self.gd(battle=2))
        self.assertEqual(st, 422)
        self.assertIn("审批", p["error"])

    def test_amendment_happy_path_cli_args(self):
        fake = FakeRunner()
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-1", "kind": "exclude",
             "matcher": "old.example.com", "note": "下线域名",
             "timestamp": "2026-10-05T00:00:00Z"}, self.gd(), runner=fake)
        self.assertEqual(st, 200)
        self.assertTrue(p["ok"])
        self.assertEqual(p["receipt"]["id"], "S-3(修订行)")
        argv = " ".join(fake.argv)
        self.assertIn("amend-scope", argv)
        self.assertIn("--amendment-of=S-1", argv)
        self.assertIn("--note=下线域名", argv)
        self.assertIn("--timestamp=2026-10-05T00:00:00Z", argv)

    def test_amendment_cli_reject_maps_422(self):
        fake = FakeRunner(returncode=1, out="FAIL kind 不在四值枚举")
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-1", "kind": "include",
             "matcher": "*.x.com", "note": "因"}, self.gd(), runner=fake)
        self.assertEqual(st, 422)
        self.assertFalse(p["ok"])

    def test_real_cli_lands_amendment_row(self):
        """真窄门集成：tanyin-ledger amend-scope 真落修订行+入链。"""
        gd = self.gd(battle=1)
        st, p = api.settings_apply(
            {"action": "amend-scope", "amendment_of": "S-2", "kind": "include",
             "matcher": "new.example.com", "note": "扩域（集成测试）",
             "timestamp": "2026-10-05T00:00:00Z"}, gd)
        self.assertEqual(st, 200)
        self.assertTrue(p["ok"], p)
        with open(os.path.join(gd, "scope.tsv"), encoding="utf-8") as f:
            scope = f.read()
        self.assertIn("new.example.com", scope)          # 修订行真入表
        self.assertIn("\tS-2\t扩域（集成测试）", scope)   # amendment_of=S-2 挂链
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("amend-scope", tl)                 # 修订史入链
        self.assertIn("->S-2", tl)


# ═══════════════════════════════ ③ 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 未落地）：GET 过会话门分发 ROUTES；
    POST 过会话门+CSRF 双检（_guard_csrf）后分发 POST_ROUTES。"""

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

    def do_POST(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.POST_ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——写面须操作员会话"})
            if not self._guard_csrf():
                return                                   # 守卫已回 403 JSON
            body = self._read_json()
            if body is None:
                return self._fail(400, {"error": "请求体须 JSON"})
            status, payload = api.dispatch_post(u.path, body,
                                                ledger_dir=self.server.ledger_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_POST()


class TestV2MountContract(unittest.TestCase):
    """动态口真服（禁碰 8900）：会话门+CSRF+读一例+写一例（真 CLI 落账）。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.gd = os.path.join(cls.td.name, "G-live")   # 主账本=可写目标
        _write(os.path.join(cls.gd, "goals.tsv"), [goal_row()])
        _write(os.path.join(cls.gd, "scope.tsv"), [
            "S-1\tinclude\t*.example.com\t\t\t\t范围基线\t1\t2026-10-01T00:00:00Z",
        ])
        _write(os.path.join(cls.gd, "timeline.tsv"), [
            "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r2\t\t\t\t1",
        ])
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

    def _req(self, method, path, body=None, cookie=True, xhr=True):
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
        conn, resp = self._req("GET", "/api/v2/settings.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()
        conn2, resp2 = self._req("POST", "/api/v2/settings.json", body={}, cookie=False)
        self.assertEqual(resp2.status, 401)
        conn2.close()

    def test_post_csrf_guard(self):
        conn, resp = self._req("POST", "/api/v2/settings.json",
                               body={"action": "amend-scope"}, xhr=False)
        self.assertEqual(resp.status, 403)                # 缺自定义头=CSRF 拒
        conn.close()

    def test_get_settings_over_http(self):
        conn, resp = self._req("GET", "/api/v2/settings.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["params"]["model_tier"], "strong")
        conn.close()

    def test_post_amendment_over_http(self):
        conn, resp = self._req("POST", "/api/v2/settings.json", body={
            "action": "amend-scope", "amendment_of": "S-1", "kind": "exclude",
            "matcher": "old.example.com", "note": "HTTP 修订（带因）",
            "timestamp": "2026-10-06T00:00:00Z"})
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(p["ok"], p)
        conn.close()
        with open(os.path.join(self.gd, "scope.tsv"), encoding="utf-8") as f:
            self.assertIn("old.example.com", f.read())

    def test_post_without_reason_422(self):
        conn, resp = self._req("POST", "/api/v2/settings.json", body={
            "action": "amend-scope", "amendment_of": "S-1", "kind": "exclude",
            "matcher": "x.example.com", "note": ""})
        self.assertEqual(resp.status, 422)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertIn("带因", p["error"])
        conn.close()


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "settings.html")
ZONE_MARKS = (
    # 参数读面（档位/护栏档/预算/速率窗/语言）
    'id="st-params"', "档位", "预算", "速率窗", "语言",
    # 修订面（行+因）
    'id="st-form"', 'id="f-amendment-of"', 'id="f-kind"', 'id="f-matcher"',
    'id="f-note"', "修订必须带因",
    # 修订链+修订史+豁免
    'id="st-scope"', 'id="st-history"', 'id="st-exempt"',
    # 四态
    'id="st-loading"', 'id="st-error"', 'id="btn-retry"', 'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/settings.json",)
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
        self.assertIn("id: 'settings'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 230, "设置页量纲")


if __name__ == "__main__":
    unittest.main()
