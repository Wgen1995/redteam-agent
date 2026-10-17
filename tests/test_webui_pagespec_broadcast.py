# -*- coding: utf-8 -*-
"""UI-2·P5.3 播报页签（T2 页规范测试）——timeline 播报类行投影 + 直播页。

契约（docs/design/ui-spec-complete-v1.md P5.3 + battle-cockpit-v1.md 页签3 +
ui-copy-standard-v1.md 宪法 #41 界面人话律）:
- API: cli/webui/api_v2_broadcast.py → GET /api/v2/broadcast.json?battle=N&frame=M
  （UI-1 壳负责路由注册与登录门;本模块纯投影只读零写入）;
- 页面: cli/webui/static/pages/broadcast.html——智能体直播气泡（时间+账本行号角标）
  +操作员气泡+底部输入框（POST 既有 /api/battle/say）+介入说明条+自动滚动可暂停
  +播报 hover「查看证据」跳 EV 卡（/evidence#f=<发现号> 锚）;URL 带 frame 只显示
  该帧前;SSE 实时（复用 /api/stream）;四态齐备;
- 播报类行定义: 战士写账行（actor=CLI）=智能体叙述;battle-say 行=操作员气泡;
  平台执法行（总控/canary/egress）与验证环行（replay）不入播报流;
- 测试独立: 动态端口起服,禁碰 8900 与 ZhuLong 仓。

python3 -m unittest tests.test_webui_pagespec_broadcast
"""
import json
import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core                     # noqa: E402
from webui import api_v2_broadcast as api   # noqa: E402
from webui import server as srv_mod         # noqa: E402

T = core.TABLES
PAGE_PATH = os.path.join(CLI, "webui", "static", "pages", "broadcast.html")
TS = "2026-10-18T01:00:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in specs:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def write_tsv(path, rows_):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    core.write_tsv(path, rows_)


def build_fixture(battles):
    """两战夹具: battle-7（8 行 mixed timeline + E-index 挂发现 + goals 立项行——
    POST /api/battle/say 的 append-timeline 走 tier0 硬门须 goals 行）与 battle-3。"""
    gd7 = os.path.join(battles, "battle-7", "G-a")
    write_tsv(os.path.join(gd7, "goals.tsv"), [row(
        "goals.tsv", id="G-a-0001", target="shop.example",
        objective="授权渗透测试", budget="200000;5000;4",
        schema_version="2", created=TS)])
    write_tsv(os.path.join(gd7, "timeline.tsv"), chained_tl([
        (TS, "CLI", "", "add-goal G-a-0001",),
        (TS, "总控", "P0", "gate-exit:P0 asserts=1 result=PASS"),
        (TS, "CLI", "P1", "add-intent INT-a-0001"),
        (TS, "CLI", "P1", "add-evidence EV-a-0001"),
        (TS, "人工", "P-lifecycle", "battle-say battle-7 len=12"),
        (TS, "replay", "P4", "replay-probe EV-a-0001 verdict=reproduced"),
        (TS, "CLI", "P4", "replay:EV-a-0001:VERIFIED"),
        (TS, "CLI", "P2", "future-verb XYZ-1"),
    ]))
    write_tsv(os.path.join(gd7, "E-index.tsv"), [row(
        "E-index.tsv", id="EV-a-0001", title="反射 XSS 回显",
        source_type="command", linked_finding="FD-a-0001",
        created=TS)])
    gd3 = os.path.join(battles, "battle-3", "G-x")
    write_tsv(os.path.join(gd3, "timeline.tsv"), chained_tl([
        (TS, "CLI", "", "add-goal G-x-0001")]))
    return battles


# ===========================================================================
# A. 投影面（api_v2_broadcast.broadcast_view 单源）
# ===========================================================================

