# -*- coding: utf-8 -*-
"""功能17补件·对话指挥闭环（command-converse-v1）——三层钉测。

python3 -m unittest tests.test_command_converse -v
律：
  ①对话建任务只产卡不建仗——propose 零写（goal 目录逐字节不变）；确认走既有
    POST /api/battle/new（授权八问仍归 new-task 表单，本模块不代办）。
  ②@引用 fuzzy 搜账本四表（目标/漏洞/事实/任务），命中=ask 同形锚（钉上下文）；
    「@X 再测一次」经 registry.lookup("add-intent") 既有通道生成任务卡进活池
    （origin=recon-event 直达 pending），dedup 机械判重=幂等。
  ③回复四分类=确定性词表推导（同审批中心 AI 预审先例——不上模型）：
    批准/拒绝→路由既有 /api/approval HMAC 面（本模块零写 approvals）；
    改方向→steer 管道 warrior-steer（cli/warrior/steer.py 既有写者）；
    给情报→注入士兵简报（steer 扫描每轮并入模型上下文=简报面）；
    未识别→保守落「给情报」（原文必达士兵，绝不自动批准）。
  屏上文本过词表（62律 scripts/vocab_lint.BANNED 单源）：漏洞/任务/士兵/目标/证据。
设计权威 docs/design/2026-10-20-command-approval-design.md（补件一）。
"""
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core  # noqa: E402
from webui import api_v2_command as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402
from tests import webui_login  # noqa: E402

T = core.TABLES
ENV_BUDGET = "TANYIN_BATTLE_BUDGET_CAP_USD"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def build_fixture(td):
    """夹具：四表各一枚可 @ 的行（词表律词形：目标/漏洞/事实/任务）。"""
    gd = os.path.join(td, "G-t1")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [
        row("goals.tsv", id="G-t1-0001", target="app.example.com",
            objective="演示目标", budget="1;1;1", schema_version="2",
            created="2026-10-18T00:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "assets.tsv"), [
        row("assets.tsv", id="AST-t1-0001", type="host",
            value="app.example.com", in_scope="1",
            schema_version="2", created="2026-10-18T01:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-t1-0001", title="管理面板探测",
            status="done", schema_version="2",
            created="2026-10-18T01:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-t1-0001", intent_id="INT-t1-0001",
            title="管理面板匿名可读", confidence="C1", impact="高",
            dedup_key="admin-anon-read", status="active",
            schema_version="2", created="2026-10-18T02:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "facts.tsv"), [
        row("facts.tsv", id="F-t1-0001", kind="surface",
            target="app.example.com", detail="Admin-Panel暴露在 /admin",
            confidence="C2", schema_version="2",
            created="2026-10-18T03:00:00Z"),
    ])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), [])
    return gd


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
        self.gd = build_fixture(self.td.name)
        self._old_budget = os.environ.get(ENV_BUDGET)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._old_budget is None:
            os.environ.pop(ENV_BUDGET, None)
        else:
            os.environ[ENV_BUDGET] = self._old_budget


# ═══════════════════ ① 对话建任务：只产卡不建仗 ═══════════════════

