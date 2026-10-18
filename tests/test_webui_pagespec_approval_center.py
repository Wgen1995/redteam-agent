# -*- coding: utf-8 -*-
"""T7·审批中心页钉测（界面线施工计划 2026-10-18 续程②：全局审批中心读面）。

python3 -m unittest tests.test_webui_pagespec_approval_center
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18；卡片形态复用 T3 拦截审批
页签（风险级徽章/工具/命令全文 mono/AI 预审「仅供参考」/三钮——写入走既有
/api/approval，本层零写）；文案宪法#41（界面人话律）。

数据单源：battles/*/G-*/ 跨代合并 timeline（revert_cmd 非空且未核销未豁免=
待审，query_cmds._replay_status 同判定跨任务重扫；按 command_hash 去重留最新
——审批绑定命令哈希不绑定行）× approvals.tsv（已决历史+豁免）× 拦截流水
（guard-reject/tools-reject/gate-fail/egress 分层，api_v2_guard.layer_of 同源）。
风险词表/AI 预审文案单源=api_v2_guard（本投影 import 复用，不造第二份词表）。

三层钉：
  ①投影层  approval_center_view——全局待审队列(带所属任务)+风险计数+已决
           历史+分层拦截流水计数+审批对齐任务(写入唯一通道)。
  ②挂载层  /api/v2/approval-center.json 过会话门（无 cookie=401 JSON）；
           动态口真服过 HTTP 返夹具（跨任务聚合真数据）。
  ③页面层  static/pages/approval-center.html——T3 卡形态+四态+nav.push 自注册
           +零 CDN；三钮仅对齐任务可点（其余卡提示切任务）。
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
from webui import api_v2_approval_center as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

# 账本 TSV 无表头（行式数据，core.TABLES 列序）
_T8 = 8    # timeline 8 列
_A6 = 6    # approvals 6 列

EV_PEND = "hook deploy canary token=abc123"
EV_REVERTED = "upload report.zip to client.example.com"
EV_EXEMPT = "rm -f /tmp/cache.bin"
CMD = "revert-upload --token=abc123"


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_fixture(root):
    # 空单元格=「」（真实账本口径——占位符会误判待审）
    b1 = os.path.join(root, "battle-1", "G-r2")
    _write(os.path.join(b1, "timeline.tsv"), [
        "2026-10-01T01:00:00Z\tagent\tP2\t" + EV_PEND + "\trevert-canary --token=abc123\t\t\t1",
        "2026-10-01T02:00:00Z\tagent\tP2\t" + EV_REVERTED + "\t" + CMD + "\t\t\t1",
        "2026-10-01T03:00:00Z\toperator\tP6\trevert:" + EV_REVERTED + "\t\t\t1",
        "2026-10-01T04:00:00Z\tagent\tP2\t" + EV_EXEMPT + "\trevert-rm --path=/tmp/cache.bin\t\t\t1",
        "2026-10-01T05:00:00Z\tguard\tP2\tguard-reject rate-limit cmd=curl http://x\t\t\t1",
    ])
    _write(os.path.join(b1, "approvals.tsv"), [
        "AP-1\tdeadbeef\texempted\t操作员\t2026-10-01T06:00:00Z\t" + EV_EXEMPT + "（观察面豁免）",
    ])
    b2 = os.path.join(root, "battle-2", "G-r5")
    _write(os.path.join(b2, "timeline.tsv"), [
        "2026-10-02T01:00:00Z\tagent\tP2\tegress upload secret.tar to bad.host\trevert-egress --id=9\t\t\t1",
        # 同命令哈希重试行（去重留最新——行号取后行）
        "2026-10-02T02:00:00Z\tagent\tP2\tegress upload secret.tar to bad.host\trevert-egress --id=9\t\t\t1",
        "2026-10-02T03:00:00Z\thook\tP3\thook block write /etc/hosts\t\t\t1",
    ])
    _write(os.path.join(b2, "approvals.tsv"), [
        "AP-2\tcafebabe\tapproved\t操作员\t2026-10-02T04:00:00Z\t历史批准（夹具）",
    ])
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
        return api.approval_center_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestCenterProjection(Base):
    def test_pending_across_battles(self):
        p = self.view()
        self.assertEqual(len(p["pending"]), 2)             # 豁免/已核销排除
        battles = sorted(set(c["battle"]["id"] for c in p["pending"]))
        self.assertEqual(battles, ["battle-1", "battle-2"])

    def test_card_shape_t3(self):
        p = self.view()
        card = [c for c in p["pending"]
                if c["battle"]["id"] == "battle-1"][0]
        self.assertEqual(card["event"], EV_PEND)
        self.assertEqual(card["command"], "revert-canary --token=abc123")
        self.assertEqual(card["tool"], "hook")             # 首词工具抽取
        self.assertIn("仅供参考", card["ai_note"])          # AI 预审恒标
        self.assertEqual(len(card["command_hash"]), 64)    # sha256
        self.assertTrue(card["risk"] in ("高", "中", "低"))

    def test_dedup_by_command_hash_keeps_latest(self):
        p = self.view()
        cards = [c for c in p["pending"]
                 if c["battle"]["id"] == "battle-2" and c["event"].startswith("egress")]
        self.assertEqual(len(cards), 1)                    # 同哈希两行=一卡
        self.assertEqual(cards[0]["row"], 2)               # 留最新行
        self.assertEqual(cards[0]["risk"], "高")            # egress 高危词表

    def test_risk_counts(self):
        p = self.view()
        self.assertEqual(p["counts"]["pending"], 2)
        self.assertEqual(p["counts"]["by_risk"]["高"], 1)
        self.assertEqual(p["counts"]["battles_with_pending"], 2)

    def test_flow_layers(self):
        p = self.view()
        by_battle = {f["id"]: f for f in p["flow"]}
        # 分层词表同源 api_v2_guard.layer_of：hook* 行入 L3、guard-reject 入 L2、
        # egress* 行入 L4（两行重试同计——流水不去重，只待审队列按哈希去重）
        self.assertEqual(by_battle["battle-1"]["flow"], 2)  # hook 部署行+guard-reject
        self.assertEqual(by_battle["battle-2"]["flow"], 3)  # egress×2+hook 拦截

    def test_recent_decisions(self):
        p = self.view()
        ids = [d["id"] for d in p["recent"]]
        self.assertIn("AP-1", ids)
        self.assertIn("AP-2", ids)
        dec = [d for d in p["recent"] if d["id"] == "AP-1"][0]
        self.assertEqual(dec["decision"], "exempted")
        self.assertEqual(dec["battle"], "battle-1")

    def test_aligned_none_when_ledger_outside(self):
        p = self.view()
        self.assertEqual(p["approval_aligned_battle"], "")
        writable = {c["battle"]["id"]: c["writable"] for c in p["pending"]}
        self.assertEqual(writable["battle-1"], False)
        self.assertEqual(writable["battle-2"], False)

    def test_aligned_battle_writable(self):
        gd = os.path.join(self.root, "battle-1", "G-r2")
        p = self.view(ledger_dir=gd)
        self.assertEqual(p["approval_aligned_battle"], "battle-1")
        card = [c for c in p["pending"]
                if c["battle"]["id"] == "battle-1"][0]
        self.assertEqual(card["writable"], True)           # 三钮仅对齐任务可点

    def test_q_filter(self):
        p = self.view(q="battle-2")
        self.assertEqual([c["battle"]["id"] for c in p["pending"]], ["battle-2"])
        p2 = self.view(q="不存在词")
        self.assertEqual(p2["pending"], [])
        self.assertTrue(p2["q"])

    def test_empty_battles_tolerant(self):
        empty = os.path.join(self.td.name, "none")
        p = api.approval_center_view(battles_dir=empty, ledger_dir=self.ledger)
        self.assertEqual(p["pending"], [])
        self.assertEqual(p["counts"]["pending"], 0)

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.td.name), before)
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


class TestV2MountContract(unittest.TestCase):
    """动态口真服（禁碰 8900）：会话门+夹具审批中心过 HTTP。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.ledger = os.path.join(cls.td.name, "G-bare")
        os.makedirs(cls.ledger, exist_ok=True)
        cls.root = build_fixture(os.path.join(cls.td.name, "battles"))
        from tests import webui_login
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=cls.ledger,
                                     operator_key=webui_login.OP_KEY,
                                     battles_dir=cls.root)
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

    def _get(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/approval-center.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_center_over_http(self):
        conn, resp = self._get("/api/v2/approval-center.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["pending"], 2)
        conn.close()

    def test_q_over_http(self):
        conn, resp = self._get("/api/v2/approval-center.json?q=egress")
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["pending"]), 1)
        conn.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "approval-center.html")
ZONE_MARKS = (
    # 顶条：过滤 + 计数
    'id="ac-search"', 'id="ac-counts"',
    # T3 卡形态六件：风险徽章/工具/命令全文/AI 预审/智能体+时间/三钮
    'id="ac-queue"', "风险·", "AI 预审", "仅供参考", "批准执行", "拒绝", "改参",
    "所属任务",
    # 已决历史 + 拦截流水
    'id="ac-recent"', 'id="ac-flow"',
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/approval-center.json", "'/api/approval'")
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场")


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
        self.assertIn("id: 'approval-center'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_230(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 230, "审批中心页量纲")


if __name__ == "__main__":
    unittest.main()
