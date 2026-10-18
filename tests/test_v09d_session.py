# -*- coding: utf-8 -*-
"""v0.9d Ship S · 会话页只读版（计划 docs/superpowers/plans/2026-10-15-v09d-ui.md Ship S 节）。

python3 -m unittest tests.test_v09d_session -v
律（docs/design/tanyin-target-form.md §1/§3 + 计划纪律节）：TDD 红绿、只读投影零写入、
Python 3.9 纯 stdlib、前端零框架零 CDN、单页 JS<2000 行。

覆盖面（计划原文：路由 200+JSON 键+页面节点+只读律字节不变钉）：
- session_view 装配：transcript 投影（battle 目录 opencode 运行日志，trace_search 同源
  文件名）+ runner 生命周期事件 + timeline 介入/注入事件穿插（PROGRESS 计数锚定）；
- 工具卡三态：调用(→)/命令($)/失败(✗+Error)，配对与归块规则见模块 docstring；
- server 路由：/session 页 + /api/session.json（无参=最新战，?battle=N 选战，坏参 404）；
- 版本 bump 0.9c→0.9d（server_version 单源；五页旧断言由换肤舰统一收口）。
"""
import json, os, re, tempfile, threading, unittest
import http.client

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)

from ledger import session_view as sv  # noqa: E402
from webui import server as srv_mod  # noqa: E402

ESC = "\x1b[0m"

# --- 夹具：battles 根下 battle-7（全要素）+ battle-8（空壳=最新战） -----------------


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _tl(ts, actor, phase, event):
    return "\t".join([ts, actor, phase, event, "", "0" * 64, "f" * 64, "2"])


LOG_TEXT = "".join([
    ESC + "\n",
    "> build · glm-5.3\n",
    "开场白第一轮。\n",
    "\n",
    "$ echo hi\n",
    "hi\n",
    ESC + "→ Read mission.txt\n",
    "读完了，开始计划。\n",
    "✗ Read missing.md failed\n",
    "Error: File not found: missing.md\n",
    "失败后的自述。\n",
    "> build · glm-5.3\n",
    "第二轮开始。\n",
    "$ echo two\n",
    "two\n",
    "收尾陈述。\n",
])

RUNNER_TSV = (
    "2026-10-11T10:00:00\tBOOT\tcwd=/x max_restarts=5\n"
    "2026-10-11T10:00:01\tLAUNCH\tpid=1 (first prompt)\n"
    "2026-10-11T10:00:02\tPROGRESS\tlog=10B timeline=3\n"
    "2026-10-11T10:05:00\tDIRECTIVE\tdigest=abc len=120\n"
    "2026-10-11T10:05:01\tRESTART\tpid=2 n=1 (directive)\n"
    "2026-10-11T10:05:02\tPROGRESS\tlog=20B timeline=5\n"
    "2026-10-11T10:10:00\tEXIT\trc=0 after progress complete=True\n"
    "2026-10-11T10:10:01\tDONE\tfinal_rc=0 restarts=1 timeline=5\n"
)

TIMELINE_TSV = "\n".join([
    _tl("2026-11-08T08:00:00Z", "CLI", "P0", "add-goal G-7-0001"),
    _tl("2026-11-08T08:03:00Z", "总控", "P0", "gate-exit:P0 asserts=3 result=PASS"),
    _tl("2026-11-08T08:30:00Z", "CLI", "P1", "add-finding FD-7-0001"),
    _tl("2026-11-08T09:00:00Z", "canary", "P0", "canary-deploy n=5 seed=42"),
    _tl("2026-11-08T09:10:00Z", "replay", "P1", "replay-probe EV-7-0001 verdict=reproduced"),
]) + "\n"


