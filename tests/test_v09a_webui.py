# -*- coding: utf-8 -*-
"""v0.9a tanyin-web 观察面骨架——snapshot 只读快照 / SSE 追尾 / server 路由 / 首页 / CLI 入口。

python3 -m unittest tests.test_v09a_webui
法律（docs/design/tanyin-target-form.md §3）：纯 stdlib、3.9 兼容、观察面只读投影零写入。
"""
import json, os, re, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)
from ledger import core  # noqa: E402

from webui import snapshot as snap_mod  # noqa: E402
from webui import sse as sse_mod  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1, TS2, TS3 = "2026-10-11T01:00:00Z", "2026-10-11T01:05:00Z", "2026-10-11T01:10:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    """按 (ts, actor, phase, event) 铸 3 列链式 timeline 行（core.row_hash 同链法）。"""
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in rows_spec:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def build_mini_ledger(td):
    """mini 账本：goals（预算 1000;100;10）+budget 两行使用+timeline 3 行。"""
    gd = os.path.join(td, "G-w1")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-w1-0001", target="shop.example", objective="授权渗透：内网分区",
        budget="1000;100;10", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "budget.tsv"), [
        row("budget.tsv", timestamp=TS1, token_delta="100", requests_delta="10",
            hours_delta="0.5", scope="goal", note="P1 recon", schema_version="2"),
        row("budget.tsv", timestamp=TS2, token_delta="200", requests_delta="20",
            hours_delta="0.2", scope="goal", note="P2 matrix", schema_version="2")])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "gate-exit:P0 asserts=3 result=PASS"),
        (TS2, "总控", "P1", "gate-fail:P1 assert=converge-check reason=not-converged"),
        (TS3, "子代理", "P1", "add-fact F-w1-0001")]))
    return gd


def snap_dir_bytes(gd):
    out = {}
    for n in sorted(os.listdir(gd)):
        p = os.path.join(gd, n)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                out[n] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_mini_ledger(self.td.name)


class TestSnapshotV09a(Base):
    """T1：只读快照——phases 态 / budget 余量 / timeline 尾部事件（sha 前 8 位）。"""

    def test_snapshot_dict_shape(self):
        s = snap_mod.snapshot(self.gd, tail=3)
        self.assertIsInstance(s, dict)
        # phases 态：P0 过门 PASS、P1 失败 FAIL、其余 PENDING（cmd_status 同源）
        self.assertEqual(s["phases"]["P0"], "PASS")
        self.assertEqual(s["phases"]["P1"], "FAIL")
        for p in ("P2", "P3", "P4", "P5", "P5.5", "P6"):
            self.assertEqual(s["phases"][p], "PENDING", p)
        self.assertEqual(s["timeline_rows"], 3)
        # goal 卡片取首行
        self.assertEqual(s["goal"]["id"], "G-w1-0001")
        self.assertEqual(s["goal"]["target"], "shop.example")

    def test_budget_left(self):
        s = snap_mod.snapshot(self.gd, tail=3)
        b = s["budget"]
        # 限额 1000;100;10 − 使用 300;30;0.7 → 余量 700;70;9.3
        self.assertEqual(b["token"]["limit"], 1000.0)
        self.assertEqual(b["token"]["used"], 300.0)
        self.assertEqual(b["token"]["left"], 700.0)
        self.assertEqual(b["requests"]["left"], 70.0)
        self.assertAlmostEqual(b["hours"]["left"], 9.3)

    def test_tail_events_with_sha8(self):
        s = snap_mod.snapshot(self.gd, tail=3)
        evs = s["events"]
        self.assertEqual(len(evs), 3)
        rows = core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)
        for e, r in zip(evs, rows):
            self.assertEqual(e["ts"], r[0])
            self.assertEqual(e["actor"], r[1])
            self.assertEqual(e["phase"], r[2])
            self.assertEqual(e["event"], r[3])
            self.assertEqual(e["sha8"], r[6][:8])
            self.assertEqual(len(e["sha8"]), 8)
        self.assertEqual(evs[-1]["event"], "add-fact F-w1-0001")

    def test_readonly_projection(self):
        """投影律：snapshot 零写入——goal 目录字节不变。"""
        before = snap_dir_bytes(self.gd)
        snap_mod.snapshot(self.gd, tail=3)
        snap_mod.snapshot(self.gd, tail=1)
        self.assertEqual(snap_dir_bytes(self.gd), before)

    def test_json_serializable(self):
        s = snap_mod.snapshot(self.gd, tail=3)
        self.assertIsInstance(json.dumps(s, ensure_ascii=False), str)

    def test_empty_dir_tolerant(self):
        """账本未初始化目录不炸：空态可投影（观察面常驻）。"""
        empty = os.path.join(self.td.name, "G-empty")
        os.makedirs(empty)
        s = snap_mod.snapshot(empty, tail=3)
        self.assertEqual(s["phases"]["P0"], "PENDING")
        self.assertEqual(s["events"], [])
        self.assertEqual(s["budget"], {})
        self.assertIsNone(s["goal"])


class TestSSEV09a(Base):
    """T2：timeline 追尾生成器——存量尾部 burst + 增量轮询 + id 游标。"""

    def test_tail_then_follow(self):
        path = os.path.join(self.gd, "timeline.tsv")
        gen = sse_mod.events(path, start_tail=2, poll_interval=0.05)
        f1 = next(gen)
        self.assertTrue(f1.startswith("id: 2\n"), f1)      # 游标=1 起行号，尾部 2 条=行 2/3
        self.assertIn("data: ", f1)
        self.assertTrue(f1.endswith("\n\n"))               # SSE 帧分隔
        p1 = json.loads(f1.split("data: ", 1)[1].strip())
        self.assertEqual(p1["event"], "gate-fail:P1 assert=converge-check reason=not-converged")
        f2 = next(gen)
        self.assertTrue(f2.startswith("id: 3\n"), f2)
        # 追写 1 行（测试内写 fixture 副本）→ 下一次 next() 吐新行
        rows = core.read_tsv(path, 8)
        prev = rows[-1][6]
        wo = ["2026-10-11T01:15:00Z", "总控", "P1", "add-cred CRED-w1-0001", "", prev, "2"]
        rows.append(["2026-10-11T01:15:00Z", "总控", "P1", "add-cred CRED-w1-0001", "", prev,
                     core.row_hash(prev, wo), "2"])
        core.write_tsv(path, rows)
        f3 = next(gen)
        self.assertTrue(f3.startswith("id: 4\n"), f3)
        p3 = json.loads(f3.split("data: ", 1)[1].strip())
        self.assertEqual(p3["event"], "add-cred CRED-w1-0001")
        self.assertEqual(p3["sha8"], rows[-1][6][:8])
        gen.close()

    def test_stop_callable_ends_generator(self):
        """stop() 真即收尾：start_tail=0 无存量帧，StopIteration 干净退出。"""
        path = os.path.join(self.gd, "timeline.tsv")
        flags = iter([False, True])
        gen = sse_mod.events(path, start_tail=0, poll_interval=0.02,
                             stop=lambda: next(flags, True))
        self.assertEqual(list(gen), [])


class ServerBase(Base):
    """每测起临时端口 serve（daemon 线程），测毕 shutdown。"""

    def setUp(self):
        super().setUp()
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.gd,
                                       tail=3, poll_s=0.05, keepalive_s=1.0)
        self.port = self.srv.server_address[1]
        import threading
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop_server)

    def _stop_server(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()


class TestServerV09a(ServerBase):
    """T3：ThreadingHTTPServer 路由三分支（/ 静态页 / state.json / stream SSE）。"""

    def _get(self, path, timeout=5):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path)
        return conn, conn.getresponse()

    def test_index_html(self):
        conn, resp = self._get("/")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        body = resp.read().decode("utf-8")
        self.assertIn('id="dashboard"', body)
        conn.close()

    def test_state_json_keys(self):
        conn, resp = self._get("/api/state.json")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        data = json.loads(resp.read().decode("utf-8"))
        for k in ("goal", "phases", "budget", "events", "timeline_rows"):
            self.assertIn(k, data)
        self.assertEqual(data["phases"]["P0"], "PASS")
        self.assertEqual(data["budget"]["token"]["left"], 700.0)
        self.assertEqual(len(data["events"]), 3)
        conn.close()

    def test_stream_sse(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3.0)
        conn.request("GET", "/api/stream")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/event-stream"))
        self.assertEqual(resp.getheader("X-Accel-Buffering"), "no")
        seen_id = seen_data = False
        try:
            for _ in range(12):                       # 首帧（存量尾 3 条）应即刻可读；3 秒超时即断
                ln = resp.readline().decode("utf-8").rstrip("\n")
                if ln.startswith("id: "):
                    seen_id = True
                if ln.startswith("data: "):
                    seen_data = True
                if seen_id and seen_data:
                    break
        finally:
            conn.close()
        self.assertTrue(seen_id, "SSE 流未见 id: 行")
        self.assertTrue(seen_data, "SSE 流未见 data: 行")

    def test_404_unknown(self):
        conn, resp = self._get("/nope")
        self.assertEqual(resp.status, 404)
        conn.close()


INDEX_HTML = os.path.join(CLI, "webui", "static", "index.html")


class TestDashboardV09a(Base):
    """T4：手写仪表盘——战局灯/budget 条/活动流容器 + EventSource 直连 SSE。"""

    def test_has_containers_and_eventsource(self):
        src = open(INDEX_HTML, encoding="utf-8").read()
        self.assertIn('id="dashboard"', src)
        self.assertIn("EventSource('/api/stream')", src)
        for cid in ('id="phases"', 'id="budget"', 'id="feed"'):
            self.assertIn(cid, src, "缺容器 " + cid)

    def test_zero_framework_zero_cdn(self):
        """语言律：零框架零构建零 CDN（离线可用）。"""
        src = open(INDEX_HTML, encoding="utf-8").read()
        self.assertNotIn("<script src=", src)        # 无外链脚本
        self.assertNotIn("https://", src)            # 无 CDN/外域引用
        self.assertNotIn("http://", src)

    def test_js_under_2000_lines(self):
        src = open(INDEX_HTML, encoding="utf-8").read()
        n = src.count("<script>")
        self.assertGreaterEqual(n, 1)
        js = src.split("<script>")[1].split("</script>")[0]
        self.assertLess(len(js.splitlines()), 2000)  # 语言律：单页 JS<2000 行


class TestCLIEntryV09a(Base):
    """T5：CLI 入口——python -m 冒烟 rc=0；--port/--ledger-dir 透传；v0.7a bootstrap 装配。"""

    def test_m_help_smoke(self):
        import subprocess
        r = subprocess.run([sys.executable, "-m", "webui.server", "--help"],
                           cwd=CLI, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("--port", r.stdout)
        self.assertIn("--ledger-dir", r.stdout)

    def test_parse_args_passthrough(self):
        kv = srv_mod.parse_args(["--ledger-dir", "/tmp/g", "--port", "18777",
                                 "--tail=9", "--host", "0.0.0.0"])
        self.assertEqual(kv["ledger_dir"], "/tmp/g")
        self.assertEqual(kv["port"], 18777)
        self.assertEqual(kv["tail"], 9)
        self.assertEqual(kv["host"], "0.0.0.0")

    def test_parse_args_defaults_and_errors(self):
        kv = srv_mod.parse_args(["--ledger-dir=/x"])
        self.assertEqual(kv["port"], srv_mod.DEFAULT_PORT)
        self.assertEqual(kv["host"], srv_mod.DEFAULT_HOST)
        self.assertEqual(kv["tail"], srv_mod.DEFAULT_TAIL)
        self.assertIn("error", srv_mod.parse_args([]))              # 缺 --ledger-dir
        self.assertIn("error", srv_mod.parse_args(["--ledger-dir=/x", "--port=x"]))  # 坏端口

    def test_main_help_and_usage_rc(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            self.assertEqual(srv_mod.main(["webui.server", "--help"]), 0)
        self.assertIn("--ledger-dir", buf_o.getvalue())
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            self.assertEqual(srv_mod.main(["webui.server"]), 2)     # 缺参=用法错 rc=2

    def test_runtime_bootstrap_pattern(self):
        """v0.7a 同款装配：ledger.runtime bootstrap 单源（path+utf8）。"""
        src = open(os.path.join(CLI, "webui", "server.py"), encoding="utf-8").read()
        self.assertIn("from ledger.runtime import bootstrap", src)
        self.assertIn("bootstrap(__file__)", src)


# ---------------------------------------------------------------------------
# v0.9d 热修批（docs/research/liveui/walk-tanyin.md §三 一致性发现 1-5）
# 白名单内最小修：九门灯 P6.0 / 版本单源 / 导航同构 / favicon 消音 / --idle 变量
# / budget ≥80% 预警 / 活动流非法时间戳防御。
# ---------------------------------------------------------------------------

PHASES_YAML = os.path.join(HERE, "..", "phases", "phases.yaml")
STATUS_JS = os.path.join(CLI, "webui", "static", "status.js")
STATIC_PAGES = ("index.html", "coverage.html", "graph.html",
                "evidence.html", "metrics.html")
# v0.9d 八视图 nav（战局总览/活动流/会话/热图/十边图/证据卡/度量/实验）
# —— /activity /session /experiments 由后续舰落页，此处只钉全站同构。
NAV_WANT = {"/", "/activity", "/session", "/coverage", "/graph",
            "/evidence", "/metrics", "/experiments"}


def _page_src(name):
    with open(os.path.join(CLI, "webui", "static", name), encoding="utf-8") as f:
        return f.read()


class TestPhasesLampNineGates(unittest.TestCase):
    """热修1（v0.9d 随新结构更新）：九门单源挪入 status.js——门 id+中文名与
    phases.yaml states 全序 + gates.title 全等（首页 var PHASES 退位）。"""

    def test_status_js_gates_equal_yaml(self):
        with open(STATUS_JS, encoding="utf-8") as f:
            src = f.read()
        m = re.search(r"TY\.NINE_GATES\s*=\s*\[(.*?)\];", src, re.S)
        self.assertIsNotNone(m, "status.js 缺 NINE_GATES 表")
        got = re.findall(r'id:\s*"([^"]+)"\s*,\s*name:\s*"([^"]+)"', m.group(1))
        with open(PHASES_YAML, encoding="utf-8") as f:
            ytext = f.read()
        ym = re.search(r"^states:\s*\[([^\]]*)\]", ytext, re.M)
        self.assertIsNotNone(ym, "phases.yaml 缺 states 行")
        yml = [p.strip() for p in ym.group(1).split(",")]
        titles = dict(re.findall(r"^  (P[0-9.]+):\s*$\s*\n\s+title:\s*(\S+)",
                                 ytext, re.M))
        self.assertEqual([g[0] for g in got], yml,
                         "门全序漂移: %s vs %s" % (got, yml))
        self.assertEqual([g[1] for g in got],
                         [titles[i] for i in yml], "门中文名漂移")
        self.assertIn("P6.0", [g[0] for g in got], "清理门 P6.0 缺席")


class TestVersionSingleSource(unittest.TestCase):
    """热修2：五页版本号对齐 server banner——server_version 单源防漂移。"""

    def test_all_page_versions_match_server_banner(self):
        banner = srv_mod.Handler.server_version          # "tanyin-web/0.9c"
        want = "v" + banner.split("/", 1)[1]
        for name in STATIC_PAGES:
            src = _page_src(name)
            # 只对 title/footer 行的版本声明做单源断言（用户可见版本面；
            # JS 注释里的功能代号——如 metrics 页 v0.9d 小节标记——不算版本声明）
            lines = [ln for ln in src.splitlines()
                     if "<title>" in ln or "<footer" in ln]
            self.assertTrue(lines, name + " 无 title/footer 行")
            found = set()
            for ln in lines:
                found |= set(re.findall(r"v\d+\.\d+[a-z]\b", ln))
            self.assertTrue(found, name + " title/footer 无版本号可对齐")
            for v in found:
                self.assertEqual(v, want, name + " 版本漂移: " + v + " != " + want)


class TestNavConsistency(unittest.TestCase):
    """热修3：五页导航同构——总览/覆盖热图/十边图/证据卡/度量 全站同集。"""

    def test_all_pages_share_nav_set(self):
        for name in STATIC_PAGES:
            src = _page_src(name)
            m = re.search(r"<nav[^>]*>(.*?)</nav>", src, re.S)
            self.assertIsNotNone(m, name + " 缺 nav 块")
            got = set(re.findall(r'href="(/[^"]*)"', m.group(1)))
            self.assertEqual(got, NAV_WANT,
                             name + " 导航漂移: " + str(got ^ NAV_WANT))


class TestFaviconNo404(ServerBase):
    """热修3b：/favicon.ico 204 消音（服务端单点根治，五页零改动）。"""

    def _get(self, path, timeout=5):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path)
        return conn, conn.getresponse()

    def test_favicon_returns_204(self):
        conn, resp = self._get("/favicon.ico")
        self.assertEqual(resp.status, 204)
        self.assertEqual(resp.read(), b"")
        conn.close()


class TestCssVarParity(unittest.TestCase):
    """热修4（v0.9d 随新结构更新）：五页视觉单源变量表镜像齐——浅色 :root 与
    深色 html[data-theme=dark] 同名成对，--idle 在两主题都不缺。"""

    def test_idle_var_on_all_pages_both_themes(self):
        for name in STATIC_PAGES:
            src = _page_src(name)
            self.assertGreaterEqual(src.count("--idle:"), 2,
                                    name + " 浅/深主题 --idle 未成对")
            self.assertIn('html[data-theme="dark"]', src,
                          name + " 缺深色镜像块")


class TestBudgetWarnThreshold(unittest.TestCase):
    """热修5a：预算用量 ≥80% 预警——含 80.0 边界，条与数值同着 --bad。"""

    def test_threshold_ge_80_and_bad_color(self):
        src = _page_src("index.html")
        self.assertIn("pct >= 80", src, "阈值须为 ≥80（含边界）")
        self.assertIn(".bar-top .left-val.hot", src, "数值预警样式缺席")
        rule = src.split(".bar-top .left-val.hot")[1].split("}")[0]
        self.assertIn("color:var(--bad)", rule, "预警色未用 --bad")


class TestFeedTsDefense(unittest.TestCase):
    """热修5b：活动流时间戳防御——非法 ts 降级原文本+⚠着色，渲染零异常。"""

    def test_bad_ts_marked_and_guarded(self):
        src = _page_src("index.html")
        self.assertIn("function tsValid(", src, "缺时间戳校验函数")
        self.assertIn("isNaN(", src, "缺 Date 解析失败检测")
        self.assertIn("\u26a0", src, "缺 ⚠ 非法标记")
        self.assertIn("ts-bad", src, "非法时间戳未着预警 class")


if __name__ == "__main__":
    unittest.main()
