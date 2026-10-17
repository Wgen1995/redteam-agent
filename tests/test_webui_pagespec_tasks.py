# -*- coding: utf-8 -*-
"""T5·P3 任务列表 + P4 新建任务——页钉测（界面线施工计划 2026-10-18 T5）。

python3 -m unittest tests.test_webui_pagespec_tasks
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P3；状态机 docs/design/task-lifecycle-v1.md
（12 态→界面七态子集投影）；文案宪法#41（界面人话律——「任务」不说「战」）。

三层钉（与 finding-detail/broadcast 同形）：
  ①投影层  api_v2_tasks.tasks_view——battles 注册表+goals+findings+budget+
           timeline 聚合（每仗一行： 名称/目标/状态徽章/预算已用vs帽[80% 预算
           预警线]/发现数[已验证/待验证双色]/更新时间）；
  ②挂载层  api_pages.py 未落地（UI-1 在飞）——Handler 子类钉 include 挂法：
           /api/v2/* 全过会话门（无 cookie=401 JSON），分发给 ROUTES 单源表；
  ③页面层  static/pages/tasks.html 结构钉（表列+四态+筛选[状态/时间]+搜索+
           「新建任务」主钮+预算进度条琥珀线+分页 20/页+nav.push 自注册）。
"""
import json
import os
import subprocess
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core                     # noqa: E402
from webui import api_v2_tasks as api       # noqa: E402
from webui import server as srv_mod         # noqa: E402

T = core.TABLES
TS1 = "2026-10-18T01:00:00Z"
TS2 = "2026-10-18T02:00:00Z"
TS3 = "2026-10-18T03:00:00Z"
TS4 = "2026-10-18T04:00:00Z"
TS5 = "2026-10-18T05:00:00Z"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(specs):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in specs:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def write_tsv(path, rows_):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    core.write_tsv(path, rows_)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


GOAL_KW = dict(id="G-x-0001", target="shop.example", objective="外网一期渗透测试",
               auth_doc="AUTH-1.pdf", auth_sha256="a" * 64, signer="王安全（CISO）",
               valid_from="2026-10-18T00:00:00Z", valid_until="2026-10-25T00:00:00Z",
               emergency_contact="13800000000", budget="2M;50000;40",
               business_context="凭据来源：客户提供；说明：外网一期",
               model_tier="strong", guard_tier="T3",
               schema_version="2", created=TS1)


def goal_row(**over):
    kw = dict(GOAL_KW)
    kw.update(over)
    return row("goals.tsv", **kw)


def battle_path(battles, n, gen="G-a"):
    return os.path.join(battles, "battle-%d" % n, gen)


def runner_tsv(battles, n, lines):
    _write(os.path.join(battles, "battle-%d" % n, "opencode-run.log.runner.tsv"),
           "".join(lines))


def add_scope(battles, n, gen="G-a"):
    """八问③：一 include 行（在册 battle 必有范围——server 建战即录）。"""
    write_tsv(os.path.join(battle_path(battles, n, gen), "scope.tsv"), [
        row("scope.tsv", id="S-1", kind="include", matcher="*.example.com",
            schema_version="2", created=TS1),
    ])