def build_battles(root):
    """造 battles 根：battle-7 全要素 / battle-8 空壳（只有 mission）。返回 battles 根。"""
    bdir = os.path.join(root, "battles")
    b7 = os.path.join(bdir, "battle-7")
    os.makedirs(os.path.join(b7, "G-g7"))
    os.makedirs(os.path.join(bdir, "battle-8"))
    _write(os.path.join(b7, "mission.txt"), "任务说明文本\n第二行\n")
    _write(os.path.join(b7, "directive.txt"), "x" * 120)
    _write(os.path.join(b7, "settle-report.txt"),
           "verify-chain：PASS\nrecall=0.50 (2/4)\nMISSING\tgt-1\nMISSING\tgt-2\n")
    _write(os.path.join(b7, "opencode-run.log"), LOG_TEXT)
    _write(os.path.join(b7, "opencode-run.log.runner.tsv"), RUNNER_TSV)
    _write(os.path.join(b7, "G-g7", "timeline.tsv"), TIMELINE_TSV)
    _write(os.path.join(bdir, "battle-8", "mission.txt"), "空壳战\n")
    os.makedirs(os.path.join(bdir, "op-1"))          # 非 battle-N 杂项目录
    return bdir


def tree_bytes(path):
    out = {}
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        for n in sorted(filenames):
            p = os.path.join(dirpath, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, path)] = f.read()
    return out


class FixtureBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.bdir = build_battles(self.td.name)
        self.b7 = os.path.join(self.bdir, "battle-7")


class TestParseTranscript(FixtureBase):
    """transcript 投影：ANSI 剥净/轮分隔/工具卡三态配对/文本块归位。"""

    def test_rounds_tools_texts(self):
        doc = sv.parse_transcript(LOG_TEXT)
        self.assertEqual(len(doc), 2)
        r1, r2 = doc
        self.assertEqual(r1["head"], "> build · glm-5.3")
        kinds = [e["kind"] for e in r1["entries"]]
        self.assertEqual(kinds, ["text", "tool", "tool", "text", "tool", "text"])
        bash = r1["entries"][1]
        self.assertEqual(bash["state"], "bash")
        self.assertEqual(bash["cmd"], "echo hi")
        self.assertEqual(bash["output"], ["hi"])
        ok = r1["entries"][2]
        self.assertEqual(ok["state"], "ok")
        self.assertEqual(ok["tool"], "Read")
        self.assertEqual(ok["title"], "Read mission.txt")
        self.assertEqual(ok["output"], [])                  # → 调用卡不吞正文
        self.assertEqual(r1["entries"][3]["lines"], ["读完了，开始计划。"])
        err = r1["entries"][4]
        self.assertEqual(err["state"], "error")
        self.assertEqual(err["tool"], "Read")
        self.assertEqual(err["output"], ["Error: File not found: missing.md"])
        self.assertEqual(r1["entries"][5]["lines"], ["失败后的自述。"])
        self.assertEqual(r2["entries"][1]["cmd"], "echo two")
        self.assertEqual(r2["entries"][1]["output"], ["two", "收尾陈述。"])  # $ 卡吞至下标记

    def test_ansi_stripped_everywhere(self):
        for rnd in sv.parse_transcript(LOG_TEXT):
            blob = json.dumps(rnd, ensure_ascii=False)
            self.assertNotIn(chr(27), blob)             # 任何字段不含 ESC 控制符
            for e in rnd["entries"]:
                for v in ([e.get("title", ""), e.get("cmd", "")]
                          + e.get("output", []) + e.get("lines", [])):
                    self.assertNotIn(chr(27), v)


