# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）·件①：多仗常驻总控 supervisor——TDD 红测试先行。

设计源：docs/design/2026-10-20-build-master-plan.md R14（多任务治理舰：总并发帽+
supervisor 舰队化）+裁决书 §十八。与 planner_loop 的分界（本测试即分界钉）：
planner_loop=仗内派活（一仗 goal 内可达空格×五因子→add-intent）；supervisor=仗间
治理（多仗并发帽/排队/优先级/停续查/全停）——supervisor 零意图铸造、零空格排序。

Ruling（写测试即写契约）：
- R-FLT-1 全局并发帽：cap_soldiers=全舰队总士兵上限；Σactive.soldiers+新仗申报
  ≤帽 →active；超帽 →queued（排队不开工，绝不挤占）。headroom=帽-Σactive。
- R-FLT-2 单仗配额继承：register 不报 soldiers=继承 fleet.json per_battle_soldiers；
  显式申报须≥1。帽/配额/权重全走 fleet.json（fail-loud 校验，planner_score 同律）。
- R-FLT-3 仗间优先级=五因子加权（复用 planner_score 思想、输入换仗级）：
  budget_margin（预算余量）/deadline_urgency（截止）/heat（白热=近窗账本活跃）/
  yield（发现产出）/wait_age（排队等待）——0-1 加权、权重和≤1、明细可解释
  （factor_detail 全因子入串）、同分按仗名字典序（确定性）。
- R-FLT-4 停/续/查三命令面：stop(仗|None=全停)→paused+warrior-stop 事件入该仗
  timeline（复用 warrior.steer 既有 halt 单源——战士 scan 即停）；resume(仗)→
  active，帽满→queued（诚实排队）；status()=帽余量/队列/停摆/在途一览。
- R-FLT-5 全停阀：emergency stop=halted 旗入 fleet-meta+所有非终态仗 paused+
  每仗 timeline 铸 warrior-stop（对账本可见的全部战士 id）——幂等（二停零追加）；
  停后 promote/register 全部不开新仗（无新意图铸出：队列不升格、新仗只排队）；
  halted 跨重启持久（恢复不复活）。
- R-FLT-6 心跳超时：tick() 从仗 timeline 同步 warrior-heartbeat →fleet 心跳列；
  active 且心跳超 timeout →failed（审计带因），腾帽促升格。
- R-FLT-7 断电恢复：recover()=读注册表重建在途集（active 原样保留不双开、
  queued 原样排队、终态不动）；重复 register 同名仗=already-registered 零变更。

跑法：python3 -m unittest tests.test_fleet_supervisor -v
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from fleet import fleet_state as fs                # noqa: E402
from fleet import supervisor as sup                # noqa: E402
from ledger import timeline as TL                  # noqa: E402
from ledger.enforce import parse_ts                # noqa: E402
from warrior import steer                          # noqa: E402

TS1 = "2026-10-20T08:00:00Z"
TS2 = "2026-10-20T09:00:00Z"
TS3 = "2026-10-20T10:00:00Z"
E1 = parse_ts(TS1)
E2 = parse_ts(TS2)
E3 = parse_ts(TS3)

FIXTURE_CFG = {"cap_soldiers": 4, "per_battle_soldiers": 2}


class FakeClock(object):
    """可拨的钟：now_fn 注入（planner_loop FakeClock 同法）。"""

    def __init__(self, t):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def _mkgoal(tmp, name, warrior_events=(), ts=TS1):
    """造一个带 timeline 的仗账本目录（warrior-start/warrior-heartbeat 可选）。"""
    gd = os.path.join(tmp, "goals", name)
    os.makedirs(gd, exist_ok=True)
    for ev in warrior_events:
        TL.append_tl_locked(gd, ts, ev, actor="warrior:W-1", phase="P-lifecycle")
    return gd


