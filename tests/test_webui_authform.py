# -*- coding: utf-8 -*-
"""W1 界面止血三件（T1 授权八问真实化 / T2 launch 点火 / T7 GraphLed 定名）。

法律（docs/USER-CHARTER.md #38 超越律：默认超越版，不递降级选项）:
- 豁免路径必须死: /api/battle/new 不再传 --allow-missing-auth=1（源码级钉 +
  行为钉: 旧式无授权件 payload=422 拒; 带真授权件 + 前端实算 sha256 = 过
  write_cmds._add_goal 真校验链——文件在位且实测 sha 一致才收行）;
- 授权八问缺一=拒: ①授权文件（原件+sha256）②授权窗口期（签署方+起止）
  ③范围白名单 ④OOB 紧急联系人 ⑤预算硬顶 ⑥凭据来源 ⑦强度档
  ⑧法律条款勾选——逐问摘除必 422;
- launch: CTRL_ACTIONS 含 launch; 点火=mission.txt（goals/scope 行单源装配）+
  directive.txt 基线 + runner spawn（可注入）+ timeline 留痕; 已在跑=拒;
  战不存在=404;
- GraphLed 定名: README 标题+一句话简介（前身=探隐 TanYin）+ webui 九页
  title/页脚/品牌位同步（内部命令 tanyin-* 不动，下批统一）。

python3 -m unittest tests.test_webui_authform
"""
import base64
import hashlib
import http.client
import json
import os
import re
import sys
import threading
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, CLI)

from ledger import core                     # noqa: E402
from webui import server as srv_mod         # noqa: E402

T = core.TABLES
OP_KEY = "op-key-w1-authform"
AP_KEY = "ap-key-w1-sign"
COOKIE_RE = re.compile(r"tanyin_sess=([^;]+)")
TS1 = "2026-10-18T01:00:00Z"
STATIC_DIR = os.path.join(CLI, "webui", "static")
PAGES = ("index.html", "login.html", "new.html", "coverage.html", "graph.html",
         "evidence.html", "metrics.html", "session.html", "activity.html")

AUTH_DOC = b"AUTHORIZATION-DOC-W1 authorization letter bytes 0123456789"
AUTH_SHA = hashlib.sha256(AUTH_DOC).hexdigest()


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event, revert in specs:
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        prev = h
    return rows


def build_goal(gd):
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-t1-0001", target="shop.example",
        objective="授权渗透：W1 夹具", budget="1000;100;10",
        signer="王安全（CISO）", valid_from="2026-10-18T00:00:00Z",
        valid_until="2026-10-25T00:00:00Z", emergency_contact="138-0000-0000",
        model_tier="strong", guard_tier="T3", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "gate-exit:P0 asserts=1 result=PASS", "")]))
    return gd


def auth_over(**kw):
    a = {"filename": "auth-w1.pdf", "sha256": AUTH_SHA,
         "content_b64": base64.b64encode(AUTH_DOC).decode("ascii"),
         "signer": "王安全（CISO）",
         "valid_from": "2026-10-18T00:00:00Z",
         "valid_until": "2026-10-25T00:00:00Z"}
    a.update(kw)
    return a


def full_payload(**over):
    p = {"name": "汽配外网", "note": "W1 真授权链",
         "scope": ["10.0.0.0/24", "*.example.com"],
         "budget": "1000;100;10",
         "auth": auth_over(),
         "emergency_contact": "138-0000-0000（王安全）",
         "cred_source": "客户提供测试账号",
         "model_tier": "strong", "guard_tier": "T3",
         "legal_ack": True}
    p.update(over)
    return p


class AuthFormBase(unittest.TestCase):
    """起服（临时口+临时战目录）+HTTP 小助手+登录。"""

    def setUp(self):
        self.td = __import__("tempfile").TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = os.path.join(self.td.name, "battles")
        self.goal = build_goal(os.path.join(self.battles, "battle-1", "G-t1"))
        self.srv = srv_mod.make_server(
            "127.0.0.1", 0, self.goal, battles_dir=self.battles,
            operator_key=OP_KEY, approval_key=AP_KEY)
        self.port = self.srv.server_address[1]
        th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        th.start()
        self.addCleanup(self.srv.shutdown)
        self.cookie = ""
        self.login()

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

    def tl_rows(self, gd=None):
        p = os.path.join(gd or self.goal, "timeline.tsv")
        with open(p, encoding="utf-8") as f:
            return [ln.split("\t") for ln in f.read().splitlines() if ln]