class TestSessionView(FixtureBase):
    """session_view 装配：meta+穿插事件+stats+只读律+确定性+空容错。"""

    def test_battle_meta(self):
        doc = sv.session_view(self.b7)
        self.assertEqual(doc["battle"]["id"], "battle-7")
        self.assertEqual(doc["battle"]["n"], 7)
        self.assertEqual(doc["battle"]["mission"], "任务说明文本\n第二行\n")
        self.assertEqual(doc["battle"]["directive_bytes"], 120)
        self.assertEqual(doc["battle"]["gen"], "G-g7")
        st = doc["battle"]["settle"]
        self.assertEqual(st["chain"], "PASS")
        self.assertEqual(st["recall"], 0.5)
        self.assertEqual(st["hits"], 2)
        self.assertEqual(st["total"], 4)

    def test_runner_lifecycle_listed(self):
        doc = sv.session_view(self.b7)
        self.assertEqual([r["kind"] for r in doc["runner"]],
                         ["BOOT", "LAUNCH", "PROGRESS", "DIRECTIVE", "RESTART",
                          "PROGRESS", "EXIT", "DONE"])
        self.assertEqual(doc["runner"][0]["ts"], "2026-10-11T10:00:00")

    def test_events_interleaved(self):
        """runner 事件按段锚轮尾（BOOT 头锚）；timeline 介入按 PROGRESS 计数锚轮尾。"""
        doc = sv.session_view(self.b7)
        r1, r2 = doc["rounds"]
        ev1 = [e for e in r1["entries"] if e["kind"] == "event"]
        # BOOT 头锚 round1 首条；DIRECTIVE（段1）+总控 row2（PROGRESS timeline=3 覆盖）尾锚
        self.assertEqual(ev1[0]["source"], "runner")
        self.assertEqual(ev1[0]["event_kind"], "BOOT")
        tail1 = [(e["source"], e.get("event_kind") or e.get("actor")) for e in ev1[1:]]
        self.assertEqual(tail1, [("runner", "DIRECTIVE"), ("timeline", "总控")])
        ev2 = [e for e in r2["entries"] if e["kind"] == "event"]
        tail2 = [(e["source"], e.get("event_kind") or e.get("actor")) for e in ev2]
        # EXIT/DONE（段2）+canary row4（PROGRESS timeline=5 首覆盖）
        self.assertEqual(tail2, [("runner", "EXIT"), ("runner", "DONE"),
                                 ("timeline", "canary")])
        tl_ev = [e for e in ev1 + ev2 if e["source"] == "timeline"]
        self.assertEqual(tl_ev[0]["row"], 2)
        self.assertEqual(tl_ev[0]["event"], "gate-exit:P0 asserts=3 result=PASS")
        self.assertEqual(tl_ev[1]["row"], 4)

    def test_timeline_interventions_flat(self):
        doc = sv.session_view(self.b7)
        flat = doc["timeline_interventions"]
        self.assertEqual([(e["row"], e["actor"]) for e in flat],
                         [(2, "总控"), (4, "canary")])     # CLI/replay 不算介入

    def test_stats(self):
        st = sv.session_view(self.b7)["stats"]
        self.assertEqual(st["rounds"], 2)
        self.assertEqual(st["tools"], 4)        # ok1+error1+bash2（两轮合计）
        self.assertEqual(st["bash"], 2)
        self.assertEqual(st["errors"], 1)
        self.assertEqual(st["texts"], 4)
        self.assertEqual(st["interventions"], 6)  # BOOT/DIRECTIVE/EXIT/DONE+2 timeline
        self.assertEqual(st["lines"], 16)

    def test_readonly_bytes_unchanged(self):
        before = tree_bytes(self.b7)
        sv.session_view(self.b7)
        sv.list_battles(self.bdir)
        self.assertEqual(tree_bytes(self.b7), before)

    def test_deterministic_json(self):
        a, b = sv.session_view(self.b7), sv.session_view(self.b7)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_empty_battle_tolerant(self):
        b8 = os.path.join(self.bdir, "battle-8")
        doc = sv.session_view(b8)
        self.assertEqual(doc["rounds"], [])
        self.assertEqual(doc["runner"], [])
        self.assertEqual(doc["timeline_interventions"], [])
        self.assertIsNone(doc["battle"]["settle"])
        self.assertEqual(doc["stats"]["rounds"], 0)
        self.assertEqual(doc["stats"]["lines"], 0)

    def test_missing_dir_empty_shape(self):
        doc = sv.session_view(os.path.join(self.bdir, "battle-404"))
        self.assertIsNone(doc["battle"])             # 目录不存在=空 shape（battle:None）
        self.assertEqual(doc["rounds"], [])


