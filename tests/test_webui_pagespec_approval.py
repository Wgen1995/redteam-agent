# -*- coding: utf-8 -*-
"""T3·P5.8 拦截审批页签钉测（界面线施工计划 2026-10-18 T3）。

python3 -m unittest tests.test_webui_pagespec_approval
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P5.8 + gates-speed-v1.md（分域
异步门：审批挂起不阻塞主战）；文案宪法#41。
数据源=approvals+guard 流水（timeline 过滤：guard-reject/tools-reject/gate-fail/
egress）+assets 范围外（扩展审批分支）。

三层钉：
  ①投影层  api_v2_guard.guard_view——待审队列（revert 未核销未豁免，_replay_status
           同判定）+风险/工具/AI 预审（仅供参考）富化+四层拦截流水
           （L1 账本/L2 执行通道/L3 宿主 hook/L4 egress 代理）+扩展审批分支
           （范围外资产挂起列表+范围修订接入判定+主战继续提示）。
  ②挂载层  /api/v2/guard.json 过会话门；与既有 /api/approval 的 command_hash
           连接钉（三钮写入走既有端点，读面不改 server.py）。
  ③页面层  static/pages/approval.html 结构钉（待审卡片三钮[批准/拒绝/改参]+AI
           预审引用「仅供参考」+四层流水表+扩展分支区+主战继续提示条+四态）。
"""
import hashlib
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
from webui import api_v2_guard as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS = ["2026-10-23T%02d:%02d:00Z" % (4 + i // 60, i % 60) for i in range(20)]


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    """(ts, actor, phase, event[, revert]) → 链式 timeline 行。"""
    rows, prev = [], core.GENESIS
    for spec in rows_spec:
        ts, actor, phase, event = spec[:4]
        revert = spec[4] if len(spec) > 4 else ""
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        prev = h
    return rows


def build_fixture(td):
    """battle-10 两代目：3 待审（含已核销排除）+四层流水各层至少一行+扩展分支。"""
    bdir = os.path.join(td, "battles", "battle-10")
    g1 = os.path.join(bdir, "G-r1")
    os.makedirs(g1)
    core.write_tsv(os.path.join(g1, "assets.tsv"), [
        row("assets.tsv", id="AST-10001", type="app", value="shop.example",
            in_scope="in_scope", created=TS[1]),
        row("assets.tsv", id="AST-10002", type="root-domain", value="evil.example",
            in_scope="out_of_scope", created=TS[10]),
        row("assets.tsv", id="AST-10003", type="root-domain", value="new.example",
            in_scope="out_of_scope", created=TS[11]),
    ])
    core.write_tsv(os.path.join(g1, "scope.tsv"), [
        row("scope.tsv", id="S-10001", kind="include", matcher="shop.example",
            created=TS[1]),
        row("scope.tsv", id="S-10002", kind="include", matcher="new.example",
            amendment_of="S-10001", note="扩展审批通过后接入", created=TS[12]),
    ])
    core.write_tsv(os.path.join(g1, "approvals.tsv", ), [
        row("approvals.tsv", id="AP-10001", command_hash="deadbeef",
            decision="approved", approver="操作员", timestamp=TS[13]),
    ])
    req_ev = "request: shop.example/a via=replay"
    core.write_tsv(os.path.join(g1, "timeline.tsv"), chained_tl([
        (TS[0], "总控", "P0", "add-goal G-r1"),
        (TS[1], "CLI", "P1", "add-asset AST-10001"),
        (TS[2], "tools", "P3",
         "tools-reject card=sqlmap approval-required: L3 卡未批即拒",
         "tanyin-tools exec sqlmap --level=3 --risk=2"),          # 待审① 高危
        (TS[3], "guard", "P3", "guard-reject out-of-scope host=evil.example"),
        (TS[4], "guard", "P3", "guard-reject enforcement-readonly cmd=rm -rf /tmp/x"),
        (TS[5], "guard", "P3", "guard-reject rate-limit used=101 limit=100 window=60s"),
        (TS[6], "总控", "P2", "gate-fail:P2 assert=ledger-matrix-gaps reason=baseline"),
        (TS[7], "replay", "P4", req_ev, "curl -X DELETE shop.example/a"),  # 后被核销
        (TS[8], "CLI", "P6", "revert:" + req_ev),                 # 核销→不列待审
        (TS[9], "tools", "P3", "tools-reject card=ffuf deny-extra: 字典含越界词",
         "ffuf -w dict.txt -u shop.example/FUZZ"),                # 待审② 中危
        (TS[10], "CLI", "P1", "add-asset AST-10002"),
        (TS[11], "CLI", "P1", "add-asset AST-10003"),
        (TS[12], "总控", "P1", "amend-scope S-10002->S-10001"),
        (TS[13], "操作员", "P5", "approve AP-10001"),
        (TS[14], "egress", "P3", "egress-block host=oob.example port=443",
         "egress canary cleanup"),                                # 待审③ 高危 L4
    ]))
    g2 = os.path.join(bdir, "G-r2")
    os.makedirs(g2)
    core.write_tsv(os.path.join(g2, "timeline.tsv"), chained_tl([
        (TS[15], "guard", "P3", "guard-reject time-travel mode=future delta=99999"),
        (TS[16], "tools", "P3",
         "tools-reject card=sqlmap approval-required: L3 卡未批即拒",
         "tanyin-tools exec sqlmap --level=3 --risk=2"),          # 待审④（二代目）
    ]))
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
        self.ledger_dir = os.path.join(self.bdir, "G-r2")


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestGuardProjection(Base):
    """待审队列+四层流水+扩展审批分支投影。"""

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles_root)
        kw.setdefault("ledger_dir", self.ledger_dir)
        return api.guard_view(**kw)

    def test_pending_queue_enriched(self):
        p = self.view()
        pend = p["pending"]
        self.assertEqual(p["counts"]["pending"], 3)   # 核销行不列；G-r2 续待审
        tools = [x for x in pend if x["tool"] == "sqlmap"]
        self.assertEqual(len(tools), 1)               # G-r1/G-r2 同命令合并视角
        it = tools[0]
        self.assertEqual(it["risk"], "高")            # L3 → 高
        self.assertIn("l3", it["risk_basis"].lower())
        self.assertEqual(it["command_hash"],
                         hashlib.sha256(
                             "tanyin-tools exec sqlmap --level=3 --risk=2"
                             .encode("utf-8")).hexdigest())
        self.assertEqual(it["command"], "tanyin-tools exec sqlmap --level=3 --risk=2")
        self.assertIn("仅供参考", it["ai_note"])
        self.assertIn("终审", it["ai_note"])
        ffuf = [x for x in pend if x["tool"] == "ffuf"][0]
        self.assertEqual(ffuf["risk"], "中")          # deny → 中
        eg = [x for x in pend if x["tool"] == "egress-block"][0]
        self.assertEqual(eg["risk"], "高")           # egress → 高

    def test_pending_excludes_reverted(self):
        p = self.view()
        evs = [x["event"] for x in p["pending"]]
        self.assertFalse(any("request: shop.example/a" == e for e in evs))

    def test_flow_four_layers(self):
        p = self.view()
        flow = p["flow"]
        layers = {f["layer"] for f in flow}
        self.assertIn("L1·账本级", layers)            # gate-fail + approval-required
        self.assertIn("L2·执行通道", layers)          # guard-reject/tools-reject
        self.assertIn("L4·egress 代理", layers)       # egress-block
        self.assertEqual(p["counts"]["flow"], 9)   # 含二代目重试拒（流水不去重）
        by_rule = {f["rule"]: f for f in flow}
        self.assertEqual(by_rule["out-of-scope"]["command"], "evil.example")
        self.assertEqual(by_rule["enforcement-readonly"]["command"], "rm -rf /tmp/x")
        self.assertEqual(by_rule["time-travel"]["ts"], TS[15])   # G-r2 并入
        self.assertTrue(all(f["result"] for f in flow))

    def test_layer_classifier_hook(self):
        self.assertEqual(api.layer_of("hook deny cmd=x", "hook"), "L3·宿主 hook")
        self.assertEqual(api.layer_of("guard-reject x", "guard"), "L2·执行通道")
        self.assertEqual(api.layer_of("tools-reject card=a approval-required: x", "tools"),
                         "L1·账本级")
        self.assertEqual(api.layer_of("egress-block h", "egress"), "L4·egress 代理")
        self.assertEqual(api.layer_of("add-goal G", "总控"), "")

    def test_extended_branch(self):
        p = self.view()
        ext = p["extended"]
        items = {i["value"]: i for i in ext["items"]}
        self.assertEqual(len(items), 2)               # 两范围外资产
        self.assertEqual(items["evil.example"]["status"], "挂起")
        self.assertEqual(items["new.example"]["status"], "已接入")   # 修订 matcher 命中
        self.assertEqual(ext["amendments"][0]["matcher"], "new.example")
        self.assertIn("主战", ext["hint"])            # 分域异步门提示
        self.assertEqual(p["counts"]["extended_pending"], 1)
        self.assertEqual(p["counts"]["extended_linked"], 1)

    def test_recent_approvals(self):
        p = self.view()
        self.assertEqual(p["recent"][0]["id"], "AP-10001")
        self.assertEqual(p["recent"][0]["decision"], "approved")

    def test_approval_aligned_flag(self):
        p = self.view()
        self.assertTrue(p["approval_aligned"])        # ledger_dir=G-r2=最新代
        p2 = self.view(ledger_dir=os.path.join(self.bdir, "G-r1"))
        self.assertFalse(p2["approval_aligned"])

    def test_battle_pick_and_errors(self):
        p = self.view()
        self.assertEqual(p["battle"]["id"], "battle-10")
        self.assertEqual(p["goal"], "G-r2")
        p2 = self.view(battle=11)
        self.assertIn("error", p2)
        with self.assertRaises(ValueError):
            self.view(battle="??")

    def test_single_goal_fallback_and_empty(self):
        gd = os.path.join(self.td.name, "G-solo")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
            (TS[0], "guard", "P3", "guard-reject out-of-scope host=x.example"),
        ]))
        p = api.guard_view(battles_dir=os.path.join(self.td.name, "none"),
                           ledger_dir=gd)
        self.assertIsNone(p["battle"])
        self.assertEqual(p["counts"]["flow"], 1)
        gd2 = os.path.join(self.td.name, "G-bare")
        os.makedirs(gd2)
        p2 = api.guard_view(battles_dir=os.path.join(self.td.name, "none"),
                            ledger_dir=gd2)
        self.assertEqual(p2["pending"], [])
        self.assertEqual(p2["flow"], [])
        self.assertTrue(p2["approval_aligned"])

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
                                     approval_key="approval-key-test",
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
    """/api/v2/guard.json 会话门+与既有 /api/approval 的 command_hash 连接钉。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/guard.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertIn("会话", json.loads(resp.read().decode("utf-8"))["error"])
        conn.close()

    def test_over_http(self):
        conn, resp = self._get("/api/v2/guard.json?battle=10")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["pending"], 3)
        self.assertTrue(p["approval_aligned"])
        conn.close()

    def test_unknown_battle_404_and_bad_422(self):
        conn, resp = self._get("/api/v2/guard.json?battle=12")
        self.assertEqual(resp.status, 404)
        conn.close()
        conn, resp = self._get("/api/v2/guard.json?battle=xx")
        self.assertEqual(resp.status, 422)
        conn.close()

    def test_command_hash_join_with_legacy_approval_api(self):
        """三钮写入走既有 /api/approval：command_hash 两侧一致（连接钉）。"""
        conn, resp = self._get("/api/v2/guard.json?battle=10")
        mine = json.loads(resp.read().decode("utf-8"))
        conn.close()
        conn, resp = self._get("/api/approval")       # 既有端点（读 server 主账本）
        legacy = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertTrue(legacy["key_configured"])
        legacy_hashes = {x["command_hash"] for x in legacy["pending"]}
        mine_hashes = {x["command_hash"] for x in mine["pending"]}
        # 服务器主账本=G-r2，其待审行必在我的 battle 投影内（同哈希可连）
        self.assertTrue(legacy_hashes & mine_hashes)
        sig_row = legacy["pending"][0]
        self.assertTrue(sig_row["_approval_sig"])

    def test_http_hits_readonly(self):
        before = dir_bytes(self.bdir)
        conn, resp = self._get("/api/v2/guard.json")
        self.assertEqual(resp.status, 200)
        resp.read()
        conn.close()
        self.assertEqual(dir_bytes(self.bdir), before)


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "approval.html")
ZONE_MARKS = (
    'id="battle-pick"', 'id="ap-counts"',
    # 待审卡片：风险徽章/工具/命令 mono/AI 预审引用「仅供参考」/三钮
    'id="ap-cards"', "风险", "AI 预审", "仅供参考", "发起方",
    'class="btn btn-approve', 'class="btn btn-reject', 'class="btn btn-sm btn-editparams', "改参",
    # 四层拦截流水表
    'id="flow-table"', 'id="flow-body"', "层", "规则", "被拦命令", "结果",
    # 扩展审批分支区 + 主战继续提示条（分域异步门）
    'id="ext-branch"', 'id="ext-hint"', 'id="ext-table"', "主战",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 宿主壳接入
    "ApprovalTab", "mode-tab",
)
FETCH_MARKS = ("'/api/v2/guard.json", "'/api/approval'")
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "复测岗")


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

    def test_three_buttons_post_legacy_endpoint(self):
        src = self._src()
        self.assertIn("decision", src)
        self.assertIn("_approval_sig", src)
        self.assertIn("approved", src)
        self.assertIn("rejected", src)
        self.assertIn("X-Requested-With", src)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'approval'", src)
        self.assertIn("label: '拦截审批'", src)
        self.assertIn("group: '任务详情'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_280(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 280, "P5.8 页 ~340 行量纲")


if __name__ == "__main__":
    unittest.main()
