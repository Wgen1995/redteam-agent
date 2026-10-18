# -*- coding: utf-8 -*-
"""全域锚定对话 MVP（anchored-chat-v1 只读问答）——三层钉测。

python3 -m unittest tests.test_webui_pagespec_anchored_chat -v
律：只读问答——AI 只回答不执行动作；账本表零写入（成功路径唯一落盘=
llmpool_state.json 运行态，同智能体运行时位置）；模型面=本地假模型服务
（tests/test_warrior_fake_model.py 动态口），绝不真调外部 API；纯 stdlib、
3.9 兼容、前端零框架零 CDN。设计权威 docs/design/contextual-chat-v1.md
（MVP 裁剪：不做动作派发、不做对话落账——后续舰接入 timeline/审批门）。

三层钉：
  ①投影层  api_v2_ask.resolve_anchor（锚=账本行址：表+行号+行内容指纹；
           发现锚富化=本行+关联证据行+所属意图行）+ ask（问题+上下文投给
           模型道，channels 机制同 warrior model_client）+ 引用行址核验；
  ②挂载层  POST /api/v2/ask 过会话门+CSRF 双检（_V2MountHandler 钉挂法）；
  ③页面层  static/pages/anchored-chat.html 结构钉（对象卡+问答面+引用区+
           只读声明+nav.push 自注册+零 CDN）。
"""
import http.client
import json
import os
import socket
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core  # noqa: E402
from webui import api_v2_ask as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402
from tests.test_warrior_fake_model import FakeModelServer  # noqa: E402
from tests import webui_login  # noqa: E402

T = core.TABLES
PAGE = os.path.join(CLI, "webui", "static", "pages", "anchored-chat.html")
ENV_CHANNELS = "TANYIN_ASK_CHANNELS"
ANSWER = ("结论：影响为高——未登录可读管理面板 [findings.tsv#1]；"
          "佐证见 [E-index.tsv#1]。不存在的行为 [findings.tsv#99]。")


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def build_fixture(td):
    """夹具：1 发现（双证据+所属意图）。"""
    gd = os.path.join(td, "G-t1")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-t1-0001", title="管理面板探测",
            status="done", schema_version="2",
            created="2026-10-18T01:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-t1-0001", intent_id="INT-t1-0001",
            title="管理面板匿名可读", confidence="C1", impact="高",
            exploitation_status="verified", dedup_key="admin-anon-read",
            description_brief="未登录可读取管理面板订单列表",
            affected_asset_id="AST-t1-0001",
            evidence_ids="EV-t1-0001,EV-t1-0002", status="active",
            schema_version="2", created="2026-10-18T02:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id="EV-t1-0001", title="管理面板响应捕获",
            source_type="capture", linked_finding="FD-t1-0001",
            schema_version="2", created="2026-10-18T02:30:00Z"),
        row("E-index.tsv", id="EV-t1-0002", title="登录爆破计数",
            source_type="command", linked_finding="FD-t1-0001",
            schema_version="2", created="2026-10-18T02:40:00Z"),
    ])
    return gd


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_fixture(self.td.name)
        self._old_env = os.environ.get(ENV_CHANNELS)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._old_env is None:
            os.environ.pop(ENV_CHANNELS, None)
        else:
            os.environ[ENV_CHANNELS] = self._old_env

    def _channels(self, srv, name="m1"):
        path = os.path.join(self.td.name, "channels.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([{"name": name, "model": name, "base_url": srv.base,
                        "api_key": "stub-key"}], f)
        os.environ[ENV_CHANNELS] = path
        return path


# ═══════════════════════════════ ① 锚解析 ═══════════════════════════════

