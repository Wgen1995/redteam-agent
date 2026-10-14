# -*- coding: utf-8 -*-
"""v0.8 Task A：llmpool 故障转移——红绿测试。

红=现状：cli/ledger 无 llmpool 模块。契约（docs/superpowers/plans/
2026-10-11-v08-artex-borrow.md Task A，含两处声明改进）：
- 错误分类：400/ctx取消 不转移；401/402/403/404 硬熔断（1 次即熔）；
  408/429/网络(URLError/timeout) 软计数；5xx 软计数。
- 软计数连续 3 次熔断；冷却阶梯 1/5/30 分钟按连续熔断次数选档。
- 改进①：429 固定短冷却 1min / 5xx 走长档——分道。
- 改进②：冷却 ±20% 抖动（随机源注入可测）。
- Registry 进程级单例 + 状态落盘/恢复（路径注入，本测试用 tmp 目录）。
- 接口：pick(models) 健康链序首个 / report(model, err) / snapshot() 三态
  （healthy/cooling/tripped）+剩余秒；时间函数注入（拨钟）；纯离线。
- trip/recover 经注入 emit 回调发 kind=llm_failover 事件；默认 None 不炸。
"""
import asyncio
import json
import os
import shutil
import socket
import tempfile
import unittest
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys_path_cli = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402
sys.path.insert(0, sys_path_cli)

from ledger import llmpool as lp  # noqa: E402


def half_rng():
    """固定 0.5 → 抖动因子恰为 1.0（确定性基准档）。"""
    return 0.5


class Clock(object):
    """可拨时钟：默认 epoch 1000.0，advance 秒级前进。"""

    def __init__(self, start=1000.0):
        self.t = float(start)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += float(seconds)


class PoolBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="v08a-pool-")
        self.state_path = os.path.join(self.tmp, "llmpool_state.json")
        self.clock = Clock()
        self.events = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pool(self, **kw):
        kw.setdefault("state_path", self.state_path)
        kw.setdefault("now", self.clock)
        kw.setdefault("rng", half_rng)
        kw.setdefault("emit", self.events.append)
        return lp.LLMPoolRegistry(**kw)

    def soft_trip(self, pool, model, err, times=3):
        for _ in range(times):
            pool.report(model, err)


class TestClassify(unittest.TestCase):
    """classify 纯函数：错误分类表逐格对账。"""

    def test_ok_2xx(self):
        self.assertEqual(lp.classify(200)[0], "ok")
        self.assertEqual(lp.classify(204)[0], "ok")

    def test_400_no_failover(self):
        bucket, lane, _ = lp.classify(400)
        self.assertEqual(bucket, "no_failover")
        self.assertIsNone(lane)

    def test_ctx_cancel_no_failover(self):
        for err in (asyncio.CancelledError(), KeyboardInterrupt()):
            bucket, lane, _ = lp.classify(err)
            self.assertEqual(bucket, "no_failover", err.__class__.__name__)
            self.assertIsNone(lane)

    def test_hard_1xx_hit(self):
        for code in (401, 402, 403, 404):
            bucket, lane, _ = lp.classify(code)
            self.assertEqual(bucket, "hard", code)
            self.assertIsNone(lane)

    def test_soft_408(self):
        bucket, lane, _ = lp.classify(408)
        self.assertEqual(bucket, "soft")
        self.assertEqual(lane, "server")

    def test_soft_429_rate_lane(self):
        bucket, lane, _ = lp.classify(429)
        self.assertEqual(bucket, "soft")
        self.assertEqual(lane, "rate")

    def test_soft_5xx_server_lane(self):
        for code in (500, 502, 503):
            bucket, lane, _ = lp.classify(code)
            self.assertEqual(bucket, "soft", code)
            self.assertEqual(lane, "server")

    def test_network_exceptions_soft_server(self):
        for err in (urllib.error.URLError("conn refused"),
                    socket.timeout("read timeout"),
                    ConnectionResetError("reset")):
            bucket, lane, _ = lp.classify(err)
            self.assertEqual(bucket, "soft", err.__class__.__name__)
            self.assertEqual(lane, "server")

    def test_httperror_classified_by_code(self):
        err = urllib.error.HTTPError("u", 429, "Too Many Requests", None, None)
        bucket, lane, _ = lp.classify(err)
        self.assertEqual(bucket, "soft")
        self.assertEqual(lane, "rate")

    def test_unknown_no_failover(self):
        # 表外 4xx / 未知异常：保守不转移
        self.assertEqual(lp.classify(409)[0], "no_failover")
        self.assertEqual(lp.classify(ValueError("bug"))[0], "no_failover")