class BroadcastViewTest(unittest.TestCase):
    """播报类行投影: 分类/人话/行号锚/证据跳转/帧过滤/尾条/错误态/只读律。"""

    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = build_fixture(os.path.join(self.td.name, "battles"))

    def view(self, **kw):
        from webui import api_v2_broadcast as bv
        kw.setdefault("battles_dir", self.battles)
        return bv.broadcast_view(**kw)

    def test_module_contract_and_route_doc(self):
        """模块在位且文档钉死路由形（/api/v2/ 前缀+会话门由壳注册）。"""
        from webui import api_v2_broadcast as bv
        self.assertTrue(callable(bv.broadcast_view))
        doc = bv.__doc__ or ""
        self.assertIn("/api/v2/broadcast.json", doc)

    def test_classification_and_row_anchors(self):
        """智能体=CLI 行,操作员=battle-say 行;平台/replay 行不入流;行号=账本行号。"""
        d = self.view(battle=7)
        self.assertEqual([r["row"] for r in d["rows"]], [1, 3, 4, 5, 7, 8])
        self.assertEqual([r["kind"] for r in d["rows"]],
                         ["agent", "agent", "agent", "operator", "agent", "agent"])
        self.assertEqual(d["latest_row"], 8)         # 全量行计数（帧=行号语义）
        self.assertEqual(d["counts"]["agent"], 5)
        self.assertEqual(d["counts"]["operator"], 1)

    def test_operator_row_len_and_no_jargon(self):
        """操作员气泡行: len 提取+人话文案（不上内部代号）。"""
        d = self.view(battle=7)
        op = [r for r in d["rows"] if r["kind"] == "operator"][0]
        self.assertEqual(op["len"], 12)
        self.assertIn("操作员指令", op["text"])
        self.assertNotIn("battle-say", op["text"])

    def test_agent_text_is_plain_language(self):
        """人话律: 已知动词译成人话,未知动词兜底「记录」,不裸出内部动词。"""
        d = self.view(battle=7)
        by_row = {r["row"]: r for r in d["rows"]}
        self.assertIn("立项", by_row[1]["text"])
        self.assertIn("新增意图", by_row[3]["text"])
        self.assertIn("存证", by_row[4]["text"])
        self.assertIn("复测通过", by_row[7]["text"])
        self.assertIn("记录", by_row[8]["text"])     # 未知动词兜底
        for r in d["rows"]:
            self.assertNotEqual(r["text"].strip(), "")

    def test_evidence_refs_and_finding_anchor(self):
        """播报行提取 EV 引用并解析发现锚（/evidence#f=<发现号> 跳 EV 卡）。"""
        d = self.view(battle=7)
        by_row = {r["row"]: r for r in d["rows"]}
        ev = by_row[4]["evidence"]
        self.assertEqual(ev, [{"id": "EV-a-0001", "finding": "FD-a-0001"}])
        self.assertEqual(by_row[7]["evidence"][0]["id"], "EV-a-0001")

    def test_frame_param_shows_only_before_frame(self):
        """URL frame 参数: 只显示该帧前（行号 < frame）。"""
        d = self.view(battle=7, frame=5)
        self.assertEqual(d["frame"], 5)
        self.assertEqual([r["row"] for r in d["rows"]], [1, 3, 4])

    def test_tail_clamps_recent_rows(self):
        """tail=最近 N 条播报（默认裁尾,不无限加载）。"""
        d = self.view(battle=7, tail=2)
        self.assertEqual([r["row"] for r in d["rows"]], [7, 8])

    def test_latest_battle_default_and_battle_pick(self):
        """无参=最新战（战号最大）;battle=3 选战。"""
        self.assertEqual(self.view()["battle"]["n"], 7)
        self.assertEqual(self.view(battle=3)["battle"]["n"], 3)

    def test_missing_battle_error_shape(self):
        """战不存在 → error 形（同 session_api 先例）,附 battles 表。"""
        d = self.view(battle=99)
        self.assertIn("error", d)
        self.assertIn("battle 不存在: 99", d["error"])
        self.assertTrue(any(b["n"] == 7 for b in d["battles"]))

    def test_bad_number_and_frame_raise(self):
        """坏战号/坏帧值 → ValueError（路由层转 4xx,投影层不吞错）。"""
        from webui import api_v2_broadcast as bv
        with self.assertRaises(ValueError):
            bv.broadcast_view(battles_dir=self.battles, battle="abc")
        with self.assertRaises(ValueError):
            bv.broadcast_view(battles_dir=self.battles, frame="x")

    def test_readonly_and_deterministic(self):
        """只读律: 目录字节不变;确定性: 两次调用同输出。"""
        def digest():
            import hashlib
            out = []
            for root, _dirs, files in os.walk(self.battles):
                for f in sorted(files):
                    p = os.path.join(root, f)
                    with open(p, "rb") as fh:
                        out.append((os.path.relpath(p, self.battles),
                                    hashlib.sha256(fh.read()).hexdigest()))
            return out
        before = digest()
        d1 = self.view(battle=7)
        self.assertEqual(before, digest())
        d2 = self.view(battle=7)
        self.assertEqual(json.dumps(d1, sort_keys=True),
                         json.dumps(d2, sort_keys=True))

    def test_json_serializable_and_empty_battles(self):
        """payload 全 JSON 可序列化;空 battles 根=空 shape 不爆。"""
        json.dumps(self.view(battle=7), ensure_ascii=False)
        import tempfile
        with tempfile.TemporaryDirectory() as empty:
            d = self.view(battles_dir=empty)
            self.assertIsNone(d["battle"])
            self.assertEqual(d["rows"], [])