class TestResolveAnchor(Base):
    """锚=账本行址：发现锚富化（本行+证据行+意图行），行内容指纹可验。"""

    def test_finding_anchor_enriched(self):
        st, a = api.resolve_anchor(self.gd, {"table": "findings.tsv",
                                             "id": "FD-t1-0001"})
        self.assertEqual(st, 200)
        self.assertEqual(a["table"], "findings.tsv")
        self.assertEqual(a["row"], 1)
        self.assertEqual(a["id"], "FD-t1-0001")
        self.assertIn("FD-t1-0001", a["label"])
        self.assertIn("管理面板匿名可读", a["label"])
        refs = [c["ref"] for c in a["context"]]
        self.assertIn("[findings.tsv#1]", refs)
        self.assertIn("[E-index.tsv#1]", refs)
        self.assertIn("[E-index.tsv#2]", refs)
        self.assertIn("[intents.tsv#1]", refs)
        for c in a["context"]:
            self.assertRegex(c["line_hash"], r"^[0-9a-f]{12}$")
            self.assertTrue(c["keyvals"])

    def test_anchor_by_row(self):
        st, a = api.resolve_anchor(self.gd, {"table": "findings.tsv",
                                             "row": 1})
        self.assertEqual(st, 200)
        self.assertEqual(a["id"], "FD-t1-0001")

    def test_generic_table_anchor(self):
        st, a = api.resolve_anchor(self.gd, {"table": "intents.tsv",
                                             "id": "INT-t1-0001"})
        self.assertEqual(st, 200)
        self.assertEqual([c["ref"] for c in a["context"]],
                         ["[intents.tsv#1]"])

    def test_unknown_id_404(self):
        st, p = api.resolve_anchor(self.gd, {"table": "findings.tsv",
                                             "id": "FD-t1-9999"})
        self.assertEqual(st, 404)
        self.assertIn("error", p)

    def test_bad_table_400(self):
        st, p = api.resolve_anchor(self.gd, {"table": "timeline.tsv",
                                             "id": "x"})
        self.assertEqual(st, 400)
        self.assertIn("error", p)

    def test_missing_fields_400(self):
        for anchor in (None, {}, {"table": ""}, {"id": "FD-t1-0001"}):
            st, p = api.resolve_anchor(self.gd, anchor)
            self.assertEqual(st, 400, "缺锚字段须拒: %r" % (anchor,))
            self.assertIn("error", p)


# ═══════════════════════════════ ② ask 流 ═══════════════════════════════

