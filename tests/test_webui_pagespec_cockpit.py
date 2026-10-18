# -*- coding: utf-8 -*-
"""驾驶舱舰（功能27）——api_v2_cockpit 四路聚合投影·真数据测（红转绿先测）。

python3 -m unittest tests.test_webui_pagespec_cockpit
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN；输出确定性
（禁 datetime.now——战场钟=全账最大行时刻，api_v2_retest 同律）。
设计唯一正文 docs/design/2026-10-20-cockpit-ui-blueprint.md（四问+词表62+
五秒三问63）；真数据=demos/DEMO-1 演示战役（DEMO-README 纪律：报数须说明
来自演示战役，别当实战胜果）。

两层钉：
  ①投影层  api_v2_cockpit 四路由（/api/v2/cockpit.json 四问聚合 +
           cockpit-findings 证据袋 + cockpit-knowledge 知识库 +
           cockpit-inbox 收件箱）——DEMO-1 真数据断言（独立双解析对账）；
  ②挂载层  生产 Handler 直测（动态口，禁碰 8900）：缺会话=401 JSON，
           带会话=200（见 test_webui_pagespec_cockpit_faces 挂载组）。
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
CLI = os.path.join(REPO, "cli")
DEMO1 = os.path.join(REPO, "demos", "DEMO-1")
sys.path.insert(0, CLI)

from ledger import core                     # noqa: E402


def _read_rows(path, tname):
    """独立双解析：盘上 TSV→列行（core.unesc 反转义——账本转义单源）。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    width = len(core.TABLES[tname])
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = [core.unesc(c) for c in line.split("\t")]
        out.append(cols + [""] * (width - len(cols)))
    return out


def _col(tname, row_, name):
    return row_[core.TABLES[tname].index(name)]