class TestPick(PoolBase):
    MODELS = [{"model": "a"}, {"model": "b"}, {"model": "c"}]

    def test_pick_first_healthy_in_chain_order(self):
        p = self.pool()
        entry = p.pick(self.MODELS)
        self.assertIs(entry, self.MODELS[0])

    def test_pick_skips_unhealthy_to_next(self):
        p = self.pool()
        p.report("a", 401)
        entry = p.pick(self.MODELS)
        self.assertIs(entry, self.MODELS[1])

    def test_pick_none_when_all_down(self):
        p = self.pool()
        for m in ("a", "b", "c"):
            p.report(m, 403)
        self.assertIsNone(p.pick(self.MODELS))
        self.assertEqual(self.events[0]["kind"], "llm_failover")

    def test_pick_empty_chain(self):
        self.assertIsNone(self.pool().pick([]))

    def test_pick_accepts_name_key(self):
        p = self.pool()
        entry = p.pick([{"name": "n1"}, {"model": "m1"}])
        self.assertEqual(entry["name"], "n1")

    def test_pick_recovers_after_cooldown(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)
        self.assertIs(p.pick(self.MODELS), self.MODELS[1])
        self.clock.advance(61)
        self.assertIs(p.pick(self.MODELS), self.MODELS[0])


class TestNoFailover(PoolBase):
    def test_400_keeps_healthy_and_no_event(self):
        p = self.pool()
        p.report("a", 400)
        snap = p.snapshot("a")
        self.assertEqual(snap["state"], "healthy")
        self.assertEqual(self.events, [])

    def test_ctx_cancel_keeps_healthy(self):
        p = self.pool()
        p.report("a", asyncio.CancelledError())
        self.assertEqual(p.snapshot("a")["state"], "healthy")


class TestHardTrip(PoolBase):
    def test_one_hit_trips(self):
        p = self.pool()
        p.report("a", 401)
        snap = p.snapshot("a")
        self.assertEqual(snap["state"], "tripped")
        self.assertIsNone(snap["remaining_s"])

    def test_hard_trip_not_healed_by_time(self):
        p = self.pool()
        p.report("a", 402)
        self.clock.advance(3600)
        self.assertEqual(p.snapshot("a")["state"], "tripped")

    def test_all_hard_codes_trip_once(self):
        for code in (401, 402, 403, 404):
            p = self.pool()
            p.report("a", code)
            self.assertEqual(p.snapshot("a")["state"], "tripped", code)

    def test_success_recovers_hard_trip(self):
        p = self.pool()
        p.report("a", 404)
        p.report("a", 200)
        self.assertEqual(p.snapshot("a")["state"], "healthy")
        self.assertEqual(self.events[-1]["event"], "recover")


class TestSoftStreak(PoolBase):
    def test_two_soft_failures_stay_healthy(self):
        p = self.pool()
        p.report("a", 503)
        p.report("a", 503)
        self.assertEqual(p.snapshot("a")["state"], "healthy")
        self.assertEqual(self.events, [])

    def test_third_consecutive_trips_to_cooling(self):
        p = self.pool()
        self.soft_trip(p, "a", 503)
        snap = p.snapshot("a")
        self.assertEqual(snap["state"], "cooling")
        self.assertEqual(snap["remaining_s"], 60)  # 阶梯第 1 档 1min

    def test_success_resets_streak(self):
        p = self.pool()
        p.report("a", 429)
        p.report("a", 429)
        p.report("a", 200)
        p.report("a", 429)
        p.report("a", 429)
        self.assertEqual(p.snapshot("a")["state"], "healthy")

    def test_soft_during_cooling_retrips(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)      # 熔 60s
        self.clock.advance(10)
        self.soft_trip(p, "a", 500)      # 冷却中再连败 → 再熔（长档）
        snap = p.snapshot("a")
        self.assertEqual(snap["state"], "cooling")
        self.assertEqual(snap["remaining_s"], 300)


