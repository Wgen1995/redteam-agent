# -*- coding: utf-8 -*-
"""LLM 录制页（模型对话记录）——三层钉测（界面线 2026-10-18 补给件）。

python3 -m unittest tests.test_webui_pagespec_llm_recordings -v
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
数据单源：cli/warrior/transcript.py 写的 <goal_dir>/transcripts/<INT>.jsonl
（行结构 ts/battle/warrior/intent/turn/model/role/content[+usage]，append-only，
跨重启续写）——本投影只读不写；文案宪法#41（界面人话律）：屏上禁内部代号。

三层钉：
  ①投影层  api_v2_llm.list_transcripts/transcript_detail——列表（意图/模型道/
           token 耗）+ 详情（请求/响应原始对，mono 原文）单源过滤投影；
  ②挂载层  api_pages.py 未落地（UI-1 在飞）——以 Handler 子类钉 include 挂法：
           /api/v2/* 全过会话门（无 cookie=401 JSON），分发 ROUTES 单源表；
  ③页面层  static/pages/llm-recordings.html 结构钉（列表/详情双栏+四态+
           nav.push 自注册+零 CDN）。
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
from webui import api_v2_llm as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402
from warrior.transcript import Transcript  # noqa: E402

T = core.TABLES
PAGE = os.path.join(CLI, "webui", "static", "pages", "llm-recordings.html")

TS1 = "2026-10-18T01:00:00Z"
TS2 = "2026-10-18T01:01:00Z"
TS3 = "2026-10-18T01:02:00Z"
TS4 = "2026-10-18T01:03:00Z"
TS5 = "2026-10-18T01:04:00Z"
TS6 = "2026-10-18T01:05:00Z"
TS9 = "2026-10-18T05:00:00Z"


def _intent_row(iid, title):
    r = [""] * len(T["intents.tsv"])
    r[T["intents.tsv"].index("id")] = iid
    r[T["intents.tsv"].index("title")] = title
    r[T["intents.tsv"].index("status")] = "done"
    r[T["intents.tsv"].index("schema_version")] = "2"
    r[T["intents.tsv"].index("created")] = TS1
    return r


def _tr_line(intent, turn, role, model, content, ts, usage=None):
    row = {"ts": ts, "battle": "G-t1", "warrior": "W-1", "intent": intent,
           "turn": turn, "model": model, "role": role, "content": content}
    if usage is not None:
        row["usage"] = usage
    return json.dumps(row, ensure_ascii=False)


def build_fixture(td):
    """夹具：3 个录制意图（1 个不在 intents.tsv）+ 垃圾文件混入。"""
    gd = os.path.join(td, "G-t1")
    os.makedirs(os.path.join(gd, "transcripts"))
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        _intent_row("INT-t1-0001", "侦察 shop.example 子域"),
        _intent_row("INT-t1-0002", "登录口令猜测（未跑模型，无录制）"),
        _intent_row("INT-t1-0003", "管理面板路径探测"),
    ])
    p1 = os.path.join(gd, "transcripts", "INT-t1-0001.jsonl")
    with open(p1, "w", encoding="utf-8", newline="\n") as f:
        f.write(_tr_line("INT-t1-0001", 1, "user", "m1",
                         "上下文+指令：枚举子域", TS1) + "\n")
        f.write(_tr_line("INT-t1-0001", 1, "assistant", "m1",
                         '{"op":"dig","q":"shop.example"}', TS2,
                         {"prompt_tokens": 100, "completion_tokens": 10}) + "\n")
        f.write(_tr_line("INT-t1-0001", 2, "user", "m1",
                         "工具结果：3 条 A 记录", TS3) + "\n")
        f.write(_tr_line("INT-t1-0001", 2, "assistant", "m1",
                         '{"op":"done","reason":"枚举完成"}', TS4,
                         {"prompt_tokens": 120, "completion_tokens": 8}) + "\n")
        f.write(_tr_line("INT-t1-0001", 3, "user", "m2",
                         "复查一遍", TS5) + "\n")
        f.write(_tr_line("INT-t1-0001", 3, "assistant", "m2",
                         '{"op":"done","reason":"确认"}', TS6,
                         {"prompt_tokens": 30, "completion_tokens": 5}) + "\n")
    p3 = os.path.join(gd, "transcripts", "INT-t1-0003.jsonl")
    with open(p3, "w", encoding="utf-8", newline="\n") as f:
        f.write("这不是 JSON 行（模拟写坏）\n")
        f.write(_tr_line("INT-t1-0003", 1, "user", "m3",
                         "探测 /admin", TS1) + "\n")
        f.write(_tr_line("INT-t1-0003", 1, "assistant", "m3",
                         "200 OK", TS2) + "\n")      # 无 usage（旧档如实）
    p9 = os.path.join(gd, "transcripts", "INT-t1-0009.jsonl")
    with open(p9, "w", encoding="utf-8", newline="\n") as f:
        f.write(_tr_line("INT-t1-0009", 1, "user", "m1",
                         "手工补录", TS9) + "\n")
    with open(os.path.join(gd, "transcripts", "notes.txt"), "w") as f:
        f.write("junk")
    with open(os.path.join(gd, "transcripts", ".DS_Store"), "wb") as f:
        f.write(b"\x00")
    return gd


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_fixture(self.td.name)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestListProjection(Base):
    """列表投影：意图/标题/模型道/token 耗聚合（确定性排序）。"""

    def test_items_sorted_with_titles(self):
        st, p = api.list_transcripts({}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual([i["intent"] for i in p["items"]],
                         ["INT-t1-0001", "INT-t1-0003", "INT-t1-0009"])
        by = {i["intent"]: i for i in p["items"]}
        self.assertEqual(by["INT-t1-0001"]["title"], "侦察 shop.example 子域")
        self.assertEqual(by["INT-t1-0009"]["title"], "", "不在意图表=空标题")
        self.assertNotIn("INT-t1-0002", by, "无录制文件的意图不上列表")

    def test_aggregates_models_turns_tokens(self):
        st, p = api.list_transcripts({}, self.gd)
        by = {i["intent"]: i for i in p["items"]}
        one = by["INT-t1-0001"]
        self.assertEqual(one["models"], ["m1", "m2"])
        self.assertEqual(one["turns"], 3)
        self.assertEqual(one["lines"], 6)
        self.assertEqual(one["bad_lines"], 0)
        self.assertEqual(one["prompt_tokens"], 250)
        self.assertEqual(one["completion_tokens"], 23)
        self.assertEqual(one["first_ts"], TS1)
        self.assertEqual(one["last_ts"], TS6)
        self.assertEqual(one["warrior"], "W-1")
        three = by["INT-t1-0003"]
        self.assertEqual(three["prompt_tokens"], 0, "无 usage=0 不虚构")
        self.assertEqual(three["bad_lines"], 1, "坏行如实披露不静默")

    def test_totals_across_intents(self):
        st, p = api.list_transcripts({}, self.gd)
        self.assertEqual(p["totals"]["intents"], 3)
        self.assertEqual(p["totals"]["lines"], 9)
        self.assertEqual(p["totals"]["prompt_tokens"], 250)
        self.assertEqual(p["totals"]["completion_tokens"], 23)
        self.assertEqual(p["goal"], "G-t1")

    def test_empty_when_no_transcripts_dir(self):
        gd2 = os.path.join(self.td.name, "G-empty")
        os.makedirs(gd2)
        st, p = api.list_transcripts({}, gd2)
        self.assertEqual(st, 200)
        self.assertEqual(p["items"], [])
        self.assertEqual(p["totals"], {"intents": 0, "lines": 0,
                                       "prompt_tokens": 0,
                                       "completion_tokens": 0})

    def test_goal_param_resolves_sibling_dir(self):
        st, p = api.list_transcripts({"goal": "G-t1"}, os.path.dirname(self.gd))
        self.assertEqual(st, 200)
        self.assertEqual(len(p["items"]), 3)


class TestDetailProjection(Base):
    """详情投影：请求/响应原始对逐行（原文保真，mono 页消费）。"""

    def test_pairs_in_file_order(self):
        st, p = api.transcript_detail({"id": "INT-t1-0001"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["intent"], "INT-t1-0001")
        self.assertEqual(p["title"], "侦察 shop.example 子域")
        roles = [l["role"] for l in p["lines"]]
        self.assertEqual(roles, ["user", "assistant"] * 3)
        self.assertEqual(p["lines"][1]["content"],
                         '{"op":"dig","q":"shop.example"}')
        self.assertEqual(p["lines"][1]["usage"],
                         {"prompt_tokens": 100, "completion_tokens": 10})
        self.assertEqual(p["lines"][0]["model"], "m1")
        self.assertEqual(p["lines"][0]["turn"], 1)
        self.assertEqual(p["lines"][0]["ts"], TS1)

    def test_usage_missing_is_none_not_fabricated(self):
        st, p = api.transcript_detail({"id": "INT-t1-0003"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["bad_lines"], 1)
        self.assertEqual(len(p["lines"]), 2)
        self.assertIsNone(p["lines"][1]["usage"])

    def test_missing_id_400(self):
        st, p = api.transcript_detail({}, self.gd)
        self.assertEqual(st, 400)
        self.assertIn("error", p)

    def test_unknown_intent_404(self):
        st, p = api.transcript_detail({"id": "INT-t1-0777"}, self.gd)
        self.assertEqual(st, 404)
        self.assertIn("error", p)

    def test_bad_id_rejected(self):
        for bad in ("../goals", "a/b", "a b", ".", "INT\\x"):
            st, p = api.transcript_detail({"id": bad}, self.gd)
            self.assertEqual(st, 400, "越界 id 须拒: %r" % bad)

    def test_writer_compatibility_append(self):
        """真写方（warrior.transcript.Transcript）跨重启续写 → 投影逐行可读。"""
        gd2 = os.path.join(self.td.name, "G-w")
        tr = Transcript(gd2, battle="G-w", warrior="W-9")
        tr.record("INT-w-0001", "user", "第一轮", ts=TS1, model="m1", turn=1)
        tr2 = Transcript(gd2, battle="G-w", warrior="W-9")
        tr2.record("INT-w-0001", "assistant", "答", ts=TS2, model="m1",
                   turn=1, usage={"prompt_tokens": 7, "completion_tokens": 2})
        st, p = api.list_transcripts({}, gd2)
        self.assertEqual(st, 200)
        self.assertEqual(p["items"][0]["warrior"], "W-9")
        st, d = api.transcript_detail({"id": "INT-w-0001"}, gd2)
        self.assertEqual([l["role"] for l in d["lines"]], ["user", "assistant"])
        self.assertEqual(d["lines"][0]["content"], "第一轮")


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
            status, payload = api.ROUTES[u.path](q, self.server.ledger_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.gd,
                                     operator_key=webui_login.OP_KEY)
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
    """/api/v2/* 会话门+分发（动态口=server_address[1]，禁碰 8900）。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/llm-transcripts", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_list_over_http(self):
        conn, resp = self._get("/api/v2/llm-transcripts")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["totals"]["intents"], 3)
        conn.close()

    def test_detail_over_http(self):
        conn, resp = self._get("/api/v2/llm-transcript-detail?id=INT-t1-0001")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["lines"]), 6)
        conn.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

ZONE_MARKS = (
    'id="rec-list"', 'id="rec-detail"',
    "模型对话记录",
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    "mono",
)
FETCH_MARKS = ("'/api/v2/llm-transcripts", "'/api/v2/llm-transcript-detail")
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战士", "战役",
               "开战", "九门")


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

    def test_copy_banned_words(self):
        src = self._src()
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src, "宪法#41 禁词上屏: " + bad)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'llm-recordings'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines(self):
        src = self._src()
        n = src.count("\n")
        self.assertLess(n, 2000)