def _mk_sup(tmp, cfg=None, t=E2):
    clock = FakeClock(t)
    s = sup.FleetSupervisor(tmp, config=cfg, now_fn=clock)
    return s, clock


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_default_config_when_missing(self):
        cfg = sup.load_config(self.root)
        self.assertGreater(cfg["cap_soldiers"], 0)
        self.assertGreater(cfg["per_battle_soldiers"], 0)
        self.assertAlmostEqual(sum(cfg["weights"].values()), 1.0, places=6)

    def test_config_file_overrides(self):
        with open(os.path.join(self.root, sup.CONFIG_NAME), "w",
                  encoding="utf-8") as f:
            json.dump({"cap_soldiers": 7, "per_battle_soldiers": 3}, f)
        cfg = sup.load_config(self.root)
        self.assertEqual(cfg["cap_soldiers"], 7)
        self.assertEqual(cfg["per_battle_soldiers"], 3)

    def test_config_fail_loud_bad_cap(self):
        for bad in (0, -1):
            with open(os.path.join(self.root, sup.CONFIG_NAME), "w",
                      encoding="utf-8") as f:
                json.dump({"cap_soldiers": bad}, f)
            with self.assertRaises(ValueError):
                sup.load_config(self.root)

    def test_config_fail_loud_bad_weights(self):
        with open(os.path.join(self.root, sup.CONFIG_NAME), "w",
                  encoding="utf-8") as f:
            json.dump({"weights": {"budget_margin": 2.0}}, f)
        with self.assertRaises(ValueError):
            sup.load_config(self.root)

    def test_config_unknown_weight_raises(self):
        with open(os.path.join(self.root, sup.CONFIG_NAME), "w",
                  encoding="utf-8") as f:
            json.dump({"weights": {"nope": 0.5}}, f)
        with self.assertRaises(ValueError):
            sup.load_config(self.root)


class TestAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_admit_within_cap_activates(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        gd = _mkgoal(self.tmp, "b1")
        v = s.register("battle-1", gd, soldiers=2)
        self.assertEqual(v["state"], "active")
        self.assertEqual(v["soldiers"], 2)
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["state"], "active")

    def test_admit_inherits_per_battle_quota(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, per_battle_soldiers=2))
        v = s.register("battle-1", _mkgoal(self.tmp, "b1"))
        self.assertEqual(v["soldiers"], 2)     # 未申报=继承配额

    def test_over_cap_queues_not_activates(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=3)
        v = s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=3)
        self.assertEqual(v["state"], "queued")
        self.assertIn("cap", v["reason"])
        self.assertEqual(fs.row_of(self.tmp, "battle-2")["state"], "queued")

    def test_headroom_math_partial_fit_still_queues(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=3)
        v = s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=2)
        self.assertEqual(v["state"], "queued")   # 余 1<2 不开工（不缩配抢跑）

    def test_register_bad_soldiers_raises(self):
        s, _ = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        for bad in (0, -1):
            with self.assertRaises(ValueError):
                s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=bad)

    def test_queue_promotion_on_capacity_free(self):
        s, clock = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=3)
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=3)
        s.register("battle-3", _mkgoal(self.tmp, "b3"), soldiers=1)
        self.assertEqual(fs.row_of(self.tmp, "battle-3")["state"], "active")
        # battle-1 收仗 →帽腾 3 →battle-2 升格
        s.finish("battle-1")
        r = s.tick()
        self.assertEqual(fs.row_of(self.tmp, "battle-2")["state"], "active")
        self.assertIn("battle-2", r["promoted"])

    def test_promotion_respects_fit(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=3)
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=3)
        s.register("battle-3", _mkgoal(self.tmp, "b3"), soldiers=3)
        s.finish("battle-1")
        s.tick()
        # 余 3：battle-2 与 battle-3 都要 3——只升一个（先按分）
        actives = [b for b in fs.rows(self.tmp)
                   if b["state"] == "active"]
        self.assertEqual(len(actives), 1)

    def test_halted_register_forced_queued(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=10))
        s.emergency_stop("drill")
        v = s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        self.assertEqual(v["state"], "queued")   # 全停期新仗只排队不开工
        self.assertIn("halt", v["reason"])