class TestLadder(PoolBase):
    def test_server_lane_escalates_1_5_30(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)
        self.assertEqual(p.snapshot("a")["remaining_s"], 60)
        self.clock.advance(61)           # 冷却窗过 → 自动恢复
        self.soft_trip(p, "a", 500)
        self.assertEqual(p.snapshot("a")["remaining_s"], 300)
        self.clock.advance(301)
        self.soft_trip(p, "a", 500)
        self.assertEqual(p.snapshot("a")["remaining_s"], 1800)
        self.clock.advance(1801)
        self.soft_trip(p, "a", 500)      # 第 4 次：封顶 30min
        self.assertEqual(p.snapshot("a")["remaining_s"], 1800)

    def test_success_resets_ladder(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)      # 1min
        self.clock.advance(61)
        self.soft_trip(p, "a", 500)      # 5min
        p.report("a", 200)               # 成功 → 连续熔断计数清零
        self.soft_trip(p, "a", 500)
        self.assertEqual(p.snapshot("a")["remaining_s"], 60)


class TestRateLane(PoolBase):
    """改进①：429 固定短冷却 1min，不随次数升档。"""

    def test_429_fixed_1min_never_escalates(self):
        p = self.pool()
        for _ in range(3):
            self.soft_trip(p, "a", 429)
            self.assertEqual(p.snapshot("a")["remaining_s"], 60)
            self.clock.advance(61)

    def test_lanes_independent(self):
        p = self.pool()
        self.soft_trip(p, "a", 429)      # rate 档 60s
        self.assertEqual(p.snapshot("a")["remaining_s"], 60)
        self.clock.advance(61)
        self.soft_trip(p, "a", 500)      # server 档仍第 1 档
        self.assertEqual(p.snapshot("a")["remaining_s"], 60)
        self.clock.advance(61)
        self.soft_trip(p, "a", 429)      # rate 再熔依旧 60s
        self.assertEqual(p.snapshot("a")["remaining_s"], 60)


class TestJitter(PoolBase):
    """改进②：冷却 ±20% 抖动，随机源注入可测。"""

    def trip_with_rng(self, rng, err=500):
        p = self.pool(rng=rng)
        self.soft_trip(p, "a", err)
        return p.snapshot("a")["remaining_s"]

    def test_lower_bound_minus_20_percent(self):
        self.assertEqual(self.trip_with_rng(lambda: 0.0), 48)    # 60*0.8

    def test_midpoint_exact(self):
        self.assertEqual(self.trip_with_rng(lambda: 0.5), 60)    # 因子 1.0

    def test_upper_region_plus_20_percent(self):
        self.assertEqual(self.trip_with_rng(lambda: 0.75), 66)   # 60*1.1

    def test_rate_lane_also_jittered(self):
        self.assertEqual(self.trip_with_rng(lambda: 0.0, err=429), 48)


class TestTimeInjection(PoolBase):
    def test_remaining_counts_down(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)
        self.clock.advance(30)
        self.assertEqual(p.snapshot("a")["remaining_s"], 30)
        self.clock.advance(29)
        snap = p.snapshot("a")
        self.assertEqual(snap["state"], "cooling")
        self.assertEqual(snap["remaining_s"], 1)
        self.clock.advance(1)
        self.assertEqual(p.snapshot("a")["state"], "healthy")

    def test_expiry_emits_recover_once(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)
        self.clock.advance(60)
        self.assertEqual(p.snapshot("a")["state"], "healthy")
        kinds = [e["event"] for e in self.events]
        self.assertEqual(kinds, ["trip", "recover"])
        p.snapshot("a")  # 幂等：不重复发 recover
        self.assertEqual([e["event"] for e in self.events], ["trip", "recover"])


