# -*- coding: utf-8 -*-
"""T3·P5.5 复测页签钉测（界面线施工计划 2026-10-18 T3）。

python3 -m unittest tests.test_webui_pagespec_retest
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P5.5；文案宪法#41（界面人话律）。
数据源=findings 复测域+重放日志（timeline replay-probe × replay/<EV>/<n>.json）。

三层钉：
  ①投影层  api_v2_retest.retest_view——复测队列(发现ID/上次结果/距上次/客户反馈)
           +逐发现复测历史(时间/结果/差异/触发方式)；多代目合并（G-r2<G-r10 自然序）。
  ②挂载层  /api/v2/retest.json 过会话门（无 cookie=401 JSON），battle 选战，
           坏战号=422、不存在=404；测试动态取口（server_address[1]，禁碰 8900）。
  ③页面层  static/pages/retest.html 结构钉（队列表+历史时间线+四态+nav.push
           自注册+零 CDN+立即复测写入路由守卫降级）。
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
from ledger import core  # noqa: E402
from webui import api_v2_retest as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-20T01:00:00Z"
TS2 = "2026-10-20T01:01:00Z"
TS3 = "2026-10-20T01:02:00Z"
TS4 = "2026-10-20T01:03:00Z"
TS5 = "2026-10-20T01:04:00Z"
TS6 = "2026-10-20T01:05:00Z"
TS7 = "2026-10-20T01:06:00Z"
TS8 = "2026-10-20T01:07:00Z"
TS9 = "2026-10-20T01:20:00Z"
TS10 = "2026-10-20T01:30:00Z"
TS11 = "2026-10-20T01:40:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in rows_spec:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _replay(gd, ev, seq, obj):
    d = os.path.join(gd, "replay", ev)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%d.json" % seq), "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True)


def build_fixture(td):
    """battle-7 三代目（G-r1/G-r2/G-r10——钉自然序而非字典序）。"""
    bdir = os.path.join(td, "battles", "battle-7")
    g1 = os.path.join(bdir, "G-r1")
    os.makedirs(g1)
    core.write_tsv(os.path.join(g1, "findings.tsv"), [
        row("findings.tsv", id="FD-7001", intent_id="INT-7001", title="管理面板匿名可读",
            confidence="C1", impact="高", exploitation_status="verified",
            dedup_key="admin-anon", affected_asset_id="AST-7001",
            evidence_ids="EV-7001,EV-7002", card_path="findings-cards/FD-7001.md",
            status="active", created=TS2),
        row("findings.tsv", id="FD-7002", intent_id="INT-7001", title="登录接口无速率限制",
            confidence="C2", impact="中", exploitation_status="suspected",
            dedup_key="login-rate", affected_asset_id="AST-7001", card_path="",
            status="active", created=TS3),
    ])
    core.write_tsv(os.path.join(g1, "E-index.tsv"), [
        row("E-index.tsv", id="EV-7001", title="管理面板响应捕获", source_type="capture",
            observed_at=TS4, network_position="internet",
            repro_command="curl -i http://shop.example/admin", repro_kind="single",
            artifact_path="artifacts/EV-7001.raw", card_path="evidence/EV-7001.md",
            linked_finding="FD-7001", created=TS4),
        row("E-index.tsv", id="EV-7002", title="登录爆破计数", source_type="command",
            observed_at=TS5, network_position="internet",
            repro_command="curl -X POST http://shop.example/login", repro_kind="single",
            artifact_path="artifacts/EV-7002.raw", card_path="evidence/EV-7002.md",
            linked_finding="FD-7001", created=TS5),
    ])
    core.write_tsv(os.path.join(g1, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-r1"),
        (TS2, "CLI", "P2", "add-finding FD-7001"),
        (TS3, "CLI", "P2", "add-finding FD-7002"),
        (TS4, "CLI", "P2", "add-evidence EV-7001"),
        (TS5, "CLI", "P2", "add-evidence EV-7002"),
        (TS6, "CLI", "P2", "replay-probe EV-7001 verdict=not-reproduced"),
        (TS7, "复测岗", "P5", "replay-probe EV-7001 verdict=reproduced"),
        (TS8, "CLI", "P2", "replay-probe EV-7002 verdict=reproduced"),
        (TS9, "操作员", "P5", "feedback FD-7001 客户称已修复请复测"),
    ]))
    _replay(g1, "EV-7001", 1, {"id": "EV-7001", "verdict": "not-reproduced",
                               "matched": False, "status": 200, "elapsed_ms": 900})
    _replay(g1, "EV-7001", 2, {"id": "EV-7001", "verdict": "reproduced",
                               "matched": True, "status": 200, "elapsed_ms": 1250})
    _replay(g1, "EV-7002", 1, {"id": "EV-7002", "verdict": "reproduced",
                               "matched": True, "status": 500})

    g2 = os.path.join(bdir, "G-r2")
    os.makedirs(g2)
    core.write_tsv(os.path.join(g2, "timeline.tsv"), chained_tl([
        (TS10, "CLI", "P2", "replay-probe EV-7002 verdict=not-reproduced"),
    ]))
    _replay(g2, "EV-7002", 1, {"id": "EV-7002", "verdict": "not-reproduced",
                               "matched": False, "status": 404})

    g10 = os.path.join(bdir, "G-r10")
    os.makedirs(g10)
    core.write_tsv(os.path.join(g10, "timeline.tsv"), chained_tl([
        (TS11, "复测岗", "P5", "replay-probe EV-7001 verdict=env-diff"),
    ]))
    _replay(g10, "EV-7001", 1, {"id": "EV-7001", "verdict": "env-diff",
                                "matched": None, "detail": "ConnectionError: refused"})
    return bdir


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
        self.bdir = build_fixture(self.td.name)
        self.battles_root = os.path.join(self.td.name, "battles")
        self.ledger_dir = os.path.join(self.bdir, "G-r1")   # 服务器主账本=最新代


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestRetestProjection(Base):
    """复测队列+历史投影：findings+timeline replay-probe × replay JSON 多代合并。"""

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles_root)
        kw.setdefault("ledger_dir", self.ledger_dir)
        return api.retest_view(**kw)

    def test_queue_columns_and_order(self):
        p = self.view()
        q = p["queue"]
        self.assertEqual([f["id"] for f in q], ["FD-7001", "FD-7002"])
        f1 = q[0]
        self.assertEqual(f1["id"], "FD-7001")
        self.assertEqual(f1["title"], "管理面板匿名可读")
        self.assertEqual(f1["impact"], "高")
        self.assertEqual(f1["last_verdict"], "env-diff")
        self.assertIn("环境差异", f1["last_verdict_zh"])
        self.assertEqual(f1["last_at"], TS11)
        self.assertTrue(f1["has_feedback"])                    # 客户反馈=有
        self.assertEqual(f1["runs"], 5)                        # 三代合并 5 次
        self.assertTrue(f1["replayable"])                      # 有证据可复测
        f2 = q[1]
        self.assertEqual(f2["last_verdict"], "")
        self.assertIn("未复测", f2["last_verdict_zh"])
        self.assertFalse(f2["has_feedback"])
        self.assertFalse(f2["replayable"])                     # 无证据不可复测
        self.assertEqual(f2["runs"], 0)

    def test_queue_order_replayable_first_then_oldest(self):
        p = self.view()
        self.assertEqual(p["queue"][0]["id"], "FD-7001")       # 有证据先列

    def test_since_last_from_ledger_clock(self):
        p = self.view()
        f1 = p["queue"][0]
        self.assertEqual(p["now_ref"], TS11)                   # 战场钟=最大行时刻
        self.assertEqual(f1["since_last_s"], 0)                # TS11-本行=0
        f2 = p["queue"][1]
        self.assertEqual(f2["since_last_s"], 2280)             # 未复测=按创建 TS3 起 38 分
        self.assertIn("38", f2["since_last_text"])             # 人话距上次

    def test_history_timeline_runs_and_diffs(self):
        p = self.view()
        h = {f["id"]: f["history"] for f in p["queue"]}["FD-7001"]
        self.assertEqual(len(h), 5)
        self.assertEqual([r["seq"] for r in h], [1, 2, 3, 4, 5])
        self.assertEqual(h[0]["at"], TS6)
        self.assertEqual(h[0]["verdict"], "not-reproduced")
        self.assertEqual(h[0]["trigger"], "手动")
        self.assertEqual(h[0]["duration_ms"], 900)
        self.assertIn("基线", h[0]["diff"])                     # 首次=基线
        self.assertEqual(h[1]["trigger"], "自动复测")            # 复测岗=自动
        self.assertIn("not-reproduced → reproduced", h[1]["diff"])
        self.assertIn("200 → 500", h[2]["diff"])                # 状态码漂移入差异
        self.assertEqual(h[3]["verdict"], "not-reproduced")     # G-r2 行在 G-r10 前
        self.assertEqual(h[4]["at"], TS11)
        self.assertEqual(h[4]["verdict"], "env-diff")
        self.assertEqual(h[4]["trigger"], "自动复测")

    def test_history_never_retest(self):
        p = self.view()
        f2 = [f for f in p["queue"] if f["id"] == "FD-7002"][0]
        self.assertEqual(f2["history"], [])

    def test_feedback_requires_finding_reference(self):
        p = self.view()
        f2 = [f for f in p["queue"] if f["id"] == "FD-7002"][0]
        self.assertFalse(f2["has_feedback"])                   # 反馈行不提 FD-7002

    def test_counts(self):
        p = self.view()
        self.assertEqual(p["counts"]["findings"], 2)
        self.assertEqual(p["counts"]["replayable"], 1)
        self.assertEqual(p["counts"]["runs_total"], 5)
        self.assertEqual(p["counts"]["with_feedback"], 1)

    def test_battle_pick_and_goal(self):
        p = self.view()
        self.assertEqual(p["battle"]["id"], "battle-7")
        self.assertEqual(p["battle"]["n"], 7)
        self.assertEqual(p["goal"], "G-r10")                   # 最新代
        self.assertEqual(len(p["battles"]), 1)
        p2 = self.view(battle="7")
        self.assertEqual(p2["battle"]["n"], 7)
        p3 = self.view(battle=None)
        self.assertEqual(p3["battle"]["n"], 7)                 # 缺省=最新战

    def test_unknown_battle_error_shape(self):
        p = self.view(battle=9)
        self.assertIn("error", p)
        self.assertEqual(p["battles"][0]["n"], 7)

    def test_bad_battle_raises(self):
        with self.assertRaises(ValueError):
            self.view(battle="xyz")

    def test_single_goal_fallback(self):
        gd = os.path.join(self.td.name, "G-solo")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "findings.tsv"), [row(
            "findings.tsv", id="FD-s1", title="单账本发现", impact="低",
            status="active", created=TS1)])
        p = api.retest_view(battles_dir=os.path.join(self.td.name, "none"),
                            ledger_dir=gd)
        self.assertIsNone(p["battle"])
        self.assertEqual(p["goal"], "G-solo")
        self.assertEqual(p["queue"][0]["id"], "FD-s1")

    def test_empty_ledger_tolerant(self):
        gd = os.path.join(self.td.name, "G-bare")
        os.makedirs(gd)
        p = api.retest_view(battles_dir=os.path.join(self.td.name, "none"),
                            ledger_dir=gd)
        self.assertEqual(p["queue"], [])
        self.assertEqual(p["counts"]["findings"], 0)
        self.assertEqual(p["now_ref"], "")

    def test_readonly_deterministic(self):
        before = dir_bytes(self.bdir)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.bdir), before)
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


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.ledger_dir,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=self.battles_root)
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
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()


class TestV2MountContract(ServerBase):
    """/api/v2/retest.json 会话门+分发（动态口=server_address[1]，禁碰 8900）。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/retest.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_over_http_with_battle(self):
        conn, resp = self._get("/api/v2/retest.json?battle=7")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["battle"]["n"], 7)
        self.assertEqual(p["queue"][0]["id"], "FD-7001")
        conn.close()

    def test_unknown_battle_404_over_http(self):
        conn, resp = self._get("/api/v2/retest.json?battle=9")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_bad_battle_422_over_http(self):
        conn, resp = self._get("/api/v2/retest.json?battle=xyz")
        self.assertEqual(resp.status, 422)
        conn.close()

    def test_unknown_v2_path_falls_through_404(self):
        conn, resp = self._get("/api/v2/nope")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_http_hits_readonly(self):
        before = dir_bytes(self.bdir)
        conn, resp = self._get("/api/v2/retest.json?battle=7")
        self.assertEqual(resp.status, 200)
        resp.read()
        conn.close()
        self.assertEqual(dir_bytes(self.bdir), before)


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "retest.html")
ZONE_MARKS = (
    # 顶部：任务选择 + 计数
    'id="battle-pick"', 'id="rt-counts"',
    # 队列表：发现/上次结果/距上次/客户反馈/立即复测
    'id="rq-table"', 'id="rq-body"', "上次结果", "距上次", "客户反馈", "立即复测",
    'class="btn-retest"',
    # 历史时间线：时间/结果/差异
    'id="rt-timeline"', "差异",
    # 四态（空/加载/错误含重试/正常）
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 复测触发方式（自动复测/手动）
    "自动复测",
    # 立即复测写入路由守卫降级（读面舰不建写入路由，在则用）
    "'/api/v2/finding/replay'",
    # 结果人话徽章（宪法#41）
    "未复现", "复现", "环境差异",
    # 宿主壳接入
    "RetestTab", "mode-tab",
)
FETCH_MARKS = ("'/api/v2/retest.json",)
COPY_BANNED = ("复测岗", "看战况", "管战场", "作战室", "琥珀线", "一键链")


class TestPageStructure(Base):
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
        self.assertIn("id: 'retest'", src)
        self.assertIn("group: '任务详情'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_250(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 250, "P5.5 页 ~280 行量纲")


if __name__ == "__main__":
    unittest.main()
