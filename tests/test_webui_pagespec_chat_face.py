# -*- coding: utf-8 -*-
"""壳重排 IA v2 舰——对话第一公民四件+导航序+任务面六签吸收+只读投影（红转绿先测）。

python3 -m unittest tests.test_webui_pagespec_chat_face -v

律：真服动态口（禁碰 8900）、生产 Handler 直测（_V2MountHandler 挂法钉，
同 tests/test_command_converse.py 先例）、前端零框架零 CDN、页面 <2000 行、
只读投影零写入零墙钟（api_v2_cockpit 同律）、词表 62 律全过。

五层钉：
  ①页面层  /p/chat 对话面四件——消息流投影气泡（id=chat-log）/输入框产卡
           （propose 内联任务卡+确认跳 /p/new-task）/@引用下拉（at-search）
           /回复四分类按钮（批准/拒绝/改方向/给情报→steer-reply）；
  ②机制层  对话页机制三律（ARTEX 前端图§六.1 借通用件不借结构）——1s 尾轮询
           +key 去重+不乐观回声+渐进披露（载入更早）；
  ③导航层  七面侧栏序=对话/仪表盘/任务/漏洞/知识库/收件箱/设置（对话第一公民，
           首页降仪表盘观察面）；对话页一击达任务与漏洞（同心圆链接）；
  ④任务面  吸收十签精华六签=概况/会话流/资产/漏洞/复测/报告——已有真面保位，
           缺的签只留位（class=slot）不虚造；旧六签（地图/活池/消费/日志）不删；
  ⑤投影层  GET /api/v2/chat-log 只读投影 timeline+ask+approval 四类事件
           （command 指挥/warrior 士兵/ask 求助/approval 待审批）为对话气泡，
           零写零墙钟，同输入两跑一致；IA 锚仍钉（四问/证据袋/复验）。
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
REPO = os.path.join(HERE, "..")
CLI = os.path.join(REPO, "cli")
sys.path.insert(0, CLI)

from webui import api_pages                     # noqa: E402
from webui import server as srv_mod             # noqa: E402
from tests import webui_login                   # noqa: E402

PAGES = os.path.join(CLI, "webui", "static", "pages")
STATIC = os.path.join(CLI, "webui", "static")
FIVE_SEC_MARK = "五秒三问"

# 七面（IA v2：对话第一公民+首页降仪表盘）——侧栏序单源钉
SEVEN_FACES = ("index.html", "chat.html", "mission.html", "findings.html",
               "knowledge.html", "inbox.html", "settings.html")
NAV_ORDER = ["chat", "home", "mission", "findings", "knowledge", "inbox",
             "settings"]
NAV_ORDER_ZH = ["对话", "仪表盘", "任务", "漏洞", "知识库", "收件箱", "设置"]
# 任务面六签（IA v2 吸收十签精华；旧四签保位不删）
TAB_FIRST_SIX = ["overview", "sess", "assets", "vuln", "retest", "report"]
TAB_KEPT_OLD = ["map", "live", "cost", "log"]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _face(name):
    if name == "index.html":
        return _read(os.path.join(STATIC, "index.html"))
    return _read(os.path.join(PAGES, name))


# ═════════════════════════ ① 页面层+② 机制层：对话面四件 ════════════════════

class TestChatFaceStructure(unittest.TestCase):
    """对话面（/p/chat）DOM 钉：四件+机制三律+零框架。"""

    def test_chat_page_exists_and_five_sec(self):
        p = os.path.join(PAGES, "chat.html")
        self.assertTrue(os.path.isfile(p), "pages/chat.html 须在盘上")
        html = _read(p)
        self.assertIn(FIVE_SEC_MARK, html)
        self.assertLess(len(html.splitlines()), 2000, "页面 <2000 行")

    def test_chat_four_pieces_dom(self):
        html = _face("chat.html")
        # 件一：消息流投影气泡
        self.assertIn('id="chat-log"', html)
        self.assertIn("/api/v2/chat-log", html)
        # 件二：输入框 → propose 内联任务卡 + 确认跳 battle/new 表单页
        self.assertIn('id="chat-input"', html)
        self.assertIn('id="btn-send"', html)
        self.assertIn("/api/v2/battle/propose", html)
        self.assertIn('id="card-prose"', html)            # 内联任务卡位
        self.assertIn("/p/new-task", html)                # 确认跳开仗表单
        # 件三：@引用下拉（at-search）
        self.assertIn('id="at-drop"', html)
        self.assertIn("/api/v2/at-search", html)
        # 件四：回复四分类按钮 → steer-reply
        self.assertIn('id="reply-bar"', html)
        self.assertIn("/api/v2/steer-reply", html)
        for cat, label in (("approve", "批准"), ("reject", "拒绝"),
                           ("redirect", "改方向"), ("intel", "给情报")):
            self.assertIn('data-cat="%s"' % cat, html, cat)
            self.assertIn(label, html, label)

    def test_chat_mechanism_three_laws(self):
        """1s 尾轮询+key 去重+不乐观回声+渐进披露（ARTEX 通用件）。"""
        html = _face("chat.html")
        self.assertIn("POLL_MS", html)
        self.assertIn("1000", html)                 # 1s 尾轮询
        self.assertIn("data-key", html)             # key 去重（seq 单调幂等同义）
        self.assertIn("不乐观回声", html)            # 发送后不本地插泡，等投影回流
        self.assertIn("载入更早", html)              # 渐进披露（尾窗渲染+翻旧）

    def test_chat_concentric_links(self):
        """同心圆导航：消息流内一击达任务面与漏洞面。"""
        html = _face("chat.html")
        self.assertIn("/p/mission", html)
        self.assertIn("/p/findings", html)

    def test_chat_zero_framework(self):
        html = _face("chat.html")
        self.assertNotIn("cdn.jsdelivr", html)
        self.assertNotIn("unpkg.com", html)
        self.assertNotIn("<iframe", html)
        self.assertIn("/static/app.js", html)       # 共享壳已消费


# ═════════════════════════ ③ 导航层：侧栏序+仪表盘降位 ══════════════════════

class TestNavOrderSevenFaces(unittest.TestCase):
    """七面侧栏序钉：对话/仪表盘/任务/漏洞/知识库/收件箱/设置。"""

    def test_nav_data_nav_order_all_faces(self):
        for name in SEVEN_FACES:
            html = _face(name)
            got = re.findall(r'data-nav="([a-z0-9-]+)"', html)
            self.assertEqual(got, NAV_ORDER, name)

    def test_home_renamed_dashboard_labels(self):
        for name in SEVEN_FACES:
            html = _face(name)
            self.assertIn(">仪表盘</a>", html, name + " 侧栏词")
        idx = _face("index.html")
        self.assertNotIn(">首页</a>", idx)          # 降位改名，不留旧词

    def test_chat_first_citizen_links(self):
        """六面+对话互相可达：每面侧栏都带 /p/chat。"""
        for name in SEVEN_FACES:
            self.assertIn("/p/chat", _face(name), name)

    def test_dashboard_four_questions_anchored(self):
        """IA 锚仍钉①：首页降观察面，四问直答不动。"""
        idx = _face("index.html")
        for a in ('id="q1"', 'id="q2"', 'id="q3"', 'id="q4"'):
            self.assertIn(a, idx)
        self.assertIn("/api/v2/cockpit.json", idx)
        self.assertIn("仪表盘", idx)


# ═══════════════════════ ④ 任务面：六签吸收十签精华 ═══════════════════════

class TestMissionSixTabsAbsorb(unittest.TestCase):
    """任务面六签（概况/会话流/资产/漏洞/复测/报告）：已有保位，缺的只留位。"""

    def test_tab_order_first_six_then_old_four(self):
        html = _face("mission.html")
        got = re.findall(r'data-t="([a-z]+)"', html)
        self.assertEqual(got[:6], TAB_FIRST_SIX)
        self.assertEqual(got[6:], TAB_KEPT_OLD)     # 旧四签保位不删
        for label in ("概况", "会话流", "资产", "漏洞", "复测", "报告"):
            self.assertIn(label, html, label)

    def test_session_flow_default_first_class(self):
        """会话流=缺的签升一等（默认开），flow 锚仍在。"""
        html = _face("mission.html")
        self.assertIn('id="flow"', html)
        self.assertIn('data-t="sess"', html)
        self.assertRegex(html, r'data-t="sess"[^>]*class="on"')

    def test_placeholder_slots_no_fabrication(self):
        """缺的签只留位（slot），链到既有真页，不虚造数据。"""
        html = _face("mission.html")
        for tid, link in (("assets", "/p/coverage"), ("retest", "/p/retest"),
                          ("report", "/p/report-center")):
            self.assertIn('id="tp-%s"' % tid, html, tid)
            self.assertRegex(
                html, 'id="tp-%s"[^>]*class="[^"]*slot' % tid, tid + " 留位")
            self.assertIn(link, html, tid + " 已有真面链接")

    def test_old_tab_words_kept(self):
        """旧六签词仍在（cockpit_faces 既有门同词防回退）。"""
        html = _face("mission.html")
        for w in ("概况", "地图", "活池", "漏洞", "消费", "日志"):
            self.assertIn(w, html, w)


# ═════════════════════ ⑤ 投影层：chat-log 只读四类气泡 ═════════════════════

TL_COLS = ["timestamp", "actor", "phase", "event", "revert_cmd",
           "prev_hash", "hash", "schema_version"]


def _tl_line(ts, actor, phase, event, revert=""):
    cols = dict.fromkeys(TL_COLS, "")
    cols.update(timestamp=ts, actor=actor, phase=phase, event=event,
                revert_cmd=revert, schema_version="2")
    return "\t".join(cols[c] for c in TL_COLS)


class _ProjBase(unittest.TestCase):
    """单账本夹具：G-x 目内 timeline 四行+ask.md 求助。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp(prefix="chatlog-g-")
        rows = [
            _tl_line("2026-10-20T01:00:00Z", "CLI", "P0", "add-goal G-x-0001"),
            _tl_line("2026-10-20T01:01:00Z", "操作员", "P3",
                     "battle-say 对齐目标范围"),
            _tl_line("2026-10-20T01:02:00Z", "CLI", "P3",
                     "tools-reject sqlmap --level=3 approval-required marker=x1",
                     revert="rm /tmp/marker-x1"),
            _tl_line("2026-10-20T01:03:00Z", "总控", "P3",
                     "warrior-steer target=w1 text=【情报】试试后台"),
        ]
        with open(os.path.join(self.gd, "timeline.tsv"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n".join(rows) + "\n")
        with open(os.path.join(self.gd, "ask.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("这个端口能不能扫？\n")

    def tearDown(self):
        shutil.rmtree(self.gd, ignore_errors=True)

    def _api(self):
        from webui import api_v2_chat
        return api_v2_chat

    def _call(self, **kw):
        api = self._api()
        st, payload = api.chat_log(kw, self.gd)
        self.assertEqual(st, 200, payload)
        return payload

    def _tree_snapshot(self):
        snap = {}
        for root, _dirs, files in os.walk(self.gd):
            for fn in files:
                p = os.path.join(root, fn)
                with open(p, "rb") as f:
                    snap[p] = f.read()
        return snap


class TestChatLogProjection(_ProjBase):
    """四类事件投影：command/warrior/ask/approval——只读零写零墙钟。"""

    def test_four_kinds_present(self):
        p = self._call()
        kinds = {e["kind"] for e in p["events"]}
        self.assertEqual(kinds, {"command", "warrior", "ask", "approval"})

    def test_event_shape_and_keys_unique(self):
        p = self._call()
        keys = [e["key"] for e in p["events"]]
        self.assertEqual(len(keys), len(set(keys)), "key 去重单源")
        for e in p["events"]:
            for f in ("kind", "ts", "text", "key"):
                self.assertIn(f, e)
        self.assertTrue(p["read_only"])

    def test_command_bubble_rule(self):
        """battle-say/warrior-steer=指挥（右泡）；其余 timeline=士兵（左泡）。"""
        p = self._call()
        texts = {(e["kind"], e.get("event", e["text"])) for e in p["events"]}
        self.assertIn(("command", "battle-say 对齐目标范围"), texts)
        self.assertIn(("command",
                       "warrior-steer target=w1 text=【情报】试试后台"), texts)
        self.assertIn(("warrior", "add-goal G-x-0001"), texts)

    def test_ask_bubble_from_ask_md(self):
        p = self._call()
        asks = [e for e in p["events"] if e["kind"] == "ask"]
        self.assertEqual(len(asks), 1)
        self.assertIn("这个端口能不能扫", asks[0]["text"])

    def test_approval_bubble_pending_with_row(self):
        """待审批气泡带 timeline row（回复四分类 join /api/approval 用）。"""
        p = self._call()
        aps = [e for e in p["events"] if e["kind"] == "approval"]
        self.assertEqual(len(aps), 1)
        self.assertEqual(aps[0]["row"], 3)
        self.assertIn("sqlmap", aps[0]["text"])

    def test_order_deterministic_two_runs_equal(self):
        a = json.dumps(self._call(), sort_keys=True, ensure_ascii=False)
        b = json.dumps(self._call(), sort_keys=True, ensure_ascii=False)
        self.assertEqual(a, b, "同输入两跑一致（零墙钟）")
        p = json.loads(a)
        ts = [e["ts"] for e in p["events"]]
        self.assertEqual(ts, sorted(ts), "按时刻升序")

    def test_limit_tail_window(self):
        p = self._call(limit=2)
        self.assertLessEqual(len(p["events"]), 2)
        self.assertGreaterEqual(p["counts"]["total"], 5)

    def test_zero_write_iron(self):
        before = self._tree_snapshot()
        self._call()
        self.assertEqual(before, self._tree_snapshot(), "只读投影零写入")

    def test_source_law_no_wall_clock(self):
        src = _read(os.path.join(CLI, "webui", "api_v2_chat.py"))
        self.assertNotIn("datetime.now", src)
        self.assertNotIn("time.time", src)
        self.assertNotIn("utcnow", src)

    def test_unknown_battle_422(self):
        battles = tempfile.mkdtemp(prefix="chatlog-b-")
        self.addCleanup(shutil.rmtree, battles, True)
        gd = os.path.join(battles, "battle-1", "G-a")
        os.makedirs(gd)
        with open(os.path.join(gd, "timeline.tsv"), "w",
                  encoding="utf-8") as f:
            f.write(_tl_line("2026-10-20T01:00:00Z", "CLI", "P0",
                             "add-goal G-b1-0001") + "\n")
        api = self._api()
        st, payload = api.chat_log({"battle": "99"}, "", battles_dir=battles)
        self.assertEqual(st, 422)
        self.assertIn("error", payload)

    def test_battles_mode_pick_battle(self):
        battles = tempfile.mkdtemp(prefix="chatlog-bb-")
        self.addCleanup(shutil.rmtree, battles, True)
        gd = os.path.join(battles, "battle-1", "G-a")
        os.makedirs(gd)
        with open(os.path.join(gd, "timeline.tsv"), "w",
                  encoding="utf-8") as f:
            f.write(_tl_line("2026-10-20T01:00:00Z", "CLI", "P0",
                             "add-goal G-b1-0001") + "\n")
        api = self._api()
        st, p = api.chat_log({"battle": "1"}, "", battles_dir=battles)
        self.assertEqual(st, 200, p)
        self.assertTrue(any(e["kind"] == "warrior" for e in p["events"]))
        self.assertEqual(p["battle"]["id"], "battle-1")


# ═══════════════ 挂载契约：生产 Handler 形（_V2MountHandler 先例） ══════════════

class _V2MountHandler(srv_mod.Handler):
    """挂法钉：GET /api/v2/chat-log 过会话门后分发（api_v2_command 同法）。"""

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/v2/chat-log":
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            api = self._chat_api()
            try:
                status, payload = api.dispatch(
                    u.path, q, self.server.ledger_dir,
                    battles_dir=getattr(self.server, "battles_dir", "") or None)
            except ValueError as e:
                status, payload = 422, {"error": str(e)}
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False)
                              .encode("utf-8"))
        return super().do_GET()

    @staticmethod
    def _chat_api():
        from webui import api_v2_chat
        return api_v2_chat


class TestV2MountContract(_ProjBase):
    """生产形挂载：会话门+四类投影+/p/chat 页路由+只读铁律。"""

    def setUp(self):
        super().setUp()
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.gd,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir="")
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
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp, body

    def test_get_401_without_session(self):
        resp, _ = self._get("/api/v2/chat-log", cookie=False)
        self.assertEqual(resp.status, 401)

    def test_get_200_with_session_four_kinds(self):
        resp, body = self._get("/api/v2/chat-log")
        self.assertEqual(resp.status, 200)
        p = json.loads(body.decode("utf-8"))
        kinds = {e["kind"] for e in p["events"]}
        self.assertEqual(kinds, {"command", "warrior", "ask", "approval"})

    def test_chat_page_served_by_production_route(self):
        """生产 /p/<slug> 页路由：chat.html 落盘即可达（api_pages 单源）。"""
        name, err = api_pages.page_file("/p/chat")
        self.assertIsNone(err, err)
        self.assertEqual(name, "pages/chat.html")
        resp, body = self._get("/p/chat")
        self.assertEqual(resp.status, 200)
        self.assertIn('id="chat-log"', body.decode("utf-8"))

    def test_read_only_sweep(self):
        before = self._tree_snapshot()
        self._get("/api/v2/chat-log")
        self._get("/p/chat")
        self.assertEqual(before, self._tree_snapshot())


# ═════════════════════ IA 锚仍钉（四问+证据袋+复验） ═════════════════════════

class TestIAAnchorsStillPinned(unittest.TestCase):
    """壳重排不推翻 GL-DS 与既有 IA 锚：四问/证据袋+复验/任务卡确认门。"""

    def test_dashboard_and_findings_anchors(self):
        idx = _face("index.html")
        self.assertIn("四问直答", idx)
        fnd = _face("findings.html")
        for a in ("证据袋", "上次验真", "待复验"):
            self.assertIn(a, fnd, a)

    def test_propose_card_confirm_gate_words(self):
        """对话面任务卡=只产卡不开仗（范围必须人确认律的平台面词）。"""
        html = _face("chat.html")
        self.assertIn("确认", html)
        self.assertIn("范围预览", html)


if __name__ == "__main__":
    unittest.main()