class TestSessionApi(FixtureBase):
    """session_api：battles 根+战号注入（可测装配）；无参=最新；坏参降级。"""

    def test_latest_and_pick(self):
        doc = sv.session_api(battles_dir=self.bdir)
        self.assertEqual(doc["battle"]["id"], "battle-8")     # 最新=8
        doc7 = sv.session_api(battles_dir=self.bdir, battle=7)
        self.assertEqual(doc7["battle"]["id"], "battle-7")
        self.assertEqual(len(doc7["rounds"]), 2)

    def test_battles_listing(self):
        self.assertEqual(sv.list_battles(self.bdir),
                         [{"id": "battle-7", "n": 7}, {"id": "battle-8", "n": 8}])

    def test_missing_battle_error_shape(self):
        doc = sv.session_api(battles_dir=self.bdir, battle=99)
        self.assertIn("error", doc)
        self.assertEqual([b["id"] for b in doc["battles"]], ["battle-7", "battle-8"])

    def test_bad_battle_raises(self):
        with self.assertRaises(ValueError):
            sv.session_api(battles_dir=self.bdir, battle="abc")

    def test_no_battles_dir(self):
        doc = sv.session_api(battles_dir=os.path.join(self.td.name, "nope"))
        self.assertIsNone(doc["battle"])
        self.assertEqual(doc["battles"], [])


class ServerBase(FixtureBase):
    def setUp(self):
        super().setUp()
        self._old_home = os.environ.get("TANYIN_HOME")
        os.environ["TANYIN_HOME"] = self.td.name       # battles 根注入（metrics 同款）
        from tests import webui_login
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.td.name,
                                       tail=3, poll_s=0.05, keepalive_s=1.0,
                                       operator_key=webui_login.OP_KEY)
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)
        self.sid = webui_login.login(self.port)   # B舰 P0 后：读面须会话

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()
        if self._old_home is None:
            os.environ.pop("TANYIN_HOME", None)
        else:
            os.environ["TANYIN_HOME"] = self._old_home

    def _get(self, path, timeout=5):
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path, headers=webui_login.cookie(self.sid))
        return conn, conn.getresponse()


class TestServerRoutesV09d(ServerBase):
    """/session 页 + /api/session.json（无参最新/?battle= 选战/坏参 404）+ 只读律。"""

    def test_session_page(self):
        conn, resp = self._get("/session")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        body = resp.read().decode("utf-8")
        for mark in ('id="rounds"', 'id="picker"', "<details", "<summary"):
            self.assertIn(mark, body, mark)
        conn.close()

    def test_api_session_json_latest(self):
        conn, resp = self._get("/api/session.json")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        doc = json.loads(resp.read().decode("utf-8"))
        conn.close()
        for k in ("battle", "rounds", "runner", "stats", "timeline_interventions",
                  "battles", "server_version"):
            self.assertIn(k, doc, k)
        self.assertEqual(doc["battle"]["id"], "battle-8")
        self.assertEqual(doc["server_version"], srv_mod.Handler.server_version)

    def test_api_session_battle_query(self):
        conn, resp = self._get("/api/session.json?battle=7")
        doc = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual(doc["battle"]["id"], "battle-7")
        self.assertEqual(doc["stats"]["rounds"], 2)

    def test_api_session_battle_404(self):
        for q in ("?battle=999", "?battle=abc"):
            conn, resp = self._get("/api/session.json" + q)
            self.assertEqual(resp.status, 404, q)
            self.assertIn("error", json.loads(resp.read().decode("utf-8")))
            conn.close()

    def test_api_hits_readonly(self):
        before = tree_bytes(self.b7)
        for p in ("/api/session.json", "/api/session.json?battle=7"):
            conn, resp = self._get(p)
            self.assertEqual(resp.status, 200, p)
            resp.read()
            conn.close()
        self.assertEqual(tree_bytes(self.b7), before)

    def test_version_bumped_09d(self):
        self.assertEqual(srv_mod.Handler.server_version, "tanyin-web/0.9d")