class TestEvents(PoolBase):
    def test_trip_event_payload(self):
        p = self.pool()
        p.report("a", 429)
        p.report("a", 429)
        p.report("a", 429)
        self.assertEqual(len(self.events), 1)
        ev = self.events[0]
        self.assertEqual(ev["kind"], "llm_failover")
        self.assertEqual(ev["event"], "trip")
        self.assertEqual(ev["model"], "a")
        self.assertEqual(ev["lane"], "rate")
        self.assertEqual(ev["cooldown_s"], 60)
        self.assertEqual(ev["ts"], self.clock())

    def test_hard_trip_event(self):
        p = self.pool()
        p.report("a", 401)
        ev = self.events[0]
        self.assertEqual(ev["event"], "trip")
        self.assertIn("401", ev["reason"])

    def test_default_emit_none_does_not_crash(self):
        p = self.pool(emit=None)
        p.report("a", 401)
        p.report("a", 200)
        self.assertEqual(p.snapshot("a")["state"], "healthy")

    def test_raising_emit_does_not_crash(self):
        def boom(ev):
            raise RuntimeError("ledger down")
        p = self.pool(emit=boom)
        p.report("a", 401)
        self.assertEqual(p.snapshot("a")["state"], "tripped")


class TestPersistence(PoolBase):
    def test_cooling_window_restored_across_restart(self):
        p1 = self.pool()
        self.soft_trip(p1, "a", 500)     # 冷却 60s 未过
        p1.report("b", 401)              # b 硬熔
        p2 = self.pool()                 # 同路径新实例=重启
        self.assertEqual(p2.snapshot("a")["state"], "cooling")
        self.assertEqual(p2.snapshot("a")["remaining_s"], 60)
        self.assertEqual(p2.snapshot("b")["state"], "tripped")

    def test_expired_window_recovers_after_restart(self):
        p1 = self.pool()
        self.soft_trip(p1, "a", 500)
        self.clock.advance(61)           # 重启前窗口已过
        p2 = self.pool()
        self.assertEqual(p2.snapshot("a")["state"], "healthy")

    def test_hard_trip_survives_restart(self):
        self.pool().report("a", 403)
        self.clock.advance(86400)
        self.assertEqual(self.pool().snapshot("a")["state"], "tripped")

    def test_corrupt_state_file_starts_fresh(self):
        with open(self.state_path, "w", encoding="utf-8") as f:
            f.write("{not-json")
        p = self.pool()
        self.assertEqual(p.snapshot("a")["state"], "healthy")
        p.report("a", 500)
        self.assertEqual(len(self.events), 0)

    def test_state_file_is_json_with_models(self):
        p = self.pool()
        self.soft_trip(p, "a", 500)
        with open(self.state_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("a", data["models"])
        self.assertEqual(data["models"]["a"]["cooldown_end"], 1060.0)

    def test_missing_state_file_starts_fresh(self):
        p = self.pool(state_path=os.path.join(self.tmp, "nope", "s.json"))
        p.report("a", 500)
        self.assertEqual(p.snapshot("a")["state"], "healthy")


class TestSingleton(PoolBase):
    def test_get_registry_process_level_singleton(self):
        lp.reset_registry()
        r1 = lp.get_registry(state_path=self.state_path, now=self.clock,
                             rng=half_rng, emit=self.events.append)
        r2 = lp.get_registry(state_path=os.path.join(self.tmp, "other.json"))
        self.assertIs(r1, r2)            # 二次取用忽略参数：进程级唯一
        self.assertEqual(r1.state_path, self.state_path)
        lp.reset_registry()
        r3 = lp.get_registry(state_path=self.state_path)
        self.assertIsNot(r1, r3)

    def tearDown(self):
        lp.reset_registry()
        super(TestSingleton, self).tearDown()


class TestSnapshot(PoolBase):
    def test_single_model_shape(self):
        p = self.pool()
        snap = p.snapshot("a")
        self.assertEqual(sorted(snap.keys()), ["remaining_s", "state"])
        self.assertEqual(snap["state"], "healthy")
        self.assertEqual(snap["remaining_s"], 0)

    def test_all_models_shape(self):
        p = self.pool()
        p.report("a", 401)
        p.report("b", 500)
        all_snap = p.snapshot()
        self.assertEqual(sorted(all_snap.keys()), ["a", "b"])
        self.assertEqual(all_snap["a"]["state"], "tripped")
        self.assertEqual(all_snap["b"]["state"], "healthy")

    def test_unknown_model_healthy(self):
        self.assertEqual(self.pool().snapshot("ghost")["state"], "healthy")


if __name__ == "__main__":
    unittest.main()
