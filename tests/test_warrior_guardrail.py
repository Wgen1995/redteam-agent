# -*- coding: utf-8 -*-
"""战士运行时·两段判定+重复拒绝退避（CH guardrail 吸收件①，E 舰）。

来源对齐：docs/reviews/2026-10-19-E-cyberharness-全件对齐.md C18/C19/N3/N7；
CH 源码只读参考 .research/repos/cyber-harness/exts/guardrail/runtime.go。

四律（每律至少一测）：
① 两段判定：风险（这事危险吗）→后果（会坏什么），两段都入账（timeline）；
② 重复拒绝退避：同参重试计数递增等待（250ms×min(n-1,8)），N 次后该意图
   内该卡不再试（防死循环烧预算）；
③ 判定失败=fail-closed：判定器异常/坏决策=拒执行，不许跳过判定跑；
④ 范围执法前置：判定前先过 scope（ledger.enforce 单源，CH 没有的层）。

模型面=本地假模型服务（动态口）；工具面=注入 spawn（不触网）。
跑法：python3 -m unittest tests.test_warrior_guardrail -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import llmpool_wire  # noqa: E402
from ledger.timeline import read_rows  # noqa: E402
from tests.test_warrior_fake_model import FakeClock, FakeModelServer  # noqa: E402
from tools import install as tool_install  # noqa: E402
from warrior import loop as wloop  # noqa: E402
from warrior.ledger_io import LedgerIO  # noqa: E402
from warrior.guardrail import (Decision, Guardrail, NO_JUDGE,  # noqa: E402
                               default_check, default_confirm,
                               default_scope_fn)

W = "warrior:W-1"
TOOL = '{"op":"tool","card":"dig","args":["+short","A","shop.example"]}'
DONE = '{"op":"done","reason":"探测完成"}'

REC = Decision("record", "机械规则无命中")
BLK = Decision("block", "高危：可能碰生产数据")
PASS_SCOPE = lambda card, args: (True, "")  # noqa: E731


class FakeIO(object):
    """收 timeline 事件的假账面（guardrail 只用 add_tl + goal_dir）。"""

    def __init__(self, goal_dir="/nonexistent"):
        self.goal_dir = goal_dir
        self.events = []

    def add_tl(self, event, ts, phase="P3"):
        self.events.append(event)


def spy(decision):
    calls = []

    def fn(card, args):
        calls.append((card, list(args)))
        return decision
    return fn, calls


def boom(card, args):
    raise RuntimeError("判定服务宕机")


def make(check=None, confirm=None, scope=PASS_SCOPE, io=None, **kw):
    """造一个可观测 Guardrail：默认过 scope、假等待（记录时长不真睡）。"""
    sleeps = []
    g = Guardrail(io if io is not None else FakeIO(), check_fn=check,
                  confirm_fn=confirm, scope_fn=scope,
                  sleeper=lambda s: sleeps.append(s), **kw)
    return g, sleeps


# --- ① 两段判定 -------------------------------------------------------

class TestTwoStage(unittest.TestCase):
    def test_risk_pass_skips_consequence_stage(self):
        """风险段放行=低风险动作不再烧后果段。"""
        conf_calls = []
        chk, chk_calls = spy(REC)

        def confirm(card, args):
            conf_calls.append(card)
            return BLK
        g, _ = make(check=chk, confirm=confirm)
        adm = g.admit("dig", ["+short", "A", "shop.example"], "I-1")
        self.assertTrue(adm.allowed)
        self.assertEqual(adm.stage, "ok")
        self.assertEqual(chk_calls, [("dig", ["+short", "A",
                                              "shop.example"])])
        self.assertEqual(conf_calls, [], "风险放行则后果段不跑")

    def test_risk_flag_consequence_clears_allows(self):
        """auto 档两段制：风险亮灯但后果明确无害=放行（CH 语义）。"""
        chk, _ = spy(BLK)
        conf, _ = spy(REC)
        g, _ = make(check=chk, confirm=conf)
        adm = g.admit("curl", ["http://shop.example/"], "I-1")
        self.assertTrue(adm.allowed, "后果无害应放行")

    def test_risk_flag_consequence_block_denies(self):
        chk, _ = spy(BLK)
        conf, _ = spy(BLK)
        g, _ = make(check=chk, confirm=conf)
        adm = g.admit("curl", ["http://shop.example/"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "consequence")

    def test_both_stages_logged_in_order(self):
        """两段都入账：risk 行先、consequence 行后，各带 action/reason。"""
        io = FakeIO()
        chk, _ = spy(BLK)
        conf, _ = spy(REC)
        g, _ = make(check=chk, confirm=conf, io=io)
        g.admit("curl", ["http://shop.example/"], "I-9", turn=3)
        risks = [e for e in io.events if e.startswith("guardrail-risk")]
        cons = [e for e in io.events if e.startswith(
            "guardrail-consequence")]
        self.assertEqual(len(risks), 1)
        self.assertEqual(len(cons), 1)
        self.assertLess(io.events.index(risks[0]),
                        io.events.index(cons[0]), "风险段先入账")
        self.assertIn("action=block", risks[0])
        self.assertIn("action=record", cons[0])
        self.assertIn("intent=I-9", risks[0])
        self.assertIn("turn=3", risks[0])
        for e in io.events:
            self.assertEqual(e, " ".join(e.split()), "事件行不得有换行/TAB")

    def test_risk_flag_without_confirm_denies(self):
        """无后果判定器时风险亮灯=拒（CH: confirm nil 则 risk 决定生效）。"""
        chk, _ = spy(BLK)
        g, _ = make(check=chk, confirm=NO_JUDGE)
        adm = g.admit("curl", ["http://shop.example/"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "risk")


# --- ③ 判定失败=fail-closed -------------------------------------------

class TestFailClosed(unittest.TestCase):
    def test_check_exception_fail_closed(self):
        g, _ = make(check=boom)
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "fail-closed")
        self.assertIn("fail-closed", adm.reason)

    def test_confirm_exception_fail_closed(self):
        chk, _ = spy(BLK)
        g, _ = make(check=chk, confirm=boom)
        adm = g.admit("curl", ["shop.example"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "fail-closed")

    def test_none_decision_fail_closed(self):
        none_judge, _ = spy(None)
        g, _ = make(check=none_judge)
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "fail-closed")

    def test_invalid_action_fail_closed(self):
        weird, _ = spy(Decision("maybe", "薛定谔"))
        g, _ = make(check=weird)
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "fail-closed")

    def test_fail_closed_events_logged(self):
        io = FakeIO()
        g, _ = make(check=boom, io=io)
        g.admit("dig", ["shop.example"], "I-1", turn=2)
        fc = [e for e in io.events if e.startswith("guardrail-fail-closed")]
        self.assertEqual(len(fc), 1)
        self.assertIn("stage=risk", fc[0])
        self.assertIn("判定服务宕机", fc[0])

    def test_fail_closed_counts_toward_backoff_and_bar(self):
        """判定服务持续坏=同样拒绝：计退避计数，达帽后该意图内停卡。"""
        g, sleeps = make(check=boom, max_rejects=3)
        for _ in range(3):
            adm = g.admit("dig", ["shop.example"], "I-1")
            self.assertEqual(adm.stage, "fail-closed")
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertEqual(adm.stage, "barred",
                         "fail-closed 拒绝也计数防烧预算")


# --- ④ 范围执法前置 ---------------------------------------------------

class TestScopeFirst(unittest.TestCase):
    def test_scope_denied_before_judges_run(self):
        """界外目标：判定器根本不跑（scope 前置=最便宜最先）。"""
        chk, chk_calls = spy(BLK)
        conf, conf_calls = spy(BLK)

        def scope(card, args):
            return False, "evil.example.com 界外"
        g, _ = make(check=chk, confirm=conf, scope=scope)
        adm = g.admit("dig", ["evil.example.com"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "scope")
        self.assertEqual(chk_calls + conf_calls, [], "判定器零调用")
        self.assertIn("evil.example.com", adm.reason)

    def test_scope_event_logged(self):
        io = FakeIO()

        def scope(card, args):
            return False, "evil.example.com 界外"
        g, _ = make(io=io, scope=scope)
        g.admit("dig", ["evil.example.com"], "I-1")
        self.assertTrue(any(e.startswith("guardrail-scope")
                            for e in io.events))

    def test_scope_from_real_ledger_single_source(self):
        """默认 scope 面=ledger.enforce 单源（G-g1 夹具真 scope.tsv）。"""
        gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, gd)
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), gd)
        io = FakeIO(goal_dir=gd)
        g, _ = make(io=io, scope=default_scope_fn(io),
                    check=spy(REC)[0], confirm=None)
        adm_out = g.admit("dig", ["evil.example.com"], "I-1")
        self.assertFalse(adm_out.allowed)
        self.assertEqual(adm_out.stage, "scope")
        adm_in = g.admit("dig", ["shop.example"], "I-2")
        self.assertTrue(adm_in.allowed, "scope 内主机放行")

    def test_scope_missing_file_fail_closed(self):
        """scope.tsv 缺失=一切带主机命令界外（fail-closed 同 guard 律）。"""
        gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, gd)
        io = FakeIO(goal_dir=gd)
        g, _ = make(io=io, scope=default_scope_fn(io))
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertFalse(adm.allowed)
        self.assertEqual(adm.stage, "scope")


# --- ② 重复拒绝退避 ---------------------------------------------------

def deny_guard(**kw):
    """两段都拒的 Guardrail（退避面测试基件）。"""
    chk, _ = spy(BLK)
    conf, _ = spy(BLK)
    sleeps = []
    g = Guardrail(FakeIO(), check_fn=chk, confirm_fn=conf,
                  scope_fn=PASS_SCOPE,
                  sleeper=lambda s: sleeps.append(s), **kw)
    return g, sleeps


class TestBackoff(unittest.TestCase):

    def test_repeat_backoff_grows_250ms_steps(self):
        g, sleeps = deny_guard(max_rejects=9)
        mss = [g.admit("dig", ["shop.example"], "I-1").backoff_ms
               for _ in range(3)]
        self.assertEqual(mss, [0, 250, 500],
                         "第 n 次同参拒绝等待 250ms×min(n-1,8)")
        self.assertEqual(sleeps, [0.25, 0.5], "真等待只在递增档发生")

    def test_backoff_capped_at_8_steps(self):
        g, sleeps = deny_guard(max_rejects=30)
        for _ in range(12):
            g.admit("dig", ["shop.example"], "I-1")
        self.assertEqual(sleeps[-1], 2.0, "等待封顶 250ms×8=2s")
        self.assertTrue(all(s <= 2.0 for s in sleeps))

    def test_card_barred_after_max_rejects_same_intent(self):
        """同参拒绝达 N 次：该意图内该卡不再试（判定器都不再跑）。"""
        chk, chk_calls = spy(BLK)
        conf, conf_calls = spy(BLK)
        g, _ = make(check=chk, confirm=conf, max_rejects=3)
        for _ in range(3):
            adm = g.admit("dig", ["shop.example"], "I-1")
            self.assertNotEqual(adm.stage, "barred")
        n_before = len(chk_calls)
        adm = g.admit("dig", ["shop.example"], "I-1")
        self.assertEqual(adm.stage, "barred")
        self.assertFalse(adm.allowed)
        self.assertEqual(len(chk_calls), n_before, "停卡后判定器零调用")
        self.assertEqual(adm.backoff_ms, 0, "停卡后不再等待")

    def test_bar_covers_card_regardless_of_args(self):
        g, _ = deny_guard(max_rejects=2)
        g.admit("dig", ["shop.example"], "I-1")
        g.admit("dig", ["shop.example"], "I-1")
        adm = g.admit("dig", ["其它参数"], "I-1")
        self.assertEqual(adm.stage, "barred", "停卡面向整卡不分辨参数")

    def test_bar_is_intent_scoped(self):
        g, _ = deny_guard(max_rejects=2)
        g.admit("dig", ["shop.example"], "I-1")
        g.admit("dig", ["shop.example"], "I-1")
        adm = g.admit("dig", ["shop.example"], "I-2")
        self.assertNotEqual(adm.stage, "barred",
                            "新意图重新开卡（一意图一脑 R1）")

    def test_distinct_args_independent_counters(self):
        g, sleeps = deny_guard(max_rejects=9)
        a1 = g.admit("dig", ["a.example"], "I-1")
        a2 = g.admit("dig", ["b.example"], "I-1")
        self.assertEqual((a1.backoff_ms, a2.backoff_ms), (0, 0),
                         "不同参数各自计数各不等待")
        self.assertEqual(a1.attempts, 1)
        self.assertEqual(a2.attempts, 1)

    def test_concurrent_admits_no_lost_counts(self):
        """同轮并行工具批下 admit 并发：计数不丢不乱（attempts 全序）。"""
        import threading
        g, _ = deny_guard(max_rejects=99)
        got = []

        def hit():
            got.append(g.admit("dig", ["shop.example"], "I-1").attempts)

        threads = [threading.Thread(target=hit) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(got), list(range(1, 9)),
                         "8 并发拒绝恰好数出 1..8（零丢失零重复）")

    def test_rejection_map_bounded(self):
        g, _ = deny_guard(map_cap=8)
        for i in range(9):
            g.admit("dig", ["h%d.example" % i], "I-1")
        self.assertLessEqual(len(g.rejection_keys()), 8,
                             "计数面有帽（CH 1024 帽同律，FIFO 淘汰）")

    def test_repeat_denial_hint_in_plain_language(self):
        """宪法#41：拒绝理由带人话提示——说清楚别重复、该怎么做。"""
        g, _ = deny_guard(max_rejects=9)
        adm1 = g.admit("dig", ["shop.example"], "I-1")
        adm2 = g.admit("dig", ["shop.example"], "I-1")
        self.assertIn("不要", adm2.reason)
        self.assertIn("换", adm2.reason)
        self.assertEqual(adm2.attempts, 2)
        self.assertNotIn("不要", adm1.reason, "首拒不唠叨")