STATIC = os.path.join(CLI, "webui", "static")
PAGE = "session.html"


class TestPageSourceV09d(unittest.TestCase):
    """会话页源码律：拉取面/四态节点/三态折叠原生 details/零框架零 CDN/JS 行数/版本单源。"""

    @staticmethod
    def _src():
        with open(os.path.join(STATIC, PAGE), encoding="utf-8") as f:
            return f.read()

    def test_fetch_and_nodes(self):
        src = self._src()
        self.assertIn("/api/session.json", src)
        for mark in ('id="rounds"', 'id="picker"', 'id="stats"', 'id="meta"',
                     'id="retry"', 'id="legend"',
                     'skeleton sk-a', 'data-state="loading"',
                     'data-state="empty"', 'data-state="error"'):
            self.assertIn(mark, src, mark)
        self.assertIn("<details", src)                  # 三态折叠=原生 details/summary
        self.assertIn("<summary", src)
        self.assertIn("textContent", src)               # 防注入纪律
        self.assertIn("你在看什么", src)                 # 人话律副题

    def test_three_state_badges(self):
        src = self._src()
        for mark in ("s-ok", "s-bash", "s-error"):
            self.assertIn(mark, src, mark)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        # v0.9d 收口批（E3 F2）：唯一外链=/status.js（server 字节级伺服）
        self.assertEqual(src.count('<script src="/status.js"></script>'), 1)
        self.assertEqual(src.count("<script src="), 1, "只许 status.js 一支外链")
        self.assertNotIn("https://", src)
        self.assertNotIn("http://", src.replace("http://www.w3.org", ""))

    def test_js_under_2000_lines(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)

    def test_footer_version_single_source(self):
        banner = srv_mod.Handler.server_version
        want = "v" + banner.split("/", 1)[1]
        src = self._src()
        lines = [ln for ln in src.splitlines() if "<title>" in ln or "<footer" in ln]
        self.assertTrue(lines, "session.html 无 title/footer 行")
        found = set()
        for ln in lines:
            found |= set(re.findall(r"v\d+\.\d+[a-z]\b", ln))
        self.assertTrue(found, "session.html title/footer 无版本号可对齐")
        for v in found:
            self.assertEqual(v, want, "session.html 版本漂移: " + v + " != " + want)


class TestServerRoutesAppendV09d(ServerBase):
    """父舰追加集成：/activity 活动流独立页 + /experiments 302（nav 八链补全）。"""  # noqa

    def test_activity_page(self):
        conn, resp = self._get("/activity")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        body = resp.read().decode("utf-8")
        for mark in ('id="feed"', 'id="feed-box"', "EventSource"):
            self.assertIn(mark, body, mark)
        conn.close()

    def test_experiments_redirect(self):
        conn, resp = self._get("/experiments")
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.getheader("Location"), "/metrics#experiments")
        resp.read()
        conn.close()

    def test_status_js_route(self):
        """E3 评审：/status.js 白名单句柄——仅此一文件出 static，application/javascript。"""
        conn, resp = self._get("/status.js")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type")
                        .startswith("application/javascript"))
        body = resp.read()
        conn.close()
        with open(os.path.join(STATIC, "status.js"), "rb") as f:
            self.assertEqual(body, f.read(), "/status.js 须字节级伺服单源文件")

    def test_static_whitelist_only_status_js(self):
        """白名单律：除 /status.js 外，static 目录其余文件不可经根路径直取。"""
        for path in ("/session.html", "/index.html", "/status.js.bak"):
            conn, resp = self._get(path)
            self.assertEqual(resp.status, 404, path)
            resp.read()
            conn.close()