class TestCockpitFourQuestionsDEMO1(unittest.TestCase):
    """四问直答投影——demos/DEMO-1 真数据（演示战役，非实战胜果）。"""

    @classmethod
    def setUpClass(cls):
        from webui import api_v2_cockpit as api
        cls.api = api
        st, payload = api.dispatch("/api/v2/cockpit.json", {}, ledger_dir=DEMO1)
        assert st == 200, payload
        cls.payload = payload

    def test_q1_verified_vuln_leaderboard_real_counts(self):
        """问一·打出什么漏洞了：只有验真+在册的漏洞进榜（盘上对账；
        同 id 后代胜——被翻案的不重复计）。"""
        q1 = self.payload["q1_vulns"]
        rows = _read_rows(os.path.join(DEMO1, "findings.tsv"), "findings.tsv")
        last = {}
        for r in rows:                     # 同 id 后行胜（事件溯源终态）
            last[_col("findings.tsv", r, "id")] = r
        want = [r for r in last.values()
                if _col("findings.tsv", r, "exploitation_status") == "verified"
                and _col("findings.tsv", r, "status") == "active"]
        self.assertEqual(q1["total"], len(want))
        self.assertEqual(q1["total"], 35)          # 演示战役钉数（防夹具漂移）
        # 每枚带：名字/多严重/在哪/证据链接——四件缺一即不合格
        self.assertLessEqual(len(q1["top"]), 10)
        for v in q1["top"]:
            self.assertTrue(v["id"])
            self.assertTrue(v["title"])
            self.assertIn(v["impact"], ("高", "中", "低"))
            self.assertTrue(v["where"])
            self.assertTrue(v["evidence"])
            self.assertIn("/p/finding-detail?id=", v["detail_url"])
        # 榜序：高>中>低（严重度先行）
        ranks = {"高": 0, "中": 1, "低": 2}
        seq = [ranks[v["impact"]] for v in q1["top"]]
        self.assertEqual(seq, sorted(seq))

    def test_q2_live_pool_inflight_intents_and_recent_timeline(self):
        """问二·正在打什么：在途任务+最近时间线（盘上对账）。"""
        q2 = self.payload["q2_live"]
        rows = _read_rows(os.path.join(DEMO1, "intents.tsv"), "intents.tsv")
        inflight = [r for r in rows
                    if _col("intents.tsv", r, "status") not in
                    ("done", "failed", "cancelled", "superseded")]
        self.assertEqual(q2["inflight_count"], len(inflight))
        self.assertEqual(q2["inflight_count"], 6)
        for it in q2["intents"]:
            self.assertTrue(it["id"] and it["title"] and it["status_zh"])
        self.assertTrue(q2["recent"])
        for ev in q2["recent"]:
            self.assertTrue(ev["ts"] and ev["text"])

    def test_q3_waiting_honest_empty_on_demo(self):
        """问三·什么在等我：DEMO-1 无待审无求助=诚实空（空态由页面人话交代）。"""
        q3 = self.payload["q3_waiting"]
        self.assertEqual(q3["counts"]["pending_approvals"], 0)
        self.assertEqual(q3["counts"]["asks"], 0)
        self.assertEqual(q3["pending_approvals"], [])
        self.assertEqual(q3["asks"], [])

    def test_q4_budget_real_sums_and_cap_bars(self):
        """问四·花多少钱：budget.tsv 聚合+goals 帽三段余量（盘上对账）。"""
        q4 = self.payload["q4_budget"]
        rows = _read_rows(os.path.join(DEMO1, "budget.tsv"), "budget.tsv")
        self.assertEqual(q4["rows_n"], len(rows))
        self.assertEqual(q4["rows_n"], 4)
        self.assertEqual(q4["used"]["tokens"], 335000)
        self.assertEqual(q4["used"]["requests"], 1552)
        self.assertAlmostEqual(q4["used"]["hours"], 1.7)
        self.assertEqual(q4["cap"]["tokens"], 2000000)
        self.assertEqual(q4["cap"]["requests"], 50000)
        self.assertEqual(q4["cap"]["hours"], 40)
        self.assertAlmostEqual(q4["pct"]["tokens"], 16.8)
        self.assertFalse(q4["over"]["tokens"])
        self.assertTrue(q4["goal"]["target"])          # 目标名真值
        self.assertTrue(q4["goal"]["objective"])

    def test_determinism_two_runs_identical(self):
        """只读律：同输入两跑一致（禁墙钟）。"""
        st, a = self.api.dispatch("/api/v2/cockpit.json", {}, ledger_dir=DEMO1)
        st2, b = self.api.dispatch("/api/v2/cockpit.json", {}, ledger_dir=DEMO1)
        self.assertEqual((st, json.dumps(a, sort_keys=True)),
                         (st2, json.dumps(b, sort_keys=True)))


