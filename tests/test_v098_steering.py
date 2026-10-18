# -*- coding: utf-8 -*-
"""v0.9.8 方向盘批——观察面第一批写操作（门禁/五钮窄门/留痕/活体冒烟）。

计划: docs/superpowers/plans/2026-10-16-steering-wheel.md（冻结）。
法律:
- 观察面数据页照旧只读; 写=窄门: POST 路由→守卫(会话+同源+自定义头)→
  subprocess 调 tanyin-ledger 既有命令面(单一写入路径)→回执带记录行号;
- 禁改 cli/ledger/**(本批零触碰); 零依赖(纯 stdlib);
- /api/battle/control 的介入通道=复用 b10 directive 文件(runner 自记 DIRECTIVE),
  终止=killpg(tanyin-runner 既有 kill_group 语义)。

python3 -m unittest tests.test_v098_steering
"""
import base64
import hashlib
import hmac
import http.client
import json
import os
import re
import subprocess
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1, TS2, TS3 = "2026-10-16T01:00:00Z", "2026-10-16T01:05:00Z", "2026-10-16T01:10:00Z"
OP_KEY = "op-key-987-direction"
AP_KEY = "ap-key-654-sign"
COOKIE_RE = re.compile(r"tanyin_sess=([^;]+)")
BANNED = re.compile(r"九门|十边|账本|验链|投影|EV-|FD-|G-r\d|opencode-run")


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    """(ts, actor, phase, event, revert) 铸链式 timeline 行。"""
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event, revert in specs:
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        prev = h
    return rows


def build_goal(gd, with_revert=False):
    """mini 战目录: goals+timeline(+一条待核销 revert 行)。"""
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-t1-0001", target="shop.example", objective="授权渗透：方向盘批夹具",
        budget="1000;100;10", schema_version="2", created=TS1)])
    specs = [(TS1, "总控", "P0", "gate-exit:P0 asserts=3 result=PASS", ""),
             (TS2, "总控", "P1", "request: curl http://x/ -o /tmp/x", "rm -f /tmp/x"),
             (TS3, "子代理", "P1", "add-fact F-t1-0001", "")]
    if not with_revert:
        specs[1] = (TS2, "总控", "P1", "scan surface done", "")
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl(specs))
    return gd


# W1-T1 后：/api/battle/new 只收授权八问全量（豁免通道已废）——本文件payload 单源。
AUTH_DOC = b"AUTH-DOC-steering authorization letter bytes 9876543210"
AUTH_SHA = hashlib.sha256(AUTH_DOC).hexdigest()


def auth_over(**kw):
    a = {"filename": "auth-b1.pdf", "sha256": AUTH_SHA,
         "content_b64": base64.b64encode(AUTH_DOC).decode("ascii"),
         "signer": "王安全（CISO）",
         "valid_from": "2026-10-16T00:00:00Z",
         "valid_until": "2026-10-23T00:00:00Z"}
    a.update(kw)
    return a


def full_payload(**over):
    p = {"name": "汽配外网", "note": "批一：外网面",
         "scope": ["10.0.0.0/24", "*.example.com"],
         "budget": "1000;100;10", "auth": auth_over(),
         "emergency_contact": "138-0000-0000（王安全）",
         "cred_source": "客户提供测试账号",
         "model_tier": "strong", "guard_tier": "T3",
         "legal_ack": True}
    p.update(over)
    return p


class SteeringBase(unittest.TestCase):
    """起服(临时口)+HTTP 小助手+登录助手。"""

    def setUp(self):
        self.td = __import__("tempfile").TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = os.path.join(self.td.name, "battles")
        self.goal = build_goal(os.path.join(self.battles, "battle-1", "G-t1"),
                               with_revert=True)
        self.srv = srv_mod.make_server(
            "127.0.0.1", 0, self.goal,
            battles_dir=self.battles, operator_key=OP_KEY, approval_key=AP_KEY)
        self.port = self.srv.server_address[1]
        th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        th.start()
        self.addCleanup(self.srv.shutdown)
        self.cookie = ""

    def req(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        hdrs = dict(headers or {})
        if self.cookie:
            hdrs["Cookie"] = "tanyin_sess=" + self.cookie
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=data, headers=hdrs)
        r = conn.getresponse()
        out = {"status": r.status,
               "headers": {k.lower(): v for k, v in r.getheaders()},
               "body": r.read()}
        conn.close()
        return out

    def write_req(self, path, body=None, xrw=True, origin=None):
        """带守卫要件的写请求(X-Requested-With+同源)。"""
        h = {"Origin": origin or ("http://127.0.0.1:%d" % self.port)}
        if xrw:
            h["X-Requested-With"] = "XMLHttpRequest"
        return self.req("POST", path, body=body, headers=h)

    def login(self, password=OP_KEY):
        r = self.write_req("/login", {"password": password})
        if r["status"] == 200:
            m = COOKIE_RE.search(r["headers"].get("set-cookie", ""))
            if m:
                self.cookie = m.group(1)
        return r

    def jbody(self, r):
        return json.loads(r["body"].decode("utf-8"))

    # ---- 夹具探针 --------------------------------------------------------
    def tl_rows(self, gd=None):
        p = os.path.join(gd or self.goal, "timeline.tsv")
        with open(p, encoding="utf-8") as f:
            return [ln.split("\t") for ln in f.read().splitlines() if ln]


