# -*- coding: utf-8 -*-
"""T6·技法库页钉测（界面线施工计划 2026-10-18 T6 ③：50 卡列表+搜索+卡详情六节只读）。

python3 -m unittest tests.test_webui_pagespec_techniques
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P8-P18（技法库）；
文案宪法#41（界面人话律）——「技法」=产品词（技法库），内部代号（K5/CP）不上导航。

数据单源：knowledge/concepts/CP-*.md（50 卡，front matter+六节结构）×
knowledge/cp-index.tsv（索引）。六节=场景/步骤/工具引用/纪律标注/证据标准/边界；
早期 8 卡=四节旧构（适用条件/步骤/证据标准/边界（Boundaries））——如实展示不硬凑。

三层钉：
  ①投影层  api_v2_techniques.techniques_view——列表(id/标题/漏洞类/成本档/状态/
           六节名)+搜索(q 命中 title/vuln_class/applicability/id)+详情(front matter
           六节正文只读)；坏卡跳过；空目录降级空表。
  ②挂载层  /api/v2/techniques.json 过会话门（无 cookie=401 JSON）；动态口真服
           过 HTTP 返真仓 50 卡（真实单源钉）；q 过滤可用。
  ③页面层  static/pages/techniques.html——卡列表+搜索框+详情六节+四态+nav.push
           自注册+零 CDN。
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
from webui import api_v2_techniques as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

REAL_CONCEPTS = os.path.join(REPO, "knowledge", "concepts")
REAL_INDEX = os.path.join(REPO, "knowledge", "cp-index.tsv")

CARD_SIX = """---
id: CP-9001
kind: technique
class: K5
title: 注入族综合测试域（夹具）
vocab_version: WSTG-v4.2
vuln_class: wstg-inpv:inj
applicability: 参数可拼入解释器的任意端点
cost_hint: 2
failure_modes: WAF 过滤（转编码绕过）；无注入点（转参数位）
judgment: 每变体出口证据；负结果最少尝试 3 次
last_verified: 2026-10-01
status: learned
source_id: KP-0006
---
## 场景

注入面系统性测试：SQL/命令/模板/表达式。

## 步骤

1. 定位注入点；2. 分变体定性；3. 受阻转向。

## 工具引用

- sqlmap（--batch --level=3）；
- 自制 payload 字典。

## 纪律标注

不执行破坏性语句；负结果如实记。

## 证据标准

完整请求响应对；判定依据可复核。

## 边界

不越权、不破坏、不伪造证据。
"""

CARD_LEGACY = """---
id: CP-9002
kind: technique
class: K5
title: 旧构四节卡（夹具）
vuln_class: wstg-auth
applicability: 认证面
cost_hint: 1
status: learned
last_verified: 2026-09-01
source_id: KP-0001
---
## 适用条件

默认凭据或会话缺陷可观测。

## 步骤

枚举入口；尝试默认凭据。

## 证据标准

登录成功截图与请求行。

## 边界（Boundaries）