class TestCockpitFindingsDEMO1(unittest.TestCase):
    """漏洞页数据：证据袋（引用+角色+版本）+上次验真+待复验队列位。"""

    @classmethod
    def setUpClass(cls):
        from webui import api_v2_cockpit as api
        cls.api = api
        st, payload = api.dispatch("/api/v2/cockpit-findings.json", {},
                                   ledger_dir=DEMO1)
        assert st == 200, payload
        cls.payload = payload

    def test_counts_match_disk(self):
        """计数=同 id 后代胜合并（盘上对账：111 行原始→76 枚在册）。"""
        c = self.payload["counts"]
        rows = _read_rows(os.path.join(DEMO1, "findings.tsv"), "findings.tsv")
        uniq = {_col("findings.tsv", r, "id") for r in rows}
        self.assertEqual(c["raw_rows"], len(rows))
        self.assertEqual(c["raw_rows"], 111)
        self.assertEqual(c["total"], len(uniq))
        self.assertEqual(c["total"], 76)
        self.assertEqual(c["verified_active"], 35)   # 同 id 后代胜终态

    def test_items_have_where(self):
        """每枚漏洞带 where（目标位置）：资产值→资产id→目标→未登记。"""
        for it in self.payload["items"]:
            self.assertIn("where", it)
            self.assertTrue(it["where"])

    def test_evidence_bag_role_and_versions(self):
        """证据袋：每枚漏洞挂 EV 卡引用+角色（证实/对照）+版本（同组多捕）。"""
        items = {f["id"]: f for f in self.payload["items"]}
        fd4 = items["FD-r18-0004"]
        bag = fd4["evidence_bag"]
        self.assertTrue(bag)
        for ev in bag:
            self.assertTrue(ev["ev_id"].startswith("EV-"))
            self.assertIn(ev["role"], ("证实", "对照"))
            self.assertTrue(ev["versions"])
            for ver in ev["versions"]:
                self.assertGreaterEqual(ver["ver"], 1)
                self.assertTrue(ver["artifact"])
        # 证实角色顺序=evidence_ids 列去重保序（盘上对账；原始列有重写重）
        rows = _read_rows(os.path.join(DEMO1, "findings.tsv"), "findings.tsv")
        fd4_row = [r for r in rows
                   if _col("findings.tsv", r, "id") == "FD-r18-0004"][0]
        ev_ids = [e for e in _col("findings.tsv", fd4_row, "evidence_ids")
                  .split(";") if e]
        dedup = list(dict.fromkeys(ev_ids))
        self.assertEqual([b["ev_id"] for b in bag if b["role"] == "证实"],
                         dedup)

    def test_pair_group_versions_surface(self):
        """版本：同 pair_group 的多次捕获整组 surfaced（盘上对账）。"""
        ev_rows = _read_rows(os.path.join(DEMO1, "E-index.tsv"), "E-index.tsv")
        pg = {}
        for r in ev_rows:
            g = _col("E-index.tsv", r, "pair_group")
            if g:
                pg.setdefault(g, []).append(_col("E-index.tsv", r, "id"))
        multi = [g for g, ids in pg.items() if len(ids) >= 2]
        self.assertTrue(multi)                     # 演示战役确有多版本组
        flat = {ev["ev_id"]: ev for f in self.payload["items"]
                for ev in f["evidence_bag"]}
        g0 = sorted(multi)[0]
        ids0 = sorted(pg[g0])
        vers = [flat[i]["versions"] for i in ids0 if i in flat]
        if vers:
            self.assertEqual(len(vers[0]), len(ids0))

    def test_last_verified_and_queue_position(self):
        """上次验真 X 天前（战场钟=全账最大行时刻，确定性）+待复验队列位。"""
        replayable = [f for f in self.payload["items"] if f["queue_pos"]]
        self.assertTrue(replayable)
        for f in replayable:
            self.assertTrue(f["last_verified_at"])
            self.assertGreaterEqual(f["since_last_days"], 0)
            self.assertTrue(f["since_last_text"])
        # 队位=可复测组内 1 基序，最久未验先列（api_v2_retest 队序同律）
        poss = sorted(f["queue_pos"] for f in replayable)
        self.assertEqual(poss, list(range(1, len(poss) + 1)))

    def test_empty_dir_honest_zero(self):
        """空账本=诚实零，不炸不造数。"""
        with tempfile.TemporaryDirectory() as td:
            st, p = self.api.dispatch("/api/v2/cockpit-findings.json", {},
                                      ledger_dir=td)
            self.assertEqual(st, 200)
            self.assertEqual(p["counts"]["total"], 0)
            self.assertEqual(p["items"], [])


class TestCockpitKnowledge(unittest.TestCase):
    """知识库页数据：打法卡+哨兵规则+蒸馏草稿人审（knowledge/ 真文件只读）。"""

    @classmethod
    def setUpClass(cls):
        from webui import api_v2_cockpit as api
        cls.api = api
        st, payload = api.dispatch("/api/v2/cockpit-knowledge.json", {},
                                   ledger_dir=DEMO1)
        assert st == 200, payload
        cls.payload = payload

    def test_patterns_50_real_files(self):
        pats = self.payload["patterns"]
        idx = os.path.join(REPO, "knowledge", "cp-index.tsv")
        with open(idx, encoding="utf-8") as f:
            want = [l.split("\t") for l in f.read().splitlines()
                    if l.strip()][1:]
        self.assertEqual(len(pats), len(want))
        self.assertEqual(len(pats), 50)
        self.assertEqual(pats[0]["id"], "CP-0001")
        self.assertIn("SQL", pats[0]["title"])
        for p in pats:
            self.assertTrue(p["id"] and p["title"] and p["status"])

    def test_sentinels_14_real_rules(self):
        sens = self.payload["sentinels"]
        path = os.path.join(REPO, "knowledge", "engineering",
                            "sentinels-v1.tsv")
        with open(path, encoding="utf-8") as f:
            want = [l.split("\t") for l in f.read().splitlines()
                    if l.strip() and not l.startswith("#")][1:]
        self.assertEqual(len(sens), len(want))
        self.assertEqual(len(sens), 14)
        for s in sens:
            self.assertTrue(s["id"] and s["signal"])
            self.assertIn(s["action"], ("downgrade-to-fact", "reject",
                                        "mark-suspicious"))

    def test_staging_human_review_real_files(self):
        """蒸馏草稿人审入口：staging 表+待入册存量（盘上对账，诚实数）。"""
        stg = self.payload["staging"]
        self.assertIn("rows", stg)
        self.assertGreaterEqual(stg["pending_count"], 0)
        intake = os.path.join(REPO, "knowledge", "staging", "gensift-intake")
        self.assertTrue(os.path.isdir(intake))
        self.assertGreater(stg["intake_files"], 0)