def dead_pid():
    """确死 pid：子进程已收尸（registry 死尸回收同判据 os.kill ESRCH）。"""
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def build_fixture(battles):
    """九仗夹具：每态一仗（草稿/待授权/待点火/执行中/复测/待签发/已签发/已归档/
    已中止）+ 预算琥珀线(80%)+发现双色计数+多代自然序合并。"""
    os.makedirs(battles, exist_ok=True)

    # battle-1 草稿：无 goals.tsv（仅 timeline 立项行）
    write_tsv(os.path.join(battle_path(battles, 1), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-d-0001")]))

    # battle-2 待授权：goals 在但八问缺件（无 sha256/窗口/联系人/强度档）+零范围
    write_tsv(os.path.join(battle_path(battles, 2), "goals.tsv"),
              [goal_row(id="G-p-0001", auth_sha256="", signer="",
                        valid_from="", valid_until="", emergency_contact="",
                        budget="", model_tier="", guard_tier="")])
    write_tsv(os.path.join(battle_path(battles, 2), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-p-0001")]))

    # battle-3 已授权待点火：八问齐+范围在册，无 runner
    write_tsv(os.path.join(battle_path(battles, 3), "goals.tsv"),
              [goal_row(id="G-m-0001", budget="200000;5000;4")])
    write_tsv(os.path.join(battle_path(battles, 3), "scope.tsv"), [
        row("scope.tsv", id="S-1", kind="include", matcher="*.example.com",
            schema_version="2", created=TS1),
        row("scope.tsv", id="S-2", kind="include", matcher="10.0.0.0/24",
            schema_version="2", created=TS1),
    ])
    write_tsv(os.path.join(battle_path(battles, 3), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-m-0001"),
                          (TS2, "CLI", "", "add-scope S-1")]))

    # battle-4 执行中：registry 在册活 pid
    add_scope(battles, 4)
    write_tsv(os.path.join(battle_path(battles, 4), "goals.tsv"),
              [goal_row(id="G-r-0001", budget="100000;5000;4")])
    write_tsv(os.path.join(battle_path(battles, 4), "budget.tsv"), [
        row("budget.tsv", timestamp=TS2, token_delta=80000, requests_delta=100,
            hours_delta=1, scope="goal", note="探测", schema_version="2"),
    ])
    write_tsv(os.path.join(battle_path(battles, 4), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-r-0001"),
                          (TS2, "CLI", "P1", "add-intent INT-r-0001"),
                          (TS3, "CLI", "P1", "add-finding FD-r-0001")]))
    write_tsv(os.path.join(battle_path(battles, 4), "findings.tsv"), [
        row("findings.tsv", id="FD-r-0001", title="反射 XSS", impact="中",
            exploitation_status="verified", status="active",
            schema_version="2", created=TS3),
        row("findings.tsv", id="FD-r-0002", title="弱口令", impact="低",
            exploitation_status="suspected", status="active",
            schema_version="2", created=TS3),
    ])
    runner_tsv(battles, 4, ["2026-10-18T01z\tBOOT\tpid=11\n",
                            "2026-10-18T01z\tLAUNCH\tround=1\n",
                            "2026-10-18T02z\tPROGRESS\ttimeline=3\n"])
    _write(os.path.join(battles, "registry.json"), json.dumps({
        "schema_version": 1,
        "entries": {"4": {"pid": os.getpid(), "budget_usd": 0, "ports": [],
                          "registered_at": "2026-10-18T01:00:00Z"}}}))

    # battle-5 复测：runner 完跑+timeline 有 replay 行+发现三色+预算 80% 琥珀线
    add_scope(battles, 5)
    write_tsv(os.path.join(battle_path(battles, 5), "goals.tsv"),
              [goal_row(id="G-t-0001", budget="2M;50000;40")])
    write_tsv(os.path.join(battle_path(battles, 5), "budget.tsv"), [
        row("budget.tsv", timestamp=TS2, token_delta=1600000, requests_delta=40000,
            hours_delta=32, scope="goal", note="波次一", schema_version="2"),
    ])
    write_tsv(os.path.join(battle_path(battles, 5), "findings.tsv"), [
        row("findings.tsv", id="FD-t-0001", title="SQL 注入", impact="高",
            exploitation_status="verified", status="active",
            schema_version="2", created=TS2),
        row("findings.tsv", id="FD-t-0002", title="越权读取", impact="中",
            exploitation_status="verified", status="active",
            schema_version="2", created=TS2),
        row("findings.tsv", id="FD-t-0003", title="信息泄露", impact="低",
            exploitation_status="suspected", status="active",
            schema_version="2", created=TS2),
        row("findings.tsv", id="FD-t-0004", title="误报已排除", impact="低",
            exploitation_status="ruled_out", status="active",
            schema_version="2", created=TS2),
    ])
    write_tsv(os.path.join(battle_path(battles, 5), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-t-0001"),
                          (TS2, "CLI", "P3", "add-finding FD-t-0001"),
                          (TS3, "replay", "P4",
                           "replay-probe EV-t-0001 verdict=reproduced"),
                          (TS4, "CLI", "P4", "replay:EV-t-0001:VERIFIED")]))
    runner_tsv(battles, 5, ["2026-10-18T01z\tDONE\tfinal_rc=0 restarts=0 timeline=4\n"])

    # battle-6 待签发：复测完+报告草稿在（render 工件）
    add_scope(battles, 6)
    write_tsv(os.path.join(battle_path(battles, 6), "goals.tsv"),
              [goal_row(id="G-s-0001")])
    write_tsv(os.path.join(battle_path(battles, 6), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-s-0001"),
                          (TS2, "replay", "P4",
                           "replay-probe EV-s-0001 verdict=reproduced")]))
    _write(os.path.join(battle_path(battles, 6), "report", "draft",
                        "v1.md"), "# 报告草稿\n")

    # battle-7 已签发：report/signed/pass.json 在场
    add_scope(battles, 7)
    write_tsv(os.path.join(battle_path(battles, 7), "goals.tsv"),
              [goal_row(id="G-g-0001")])
    write_tsv(os.path.join(battle_path(battles, 7), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-g-0001"),
                          (TS5, "总控", "P5", "disclosure 报告签发")]))
    _write(os.path.join(battle_path(battles, 7), "report", "signed",
                        "pass.json"), "{}")
    _write(os.path.join(battle_path(battles, 7), "report", "signed",
                        "report-20261018T050000Z.md"), "# 签发稿\n")

    # battle-8 已归档：归档清单在场（battle 目录根）
    add_scope(battles, 8)
    write_tsv(os.path.join(battle_path(battles, 8), "goals.tsv"),
              [goal_row(id="G-arc-0001")])
    _write(os.path.join(battles, "battle-8", "archive-manifest.json"),
           '{"schema_version": 1, "files": {}}')

    # battle-9 已中止：runner 非零退
    add_scope(battles, 9)
    write_tsv(os.path.join(battle_path(battles, 9), "goals.tsv"),
              [goal_row(id="G-ab-0001")])
    write_tsv(os.path.join(battle_path(battles, 9), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-ab-0001")]))
    runner_tsv(battles, 9, ["2026-10-18T01z\tDONE\tfinal_rc=1 restarts=0 timeline=1\n"])

    # battle-11 多代自然序：G-r2（旧）+G-r10（新）——目标/时间线取新代合并律
    add_scope(battles, 11, "G-r10")
    write_tsv(os.path.join(battle_path(battles, 11, "G-r2"), "goals.tsv"),
              [goal_row(id="G-r2-0001", target="old.example",
                        budget="100;10;1")])
    write_tsv(os.path.join(battle_path(battles, 11, "G-r2"), "timeline.tsv"),
              chained_tl([(TS1, "CLI", "", "add-goal G-r2-0001")]))
    write_tsv(os.path.join(battle_path(battles, 11, "G-r10"), "goals.tsv"),
              [goal_row(id="G-r10-0001", target="new.example",
                        budget="1000;100;10")])
    write_tsv(os.path.join(battle_path(battles, 11, "G-r10"), "timeline.tsv"),
              chained_tl([(TS2, "CLI", "", "add-goal G-r10-0001"),
                          (TS3, "CLI", "P1", "add-intent INT-r10-0001")]))
    return battles


def dir_bytes(root):
    out = {}
    for r, _d, files in os.walk(root):
        for n in sorted(files):
            p = os.path.join(r, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.battles = build_fixture(os.path.join(self.td.name, "battles"))


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestTasksProjection(Base):
    """每仗一行聚合：名称/目标/状态徽章（12→7 态投影）/预算琥珀线/发现双色/
    更新时间/多代合并律/只读确定性。"""

    def view(self, **kw):
        kw.setdefault("battles_dir", self.battles)
        return api.tasks_view(**kw)

    def by_n(self):
        return {b["n"]: b for b in self.view()["battles"]}

    def test_all_battles_listed_with_identity(self):
        d = self.by_n()
        self.assertEqual(sorted(d), [1, 2, 3, 4, 5, 6, 7, 8, 9, 11])
        b5 = d[5]
        self.assertEqual(b5["battle"], "battle-5")
        self.assertEqual(b5["name"], "shop.example")
        self.assertEqual(b5["objective"], "外网一期渗透测试")
        self.assertEqual(b5["goal_id"], "G-t-0001")

    def test_state_seven_bucket_projection(self):
        """task-lifecycle 12 态→界面七态子集（异常终态诚实保留）。"""
        d = self.by_n()
        self.assertEqual(d[1]["state"]["label"], "草稿")
        self.assertEqual(d[2]["state"]["label"], "待授权")
        self.assertEqual(d[3]["state"]["label"], "执行中")
        self.assertEqual(d[3]["state"]["detail"], "已授权 · 待点火")
        self.assertEqual(d[4]["state"]["label"], "执行中")
        self.assertEqual(d[5]["state"]["label"], "复测")
        self.assertEqual(d[6]["state"]["label"], "待签发")
        self.assertEqual(d[7]["state"]["label"], "已签发")
        self.assertEqual(d[8]["state"]["label"], "已归档")
        self.assertEqual(d[9]["state"]["label"], "已中止")
        for b in d.values():
            self.assertIn(b["state"]["label"],
                          ("草稿", "待授权", "执行中", "复测", "待签发",
                           "已签发", "已归档", "已中止", "环境失败"))

    def test_state_codes_raw_lifecycle(self):
        d = self.by_n()
        self.assertEqual(d[1]["state"]["code"], "DRAFT")
        self.assertEqual(d[2]["state"]["code"], "AUTH-PENDING")
        self.assertEqual(d[3]["state"]["code"], "ARMED")
        self.assertEqual(d[4]["state"]["code"], "RUNNING")
        self.assertEqual(d[5]["state"]["code"], "RETESTING")
        self.assertEqual(d[6]["state"]["code"], "SIGN-PENDING")
        self.assertEqual(d[7]["state"]["code"], "SIGNED")
        self.assertEqual(d[8]["state"]["code"], "ARCHIVED")
        self.assertEqual(d[9]["state"]["code"], "ABORTED")

    def test_budget_used_vs_cap_with_amber_line(self):
        """预算已用 vs 帽：2M 帽用 1.6M=80.0%——预警线口径（≥80=预警）。"""
        d = self.by_n()
        bud = d[5]["budget"]["token"]
        self.assertEqual(bud["used"], 1600000)
        self.assertEqual(bud["cap"], 2000000)
        self.assertAlmostEqual(bud["pct"], 80.0)
        self.assertTrue(bud["warn"])                     # 80% 整=预警
        self.assertFalse(bud["over"])
        b4 = d[4]["budget"]["token"]                     # 80%=80
        self.assertEqual(b4["used"], 80000)
        self.assertEqual(b4["cap"], 100000)
        self.assertTrue(b4["warn"])
        b3 = d[3]["budget"]["token"]                     # 0%=不预警
        self.assertEqual(b3["used"], 0)
        self.assertFalse(b3["warn"])
        self.assertEqual(d[5]["budget"]["requests"]["used"], 40000)
        self.assertEqual(d[5]["budget"]["hours"]["used"], 32)

    def test_budget_cap_suffix_parse(self):
        """帽三段解析：2M=2,000,000（K/M 后缀）；原始串随行。"""
        d = self.by_n()
        self.assertEqual(d[5]["budget"]["raw"], "2M;50000;40")
        self.assertEqual(d[5]["budget"]["requests"]["cap"], 50000)
        self.assertEqual(d[5]["budget"]["hours"]["cap"], 40)

    def test_findings_dual_counts(self):
        """发现计数双色：已验证/待验证（已失效单列不入待验证）。"""
        d = self.by_n()
        f5 = d[5]["findings"]
        self.assertEqual(f5["total"], 4)
        self.assertEqual(f5["verified"], 2)
        self.assertEqual(f5["pending"], 1)
        self.assertEqual(f5["ruled_out"], 1)
        f4 = d[4]["findings"]
        self.assertEqual(f4["verified"], 1)
        self.assertEqual(f4["pending"], 1)
        self.assertEqual(d[3]["findings"]["total"], 0)

    def test_times_start_and_update(self):
        """开始=goals.created；更新=timeline 末行时刻（多代合并后全序）。"""
        d = self.by_n()
        self.assertEqual(d[5]["created"], TS1)
        self.assertEqual(d[5]["updated"], TS4)
        self.assertEqual(d[4]["updated"], TS3)
        self.assertEqual(d[7]["updated"], TS5)

    def test_multigen_natural_order_latest_goal(self):
        """G-r2<G-r10 自然序：目标/帽取最新代，时间线跨代合并。"""
        d = self.by_n()
        b11 = d[11]
        self.assertEqual(b11["goal"], "G-r10")
        self.assertEqual(b11["name"], "new.example")
        self.assertEqual(b11["budget"]["token"]["cap"], 1000)
        self.assertEqual(b11["updated"], TS3)

    def test_draft_battle_no_goal_row(self):
        d = self.by_n()
        b1 = d[1]
        self.assertEqual(b1["name"], "")
        self.assertEqual(b1["state"]["label"], "草稿")
        self.assertEqual(b1["updated"], TS1)

    def test_counts_and_state_filter_vocab(self):
        d = self.view()
        self.assertEqual(d["counts"]["battles"], 10)
        self.assertEqual(d["counts"]["by_label"]["执行中"], 3)   # 3 待点火+4 在跑+11 待点火
        self.assertEqual(d["counts"]["by_label"]["已签发"], 1)
        labels = [s["label"] for s in d["states"]]
        self.assertEqual(labels[0], "全部")
        for want in ("草稿", "待授权", "执行中", "复测", "待签发", "已签发", "已归档"):
            self.assertIn(want, labels)

    def test_empty_battles_root(self):
        st, p = api.tasks_route({}, battles_dir=os.path.join(self.td.name, "none"))
        self.assertEqual(st, 200)
        self.assertEqual(p["battles"], [])
        self.assertEqual(p["counts"]["battles"], 0)

    def test_readonly_deterministic_json(self):
        before = dir_bytes(self.battles)
        a = self.view()
        b = self.view()
        self.assertEqual(dir_bytes(self.battles), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_route_adapter_and_dispatch(self):
        st, p = api.tasks_route({}, battles_dir=self.battles)
        self.assertEqual(st, 200)
        self.assertEqual(len(p["battles"]), 10)
        self.assertIsNone(api.dispatch("/api/v2/nope", {}, battles_dir=self.battles))
        st2, p2 = api.dispatch("/api/v2/tasks.json", {}, battles_dir=self.battles)
        self.assertEqual(st2, 200)
        self.assertEqual(p2, p)


class TestRegistryLiveness(Base):
    """registry 活性投影：死 pid 回收=不执行中；册缺=不炸。"""

    def test_dead_pid_entry_not_running(self):
        _write(os.path.join(self.battles, "registry.json"), json.dumps({
            "schema_version": 1,
            "entries": {"5": {"pid": dead_pid(), "budget_usd": 0, "ports": [],
                              "registered_at": TS1}}}))
        d = {b["n"]: b for b in api.tasks_view(battles_dir=self.battles)["battles"]}
        self.assertEqual(d[5]["state"]["code"], "RETESTING")   # 死尸回收回真实态

    def test_broken_registry_tolerated(self):
        _write(os.path.join(self.battles, "registry.json"), "{broken")
        st, p = api.tasks_route({}, battles_dir=self.battles)
        self.assertEqual(st, 200)                               # 坏册=不执法不炸页
        self.assertEqual(p["counts"]["battles"], 10)


# ═══════════════════════════════ ② 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 未落地，UI-1 在飞）：/api/v2/* 过会话门后
    分发 ROUTES 单源表——dispatch(path, query, ledger_dir, battles_dir)。"""

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path.startswith("/api/v2/") or u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            res = api.dispatch(u.path, q, self.server.ledger_dir,
                               battles_dir=self.server.battles_dir or None)
            if res is not None:
                status, payload = res
                return self._send(status, "application/json",
                                  json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(
            ("127.0.0.1", 0), _V2MountHandler,
            ledger_dir=os.path.join(self.battles, "battle-5", "G-a"),
            operator_key=webui_login.OP_KEY, battles_dir=self.battles)
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
        conn, resp = self._get("/api/v2/tasks.json", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_tasks_over_http(self):
        conn, resp = self._get("/api/v2/tasks.json")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["counts"]["battles"], 10)
        by = {b["n"]: b for b in p["battles"]}
        self.assertEqual(by[5]["state"]["label"], "复测")
        self.assertTrue(by[5]["budget"]["token"]["warn"])
        conn.close()

    def test_unknown_v2_path_falls_through_404(self):
        conn, resp = self._get("/api/v2/nope")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_http_hits_readonly(self):
        before = dir_bytes(self.battles)
        conn, resp = self._get("/api/v2/tasks.json")
        self.assertEqual(resp.status, 200)
        resp.read()
        conn.close()
        self.assertEqual(dir_bytes(self.battles), before)


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "tasks.html")
ZONE_MARKS = (
    # 工具栏：搜索+状态筛选+时间筛选+「新建任务」主钮
    'id="q-search"', 'id="f-state"', 'id="f-time"', 'id="btn-new"',
    # 表列：名称/目标/状态徽章/预算进度条(80% 预算预警线)/发现双色/更新时间
    'id="tasks-tbody"', "c-name", "c-target", "c-state", "c-budget", "c-findings",
    "c-updated", 'id="tbl-tasks"',
    # 预算进度条+琥珀线（80% 预算预警线——宪法#41 人话词）
    "amber-line", "预算预警线",
    # 发现双色
    "fv-ok", "fv-pend",
    # 四态
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 分页 20/页
    'id="pager"', "20",
    # 行点击进任务详情
    "openDetail",
    # 状态徽章七态词（task-lifecycle 界面子集）
    "草稿", "待授权", "执行中", "复测", "待签发", "已签发", "已归档",
)
FETCH_MARKS = ("'/api/v2/tasks.json",)


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

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'tasks'", src)
        self.assertIn("label: '任务列表'", src)
        self.assertIn("typeof nav.push", src)               # 壳未落也不炸

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)                   # 零 CDN

    def test_page_over_400_lines_js_under_1500(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 1500)
        self.assertGreaterEqual(len(src.splitlines()), 400, "P3 全量页量纲")

    def test_js_hygiene_strict_loop_vars(self):
        """'use strict' 下裸循环变量=ReferenceError（finding-detail 教训钉）。"""
        import re as _re
        src = self._src()
        js = src.split("<script>")[1].split("</script>")[0]
        for m in _re.finditer(r"for\s*\(([^)]{0,40})", js):
            self.assertTrue(m.group(1).lstrip().startswith("var "),
                            "循环变量须 var 声明（严格模式）: " + m.group(0))

    def test_copy_standard_no_jargon(self):
        """宪法#41：界面只说人话——战/战役/开战不上屏。"""
        src = self._src()
        for bad in ("开战", "战役", "战报", "看战况", "管战场"):
            self.assertNotIn(bad, src.split("<script>")[0] or
                             src.split("<script>")[0] + "x", "黑话上屏: " + bad)


if __name__ == "__main__":
    unittest.main()