不动真实用户数据。
"""

INDEX_TSV = (
    "id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\n"
    "CP-9001\t注入族综合测试域（夹具）\tKP-0006\tfixture\tlearned\t2026-10-01\n"
    "CP-9002\t旧构四节卡（夹具）\tKP-0001\tfixture\tlearned\t2026-09-01\n"
)


def build_fixture(td):
    cd = os.path.join(td, "concepts")
    os.makedirs(cd)
    with open(os.path.join(cd, "CP-9001.md"), "w", encoding="utf-8") as f:
        f.write(CARD_SIX)
    with open(os.path.join(cd, "CP-9002.md"), "w", encoding="utf-8") as f:
        f.write(CARD_LEGACY)
    with open(os.path.join(cd, "CP-bad.md"), "w", encoding="utf-8") as f:
        f.write("no front matter here\n")            # 坏卡=跳过
    idx = os.path.join(td, "cp-index.tsv")
    with open(idx, "w", encoding="utf-8") as f:
        f.write(INDEX_TSV)
    return cd, idx


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
        self.cd, self.idx = build_fixture(self.td.name)

    def view(self, **kw):
        kw.setdefault("concepts_dir", self.cd)
        kw.setdefault("index_path", self.idx)
        return api.techniques_view(**kw)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestTechniquesProjection(Base):
    def test_list_columns_and_order(self):
        p = self.view()
        cards = p["cards"]
        self.assertEqual([c["id"] for c in cards], ["CP-9001", "CP-9002"])
        c1 = cards[0]
        self.assertEqual(c1["title"], "注入族综合测试域（夹具）")
        self.assertEqual(c1["vuln_class"], "wstg-inpv:inj")
        self.assertEqual(c1["cost_hint"], 2)
        self.assertEqual(c1["status"], "learned")
        self.assertEqual(c1["shape"], "六节")                 # 六节结构卡
        self.assertEqual(c1["section_count"], 6)
        self.assertIn("工具引用", c1["section_names"])
        self.assertNotIn("CP-bad", [c["id"] for c in cards])  # 坏卡跳过

    def test_legacy_card_shape_honest(self):
        p = self.view()
        c2 = [c for c in p["cards"] if c["id"] == "CP-9002"][0]
        self.assertEqual(c2["shape"], "早期四节")              # 不硬凑六节
        self.assertEqual(c2["section_count"], 4)
        self.assertIn("适用条件", c2["section_names"])

    def test_search_q_filters(self):
        p = self.view(q="注入")
        self.assertEqual([c["id"] for c in p["cards"]], ["CP-9001"])
        p2 = self.view(q="wstg-auth")                        # vuln_class 命中
        self.assertEqual([c["id"] for c in p2["cards"]], ["CP-9002"])
        p3 = self.view(q="解释器")                            # applicability 命中
        self.assertEqual([c["id"] for c in p3["cards"]], ["CP-9001"])
        p4 = self.view(q="CP-9002")                          # id 命中
        self.assertEqual([c["id"] for c in p4["cards"]], ["CP-9002"])
        p5 = self.view(q="不存在词")
        self.assertEqual(p5["cards"], [])
        self.assertTrue(p5["q"])

    def test_detail_returns_sections_bodies(self):
        p = self.view(id="CP-9001")
        self.assertEqual(p["card"]["id"], "CP-9001")
        self.assertEqual(p["card"]["failure_modes"], "WAF 过滤（转编码绕过）；无注入点（转参数位）")
        names = [s["name"] for s in p["card"]["sections"]]
        self.assertEqual(names, ["场景", "步骤", "工具引用", "纪律标注", "证据标准", "边界"])
        bodies = {s["name"]: s["body"] for s in p["card"]["sections"]}
        self.assertIn("sqlmap", bodies["工具引用"])
        self.assertIn("不执行破坏性语句", bodies["纪律标注"])
        self.assertNotIn("##", bodies["场景"])                # 节名剥离正文干净

    def test_detail_unknown_id_error(self):
        p = self.view(id="CP-4242")
        self.assertIn("error", p)

    def test_index_enriches_source_topic(self):
        p = self.view()
        c1 = p["cards"][0]
        self.assertEqual(c1["source_topic"], "fixture")       # 索引联表

    def test_counts(self):
        p = self.view()
        self.assertEqual(p["counts"]["total"], 2)
        self.assertEqual(p["counts"]["six_section"], 1)
        self.assertEqual(p["counts"]["legacy"], 1)

    def test_empty_dir_tolerant(self):
        empty = os.path.join(self.td.name, "empty")
        os.makedirs(empty)
        p = self.view()
        p2 = api.techniques_view(concepts_dir=empty,
                                 index_path=os.path.join(self.td.name, "none.tsv"))
        self.assertEqual(p2["cards"], [])
        self.assertEqual(p2["counts"]["total"], 0)

    def test_readonly_deterministic(self):
        before = dir_bytes(self.td.name)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.td.name), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_real_repo_fifty_cards(self):
        """真实单源钉：仓内 knowledge/concepts 恰 50 卡（CP-0001..CP-0050）。"""
        p = api.techniques_view(concepts_dir=REAL_CONCEPTS, index_path=REAL_INDEX)
        self.assertEqual(len(p["cards"]), 50)
        self.assertEqual(p["cards"][0]["id"], "CP-0001")
        self.assertEqual(p["cards"][-1]["id"], "CP-0050")
        self.assertEqual(p["counts"]["six_section"] + p["counts"]["legacy"], 50)


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
    """动态口真服（禁碰 8900）：会话门+真仓 50 卡过 HTTP。"""

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
        conn, resp = self._get("/api/v2/techniques.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_fifty_cards_over_http(self):
        conn, resp = self._get("/api/v2/techniques.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(p["cards"]), 50)
        conn.close()

    def test_q_and_detail_over_http(self):
        conn, resp = self._get("/api/v2/techniques.json?q=SQL")
        p = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(p["cards"])
        self.assertIn("SQL", json.dumps(p, ensure_ascii=False))
        conn.close()
        conn2, resp2 = self._get("/api/v2/techniques.json?id=CP-0001")
        d = json.loads(resp2.read().decode("utf-8"))
        self.assertEqual(d["card"]["id"], "CP-0001")
        self.assertEqual(len(d["card"]["sections"]), 4)      # 早期四节如实
        conn2.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "techniques.html")
ZONE_MARKS = (
    # 顶条：搜索 + 计数
    'id="tech-search"', 'id="tech-counts"',
    # 卡列表（id/标题/漏洞类/成本档/六节徽章）
    'id="tech-list"', "成本档",
    # 详情：六节只读（场景/步骤/工具引用/纪律标注/证据标准/边界）
    'id="tech-detail"', "场景", "工具引用", "纪律标注", "证据标准", "边界",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 宿主壳接入
    "TechniquesTab", "mode-tab",
)
FETCH_MARKS = ("'/api/v2/techniques.json",)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "K5 技法页")


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
        self.assertIn("id: 'techniques'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_js_under_2000_lines_page_over_250(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 250, "技法页 ~300 行量纲")


if __name__ == "__main__":
    unittest.main()