class TestCockpitInbox(unittest.TestCase):
    """收件箱：待审批（revert_cmd 未销账推导）+求助（ask.md）+同类聚合。"""

    def _dispatch(self, ledger_dir, battles_dir=None):
        from webui import api_v2_cockpit as api
        return api.dispatch("/api/v2/cockpit-inbox.json", {},
                            ledger_dir=ledger_dir, battles_dir=battles_dir)

    def test_demo1_honest_empty(self):
        st, p = self._dispatch(DEMO1)
        self.assertEqual(st, 200)
        self.assertEqual(p["counts"]["pending_approvals"], 0)
        self.assertEqual(p["counts"]["asks"], 0)

    def test_pending_ask_and_grouping_from_fixture(self):
        T = core.TABLES
        with tempfile.TemporaryDirectory() as td:
            battles = os.path.join(td, "battles")
            g = os.path.join(battles, "battle-1", "G-a")
            os.makedirs(g, exist_ok=True)
            # 两笔带 revert_cmd 的待审行（哈希链按 core.row_hash 串好）
            specs = [("2026-10-20T01:00:00Z", "CLI", "", "add-goal G-i-0001",
                      ""),
                     ("2026-10-20T02:00:00Z", "CLI", "P2",
                      "run-tool A revert-me", "docker kill x1"),
                     ("2026-10-20T03:00:00Z", "CLI", "P2",
                      "run-tool B revert-me2", "docker kill x2")]
            rows_, prev = [], core.GENESIS
            for ts, actor, phase, event, revert in specs:
                r = [ts, actor, phase, event, revert, prev, "2"]
                h = core.row_hash(prev, r)
                r[T["timeline.tsv"].index("hash")] = h
                rows_.append(r)
                prev = h
            core.write_tsv(os.path.join(g, "timeline.tsv"), rows_)
            # 求助：battle 根 ask.md 非空（watchdog ask:human 通道同位）
            with open(os.path.join(battles, "battle-1", "ask.md"), "w",
                      encoding="utf-8") as f:
                f.write("士兵卡在登录墙，需要一把测试钥匙\n细节第二行\n")
            st, p = self._dispatch(os.path.join(td, "G-bare"), battles)
            self.assertEqual(st, 200)
            self.assertEqual(p["counts"]["pending_approvals"], 2)
            self.assertEqual(p["counts"]["asks"], 1)
            cmds = sorted(a["command"] for a in p["pending_approvals"])
            self.assertEqual(cmds, ["docker kill x1", "docker kill x2"])
            for a in p["pending_approvals"]:
                self.assertEqual(a["battle"], "battle-1")
                self.assertTrue(a["ts"] and a["event"])
            ask = p["asks"][0]
            self.assertEqual(ask["battle"], "battle-1")
            self.assertIn("钥匙", ask["question"])
            # 批量同类聚合：同工具两笔=一票组（首词聚合，一票展开审）
            groups = p["groups"]
            self.assertTrue(groups)
            self.assertEqual(groups[0]["count"], 2)
            self.assertEqual(groups[0]["label"], "docker kill")


if __name__ == "__main__":
    unittest.main()
