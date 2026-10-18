# -*- coding: utf-8 -*-
"""UI-1 总装挂测——已建成未挂载界面全部并网生产冒烟（任务书 2026-10-19）。

python3 -m unittest tests.test_webui_mount_all -v
律：起真服（动态口=server_address[1]，禁碰 8900）→ 登录 → 逐页 fetch 200 +
关键 DOM 断言 + 逐 API 真数据断言；生产 Handler 直测（零子类——挂载本体即被测）。

四层钉：
  ①页路由  /p/<slug>（含兄弟页相对链接形 /p/<slug>.html）→ pages/<slug>.html；
  ②API     /api/v2/* 会话门→api_pages.api_v2_dispatch 查表→十件全挂；
  ③导航网  static/app.js（全站页网+nav.push）+ console.js NAV + index.html 总目；
  ④只读    全扫前后账本目录逐字节不变。
"""
import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core                     # noqa: E402
from ledger.norm import artifact_hashes     # noqa: E402
from webui import api_pages                 # noqa: E402
from webui import server as srv_mod         # noqa: E402
from tests import webui_login               # noqa: E402

T = core.TABLES
TS1, TS2, TS3, TS4 = ("2026-10-19T01:00:00Z", "2026-10-19T02:00:00Z",
                      "2026-10-19T03:00:00Z", "2026-10-19T04:00:00Z")
VEC = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"      # 经典 9.1 向量
ART1 = (b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nSet-Cookie: sid=x\r\n\r\n"
        b"<html>admin orders</html>")
ART2 = b"5 login attempts in 10s"

STABLE_PAGES = {  # slug → (标题片段, 结构 DOM 钉)
    "tasks": ("任务列表", 'id="tbl-tasks"'),
    "new-task": ("新建任务", 'id="btn-create"'),
    "finding-detail": ("漏洞详情", 'id="btn-drawer"'),
    "broadcast": ("播报", 'id="composer"'),
    "report-center": ("报告中心", 'id="binding-bar"'),
    "retest": ("复测", 'id="retest-panel"'),
    "assets": ("测试资产", 'id="as-table"'),
    "coverage": ("资产覆盖", 'id="cv-legend"'),
    "approval": ("拦截审批", 'id="ap-cards"'),
    "approval-center": ("审批中心", 'id="ac-queue"'),
    "asset-registry": ("资产库", 'id="reg-body"'),
    "techniques": ("技法库", 'id="list-sub"'),
    "settings": ("设置", 'id="exempt-body"'),
}

TEN_MODULES = ("api_v2_findings", "api_v2_broadcast", "api_v2_reports",
               "api_v2_tasks", "api_v2_assets", "api_v2_coverage",
               "api_v2_guard", "api_v2_approval_center", "api_v2_asset_registry")


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    """(ts, actor, phase, event[, revert_cmd]) → 哈希链 timeline 行。"""
    rows, prev = [], core.GENESIS
    for spec in specs:
        ts, actor, phase, event = spec[:4]
        revert = spec[4] if len(spec) > 4 else ""
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        prev = h
    return rows


def write_tsv(path, rows_):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    core.write_tsv(path, rows_)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


GOAL_KW = dict(id="G-m-0001", target="shop.example", objective="外网一期渗透测试",
               auth_doc="AUTH-1.pdf", auth_sha256="a" * 64, signer="王安全（CISO）",
               valid_from="2026-10-18T00:00:00Z", valid_until="2026-10-25T00:00:00Z",
               emergency_contact="13800000000", budget="2M;50000;40",
               business_context="凭据来源：客户提供；说明：外网一期",
               model_tier="strong", guard_tier="T3",
               schema_version="2", created=TS1)