# ===========================================================================
# B. 挂载层（api_pages.py 未落地——Handler 子类钉 include 挂法,T1·P6 同形）
# ===========================================================================

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉: /api/v2/* 过会话门后分发 ROUTES 单源表。

    UI-1 的 api_pages.py 落地时按本形挂载: 会话门复用 Handler._session_ok,
    分发=api_v2_broadcast.dispatch(path, query, ledger_dir, battles_dir) →
    (status, payload);ValueError=422,error 形=404。
    """

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            status, payload = api.dispatch(u.path, q, self.server.ledger_dir,
                                           battles_dir=self.server.battles_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class ServerBase(unittest.TestCase):
    """动态口起服（server_address[1],禁碰 8900）+登录拿会话 cookie。"""

    def setUp(self):
        import tempfile
        from tests import webui_login
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = build_fixture(os.path.join(self.td.name, "battles"))
        self.ledger = os.path.join(self.td.name, "ledger")
        os.makedirs(self.ledger)
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.ledger,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=self.battles)
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
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=8)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def _post(self, path, body):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        conn.request("POST", path, body=json.dumps(body).encode("utf-8"), headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "http://127.0.0.1:%d" % self.port,
            "Cookie": "tanyin_sess=" + self.sid})
        return conn, conn.getresponse()


class TestV2MountContract(ServerBase):
    """/api/v2/broadcast.json 会话门+分发+错误映射（404/422）+只读律。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/broadcast.json?battle=7", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_200_payload_over_http(self):
        conn, resp = self._get("/api/v2/broadcast.json?battle=7")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["battle"]["n"], 7)
        self.assertEqual([r["row"] for r in p["rows"]], [1, 3, 4, 5, 7, 8])
        self.assertEqual(p["stream_aligned"], False)   # 服务器账本≠战目录
        conn.close()

    def test_frame_filter_over_http(self):
        conn, resp = self._get("/api/v2/broadcast.json?battle=7&frame=5")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual([r["row"] for r in p["rows"]], [1, 3, 4])
        conn.close()

    def test_missing_battle_maps_404(self):
        conn, resp = self._get("/api/v2/broadcast.json?battle=99")
        self.assertEqual(resp.status, 404)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertIn("battle 不存在", p["error"])
        conn.close()

    def test_bad_value_maps_422(self):
        conn, resp = self._get("/api/v2/broadcast.json?battle=7&frame=abc")
        self.assertEqual(resp.status, 422)
        self.assertIn("error", json.loads(resp.read().decode("utf-8")))
        conn.close()
        conn, resp = self._get("/api/v2/broadcast.json?battle=abc")
        self.assertEqual(resp.status, 422)
        resp.read()
        conn.close()

    def test_unknown_v2_path_falls_through_404(self):
        conn, resp = self._get("/api/v2/nope")
        self.assertEqual(resp.status, 404)
        resp.read()
        conn.close()

    def test_stream_aligned_when_ledger_is_battle_gen(self):
        """服务器 --ledger-dir 指到战最新代目录时 stream_aligned=True（SSE 同轴）。"""
        gen = os.path.join(self.battles, "battle-7", "G-a")
        self.srv.ledger_dir = gen
        conn, resp = self._get("/api/v2/broadcast.json?battle=7")
        p = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(p["stream_aligned"])
        conn.close()

    def test_http_hits_readonly(self):
        import hashlib
        def digest():
            out = []
            for root, _dirs, files in os.walk(self.battles):
                for f in sorted(files):
                    p = os.path.join(root, f)
                    with open(p, "rb") as fh:
                        out.append((os.path.relpath(p, self.battles),
                                    hashlib.sha256(fh.read()).hexdigest()))
            return out
        before = digest()
        for pth in ("/api/v2/broadcast.json?battle=7",
                    "/api/v2/broadcast.json?battle=7&frame=5",
                    "/api/v2/broadcast.json"):
            conn, resp = self._get(pth)
            self.assertEqual(resp.status, 200, pth)
            resp.read()
            conn.close()
        self.assertEqual(digest(), before)


class TestSayDualWrite(ServerBase):
    """底部输入框发送通道: 既有 POST /api/battle/say——指令文件+timeline 双落。"""

    def test_say_writes_directive_and_timeline_then_broadcasts(self):
        text = "暂停外发，先取证再继续"
        conn, resp = self._post("/api/battle/say", {"battle": 7, "text": text})
        body = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["battle"], 7)
        self.assertEqual(body["directive"], "written")
        # 双落①: 指令通道原文
        with open(os.path.join(self.battles, "battle-7", "directive.txt"),
                  encoding="utf-8") as f:
            self.assertEqual(f.read(), text)
        # 双落②: timeline 留痕行（actor=人工,事件带长度）
        tl = core.Session(os.path.join(self.battles, "battle-7", "G-a")
                          ).rows("timeline.tsv")
        self.assertEqual(len(tl), 9)
        last = tl[-1]
        self.assertEqual(last[T["timeline.tsv"].index("actor")], "人工")
        self.assertEqual(last[T["timeline.tsv"].index("event")],
                         "battle-say battle-7 len=%d" % len(text))
        self.assertEqual(body["timeline_row"], 9)
        # 播报投影收操作员气泡（行号=回执行号,长度入文）
        conn, resp = self._get("/api/v2/broadcast.json?battle=7&tail=1")
        p = json.loads(resp.read().decode("utf-8"))
        conn.close()
        op = p["rows"][-1]
        self.assertEqual(op["kind"], "operator")
        self.assertEqual(op["row"], 9)
        self.assertEqual(op["len"], len(text))
        self.assertIn("操作员指令", op["text"])

    def test_say_rejects_empty_text(self):
        conn, resp = self._post("/api/battle/say", {"battle": 7, "text": "  "})
        self.assertEqual(resp.status, 422)
        self.assertIn("error", json.loads(resp.read().decode("utf-8")))
        conn.close()

    def test_say_rejects_missing_battle(self):
        conn, resp = self._post("/api/battle/say", {"battle": 99, "text": "hi"})
        self.assertEqual(resp.status, 404)
        resp.read()
        conn.close()


# ===========================================================================
# C. 页面层（static/pages/broadcast.html 结构钉——四态+介入条+输入+SSE+吸附滚动）
# ===========================================================================

PAGE_MARKS = (
    # 顶部任务条: 战选择/代目录/实时通道状态/行计数
    'id="battle-pick"', 'id="stream-dot"', 'id="stream-tip"', 'id="row-count"',
    # 介入说明条（P5.3 布局钉）
    'id="intervene-bar"',
    # 历史视图联动: URL frame 参数横幅+回到最新
    'id="hist-banner"', 'id="hist-text"', 'id="btn-latest"', '回到最新',
    # 四态（空/加载/错误含重试/正常）
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 气泡流+自动滚动可暂停吸附
    'id="feed"', 'id="follow-chip"',
    # 底部输入框+发送（POST 既有 /api/battle/say 指令通道）
    'id="say-input"', 'id="btn-send"', 'id="send-note"',
    # 气泡结构: 时间+账本行号角标+原文回显+hover 证据链接
    'bub-time', 'row-badge', 'bub-raw', 'ev-link', '查看证据',
    # 宿主壳接入（UI-1 app.js）+页签导出
    'nav.push', "id: 'broadcast'", 'typeof nav.push', 'BroadcastTab',
)
FETCH_MARKS = ("'/api/v2/broadcast.json", "EventSource('/api/stream?tail=0')",
               "'/api/battle/say'", "X-Requested-With")
BANNED_WORDS = ("战士", "琥珀线", "八问", "作战室", "三态")   # 宪法#41 界面人话律


class TestPageStructure(unittest.TestCase):
    """播报页结构钉: 四态齐备/介入条/输入/SSE 复用/证据跳转/零 CDN/人话律。"""

    def _src(self):
        with open(PAGE_PATH, encoding="utf-8") as f:
            return f.read()

    def test_zones_and_states_present(self):
        src = self._src()
        for m in PAGE_MARKS:
            self.assertIn(m, src, "缺 " + m)
        for m in FETCH_MARKS:
            self.assertIn(m, src, "须接 " + m)

    def test_copy_constitution_no_jargon(self):
        """宪法#41: 战士→智能体等映射上屏;内部代号禁绝。"""
        src = self._src()
        for w in BANNED_WORDS:
            self.assertNotIn(w, src, "禁词上屏: " + w)
        for w in ("智能体", "操作员", "介入"):
            self.assertIn(w, src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)
        self.assertNotIn("http://", src.replace("127.0.0.1", ""))  # 无外链

    def test_line_budget_about_450(self):
        """~450 行量纲（P5.3 页签）;JS<2000。"""
        src = self._src()
        n = len(src.splitlines())
        self.assertGreaterEqual(n, 400, "低于量纲下限: %d" % n)
        self.assertLessEqual(n, 800, "超量纲上限: %d" % n)
        blocks = src.split("<script>")[1:]
        js = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(js, 2000)

    def test_frame_history_and_stream_guard_in_js(self):
        """历史视图: frame 在场禁 SSE/禁发送;对齐旗决定 SSE 或轮询。"""
        src = self._src()
        self.assertIn("stream_aligned", src)
        self.assertIn("setInterval", src)          # 未对齐回落轮询
        self.assertIn("frame", src)


if __name__ == "__main__":
    unittest.main()