class TestLoginGate(SteeringBase):
    """第一段 门禁: 未登录 401 JSON/自定义头缺失 403/跨源 403/错 5 锁/HttpOnly。"""

    def test_write_without_session_401_json(self):
        r = self.write_req("/api/battle/say", {"battle": 1, "text": "hi"})
        self.assertEqual(r["status"], 401)
        self.assertEqual(r["headers"]["content-type"], "application/json")
        self.assertIn("error", self.jbody(r))

    def test_write_without_custom_header_403(self):
        self.login()
        r = self.write_req("/api/battle/say", {"battle": 1, "text": "hi"}, xrw=False)
        self.assertEqual(r["status"], 403)

    def test_cross_origin_403(self):
        self.login()
        r = self.write_req("/api/battle/say", {"battle": 1, "text": "hi"},
                           origin="http://evil.example")
        self.assertEqual(r["status"], 403)

    def test_login_ok_httponly_cookie_and_pages_visible(self):
        r = self.login()
        self.assertEqual(r["status"], 200)
        sc = r["headers"]["set-cookie"]
        self.assertIn("HttpOnly", sc)
        self.assertIn("tanyin_sess=", sc)
        # 登录后写路由放行到业务层(空文 422 而非 401)
        r2 = self.write_req("/api/battle/say", {"battle": 1, "text": ""})
        self.assertEqual(r2["status"], 422)

    def test_login_wrong_5_locks_60s(self):
        for _ in range(5):
            r = self.write_req("/login", {"password": "wrong"})
            self.assertEqual(r["status"], 401)
        # 第 6 次: 连对口令也锁(429)
        r = self.login()
        self.assertEqual(r["status"], 429)
        body = self.jbody(r)
        self.assertIn("error", body)

    def test_read_pages_gated_without_login(self):
        """B舰 P0 后法律：读面过登录门——/login 开放；页 302 跳登录、API 401。"""
        r = self.req("GET", "/login")
        self.assertEqual(r["status"], 200)
        self.cookie = ""
        for path in ("/", "/session", "/new"):
            r = self.req("GET", path)
            self.assertEqual(r["status"], 302, path)
            self.assertEqual(r["headers"].get("location"), "/login", path)
        r = self.req("GET", "/api/state.json")
        self.assertEqual(r["status"], 401)
        # 登录后读面照常
        self.login()
        for path in ("/", "/api/state.json"):
            self.assertEqual(self.req("GET", path)["status"], 200, path)


