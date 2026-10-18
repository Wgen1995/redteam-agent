# -*- coding: utf-8 -*-
"""T7·工具执行页钉测（界面线施工计划 2026-10-18 续程④：25 张工具卡只读面）。

python3 -m unittest tests.test_webui_pagespec_tools
律：投影只读零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN；本页无写路径
（只读+「复制调用命令」按钮——复制=页端剪贴板，零服务端写）。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18 + W3 蓝图 25 卡
（cli/tools/cards.py 单源）；文案宪法#41（界面人话律）。

数据单源：cli/tools/cards.py 注册表（25 卡：名称/用途/风险级/revert 义务）+
timeline（工具行：actor=tools 的 tool-card-exec / tools-reject——gate.execute
单源写方）。

四层钉：
  ①投影层  tools_view——卡清单（as_public_dict 稳定投影+用途/收尾义务/
            可复制调用命令）+执行历史（timeline 工具行解析，多代合并，
            新者在前，有界 200 行）+单卡详情六节（基本信息/用途/风险与
            审批/限速与拒绝/收尾义务/调用示例）。
  ③挂载层  GET 过会话门（Handler._session_ok）；动态口真服过 HTTP 一例
            （列表+详情）；无 POST 面（只读页零写路由）。
  ④页面层  static/pages/tools.html——卡表+执行历史+详情六节+复制调用命令
            钮+四态+nav.push 自注册+零 CDN。
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
from webui import api_v2_tools as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def goal_row():
    """goals 行（19 列，core.TABLES 序；settings 同款夹具）。"""
    return ("G-r2\trange.example.com\t全量测试\tauth.pdf\t" + "a" * 64 +
            "\t签名官\t2026-10-01T00:00:00Z\t2026-10-31T00:00:00Z\t"
            "600/10m\t08:00-20:00\t值班人\t100000;5000;40\t0\tzh\t"
            "业务背景\tstrong\tT2\t1\t2026-10-01T00:00:00Z")


TOOL_ROWS_R2 = [
    "2026-10-02T00:00:00Z\ttools\tP3\ttool-card-exec name=nuclei rc=0 tier=L1 rate=10/s\t\t\t\t1",
    "2026-10-02T00:01:00Z\ttools\tP3\ttool-card-exec name=sqlmap rc=0 tier=L3 rate=5/s\t输出目录 --purge 核销（--purge-output 痕迹清理义务）\t\t\t1",
    "2026-10-02T00:02:00Z\ttools\tP3\ttools-reject card=impacket unknown-tool: 'x' 不在注册表（25 卡清单外拒执行）\t\t\t\t1",
]
TOOL_ROWS_R3 = [
    "2026-10-03T00:00:00Z\ttools\tP3\ttool-card-exec name=httpx rc=0 tier=L1 rate=20/s\t\t\t\t1",
    "2026-10-03T00:05:00Z\tllmpool\tP-lifecycle\tllm_failover event=trip model=a reason=http:500 lane=server cooldown_s=60\t\t\t\t1",
]


def build_fixture(root):
    """battle-1 两代（G-r2/G-r3）——工具行跨代合并；battle-2 无工具行。"""
    b1 = os.path.join(root, "battle-1", "G-r2")
    _write(os.path.join(b1, "goals.tsv"), [goal_row()])
    _write(os.path.join(b1, "timeline.tsv"), [
        "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r2\t\t\t\t1",
    ] + TOOL_ROWS_R2)
    b1r3 = os.path.join(root, "battle-1", "G-r3")
    _write(os.path.join(b1r3, "goals.tsv"), [goal_row().replace("G-r2", "G-r3")])
    _write(os.path.join(b1r3, "timeline.tsv"), [
        "2026-10-03T00:00:00Z\tCLI\tP0\tadd-goal G-r3\t\t\t\t1",
    ] + TOOL_ROWS_R3)
    b2 = os.path.join(root, "battle-2", "G-r4")
    _write(os.path.join(b2, "goals.tsv"), [goal_row().replace("G-r2", "G-r4")])
    _write(os.path.join(b2, "timeline.tsv"), [
        "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r4\t\t\t\t1",
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
        return api.tools_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestToolsProjection(Base):
    def test_cards_count_is_25(self):
        p = self.view(battle=1)
        self.assertEqual(len(p["cards"]), 55)   # W3 25+F22 补卡 30
        self.assertEqual(p["counts"]["cards"], 55)

    def test_card_fields_present(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["cards"]}
        nuc = by["nuclei"]
        self.assertEqual(nuc["binary"], "nuclei")
        self.assertEqual(nuc["tier"], "L1")
        self.assertEqual(nuc["risk"], "medium")
        self.assertEqual(nuc["rate"], "10/s")
        self.assertEqual(nuc["category"], "vuln-scan")
        self.assertFalse(nuc["requires_approval"])
        self.assertTrue(by["sqlmap"]["requires_approval"])   # L3=审批挂卡

    def test_purpose_maps_summary(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["cards"]}
        self.assertIn("模板化漏洞扫描", by["nuclei"]["purpose"])  # 用途=summary 单源
        self.assertTrue(all(c["purpose"] for c in p["cards"]))

    def test_revert_obligation_split(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["cards"]}
        self.assertFalse(by["nuclei"]["revert_required"])    # none(只读*)=无义务
        self.assertTrue(by["sqlmap"]["revert_required"])
        self.assertTrue(by["smbclient"]["revert_required"])
        n_paid = sum(1 for c in p["cards"] if c["revert_required"])
        self.assertGreater(n_paid, 0)
        self.assertLess(n_paid, 25)

    def test_example_command_copyable(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["cards"]}
        self.assertEqual(by["nuclei"]["example_command"],
                         "nuclei -rl 10 -etags dos,intrusive "
                         "-u https://target.example")
        for c in p["cards"]:
            self.assertTrue(c["example_command"].startswith(c["binary"]))

    def test_history_exec_rows_newest_first(self):
        p = self.view(battle=1)
        h = p["history"]
        self.assertEqual(h[0]["card"], "httpx")              # 新者在前
        kinds = [r["kind"] for r in h]
        self.assertEqual(kinds.count("执行"), 3)
        sql = next(r for r in h if r["card"] == "sqlmap")
        self.assertEqual(sql["rc"], 0)
        self.assertEqual(sql["tier"], "L3")
        self.assertIn("purge", sql["revert"])

    def test_history_reject_row(self):
        p = self.view(battle=1)
        rej = next(r for r in p["history"] if r["kind"] == "拒绝")
        self.assertEqual(rej["card"], "impacket")
        self.assertIn("25 卡清单外", rej["detail"])

    def test_history_multigen_merged(self):
        p = self.view(battle=1)                              # G-r2+G-r3 合并
        cards = [r["card"] for r in p["history"]]
        self.assertIn("nuclei", cards)
        self.assertIn("httpx", cards)
        llm = [r for r in p["history"] if r["card"] == "a"]  # llmpool 行不入工具史
        self.assertEqual(llm, [])

    def test_history_bounded_200(self):
        gd = os.path.join(self.root, "battle-2", "G-r4")
        rows = ["2026-10-01T00:00:00Z\ttools\tP3\ttool-card-exec name=curl rc=0 tier=L1 rate=10/s\t\t\t\t1"]
        _write(os.path.join(gd, "timeline.tsv"),
               ["2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r4\t\t\t\t1"]
               + rows * 260)
        p = self.view(battle=2)
        self.assertLessEqual(len(p["history"]), 200)         # 有界：≤200 行
        self.assertTrue(p["history_truncated"])              # 如实标截断

    def test_history_absent_battle(self):
        p = self.view(battle=2)
        self.assertEqual(p["history"], [])
        self.assertFalse(p["history_truncated"])

    def test_detail_six_sections(self):
        p = self.view(battle=1, card="sqlmap")
        secs = p["detail"]["sections"]
        self.assertEqual([s["key"] for s in secs],
                         ["basics", "purpose", "risk", "rate", "revert", "example"])
        flat = json.dumps(secs, ensure_ascii=False)
        self.assertIn("sqlmap", flat)
        self.assertIn("SQL 注入利用", flat)                    # 用途节
        self.assertIn("critical", flat)                      # 风险节
        self.assertIn("5/s", flat)                           # 限速节
        self.assertIn("purge", flat)                         # 收尾义务节
        self.assertIn("sqlmap -u", flat)                     # 调用示例节

    def test_detail_unknown_card(self):
        p = self.view(battle=1, card="no-such-card")
        self.assertIn("error", p)
        self.assertIn("no-such-card", p["error"])

    def test_bad_battle_valueerror(self):
        with self.assertRaises(ValueError):
            self.view(battle="x")

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view(battle=1, card="sqlmap")
        b = self.view(battle=1, card="sqlmap")
        self.assertEqual(dir_bytes(self.td.name), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)


# ═══════════════════════════════ ③ 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 未落地）：GET 过会话门分发 ROUTES；
    本页零 POST 面（只读）。"""

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
    """动态口真服（禁碰 8900）：会话门+读两例（列表/详情）。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.gd = os.path.join(cls.td.name, "G-live")
        _write(os.path.join(cls.gd, "goals.tsv"), [goal_row()])
        _write(os.path.join(cls.gd, "timeline.tsv"), [
            "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r2\t\t\t\t1",
            "2026-10-02T00:00:00Z\ttools\tP3\ttool-card-exec name=nuclei rc=0 tier=L1 rate=10/s\t\t\t\t1",
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

    def _req(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._req("/api/v2/tools.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_get_tools_over_http(self):
        conn, resp = self._req("/api/v2/tools.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["cards"]), 55)   # W3 25+F22 补卡 30
        self.assertEqual(p["history"][0]["card"], "nuclei")
        conn.close()

    def test_get_card_detail_over_http(self):
        conn, resp = self._req("/api/v2/tools.json?card=sqlmap")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["detail"]["sections"]), 6)
        conn.close()

    def test_get_unknown_card_404_over_http(self):
        conn, resp = self._req("/api/v2/tools.json?card=nope")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_no_post_surface(self):
        self.assertEqual(api.POST_ROUTES, {})                # 只读页零写路由


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "tools.html")
ZONE_MARKS = (
    # 卡清单（名称/用途/风险级/revert 义务）
    'id="tl-cards"', "名称", "用途", "风险级", "revert 义务",
    # 执行历史 + 详情六节
    'id="tl-history"', 'id="tl-detail"',
    # 复制调用命令钮（只读页唯一动作）
    'id="btn-copy-cmd"', "复制调用命令",
    # 四态
    'id="st-loading"', 'id="st-error"', 'id="btn-retry"', 'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/tools.json",)
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

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'tools'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 200, "工具页量纲")


if __name__ == "__main__":
    unittest.main()