class TestPriority(unittest.TestCase):
    """仗间优先级五因子——纯函数钉（R-FLT-3）。"""

    BASE = {
        "budget_used_usd": 20.0, "budget_cap_usd": 100.0,
        "deadline": None, "recent_events": 0, "findings": 0,
        "queued_at": None,
    }

    def _score(self, **kw):
        stats = dict(self.BASE)
        stats.update(kw)
        return sup.battle_factors(stats, E3, sup.DEFAULT_CONFIG)

    def test_budget_margin_direction(self):
        rich, poor = self._score(budget_used_usd=10.0), \
            self._score(budget_used_usd=95.0)
        self.assertGreater(rich[1]["budget_margin"],
                           poor[1]["budget_margin"])
        self.assertGreater(rich[0], poor[0])

    def test_budget_margin_unknown_cap_neutral(self):
        _s, f = self._score(budget_cap_usd=0.0)
        self.assertEqual(f["budget_margin"], 0.5)

    def test_deadline_urgent_beats_far(self):
        urgent = self._score(deadline=TS3)                       # 此刻截止
        far = self._score(deadline="2026-10-27T08:00:00Z")       # 7 天后
        none_ = self._score(deadline=None)
        self.assertGreater(urgent[1]["deadline_urgency"],
                           far[1]["deadline_urgency"])
        self.assertEqual(none_[1]["deadline_urgency"], 0.5)      # 无截止=中性

    def test_heat_factor(self):
        hot, cold = self._score(recent_events=50), self._score(recent_events=0)
        self.assertGreater(hot[1]["heat"], cold[1]["heat"])
        self.assertEqual(hot[1]["heat"], 1.0)

    def test_yield_and_wait_age(self):
        rich, starved = self._score(findings=10), self._score(findings=0)
        self.assertGreater(rich[1]["yield"], starved[1]["yield"])
        old = self._score(queued_at=TS1)                          # 已等 2h
        new = self._score(queued_at=TS3)
        self.assertGreater(old[1]["wait_age"], new[1]["wait_age"])

    def test_factor_detail_explainable(self):
        _s, f = self._score()
        detail = sup.factor_detail(f)
        for name in ("budget_margin", "deadline_urgency", "heat",
                     "yield", "wait_age"):
            self.assertIn(name, detail)      # 可解释律：为什么它排第一

    def test_rank_queued_deterministic_order(self):
        rows = [
            {"battle": "battle-2", "soldiers": "1", "queued_at": TS1,
             "budget_usd": "90", "budget_cap_usd": "100", "deadline": ""},
            {"battle": "battle-1", "soldiers": "1", "queued_at": TS1,
             "budget_usd": "10", "budget_cap_usd": "100", "deadline": ""},
        ]
        ranked = sup.rank_battles(rows, {"battle-2": _gd_stats(90),
                                         "battle-1": _gd_stats(10)},
                                  E3, sup.DEFAULT_CONFIG)
        self.assertEqual([r["battle"] for r in ranked],
                         ["battle-1", "battle-2"])   # 余量多者先，同分名字典序


def _gd_stats(used):
    return {"budget_used_usd": float(used), "budget_cap_usd": 100.0,
            "deadline": None, "recent_events": 0, "findings": 0,
            "queued_at": None}


class TestStopResumeStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_stop_battle_pauses_and_signals_warriors(self):
        gd = _mkgoal(self.tmp, "b1", [
            "warrior-start battle=battle-1 warrior=warrior:W-1 pid=101",
            "warrior-heartbeat warrior=warrior:W-1 intent=INT-g1-0001",
        ])
        s, clock = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", gd, soldiers=2)
        v = s.stop("battle-1", reason="operator-halt")
        self.assertEqual(v["state"], "paused")
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["state"], "paused")
        # 既有 halt 机制单源复用：战士 scan 到 stop_reason
        st = steer.scan(gd, "warrior:W-1", 0)
        self.assertIsNotNone(st.stop_reason)
        self.assertIn("operator-halt", st.stop_reason)

    def test_stop_writes_fleet_bookkeeping_event(self):
        gd = _mkgoal(self.tmp, "b1")
        s, _ = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        s.register("battle-1", gd, soldiers=2)
        s.stop("battle-1", reason="r1")
        evs = [r[3] for r in TL.read_rows(gd)]
        self.assertTrue(any(e.startswith("fleet-stop battle=battle-1") for e in evs))

    def test_stop_idempotent(self):
        gd = _mkgoal(self.tmp, "b1", ["warrior-start battle=battle-1 "
                                      "warrior=warrior:W-1 pid=1"])
        s, _ = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        s.register("battle-1", gd, soldiers=2)
        s.stop("battle-1", reason="r")
        n_tl = len(TL.read_rows(gd))
        v = s.stop("battle-1", reason="again")
        self.assertFalse(v["changed"])
        self.assertEqual(len(TL.read_rows(gd)), n_tl)   # 二停零追加

    def test_stop_unknown_raises(self):
        s, _ = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        with self.assertRaises(ValueError):
            s.stop("battle-404")

    def test_stop_queued_battle_pauses(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=2))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        v = s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=2)
        self.assertEqual(v["state"], "queued")
        v2 = s.stop("battle-2", reason="wait")
        self.assertEqual(v2["state"], "paused")

    def test_resume_activates_when_headroom(self):
        gd = _mkgoal(self.tmp, "b1")
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", gd, soldiers=2)
        s.stop("battle-1", reason="r")
        v = s.resume("battle-1")
        self.assertEqual(v["state"], "active")
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["state"], "active")

    def test_resume_over_cap_goes_queued(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=2)
        s.register("battle-3", _mkgoal(self.tmp, "b3"), soldiers=2)
        v0 = s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        self.assertEqual(v0["state"], "queued")     # b2+b3 已占满帽 4
        s.stop("battle-1", reason="r")
        # battle-2+battle-3 占满帽 4；battle-1 续仗 →帽满 →排队不开工
        v = s.resume("battle-1")
        self.assertEqual(v["state"], "queued")
        self.assertIn("cap", v["reason"])

    def test_status_totals(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=3)
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=3)
        st = s.status()
        self.assertEqual(st["cap_soldiers"], 4)
        self.assertEqual(st["active_soldiers"], 3)
        self.assertEqual(st["headroom"], 1)
        self.assertEqual(st["queued"], 1)
        self.assertFalse(st["halted"])
        self.assertEqual(len(st["battles"]), 2)