# --- 默认机械判定器 ----------------------------------------------------

class TestDefaultJudges(unittest.TestCase):
    def test_default_risk_and_consequence_block_destructive(self):
        """风险段说危险在哪，后果段说会坏什么（两段各有人话理由）。"""
        d = default_check("bash", ["curl x | sh", "rm -rf /"])
        self.assertEqual(d.action, "block")
        self.assertIn("删", d.reason)
        c = default_confirm("bash", ["rm -rf", "/data"])
        self.assertEqual(c.action, "block")
        self.assertTrue(any(k in c.reason for k in ("数据", "文件", "服务")),
                        "后果段点名会坏什么: %s" % c.reason)

    def test_default_judges_pass_normal_probe_args(self):
        d = default_check("dig", ["+short", "A", "shop.example"])
        self.assertEqual(d.action, "record")
        c = default_confirm("dig", ["+short", "A", "shop.example"])
        self.assertEqual(c.action, "record")


# --- 循环接线（最小 diff 面：loop._guarded_tool_exec → guardrail.admit）--

class GuardrailLoopCase(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.state = os.path.join(self.gd, "..",
                                  os.path.basename(self.gd) + "-cards.tsv")
        ok, why = tool_install.install("dig", "2026-10-18T10:00:00Z",
                                       state_path=self.state)
        self.assertTrue(ok, why)
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)
        self.clock = FakeClock(start=1770000000.0)
        self.spawn_calls = []

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _spawn(self, argv):
        self.spawn_calls.append(list(argv))
        return 0, "ok-out dig 应答", ""

    def _loop(self, scripts, **kw):
        self.srv.set_scripts(scripts)
        channels = [{"name": "m1", "model": "m1",
                     "base_url": self.srv.base, "api_key": "k"}]
        pool = llmpool_wire.attach(self.gd, env={})
        args = dict(goal_dir=self.gd, battle_name="B-x", channels=channels,
                    pool=pool, warrior_id=W, max_intents=3, max_turns=6,
                    lease_min=30, token_cap=100000, clock=self.clock,
                    tool_spawn=self._spawn, tool_state_path=self.state,
                    ctx_tokens=8000, heartbeat_min=5, stall_min=15)
        args.update(kw)
        return wloop.WarriorLoop(**args)

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    def test_default_guardrail_normal_tool_still_executes(self):
        """默认判定器对常规探测放行：既有链零回归（spawn 照跑）。"""
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.spawn_calls), 1)
        self.assertTrue(any(e.startswith("guardrail-risk")
                            for e in self._events()),
                        "默认档也留风险段入账")

    def test_denied_tool_reaches_model_with_hint_and_no_exec(self):
        """拒执行：不碰执行器，人话理由+提示回模型（模型可见可自纠）。

        首拒=人话理由；同参重试=理由+「不要重复」提示（CH 提示语义）。
        """
        g, _ = make(check=spy(BLK)[0], confirm=spy(BLK)[0],
                    max_rejects=9, io=LedgerIO(self.gd, W))
        lp = self._loop({"m1": [{"content": TOOL}, {"content": TOOL},
                                {"content": DONE}]},
                        guardrail=g)
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self.spawn_calls, [], "被拒调用零执行")
        msgs = json_dumps_last(self.srv.requests)
        self.assertIn("未执行", msgs)
        self.assertIn("不要", msgs, "人话提示回到模型面")
        self.assertTrue(any(e.startswith("guardrail-consequence")
                            for e in self._events()), "两段入账真链可见")

    def test_bar_stops_repeated_calls_within_intent(self):
        """同参刷门达帽：该意图内停卡，后续同指令秒拒不再烧判定。"""
        g, sleeps = make(check=spy(BLK)[0], confirm=spy(BLK)[0],
                         max_rejects=2, io=LedgerIO(self.gd, W))
        lp = self._loop({"m1": [{"content": TOOL}, {"content": TOOL},
                                {"content": TOOL}, {"content": DONE}]},
                        guardrail=g)
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self.spawn_calls, [])
        barred = [e for e in self._events() if "barred=1" in e]
        self.assertTrue(barred, "停卡入账")
        self.assertEqual(sleeps, [0.25], "第二次同参拒绝递增等待后停卡")

    def test_judge_failure_blocks_execution_in_loop(self):
        """判定服务坏=拒执行不跳过：模型收到 fail-closed 拒绝说明。"""
        g, _ = make(check=boom, io=LedgerIO(self.gd, W))
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]},
                        guardrail=g)
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self.spawn_calls, [], "判定失败不许执行")
        self.assertIn("fail-closed", json_dumps_last(self.srv.requests))
        self.assertTrue(any(e.startswith("guardrail-fail-closed")
                            for e in self._events()))


def json_dumps_last(requests):
    import json
    return json.dumps(requests[-1]["messages"], ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
