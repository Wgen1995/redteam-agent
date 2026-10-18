# -*- coding: utf-8 -*-
"""T7·评测对比页钉测（界面线施工计划 2026-10-18 续程⑤：D2 三臂同考读面）。

python3 -m unittest tests.test_webui_pagespec_evals
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18（评测对比=D2 三臂同考读面）；
文案宪法#41（界面人话律）——「考卷/对赌」不上屏（界面词=基准评测）。

数据单源：experiments/<exp-id>.tsv 实验登记处（解析单源=webui.metrics.
parse_exp_tsv/experiments_view 复用，不造第二份格式）× battles_metrics 逐战
结算（settle-report recall 行）。臂=battles_<name> 字段通用解析（双臂/三臂
同律）；登记战例 × 结算行联表：未结算战例如实标「未结算」不造数；D2=
id 以 d2 起头的登记（三臂同考），未登记=诚实空态+预登记律提示。

三层钉：
  ①投影层  evals_view——登记逐字上屏（verdict/status/note 原样）+臂解析
           （名/战例/已结算均值/未结算数）+d2 旗标与提示。
  ②挂载层  /api/v2/evals.json 过会话门（无 cookie=401 JSON）；动态口真服
           过 HTTP 返真仓登记（directive-n5 在册）。
  ③页面层  static/pages/evals.html——D2 三臂区+登记表+四态+nav.push 自注册
           +零 CDN。
"""
import json
import os
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
REPO = os.path.join(HERE, "..")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from webui import api_v2_evals as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


D2_TSV = (
    "id\td2-baseline1\n"
    "question\t三臂同卷 recall/precision/时延/成本（夹具）\n"
    "battles_tanyin\tb1 b2\n"
    "battles_artex\tb3 b4\n"
    "battles_vulnclaw\tb5\n"
    "gt_gen\t一战一 gen（夹具）\n"
    "decision_rule\t分层 recall 描述性对比+Wilson CI（夹具）\n"
    "registered\t2026-10-18 夹具预登记\n"
    "status\t进行中\n"
    "verdict\t\n"
    "source\t夹具\n"
    "note\tn=4 判不了产品间显著性——跨臂只报区间不判显著（夹具）\n"
)

N5_TSV = (
    "id\tdirective-n5\n"
    "question\t预置指令是否提升检出力（夹具双臂）\n"
    "battles_control\tb1\n"
    "battles_treatment\tb2\n"
    "registered\t2026-10-11 夹具\n"
    "status\t已判决\n"
    "verdict\t子集不可复原\n"
    "source\t夹具\n"
)


def settle(recall_txt):
    return "verify-chain: PASS\nrecall=%s\n" % recall_txt


