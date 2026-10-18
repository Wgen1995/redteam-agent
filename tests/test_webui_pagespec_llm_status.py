# -*- coding: utf-8 -*-
"""T7·模型状态页钉测（界面线施工计划 2026-10-18 续程④：多通道模型池只读面）。

python3 -m unittest tests.test_webui_pagespec_llm_status
律：投影只读零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN；本页无写路径
（只读观察面）；剩余秒=读取时刻计算（now 注入位——view 本体给定 now 输出
确定）。文案宪法#41（界面人话律）。

数据单源（spec §P8-P18 模型状态页）：
  通道配置 = 任务目录 channels.json（战士 --channels 同形；密钥永不上屏——
             只出「是否已配」布尔，SEC 钥不落页面律）；
  各道健康/熔断态/冷却剩时 = goal 目录 llmpool_state.json（llmpool_wire.attach
             钉根路径；hard=熔断、cooldown_end>now=冷却、否则健康）；
  故障转移事件 = timeline llmpool_wire 行（actor=llmpool，event=
             llm_failover k=v 负载——trip/recover）；
  判定参数 = ledger.llmpool 常量单源（阈值/冷却档/抖动——import 不复制）。

四层钉：
  ①投影层  llm_status_view——通道池（配置+健康+熔断+冷却剩时，密钥脱敏）+
           故障转移事件时间线（新者在前有界）+判定参数披露。
  ③挂载层  GET 过会话门；动态口真服过 HTTP 一例（线上也须无密钥）。
  ④页面层  static/pages/llm-status.html——通道池表+事件时间线+参数卡+四态
           +nav.push 自注册+零 CDN。
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
from ledger import llmpool as llmpool_mod          # noqa: E402
from webui import api_v2_llm_status as api         # noqa: E402
from webui import server as srv_mod                # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_lines(path, lines):
    _write(path, "\n".join(lines) + "\n")


def goal_row():
    return ("G-r2\trange.example.com\t全量测试\tauth.pdf\t" + "a" * 64 +
            "\t签名官\t2026-10-01T00:00:00Z\t2026-10-31T00:00:00Z\t"
            "600/10m\t08:00-20:00\t值班人\t100000;5000;40\t0\tzh\t"
            "业务背景\tstrong\tT2\t1\t2026-10-01T00:00:00Z")


CHANNELS = [{"name": "primary", "model": "model-a",
             "base_url": "http://127.0.0.1:9001/v1", "api_key": "sk-SECRET-KEY"},
            {"name": "backup", "model": "model-b",
             "base_url": "http://127.0.0.1:9002/v1", "api_key": ""}]

POOL_STATE = {"version": 1, "models": {
    "primary": {"soft_streak": 0, "rate_trips": 1, "server_trips": 1,
                "cooldown_end": 1030.0, "hard": False},
    "backup": {"soft_streak": 0, "rate_trips": 0, "server_trips": 2,
               "cooldown_end": 0.0, "hard": True},
    "spare": {"soft_streak": 1, "rate_trips": 0, "server_trips": 0,
              "cooldown_end": 0.0, "hard": False},
}}

TL_ROWS = [
    "2026-10-01T00:00:00Z\tCLI\tP0\tadd-goal G-r2\t\t\t\t1",
    "2026-10-01T00:10:00Z\tllmpool\tP-lifecycle\tllm_failover event=trip model=primary reason=http:500 lane=server cooldown_s=60\t\t\t\t1",
    "2026-10-01T00:20:00Z\tllmpool\tP-lifecycle\tllm_failover event=recover model=primary reason=success\t\t\t\t1",
    "2026-10-01T00:30:00Z\tllmpool\tP-lifecycle\tllm_failover event=trip model=backup reason=http:401 lane=None cooldown_s=None\t\t\t\t1",
    "2026-10-01T00:31:00Z\ttools\tP3\ttool-card-exec name=curl rc=0 tier=L1 rate=10/s\t\t\t\t1",
]


def build_fixture(root):
    b1 = os.path.join(root, "battle-1", "G-r2")
    _write_lines(os.path.join(b1, "goals.tsv"), [goal_row()])
    _write_lines(os.path.join(b1, "timeline.tsv"), TL_ROWS)
    _write(os.path.join(b1, "llmpool_state.json"),
           json.dumps(POOL_STATE, ensure_ascii=False))
    _write(os.path.join(os.path.join(root, "battle-1"), "channels.json"),
           json.dumps(CHANNELS, ensure_ascii=False))
    b2 = os.path.join(root, "battle-2", "G-r4")
    _write_lines(os.path.join(b2, "goals.tsv"),
                 [goal_row().replace("G-r2", "G-r4")])
    _write_lines(os.path.join(b2, "timeline.tsv"), [TL_ROWS[0]])
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
        kw.setdefault("now", 1000.0)
        return api.llm_status_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestLLMPoolProjection(Base):
    def test_channels_redacted(self):
        p = self.view(battle=1)
        flat = json.dumps(p, ensure_ascii=False)
        self.assertNotIn("sk-SECRET-KEY", flat)             # 密钥永不上屏
        self.assertNotIn('"api_key"', flat)                 # 原键不得出现（只许 api_key_set）
        for c in p["channels"]:
            self.assertNotIn("api_key", c)
        by = {c["name"]: c for c in p["channels"]}
        self.assertTrue(by["primary"]["api_key_set"])
        self.assertFalse(by["backup"]["api_key_set"])

    def test_channels_fields(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["channels"]}
        self.assertEqual(by["primary"]["model"], "model-a")
        self.assertEqual(by["primary"]["base_url"], "http://127.0.0.1:9001/v1")

    def test_cooling_remaining(self):
        p = self.view(battle=1)                              # now=1000，窗到 1030
        by = {c["name"]: c for c in p["channels"]}
        self.assertEqual(by["primary"]["state"], "cooling")
        self.assertEqual(by["primary"]["remaining_s"], 30)

    def test_hard_tripped_no_auto_recover(self):
        p = self.view(battle=1)
        by = {c["name"]: c for c in p["channels"]}
        self.assertEqual(by["backup"]["state"], "tripped")
        self.assertIsNone(by["backup"]["remaining_s"])      # 硬熔断无自动恢复

    def test_state_only_model_listed(self):
        p = self.view(battle=1)
        names = [c["name"] for c in p["channels"]]
        self.assertEqual(names, ["primary", "backup", "spare"])  # 配置序+状态在册
        spare = p["channels"][2]
        self.assertFalse(spare["configured"])               # 配置未见但状态在册
        self.assertEqual(spare["state"], "healthy")

    def test_pool_counts(self):
        p = self.view(battle=1)
        self.assertEqual(p["counts"]["healthy"], 1)
        self.assertEqual(p["counts"]["cooling"], 1)
        self.assertEqual(p["counts"]["tripped"], 1)
        self.assertEqual(p["counts"]["channels_configured"], 2)

    def test_failover_events_newest_first(self):
        p = self.view(battle=1)
        ev = p["events"]
        self.assertEqual(len(ev), 3)                         # 工具行不入事件线
        self.assertEqual(ev[0]["payload"]["model"], "backup")
        self.assertEqual(ev[1]["payload"]["event"], "recover")
        self.assertEqual(ev[2]["payload"]["lane"], "server")

    def test_event_payload_types(self):
        p = self.view(battle=1)
        trip = p["events"][2]
        self.assertEqual(trip["payload"]["cooldown_s"], 60)  # 数值型负载
        self.assertEqual(trip["payload"]["reason"], "http:500")
        hard = p["events"][0]
        self.assertIsNone(hard["payload"]["lane"])           # lane=None 照印为 None
        self.assertIn("row", hard)

    def test_pool_constants_single_source(self):
        p = self.view(battle=1)
        c = p["params"]
        self.assertEqual(c["soft_trip_threshold"],
                         llmpool_mod.SOFT_TRIP_THRESHOLD)    # 常量 import 单源
        self.assertEqual(c["rate_cooldown_s"], llmpool_mod.RATE_COOLDOWN_S)
        self.assertEqual(c["server_ladder_s"], list(llmpool_mod.LADDER_S))
        self.assertEqual(c["jitter"], llmpool_mod.JITTER)

    def test_no_state_no_channels_honest(self):
        p = self.view(battle=2)
        self.assertEqual(p["channels"], [])
        self.assertEqual(p["counts"]["channels_configured"], 0)
        flat = json.dumps(p, ensure_ascii=False)
        self.assertIn("未发现", flat)                        # 诚实空态说明
        self.assertIn("启动参数", flat)

    def test_corrupt_state_treated_empty(self):
        gd = os.path.join(self.root, "battle-2", "G-r4")
        _write(os.path.join(gd, "llmpool_state.json"), "{corrupt json")
        p = self.view(battle=2)
        self.assertEqual(p["channels"], [])                  # corrupt=全新（池同律）

    def test_bad_battle_valueerror(self):
        with self.assertRaises(ValueError):
            self.view(battle="x")

    def test_readonly_deterministic_given_now(self):
        before = dir_bytes(self.td.name)
        a = self.view(battle=1)
        b = self.view(battle=1)
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
    """动态口真服（禁碰 8900）：会话门+读一例（线上也须无密钥）。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.gd = os.path.join(cls.td.name, "G-live")
        _write_lines(os.path.join(cls.gd, "goals.tsv"), [goal_row()])
        _write_lines(os.path.join(cls.gd, "timeline.tsv"), [
            TL_ROWS[0],
            "2026-10-01T00:10:00Z\tllmpool\tP-lifecycle\tllm_failover event=trip model=a reason=http:500 lane=server cooldown_s=60\t\t\t\t1",
        ])
        _write(os.path.join(cls.gd, "llmpool_state.json"),
               json.dumps({"version": 1, "models": {
                   "a": {"soft_streak": 0, "rate_trips": 0, "server_trips": 1,
                         "cooldown_end": 2000000000.0, "hard": False}}}))
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
        conn, resp = self._req("/api/v2/llm-status.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_get_over_http_no_secret(self):
        conn, resp = self._req("/api/v2/llm-status.json")
        self.assertEqual(resp.status, 200)
        body = resp.read().decode("utf-8")
        p = json.loads(body)
        self.assertEqual(p["events"][0]["payload"]["model"], "a")
        self.assertEqual(p["channels"][0]["state"], "cooling")   # 主账本回落面
        self.assertNotIn('"api_key"', body)                    # 原键不得上 wire
        conn.close()

    def test_no_post_surface(self):
        self.assertEqual(api.POST_ROUTES, {})                # 只读页零写路由


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "llm-status.html")
ZONE_MARKS = (
    # 通道池（配置/健康/熔断态/冷却剩时）
    'id="ls-channels"', "通道", "模型", "密钥", "健康状态", "冷却剩余",
    # 故障转移事件时间线 + 判定参数
    'id="ls-events"', 'id="ls-params"',
    # 四态
    'id="st-loading"', 'id="st-error"', 'id="btn-retry"', 'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/llm-status.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场", "战士", "开战",
               "道池")


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
        self.assertIn("id: 'llm-status'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 200, "模型状态页量纲")


if __name__ == "__main__":
    unittest.main()