def build_fixture(battles):
    """两仗夹具：battle-3 主战（全要素）+ battle-4 副战（跨任务面）。"""
    g3 = os.path.join(battles, "battle-3", "G-a")
    write_tsv(os.path.join(g3, "goals.tsv"), [row("goals.tsv", **GOAL_KW)])
    write_tsv(os.path.join(g3, "scope.tsv"), [
        row("scope.tsv", id="S-1", kind="include", matcher="*.example.com",
            schema_version="2", created=TS1),
        row("scope.tsv", id="S-2", kind="exclude", matcher="vpn.example.com",
            schema_version="2", created=TS1),
    ])
    write_tsv(os.path.join(g3, "assets.tsv"), [
        row("assets.tsv", id="AST-m-0001", type="endpoint",
            value="shop.example/admin", in_scope="1",
            schema_version="2", created=TS1),
        row("assets.tsv", id="AST-m-0002", type="web", value="shop.example",
            in_scope="1", schema_version="2", created=TS1),
    ])
    write_tsv(os.path.join(g3, "intents.tsv"), [
        row("intents.tsv", id="INT-m-0001", title="管理面板匿名读取", detail="P3",
            status="done", engine="glm", kind="vuln", origin="seed",
            score="1", schema_version="2", created=TS1),
    ])
    write_tsv(os.path.join(g3, "matrix.tsv"), [
        row("matrix.tsv", attack_surface="shop.example/admin", vuln_class="越权",
            state="tested", reason="EV-m-0001 已重放", intent_id="INT-m-0001",
            schema_version="2", updated=TS2),
        row("matrix.tsv", attack_surface="shop.example", vuln_class="注入",
            state="untested", reason="范围外", intent_id="INT-m-0001",
            schema_version="2", updated=TS2),
    ])
    write_tsv(os.path.join(g3, "findings.tsv"), [
        row("findings.tsv", id="FD-m-0001", intent_id="INT-m-0001",
            title="管理面板匿名可读", confidence="C1", impact="高",
            exploitation_status="verified", dedup_key="admin-anon-read",
            vuln_ref="CVE-2026-1337", scope_check="in_scope",
            description_brief="未登录可读取管理面板订单列表",
            reproducible_steps="1) GET /admin 2) 观察订单数据",
            affected_asset_id="AST-m-0001",
            evidence_ids="EV-m-0001,EV-m-0002", card_path="findings-cards/FD-m-0001.md",
            status="active", schema_version="2", created=TS2),
        row("findings.tsv", id="FD-m-0002", intent_id="INT-m-0001",
            title="登录接口无速率限制", confidence="C2", impact="中",
            exploitation_status="suspected", dedup_key="login-no-ratelimit",
            scope_check="in_scope", description_brief="连续登录尝试无频控",
            affected_asset_id="AST-m-0002", card_path="findings-cards/FD-m-0002.md",
            status="active", schema_version="2", created=TS2),
    ])
    h1r, h1n = artifact_hashes(ART1)
    h2r, h2n = artifact_hashes(ART2)
    write_tsv(os.path.join(g3, "E-index.tsv"), [
        row("E-index.tsv", id="EV-m-0001", title="管理面板响应捕获",
            source_type="capture", observed_at=TS2, network_position="internet",
            repro_command="curl -i http://shop.example/admin", repro_kind="single",
            content_hash_raw=h1r, content_hash_norm=h1n,
            artifact_path="artifacts/EV-m-0001.raw", card_path="evidence/EV-m-0001.md",
            linked_finding="FD-m-0001", raw_excerpt="HTTP 200 admin",
            schema_version="2", created=TS2),
        row("E-index.tsv", id="EV-m-0002", title="登录爆破计数",
            source_type="command", observed_at=TS3, network_position="internet",
            repro_command="curl -X POST http://shop.example/login --data u=x",
            repro_kind="single", content_hash_raw=h2r, content_hash_norm=h2n,
            artifact_path="artifacts/EV-m-0002.raw", card_path="evidence/EV-m-0002.md",
            linked_finding="FD-m-0001", raw_excerpt="5 attempts",
            schema_version="2", created=TS3),
    ])
    write_tsv(os.path.join(g3, "approvals.tsv"), [
        row("approvals.tsv", id="AP-1", command_hash="b" * 64,
            decision="approved", approver="操作员", timestamp=TS3,
            note="已放行", schema_version="2"),
    ])
    write_tsv(os.path.join(g3, "timeline.tsv"), chained_tl([
        (TS1, "CLI", "P0", "add-goal G-m-0001"),
        (TS1, "CLI", "P1", "add-asset AST-m-0001"),
        (TS2, "CLI", "P3", "add-finding FD-m-0001"),
        (TS2, "CLI", "P2", "add-evidence EV-m-0001"),
        (TS2, "操作员", "P3", "battle-say 对齐目标范围 len=12"),
        (TS3, "CLI", "P3", "tools-reject sqlmap --level=3 approval-required marker=x1",
         "rm /tmp/marker-x1"),
        (TS3, "CLI", "P2", "guard-reject nmap 10.0.0.5 范围外"),
        (TS3, "hook", "P2", "hook-block curl oob.canary"),
        (TS3, "egress", "P2", "egress-deny curl http://oob.example"),
        (TS4, "CLI", "P4", "replay-probe EV-m-0001 verdict=reproduced"),
    ]))
    for ev, data in (("EV-m-0001", ART1), ("EV-m-0002", ART2)):
        p = os.path.join(g3, "artifacts", ev + ".raw")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
    _write(os.path.join(g3, "findings-cards", "FD-m-0001.md"),
           "---\nid: FD-m-0001\ndedup_key: admin-anon-read\nscope_check: in_scope\n"
           "exploitation_status: verified\nconfidence: C1\nimpact: 高\nauth_context: \n"
           "evidence_ids: [EV-m-0001, EV-m-0002]\ncontrol_evidence_ids: []\n"
           "affected_asset_id: AST-m-0001\npair_group: \n"
           "cvss_vector: '" + VEC + "'\n---\n"
           "## 漏洞叙述\n管理面板路由缺会话校验中间件，匿名请求直达订单数据接口。\n"
           "## 复现步骤\n引用 EV-m-0001 卡片四要素。\n"
           "## 修复建议叙述\n根因: admin 路由未挂会话校验中间件\n"
           "代码位: routes/admin.py:42\n修复后验证: curl -i http://shop.example/admin 应 302\n")
    _write(os.path.join(g3, "findings-cards", "FD-m-0002.md"),
           "---\nid: FD-m-0002\ndedup_key: login-no-ratelimit\n---\n"
           "## 漏洞叙述\n（待 LLM 撰写）\n## 复现步骤\n（引用 EV 卡片）\n")
    _write(os.path.join(g3, "evidence", "EV-m-0001.md"),
           "---\nid: EV-m-0001\ntitle: 管理面板响应捕获\nsource_type: capture\n"
           "observed_at: " + TS2 + "\nnetwork_position: internet\npreconditions: []\n"
           "raw_request: |\n  GET /admin HTTP/1.1\n  Host: shop.example\n  \n"
           "---\nGET 响应捕获 200，Set-Cookie sid=x。\n")

    g4 = os.path.join(battles, "battle-4", "G-a")
    write_tsv(os.path.join(g4, "goals.tsv"),
              [row("goals.tsv", **dict(GOAL_KW, id="G-m-0002",
                                       target="api.example", objective="API 一期"))])
    write_tsv(os.path.join(g4, "findings.tsv"), [
        row("findings.tsv", id="FD-m2-0001", intent_id="INT-m2-0001",
            title="Swagger 文档未鉴权", confidence="C1", impact="低",
            exploitation_status="verified", dedup_key="swagger-open",
            scope_check="in_scope", description_brief="api-docs 匿名可读",
            affected_asset_id="AST-m2-0001", card_path="",
            status="active", schema_version="2", created=TS2),
    ])
    write_tsv(os.path.join(g4, "timeline.tsv"), chained_tl([
        (TS1, "CLI", "P0", "add-goal G-m-0002"),
        (TS3, "CLI", "P3", "add-finding FD-m2-0001"),
        (TS3, "CLI", "P3", "tools-reject hydra -L dict.txt approval-required marker=y2",
         "rm /tmp/marker-y2"),
    ]))
    return g3