class TestActivityPageSourceV09d(unittest.TestCase):
    """活动流独立页源码律：四态/时间戳防御/零框架零 CDN/nav 八链/版本单源。"""

    @staticmethod
    def _src():
        with open(os.path.join(STATIC, "activity.html"), encoding="utf-8") as f:
            return f.read()

    def test_nodes(self):
        src = self._src()
        for mark in ('id="feed"', 'id="feed-box"', 'id="sse-state"',
                     "EventSource", "tsValid", "<footer"):
            self.assertIn(mark, src, mark)

    def test_nav_eight_links(self):
        # 用户实逛反馈批（2026-10-19）：导航拍平=主入口 7 链+页面总目 13 链
        want_nav = {"/", "/evidence", "/p/tasks", "/p/new-task", "/p/techniques",
                    "/p/broadcast", "/p/report-center", "/activity", "/session",
                    "/graph", "/metrics", "/coverage", "/p/retest",
                    "/p/approval-center", "/p/asset-registry", "/p/assets",
                    "/p/coverage", "/p/capability", "/console", "/p/settings"}
        for name in ("session.html", "activity.html"):
            with open(os.path.join(STATIC, name), encoding="utf-8") as f:
                src = f.read()
            m = re.search(r"<nav[^>]*>(.*?)</nav>", src, re.S)
            self.assertIsNotNone(m, name + " 缺 nav 块")
            got = set(re.findall(r'href="(/[^"#?]*)"', m.group(1)))
            self.assertEqual(got, want_nav, name + " 导航漂移: " + str(got))

    def test_uses_external_status_js(self):
        """E3 评审：activity.html 外链 /status.js 单源（不再字节内嵌，新进程有该路由）。"""
        src = self._src()
        self.assertIn('<script src="/status.js"></script>', src)
        self.assertNotIn("/* STATUS-JS:BEGIN */", src, "activity.html 不得再内嵌副本")

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        # 唯一例外：同源 /status.js（E3 评审裁定可外链）；其余零外链零 CDN 零外域
        self.assertEqual(src.count("<script src="), 1)
        self.assertIn('src="/status.js"', src)
        self.assertNotIn("https://", src)
        self.assertNotIn("http://", src.replace("http://www.w3.org", ""))

    def test_js_under_2000_lines(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)

    def test_footer_version_single_source(self):
        banner = srv_mod.Handler.server_version
        want = "v" + banner.split("/", 1)[1]
        src = self._src()
        lines = [ln for ln in src.splitlines() if "<title>" in ln or "<footer" in ln]
        self.assertTrue(lines, "activity.html 无 title/footer 行")
        found = set()
        for ln in lines:
            found |= set(re.findall(r"v\d+\.\d+[a-z]\b", ln))
        self.assertTrue(found, "activity.html title/footer 无版本号可对齐")
        for v in found:
            self.assertEqual(v, want, "activity.html 版本漂移: " + v + " != " + want)


class TestFivePageVersionBump(unittest.TestCase):
    """旧皮肤四页版本串行级随 server bump（title/footer 行内 0.9c→0.9d；v09a 单源钉同验）。
    R64: 随49b1619 IA v2移除 index.html 出版本对齐（GL-DS v1 新面 title/footer
    不带版本号，版本唯一单源=server banner）。"""

    def test_five_pages_match_server_banner(self):
        banner = srv_mod.Handler.server_version
        want = "v" + banner.split("/", 1)[1]
        for name in ("coverage.html", "graph.html",
                     "evidence.html", "metrics.html"):
            with open(os.path.join(STATIC, name), encoding="utf-8") as f:
                src = f.read()
            lines = [ln for ln in src.splitlines()
                     if "<title>" in ln or "<footer" in ln]
            self.assertTrue(lines, name + " 无 title/footer 行")
            found = set()
            for ln in lines:
                found |= set(re.findall(r"v\d+\.\d+[a-z]\b", ln))
            self.assertTrue(found, name + " title/footer 无版本号可对齐")
            for v in found:
                self.assertEqual(v, want, name + " 版本漂移: " + v + " != " + want)


if __name__ == "__main__":
    unittest.main()