class TestBattleNew(SteeringBase):
    """钮 1 /api/battle/new: 授权八问缺一 422; 全量成事落 goals/scope+行号回执。"""

    def test_scope_empty_422(self):
        self.login()
        r = self.write_req("/api/battle/new", full_payload(scope=[]))
        self.assertEqual(r["status"], 422)
        self.assertIn("范围", self.jbody(r)["error"])

    def test_scope_missing_422(self):
        self.login()
        p = full_payload()
        del p["scope"]
        r = self.write_req("/api/battle/new", p)
        self.assertEqual(r["status"], 422)

    def test_name_empty_422(self):
        self.login()
        r = self.write_req("/api/battle/new", full_payload(name=""))
        self.assertEqual(r["status"], 422)

    def test_old_payload_without_auth_422(self):
        """W1-T1 钉：旧四键口径（无授权件）不再被收——豁免通道已废。"""
        self.login()
        r = self.write_req("/api/battle/new",
                           {"name": "汽配外网", "scope": ["10.0.0.0/24"],
                            "budget": "1000;100;10", "note": "批一"})
        self.assertEqual(r["status"], 422)

    def test_new_ok_goal_scope_ledger_rows(self):
        self.login()
        r = self.write_req("/api/battle/new", full_payload())
        self.assertEqual(r["status"], 200)
        body = self.jbody(r)
        self.assertEqual(body["battle"], 2)          # battle-1 在,新战=2
        gd = os.path.join(self.battles, "battle-2", "G-w1")
        self.assertTrue(os.path.isdir(gd))
        grows = core.Session(gd).rows("goals.tsv")
        self.assertEqual(len(grows), 1)
        self.assertEqual(grows[0][T["goals.tsv"].index("target")], "汽配外网")
        # 真授权件落盘+实测 sha 入行（豁免废除后的产物）
        self.assertEqual(grows[0][T["goals.tsv"].index("auth_sha256")], AUTH_SHA)
        with open(os.path.join(gd, "auth-b1.pdf"), "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), AUTH_SHA)
        srows = core.Session(gd).rows("scope.tsv")
        self.assertEqual(sorted(r2[T["scope.tsv"].index("matcher")] for r2 in srows),
                         ["*.example.com", "10.0.0.0/24"])
        # 留痕: add-goal+2×add-scope 三行入 timeline; 回执行号=文件实况
        tl = self.tl_rows(gd)
        self.assertEqual(len(tl), 3)
        events = [t2[3] for t2 in tl]
        self.assertTrue(events[0].startswith("add-goal "))
        self.assertEqual(sum(1 for e in events if e.startswith("add-scope ")), 2)
        receipts = body["ledger"]
        self.assertEqual(len(receipts), 3)
        self.assertEqual([x["timeline_row"] for x in receipts], [1, 2, 3])
        self.assertTrue(receipts[0]["id"].startswith("G-"))

    def test_new_bad_matcher_rejected_by_ledger(self):
        self.login()
        r = self.write_req("/api/battle/new",
                           full_payload(scope=["bad matcher!!"]))
        self.assertEqual(r["status"], 422)
        # 账本级 REJECT: goals 行已落,scope 拒——如实回执 rc=1
        body = self.jbody(r)
        self.assertFalse(body.get("ok"))


class TestBattleControl(SteeringBase):
    """钮 2 /api/battle/control: pause/resume/stop。"""

    def setUp(self):
        super().setUp()
        self.directive = os.path.join(self.battles, "battle-1", "directive.txt")
        with open(self.directive, "w", encoding="utf-8") as f:
            f.write("")
        self.login()

    def test_pause_writes_directive_and_timeline(self):
        r = self.write_req("/api/battle/control", {"battle": 1, "action": "pause"})
        self.assertEqual(r["status"], 200)
        with open(self.directive, encoding="utf-8") as f:
            dtext = f.read()
        self.assertIn("暂停", dtext)
        tl = self.tl_rows()
        last = tl[-1][3]
        self.assertIn("battle-pause", last)
        self.assertEqual(tl[-1][1], "人工")
        self.assertEqual(self.jbody(r)["timeline_row"], len(tl))

    def test_resume_writes_directive_and_timeline(self):
        self.write_req("/api/battle/control", {"battle": 1, "action": "pause"})
        r = self.write_req("/api/battle/control", {"battle": 1, "action": "resume"})
        self.assertEqual(r["status"], 200)
        with open(self.directive, encoding="utf-8") as f:
            self.assertIn("恢复", f.read())
        self.assertIn("battle-resume", self.tl_rows()[-1][3])

    def test_unknown_action_422(self):
        r = self.write_req("/api/battle/control", {"battle": 1, "action": "boost"})
        self.assertEqual(r["status"], 422)

    def test_missing_battle_404(self):
        r = self.write_req("/api/battle/control", {"battle": 99, "action": "pause"})
        self.assertEqual(r["status"], 404)

    def test_stop_kills_processes_exit_row_and_timeline(self):
        home = os.path.join(self.battles, "battle-1")
        runner_tsv = os.path.join(home, "opencode-run.log.runner.tsv")
        # 假 runner：脚本路径名义 tanyin-runner（pgrep 按完整命令行匹配——生产
        # 形态=python3 <repo>/cli/tanyin-runner start --ledger-dir <battle>）
        fake_bin = os.path.join(self.td.name, "tanyin-runner")
        with open(fake_bin, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\nimport time; time.sleep(600)\n")
        os.chmod(fake_bin, 0o755)
        runner = subprocess.Popen(
            [sys.executable, fake_bin, "start", "--ledger-dir", home],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, start_new_session=True)
        warrior = subprocess.Popen(
            [sys.executable, "-c", "import time;time.sleep(600)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, start_new_session=True)
        self.addCleanup(runner.kill)
        self.addCleanup(warrior.kill)
        with open(runner_tsv, "w", encoding="utf-8") as f:
            f.write("2026-10-16T02:00:00\tBOOT\tfake\n"
                    "2026-10-16T02:00:01\tLAUNCH\tpid=%d (first prompt)\n" % warrior.pid)
        # 等 pgrep 可见（macOS 上 argv 命名法骗不过 pgrep——脚本路径法才可见）
        deadline = time.time() + 5
        seen = False
        while time.time() < deadline:
            pg = subprocess.run(["pgrep", "-f", "tanyin-runner"], capture_output=True)
            if str(runner.pid) in pg.stdout.decode().split():
                seen = True
                break
            time.sleep(0.1)
        if not seen:
            self.skipTest("pgrep 不可用(非 POSIX 环境)")
        r = self.write_req("/api/battle/control", {"battle": 1, "action": "stop"})
        self.assertEqual(r["status"], 200)
        body = self.jbody(r)
        self.assertTrue(body.get("runner_killed"))
        self.assertTrue(body.get("warrior_killed"))
        deadline = time.time() + 5
        while time.time() < deadline and (runner.poll() is None or warrior.poll() is None):
            time.sleep(0.1)
        self.assertIsNotNone(runner.poll())
        self.assertIsNotNone(warrior.poll())
        with open(runner_tsv, encoding="utf-8") as f:
            tail = f.read()
        self.assertIn("\tEXIT\t", tail)
        self.assertIn("operator-stop", tail)
        self.assertIn("battle-stop", self.tl_rows()[-1][3])


class TestBattleSay(SteeringBase):
    """钮 3 /api/battle/say: 对话框→指令通道+留痕。"""

    def test_say_empty_422(self):
        self.login()
        r = self.write_req("/api/battle/say", {"battle": 1, "text": ""})
        self.assertEqual(r["status"], 422)

    def test_say_ok_directive_and_timeline(self):
        directive = os.path.join(self.battles, "battle-1", "directive.txt")
        with open(directive, "w", encoding="utf-8") as f:
            f.write("")
        self.login()
        r = self.write_req("/api/battle/say", {"battle": 1, "text": "优先看登录接口"})
        self.assertEqual(r["status"], 200)
        with open(directive, encoding="utf-8") as f:
            self.assertEqual(f.read(), "优先看登录接口")
        tl = self.tl_rows()
        self.assertIn("battle-say", tl[-1][3])
        self.assertEqual(tl[-1][1], "人工")
        self.assertEqual(self.jbody(r)["timeline_row"], len(tl))

    def test_say_missing_battle_404(self):
        self.login()
        r = self.write_req("/api/battle/say", {"battle": 42, "text": "x"})
        self.assertEqual(r["status"], 404)


class TestApproval(SteeringBase):
    """钮 4 /api/approval: 待审投影(持会话)+持钥签名落账。"""

    @staticmethod
    def _sig(command_hash):
        return hmac.new(hashlib.sha256(AP_KEY.encode()).digest(),
                        command_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    def test_get_pending_requires_session(self):
        r = self.req("GET", "/api/approval")
        self.assertEqual(r["status"], 401)

    def test_get_pending_lists_revert_row(self):
        self.login()
        r = self.req("GET", "/api/approval")
        self.assertEqual(r["status"], 200)
        body = self.jbody(r)
        pend = body["pending"]
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["revert_cmd"], "rm -f /tmp/x")
        self.assertTrue(pend[0]["command_hash"])
        self.assertEqual(pend[0]["_approval_sig"], self._sig(pend[0]["command_hash"]))

    def test_post_without_sig_rejected(self):
        self.login()
        r = self.write_req("/api/approval", {"row": 2, "decision": "exempted"})
        self.assertEqual(r["status"], 403)

    def test_post_bad_sig_rejected(self):
        self.login()
        r = self.write_req("/api/approval", {"row": 2, "decision": "exempted",
                                             "_approval_sig": "0" * 64})
        self.assertEqual(r["status"], 403)
        # 零落账
        self.assertFalse(core.Session(self.goal).rows("approvals.tsv"))

    def test_post_ok_approves_and_ledgers(self):
        self.login()
        pend = self.jbody(self.req("GET", "/api/approval"))["pending"][0]
        r = self.write_req("/api/approval",
                           {"row": pend["row"], "decision": "exempted",
                            "_approval_sig": pend["_approval_sig"]})
        self.assertEqual(r["status"], 200)
        arows = core.Session(self.goal).rows("approvals.tsv")
        self.assertEqual(len(arows), 1)
        self.assertEqual(arows[0][T["approvals.tsv"].index("decision")], "exempted")
        self.assertIn("sig=", arows[0][T["approvals.tsv"].index("note")])
        self.assertIn("approve ", self.tl_rows()[-1][3])
        self.assertEqual(self.jbody(r)["timeline_row"], len(self.tl_rows()))

    def test_post_decision_enum_422(self):
        self.login()
        pend = self.jbody(self.req("GET", "/api/approval"))["pending"][0]
        r = self.write_req("/api/approval",
                           {"row": pend["row"], "decision": "yolo",
                            "_approval_sig": pend["_approval_sig"]})
        self.assertEqual(r["status"], 422)

    def test_no_approval_key_configured_422(self):
        srv2 = srv_mod.make_server("127.0.0.1", 0, self.goal,
                                   battles_dir=self.battles,
                                   operator_key=OP_KEY, approval_key="")
        th2 = threading.Thread(target=srv2.serve_forever, daemon=True)
        th2.start()
        self.addCleanup(srv2.shutdown)
        conn = http.client.HTTPConnection("127.0.0.1", srv2.server_address[1], timeout=10)
        conn.request("POST", "/login", json.dumps({"password": OP_KEY}).encode(),
                     {"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest",
                      "Origin": "http://127.0.0.1:%d" % srv2.server_address[1]})
        resp = conn.getresponse()
        sc = resp.getheader("Set-Cookie") or ""
        resp.read()
        m = COOKIE_RE.search(sc)
        self.assertTrue(m)
        conn.request("POST", "/api/approval", json.dumps({"row": 2, "decision": "exempted",
                                                            "_approval_sig": "x"}).encode(),
                     {"Content-Type": "application/json",
                      "X-Requested-With": "XMLHttpRequest", "Cookie": "tanyin_sess=" + m.group(1),
                      "Origin": "http://127.0.0.1:%d" % srv2.server_address[1]})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 422)
        resp.read()
        conn.close()


class TestReportDownload(SteeringBase):
    """钮 5 /api/report/download: 缓存命中即回文件; 无产物如实报错。"""

    def test_download_cached_report_file(self):
        draft = os.path.join(self.goal, "report", "draft")
        os.makedirs(draft, exist_ok=True)
        with open(os.path.join(draft, "FD-t1-0001.md"), "w", encoding="utf-8") as f:
            f.write("# 测试报告草稿\n\n内容\n")
        self.login()
        r = self.write_req("/api/report/download", {})
        self.assertEqual(r["status"], 200)
        self.assertIn("attachment", r["headers"].get("content-disposition", ""))
        self.assertIn(b"# \xe6\xb5\x8b\xe8\xaf\x95\xe6\x8a\xa5\xe5\x91\x8a", r["body"])

    def test_download_no_report_honest_error(self):
        self.login()
        r = self.write_req("/api/report/download", {})
        self.assertIn(r["status"], (409, 422))
        body = self.jbody(r)
        self.assertIn("error", body)

    def test_download_requires_session(self):
        r = self.write_req("/api/report/download", {})
        self.assertEqual(r["status"], 401)


class TestStaticPages(SteeringBase):
    """第三段 界面: 登录页/新建页/总览审批卡+开战钮/对话操控条/发现下载钮+文案律。"""

    def test_login_page_minimal(self):
        r = self.req("GET", "/login")
        self.assertEqual(r["status"], 200)
        body = r["body"].decode("utf-8")
        self.assertIn("操作员口令", body)
        self.assertIn("type=\"password\"", body)

    def test_new_page_form_fields(self):
        self.login()                                  # B舰 P0 后：读面须会话
        r = self.req("GET", "/new")
        self.assertEqual(r["status"], 200)
        body = r["body"].decode("utf-8")
        for needle in ("任务名称", "范围白名单", "预算", "说明", "授权文件"):
            self.assertIn(needle, body)

    def test_index_has_start_button_and_approval_card(self):
        with open(os.path.join(CLI, "webui", "static", "index.html"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn('href="/new"', src)
        self.assertIn("开战", src)
        self.assertIn('id="approval-card"', src)

    def test_session_page_has_controls(self):
        with open(os.path.join(CLI, "webui", "static", "session.html"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn('id="say-box"', src)
        self.assertIn('id="pause-btn"', src)
        self.assertIn('id="stop-btn"', src)

    def test_evidence_page_has_download_button(self):
        with open(os.path.join(CLI, "webui", "static", "evidence.html"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn('id="report-dl"', src)
        self.assertIn("下载报告", src)

    @staticmethod
    def _label_zone(name):
        """标签区文本（test_ui_copy 同口径：剥 script/style，只查可见文案）。"""
        from html.parser import HTMLParser

        class _V(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.chunks = []
                self._skip = 0

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "pre", "code", "textarea", "template"):
                    self._skip += 1

            def handle_endtag(self, tag):
                if tag in ("script", "style", "pre", "code", "textarea",
                           "template") and self._skip:
                    self._skip -= 1

            def handle_data(self, data):
                if not self._skip:
                    self.chunks.append(data)

        with open(os.path.join(CLI, "webui", "static", name), encoding="utf-8") as f:
            p = _V()
            p.feed(f.read())
            p.close()
        return "\n".join(p.chunks)

    def test_new_pages_no_banned_words(self):
        for name in ("login.html", "new.html"):
            m = BANNED.search(self._label_zone(name))
            self.assertIsNone(m, name + " 标签区出现禁词: %r" % (m and m.group(0)))

    def test_existing_pages_still_no_banned_words(self):
        for name in ("index.html", "session.html", "evidence.html"):
            m = BANNED.search(self._label_zone(name))
            self.assertIsNone(m, name + " 标签区出现禁词: %r" % (m and m.group(0)))


class TestPlaywrightSmoke(SteeringBase):
    """活体冒烟: 登录→新建→回显。"""

    def test_login_create_echo(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright 缺席 ENV-SKIP")
        base = "http://127.0.0.1:%d" % self.port
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome")
        except Exception as e:  # 浏览器二进制缺席
            self.skipTest("chromium 不可启动: %r" % e)
        auth_path = os.path.join(self.td.name, "auth-smoke.pdf")
        with open(auth_path, "wb") as f:
            f.write(AUTH_DOC)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page()
            page.goto(base + "/login")
            page.fill("#op-password", OP_KEY)
            page.click("#op-login")
            page.wait_for_url("**/console", timeout=5000)  # 登录常态=总览
            page.goto(base + "/new")                       # 冒烟目标=八问向导
            # W1 授权八问向导：基本信息+①授权件+②窗口 → 范围+④联系人
            # → 预算+⑥凭据+⑦强度 → ⑧法律勾选+提交（③⑤在二/三步内）
            page.fill("#f-name", "冒烟战")
            page.fill("#f-note", "冒烟")
            page.set_input_files("#f-auth-file", auth_path)
            page.fill("#f-signer", "王安全（CISO）")
            page.fill("#f-valid-from", "2026-10-16T00:00:00Z")
            page.fill("#f-valid-until", "2026-10-23T00:00:00Z")
            page.wait_for_function(          # sha256 浏览器实算完才放行
                "() => !document.getElementById('btn-next').disabled")
            page.click("#btn-next")
            page.fill("#f-scope", "10.0.0.0/24\n*.smoke.example")
            page.fill("#f-contact", "138-0000-0000（王安全）")
            page.click("#btn-next")
            page.fill("#f-budget-tokens", "1000")
            page.fill("#f-budget-reqs", "100")
            page.fill("#f-budget-hours", "10")
            page.fill("#f-cred-source", "客户提供测试账号")
            page.click("#btn-next")
            page.wait_for_selector("#sum-name")
            page.check("#f-legal-ack")
            page.click("#f-submit")
            page.wait_for_selector("#new-result.ok", timeout=10000)
            txt = page.inner_text("#new-result")
            self.assertIn("battle-2", txt)
            browser.close()


if __name__ == "__main__":
    unittest.main()