class MountBase(unittest.TestCase):
    """生产 Handler 直测（零子类）——动态口，禁碰 8900。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="webui-mount-")
        cls.battles = os.path.join(cls.tmp, "battles")
        cls.gd = build_fixture(cls.battles)
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), srv_mod.Handler,
                                    ledger_dir=cls.gd,
                                    operator_key=webui_login.OP_KEY,
                                    battles_dir=cls.battles)
        cls.port = cls.srv.server_address[1]
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()
        cls.sid = webui_login.login(cls.port)
        cls._snapshot = cls._dir_state()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stopping = True
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def _dir_state(cls):
        state = []
        for root, _dirs, files in os.walk(cls.battles):
            for name in sorted(files):
                p = os.path.join(root, name)
                with open(p, "rb") as f:
                    state.append((os.path.relpath(p, cls.battles), f.read()))
        return state

    def _get(self, path, cookie=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp, body

    def _json(self, path):
        resp, body = self._get(path)
        return resp.status, json.loads(body.decode("utf-8"))


# ═══════════════════════════ ① 页路由（/p/<slug>） ═══════════════════════════

class TestPagesMounted(MountBase):

    def test_stable_pages_served_with_dom(self):
        for slug, (title_frag, dom) in sorted(STABLE_PAGES.items()):
            with self.subTest(slug=slug):
                resp, body = self._get("/p/" + slug)
                self.assertEqual(resp.status, 200, slug)
                html = body.decode("utf-8")
                self.assertIn(title_frag, html)
                self.assertIn(dom, html)
                self.assertIn("/static/app.js", html)   # 共享壳已消费

    def test_sibling_relative_alias_served(self):
        """兄弟页相对链接形（finding-detail.html）与裸名同件同字节。"""
        resp_a, body_a = self._get("/p/tasks")
        resp_b, body_b = self._get("/p/tasks.html")
        self.assertEqual(resp_a.status, 200)
        self.assertEqual(resp_b.status, 200)
        self.assertEqual(body_a, body_b)

    def test_every_disk_page_reachable(self):
        """盘上 pages/*.html 全量 200（未来舰页落盘即自动并网）。"""
        slugs = api_pages.page_slugs()
        self.assertGreaterEqual(len(slugs), len(STABLE_PAGES))
        for slug in slugs:
            with self.subTest(slug=slug):
                resp, _ = self._get("/p/" + slug)
                self.assertEqual(resp.status, 200, slug)

    def test_unknown_page_404(self):
        resp, body = self._get("/p/nope")
        self.assertEqual(resp.status, 404)
        self.assertIn("页面不存在", body.decode("utf-8"))

    def test_bad_slug_404(self):
        for bad in ("/p/Bad_Name", "/p/..%2Flogin", "/p/tasks.html.html"):
            with self.subTest(bad=bad):
                resp, _ = self._get(bad)
                self.assertEqual(resp.status, 404, bad)

    def test_unauth_page_redirects_login(self):
        resp, _ = self._get("/p/tasks", cookie=False)
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.getheader("Location"), "/login")

    def test_shell_appjs_served(self):
        resp, body = self._get("/static/app.js")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/javascript"))
        js = body.decode("utf-8")
        self.assertIn("nav.push", js)            # 自注册面在
        self.assertIn("/p/tasks", js)            # 页网已织
        self.assertIn("__plkCtl", js)            # 裸⌘K 让位命令面板（96e10b93 裁）

    def test_pages_js_asset_allowlist(self):
        """页级共享 JS（命令面板 _palette.js）放行：在盘 200，越界/缺席 404。"""
        if os.path.isfile(os.path.join(srv_mod.STATIC_DIR, "pages",
                                       "_palette.js")):
            resp, body = self._get("/static/pages/_palette.js")
            self.assertEqual(resp.status, 200)
            self.assertIn("__plkCtl", body.decode("utf-8"))
        for bad in ("/static/pages/nope.js", "/static/pages/../app.js",
                    "/static/pages/tasks.html", "/static/pages/.js"):
            with self.subTest(bad=bad):
                resp, _ = self._get(bad)
                self.assertEqual(resp.status, 404, bad)

    def test_pages_js_asset_gated(self):
        resp, _ = self._get("/static/pages/_palette.js", cookie=False)
        self.assertEqual(resp.status, 401)


# ═══════════════════════ ② /api/v2/* 统一分发（十件全挂） ═══════════════════════

class TestApiV2Mounted(MountBase):

    def test_unauth_api_401_json(self):
        resp, body = self._get("/api/v2/tasks.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(body.decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")

    def test_unknown_v2_404(self):
        resp, body = self._get("/api/v2/nope")
        self.assertEqual(resp.status, 404)
        self.assertIn("未知路由", body.decode("utf-8"))

    def test_all_ten_modules_mounted(self):
        routes = api_pages.mounted_v2_routes()
        mods = set(routes.values())
        for m in TEN_MODULES:
            self.assertIn(m, mods, m)

    def test_tasks_real_data(self):
        status, p = self._json("/api/v2/tasks.json")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(p["counts"]["battles"], 2)
        self.assertIn("battle-3", json.dumps(p))

    def test_broadcast_real_data(self):
        status, p = self._json("/api/v2/broadcast.json?battle=3")
        self.assertEqual(status, 200)
        kinds = [r["kind"] for r in p["rows"]]
        self.assertIn("agent", kinds)
        self.assertIn("operator", kinds)

    def test_guard_real_data(self):
        status, p = self._json("/api/v2/guard.json?battle=3")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(p["counts"]["pending"], 1)
        self.assertGreaterEqual(p["counts"]["flow"], 1)
        layers = {f["layer"] for f in p["flow"]}
        self.assertTrue(any("L1" in x or "L2" in x or "L3" in x or "L4" in x
                            for x in layers), layers)

    def test_approval_center_real_data(self):
        status, p = self._json("/api/v2/approval-center.json")
        self.assertEqual(status, 200)
        pending = json.dumps(p.get("pending", []), ensure_ascii=False)
        self.assertIn("battle-3", pending)
        self.assertIn("battle-4", pending)

    def test_assets_real_data(self):
        status, p = self._json("/api/v2/assets.json?battle=3")
        self.assertEqual(status, 200)
        self.assertIn("shop.example/admin", json.dumps(p, ensure_ascii=False))

    def test_coverage_real_data(self):
        status, p = self._json("/api/v2/coverage.json?battle=3")
        self.assertEqual(status, 200)

    def test_asset_registry_real_data(self):
        status, p = self._json("/api/v2/asset-registry.json")
        self.assertEqual(status, 200)

    def test_retest_real_data(self):
        status, p = self._json("/api/v2/retest.json?battle=3")
        self.assertEqual(status, 200)

    def test_report_list_real_data(self):
        status, p = self._json("/api/v2/report-list.json")
        self.assertEqual(status, 200)
        body = json.dumps(p, ensure_ascii=False)
        self.assertIn("battle-3", body)

    def test_new_task_meta_real_data(self):
        status, p = self._json("/api/v2/new-task-meta.json")
        self.assertEqual(status, 200)

    def test_techniques_real_data(self):
        status, p = self._json("/api/v2/techniques.json")
        self.assertEqual(status, 200)

    def test_finding_detail_real_data(self):
        status, p = self._json("/api/v2/finding-detail?id=FD-m-0001")
        self.assertEqual(status, 200)
        self.assertEqual(p["finding"]["id"], "FD-m-0001")
        self.assertEqual(p["cvss"]["score"], 9.1)

    def test_finding_detail_unknown_404(self):
        status, _ = self._json("/api/v2/finding-detail?id=FD-nope")
        self.assertEqual(status, 404)

    def test_evidence_raw_real_data(self):
        status, p = self._json("/api/v2/evidence-raw?id=EV-m-0001")
        self.assertEqual(status, 200)
        self.assertTrue(p["response"]["is_http"])

    def test_parent_batch_three_modules_mounted(self):
        """父舰收编三件（tools/llm-status/system）稳定挂载 GET 200。"""
        for path in ("/api/v2/tools.json", "/api/v2/llm-status.json",
                     "/api/v2/system.json"):
            with self.subTest(path=path):
                status, _ = self._json(path)
                self.assertEqual(status, 200, path)

    def _post(self, path, body, cookie=True, csrf=True):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = {"Content-Type": "application/json",
                "Origin": "http://127.0.0.1:%d" % self.port}
        if csrf:
            hdrs["X-Requested-With"] = "XMLHttpRequest"
        if cookie:
            hdrs.update(webui_login.cookie(self.sid))
        conn.request("POST", path, body=json.dumps(body).encode("utf-8"),
                     headers=hdrs)
        resp = conn.getresponse()
        payload = resp.read()
        conn.close()
        return resp, payload

    def test_settings_post_wire_guard(self):
        """T7 settings POST 挂载契约：会话门 401 → CSRF 403（守卫序）。"""
        resp, body = self._post("/api/v2/settings.json", {"x": 1}, cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertIn("会话", json.loads(body.decode("utf-8"))["error"])
        resp, body = self._post("/api/v2/settings.json", {"x": 1}, csrf=False)
        self.assertEqual(resp.status, 403)

    def test_settings_post_unknown_v2_post_404(self):
        resp, body = self._post("/api/v2/nope-write", {"x": 1})
        self.assertEqual(resp.status, 404)
        self.assertIn("未知路由", body.decode("utf-8"))


# ═══════════════════════════ ③ 导航网（一张网） ═══════════════════════════════

class TestNavNet(MountBase):

    def test_appjs_nav_slugs_all_on_disk(self):
        with open(os.path.join(srv_mod.STATIC_DIR, "app.js"), encoding="utf-8") as f:
            js = f.read()
        slugs = set(re.findall(r"/p/([a-z0-9-]+)", js))
        # 壳网至少织入 12 张常驻页（finding-detail 须带 ?id= 入——由页内链
        # 与 nav.push 自注册入网，不做无参死链入口）
        self.assertGreaterEqual(len(slugs), 12)
        on_disk = set(api_pages.page_slugs())
        self.assertLessEqual(slugs, on_disk)

    def test_console_nav_wired(self):
        """控制台 23 项壳的占位已接真页（test_console_ui 钉 23 项不增项）。"""
        with open(os.path.join(srv_mod.STATIC_DIR, "console.js"), encoding="utf-8") as f:
            js = f.read()
        for slug in ("new-task", "broadcast", "report-center", "techniques",
                     "settings", "coverage"):
            self.assertIn("/p/" + slug, js, slug)

    def test_index_home_directory(self):
        """驾驶舱首页（功能27 蓝图：25页砍到6面，首页=四问直答）。"""
        resp, body = self._get("/")
        self.assertEqual(resp.status, 200)
        html = body.decode("utf-8")
        self.assertIn("id=\"q1\"", html)          # 四问锚在（问一..问四）
        self.assertIn("id=\"q4\"", html)
        self.assertIn("五秒三问", html)             # 63律注释在
        self.assertIn("/p/tasks", html)             # 深页目录不断链


# ═══════════════════════════ ④ 只读铁律 ═══════════════════════════════════════

class TestReadOnly(MountBase):

    def test_full_sweep_leaves_ledger_untouched(self):
        paths = ["/p/" + s for s in api_pages.page_slugs()]
        paths += ["/api/v2/tasks.json", "/api/v2/broadcast.json?battle=3",
                  "/api/v2/guard.json?battle=3", "/api/v2/approval-center.json",
                  "/api/v2/assets.json?battle=3", "/api/v2/coverage.json?battle=3",
                  "/api/v2/asset-registry.json", "/api/v2/retest.json?battle=3",
                  "/api/v2/report-list.json", "/api/v2/new-task-meta.json",
                  "/api/v2/techniques.json",
                  "/api/v2/finding-detail?id=FD-m-0001",
                  "/api/v2/evidence-raw?id=EV-m-0001"]
        for path in paths:
            resp, _ = self._get(path)
            self.assertEqual(resp.status, 200, path)
        self.assertEqual(self._dir_state(), self._snapshot)


if __name__ == "__main__":
    unittest.main()