class TestAskFlow(Base):
    """问题+锚上下文投给模型道（假模型服务动态口）→ 答案+引用行址核验。"""

    def setUp(self):
        super().setUp()
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)

    def _ask(self, anchor=None, message="这个发现的影响是什么？", **kw):
        body = {"anchor": anchor or {"table": "findings.tsv",
                                     "id": "FD-t1-0001"},
                "message": message}
        body.update(kw)
        return api.ask(body, self.gd)

    def test_ask_success(self):
        self.srv.set_scripts({"m1": [{"content": ANSWER,
                                      "prompt_tokens": 321,
                                      "completion_tokens": 45}]})
        self._channels(self.srv)
        st, p = self._ask()
        self.assertEqual(st, 200)
        self.assertEqual(p["answer"], ANSWER)
        self.assertEqual(p["model"], "m1")
        self.assertEqual(p["usage"], {"prompt_tokens": 321,
                                      "completion_tokens": 45})
        self.assertEqual(p["attempts"], [{"model": "m1", "outcome": "ok"}])
        self.assertTrue(p["read_only"])
        self.assertEqual(p["anchor"]["id"], "FD-t1-0001")

    def test_prompt_carries_context_and_question(self):
        self.srv.set_scripts({"m1": [{"content": "答"}]})
        self._channels(self.srv)
        st, p = self._ask(message="复述一句：这个发现的影响是什么？")
        self.assertEqual(st, 200)
        req = self.srv.requests[-1]
        roles = [m["role"] for m in req["messages"]]
        self.assertEqual(roles, ["system", "user"])
        user = req["messages"][1]["content"]
        self.assertIn("[findings.tsv#1]", user)
        self.assertIn("[E-index.tsv#1]", user)
        self.assertIn("这个发现的影响是什么？", user)
        system = req["messages"][0]["content"]
        self.assertIn("只", system)

    def test_citations_verified(self):
        self.srv.set_scripts({"m1": [{"content": ANSWER}]})
        self._channels(self.srv)
        st, p = self._ask()
        ok = {c["ref"]: c for c in p["citations"]}
        self.assertTrue(ok["[findings.tsv#1]"]["ok"])
        self.assertRegex(ok["[findings.tsv#1]"]["line_hash"], r"^[0-9a-f]{12}$")
        self.assertIn("FD-t1-0001", ok["[findings.tsv#1]"]["label"])
        self.assertTrue(ok["[E-index.tsv#1]"]["ok"])
        self.assertFalse(ok["[findings.tsv#99]"]["ok"], "不存在行=未命中")

    def test_missing_message_400(self):
        self._channels(self.srv)
        st, p = self._ask(message="  ")
        self.assertEqual(st, 400)
        self.assertIn("error", p)

    def test_channels_unset_503(self):
        os.environ.pop(ENV_CHANNELS, None)
        st, p = self._ask()
        self.assertEqual(st, 503)
        self.assertIn("error", p)

    def test_channels_bad_json_503(self):
        path = os.path.join(self.td.name, "bad.json")
        with open(path, "w") as f:
            f.write("{not-json")
        os.environ[ENV_CHANNELS] = path
        st, p = self._ask()
        self.assertEqual(st, 503)
        self.assertIn("error", p)

    def test_model_down_502(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dead = s.getsockname()[1]
        s.close()
        path = os.path.join(self.td.name, "dead.json")
        with open(path, "w") as f:
            json.dump([{"name": "m1", "model": "m1",
                        "base_url": "http://127.0.0.1:%d/v1" % dead,
                        "api_key": "k"}], f)
        os.environ[ENV_CHANNELS] = path
        st, p = self._ask()
        self.assertEqual(st, 502)
        self.assertIn("error", p)
        self.assertIn("reason", p)

    def test_read_only_ledger_tables_unchanged(self):
        """成功问答后：账本表逐字节不变；新增文件仅 llmpool_state.json。"""
        self.srv.set_scripts({"m1": [{"content": ANSWER}]})
        self._channels(self.srv)
        before = {}
        for name in sorted(os.listdir(self.gd)):
            p = os.path.join(self.gd, name)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    before[name] = f.read()
        st, p = self._ask()
        self.assertEqual(st, 200)
        after = {}
        for name in sorted(os.listdir(self.gd)):
            p = os.path.join(self.gd, name)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    after[name] = f.read()
        for name, blob in before.items():
            self.assertEqual(after.get(name), blob, "表被改写: " + name)
        new = set(after) - set(before)
        self.assertTrue(new <= {"llmpool_state.json"},
                        "成功路径只许运行态一个新文件: %r" % new)


# ═══════════════════════════════ ③ 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉：POST /api/v2/ask 过会话门+CSRF 后分发 POST_ROUTES。"""

    def do_POST(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.POST_ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——写面须操作员会话"})
            if not self._guard_csrf():
                return
            body = self._read_json()
            if body is None:
                return self._fail(400, {"error": "请求体须 JSON"})
            status, payload = api.dispatch_post(u.path, body,
                                                self.server.ledger_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_POST()


class ServerBase(Base):
    def setUp(self):
        super().setUp()
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

    def _post(self, path, body, cookie=True, csrf=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = {"Content-Type": "application/json"}
        if cookie:
            hdrs.update(webui_login.cookie(self.sid))
        if csrf:
            hdrs["X-Requested-With"] = "XMLHttpRequest"
            hdrs["Origin"] = "http://127.0.0.1:%d" % self.port
        conn.request("POST", path, body=json.dumps(body).encode("utf-8"),
                     headers=hdrs)
        return conn, conn.getresponse()


class TestV2MountContract(ServerBase):
    """POST 会话门+CSRF 双检+分发（动态口=server_address[1]，禁碰 8900）。"""

    def setUp(self):
        super().setUp()
        self.fake = FakeModelServer()
        self.addCleanup(self.fake.stop)
        self.fake.set_scripts({"m1": [{"content": ANSWER}]})
        self._channels(self.fake)

    def test_401_without_session(self):
        conn, resp = self._post("/api/v2/ask", {"anchor": {}, "message": "x"},
                                cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_403_without_csrf_header(self):
        conn, resp = self._post("/api/v2/ask", {"anchor": {}, "message": "x"},
                                csrf=False)
        self.assertEqual(resp.status, 403)
        conn.close()

    def test_ask_over_http_happy(self):
        conn, resp = self._post("/api/v2/ask", {
            "anchor": {"table": "findings.tsv", "id": "FD-t1-0001"},
            "message": "影响是什么？"})
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["answer"], ANSWER)
        self.assertTrue(p["read_only"])
        conn.close()


# ═══════════════════════════════ ④ 页面层 ═══════════════════════════════

ZONE_MARKS = (
    "问 AI",
    'id="anchor-card"', 'id="ask-input"', 'id="btn-ask"',
    'id="chat-log"', 'id="ask-citations"',
    "不执行任何操作",
    'id="st-error"', 'id="btn-retry"',
)
FETCH_MARKS = ("'/api/v2/ask'", "X-Requested-With")
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战士", "战役",
               "开战", "九门")


class TestPageStructure(unittest.TestCase):
    def _src(self):
        with open(PAGE, encoding="utf-8") as f:
            return f.read()

    def test_zones_present(self):
        src = self._src()
        for m in ZONE_MARKS:
            self.assertIn(m, src, "缺 " + m)
        for m in FETCH_MARKS:
            self.assertIn(m, src, "须拉取 " + m)

    def test_copy_banned_words(self):
        src = self._src()
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src, "宪法#41 禁词上屏: " + bad)

    def test_nav_guard_and_zero_cdn(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'anchored-chat'", src)
        self.assertIn("typeof nav.push", src)
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines(self):
        src = self._src()
        self.assertLess(src.count("\n"), 2000)