class TestEmergencyStop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _fleet_of_two(self, cap=10):
        gd1 = _mkgoal(self.tmp, "b1", [
            "warrior-start battle=battle-1 warrior=warrior:W-1 pid=101"])
        gd2 = _mkgoal(self.tmp, "b2", [
            "warrior-start battle=battle-2 warrior=warrior:W-2 pid=202",
            "warrior-heartbeat warrior=warrior:W-2 intent=INT-x"])
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=cap))
        s.register("battle-1", gd1, soldiers=2)
        s.register("battle-2", gd2, soldiers=2)
        return s, gd1, gd2

    def test_emergency_stop_pauses_all_and_halts(self):
        s, gd1, gd2 = self._fleet_of_two()
        v = s.emergency_stop("incident")
        self.assertTrue(v["halted"])
        self.assertEqual(sorted(v["paused"]), ["battle-1", "battle-2"])
        self.assertTrue(s.status()["halted"])
        self.assertEqual(fs.meta(self.tmp).get("halted"), "1")

    def test_emergency_stop_signals_every_battle(self):
        """全停传播到所有仗：每仗账本可见的战士都拿到 stop 事件（halt 单源）。"""
        s, gd1, gd2 = self._fleet_of_two()
        s.emergency_stop("incident")
        self.assertIsNotNone(steer.scan(gd1, "warrior:W-1", 0).stop_reason)
        self.assertIsNotNone(steer.scan(gd2, "warrior:W-2", 0).stop_reason)
        for gd in (gd1, gd2):
            evs = [r[3] for r in TL.read_rows(gd)]
            self.assertTrue(any(e.startswith("fleet-halt") for e in evs))

    def test_emergency_stop_idempotent(self):
        s, gd1, gd2 = self._fleet_of_two()
        s.emergency_stop("incident")
        n1, n2 = len(TL.read_rows(gd1)), len(TL.read_rows(gd2))
        v = s.emergency_stop("again")
        self.assertFalse(v["changed"])
        self.assertEqual(len(TL.read_rows(gd1)), n1)
        self.assertEqual(len(TL.read_rows(gd2)), n2)

    def test_after_halt_no_promotion_no_new_intents(self):
        """全停后无新意图铸出：队列不升格、无仗 active、战士见停信号。"""
        s, gd1, gd2 = self._fleet_of_two(cap=4)          # 2+2=帽满
        v = s.register("battle-3", _mkgoal(self.tmp, "b3"), soldiers=2)
        self.assertEqual(v["state"], "queued")
        s.emergency_stop("incident")
        r = s.tick()
        self.assertEqual(r["promoted"], [])              # 队列冻结
        states = {b["battle"]: b["state"] for b in fs.rows(self.tmp)}
        self.assertTrue(all(st != "active" for st in states.values()))
        # 战士侧：领新意图前必先过 stop 信号（warrior loop 停序既有执法）
        self.assertIsNotNone(steer.scan(gd1, "warrior:W-1", 0).stop_reason)
        self.assertIsNotNone(steer.scan(gd2, "warrior:W-2", 0).stop_reason)

    def test_fleet_resume_clears_halt_and_promotes(self):
        s, _gd1, _gd2 = self._fleet_of_two()
        s.emergency_stop("incident")
        v = s.resume()                                   # 舰队级续
        self.assertTrue(v["resumed_fleet"])
        self.assertFalse(s.status()["halted"])
        self.assertEqual(len(v["promoted"]), 2)          # 帽 10 全装得下