def build_fixture(root):
    """repo 根（登记处）+battles 根（1-4 已结算，5 未结算）。"""
    _write(os.path.join(root, "experiments", "d2-baseline1.tsv"), D2_TSV)
    _write(os.path.join(root, "experiments", "directive-n5.tsv"), N5_TSV)
    b = os.path.join(root, "battles")
    for n, txt in [(1, "recall=0.5000 (28/56)"), (2, "recall=0.6000 (34/56)"),
                   (3, "recall=0.4000 (22/56)"), (4, "recall=0.7000 (39/56)")]:
        _write(os.path.join(b, "battle-%d" % n, "settle-report.txt"), settle(txt))
        _write(os.path.join(b, "battle-%d" % n, "directive.txt"), "")
    os.makedirs(os.path.join(b, "battle-5"), exist_ok=True)   # 未结算（无报告）
    _write(os.path.join(b, "battle-5", "directive.txt"), "x")
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
        self.root = build_fixture(os.path.join(self.td.name, "repo"))

    def view(self, **kw):
        kw.setdefault("repo_root", self.root)
        kw.setdefault("battles_dir", os.path.join(self.root, "battles"))
        return api.evals_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestEvalsProjection(Base):
    def test_d2_three_arms_parsed(self):
        p = self.view()
        self.assertTrue(p["d2"]["registered"])
        d2 = [e for e in p["experiments"] if e["id"] == "d2-baseline1"][0]
        names = [a["name"] for a in d2["arms"]]
        self.assertEqual(names, ["tanyin", "artex", "vulnclaw"])   # 三臂同考

    def test_arm_join_with_settled_metrics(self):
        p = self.view()
        d2 = [e for e in p["experiments"] if e["id"] == "d2-baseline1"][0]
        tanyin = [a for a in d2["arms"] if a["name"] == "tanyin"][0]
        self.assertEqual(tanyin["battles"], ["b1", "b2"])
        self.assertEqual(tanyin["settled"], 2)
        # 每战 recall 先四位舍入（28/56=0.5, 34/56=0.6071）再算均值
        self.assertEqual(tanyin["mean_recall"], 0.5535)
        self.assertEqual(tanyin["unsettled"], 0)
        vc = [a for a in d2["arms"] if a["name"] == "vulnclaw"][0]
        self.assertEqual(vc["settled"], 0)
        self.assertEqual(vc["unsettled"], 1)                      # b5 无结算=如实

    def test_registry_verbatim_passthrough(self):
        p = self.view()
        n5 = [e for e in p["experiments"] if e["id"] == "directive-n5"][0]
        self.assertEqual(n5["verdict"], "子集不可复原")             # 逐字上屏
        self.assertEqual(n5["status"], "已判决")
        self.assertEqual([a["name"] for a in n5["arms"]], ["control", "treatment"])
        d2 = [e for e in p["experiments"] if e["id"] == "d2-baseline1"][0]
        self.assertIn("只报区间", d2["note"])                     # 诚实话术原样

    def test_counts(self):
        p = self.view()
        self.assertEqual(p["counts"]["experiments"], 2)
        self.assertEqual(p["counts"]["d2"], 1)

    def test_no_d2_registration_honest_empty(self):
        empty_repo = os.path.join(self.td.name, "repo2",)
        _write(os.path.join(empty_repo, "experiments", "x1.tsv"), N5_TSV)
        p = api.evals_view(repo_root=empty_repo,
                           battles_dir=os.path.join(self.root, "battles"))
        self.assertFalse(p["d2"]["registered"])
        self.assertIn("预登记", p["d2"]["hint"])                  # 预登记律提示

    def test_missing_everything_tolerant(self):
        none = os.path.join(self.td.name, "repo3")
        p = api.evals_view(repo_root=none, battles_dir=os.path.join(none, "b"))
        self.assertFalse(p["d2"]["registered"])
        self.assertEqual(p["experiments"], [])

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
    """动态口真服（禁碰 8900）：会话门+真仓登记处（directive-n5 在册）。"""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.ledger = os.path.join(cls.td.name, "G-bare")
        os.makedirs(cls.ledger, exist_ok=True)
        from tests import webui_login
        cls.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=cls.ledger,
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

    def _get(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/evals.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_real_repo_registry_over_http(self):
        conn, resp = self._get("/api/v2/evals.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        ids = [e["id"] for e in p["experiments"]]
        self.assertIn("directive-n5", ids)                       # 真仓单源在册
        n5 = [e for e in p["experiments"] if e["id"] == "directive-n5"][0]
        self.assertEqual(n5["verdict"], "子集不可复原")
        conn.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "evals.html")
ZONE_MARKS = (
    # D2 三臂区 + 登记表
    'id="ev-d2"', 'id="ev-arms"', 'id="ev-registry"',
    "三臂", "预登记",
    # 臂表列
    "臂", "战例", "均值",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
)
FETCH_MARKS = ("'/api/v2/evals.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场", "对赌")


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
        self.assertIn("id: 'evals'", src)
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
        self.assertGreaterEqual(len(src.splitlines()), 230, "评测对比页量纲")


if __name__ == "__main__":
    unittest.main()