# ===========================================================================
# T1·一 豁免路径必须死
# ===========================================================================

class TestExemptionDead(AuthFormBase):
    """/api/battle/new 的 --allow-missing-auth 豁免通道废除钉。"""

    def test_server_source_has_no_exemption(self):
        """源码级钉：server.py 不得再出现豁免旗标/场景指纹伪造。"""
        with open(os.path.join(CLI, "webui", "server.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("--allow-missing-auth", src,
                         "webui 建战不得走豁免通道（场景伪造授权已废）")
        self.assertNotIn("webui-scenario", src,
                         "场景占位指纹（名称+时刻伪 sha）必须死")

    def test_old_payload_without_auth_rejected(self):
        """行为钉：旧式四键 payload（无授权件）=422 拒，不再伪造授权四件。"""
        r = self.write_req("/api/battle/new",
                           {"name": "汽配外网", "scope": ["10.0.0.0/24"],
                            "budget": "1000;100;10", "note": "旧口径"})
        self.assertEqual(r["status"], 422)
        self.assertIn("授权", self.jbody(r)["error"])
        # 未落任何新战目录（battle-2 不许因豁免而立）
        self.assertFalse(os.path.exists(os.path.join(self.battles, "battle-2")))

    def test_full_auth_passes_real_chain(self):
        """带真授权件=过：add-goal 走真校验链，goals 行=实测 sha+原件落盘。"""
        r = self.write_req("/api/battle/new", full_payload())
        self.assertEqual(r["status"], 200, self.jbody(r))
        body = self.jbody(r)
        self.assertEqual(body["battle"], 2)
        gd = os.path.join(self.battles, "battle-2", "G-w1")
        grows = core.Session(gd).rows("goals.tsv")
        self.assertEqual(len(grows), 1)
        g = grows[0]

        def col(k):
            return g[T["goals.tsv"].index(k)]
        # 真校验链产物：sha=前端实算值且与盘上原件一致
        self.assertEqual(col("auth_sha256"), AUTH_SHA)
        doc_name = col("auth_doc")
        self.assertTrue(doc_name)
        with open(os.path.join(gd, doc_name), "rb") as f:
            on_disk = f.read()
        self.assertEqual(on_disk, AUTH_DOC)
        self.assertEqual(hashlib.sha256(on_disk).hexdigest(), AUTH_SHA)
        # 八问结构化字段入行
        self.assertEqual(col("signer"), "王安全（CISO）")
        self.assertEqual(col("valid_from"), "2026-10-18T00:00:00Z")
        self.assertEqual(col("valid_until"), "2026-10-25T00:00:00Z")
        self.assertEqual(col("emergency_contact"), "138-0000-0000（王安全）")
        self.assertEqual(col("model_tier"), "strong")
        self.assertEqual(col("guard_tier"), "T3")
        self.assertIn("凭据来源：客户提供测试账号", col("business_context"))

    def test_wrong_sha_rejected_by_real_chain(self):
        """sha 与原件不符=账本真链拒（禁先记后补）；空战目录即时清理。"""
        bad = full_payload(auth=auth_over(sha256="0" * 64))
        r = self.write_req("/api/battle/new", bad)
        self.assertEqual(r["status"], 422)
        err = self.jbody(r)["error"]
        self.assertIn("立项被拒", err)
        self.assertFalse(os.path.exists(os.path.join(self.battles, "battle-2")),
                         "被拒之战不得占号留壳")

    def test_auth_without_content_rejected(self):
        """只有文件名+sha 没有原件字节=①问缺件（文件都不在位，豁免已死）。"""
        a = auth_over()
        del a["content_b64"]
        r = self.write_req("/api/battle/new", full_payload(auth=a))
        self.assertEqual(r["status"], 422)
        self.assertIn("授权文件", self.jbody(r)["error"])

    def test_auth_filename_traversal_sanitized(self):
        """目录穿越名被剥成安全落盘名（不得逃出 goal 目录/覆盖 tsv）。"""
        r = self.write_req("/api/battle/new",
                           full_payload(auth=auth_over(filename="../../evil/x.pdf")))
        self.assertEqual(r["status"], 200, self.jbody(r))
        gd = os.path.join(self.battles, "battle-2", "G-w1")
        g = core.Session(gd).rows("goals.tsv")[0]
        doc = g[T["goals.tsv"].index("auth_doc")]
        self.assertNotIn("..", doc)
        self.assertTrue(os.path.isfile(os.path.join(gd, doc)))
        parent = os.path.join(self.battles, "evil")
        self.assertFalse(os.path.exists(parent), "不得写出 goal 目录外")


# ===========================================================================
# T1·二 八问缺一=拒
# ===========================================================================

class TestEightQuestionsEachRequired(AuthFormBase):
    """逐问摘除必 422（缺一不接单）。"""

    def _reject(self, payload, kw):
        r = self.write_req("/api/battle/new", payload)
        self.assertEqual(r["status"], 422, kw)
        self.assertIn("授权八问", self.jbody(r)["error"], kw)
        self.assertFalse(os.path.exists(os.path.join(self.battles, "battle-2")),
                         kw + "：缺件之战不得落目录")

    def test_q1_auth_doc_missing(self):
        self._reject(full_payload(auth=None), "①授权文件整件缺席")

    def test_q1_auth_signer_missing(self):
        self._reject(full_payload(auth=auth_over(signer="")), "①签署方空")

    def test_q2_window_missing_or_malformed(self):
        self._reject(full_payload(auth=auth_over(valid_from="")), "②窗口起缺")
        self._reject(full_payload(auth=auth_over(valid_until="")), "②窗口止缺")
        self._reject(full_payload(auth=auth_over(
            valid_until="2026/10/25 09:00")), "②窗口格式不认")

    def test_q3_scope_empty(self):
        self._reject(full_payload(scope=[]), "③范围空")
        self._reject(full_payload(scope=["", "  "]), "③范围全空白行")

    def test_q4_oob_contact_missing(self):
        self._reject(full_payload(emergency_contact=""), "④OOB联系人空")

    def test_q5_budget_missing(self):
        self._reject(full_payload(budget=""), "⑤预算空")

    def test_q6_cred_source_missing(self):
        self._reject(full_payload(cred_source=""), "⑥凭据来源空")

    def test_q7_strength_tier_missing_or_invalid(self):
        self._reject(full_payload(model_tier=""), "⑦模型档缺")
        self._reject(full_payload(guard_tier=""), "⑦护栏档缺")
        self._reject(full_payload(model_tier="turbo"), "⑦模型档非枚举")
        self._reject(full_payload(guard_tier="T9"), "⑦护栏档非枚举")

    def test_q8_legal_ack_missing_or_false(self):
        p = full_payload()
        del p["legal_ack"]
        self._reject(p, "⑧法律条款未勾选（键缺席）")
        self._reject(full_payload(legal_ack=False), "⑧法律条款未勾选（false）")
        self._reject(full_payload(legal_ack="yes"), "⑧法律条款勾选须真布尔")


# ===========================================================================
# T2 launch 点火钮
# ===========================================================================

class TestLaunchAction(AuthFormBase):
    """/api/battle/control action=launch：任务书+指令基线+spawn+留痕。"""

    def test_ctrl_actions_contains_launch(self):
        self.assertIn("launch", srv_mod.CTRL_ACTIONS)

    def test_launch_ok_spawns_runner_and_leaves_trail(self):
        home = os.path.join(self.battles, "battle-1")
        gd = os.path.join(home, "G-t1")
        with mock.patch.object(srv_mod, "_spawn_runner",
                               return_value=4312) as sp:
            r = self.write_req("/api/battle/control",
                               {"battle": 1, "action": "launch"})
        self.assertEqual(r["status"], 200, self.jbody(r))
        sp.assert_called_once_with(home, gd)
        body = self.jbody(r)
        self.assertEqual(body["runner_pid"], 4312)
        # 任务书=goals/scope 行单源装配（目标/预算入文，不虚构）
        with open(os.path.join(home, "mission.txt"), encoding="utf-8") as f:
            mission = f.read()
        self.assertIn("shop.example", mission)
        self.assertIn("1000;100;10", mission)
        # 指令通道基线在位（空文件=digest 基线，battle.py 同式）
        self.assertTrue(os.path.isfile(os.path.join(home, "directive.txt")))
        # 留痕：timeline 最后一行=battle-launch+runner-pid，actor=人工
        tl = self.tl_rows(gd)
        self.assertIn("battle-launch", tl[-1][3])
        self.assertIn("runner-pid=4312", tl[-1][3])
        self.assertEqual(tl[-1][1], "人工")
        self.assertEqual(body["timeline_row"], len(tl))

    def test_launch_keeps_operator_edited_mission(self):
        home = os.path.join(self.battles, "battle-1")
        with open(os.path.join(home, "mission.txt"), "w",
                  encoding="utf-8") as f:
            f.write("OPERATOR-EDITED 任务书")
        with mock.patch.object(srv_mod, "_spawn_runner", return_value=11):
            r = self.write_req("/api/battle/control",
                               {"battle": 1, "action": "launch"})
        self.assertEqual(r["status"], 200)
        with open(os.path.join(home, "mission.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "OPERATOR-EDITED 任务书")

    def test_launch_rejected_when_runner_already_alive(self):
        with mock.patch.object(srv_mod, "_find_runner_pids",
                               return_value=[9999]), \
                mock.patch.object(srv_mod, "_spawn_runner",
                                  return_value=1) as sp:
            r = self.write_req("/api/battle/control",
                               {"battle": 1, "action": "launch"})
        self.assertEqual(r["status"], 422)
        self.assertIn("已在跑", self.jbody(r)["error"])
        sp.assert_not_called()
        self.assertNotIn("battle-launch", self.tl_rows()[-1][3],
                         "拒点火不得留 battle-launch 痕")

    def test_launch_unknown_battle_404(self):
        r = self.write_req("/api/battle/control",
                           {"battle": 99, "action": "launch"})
        self.assertEqual(r["status"], 404)

    def test_runner_argv_shape(self):
        """真 spawn 参数表钉：tanyin-runner start 全参（battle.py 同参式）。"""
        home = os.path.join(self.battles, "battle-1")
        gd = os.path.join(home, "G-t1")
        argv = srv_mod._runner_argv(home, gd)
        self.assertEqual(argv[0], sys.executable)
        self.assertTrue(argv[1].endswith("tanyin-runner"), argv[1])
        self.assertIn("start", argv)

        def flag(k):
            return argv[argv.index(k) + 1]
        self.assertEqual(flag("--ledger-dir"), gd)
        self.assertEqual(flag("--prompt-file"), os.path.join(home, "mission.txt"))
        self.assertEqual(flag("--directive-file"),
                         os.path.join(home, srv_mod.DIRECTIVE_TXT))


# ===========================================================================
# T1/T2 界面钉 —— new.html 八问表单 + launch 接线 + 摆设件处置
# ===========================================================================

class TestNewFormWiring(unittest.TestCase):
    """new.html：八问控件在位且活、sha256 前端实算、立即执行接线 launch。"""

    @staticmethod
    def _src():
        with open(os.path.join(STATIC_DIR, "new.html"), encoding="utf-8") as f:
            return f.read()

    def _tag(self, cid):
        src = self._src()
        m = re.search(r'<[^>]*id="' + cid + '"[^>]*>', src)
        self.assertIsNotNone(m, "缺控件 " + cid)
        return m.group(0)

    def test_eight_question_controls_present_and_live(self):
        for cid in ("f-auth-file", "f-signer", "f-valid-from", "f-valid-until",
                    "f-contact", "f-cred-source", "f-model-tier",
                    "f-guard-tier", "f-legal-ack"):
            tag = self._tag(cid)
            self.assertNotIn("disabled", tag, cid + " 不得禁用（八问=活控件）")

    def test_sha256_computed_in_browser(self):
        src = self._src()
        self.assertIn("crypto.subtle", src, "sha256 须前端实算（WebCrypto）")
        self.assertIn("SHA-256", src)
        self.assertIn("arrayBuffer", src, "原件字节须入浏览器")

    def test_exec_now_wired_to_launch(self):
        src = self._src()
        tag = self._tag("f-exec-now")
        self.assertNotIn("disabled", tag, "立即执行须真启用（已接 launch）")
        self.assertNotIn("aria-disabled", tag)
        self.assertIn("/api/battle/control", src, "须打 control 路由")
        self.assertIn('"launch"', src, "action=launch 须入请求体")

    def test_dead_fields_cut_not_pretended(self):
        """砍掉的摆设件不许留影（也不许再挂「即将支持」假装即将）。"""
        src = self._src()
        for cid in ("f-approval", "f-concurrency", "f-schedule"):
            self.assertNotIn('id="' + cid + '"', src,
                             cid + " 已砍——不许留摆设")
        self.assertNotIn("即将支持", src)
        self.assertNotIn("后端未接线", src)

    def test_payload_carries_eight_answers(self):
        src = self._src()
        for k in ("legal_ack", "emergency_contact", "cred_source",
                  "model_tier", "guard_tier", "content_b64", "valid_from",
                  "valid_until", "signer", "sha256"):
            self.assertIn(k, src, "payload 缺键 " + k)


# ===========================================================================
# T7 GraphLed 定名
# ===========================================================================

class TestGraphLedNaming(unittest.TestCase):
    """README 标题/一句话 + webui 九页 title/页脚/品牌位。"""

    @staticmethod
    def _page(name):
        with open(os.path.join(STATIC_DIR, name), encoding="utf-8") as f:
            return f.read()

    def test_readme_title_and_one_liner(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
            head = "".join(f.readline() for _ in range(12))
        self.assertIn("GraphLed", head.splitlines()[0], "标题须 GraphLed")
        self.assertIn("账本为骨", head)
        self.assertIn("图谱为形", head)
        self.assertIn("前身", head)
        self.assertIn("探隐", head)          # 旧名注明为前身
        self.assertIn("TanYin", head)

    def test_page_titles_renamed(self):
        for name in PAGES:
            title = [ln for ln in self._page(name).splitlines()
                     if "<title>" in ln]
            self.assertTrue(title, name + " 无 title")
            self.assertIn("GraphLed", title[0], name + " title 未定名")
            self.assertNotIn("探隐", title[0], name + " title 残留旧名")

    def test_page_footers_and_brand_renamed(self):
        for name in PAGES:
            src = self._page(name)
            footers = [ln for ln in src.splitlines() if "<footer" in ln]
            self.assertTrue(footers, name + " 无页脚")
            for ln in footers:
                self.assertIn("GraphLed", ln, name + " 页脚未定名")
                self.assertNotIn("探隐", ln, name + " 页脚残留旧名")
            self.assertNotIn('class="brand">探隐', src, name + " 品牌位残留")
        self.assertIn("<h1>GraphLed</h1>", self._page("login.html"),
                      "登录页品牌标题须 GraphLed")


# ===========================================================================
# 第 4 件 · B舰 P0：读面全过登录门（读路由零鉴权修）
# ===========================================================================

class TestReadGate(AuthFormBase):
    """do_GET 全读面须会话——未登录：页 302 跳 /login、API 401 JSON；
    /login 与 /favicon.ico 例外；登录后读面照常可用。"""

    PAGES = ("/", "/coverage", "/graph", "/evidence", "/metrics",
             "/session", "/activity", "/new", "/experiments", "/status.js")
    APIS = ("/api/state.json", "/api/matrix.json", "/api/graph.json",
            "/api/evidence.json", "/api/metrics.json", "/api/session.json",
            "/api/session.json?battle=1", "/api/stream")

    def test_pages_redirect_to_login_when_anonymous(self):
        self.cookie = ""
        for p in self.PAGES:
            r = self.req("GET", p)
            self.assertIn(r["status"], (301, 302), p + " 未登录读页须跳登录")
            self.assertEqual(r["headers"].get("location"), "/login",
                             p + " 须 302 到 /login")

    def test_apis_401_json_when_anonymous(self):
        self.cookie = ""
        for p in self.APIS:
            r = self.req("GET", p)
            self.assertEqual(r["status"], 401, p + " 未登录读 API 须 401")
            self.assertIn("error", self.jbody(r), p)

    def test_login_and_favicon_still_open(self):
        self.cookie = ""
        self.assertEqual(self.req("GET", "/login")["status"], 200)
        self.assertEqual(self.req("GET", "/favicon.ico")["status"], 204)

    def test_reads_open_after_login(self):
        for p in ("/", "/session", "/new"):
            self.assertEqual(self.req("GET", p)["status"], 200, p)
        for p in ("/api/state.json", "/api/metrics.json", "/api/session.json"):
            self.assertEqual(self.req("GET", p)["status"], 200, p)
        r = self.req("GET", "/experiments")     # 登录后照旧锚跳度量页
        self.assertEqual(r["status"], 302)
        self.assertEqual(r["headers"].get("location"), "/metrics#experiments")


if __name__ == "__main__":
    unittest.main()