class TestHeartbeatMonitor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_tick_marks_stale_active_failed(self):
        gd = _mkgoal(self.tmp, "b1")
        s, clock = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4), t=E1)
        s.register("battle-1", gd, soldiers=2)
        clock.advance(7200)                                       # 2h 无心跳
        r = s.tick()
        self.assertEqual(r["failed_stale"], ["battle-1"])
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["state"], "failed")
        audit = fs.audit_rows(self.tmp)
        self.assertTrue(any("heartbeat" in a["detail"] for a in audit))

    def test_tick_syncs_heartbeat_from_battle_timeline(self):
        """战士心跳行（账本既有事实）→舰队心跳列：不另造心跳协议。"""
        gd = _mkgoal(self.tmp, "b1", [
            "warrior-heartbeat warrior=warrior:W-1 intent=INT-1 tokens=10"], ts=TS3)
        s, clock = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=4,
                                              heartbeat_timeout_s=900.0), t=E3)
        s.register("battle-1", gd, soldiers=2)
        clock.advance(600)                                        # 10min<900s
        r = s.tick()
        self.assertEqual(r["failed_stale"], [])
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["heartbeat_at"], TS3)

    def test_stale_failure_frees_cap_for_promotion(self):
        s, clock = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=2), t=E1)
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=2)
        clock.advance(7200)
        r = s.tick()
        self.assertEqual(r["failed_stale"], ["battle-1"])
        self.assertEqual(r["promoted"], ["battle-2"])             # 腾帽即升格


class TestRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_recover_rebuilds_inflight_no_reregister(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=8))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        s.register("battle-2", _mkgoal(self.tmp, "b2"), soldiers=2)
        s.register("battle-3", _mkgoal(self.tmp, "b3"), soldiers=2)
        s.finish("battle-3")
        n_audit = len(fs.audit_rows(self.tmp))
        # 断电重启：新实例读同一注册表
        s2 = sup.FleetSupervisor(self.tmp, config=FIXTURE_CFG, now_fn=lambda: E3)
        r = s2.recover()
        self.assertEqual(r["in_flight"], ["battle-1", "battle-2"])   # 在途集
        self.assertEqual(len(fs.audit_rows(self.tmp)), n_audit)      # 恢复零审计噪音
        self.assertEqual(fs.row_of(self.tmp, "battle-3")["state"], "done")

    def test_recover_does_not_double_open(self):
        s, _ = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        gd = _mkgoal(self.tmp, "b1")
        s.register("battle-1", gd, soldiers=2)
        s2 = sup.FleetSupervisor(self.tmp, config=FIXTURE_CFG, now_fn=lambda: E3)
        s2.recover()
        v = s2.register("battle-1", gd, soldiers=2)                  # 重开同仗
        self.assertFalse(v["registered"])
        self.assertEqual(fs.row_of(self.tmp, "battle-1")["state"], "active")

    def test_halt_persists_across_recovery(self):
        s, _ = _mk_sup(self.tmp, cfg=dict(FIXTURE_CFG, cap_soldiers=8))
        s.register("battle-1", _mkgoal(self.tmp, "b1"), soldiers=2)
        s.emergency_stop("incident")
        s2 = sup.FleetSupervisor(self.tmp, config=FIXTURE_CFG, now_fn=lambda: E3)
        s2.recover()
        self.assertTrue(s2.status()["halted"])
        r = s2.tick()
        self.assertEqual(r["promoted"], [])                          # 不复活

    def test_run_loop_steps_injectable(self):
        s, clock = _mk_sup(self.tmp, cfg=FIXTURE_CFG)
        slept = []
        s.sleep = lambda sec: slept.append(sec)
        rounds = s.run(max_rounds=3, interval=5.0)
        self.assertEqual(rounds, 3)
        self.assertEqual(slept, [5.0, 5.0, 5.0])


class TestPlannerBoundary(unittest.TestCase):
    """与 planner_loop 的分界声明（母舰令：你是仗间层，别重叠）。

    supervisor.py 的 docstring 允许声明分界（可提及 planner_loop 名），
    但代码面零重叠：不 import planner 家族、不铸意图、不排空格。
    """

    def test_supervisor_module_never_imports_planner(self):
        import re as _re
        src = open(os.path.join(HERE, "..", "cli", "fleet",
                                "supervisor.py"), encoding="utf-8").read()
        body = _re.sub(r'""".*?"""', "", src, flags=_re.S)  # 剥 docstring
        self.assertIsNone(_re.search(r"^\s*(from|import)\s+.*planner",
                                     body, flags=_re.M))
        self.assertNotIn("add-intent", body)    # 零意图铸造（不碰仗内派活）
        self.assertNotIn("rank_gaps", body)     # 零空格排序
        self.assertIn("分界", src)               # docstring 必须声明分界


if __name__ == "__main__":
    unittest.main()
