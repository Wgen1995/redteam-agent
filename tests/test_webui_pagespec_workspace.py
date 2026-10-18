# -*- coding: utf-8 -*-
"""T7·工作区页钉测（界面线施工计划 2026-10-18 续程④：任务工件浏览+下载）。

python3 -m unittest tests.test_webui_pagespec_workspace
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18（工作区=工件浏览+下载）；
文案宪法#41（界面人话律）——「任务」上屏。

数据单源：battles/<battle-N>/ 工作区实勘（有界漫游：深度≤3、条目≤800、
超出如实截断标 truncated——不虚报全量）；工件类别=确定性后缀/位置推导
（报告 md/摘要 json/指令与结算 txt/日志 log/账本表 tsv/证据 evidence/ 代目
G-*）。下载=同路由 path 参数：路径监狱（禁 .. 与绝对路径——只出任务根）、
2MB 上限（超出=413 如实报）、b64 装载（页端组 blob 落盘）。

三层钉：
  ①投影层  workspace_view——工件清单(路径/类别/大小)+类别计数+截断旗标。
  ②下载层  ?path= 路径监狱+大小上限+真字节往返（b64 解码=原文）。
  ③挂载层  /api/v2/workspace.json 过会话门（无 cookie=401 JSON）；动态口
           真服过 HTTP 清单+下载各一例。
  ④页面层  static/pages/workspace.html——任务选择+类别过滤+工件表+下载钮
           +四态+nav.push 自注册+零 CDN。
"""
import base64
import json
import os
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from webui import api_v2_workspace as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_fixture(root):
    b1 = os.path.join(root, "battle-1")
    _write(os.path.join(b1, "directive.txt"), "指令：全量测试\n")
    _write(os.path.join(b1, "mission.txt"), "任务简报\n")
    _write(os.path.join(b1, "settle-report.txt"), "recall=0.5 hits=28 total=56\n")
    _write(os.path.join(b1, "battle-report.md"), "# 报告\n正文\n")
    _write(os.path.join(b1, "opencode-run.log"), "log line 1\nlog line 2\n")
    _write(os.path.join(b1, "G-r2", "timeline.tsv"), "r1\nr2\n")
    _write(os.path.join(b1, "G-r2", "evidence", "xss1.raw"), "<html>probe</html>\n")
    _write(os.path.join(b1, "G-r2", "evidence", "EV-0001.md"), "# EV 卡\n证据\n")
    _write(os.path.join(b1, "G-r2-summary.json"), '{"gen":"G-r2"}\n')
    b2 = os.path.join(root, "battle-2")
    _write(os.path.join(b2, "directive.txt"), "指令二\n")
    _write(os.path.join(b2, "G-r5", "timeline.tsv"), "x\n")
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
        return api.workspace_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestWorkspaceProjection(Base):
    def test_inventory_kinds(self):
        p = self.view(battle=1)
        kinds = {e["path"]: e["kind"] for e in p["entries"]}
        self.assertEqual(kinds["battle-report.md"], "报告")
        self.assertEqual(kinds["G-r2-summary.json"], "摘要")
        self.assertEqual(kinds["directive.txt"], "指令")
        self.assertEqual(kinds["settle-report.txt"], "结算")
        self.assertEqual(kinds["opencode-run.log"], "日志")
        self.assertEqual(kinds["G-r2/timeline.tsv"], "账本表")
        self.assertEqual(kinds["G-r2/evidence/xss1.raw"], "证据")
        # 目录也入清单（代目/证据目录可浏览）
        self.assertEqual(kinds["G-r2"], "代目")
        self.assertEqual(kinds["G-r2/evidence"], "证据")
        self.assertEqual(len(p["entries"]), 11)

    def test_sizes_and_counts(self):
        p = self.view(battle=1)
        by = {e["path"]: e for e in p["entries"]}
        self.assertEqual(by["battle-report.md"]["size"],
                         len("# 报告\n正文\n".encode("utf-8")))   # 大小=字节
        self.assertEqual(p["counts"]["报告"], 1)
        self.assertEqual(p["counts"]["证据"], 2)      # 只计文件（目录另计浏览）
        self.assertFalse(p["truncated"])

    def test_battle_default_latest_and_picker(self):
        p = self.view()
        self.assertEqual(p["battle"]["id"], "battle-2")   # 缺省=最新任务
        self.assertEqual(len(p["battles"]), 2)

    def test_bad_battle(self):
        with self.assertRaises(ValueError):
            self.view(battle="x")
        p = self.view(battle=99)
        self.assertIn("error", p)                          # 不存在=404 形

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view(battle=1)
        b = self.view(battle=1)
        self.assertEqual(dir_bytes(self.td.name), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)


# ═══════════════════════════════ ② 下载层 ═══════════════════════════════

class TestWorkspaceDownload(Base):
    def test_download_roundtrip(self):
        st, p = api.workspace_view(battles_dir=self.root, battle=1,
                                   path="G-r2/evidence/xss1.raw")
        self.assertEqual(st, 200)
        self.assertEqual(p["name"], "xss1.raw")
        self.assertEqual(p["mime"], "application/octet-stream")
        self.assertEqual(base64.b64decode(p["b64"]), b"<html>probe</html>\n")

    def test_download_text_mime(self):
        st, p = api.workspace_view(battles_dir=self.root, battle=1,
                                   path="battle-report.md")
        self.assertEqual(st, 200)
        self.assertTrue(p["mime"].startswith("text/markdown"))

    def test_path_jail(self):
        st, p = api.workspace_view(battles_dir=self.root, battle=1,
                                   path="../outside.txt")
        self.assertEqual(st, 422)                          # 越狱=拒
        self.assertIn("路径", p["error"])
        st2, p2 = api.workspace_view(battles_dir=self.root, battle=1,
                                     path="/etc/passwd")   # 绝对路径=拒
        self.assertEqual(st2, 422)

    def test_download_missing_file(self):
        st, p = api.workspace_view(battles_dir=self.root, battle=1,
                                   path="nope.txt")
        self.assertEqual(st, 404)

    def test_download_size_cap(self):
        big = os.path.join(self.root, "battle-1", "big.bin")
        with open(big, "wb") as f:
            f.write(b"\0" * (api.MAX_DOWNLOAD + 1))
        st, p = api.workspace_view(battles_dir=self.root, battle=1,
                                   path="big.bin")
        self.assertEqual(st, 413)
        self.assertIn("2MB", p["error"])


# ═══════════════════════════════ ③ 挂载层 ═══════════════════════════════

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
    """动态口真服（禁碰 8900）：会话门+清单/下载过 HTTP。"""

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
        conn, resp = self._get("/api/v2/workspace.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_inventory_over_http(self):
        conn, resp = self._get("/api/v2/workspace.json?battle=1")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["entries"]), 11)
        conn.close()

    def test_download_over_http(self):
        import urllib.parse
        q = urllib.parse.quote("G-r2/evidence/xss1.raw")
        conn, resp = self._get("/api/v2/workspace.json?battle=1&path=" + q)
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(base64.b64decode(p["b64"]), b"<html>probe</html>\n")
        conn.close()


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "workspace.html")
ZONE_MARKS = (
    # 顶条：任务选择 + 类别过滤 + 计数
    'id="ws-battle"', 'id="ws-kind"', 'id="ws-counts"',
    # 工件表（路径/类别/大小/下载）
    'id="ws-table"', "下载",
    # 截断披露
    "truncated",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/workspace.json",)
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
        self.assertIn("id: 'workspace'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 230, "工作区页量纲")


if __name__ == "__main__":
    unittest.main()