class TestPropose(Base):
    def test_propose_parses_target_and_objective(self):
        st, p = api.propose({"text": "打 xxx.com,找尽可能多漏洞"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["target"], "xxx.com")
        self.assertEqual(p["objective"], "找尽可能多漏洞")
        self.assertTrue(p["needs_confirm"])

    def test_propose_card_fields(self):
        st, p = api.propose({"text": "打 xxx.com"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["card_version"], "propose-v1")
        self.assertIn("xxx.com", p["scope_preview"])
        self.assertIn("*.xxx.com", p["scope_preview"])   # 域名→同根泛域
        self.assertTrue(p["red_lines"])                    # 红线非空
        joined = " ".join(p["red_lines"])
        self.assertIn("范围外", joined)                    # 范围外不碰
        self.assertIn("审批", joined)                      # 高危须审批
        self.assertTrue("budget_cap" in p)                 # 预算帽（未设=空串）
        # 字典版=battle/new 表单字段直映射（确认零转译）
        self.assertEqual(p["form"]["name"], "xxx.com")
        self.assertEqual(p["form"]["scope"], p["scope_preview"])
        self.assertIn("/api/battle/new", p["confirm_route"])

    def test_propose_cidr_target(self):
        st, p = api.propose({"text": "打 10.0.0.0/24 全网扫"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["target"], "10.0.0.0/24")
        self.assertEqual(p["scope_preview"], ["10.0.0.0/24"])

    def test_propose_budget_cap_from_env(self):
        os.environ[ENV_BUDGET] = "12.5"
        st, p = api.propose({"text": "打 xxx.com"}, self.gd)
        self.assertEqual(p["budget_cap"], "12.5")

    def test_propose_no_target_422(self):
        st, p = api.propose({"text": "今天天气怎么样"}, self.gd)
        self.assertEqual(st, 422)
        self.assertIn("error", p)
        self.assertIn("目标", p["error"])

    def test_propose_empty_400(self):
        st, p = api.propose({"text": "  "}, self.gd)
        self.assertEqual(st, 400)

    def test_propose_zero_write(self):
        """只产卡不建仗：goal 目录逐字节不变（无新文件无改写）。"""
        before = dir_bytes(self.td.name)
        st, _ = api.propose({"text": "打 xxx.com,找尽可能多漏洞"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(dir_bytes(self.td.name), before)


# ═══════════════════ ② @引用：fuzzy 搜账本全域+派活 ═══════════════════

class TestAtSearch(Base):
    def test_search_across_tables(self):
        st, p = api.at_search({"q": "admin"}, self.gd)
        self.assertEqual(st, 200)
        tables = {h["table"] for h in p["hits"]}
        self.assertIn("findings.tsv", tables)      # 管理面板匿名可读
        self.assertIn("facts.tsv", tables)         # Admin-Panel暴露
        for h in p["hits"]:
            self.assertTrue(h["id"])
            self.assertEqual(h["ref"], "[%s#%d]" % (h["table"], h["row"]))
            self.assertTrue(h["label"])

    def test_search_kind_human_words(self):
        """表名→人话类词（62律）：asset=目标 finding=漏洞 fact=事实 intent=任务。"""
        st, p = api.at_search({"q": "管理面板"}, self.gd)
        self.assertEqual(st, 200)
        kinds = {h["table"]: h["kind"] for h in p["hits"]}
        self.assertEqual(kinds.get("findings.tsv"), "漏洞")
        self.assertEqual(kinds.get("intents.tsv"), "任务")
        st2, p2 = api.at_search({"q": "example.com"}, self.gd)
        kinds2 = {h["table"]: h["kind"] for h in p2["hits"]}
        self.assertEqual(kinds2.get("assets.tsv"), "目标")
        st3, p3 = api.at_search({"q": "Admin"}, self.gd)
        kinds3 = {h["table"]: h["kind"] for h in p3["hits"]}
        self.assertEqual(kinds3.get("facts.tsv"), "事实")

    def test_search_fuzzy_case_insensitive(self):
        st, p = api.at_search({"q": "APP.EXAMPLE.COM"}, self.gd)
        self.assertEqual(st, 200)
        self.assertTrue(any(h["id"] == "AST-t1-0001" for h in p["hits"]))

    def test_search_anchor_shape(self):
        """选中即钉上下文：hit 带 ask 同形锚（table+id+row）。"""
        st, p = api.at_search({"q": "AST-t1"}, self.gd)
        self.assertEqual(st, 200)
        h = p["hits"][0]
        self.assertEqual(h["anchor"], {"table": "assets.tsv",
                                       "id": "AST-t1-0001", "row": 1})

    def test_search_empty_q_400(self):
        st, p = api.at_search({"q": " "}, self.gd)
        self.assertEqual(st, 400)

    def test_search_no_hit(self):
        st, p = api.at_search({"q": "不存在的东西"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["hits"], [])


class TestAtDispatch(Base):
    """「@X 再测一次」→ add-intent 既有通道生成任务卡进活池（幂等）。"""

    def _dispatch(self, command="再测一次"):
        return api.at_dispatch({"anchor": {"table": "findings.tsv",
                                          "id": "FD-t1-0001"},
                                "command": command}, self.gd)

    def test_dispatch_creates_intent_card(self):
        st, p = self._dispatch()
        self.assertEqual(st, 200)
        rows = core.Session(self.gd).rows("intents.tsv")
        self.assertEqual(len(rows), 2)
        r = rows[-1]
        idx = {f: i for i, f in enumerate(T["intents.tsv"])}
        self.assertEqual(r[idx["status"]], "pending")       # 活池
        self.assertEqual(r[idx["origin"]], "recon-event")
        self.assertIn("复测", r[idx["title"]])
        self.assertIn("管理面板匿名可读", r[idx["title"]])
        self.assertIn("[findings.tsv#1]", r[idx["detail"]])  # 溯源行址
        self.assertEqual(p["intent_id"], r[idx["id"]])
        self.assertFalse(p["dedup"])

    def test_dispatch_idempotent(self):
        st1, p1 = self._dispatch()
        self.assertEqual(st1, 200)
        st2, p2 = self._dispatch()
        self.assertEqual(st2, 200)
        self.assertTrue(p2["dedup"])                          # 机械判重=幂等
        self.assertEqual(len(core.Session(self.gd).rows("intents.tsv")), 2)

    def test_dispatch_unknown_anchor_404(self):
        st, p = api.at_dispatch({"anchor": {"table": "findings.tsv",
                                           "id": "FD-t1-9999"},
                                 "command": "再测一次"}, self.gd)
        self.assertEqual(st, 404)

    def test_dispatch_unknown_command_422(self):
        st, p = self._dispatch(command="帮我把报告写了")
        self.assertEqual(st, 422)
        self.assertIn("error", p)

    def test_dispatch_zero_other_tables(self):
        """只 add-intent 一条写——别的不碰。"""
        st, _ = self._dispatch()
        self.assertEqual(st, 200)
        s = core.Session(self.gd)
        self.assertEqual(len(s.rows("findings.tsv")), 1)
        self.assertEqual(len(s.rows("facts.tsv")), 1)


# ═══════════════════ ③ 回复四分类 ═══════════════════

class TestClassifyReply(unittest.TestCase):
    """确定性词表推导：四类+保守缺省（绝不自动批准）。"""

    def test_approve_words(self):
        for text in ("同意，批准", "准了", "放行吧", "批准执行"):
            self.assertEqual(api.classify_reply(text), "approve", text)

    def test_reject_words(self):
        for text in ("不行，拒绝", "驳回", "不准这么做", "别执行"):
            self.assertEqual(api.classify_reply(text), "reject", text)

    def test_redirect_words(self):
        for text in ("别管这个了，改打 b.com", "转向先测登录口",
                     "换成深挖上传点", "改方向：优先账本"):
            self.assertEqual(api.classify_reply(text), "redirect", text)

    def test_intel_words(self):
        for text in ("情报：后台入口在 /admin", "线索：钥匙是 admin/admin",
                     "提示一下，管理端没做限速"):
            self.assertEqual(api.classify_reply(text), "intel", text)

    def test_unknown_defaults_intel_never_approve(self):
        for text in ("嗯嗯好的呀", "你看着办", "？？"):
            self.assertEqual(api.classify_reply(text), "intel", text)


class TestSteerReply(Base):
    CTX = {"row": 3, "command_hash": "a" * 64, "_approval_sig": "b" * 64}

    def _reply(self, text, **kw):
        body = {"warrior": "w1", "reply": text}
        body.update(kw)
        return api.steer_reply(body, self.gd)

    def test_approve_routes_existing_hmac_face(self):
        """批准→既有 /api/approval HMAC 面（本模块零写 approvals）。"""
        ap = os.path.join(self.gd, "approvals.tsv")
        before = open(ap, "rb").read() if os.path.exists(ap) else None
        st, p = self._reply("同意，批准", context=self.CTX)
        self.assertEqual(st, 200)
        self.assertEqual(p["category"], "approve")
        self.assertEqual(p["action"]["route"], "/api/approval")
        self.assertEqual(p["action"]["body"]["decision"], "approved")
        self.assertEqual(p["action"]["body"]["row"], 3)
        self.assertEqual(p["action"]["body"]["_approval_sig"], "b" * 64)
        after = open(ap, "rb").read() if os.path.exists(ap) else None
        self.assertEqual(before, after)                     # 零写

    def test_reject_routes_existing_face(self):
        st, p = self._reply("不行，拒绝", context=self.CTX)
        self.assertEqual(st, 200)
        self.assertEqual(p["category"], "reject")
        self.assertEqual(p["action"]["body"]["decision"], "rejected")
        self.assertEqual(p["action"]["route"], "/api/approval")

    def test_approve_without_context_422(self):
        st, p = self._reply("批准")
        self.assertEqual(st, 422)
        self.assertIn("待审", p["error"])

    def test_redirect_writes_steer_pipeline(self):
        st, p = self._reply("改打 b.com 的登录口")
        self.assertEqual(st, 200)
        self.assertEqual(p["category"], "redirect")
        tl = core.Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any(r[3].startswith("warrior-steer target=w1 text=")
                            and "b.com" in r[3] for r in tl))
        self.assertTrue(p["timeline_row"] >= 1)

    def test_intel_injects_briefing(self):
        st, p = self._reply("情报：后台入口在 /admin")
        self.assertEqual(st, 200)
        self.assertEqual(p["category"], "intel")
        tl = core.Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any("warrior-steer" in r[3] and "【情报】" in r[3]
                            and "/admin" in r[3] for r in tl))
        self.assertIn("简报", p["note"])

    def test_reply_empty_400(self):
        st, p = self._reply("  ")
        self.assertEqual(st, 400)

    def test_reply_body_must_be_dict(self):
        st, p = api.steer_reply(["not", "dict"], self.gd)
        self.assertEqual(st, 400)


# ═══════════════════ 词表律（62律机检面单源） ═══════════════════

class TestVocabLaw(unittest.TestCase):
    """本模块全部人话文案过 scripts/vocab_lint.BANNED 单源词表。"""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
        from vocab_lint import BANNED
        cls.banned = tuple(BANNED)

    def _assert_clean(self, text):
        low = text.lower()
        for bad in self.banned:
            self.assertNotIn(bad.lower(), low,
                             "黑话『%s』上屏——应用人话" % bad)

    def test_kind_labels_clean(self):
        for label in api.KIND_WORDS.values():
            self._assert_clean(label)

    def test_note_and_error_strings_clean(self):
        for text in api.SCREEN_TEXTS:
            self._assert_clean(text)


# ═══════════════════ 挂载层（_V2MountHandler 挂法钉） ═══════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉：GET/POST /api/v2/command 域过会话门+CSRF 后分发。"""

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            status, payload = api.dispatch(u.path, q,
                                           ledger_dir=self.server.ledger_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()

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


class TestV2MountContract(Base):
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

    def _get(self, path, cookie=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_post_401_without_session(self):
        conn, resp = self._post("/api/v2/battle/propose", {"text": "打 x.com"},
                                cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_post_403_without_csrf_header(self):
        conn, resp = self._post("/api/v2/battle/propose", {"text": "打 x.com"},
                                csrf=False)
        self.assertEqual(resp.status, 403)
        conn.close()

    def test_get_401_without_session(self):
        conn, resp = self._get("/api/v2/at-search?q=admin", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_propose_over_http(self):
        conn, resp = self._post("/api/v2/battle/propose",
                                {"text": "打 xxx.com,找尽可能多漏洞"})
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["target"], "xxx.com")
        conn.close()

    def test_at_search_over_http(self):
        conn, resp = self._get("/api/v2/at-search?q=admin")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(p["hits"])
        conn.close()

    def test_steer_reply_over_http(self):
        conn, resp = self._post("/api/v2/steer-reply",
                                {"warrior": "w1", "reply": "改打 b.com"})
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["category"], "redirect")
        conn.close()

    def test_registered_in_api_pages(self):
        """include 总装并网钉：本舰 GET/POST 域路由进 api_pages 单源表。"""
        from webui import api_pages
        mounted = api_pages.mounted_v2_routes()
        self.assertEqual(mounted.get("/api/v2/at-search"), "api_v2_command")
        res = api_pages.api_v2_post_dispatch(
            "/api/v2/battle/propose", {"text": "打 xxx.com"}, self.gd)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], 200)
        res2 = api_pages.api_v2_post_dispatch(
            "/api/v2/unknown", {}, self.gd)
        self.assertIsNone(res2)


if __name__ == "__main__":
    unittest.main()
