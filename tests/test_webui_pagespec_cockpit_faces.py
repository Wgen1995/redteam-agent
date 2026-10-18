# -*- coding: utf-8 -*-
"""驾驶舱舰（功能27）——六面页钉+挂载+词表门（红转绿先测）。

python3 -m unittest tests.test_webui_pagespec_cockpit_faces
律：真服动态口（禁碰 8900）、生产 Handler 直测、前端零框架零 CDN、
页面 <2000 行；每页头部注释写「五秒三问」答案（宪法63律）；屏上词
全过 scripts/vocab_lint（宪法62律，0 黑话才算完）。

三层钉：
  ①挂载层  生产 server（api_pages._OPTIONAL_MODULES 通道）——缺会话
           401、带会话 200、未知路由 404、四路由全挂；
  ②页面层  六面结构钉——首页(四问)/任务(会话流+六签)/漏洞(证据袋+
           上次验真+待复验位)/知识库(打法卡+哨兵+蒸馏草稿)/收件箱
           (审批+求助+批量聚合)/设置(既有页入顶导航)；
  ③词表门  scripts/vocab_lint.py 退出码 0（全站 0 黑话才算完）。
"""
import os
import subprocess
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
CLI = os.path.join(REPO, "cli")
DEMO1 = os.path.join(REPO, "demos", "DEMO-1")
sys.path.insert(0, CLI)

from webui import api_pages                     # noqa: E402
from webui import server as srv_mod             # noqa: E402
from tests import webui_login                   # noqa: E402

PAGES = os.path.join(CLI, "webui", "static", "pages")
INDEX = os.path.join(CLI, "webui", "static", "index.html")
APPJS = os.path.join(CLI, "webui", "static", "app.js")

FIVE_SEC_MARK = "五秒三问"       # 每页头部注释必写（63律）


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestMountContract(unittest.TestCase):
    """生产 Handler 直测（动态口）：四路由全挂+会话门。"""

    @classmethod
    def setUpClass(cls):
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), srv_mod.Handler,
                                     ledger_dir=DEMO1,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir="")
        cls.port = cls.srv.server_address[1]
        t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        t.start()
        cls.sid = webui_login.login(cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stopping = True
        cls.srv.shutdown()
        cls.srv.server_close()

    def _get(self, path, cookie=True):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp, body

    def test_routes_registered_in_page_table(self):
        routes = api_pages.mounted_v2_routes()
        for r in ("/api/v2/cockpit.json", "/api/v2/cockpit-findings.json",
                  "/api/v2/cockpit-knowledge.json", "/api/v2/cockpit-inbox.json"):
            self.assertEqual(routes.get(r), "api_v2_cockpit", r)

    def test_cockpit_json_needs_session(self):
        resp, body = self._get("/api/v2/cockpit.json", cookie=False)
        self.assertEqual(resp.status, 401)

    def test_four_routes_200_with_session(self):
        import json
        for path, probe in (
                ("/api/v2/cockpit.json", "q1_vulns"),
                ("/api/v2/cockpit-findings.json", "items"),
                ("/api/v2/cockpit-knowledge.json", "sentinels"),
                ("/api/v2/cockpit-inbox.json", "pending_approvals")):
            resp, body = self._get(path)
            self.assertEqual(resp.status, 200, path)
            self.assertIn(probe, json.loads(body.decode("utf-8")))

    def test_unknown_v2_route_404(self):
        resp, _ = self._get("/api/v2/cockpit-nope")
        self.assertEqual(resp.status, 404)

    def test_index_home_served_with_four_questions(self):
        resp, body = self._get("/")
        self.assertEqual(resp.status, 200)
        self.assertIn("q1", body.decode("utf-8"))


class TestSixFacesStructure(unittest.TestCase):
    """六面结构钉：五秒三问注释+四问/六签/证据袋/词表锚+共享壳。"""

    def test_index_four_questions_and_five_sec(self):
        html = _read(INDEX)
        self.assertIn(FIVE_SEC_MARK, html)
        for anchor in ("id=\"q1\"", "id=\"q2\"", "id=\"q3\"",
                       "id=\"q4\""):
            self.assertIn(anchor, html)
        self.assertIn("/api/v2/cockpit.json", html)
        self.assertIn("/static/app.js", html)
        self.assertIn("/p/tasks", html)          # 深页目录不断链

    def test_mission_session_flow_and_six_tabs(self):
        html = _read(os.path.join(PAGES, "mission.html"))
        self.assertIn(FIVE_SEC_MARK, html)
        self.assertIn("id=\"flow\"", html)               # 会话流=一等对象
        for tab in ("概况", "地图", "活池", "漏洞", "消费", "日志"):
            self.assertIn(tab, html)
        self.assertIn("/api/v2/tasks.json", html)
        self.assertIn("/static/app.js", html)
        self.assertIn("nav.push", html)

    def test_findings_evidence_bag_and_retest_slot(self):
        html = _read(os.path.join(PAGES, "findings.html"))
        self.assertIn(FIVE_SEC_MARK, html)
        self.assertIn("证据袋", html)
        self.assertIn("上次验真", html)
        self.assertIn("待复验", html)
        self.assertIn("/api/v2/cockpit-findings.json", html)
        self.assertIn("/static/app.js", html)
        self.assertIn("nav.push", html)

    def test_knowledge_three_sections(self):
        html = _read(os.path.join(PAGES, "knowledge.html"))
        self.assertIn(FIVE_SEC_MARK, html)
        for sec in ("打法卡", "哨兵规则", "蒸馏"):
            self.assertIn(sec, html)
        self.assertIn("/api/v2/cockpit-knowledge.json", html)
        self.assertIn("nav.push", html)

    def test_inbox_approval_ask_batch(self):
        html = _read(os.path.join(PAGES, "inbox.html"))
        self.assertIn(FIVE_SEC_MARK, html)
        for sec in ("待审批", "求助", "批量"):
            self.assertIn(sec, html)
        self.assertIn("/api/v2/cockpit-inbox.json", html)
        self.assertIn("nav.push", html)

    def test_settings_face_has_five_sec_note(self):
        html = _read(os.path.join(PAGES, "settings.html"))
        self.assertIn(FIVE_SEC_MARK, html)

    def test_appjs_six_top_nav_and_more_menu(self):
        """顶部导航六项+旧页收进「更多」不删。"""
        js = _read(APPJS)
        for label in ("首页", "任务", "漏洞", "知识库", "收件箱", "设置"):
            self.assertIn('"' + label + '"', js)
        self.assertIn("更多", js)
        # 旧页全在（收进更多，不删）
        for slug in ("tasks", "new-task", "broadcast", "retest",
                     "approval-center", "approval", "report-center",
                     "capability", "asset-registry", "assets", "coverage",
                     "techniques", "settings"):
            self.assertIn("/p/" + slug, js, slug)
        # 旧观察面页也不删
        for path in ("/console", "/metrics", "/evidence", "/activity"):
            self.assertIn('"' + path + '"', js)


class TestVocabGate(unittest.TestCase):
    """宪法62律机检门：全站 0 黑话才算完（vocab_lint=验收器）。"""

    def test_vocab_lint_zero(self):
        r = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts", "vocab_lint.py"),
             "--quiet"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
