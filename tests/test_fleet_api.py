# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）·件③：总控数据端点 api_v2_fleet——TDD 红测试先行。

舰间契约（api_v2_tasks 同律）：本文件=本舰独写；只读投影零写入（一切文件 r 模式，
禁 datetime.now——输出确定性）；挂载=api_pages._OPTIONAL_MODULES guarded import
（落成即并网）；会话门在 server.py 挂载点（本模块零门禁）。

GET /api/v2/fleet.json →
  halted / cap{cap_soldiers, per_battle_soldiers, soldiers_active, headroom,
  queued} / battles[]{battle, goal_dir, state, soldiers, priority, heartbeat_at,
  deadline, four_q{found{total,verified,suspected}, running{count,intents},
  waiting{pending,blocked}, spend{tokens_used,usd_used,usd_cap}}} / counts{...}

四问口径（驾驶舱舰 blueprint 四问→仗级汇总）：
  ①打出什么漏洞了=findings 计数（verified/suspected 双色）
  ②正在打什么=intents status=active 的标题（≤5 条）
  ③什么在等我=intents status=pending/blocked 计数
  ④花多少钱=budget.tsv token 累计+舰队行 usd 已用/帽

跑法：python3 -m unittest tests.test_fleet_api -v
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from fleet import fleet_state as fs              # noqa: E402
from ledger import core                          # noqa: E402
from webui import api_v2_fleet as api            # noqa: E402

T = core.TABLES
TS1 = "2026-10-20T08:00:00Z"
TS2 = "2026-10-20T09:00:00Z"
ROUTE = "/api/v2/fleet.json"


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def _mk_root():
    root = tempfile.mkdtemp()
    gd = os.path.join(root, "battle-1", "G-w1")
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-1", exploitation_status="verified"),
        row("findings.tsv", id="FD-2", exploitation_status="verified"),
        row("findings.tsv", id="FD-3", exploitation_status="suspected"),
    ])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-1", title="打 admin 面板", status="active"),
        row("intents.tsv", id="INT-2", title="扫 vpn", status="pending"),
        row("intents.tsv", id="INT-3", title="待复核", status="blocked"),
        row("intents.tsv", id="INT-4", title="已完成", status="done"),
    ])
    core.write_tsv(os.path.join(gd, "budget.tsv"), [
        row("budget.tsv", timestamp=TS1, token_delta=12000, dollars_delta=1.5),
        row("budget.tsv", timestamp=TS2, token_delta=3400, dollars_delta=0.5),
    ])
    fs.register(root, "battle-1", gd, soldiers=3, budget_usd=2.0,
                budget_cap_usd=10.0, now_iso=TS1)
    fs.transition(root, "battle-1", "active", now_iso=TS2)
    fs.heartbeat(root, "battle-1", now_iso=TS2)
    fs.register(root, "battle-2", os.path.join(root, "battle-2", "G-w1"),
                soldiers=2, now_iso=TS2)          # 排队仗（目录不存在=诚实空）
    return root


class TestDispatch(unittest.TestCase):
    def test_foreign_route_none(self):
        root = _mk_root()
        self.assertIsNone(api.dispatch("/api/v2/other.json", {}, "/l", root))
        self.assertIsNone(api.dispatch("/p/fleet", {}, "/l", root))

    def test_fleet_json_shape(self):
        root = _mk_root()
        st, payload = api.dispatch(ROUTE, {}, "/ledger", root)
        self.assertEqual(st, 200)
        self.assertFalse(payload["halted"])
        cap = payload["cap"]
        self.assertEqual(cap["cap_soldiers"], 10)       # 缺省帽（无 fleet.json）
        self.assertEqual(cap["soldiers_active"], 3)
        self.assertEqual(cap["headroom"], 7)
        self.assertEqual(cap["queued"], 1)
        battles = {b["battle"]: b for b in payload["battles"]}
        self.assertEqual(battles["battle-1"]["state"], "active")
        self.assertEqual(battles["battle-2"]["state"], "queued")
        self.assertEqual(payload["counts"]["active"], 1)
        self.assertEqual(payload["counts"]["queued"], 1)

    def test_four_questions_per_battle(self):
        root = _mk_root()
        _st, payload = api.dispatch(ROUTE, {}, "/ledger", root)
        q = {b["battle"]: b["four_q"] for b in payload["battles"]}["battle-1"]
        self.assertEqual(q["found"], {"total": 3, "verified": 2, "suspected": 1})
        self.assertEqual(q["running"]["count"], 1)
        self.assertEqual(q["running"]["intents"], ["打 admin 面板"])
        self.assertEqual(q["waiting"], {"pending": 1, "blocked": 1})
        self.assertEqual(q["spend"]["tokens_used"], 15400)
        self.assertAlmostEqual(q["spend"]["usd_used"], 2.0)
        self.assertAlmostEqual(q["spend"]["usd_cap"], 10.0)

    def test_missing_goal_dir_honest_empty(self):
        root = _mk_root()
        _st, payload = api.dispatch(ROUTE, {}, "/ledger", root)
        q = {b["battle"]: b["four_q"] for b in payload["battles"]}["battle-2"]
        self.assertEqual(q["found"]["total"], 0)
        self.assertEqual(q["spend"]["tokens_used"], 0)

    def test_deterministic_two_calls_equal(self):
        root = _mk_root()
        a = api.dispatch(ROUTE, {}, "/l", root)
        b = api.dispatch(ROUTE, {}, "/l", root)
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))

    def test_empty_root_honest(self):
        root = tempfile.mkdtemp()
        st, payload = api.dispatch(ROUTE, {}, "/l", root)
        self.assertEqual(st, 200)
        self.assertEqual(payload["battles"], [])
        self.assertEqual(payload["cap"]["soldiers_active"], 0)

    def test_halted_flag_surfaced(self):
        root = _mk_root()
        fs.set_meta(root, "halted", "1", now_iso=TS2, reason="incident")
        _st, payload = api.dispatch(ROUTE, {}, "/l", root)
        self.assertTrue(payload["halted"])

    def test_readonly_zero_writes(self):
        """只读投影：dispatch 前后 fleet.tsv/审计字节零变化。"""
        root = _mk_root()

        def _read(name):
            with open(os.path.join(root, name), "rb") as f:
                return f.read()

        before, audit_before = _read(fs.FLEET_TSV), _read(fs.AUDIT_TSV)
        api.dispatch(ROUTE, {}, "/l", root)
        self.assertEqual(_read(fs.FLEET_TSV), before)
        self.assertEqual(_read(fs.AUDIT_TSV), audit_before)


class TestMount(unittest.TestCase):
    def test_route_registered_in_pages_mount(self):
        from webui import api_pages
        routes = api_pages.mounted_v2_routes()
        self.assertEqual(routes.get(ROUTE), "api_v2_fleet")

    def test_routes_table_single_source(self):
        self.assertEqual(list(api.ROUTES.keys()), [ROUTE])


if __name__ == "__main__":
    unittest.main()
